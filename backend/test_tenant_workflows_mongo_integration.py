"""Real HTTP+Mongo isolation tests for the opt-in recipe/order/Z workflow pilot.

Disabled during normal discovery; run explicitly using the temporary QA replica
set provided by scripts/test-restop-tenant-mongo.sh. Never use a client DB.
"""
import ast
import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

QA_URL = os.getenv("RESTOP_TEST_TENANT_MONGO_URL")


@unittest.skipUnless(QA_URL, "Requires isolated QA Mongo replica set")
class WorkflowTenantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi import FastAPI, Header, HTTPException
        from fastapi.testclient import TestClient
        from motor.motor_asyncio import AsyncIOMotorClient
        from pymongo import ASCENDING, MongoClient
        from tenant_stock_api import build_tenant_router
        from tenant_workflows_api import build_tenant_workflow_router

        cls.db_name = "restop_tenant_qa_" + uuid4().hex[:16]
        assert cls.db_name.startswith("restop_tenant_qa_")
        cls.mongo = MongoClient(QA_URL, serverSelectionTimeoutMS=5000)
        hello = cls.mongo.admin.command("hello")
        if not hello.get("setName"):
            raise RuntimeError("Real workflow QA requires Mongo replica set")
        cls.sync_db = cls.mongo[cls.db_name]
        cls.sync_db.users.insert_many([
            {"id": "a", "restaurant_id": "restaurant_A", "role": "patron", "is_active": True},
            {"id": "b", "restaurant_id": "restaurant_B", "role": "patron", "is_active": True},
            {"id": "chef", "restaurant_id": "restaurant_A", "role": "chef_cuisine", "is_active": True},
            {"id": "cashier", "restaurant_id": "restaurant_A", "role": "caissier", "is_active": True},
            {"id": "employee", "restaurant_id": "restaurant_A", "role": "employe_cuisine", "is_active": True},
            {"id": "legacy", "role": "super_admin", "is_active": True}
        ])
        cls.sync_db.user_sessions.insert_many([
            {"session_id": u+"-token", "user_id": u, "login_time": datetime.utcnow()}
            for u in ["a", "b", "chef", "cashier", "employee", "legacy"]
        ])
        cls.sync_db.tenant_z_reports.create_index(
            [("restaurant_id", ASCENDING), ("report_reference", ASCENDING)], unique=True)
        cls.async_client = AsyncIOMotorClient(QA_URL, serverSelectionTimeoutMS=5000)
        cls.async_db = cls.async_client[cls.db_name]

        tree = ast.parse((Path(__file__).parent/"server.py").read_text(encoding="utf-8"))
        auth = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                and node.name == "require_active_user"]
        assert len(auth) == 1
        ns = {"db": cls.async_db, "Optional": Optional, "Header": Header,
              "HTTPException": HTTPException, "datetime": datetime, "timedelta": timedelta}
        exec(compile(ast.Module(body=auth, type_ignores=[]), "server.auth", "exec"), ns)
        cls.api = FastAPI()
        cls.api.include_router(build_tenant_router(cls.async_db, ns["require_active_user"]), prefix="/api")
        cls.api.include_router(build_tenant_workflow_router(cls.async_db, ns["require_active_user"]), prefix="/api")
        cls.http = TestClient(cls.api)
        cls.http.__enter__()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.http.__exit__(None, None, None)
            cls.async_client.close()
        finally:
            assert cls.db_name.startswith("restop_tenant_qa_")
            cls.mongo.drop_database(cls.db_name)
            cls.mongo.close()

    def call(self, user, method, path, data=None):
        return self.http.request(method, "/api/tenant"+path,
                                 headers={"Authorization": "Bearer "+user+"-token"}, json=data)

    def supplier(self, user, name):
        response = self.call(user, "POST", "/suppliers", {"name": name})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def product(self, user, name, supplier, cents=250):
        response = self.call(user, "POST", "/products", {
            "name": name, "unit": "kg", "purchase_price_cents": cents,
            "supplier_id": supplier})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def test_a_no_anonymous_or_non_tenant_and_role_boundaries(self):
        self.assertEqual(self.http.get("/api/tenant/recipes").status_code, 401)
        self.assertEqual(self.call("legacy", "GET", "/recipes").status_code, 403)
        self.assertEqual(self.call("legacy", "POST", "/z-reports", {}).status_code, 403)
        self.assertEqual(self.call("cashier", "GET", "/recipes").status_code, 403)
        self.assertEqual(self.call("employee", "GET", "/recipes").status_code, 403)
        self.assertEqual(self.call("chef", "GET", "/z-reports").status_code, 403)
        self.assertEqual(self.call("cashier", "GET", "/z-reports").status_code, 200)
        self.assertEqual(self.call("chef", "GET", "/purchase-orders").status_code, 200)
        self.assertEqual(self.call("cashier", "GET", "/purchase-orders").status_code, 403)

    def test_b_recipe_validates_ingredients_cost_and_cross_tenant_access(self):
        s_a = self.supplier("a", "Maraîcher A")
        s_b = self.supplier("b", "Maraîcher B")
        p_a = self.product("a", "Tomate A", s_a, 333)
        p_b = self.product("b", "Tomate B", s_b, 500)
        draft = {"name": "Sauce tomate", "yield_portions": 3, "sale_price_cents": 1500,
                 "ingredients": [{"product_id": p_a, "quantity_milliunits": 1500}]}
        foreign = {**draft, "ingredients": [{"product_id": p_b, "quantity_milliunits": 1000}]}
        self.assertEqual(self.call("a", "POST", "/recipes", foreign).status_code, 404)
        forged = {**draft, "restaurant_id": "restaurant_B"}
        self.assertEqual(self.call("a", "POST", "/recipes", forged).status_code, 422)
        dup = {**draft, "ingredients": draft["ingredients"] * 2}
        self.assertEqual(self.call("a", "POST", "/recipes", dup).status_code, 422)
        created = self.call("a", "POST", "/recipes", draft)
        self.assertEqual(created.status_code, 201, created.text)
        recipe = created.json()
        self.assertEqual(recipe["cost_snapshot_cents"], 500)  # 333 * 1.5, half-up
        self.assertEqual(recipe["cost_per_portion_snapshot_cents"], 167)
        self.assertEqual(recipe["ingredients"][0]["price_snapshot_cents"], 333)
        self.assertEqual(self.call("b", "GET", "/recipes/"+recipe["id"]).status_code, 404)
        self.assertEqual(self.call("b", "GET", "/recipes").json(), [])
        self.assertEqual(len(self.call("a", "GET", "/recipes").json()), 1)
        self.assertEqual(self.sync_db.recettes.count_documents({}), 0)

    def test_c_order_draft_is_internal_and_fully_supplier_scoped(self):
        s_a = self.supplier("a", "Viandes A")
        s_b = self.supplier("b", "Viandes B")
        p_a = self.product("a", "Boeuf", s_a, 900)
        p_b = self.product("b", "Boeuf", s_b, 1100)
        body = {"supplier_id": s_a, "lines": [
            {"product_id": p_a, "quantity_milliunits": 2500, "unit_price_cents": 950}],
            "note": "À valider par le gérant"}
        other_supplier = {**body, "supplier_id": s_b}
        self.assertEqual(self.call("a", "POST", "/purchase-orders", other_supplier).status_code, 404)
        foreign_product = {**body, "lines": [
            {"product_id": p_b, "quantity_milliunits": 1000, "unit_price_cents": 1000}]}
        self.assertEqual(self.call("a", "POST", "/purchase-orders", foreign_product).status_code, 404)
        forged = {**body, "status": "submitted", "restaurant_id": "restaurant_B"}
        self.assertEqual(self.call("a", "POST", "/purchase-orders", forged).status_code, 422)
        created = self.call("a", "POST", "/purchase-orders", body)
        self.assertEqual(created.status_code, 201, created.text)
        order = created.json()
        self.assertEqual(order["status"], "draft")
        self.assertEqual(order["estimated_total_cents"], 2375)
        self.assertEqual(self.call("b", "GET", "/purchase-orders/"+order["id"]).status_code, 404)
        self.assertEqual(self.call("b", "GET", "/purchase-orders").json(), [])
        self.assertEqual(len(self.call("a", "GET", "/purchase-orders").json()), 1)
        self.assertEqual(self.sync_db.orders.count_documents({}), 0)
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({}), 0)

    def test_d_z_closure_is_casher_scoped_validated_and_idempotent(self):
        body = {"report_reference": "Z-2026-10-16-caisse1", "report_date": "2026-10-16",
                "total_cents": 12000, "cash_cents": 4000, "card_cents": 7000,
                "other_cents": 1000}
        bad = {**body, "cash_cents": 3999}
        self.assertEqual(self.call("cashier", "POST", "/z-reports", bad).status_code, 422)
        forged = {**body, "restaurant_id": "restaurant_B"}
        self.assertEqual(self.call("cashier", "POST", "/z-reports", forged).status_code, 422)
        self.assertEqual(self.call("chef", "POST", "/z-reports", body).status_code, 403)
        first = self.call("cashier", "POST", "/z-reports", body)
        self.assertEqual(first.status_code, 201, first.text)
        self.assertFalse(first.json()["replayed"])
        rid = first.json()["report"]["id"]
        again = self.call("cashier", "POST", "/z-reports", body)
        self.assertEqual(again.status_code, 201, again.text)
        self.assertTrue(again.json()["replayed"])
        self.assertEqual(first.json()["report"]["id"], again.json()["report"]["id"])
        self.assertEqual(self.call("cashier", "POST", "/z-reports",
                                   {**body, "cash_cents": 5000, "card_cents": 6000}
                                   ).status_code, 409)
        self.assertEqual(self.call("b", "GET", "/z-reports/"+rid).status_code, 404)
        self.assertEqual(self.call("b", "GET", "/z-reports").json(), [])
        self.assertEqual(self.call("b", "POST", "/z-reports", body).status_code, 201)
        self.assertEqual(self.sync_db.tenant_z_reports.count_documents({}), 2)
        self.assertEqual(self.sync_db.rapports_z.count_documents({}), 0)

if __name__ == "__main__":
    unittest.main()
