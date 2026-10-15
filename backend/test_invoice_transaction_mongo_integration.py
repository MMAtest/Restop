"""Optional real MongoDB integration test (requires an isolated test replica set).

Opt-in only: RESTOP_TEST_MONGO_URI and RESTOP_INTEGRATION_TEST_ACK=isolated.
This test creates and deletes a uniquely named test database. NEVER run on prod.
"""
import asyncio
from datetime import datetime
import os
import uuid
import unittest
from invoice_guard import reserve_invoice_for_import, run_stock_transaction, transaction_topology_supported


@unittest.skipUnless(os.getenv('RESTOP_TEST_MONGO_URI') and
                     os.getenv('RESTOP_INTEGRATION_TEST_ACK') == 'isolated',
                     'Needs explicit isolated MongoDB test URI and acknowledgement')
class MongoRealTransactions(unittest.TestCase):
    def test_rollback_commit_and_concurrent_claim(self):
        async def scenario():
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(os.environ['RESTOP_TEST_MONGO_URI'], serverSelectionTimeoutMS=5000)
            db_name = 'restop_txn_ci_' + uuid.uuid4().hex
            db = client[db_name]
            try:
                hello = await db.command('hello')
                self.assertTrue(transaction_topology_supported(hello), 'Need replica set or sharded cluster')
                async def failing(session):
                    await db.produits.insert_one({'id':'p1'}, session=session)
                    await db.stocks.insert_one({'produit_id':'p1','quantite_actuelle':1}, session=session)
                    raise RuntimeError('simulate failure after writes')
                with self.assertRaises(RuntimeError):
                    await run_stock_transaction(client,failing)
                self.assertEqual(await db.produits.count_documents({}),0)
                self.assertEqual(await db.stocks.count_documents({}),0)
                async def success(session):
                    await db.produits.insert_one({'id':'p1'}, session=session)
                    await db.stocks.insert_one({'produit_id':'p1','quantite_actuelle':1}, session=session)
                    return 'ok'
                self.assertEqual(await run_stock_transaction(client,success),'ok')
                self.assertEqual(await db.produits.count_documents({}),1)
                self.assertEqual(await db.stocks.count_documents({}),1)
                await db.documents_ocr.insert_one({'id':'invoice1','type_document':'facture_fournisseur','statut':'traite'})
                attempts = await asyncio.gather(*[
                    reserve_invoice_for_import(db.documents_ocr,'invoice1',datetime.utcnow()) for _ in range(10)
                ])
                self.assertEqual(sum(bool(x) for x in attempts),1)
            finally:
                if db_name.startswith('restop_txn_ci_'):
                    await client.drop_database(db_name)
                client.close()
        asyncio.run(scenario())


if __name__ == '__main__': unittest.main()
