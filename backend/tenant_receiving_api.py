"""Tenant-isolated three-way receiving pilot (internal order, delivery slip, verified invoice).

Strictly opt-in via RESTOP_ENABLE_TENANT_V2. No real OCR extraction here: invoice
fields must be checked by a human before confirmation. No external order dispatch.
"""
import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure, PyMongoError

from tenant_stock_api import scoped_stock_id
from tenant_workflows_api import cents_for_quantity


class _StrictPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ReceivedLine(_StrictPayload):
    product_id: str = Field(min_length=1, max_length=64)
    received_milliunits: StrictInt = Field(gt=0, le=100000000)
    invoiced_milliunits: StrictInt = Field(gt=0, le=100000000)
    invoiced_unit_price_cents: StrictInt = Field(ge=0, le=100000000)


class ReceiptInput(_StrictPayload):
    delivery_note_reference: str = Field(min_length=3, max_length=90)
    invoice_reference: str = Field(min_length=3, max_length=90)
    invoice_source: Literal['human_verified']
    invoice_document_id: Optional[str] = Field(default=None, min_length=32, max_length=64)
    lines: List[ReceivedLine] = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=12, max_length=128)
    acknowledge_variances: StrictBool = False
    variance_reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator('delivery_note_reference', 'invoice_reference')
    @classmethod
    def normalized_reference(cls, value):
        value = value.strip().upper()
        if len(value) < 3:
            raise ValueError('Référence du justificatif requise')
        return value

    @field_validator('idempotency_key')
    @classmethod
    def valid_key(cls, value):
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{12,128}', value):
            raise ValueError('Clé de requête invalide')
        return value

    @model_validator(mode='after')
    def unique_products(self):
        ids = [line.product_id for line in self.lines]
        if len(ids) != len(set(ids)):
            raise ValueError('Un produit doit figurer dans une seule ligne')
        if self.acknowledge_variances and (not self.variance_reason or len(self.variance_reason.strip()) < 8):
            raise ValueError('Justification requise lors de la validation d’écarts')
        return self


def _fingerprint(order_id, body):
    canonical = {'order_id': order_id, **body.model_dump(mode='json')}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _receipt_id(rid, key):
    return hashlib.sha256((rid + '\0receipt\0' + key).encode()).hexdigest()


def _movement_id(receipt_id, product_id):
    return hashlib.sha256((receipt_id + '\0' + product_id).encode()).hexdigest()


async def ensure_receiving_indexes(db):
    await db.tenant_receipts.create_index([('restaurant_id', ASCENDING), ('id', ASCENDING)], unique=True)
    # One normalized supplier invoice cannot affect stock twice for a restaurant.
    await db.tenant_receipts.create_index([('restaurant_id', ASCENDING), ('supplier_id', ASCENDING), ('invoice_reference', ASCENDING)], unique=True)
    await db.tenant_receipts.create_index([('restaurant_id', ASCENDING), ('order_id', ASCENDING)])


