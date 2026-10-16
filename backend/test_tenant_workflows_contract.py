"""Static guards for opt-in tenant workflows; does not need MongoDB/third-party SDKs."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).parent

class TenantWorkflowContractTests(unittest.TestCase):
    def test_workflows_are_opt_in_and_indexes_registered(self):
        source=(ROOT/'server.py').read_text(encoding='utf-8')
        self.assertIn('if os.getenv("RESTOP_ENABLE_TENANT_V2") == "1":',source)
        self.assertIn('api_router.include_router(build_tenant_workflow_router(db, require_active_user))',source)
        self.assertIn('await ensure_workflow_indexes(db)',source)

    def test_workflow_routes_declare_guards(self):
        tree=ast.parse((ROOT/'tenant_workflows_api.py').read_text(encoding='utf-8'))
        builder=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_tenant_workflow_router')
        routes=0
        for node in ast.walk(builder):
            if not isinstance(node,ast.AsyncFunctionDef):continue
            for d in node.decorator_list:
                if not isinstance(d,ast.Call) or not isinstance(d.func,ast.Attribute):continue
                if d.func.attr not in ('get','post','put','patch','delete'):continue
                routes+=1
                signature=ast.dump(node.args)
                self.assertIn('Depends',signature,node.name)
                self.assertTrue('editor' in signature or 'z_reader' in signature,node.name)
                self.assertNotIn("restaurant_id",[arg.arg for arg in node.args.args],node.name)
        self.assertGreaterEqual(routes,9)

    def test_workflows_do_not_read_global_legacy_collections(self):
        tree=ast.parse((ROOT/'tenant_workflows_api.py').read_text(encoding='utf-8'))
        names=[]
        for n in ast.walk(tree):
            if not isinstance(n,ast.Attribute) or not isinstance(n.value,ast.Name) or n.value.id!='db':continue
            names.append(n.attr)
        self.assertTrue(names)
        self.assertTrue(all(n.startswith('tenant_') for n in names),names)

    def test_z_reports_are_immutable_and_balance_checked(self):
        source=(ROOT/'tenant_workflows_api.py').read_text(encoding='utf-8')
        self.assertIn('check_payment_total',source)
        self.assertIn('total_cents != self.cash_cents + self.card_cents + self.other_cents',source)
        self.assertIn('("report_reference", ASCENDING)',source)
        self.assertIn('return v.upper()',source)
        tree=ast.parse(source)
        builder=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_tenant_workflow_router')
        z_methods=[]
        for node in ast.walk(builder):
            if not isinstance(node,ast.AsyncFunctionDef):continue
            for d in node.decorator_list:
                if isinstance(d,ast.Call) and d.args and isinstance(d.args[0],ast.Str) and d.args[0].s.startswith('/z-reports'):
                    z_methods.append(d.func.attr)
        self.assertNotIn('delete',z_methods)
        self.assertNotIn('patch',z_methods)
        self.assertNotIn('put',z_methods)

if __name__=='__main__':unittest.main()
