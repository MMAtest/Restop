"""Dependency-free structural gates for the disabled-by-default tenant pilot."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class TenantContractTests(unittest.TestCase):
    def test_tenant_route_opt_in_only(self):
        source = (ROOT / 'server.py').read_text(encoding='utf-8')
        self.assertIn('if os.getenv("RESTOP_ENABLE_TENANT_V2") == "1":', source)
        self.assertIn('api_router.include_router(build_tenant_router(db, require_active_user))', source)
        self.assertIn('await ensure_tenant_indexes(db)', source)

    def test_all_pilot_routes_are_scoped_through_server_auth(self):
        tree = ast.parse((ROOT / 'tenant_stock_api.py').read_text(encoding='utf-8'))
        builder = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build_tenant_router')
        routes = 0
        for node in ast.walk(builder):
            if not isinstance(node, ast.AsyncFunctionDef) or not node.decorator_list:
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                if not decorator.args or not isinstance(decorator.args[0], ast.Str):
                    continue
                if decorator.func.attr not in ('get', 'post', 'put', 'delete'):
                    continue
                routes += 1
                args = ast.dump(node.args)
                self.assertIn('Depends', args, node.name)
                self.assertTrue('tenant_reader' in args or 'tenant_editor' in args, node.name)
                self.assertNotEqual('restaurant_id', node.args.args[-1].arg, 'Unexpected user-supplied tenant path')
        self.assertGreaterEqual(routes, 7)

    def test_mutation_uses_multi_collection_transaction(self):
        tree = ast.parse((ROOT / 'tenant_stock_api.py').read_text(encoding='utf-8'))
        target = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == 'adjust_stock')
        body = ast.dump(target)
        self.assertIn('start_transaction', body)
        self.assertIn('tenant_stock_movements', body)
        self.assertIn('tenant_stocks', body)
        self.assertIn('scoped_stock_id', body)
        self.assertIn('scoped_movement_id', body)
        self.assertIn('restaurant_id', body)


if __name__ == '__main__':
    unittest.main()
