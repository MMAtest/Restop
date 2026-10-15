"""Fast, dependency-free regression gates for legacy RESTOP route security.

This file checks the real AST and executes guard functions with fake collections.
It is intentionally NOT a substitute for live MongoDB and end-to-end FastAPI tests.
"""
import ast
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import unittest

SOURCE = (Path(__file__).parent / "server.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
PREFIXES = (
    "/supplier-product-info", "/product-batches", "/price-anomalies", "/stock/",
    "/stock-preparations", "/stocks", "/analytics", "/fournisseurs",
    "/supplier-cost-config", "/suppliers/", "/orders", "/preparations", "/produits",
    "/mouvements", "/recettes", "/rapports_z", "/archive", "/archives",
    "/restore", "/missions", "/notifications", "/dashboard",
    "/formes-decoupe", "/categories-production", "/unites", "/convert-unite",
    "/export/", "/import/", "/demo/"
)

class FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        super().__init__(detail)

class FakeCollection:
    async def find_one(self, query):
        if "session_id" in query:
            return {"user_id": "user-1", "login_time": datetime.utcnow()}
        if "is_active" in query:
            return {"id": "user-1", "is_active": True, "role": "patron"}
        return None

class FakeDB:
    user_sessions = FakeCollection()
    users = FakeCollection()

def real_guards():
    allowed = {
        "require_active_user", "require_legacy_restaurant_reader",
        "require_legacy_restaurant_editor", "require_legacy_restaurant_manager",
        "require_legacy_restaurant_cashier"
    }
    chosen = [node for node in TREE.body
              if isinstance(node, ast.AsyncFunctionDef) and node.name in allowed]
    scope = {
        "Optional": Optional, "Header": lambda default=None: default,
        "Depends": lambda dependency: None, "HTTPException": FakeHTTPException,
        "db": FakeDB, "datetime": datetime, "timedelta": timedelta
    }
    exec(compile(ast.Module(body=chosen, type_ignores=[]), "server.guards", "exec"), scope)
    return scope

def decorator_path(deco):
    if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
        return None
    if not deco.args or not isinstance(deco.args[0], ast.Str):
        return None
    return deco.args[0].s

def decorated_guard(deco):
    keyword = next((k for k in deco.keywords if k.arg == "dependencies"), None)
    if keyword is None or not isinstance(keyword.value, ast.List):
        return None
    return ast.dump(keyword.value)

class LegacyGuardTests(unittest.TestCase):
    def test_no_session_does_not_enter_legacy_api(self):
        guards = real_guards()
        with self.assertRaises(FakeHTTPException) as caught:
            asyncio.run(guards["require_active_user"](None))
        self.assertEqual(caught.exception.status_code, 401)

    def test_tenant_scoped_accounts_fail_closed(self):
        guards = real_guards()
        caller = {"id": "user-1", "role": "patron", "restaurant_id": "restaurant-1"}
        with self.assertRaises(FakeHTTPException) as caught:
            asyncio.run(guards["require_legacy_restaurant_reader"](caller))
        self.assertEqual(caught.exception.status_code, 503)

    def test_role_matrix(self):
        guards = real_guards()
        self.assertEqual(asyncio.run(guards["require_legacy_restaurant_reader"](
            {"id": "user-1", "role": "employe_cuisine"}))["id"], "user-1")
        for role in ("employe_cuisine", "caissier", "barman"):
            with self.subTest(role=role), self.assertRaises(FakeHTTPException) as caught:
                asyncio.run(guards["require_legacy_restaurant_editor"]({"role": role}))
            self.assertEqual(caught.exception.status_code, 403)
        with self.assertRaises(FakeHTTPException) as caught:
            asyncio.run(guards["require_legacy_restaurant_manager"](
                {"role": "chef_cuisine"}))
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(asyncio.run(guards["require_legacy_restaurant_cashier"](
            {"role": "caissier"}))["role"], "caissier")

    def test_route_decorators_have_server_side_dependencies(self):
        seen = []
        for node in TREE.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for deco in node.decorator_list:
                path = decorator_path(deco)
                if path is None or not path.startswith(PREFIXES):
                    continue
                seen.append(path)
                name = decorated_guard(deco)
                self.assertTrue(name, "Missing route guard for " + path)
                if path.startswith("/demo/"):
                    self.assertIn("require_legacy_restaurant_manager", name)
                if path == "/rapports_z" and deco.func.attr == "post":
                    self.assertIn("require_legacy_restaurant_cashier", name)
                if deco.func.attr == "delete":
                    self.assertIn("require_legacy_restaurant_manager", name)
        self.assertGreaterEqual(len(seen), 90)

    def test_owner_checks_present_on_sensitive_mission_routes(self):
        functions = {
            node.name: ast.dump(node)
            for node in TREE.body if isinstance(node, ast.AsyncFunctionDef)
        }
        for name in ("create_mission", "get_missions", "get_missions_by_user",
                     "update_mission", "get_user_notifications", "mark_notification_read"):
            self.assertIn("editor", functions[name])
        self.assertIn("assigned_by_user_id", functions["create_mission"])
        self.assertIn("assigned_to_user_id", functions["get_missions"])
        self.assertIn("user_id", functions["get_user_notifications"])
        self.assertIn("user_id", functions["mark_notification_read"])

    def test_preparation_archive_type_supported(self):
        functions = {
            node.name: ast.dump(node)
            for node in TREE.body if isinstance(node, ast.AsyncFunctionDef)
        }
        self.assertIn("preparation", functions["archive_item"])
        self.assertIn("preparation", functions["restore_item"])

if __name__ == "__main__":
    unittest.main()
