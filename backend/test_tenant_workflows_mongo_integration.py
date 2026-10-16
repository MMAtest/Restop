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
        from tenant_receiving_api import build_receiving_router
        from tenant_invoice_api import build_invoice_router, ensure_invoice_indexes
        from pymongo.errors import PyMongoError

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
        cls.api.include_router(build_receiving_router(cls.async_db, ns["require_active_user"]), prefix="/api")
        cls.api.include_router(build_invoice_router(cls.async_db, ns["require_active_user"]), prefix="/api")
        class BrokenMovements:
            async def insert_one(self, *args, **kwargs):
                raise PyMongoError("injected failure after stock change")
        class BrokenDB:
            def __getattr__(self, key):
                return BrokenMovements() if key == "tenant_stock_movements" else getattr(cls.async_db, key)
        cls.api.include_router(build_receiving_router(BrokenDB(), ns["require_active_user"]), prefix="/api/broken")
        cls.sync_db.tenant_receipts.create_index([("restaurant_id", ASCENDING), ("supplier_id", ASCENDING), ("invoice_reference", ASCENDING)], unique=True)
        cls.sync_db.tenant_invoice_documents.create_index([("restaurant_id", ASCENDING), ("supplier_id", ASCENDING), ("sha256", ASCENDING)], unique=True)
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
        again = self.call("cashier", "POST", "/z-reports", {**body,
                          "report_reference": " z-2026-10-16-caisse1  "})
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

    def receipt_fixture(self, user='a', qty=3000):
        sup=self.supplier(user,'Primeur réception')
        pid=self.product(user,'Tomates livraison',sup,200)
        response=self.call(user,'POST','/purchase-orders',{'supplier_id':sup,'lines':[
            {'product_id':pid,'quantity_milliunits':qty,'unit_price_cents':200}]})
        self.assertEqual(response.status_code,201,response.text)
        return response.json()['id'],pid,sup

    def receipt_body(self,pid,qty=3000,invoice='FAC-TEST-001',key='receipt-unique-001'):
        return {'delivery_note_reference':'BL-TEST-001','invoice_reference':invoice,
            'invoice_source':'human_verified','idempotency_key':key,'lines':[
                {'product_id':pid,'received_milliunits':qty,
                 'invoiced_milliunits':qty,'invoiced_unit_price_cents':200}]}

    def test_e_receiving_preview_guards_and_manual_approval(self):
        oid,pid,_=self.receipt_fixture()
        path='/purchase-orders/'+oid
        body=self.receipt_body(pid,key='preview-only-0001')
        self.assertEqual(self.http.post('/api/tenant'+path+'/receipts/preview',json=body).status_code,401)
        self.assertEqual(self.call('a','POST',path+'/receipts/preview',body).status_code,409)
        self.assertEqual(self.call('b','POST',path+'/approve').status_code,404)
        self.assertEqual(self.call('chef','POST',path+'/approve').status_code,403)
        self.assertEqual(self.call('cashier','POST',path+'/approve').status_code,403)
        self.assertEqual(self.call('a','POST',path+'/approve').status_code,200)
        self.assertEqual(self.call('a','POST',path+'/approve').status_code,409)
        self.assertEqual(self.call('cashier','POST',path+'/receipts/preview',body).status_code,403)
        self.assertEqual(self.call('employee','POST',path+'/receipts/confirm',body).status_code,403)
        self.assertEqual(self.call('b','POST',path+'/receipts/confirm',body).status_code,404)
        res=self.call('chef','POST',path+'/receipts/preview',body)
        self.assertEqual(res.status_code,200,res.text)
        self.assertTrue(res.json()['can_confirm'])
        self.assertEqual(res.json()['invoice_total_cents'],600)
        self.assertEqual(self.sync_db.tenant_stocks.count_documents({'restaurant_id':'restaurant_A','product_id':pid}),0)
        self.assertEqual(self.sync_db.tenant_receipts.count_documents({'restaurant_id':'restaurant_A','order_id':oid}),0)
        for invalid in [
            {**body,'restaurant_id':'restaurant_B'},
            {**body,'invoice_source':'ocr_unchecked'},
            {**body,'lines':body['lines']*2},
            {**body,'lines':[{**body['lines'][0],'received_milliunits':0}]},
        ]:
            self.assertEqual(self.call('a','POST',path+'/receipts/preview',invalid).status_code,422)
        over=self.receipt_body(pid,qty=4000,invoice='FAC-OVER-1',key='overreceipt-0001')
        self.assertEqual(self.call('a','POST',path+'/receipts/confirm',over).status_code,409)

    def test_f_receiving_three_way_variances_idempotency_and_stock(self):
        oid,pid,_=self.receipt_fixture()
        path='/purchase-orders/'+oid
        self.assertEqual(self.call('a','POST',path+'/approve').status_code,200)
        body=self.receipt_body(pid,qty=1200,invoice='FAC-PART-1',key='part-receipt-001')
        body['lines'][0]['invoiced_milliunits']=1500
        body['lines'][0]['invoiced_unit_price_cents']=240
        preview=self.call('a','POST',path+'/receipts/preview',body)
        self.assertEqual(preview.status_code,200,preview.text)
        codes={issue['code'] for issue in preview.json()['issues']}
        self.assertEqual(codes,{'livraison_partielle','quantite_facturee_differente','prix_facture_different'})
        self.assertEqual(preview.json()['invoice_total_cents'],360)
        self.assertFalse(preview.json()['can_confirm'])
        self.assertEqual(self.call('a','POST',path+'/receipts/confirm',body).status_code,409)
        ack={**body,'acknowledge_variances':True,
            'variance_reason':'Contrôle physique effectué par le responsable'}
        receipt=self.call('chef','POST',path+'/receipts/confirm',ack)
        self.assertEqual(receipt.status_code,201,receipt.text)
        rid=receipt.json()['id']
        self.assertEqual(receipt.json()['order_status_after'],'receiving')
        self.assertEqual(self.call('a','GET','/receipts/by-key/part-receipt-001').json()['id'],rid)
        self.assertEqual(self.call('b','GET','/receipts/'+rid).status_code,404)
        self.assertEqual(self.call('b','GET','/receipts').json(),[])
        replay=self.call('a','POST',path+'/receipts/confirm',ack)
        self.assertEqual(replay.status_code,201,replay.text)
        self.assertTrue(replay.json()['replayed'])
        self.assertEqual(self.call('a','POST',path+'/receipts/confirm',
            {**ack,'variance_reason':'justification contradictoire'}).status_code,409)
        self.assertEqual(self.call('a','POST',path+'/receipts/confirm',
            self.receipt_body(pid,qty=100,invoice=' fac-part-1 ',key='duplicate-invoice-01')).status_code,409)
        self.assertEqual(self.call('a','GET','/stock').json()[0]['quantity_milliunits'],1200)
        finish=self.call('a','POST',path+'/receipts/confirm',self.receipt_body(
            pid,qty=1800,invoice='FAC-FIN-1',key='final-receipt-001'))
        self.assertEqual(finish.status_code,201,finish.text)
        self.assertEqual(finish.json()['order_status_after'],'received')
        self.assertEqual(self.call('a','GET','/stock').json()[0]['quantity_milliunits'],3000)
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({'source':'supplier_receipt','restaurant_id':'restaurant_A','product_id':pid}),2)
        self.assertEqual(self.sync_db.tenant_receipts.count_documents({'restaurant_id':'restaurant_A','order_id':oid}),2)
        self.assertEqual(self.sync_db.tenant_purchase_orders.find_one({'id':oid})['receipt_version'],2)
        self.assertEqual(self.call('a','POST',path+'/receipts/confirm',self.receipt_body(
            pid,qty=100,invoice='FAC-LATE-1',key='late-receipt-001')).status_code,409)
        self.assertEqual(self.sync_db.stocks.count_documents({}),0)
        self.assertEqual(self.sync_db.orders.count_documents({}),0)

    def test_g_receiving_rollback_injected_after_stock_write(self):
        oid,pid,_=self.receipt_fixture(qty=1000)
        path='/purchase-orders/'+oid
        self.assertEqual(self.call('a','POST',path+'/approve').status_code,200)
        body=self.receipt_body(pid,qty=1000,invoice='FAC-FAIL-001',key='rollback-key-001')
        failed=self.http.post('/api/broken/tenant'+path+'/receipts/confirm',
            headers={'Authorization':'Bearer a-token'},json=body)
        self.assertEqual(failed.status_code,503,failed.text)
        self.assertEqual(self.sync_db.tenant_stocks.count_documents({'restaurant_id':'restaurant_A','product_id':pid}),0)
        self.assertEqual(self.sync_db.tenant_receipts.count_documents({'restaurant_id':'restaurant_A','order_id':oid}),0)
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({'restaurant_id':'restaurant_A','product_id':pid}),0)
        latest=self.sync_db.tenant_purchase_orders.find_one({'id':oid})
        self.assertEqual(latest['status'],'approved')
        self.assertEqual(latest['receipt_version'],0)
        recovered=self.call('a','POST',path+'/receipts/confirm',body)
        self.assertEqual(recovered.status_code,201,recovered.text)
        self.assertEqual(self.call('a','GET','/stock').json()[-1]['quantity_milliunits'],1000)

    def test_h_concurrent_identical_receipts_never_duplicate_stock(self):
        from concurrent.futures import ThreadPoolExecutor
        oid,pid,_=self.receipt_fixture(qty=1000)
        path='/purchase-orders/'+oid
        self.assertEqual(self.call('a','POST',path+'/approve').status_code,200)
        body=self.receipt_body(pid,qty=1000,invoice='FAC-CONCURRENT-001',key='concurrent-key-0001')
        with ThreadPoolExecutor(max_workers=2) as pool:
            calls=[pool.submit(self.call,'a','POST',path+'/receipts/confirm',body) for _ in range(2)]
            results=[f.result() for f in calls]
        self.assertTrue(all(r.status_code in (201,409) for r in results),[(r.status_code,r.text) for r in results])
        self.assertTrue(any(r.status_code==201 for r in results))
        db_stock=self.sync_db.tenant_stocks.find_one({'restaurant_id':'restaurant_A','product_id':pid})
        self.assertEqual(db_stock['quantity_milliunits'],1000)
        self.assertEqual(self.sync_db.tenant_receipts.count_documents({'restaurant_id':'restaurant_A','order_id':oid}),1)
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({'restaurant_id':'restaurant_A','product_id':pid,'source':'supplier_receipt'}),1)
        self.assertEqual(self.sync_db.tenant_purchase_orders.find_one({'id':oid})['receipt_version'],1)

    def qa_pdf(self, reference='INV-PDF-001'):
        from io import BytesIO
        from reportlab.pdfgen import canvas
        data=BytesIO()
        pdf=canvas.Canvas(data)
        pdf.drawString(80,760, 'FACTURE N '+reference)
        pdf.drawString(80,734, 'Tomates Provence quantite 3 kg prix 2 euros')
        pdf.showPage()
        pdf.save()
        return data.getvalue()

    def invoice_upload(self,identity,order_id,content=None,filename='facture.pdf'):
        return self.http.post('/api/tenant/invoices/upload',
            params={'order_id':order_id},
            headers={'Authorization':'Bearer '+identity+'-token'},
            files={'file':(filename,content if content is not None else self.qa_pdf(),'application/pdf')})

    def test_i_invoice_pdf_extraction_isolation_and_tamper_guards(self):
        import hashlib
        oid,pid,sup=self.receipt_fixture()
        self.assertEqual(self.call('a','POST','/purchase-orders/'+oid+'/approve').status_code,200)
        pdf=self.qa_pdf('INV-PDF-001')
        uploaded=self.invoice_upload('a',oid,pdf)
        self.assertEqual(uploaded.status_code,201,uploaded.text)
        doc=uploaded.json()
        did=doc['id']
        self.assertEqual(doc['status'],'needs_review')
        self.assertEqual(doc['sha256'],hashlib.sha256(pdf).hexdigest())
        self.assertEqual(doc['extraction_engine'],'pdf_embedded_text')
        self.assertTrue(doc['extracted_chars']>0)
        self.assertEqual(doc['suggestions'].get('invoice_reference'),'INV-PDF-001')
        self.assertNotIn('extracted_text',doc)
        detail=self.call('a','GET','/invoices/'+did)
        self.assertEqual(detail.status_code,200)
        self.assertIn('INV-PDF-001',detail.json()['extracted_text'])
        self.assertEqual(self.call('b','GET','/invoices/'+did).status_code,404)
        self.assertEqual(self.call('b','GET','/invoices/'+did+'/file').status_code,404)
        self.assertEqual(self.call('cashier','GET','/invoices/'+did).status_code,403)
        self.assertEqual(self.http.get('/api/tenant/invoices/'+did).status_code,401)
        original=self.call('a','GET','/invoices/'+did+'/file')
        self.assertEqual(original.status_code,200)
        self.assertEqual(original.content,pdf)
        self.assertEqual(original.headers['cache-control'],'no-store')
        self.assertEqual(self.http.get('/api/tenant/invoices',params={'order_id':oid},headers={'Authorization':'Bearer a-token'}).status_code,200)
        listed=self.http.get('/api/tenant/invoices',params={'order_id':oid},headers={'Authorization':'Bearer a-token'}).json()
        self.assertNotIn('extracted_text',listed[0])
        self.assertEqual(self.invoice_upload('a',oid,pdf).status_code,409)
        self.assertEqual(self.invoice_upload('b',oid,pdf).status_code,404)
        self.assertEqual(self.invoice_upload('a',oid,b'plain text that is not a PDF').status_code,422)
        self.assertEqual(self.invoice_upload('a',oid,b'%PDF-'+b'A'*(8*1024*1024),filename='oversize.pdf').status_code,413)
        body=self.receipt_body(pid,invoice='INV-PDF-001',key='invoice-doc-001')
        body['invoice_document_id']=did
        self.assertEqual(self.call('a','POST','/purchase-orders/'+oid+'/receipts/preview',body).status_code,409)
        wrong={'invoice_reference':'INV-PDF-001','lines':[{'product_id':'other-product','invoiced_milliunits':3000,'invoiced_unit_price_cents':200}],
               'review_note':'Vérification de la facture'}
        self.assertEqual(self.call('a','POST','/invoices/'+did+'/review',wrong).status_code,422)
        review={'invoice_reference':'INV-PDF-001','lines':[{'product_id':pid,'invoiced_milliunits':3000,'invoiced_unit_price_cents':200}],
                'review_note':'Toutes les données contrôlées manuellement'}
        check=self.call('chef','POST','/invoices/'+did+'/review',review)
        self.assertEqual(check.status_code,200,check.text)
        self.assertEqual(check.json()['status'],'reviewed')
        self.assertEqual(self.call('chef','POST','/invoices/'+did+'/review',review).status_code,409)
        mismatch={**body,'lines':[dict(body['lines'][0],invoiced_unit_price_cents=240)]}
        self.assertEqual(self.call('a','POST','/purchase-orders/'+oid+'/receipts/confirm',mismatch).status_code,409)
        self.assertEqual(self.sync_db.tenant_stocks.count_documents({'restaurant_id':'restaurant_A','product_id':pid}),0)
        ok=self.call('a','POST','/purchase-orders/'+oid+'/receipts/confirm',body)
        self.assertEqual(ok.status_code,201,ok.text)
        self.assertEqual(ok.json()['invoice_document_id'],did)
        self.assertEqual(ok.json()['invoice_sha256'],hashlib.sha256(pdf).hexdigest())
        doc_after=self.call('a','GET','/invoices/'+did)
        self.assertEqual(doc_after.json()['status'],'received')
        self.assertEqual(doc_after.json()['receipt_id'],ok.json()['id'])
        replay=self.call('a','POST','/purchase-orders/'+oid+'/receipts/confirm',body)
        self.assertEqual(replay.status_code,201,replay.text)
        self.assertTrue(replay.json()['replayed'])
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({'restaurant_id':'restaurant_A','product_id':pid,'source':'supplier_receipt'}),1)

    def test_j_invoice_document_claim_rolls_back_with_stock(self):
        oid,pid,_=self.receipt_fixture(qty=1000)
        self.assertEqual(self.call('a','POST','/purchase-orders/'+oid+'/approve').status_code,200)
        doc=self.invoice_upload('a',oid,self.qa_pdf('INV-ROLLBACK-01'))
        self.assertEqual(doc.status_code,201,doc.text)
        did=doc.json()['id']
        review={'invoice_reference':'INV-ROLLBACK-01','lines':[{'product_id':pid,'invoiced_milliunits':1000,'invoiced_unit_price_cents':200}],
            'review_note':'Quantité, prix et référence vérifiés'}
        self.assertEqual(self.call('a','POST','/invoices/'+did+'/review',review).status_code,200)
        body=self.receipt_body(pid,qty=1000,invoice='INV-ROLLBACK-01',key='doc-rollback-key-01')
        body['invoice_document_id']=did
        failure=self.http.post('/api/broken/tenant/purchase-orders/'+oid+'/receipts/confirm',
            headers={'Authorization':'Bearer a-token'},json=body)
        self.assertEqual(failure.status_code,503,failure.text)
        self.assertEqual(self.call('a','GET','/invoices/'+did).json()['status'],'reviewed')
        self.assertEqual(self.sync_db.tenant_receipts.count_documents({'order_id':oid}),0)
        self.assertEqual(self.sync_db.tenant_stocks.count_documents({'product_id':pid}),0)
        self.assertEqual(self.call('a','POST','/purchase-orders/'+oid+'/receipts/confirm',body).status_code,201)

    def test_k_png_and_scanned_pdf_are_retained_for_review(self):
        from io import BytesIO
        from PIL import Image, ImageDraw, ImageFont
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        oid,pid,_=self.receipt_fixture(qty=1000)
        self.assertEqual(self.call('a','POST','/purchase-orders/'+oid+'/approve').status_code,200)
        img=Image.new('RGB',(1180,300),'white')
        paint=ImageDraw.Draw(img)
        try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',42)
        except OSError:font=ImageFont.load_default()
        paint.text((50,90),'FACTURE N IMAGE-4242',fill='black',font=font)
        out=BytesIO();img.save(out,format='PNG');png=out.getvalue()
        uploaded=self.invoice_upload('a',oid,png,filename='facture-image.png')
        self.assertEqual(uploaded.status_code,201,uploaded.text)
        doc=uploaded.json()
        self.assertEqual(doc['media_type'],'image/png')
        self.assertIn(doc['extraction_engine'],('tesseract_image','ocr_engine_unavailable'))
        self.assertEqual(doc['status'],'needs_review')
        self.assertEqual(self.call('a','GET','/invoices/'+doc['id']+'/file').content,png)
        self.assertEqual(self.call('b','GET','/invoices/'+doc['id']).status_code,404)
        # An image-only PDF should never be treated as a validated invoice.
        pdf_bytes=BytesIO();pdf=canvas.Canvas(pdf_bytes)
        pdf.drawImage(ImageReader(img),20,570,width=590,height=150)
        pdf.showPage();pdf.save()
        scanned=self.invoice_upload('a',oid,pdf_bytes.getvalue())
        self.assertEqual(scanned.status_code,201,scanned.text)
        self.assertIn(scanned.json()['extraction_engine'],('pdf_scanned_tesseract','ocr_engine_unavailable','pdf_no_text','pdf_scanned_ocr_unavailable'))
        self.assertEqual(scanned.json()['status'],'needs_review')
        self.assertEqual(self.sync_db.tenant_receipts.count_documents({'order_id':oid}),0)
        self.assertEqual(self.sync_db.tenant_stocks.count_documents({'product_id':pid}),0)

if __name__ == "__main__":
    unittest.main()
