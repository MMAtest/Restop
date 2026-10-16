"""Real MongoDB replica-set isolation test, intentionally OFF by default.

Run ONLY on an isolated MongoDB QA container:
 RESTOP_TEST_TENANT_MONGO_URL=mongodb://localhost:27017/?directConnection=true&replicaSet=rsrestopQA \\
   python -m unittest test_tenant_mongo_integration -v
Every test creates/drops a random database prefixed restop_tenant_qa_.
"""
import ast
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4
import unittest

# Third-party dependencies are intentionally imported only when a test QA URL
# is explicitly supplied. Ordinary unittest discovery stays side-effect-free.
QA_URL = os.getenv('RESTOP_TEST_TENANT_MONGO_URL')


@unittest.skipUnless(QA_URL, 'Requires explicit isolated QA Mongo URL')
class RealTenantMongoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi import FastAPI, Header, HTTPException
        from fastapi.testclient import TestClient
        from motor.motor_asyncio import AsyncIOMotorClient
        from pymongo import MongoClient
        from tenant_stock_api import build_tenant_router
        cls.db_name = 'restop_tenant_qa_' + uuid4().hex[:16]
        assert cls.db_name.startswith('restop_tenant_qa_')
        cls.sync = MongoClient(QA_URL, serverSelectionTimeoutMS=5000)
        hello = cls.sync.admin.command('hello')
        if not hello.get('setName'):
            raise RuntimeError('QA MongoDB MUST be a replica set for atomic stock writes')
        cls.sync_db = cls.sync[cls.db_name]
        cls.sync_db.users.insert_many([
            {'id':'alice','restaurant_id':'restaurant_A','role':'patron','is_active':True},
            {'id':'bob','restaurant_id':'restaurant_B','role':'patron','is_active':True},
            {'id':'employee','restaurant_id':'restaurant_A','role':'employe_cuisine','is_active':True},
            {'id':'cashier','restaurant_id':'restaurant_A','role':'caissier','is_active':True},
            {'id':'legacy','role':'super_admin','is_active':True},
        ])
        cls.sync_db.user_sessions.insert_many([
            {'session_id':name+'-token','user_id':name,'login_time':datetime.utcnow()}
            for name in ['alice','bob','employee','cashier','legacy']
        ])
        cls.async_mongo = AsyncIOMotorClient(QA_URL, serverSelectionTimeoutMS=5000)
        cls.async_db = cls.async_mongo[cls.db_name]

        # Execute the REAL session-verification function from server.py, not
        # a fake authenticated-user dependency. Importing server.py directly
        # requires unrelated third-party OCR SDKs so select the AST function.
        tree=ast.parse((Path(__file__).parent/'server.py').read_text(encoding='utf-8'))
        auth=[node for node in tree.body if isinstance(node,ast.AsyncFunctionDef) and node.name=='require_active_user']
        assert len(auth)==1
        namespace={'db':cls.async_db,'Optional':Optional,'Header':Header,'HTTPException':HTTPException,
                   'datetime':datetime,'timedelta':timedelta}
        exec(compile(ast.Module(body=auth,type_ignores=[]),'server.auth','exec'),namespace)
        app=FastAPI()
        app.include_router(build_tenant_router(cls.async_db,namespace['require_active_user']),prefix='/api')
        # Failure injection shares the exact same TestClient and asyncio loop.
        # Motor clients cannot be used on separate TestClient event loops.
        from pymongo.errors import PyMongoError
        class BrokenMovementCollection:
            async def find_one(self,*args,**kwargs):
                return await cls.async_db.tenant_stock_movements.find_one(*args,**kwargs)
            async def insert_one(self,*args,**kwargs):
                raise PyMongoError('injected post-stock failure')
        class BrokenDB:
            def __getattr__(self,name):
                return BrokenMovementCollection() if name=='tenant_stock_movements' else getattr(cls.async_db,name)
        app.include_router(build_tenant_router(BrokenDB(),namespace['require_active_user']),prefix='/api/qa-failure')
        cls.http_client=TestClient(app)
        cls.http_client.__enter__()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.http_client.__exit__(None,None,None)
            cls.async_mongo.close()
        finally:
            assert cls.db_name.startswith('restop_tenant_qa_')
            cls.sync.drop_database(cls.db_name)
            cls.sync.close()

    def request(self, identity, verb, path, body=None):
        headers={'Authorization':'Bearer '+identity+'-token'}
        return self.http_client.request(verb,'/api/tenant'+path,headers=headers,json=body)

    def create_supplier(self, identity, name):
        res=self.request(identity,'POST','/suppliers',{'name':name})
        self.assertEqual(res.status_code,201,res.text)
        return res.json()['id']

    def create_product(self, identity, name, supplier=None):
        res=self.request(identity,'POST','/products',{'name':name,'supplier_id':supplier,
            'unit':'kg','purchase_price_cents':320})
        self.assertEqual(res.status_code,201,res.text)
        return res.json()['id']

    def stock_adjust(self, identity, product_id, delta, key, reason='Inventaire test'):
        return self.request(identity,'POST','/stock/adjustments',{'product_id':product_id,
            'delta_milliunits':delta,'idempotency_key':key,'reason':reason})

    def test_transaction_rolls_back_when_movement_insert_fails(self):
        # Failure is injected AFTER writing stock in a real Mongo transaction.
        # No stock adjustment nor movement may persist.
        pid=self.create_product('alice','Rollback test')
        response=self.http_client.post('/api/qa-failure/tenant/stock/adjustments',
            headers={'Authorization':'Bearer alice-token'},
            json={'product_id':pid,'delta_milliunits':2500,
                  'idempotency_key':'rollback-qa-12345','reason':'simulated failure'})
        self.assertEqual(response.status_code,503,response.text)
        self.assertEqual(self.sync_db.tenant_stocks.count_documents({'restaurant_id':'restaurant_A','product_id':pid}),0)
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({'restaurant_id':'restaurant_A','product_id':pid}),0)

    def test_revoked_and_expired_sessions_are_denied(self):
        self.sync_db.user_sessions.insert_one({'session_id':'expired-token','user_id':'employee',
             'login_time':datetime.utcnow()-timedelta(hours=13)})
        expired=self.http_client.get('/api/tenant/products',headers={'Authorization':'Bearer expired-token'})
        self.assertEqual(expired.status_code,401)
        self.assertEqual(self.sync_db.user_sessions.count_documents({'session_id':'expired-token'}),0)
        self.sync_db.users.update_one({'id':'employee'},{'$set':{'is_active':False}})
        disabled=self.request('employee','GET','/products')
        self.assertEqual(disabled.status_code,401)
        self.sync_db.users.update_one({'id':'employee'},{'$set':{'is_active':True}})

    def test_tenant_stock_isolation_and_atomic_adjustments(self):
        # A and B may use the same supplier names, product names and prices,
        # but must receive different rows and observe no external resources.
        supplier_a=self.create_supplier('alice','Primeur commun')
        supplier_b=self.create_supplier('bob','Primeur commun')
        product_a=self.create_product('alice','Tomates',supplier_a)
        product_b=self.create_product('bob','Tomates',supplier_b)

        self.assertEqual(self.request('alice','GET','/products').status_code,200)
        listing_a=self.request('alice','GET','/products').json()
        listing_b=self.request('bob','GET','/products').json()
        self.assertIn(product_a,[p['id'] for p in listing_a])
        self.assertNotIn(product_b,[p['id'] for p in listing_a])
        self.assertIn(product_b,[p['id'] for p in listing_b])
        self.assertNotIn(product_a,[p['id'] for p in listing_b])
        self.assertEqual(self.request('bob','GET','/products/'+product_a).status_code,404)
        self.assertEqual(self.request('alice','GET','/products/'+product_b).status_code,404)
        self.assertEqual(self.request('alice','POST','/products',
            {'name':'False external supplier','supplier_id':supplier_b,'unit':'kg','purchase_price_cents':210}).status_code,404)
        self.assertEqual(self.stock_adjust('alice',product_b,1000,'foreign-write-123456').status_code,404)
        self.assertEqual(self.stock_adjust('bob',product_a,1000,'foreign-write-234567').status_code,404)
        self.assertEqual(self.request('alice','GET','/stock').json(),[])
        self.assertEqual(self.request('bob','GET','/stock').json(),[])

        result=self.stock_adjust('alice',product_a,4500,'inventory-key-001')
        self.assertEqual(result.status_code,201,result.text)
        self.assertEqual(result.json()['quantity_milliunits'],4500)
        again=self.stock_adjust('alice',product_a,4500,'inventory-key-001')
        self.assertEqual(again.status_code,201,again.text)
        self.assertTrue(again.json()['replayed'])
        self.assertEqual(again.json()['quantity_milliunits'],4500)
        self.assertEqual(self.stock_adjust('alice',product_a,1000,'inventory-key-001').status_code,409)
        self.assertEqual(self.stock_adjust('alice',product_a,-6000,'inventory-key-002').status_code,409)
        self.assertEqual(self.request('alice','GET','/stock').json()[0]['quantity_milliunits'],4500)
        self.assertEqual(self.request('bob','GET','/stock').json(),[])
        self.assertEqual(len(self.request('alice','GET','/stock/movements').json()),1)
        self.assertEqual(len(self.request('bob','GET','/stock/movements').json()),0)

        self.assertEqual(self.stock_adjust('bob',product_b,1250,'inventory-key-001').status_code,201)
        self.assertEqual(self.request('bob','GET','/stock').json()[0]['quantity_milliunits'],1250)
        self.assertEqual(self.request('alice','GET','/stock').json()[0]['quantity_milliunits'],4500)

        # Only tenant-scoped collections created. No legacy product was inserted.
        self.assertEqual(self.sync_db.produits.count_documents({}),0)
        self.assertEqual(self.sync_db.stocks.count_documents({}),0)
        self.assertEqual(self.sync_db.tenant_stock_movements.count_documents({}),2)

    def test_authentication_and_roles_from_persisted_session(self):
        no_token=self.http_client.get('/api/tenant/products')
        self.assertEqual(no_token.status_code,401)
        forged_role=self.http_client.post('/api/tenant/products',
            headers={'Authorization':'Bearer employee-token','X-Role':'patron'},
            json={'name':'Interdit','unit':'kg','purchase_price_cents':300})
        self.assertEqual(forged_role.status_code,403)
        self.assertEqual(self.request('cashier','POST','/suppliers',{'name':'Interdit'}).status_code,403)
        # Never trust client-supplied restaurant claims or owner IDs.
        self.assertEqual(self.request('bob','POST','/products',
            {'name':'Injection A','restaurant_id':'restaurant_A','unit':'kg',
             'purchase_price_cents':100}).status_code,422)
        self.assertEqual(self.request('alice','POST','/suppliers',
            {'name':'Supplier A','restaurant_id':'restaurant_B'}).status_code,422)
        self.assertEqual(self.request('bob','POST','/products',
            {'name':'Type invalide','unit':'kg','purchase_price_cents':'199'}).status_code,422)
        self.assertEqual(self.request('employee','GET','/products').status_code,200)
        self.assertEqual(self.request('legacy','GET','/products').status_code,403)
        self.assertEqual(self.request('legacy','POST','/products',
            {'name':'Hors tenant','unit':'kg','purchase_price_cents':100}).status_code,403)
        self.assertEqual(self.sync_db.tenant_products.count_documents({}),0)


if __name__=='__main__':
    unittest.main()
