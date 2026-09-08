#!/usr/bin/env python3
"""
Debug script avec la nouvelle approche (lignes non-strippées)
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

print("=== DEBUG PRODUCTIONS DETECTION (NOUVELLE APPROCHE) ===")
print()

# Analyser ligne par ligne avec la nouvelle approche
lines = [l for l in test_ocr_text.split('\n') if l and len(l.strip()) > 0]

print("Lignes avec indentation préservée:")
for i, line in enumerate(lines):
    print(f"{i:2d}: '{line}'")
    if line.startswith(' ') or line.startswith('\t'):
        print(f"    -> INDENTÉE: '{line}'")
        clean_line = line.lstrip(' \t_')
        print(f"    -> NETTOYÉE: '{clean_line}'")

print()

# Appeler la fonction complète
print("=== RÉSULTAT FONCTION COMPLÈTE (CORRIGÉE) ===")
result = analyze_z_report_categories(test_ocr_text)
print(f"Productions détectées: {len(result.get('productions_detectees', []))}")
for prod in result.get('productions_detectees', []):
    print(f"  - {prod['nom']}: {prod['quantite']} x {prod['prix_total']}€")

print()
print(f"Catégories détectées: {len(result.get('categories_detectees', []))}")
for cat in result.get('categories_detectees', []):
    print(f"  - {cat['nom']}: {cat['quantite']} x {cat['prix_total']}€")