def build_receiving_router(db, session_guard):
    router = APIRouter(prefix='/tenant', tags=['tenant-v2-receiving-pilot'])

    async def reader(user=Depends(session_guard)):
        if not isinstance(user.get('restaurant_id'), str) or not user['restaurant_id'].strip():
            raise HTTPException(status_code=403, detail='Compte sans établissement')
        if user.get('role') not in {'super_admin', 'patron', 'gerant', 'chef_cuisine'}:
            raise HTTPException(status_code=403, detail='Réception réservée au responsable')
        return user

    async def approver(user=Depends(reader)):
        if user.get('role') not in {'super_admin', 'patron', 'gerant'}:
            raise HTTPException(status_code=403, detail='Approbation réservée à la direction')
        return user

    async def order_for(rid, order_id, session=None):
        order = await db.tenant_purchase_orders.find_one(
            {'restaurant_id': rid, 'id': order_id}, session=session)
        if order is None:
            raise HTTPException(status_code=404, detail='Commande introuvable')
        return order

    async def evaluate(order, body, session=None):
        # Uploaded documents are only suggestions until explicitly reviewed by a
        # responsible user. The reviewed bill must match the confirmation exactly.
        checked_document = None
        if body.invoice_document_id:
            checked_document = await db.tenant_invoice_documents.find_one({
                'restaurant_id': order['restaurant_id'], 'id': body.invoice_document_id,
                'order_id': order['id'], 'supplier_id': order['supplier_id']}, session=session)
            if checked_document is None:
                raise HTTPException(status_code=404, detail='Facture étrangère ou introuvable')
            if checked_document.get('status') != 'reviewed':
                raise HTTPException(status_code=409, detail='La facture doit être vérifiée avant réception')
            if checked_document.get('reviewed_reference') != body.invoice_reference:
                raise HTTPException(status_code=409, detail='Référence différente du document vérifié')
            reviewed_lines = {line['product_id']: line for line in checked_document['reviewed_lines']}
            supplied_lines = {line.product_id: line for line in body.lines}
            if set(reviewed_lines) != set(supplied_lines):
                raise HTTPException(status_code=409, detail='Lignes différentes de la facture vérifiée')
            for pid, reviewed in reviewed_lines.items():
                claimed = supplied_lines[pid]
                if (reviewed['invoiced_milliunits'] != claimed.invoiced_milliunits or
                    reviewed['invoiced_unit_price_cents'] != claimed.invoiced_unit_price_cents):
                    raise HTTPException(status_code=409, detail='Montant ou quantité différent de la facture vérifiée')
        order_lines = {line['product_id']: line for line in order['lines']}
        rid = order['restaurant_id']
        issues = []
        preview_lines = []
        for line in body.lines:
            original = order_lines.get(line.product_id)
            if original is None:
                raise HTTPException(status_code=422, detail='Produit absent de cette commande')
            product = await db.tenant_products.find_one({'restaurant_id': rid, 'id': line.product_id}, {'_id': 0}, session=session)
            if not product or product.get('supplier_id') != order['supplier_id']:
                raise HTTPException(status_code=404, detail='Produit/fournisseur indisponible')
            previous = (order.get('received_milliunits_by_product') or {}).get(line.product_id, 0)
            remaining = original['quantity_milliunits'] - previous
            if remaining <= 0 or line.received_milliunits > remaining:
                raise HTTPException(status_code=409, detail='Quantité supérieure au reliquat de commande')
            line_issues = []
            if line.received_milliunits < remaining:
                line_issues.append('livraison_partielle')
            if line.invoiced_milliunits != line.received_milliunits:
                line_issues.append('quantite_facturee_differente')
            if line.invoiced_unit_price_cents != original['unit_price_cents']:
                line_issues.append('prix_facture_different')
            issues.extend({'product_id': line.product_id, 'code': issue} for issue in line_issues)
            preview_lines.append({'product_id': line.product_id, 'name': product['name'],
                'unit': product['unit'], 'ordered_milliunits': original['quantity_milliunits'],
                'previously_received_milliunits': previous, 'remaining_milliunits': remaining,
                'received_milliunits': line.received_milliunits, 'invoiced_milliunits': line.invoiced_milliunits,
                'ordered_unit_price_cents': original['unit_price_cents'],
                'invoiced_unit_price_cents': line.invoiced_unit_price_cents,
                'invoiced_line_total_cents': cents_for_quantity(line.invoiced_unit_price_cents, line.invoiced_milliunits),
                'issues': line_issues})
        # Missing order lines are never silently treated as delivered.
        missing = set(order_lines) - {line.product_id for line in body.lines}
        for pid in missing:
            original = order_lines.get(pid)
            if original:
                previous = (order.get('received_milliunits_by_product') or {}).get(pid, 0)
                if original['quantity_milliunits'] > previous:
                    issues.append({'product_id': pid, 'code': 'ligne_non_livree'})
        return {'order_id': order['id'], 'supplier_id': order['supplier_id'],
            'delivery_note_reference': body.delivery_note_reference, 'invoice_reference': body.invoice_reference,
            'lines': preview_lines, 'issues': issues,
            'invoice_total_cents': sum(line['invoiced_line_total_cents'] for line in preview_lines),
            'invoice_document_id': body.invoice_document_id,
            'invoice_sha256': checked_document['sha256'] if checked_document else None,
            'can_confirm': not issues or (body.acknowledge_variances and bool(body.variance_reason and len(body.variance_reason.strip()) >= 8))}

    @router.post('/purchase-orders/{order_id}/approve')
    async def approve_order(order_id: str, user=Depends(approver)):
        rid = user['restaurant_id']
        approved = await db.tenant_purchase_orders.find_one_and_update(
            {'restaurant_id': rid, 'id': order_id, 'status': 'draft'},
            {'$set': {'status': 'approved', 'approved_by': user['id'], 'approved_at': datetime.utcnow(), 'receipt_version': 0}},
            return_document=True, projection={'_id': 0})
        if approved:
            return approved
        current = await order_for(rid, order_id)
        raise HTTPException(status_code=409, detail=f'Commande déjà en statut {current["status"]}')

    @router.post('/purchase-orders/{order_id}/receipts/preview')
    async def preview_receipt(order_id: str, body: ReceiptInput, user=Depends(reader)):
        order = await order_for(user['restaurant_id'], order_id)
        if order['status'] not in {'approved', 'receiving'}:
            raise HTTPException(status_code=409, detail='Approbation préalable requise')
        return await evaluate(order, body)

    @router.get('/receipts')
    async def list_receipts(user=Depends(reader)):
        return await db.tenant_receipts.find({'restaurant_id': user['restaurant_id']}, {'_id': 0}).sort('created_at', -1).limit(200).to_list(length=200)

    @router.get('/receipts/by-key/{key}')
    async def receipt_by_key(key: str, user=Depends(reader)):
        rid = user['restaurant_id']
        row = await db.tenant_receipts.find_one({'_id': _receipt_id(rid, key), 'restaurant_id': rid}, {'_id': 0})
        if row is None:
            raise HTTPException(status_code=404, detail='Réception introuvable')
        return row

    @router.get('/receipts/{receipt_id}')
    async def get_receipt(receipt_id: str, user=Depends(reader)):
        row = await db.tenant_receipts.find_one({'restaurant_id': user['restaurant_id'], 'id': receipt_id}, {'_id': 0})
        if row is None:
            raise HTTPException(status_code=404, detail='Réception introuvable')
        return row

    @router.post('/purchase-orders/{order_id}/receipts/confirm', status_code=201)
    async def confirm_receipt(order_id: str, body: ReceiptInput, user=Depends(reader)):
        rid = user['restaurant_id']
        receipt_id = _receipt_id(rid, body.idempotency_key)
        fingerprint = _fingerprint(order_id, body)

        async def replay():
            previous = await db.tenant_receipts.find_one({'_id': receipt_id, 'restaurant_id': rid}, {'_id': 0})
            if previous is None:
                return None
            if previous.get('request_fingerprint') != fingerprint:
                raise HTTPException(status_code=409, detail='Clé déjà utilisée pour une réception différente')
            return {**previous, 'replayed': True}

        old = await replay()
        if old:
            return old
        try:
            hello = await db.client.admin.command('hello')
            if not hello.get('setName') and hello.get('msg') != 'isdbgrid':
                raise HTTPException(status_code=503, detail='Transactions MongoDB indisponibles')
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    order = await order_for(rid, order_id, session=session)
                    if order['status'] not in {'approved', 'receiving'}:
                        raise HTTPException(status_code=409, detail='Commande non ouverte à réception')
                    preview = await evaluate(order, body, session=session)
                    if not preview['can_confirm']:
                        raise HTTPException(status_code=409, detail='Écarts à justifier avant mise en stock')
                    now = datetime.utcnow()
                    for line in preview['lines']:
                        sid = scoped_stock_id(rid, line['product_id'])
                        stock = await db.tenant_stocks.find_one({'_id': sid, 'restaurant_id': rid}, session=session)
                        before = stock['quantity_milliunits'] if stock else 0
                        after = before + line['received_milliunits']
                        if after > 1000000000000:
                            raise HTTPException(status_code=409, detail='Plafond de quantité atteint')
                        if stock:
                            await db.tenant_stocks.update_one({'_id': sid, 'restaurant_id': rid, 'quantity_milliunits': before},
                                {'$set': {'quantity_milliunits': after, 'updated_at': now}}, session=session)
                        else:
                            await db.tenant_stocks.insert_one({'_id': sid, 'restaurant_id': rid, 'product_id': line['product_id'],
                                'quantity_milliunits': after, 'updated_at': now}, session=session)
                        await db.tenant_stock_movements.insert_one({
                            '_id': _movement_id(receipt_id, line['product_id']), 'restaurant_id': rid,
                            'product_id': line['product_id'], 'delta_milliunits': line['received_milliunits'],
                            'quantity_after_milliunits': after, 'source': 'supplier_receipt', 'receipt_id': receipt_id,
                            'actor_id': user['id'], 'created_at': now}, session=session)
                    received = dict(order.get('received_milliunits_by_product') or {})
                    for line in preview['lines']:
                        pid = line['product_id']
                        received[pid] = received.get(pid, 0) + line['received_milliunits']
                    complete = all(received.get(line['product_id'], 0) == line['quantity_milliunits'] for line in order['lines'])
                    status = 'received' if complete else 'receiving'
                    # Conditional status + version protects against concurrent stock receiving.
                    result = await db.tenant_purchase_orders.update_one({
                        '_id': order['_id'], 'restaurant_id': rid,
                        'status': order['status'], 'receipt_version': order.get('receipt_version', 0)},
                        {'$set': {'received_milliunits_by_product': received, 'status': status, 'updated_at': now},
                         '$inc': {'receipt_version': 1}}, session=session)
                    if result.modified_count != 1:
                        raise HTTPException(status_code=409, detail='Commande modifiée par un autre utilisateur')
                    # Document claim commits in the SAME transaction as stock.
                    # A second receipt cannot claim the same reviewed original.
                    if body.invoice_document_id:
                        document_claim = await db.tenant_invoice_documents.update_one({
                            'restaurant_id': rid, 'id': body.invoice_document_id,
                            'order_id': order_id, 'status': 'reviewed'},
                            {'$set': {'status': 'received', 'receipt_id': receipt_id,
                                      'received_at': now}}, session=session)
                        if document_claim.modified_count != 1:
                            raise HTTPException(status_code=409, detail='Facture déjà liée à une réception')
                    row = {'_id': receipt_id, 'id': receipt_id, 'restaurant_id': rid,
                        'order_id': order_id, 'supplier_id': order['supplier_id'],
                        'delivery_note_reference': body.delivery_note_reference,
                        'invoice_reference': body.invoice_reference, 'invoice_source': body.invoice_source,
                        'invoice_document_id': body.invoice_document_id,
                        'invoice_sha256': preview.get('invoice_sha256'),
                        'request_fingerprint': fingerprint, 'lines': preview['lines'],
                        'issues': preview['issues'], 'variance_reason': body.variance_reason,
                        'invoice_total_cents': preview['invoice_total_cents'],
                        'order_status_after': status, 'reviewed_by': user['id'], 'created_at': now}
                    await db.tenant_receipts.insert_one(row, session=session)
            row.pop('_id', None)
            return {**row, 'replayed': False}
        except HTTPException:
            raise
        except (DuplicateKeyError, OperationFailure) as exc:
            old = await replay()
            if old:
                return old
            raise HTTPException(status_code=409, detail='Conflit de réception ou référence facture déjà utilisée') from exc
        except PyMongoError as exc:
            raise HTTPException(status_code=503, detail='État de réception incertain : vérifier la clé avant de réessayer') from exc

    return router
