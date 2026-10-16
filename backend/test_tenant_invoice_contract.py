"""Dependency-free API invariants for tenant-local immutable invoice documents."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class InvoiceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT/'tenant_invoice_api.py').read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.source)

    def test_disabled_by_default_and_indexes(self):
        server = (ROOT/'server.py').read_text(encoding='utf-8')
        self.assertIn('if os.getenv("RESTOP_ENABLE_TENANT_V2") == "1":', server)
        self.assertIn('build_invoice_router(db, require_active_user)', server)
        self.assertIn('await ensure_invoice_indexes(db)', server)
        for name in ('tenant_invoice_documents','tenant_invoice_files','sha256','restaurant_id'):
            self.assertIn(name, self.source)

    def test_every_route_authenticates_and_tenant_is_never_client_claimed(self):
        builder = next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_invoice_router')
        paths = []
        for fn in ast.walk(builder):
            if not isinstance(fn,ast.AsyncFunctionDef): continue
            for deco in fn.decorator_list:
                if not isinstance(deco,ast.Call) or not isinstance(deco.func,ast.Attribute):continue
                if deco.func.attr not in ('post','get','delete','put','patch'):continue
                paths.append(fn.name)
                self.assertIn('Depends',ast.dump(fn.args),fn.name)
                self.assertIn('invoice_editor',ast.dump(fn.args),fn.name)
                self.assertNotIn('restaurant_id',[x.arg for x in fn.args.args],fn.name)
        self.assertGreaterEqual(len(paths),5)
        self.assertNotIn('delete_invoice',paths)

    def test_no_legacy_collections_or_automatic_stock_mutation(self):
        attrs=[]
        for node in ast.walk(self.tree):
            if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='db':
                attrs.append(node.attr)
        self.assertTrue(attrs)
        self.assertTrue(all(a.startswith('tenant_') or a=='client' for a in attrs),attrs)
        self.assertNotIn('tenant_stocks',attrs)
        self.assertIn("'status': 'needs_review'",self.source)
        self.assertIn("'status': 'reviewed'",self.source)

    def test_original_not_exposed_in_metadata_and_download_has_no_sniff(self):
        self.assertIn("if k not in ('_id', 'extracted_text')",self.source)
        self.assertIn("'X-Content-Type-Options': 'nosniff'",self.source)
        self.assertIn("'Cache-Control': 'no-store'",self.source)
        self.assertIn('MAX_INVOICE_BYTES = 8 * 1024 * 1024',self.source)

    def test_receipt_document_claim_in_same_stock_transaction(self):
        receipt = ast.parse((ROOT/'tenant_receiving_api.py').read_text(encoding='utf-8'))
        fn=next(x for x in ast.walk(receipt) if isinstance(x,ast.AsyncFunctionDef) and x.name=='confirm_receipt')
        dump=ast.dump(fn)
        for token in ('start_transaction','tenant_stocks','tenant_receipts',
                      'tenant_invoice_documents','invoice_document_id','invoice_sha256'):
            self.assertIn(token,dump)

if __name__ == '__main__':unittest.main()
