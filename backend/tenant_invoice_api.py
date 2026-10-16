"""Tenant-v2 document ingestion: immutable original, suggested extraction, manual review.

Never trusts OCR to modify a restaurant's stock. The tenant is the persisted
session's tenant, not a form field, filename, or extracted document content.
"""
import asyncio
import hashlib
import io
import re
import unicodedata
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

MAX_INVOICE_BYTES = 8 * 1024 * 1024  # BSON limit is 16 MiB: no unbounded documents
MAX_EXTRACT_CHARS = 16000
MAX_FILES_PER_ORDER = 20


class ReviewLine(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product_id: str = Field(min_length=1, max_length=64)
    invoiced_milliunits: StrictInt = Field(gt=0, le=100000000)
    invoiced_unit_price_cents: StrictInt = Field(ge=0, le=100000000)


class InvoiceReview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    invoice_reference: str = Field(min_length=3, max_length=90)
    lines: List[ReviewLine] = Field(min_length=1, max_length=100)
    review_note: str = Field(min_length=8, max_length=500)

    @field_validator('invoice_reference')
    @classmethod
    def normalized_reference(cls, value):
        value = value.strip().upper()
        if len(value) < 3:
            raise ValueError('Numéro de facture requis')
        return value

    @field_validator('review_note')
    @classmethod
    def clean_note(cls, value):
        if len(value.strip()) < 8:
            raise ValueError('Indiquer le contrôle humain effectué')
        return value.strip()

    @model_validator(mode='after')
    def distinct_items(self):
        product_ids = [line.product_id for line in self.lines]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError('Lignes produits dupliquées')
        return self


def detect_format(content):
    if content.startswith(b'%PDF-'):
        return 'application/pdf', 'pdf'
    if content.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png', 'png'
    if content.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg', 'jpg'
    if len(content) >= 12 and content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return 'image/webp', 'webp'
    raise ValueError('Fichier invalide : PDF, JPEG, PNG ou WebP uniquement')


def _tesseract_best_effort(image):
    """Run local OCR with an execution timeout; fall back to manual review."""
    import pytesseract
    for language in ('fra+eng', 'eng'):
        try:
            return pytesseract.image_to_string(image, lang=language, timeout=15), 'tesseract'
        except (pytesseract.TesseractNotFoundError, RuntimeError):
            continue
    return '', 'ocr_engine_unavailable'


def extract_text_locally(content, ext):
    """Best effort; never derive authoritative invoice lines from OCR text."""
    if ext == 'pdf':
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise ValueError('PDF protégé par mot de passe')
        if len(reader.pages) > 10:
            raise ValueError('PDF trop long : 10 pages maximum')
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or '')
            if sum(len(p) for p in parts) > MAX_EXTRACT_CHARS:
                break
        text = '\n'.join(parts)[:MAX_EXTRACT_CHARS]
        if len(text.strip()) >= 20:
            return text, 'pdf_embedded_text'
        # Scanned PDFs can contain only raster pages. Render max 2 at modest
        # resolution for OCR; the entire invoice still requires visual review.
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(content)
            scanned = []
            for i in range(min(len(pdf), 2)):
                page = pdf[i]
                width, height = page.get_size()
                if width * height * 1.5 * 1.5 > 12_000_000:
                    continue
                image = page.render(scale=1.5).to_pil().convert('RGB')
                extracted, engine = _tesseract_best_effort(image)
                if engine == 'ocr_engine_unavailable':
                    return text, 'ocr_engine_unavailable'
                scanned.append(extracted)
            ocr_text = '\n'.join(scanned).strip()
            return (ocr_text or text)[:MAX_EXTRACT_CHARS], 'pdf_scanned_tesseract' if ocr_text else 'pdf_no_text'
        except (ImportError, OSError):
            return text, 'pdf_scanned_ocr_unavailable'
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 12_000_000
    with Image.open(io.BytesIO(content)) as source:
        if source.format not in ('PNG', 'JPEG', 'WEBP'):
            raise ValueError('Encodage image invalide')
        if source.width * source.height > 12_000_000:
            raise ValueError('Image trop grande')
        source.verify()
    with Image.open(io.BytesIO(content)) as image:
        prepared = ImageOps.exif_transpose(image).convert('RGB')
        text, engine = _tesseract_best_effort(prepared)
        return text[:MAX_EXTRACT_CHARS], 'tesseract_image' if engine == 'tesseract' else engine


