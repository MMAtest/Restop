"""Tests du contrat transactionnel. Mocks uniquement : pas un test d'intégration Mongo."""
import ast
import asyncio
from pathlib import Path
import unittest

from invoice_guard import transaction_topology_supported, run_stock_transaction


class TransactionSession:
    def __init__(self, state):
        self.state = state
        self.pending = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def start_transaction(self):
        parent = self
        class Transaction:
            async def __aenter__(self):
                return parent
            async def __aexit__(self, exc_type, exc, traceback):
                if exc_type is None:
                    parent.state.extend(parent.pending)
                parent.pending.clear()
                return False
        return Transaction()


class Client:
    def __init__(self, state):
        self.state = state
    async def start_session(self):
        return TransactionSession(self.state)


class TransactionContractTests(unittest.TestCase):
    def test_replica_set_supported_standalone_rejected(self):
        self.assertTrue(transaction_topology_supported({'setName':'rs0','logicalSessionTimeoutMinutes':30}))
        self.assertTrue(transaction_topology_supported({'msg':'isdbgrid','logicalSessionTimeoutMinutes':30}))
        self.assertFalse(transaction_topology_supported({'isWritablePrimary':True,'logicalSessionTimeoutMinutes':30}))
        self.assertFalse(transaction_topology_supported({'setName':'rs0'}))

    def test_rollback_when_one_of_many_writes_fails(self):
        state=[]
        async def apply(session):
            session.pending.extend(['supplier','batch','stock'])
            raise RuntimeError('fault after stock write')
        async def scenario():
            with self.assertRaises(RuntimeError):
                await run_stock_transaction(Client(state),apply)
        asyncio.run(scenario())
        self.assertEqual(state,[])

    def test_commit_complete_set_once(self):
        state=[]
        async def apply(session):
            session.pending.extend(['product','batch','movement','stock','invoice'])
            return {'stock_entries':1}
        result=asyncio.run(run_stock_transaction(Client(state),apply))
        self.assertEqual(result,{'stock_entries':1})
        self.assertEqual(len(state),5)

    def test_every_mutating_db_call_inside_invoice_transaction_uses_session(self):
        tree=ast.parse((Path(__file__).parent/'server.py').read_text())
        callbacks=[n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=='apply_atomic_invoice']
        self.assertEqual(len(callbacks),1)
        writes=[]
        missing=[]
        for node in ast.walk(callbacks[0]):
            if not isinstance(node,ast.Call):
                continue
            fn=node.func
            if not isinstance(fn,ast.Attribute) or fn.attr not in {'insert_one','update_one','find_one_and_update','delete_one'}:
                continue
            coll=fn.value
            if not (isinstance(coll,ast.Attribute) and isinstance(coll.value,ast.Name) and coll.value.id=='db'):
                continue
            writes.append((coll.attr,fn.attr))
            if not any(k.arg=='session' and isinstance(k.value,ast.Name) and k.value.id=='mongo_session' for k in node.keywords):
                missing.append((coll.attr,fn.attr,node.lineno))
        self.assertGreaterEqual(len(writes),8)
        self.assertEqual(missing,[])


if __name__=='__main__':
    unittest.main()
