"""Regression contract for session and role checks without external dependencies."""
import ast
import asyncio
from pathlib import Path
import unittest
from typing import Optional


class FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class Collection:
    def __init__(self, records):
        self.records = records

    async def find_one(self, query):
        for record in self.records:
            if all(record.get(key) == val for key, val in query.items()):
                return record
        return None


class DB:
    user_sessions = Collection([{'session_id':'safe-token','user_id':'1'}])
    users = Collection([{'id':'1','is_active':True,'role':'patron'}, {'id':'2','is_active':False,'role':'super_admin'}])


def load_guards():
    tree = ast.parse((Path(__file__).parent / 'server.py').read_text())
    selected = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name in
                ('require_active_user', 'require_user_manager', 'require_invoice_editor')]
    namespace = {
        'Optional': Optional, 'HTTPException': FakeHTTPException, 'Header': lambda default=None: default,
        'Depends': lambda func: None, 'db': DB,
    }
    exec(compile(ast.Module(body=selected), 'server.guards', 'exec'), namespace)
    return namespace


class AuthGuardTests(unittest.TestCase):
    def test_missing_session_refused(self):
        guards = load_guards()
        with self.assertRaises(FakeHTTPException) as error:
            asyncio.run(guards['require_active_user'](None))
        self.assertEqual(error.exception.status_code, 401)

    def test_valid_session_uses_real_role(self):
        guards = load_guards()
        user = asyncio.run(guards['require_active_user']('Bearer safe-token'))
        self.assertEqual(user['role'], 'patron')
        self.assertEqual(asyncio.run(guards['require_invoice_editor'](user))['role'], 'patron')

    def test_disallowed_role_rejected(self):
        guards = load_guards()
        with self.assertRaises(FakeHTTPException) as error:
            asyncio.run(guards['require_invoice_editor']({'role':'barman'}))
        self.assertEqual(error.exception.status_code, 403)


if __name__ == '__main__':
    unittest.main()
