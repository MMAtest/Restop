#!/usr/bin/env python3
"""
Debug script pour comprendre pourquoi les productions ne sont pas détectées
"""

import sys
import re

# Importer la fonction depuis le backend
sys.path.append('/app/backend')
from server import analyze_z_report_categories

# Texte de test avec indentation visible
test_ocr_text = """RAPPORT DE CLOTURE
Date: 01/09/2025
Heure: 22:59:38

SOLDE DE CAISSE
Nombre de couverts: 122,00
Total HT: 6660,26
Total TTC: 7433,00

VENTES PAR CATEGORIES
x73) Entrees 1450,00
  x14) Moules 252,00
  x8) Salade Caesar 184,00

x28) Boissons Chaudes 88,80
  x15) Café 45,00
  x13) Thé 43,80

x45) Plats principaux 3200,50
  x12) Steak frites 420,00
  x8) Poisson grillé 288,00

x22) Bouteille ROUGE 445,60
x18) Cocktail 234,50

x15) Desserts 312,40
  x6) Tiramisu 108,00
  x9) Tarte aux pommes 204,40

TOTAL GENERAL: 7433,00"""

print("=== DEBUG PRODUCTIONS DETECTION ===")
print()

# Analyser ligne par ligne
lines = [l.strip() for l in test_ocr_text.split('\n') if l and len(l.strip()) > 0]

print("Lignes analysées:")
for i, line in enumerate(lines):
    print(f"{i:2d}: '{line}'")
    if line.startswith(' ') or line.startswith('\t'):
        print(f"    -> INDENTÉE: '{line}'")

print()

# Tester les patterns
production_pattern = re.compile(r"^\(?x?(\d+)\)?\s*([^0-9]+?)\s+([0-9]+(?:[,\.][0-9]{2}))$", re.IGNORECASE)

print("Test des patterns de production:")
test_lines = [
    "  x14) Moules 252,00",
    "x14) Moules 252,00",
    "  x8) Salade Caesar 184,00"
]

for line in test_lines:
    print(f"Ligne: '{line}'")
    print(f"  Commence par espace: {line.startswith(' ')}")
    clean_chars = ' \\t_'
    clean_line = line.lstrip(clean_chars)
    print(f"  Ligne nettoyée: '{clean_line}'")
    
    match = production_pattern.match(clean_line)
    if match:
        print(f"  MATCH: quantité={match.group(1)}, nom='{match.group(2).strip()}', prix={match.group(3)}")
    else:
        print(f"  PAS DE MATCH")
    print()

# Appeler la fonction complète
print("=== RÉSULTAT FONCTION COMPLÈTE ===")
result = analyze_z_report_categories(test_ocr_text)
print(f"Productions détectées: {len(result.get('productions_detectees', []))}")
for prod in result.get('productions_detectees', []):
    print(f"  - {prod['nom']}: {prod['quantite']} x {prod['prix_total']}€")