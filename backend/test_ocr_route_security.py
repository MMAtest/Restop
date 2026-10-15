"""Structural route-level regression tests; do not replace live HTTP auth tests."""
import ast
from pathlib import Path
import unittest

class OCRRoutePolicy(unittest.TestCase):
    def test_all_ocr_routes_require_backend_dependency(self):
        source=(Path(__file__).parent/'server.py').read_text()
        tree=ast.parse(source)
        checked=[]
        for fn in tree.body:
            if not isinstance(fn,(ast.AsyncFunctionDef,ast.FunctionDef)):
                continue
            for decorator in fn.decorator_list:
                if not isinstance(decorator,ast.Call) or not decorator.args:
                    continue
                if not isinstance(decorator.args[0],ast.Str) or not decorator.args[0].s.startswith('/ocr/'):
                    continue
                route=decorator.args[0].s
                protected=(any(k.arg=='dependencies' for k in decorator.keywords)
                    or fn.name=='confirm_import_facture')
                self.assertTrue(protected, 'OCR route unprotected: '+route)
                checked.append(route)
        self.assertGreaterEqual(len(checked),15)

    def test_destructive_all_documents_removed(self):
        source=(Path(__file__).parent/'server.py').read_text()
        tree=ast.parse(source)
        fn=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='delete_all_ocr_documents')
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr=='delete_many' for n in ast.walk(fn)))

if __name__=='__main__': unittest.main()
