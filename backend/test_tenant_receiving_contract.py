"""Dependency-free controls for experimental tenant-scoped receiving endpoints."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).parent


class ReceivingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'tenant_receiving_api.py').read_text(encoding='utf-8')
        cls.tree=ast.parse(cls.source)

    def test_opt_in_and_indexes_only_with_tenant_pilot(self):
        s=(ROOT/'server.py').read_text(encoding='utf-8')
        self.assertIn('if os.getenv("RESTOP_ENABLE_TENANT_V2") == "1":',s)
        self.assertIn('build_receiving_router(db, require_active_user)',s)
        self.assertIn('await ensure_receiving_indexes(db)',s)

    def test_all_receiving_routes_have_server_auth_and_no_tenant_input(self):
        builder=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_receiving_router')
        routes=[]
        for fn in ast.walk(builder):
            if not isinstance(fn,ast.AsyncFunctionDef):continue
            for deco in fn.decorator_list:
                if not isinstance(deco,ast.Call) or not isinstance(deco.func,ast.Attribute):continue
                if deco.func.attr not in ('get','post','patch','delete'):continue
                routes.append((fn.name,deco.func.attr))
                signature=ast.dump(fn.args)
                self.assertIn('Depends',signature,fn.name)
                self.assertTrue('reader' in signature or 'approver' in signature,fn.name)
                self.assertNotIn('restaurant_id',[a.arg for a in fn.args.args])
        self.assertGreaterEqual(len(routes),6)
        self.assertNotIn('delete',[method for _,method in routes])

    def test_no_unscoped_legacy_collections_or_client_claimed_ocr(self):
        attrs=[]
        for n in ast.walk(self.tree):
            if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='db':
                if n.attr != 'client':attrs.append(n.attr)
        self.assertTrue(attrs)
        self.assertTrue(all(name.startswith('tenant_') for name in attrs),attrs)
        self.assertIn("Literal['human_verified']",self.source)
        self.assertIn("extra='forbid'",self.source)

    def test_stock_movement_receipt_and_order_committed_in_one_transaction(self):
        confirm=next(n for n in ast.walk(self.tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=='confirm_receipt')
        body=ast.dump(confirm)
        for needle in ('start_transaction','tenant_stocks','tenant_stock_movements',
                       'tenant_receipts','tenant_purchase_orders','request_fingerprint','scoped_stock_id'):
            self.assertIn(needle,body)
        self.assertIn('received_milliunits_by_product',body)


if __name__=='__main__':unittest.main()