def normalized_text(value):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', value.casefold())
                   if not unicodedata.combining(ch))


def low_confidence_suggestions(text):
    # Never auto-match products or validate money from arbitrary OCR fragments.
    suggestion = {}
    found = re.search(r'(?:FACTURE|INVOICE)\s*(?:N\s*[°o.]?|NUM[EÉ]RO|#|:)\s*([\w/-]{3,70})', text, re.IGNORECASE)
    if found:
        suggestion['invoice_reference'] = found.group(1).upper()
    return suggestion


def metadata(row):
    return {k: v for k, v in row.items() if k not in ('_id', 'extracted_text')}


async def ensure_invoice_indexes(db):
    await db.tenant_invoice_documents.create_index([('restaurant_id', ASCENDING), ('id', ASCENDING)], unique=True)
    await db.tenant_invoice_documents.create_index([('restaurant_id', ASCENDING), ('supplier_id', ASCENDING), ('sha256', ASCENDING)], unique=True)
    await db.tenant_invoice_files.create_index([('restaurant_id', ASCENDING), ('document_id', ASCENDING)], unique=True)


def build_invoice_router(db, session_guard):
    router = APIRouter(prefix='/tenant/invoices', tags=['tenant-v2-invoice-documents'])

    async def invoice_editor(user=Depends(session_guard)):
        rid = user.get('restaurant_id')
        if not isinstance(rid, str) or not rid.strip():
            raise HTTPException(status_code=403, detail='Compte sans restaurant')
        if user.get('role') not in {'super_admin', 'patron', 'gerant', 'chef_cuisine'}:
            raise HTTPException(status_code=403, detail='Documents réservés aux responsables')
        return user

    async def get_document(rid, document_id):
        row = await db.tenant_invoice_documents.find_one({'restaurant_id': rid, 'id': document_id})
        if row is None:
            raise HTTPException(status_code=404, detail='Facture introuvable')
        return row

    @router.post('/upload', status_code=201)
    async def upload_invoice(order_id: str, file: UploadFile = File(...), user=Depends(invoice_editor)):
        rid = user['restaurant_id']
        order = await db.tenant_purchase_orders.find_one({'restaurant_id': rid, 'id': order_id})
        if order is None:
            raise HTTPException(status_code=404, detail='Commande introuvable')
        if order['status'] not in ('approved', 'receiving'):
            raise HTTPException(status_code=409, detail='Approuver la commande avant dépôt')
        content = await file.read(MAX_INVOICE_BYTES + 1)
        await file.close()
        if not content or len(content) > MAX_INVOICE_BYTES:
            raise HTTPException(status_code=413, detail='Fichier vide ou supérieur à 8 Mio')
        try:
            mime, ext = detect_format(content)
            text, engine = await asyncio.to_thread(extract_text_locally, content, ext)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            # Unparseable PDF is not a trustworthy invoice file.
            raise HTTPException(status_code=422, detail='Document illisible ou invalide') from exc
        if await db.tenant_invoice_documents.count_documents({'restaurant_id': rid, 'order_id': order_id}) >= MAX_FILES_PER_ORDER:
            raise HTTPException(status_code=429, detail='20 documents maximum par commande pilote')
        # Name matches are low-confidence hints only: no numeric OCR field is
        # trusted, and no stock or supplier price is ever mutated here.
        suggestions = low_confidence_suggestions(text)
        normalized = normalized_text(text)
        if len(normalized) >= 8:
            product_ids = [line['product_id'] for line in order['lines']]
            products = await db.tenant_products.find({'restaurant_id': rid, 'id': {'$in': product_ids}},
                                                      {'_id': 0, 'id': 1, 'name': 1}).to_list(length=100)
            suggestions['potential_product_matches'] = [
                {'product_id': p['id'], 'name': p['name']} for p in products
                if len(p['name'].strip()) >= 4 and normalized_text(p['name']) in normalized]
        digest = hashlib.sha256(content).hexdigest()
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow()
        row = {'id': doc_id, 'restaurant_id': rid, 'supplier_id': order['supplier_id'],
            'order_id': order_id, 'sha256': digest, 'size_bytes': len(content),
            'media_type': mime, 'extension': ext, 'status': 'needs_review',
            'extraction_engine': engine, 'extracted_text': text,
            'extracted_chars': len(text), 'suggestions': suggestions,
            'created_by': user['id'], 'created_at': now}
        try:
            hello = await db.client.admin.command('hello')
            if not hello.get('setName') and hello.get('msg') != 'isdbgrid':
                raise HTTPException(status_code=503, detail='Stockage transactionnel indisponible')
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    await db.tenant_invoice_files.insert_one({'_id': doc_id, 'document_id': doc_id,
                        'restaurant_id': rid, 'content': content, 'sha256': digest}, session=session)
                    await db.tenant_invoice_documents.insert_one(dict(row), session=session)
        except HTTPException:
            raise
        except DuplicateKeyError as exc:
            raise HTTPException(status_code=409, detail='Ce fichier existe déjà pour ce fournisseur') from exc
        except PyMongoError as exc:
            raise HTTPException(status_code=503, detail='Écriture de facture non confirmée') from exc
        return metadata(row)

    @router.get('')
    async def list_invoices(order_id: str, user=Depends(invoice_editor)):
        rid = user['restaurant_id']
        order = await db.tenant_purchase_orders.find_one({'restaurant_id': rid, 'id': order_id})
        if not order:
            raise HTTPException(status_code=404, detail='Commande introuvable')
        rows = await db.tenant_invoice_documents.find(
            {'restaurant_id': rid, 'order_id': order_id}, {'_id': 0, 'extracted_text': 0}
        ).sort('created_at', -1).limit(100).to_list(length=100)
        return rows

    @router.get('/{document_id}')
    async def get_invoice(document_id: str, user=Depends(invoice_editor)):
        row = await get_document(user['restaurant_id'], document_id)
        return {**metadata(row), 'extracted_text': row['extracted_text']}

    @router.get('/{document_id}/file')
    async def download_invoice(document_id: str, user=Depends(invoice_editor)):
        rid = user['restaurant_id']
        row = await get_document(rid, document_id)
        blob = await db.tenant_invoice_files.find_one({'restaurant_id': rid, 'document_id': document_id})
        if not blob or hashlib.sha256(blob['content']).hexdigest() != row['sha256']:
            raise HTTPException(status_code=503, detail='Fichier original absent ou empreinte invalide')
        # Filename is generated by the server. Never use untrusted uploaded filename.
        return Response(content=bytes(blob['content']), media_type='application/octet-stream', headers={
            'Content-Disposition': f'attachment; filename="restop-invoice-{document_id}.{row["extension"]}"',
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})

    @router.post('/{document_id}/review')
    async def review_invoice(document_id: str, body: InvoiceReview, user=Depends(invoice_editor)):
        rid = user['restaurant_id']
        document = await get_document(rid, document_id)
        if document['status'] != 'needs_review':
            raise HTTPException(status_code=409, detail='Facture déjà vérifiée ou liée à une réception')
        order = await db.tenant_purchase_orders.find_one({'restaurant_id': rid, 'id': document['order_id']})
        if order is None or order['status'] not in ('approved', 'receiving'):
            raise HTTPException(status_code=409, detail='Commande non ouverte à la réception')
        items = {line['product_id'] for line in order['lines']}
        if any(item.product_id not in items for item in body.lines):
            raise HTTPException(status_code=422, detail='Référence absente de la commande')
        reviewed = await db.tenant_invoice_documents.find_one_and_update(
            {'restaurant_id': rid, 'id': document_id, 'status': 'needs_review'},
            {'$set': {'status': 'reviewed', 'reviewed_reference': body.invoice_reference,
                      'reviewed_lines': [line.model_dump() for line in body.lines],
                      'review_note': body.review_note, 'reviewed_by': user['id'],
                      'reviewed_at': datetime.utcnow()}}, return_document=True)
        if reviewed is None:
            raise HTTPException(status_code=409, detail='Facture modifiée simultanément')
        return metadata(reviewed)

    return router
