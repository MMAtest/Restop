#!/usr/bin/env python3
"""
Test de debug pour vérifier le parsing des formats de prix spécifiques
"""

import re

def parse_price(val: str) -> float:
    try:
        v = val.replace('€', '').replace(' ', '').replace('\u202f', '').replace('\xa0', '')
        # Replace comma decimal
        if v.count(',') == 1 and v.count('.') == 0:
            v = v.replace(',', '.')
        # Remove thousand separators if any
        v = v.replace('.', '.')  # no-op but keeps format
        return float(v)
    except Exception:
        return None

def try_parse_item_line(line: str):
    # Clean leading markers
    line_clean = re.sub(r'^[_\-\•\·\s]+', '', line).strip()
    # Patterns with price
    patterns = [
        # (x3) Name 12,00
        (r'^\(?x?(\d{1,3})\)?\s*[)\-]*\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))$', ('qty','name','price')),
        # (x3) Name €12.00
        (r'^\(?x?(\d{1,3})\)?\s*[)\-]*\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€\s?(\d{1,4}(?:[\.,]\d{2}))$', ('qty','name','price')),
        # Name €12.00 x 3
        (r'^([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))\s*x\s*(\d{1,3})$', ('name','price','qty')),
        # Name x 3 12,00
        (r'^([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+x\s*(\d{1,3})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))$', ('name','qty','price')),
        # 3x Name 12,00
        (r'^(\d{1,3})\s*x\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))$', ('qty','name','price')),
    ]
    for pat, order in patterns:
        m = re.match(pat, line_clean, re.IGNORECASE)
        if m:
            groups = m.groups()
            qty = int(groups[order.index('qty')])
            name = groups[order.index('name')].strip()
            price = parse_price(groups[order.index('price')])
            return name, qty, price
    return None

# Test avec les formats spécifiés dans la demande
test_lines = [
    "(x3) Linguine aux palourdes 28,00",
    "Burrata di Bufala €18.50 x 2",
    "4x Supions persillade 24,00",
    # Variations supplémentaires
    "(x2) Tarte citron 14,50",
    "Bœuf Wellington €56.00 x 1",
    "3x Pastis Ricard 6,00",
    "Vin rouge Côtes du Rhône €8.50 x 4"
]

print("🔍 TEST PARSING FORMATS PRIX SPÉCIFIQUES")
print("=" * 50)

for line in test_lines:
    print(f"\nLigne: '{line}'")
    result = try_parse_item_line(line)
    if result:
        name, qty, price = result
        total_price = (price * qty) if price is not None else None
        print(f"✅ PARSÉ: nom='{name}', qty={qty}, unit_price={price}, total_price={total_price}")
    else:
        print(f"❌ NON PARSÉ")

print(f"\n🎯 CONCLUSION:")
parsed_count = sum(1 for line in test_lines if try_parse_item_line(line) is not None)
print(f"Formats parsés: {parsed_count}/{len(test_lines)} ({parsed_count/len(test_lines)*100:.1f}%)")