"""Pure invoice consistency rules. Advisory: never substitute OCR for accounting approval.

Amounts are euros and use Decimal to avoid binary float comparison errors.
Numbers can be strings in either French or international numeric notation.
"""
from decimal import Decimal, InvalidOperation
import hashlib
import re
import unicodedata


def money(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        raw = str(value).strip().replace('\u202f', '').replace('\xa0', '').replace(' ', '').replace('€', '')
        if not raw:
            return None
        # European decimal notation with optional thousands separators.
        if ',' in raw:
            raw = raw.replace('.', '').replace(',', '.')
        result = Decimal(raw)
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def normalized_key(text):
    text = unicodedata.normalize('NFKD', str(text or ''))
    return re.sub(r'[^A-Z0-9]', '', ''.join(c for c in text if not unicodedata.combining(c)).upper())


def supplier_invoice_fingerprint(supplier, invoice_number):
    name = normalized_key(supplier)
    number = normalized_key(invoice_number)
    if not name or not number or number in {'NA', 'INCONNU', 'UNKNOWN', 'AUCUN'}:
        return None
    return hashlib.sha256((name + ':' + number).encode('utf-8')).hexdigest()


def audit_invoice_totals(parsed, tolerance=Decimal('0.05')):
    """Advisory anomalies with explicit assumptions; no line sum treated as definitive VAT proof."""
    parsed = parsed if isinstance(parsed, dict) else {}
    warnings = []
    ht = money(parsed.get('total_ht'))
    ttc = money(parsed.get('total_ttc'))
    if ht is not None and ht < 0 or ttc is not None and ttc < 0:
        warnings.append({'code': 'negative_total', 'message': 'Un total de facture négatif doit être vérifié (avoir éventuel).', 'severity': 'warning'})
    if ht is not None and ttc is not None and ht > 0:
        if ttc + tolerance < ht:
            warnings.append({'code': 'ttc_below_ht', 'message': 'Le total TTC est inférieur au total HT. Vérifiez remises, avoirs et lecture OCR.', 'severity': 'warning'})
        elif (ttc - ht) / ht > Decimal('0.30'):
            warnings.append({'code': 'unusual_tax', 'message': 'L’écart entre TTC et HT dépasse 30 %. Vérifiez les montants ou taxes particulières.', 'severity': 'warning'})
    items = parsed.get('produits') or []
    if not isinstance(items, list):
        return warnings
    computed = Decimal('0')
    count = 0
    all_valid = bool(items)
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            all_valid = False
            continue
        qty = money(item.get('quantite'))
        price = money(item.get('prix_unitaire'))
        line_total = money(item.get('prix_total', item.get('total')))
        if qty is None or qty <= 0 or price is None or price < 0:
            all_valid = False
            continue
        expected = qty * price
        computed += expected
        count += 1
        if line_total is not None and line_total > 0 and abs(expected - line_total) > max(tolerance, line_total * Decimal('0.01')):
            warnings.append({'code': 'line_mismatch', 'line': i,
                'message': 'Ligne {} : quantité × prix unitaire diffère du total OCR. Vérifiez colis, poids variable et remises.'.format(i),
                'severity': 'warning'})
    # Partial OCR, delivery fees, deposits and discounts make computed totals non-authoritative.
    if ht is not None and ht > 0 and count and all_valid and abs(computed - ht) > max(Decimal('1.00'), ht * Decimal('0.02')):
        warnings.append({'code': 'subtotal_mismatch',
            'message': 'La somme indicative des lignes diffère du HT facturé. Vérifiez frais, remises, consignes et unités.',
            'severity': 'warning'})
    return warnings


async def reserve_invoice_for_import(documents_collection, document_id, now):
    """Single compare-and-set reservation; concurrent attempts must not both pass.

    This serializes a document but is NOT a Mongo multi-collection transaction.
    """
    return await documents_collection.find_one_and_update(
        {"id": document_id, "type_document": "facture_fournisseur",
         "statut": {"$nin": ["integre", "import_en_cours", "import_incomplet"]}},
        {"$set": {"statut": "import_en_cours", "import_started_at": now}}
    )
