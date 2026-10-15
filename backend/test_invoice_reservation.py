"""Lightweight concurrency contract, independent of MongoDB and external OCR SDKs."""
import asyncio
from datetime import datetime
import unittest
from invoice_guard import reserve_invoice_for_import


class MemoryDocuments:
    def __init__(self):
        self.docs = {'a': {'id':'a','type_document':'facture_fournisseur','statut':'traite'}}
        self.lock = asyncio.Lock()

    async def find_one_and_update(self, query, update):
        async with self.lock:
            doc = self.docs.get(query['id'])
            if doc is None or doc['type_document'] != query['type_document']:
                return None
            if doc['statut'] in query['statut']['$nin']:
                return None
            old = dict(doc)
            doc.update(update['$set'])
            return old


class ReservationTests(unittest.TestCase):
    def test_concurrent_imports_only_one_reservation(self):
        async def scenario():
            docs = MemoryDocuments()
            results = await asyncio.gather(*[
                reserve_invoice_for_import(docs, 'a', datetime.utcnow()) for _ in range(25)
            ])
            return results, docs
        results, docs = asyncio.run(scenario())
        self.assertEqual(sum(bool(result) for result in results), 1)
        self.assertEqual(docs.docs['a']['statut'], 'import_en_cours')

    def test_block_incomplete_or_integrated_import(self):
        async def scenario(status):
            docs = MemoryDocuments()
            docs.docs['a']['statut'] = status
            return await reserve_invoice_for_import(docs, 'a', datetime.utcnow())
        for status in ('integre', 'import_en_cours', 'import_incomplet'):
            self.assertIsNone(asyncio.run(scenario(status)))


if __name__ == '__main__':
    unittest.main()
