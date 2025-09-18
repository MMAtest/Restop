#!/usr/bin/env python3
"""
Debug script pour comprendre le problème d'indentation
"""

import sys
import re

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

print("=== ANALYSE LIGNES AVANT ET APRÈS STRIP ===")
print()

# Analyser les lignes AVANT strip
raw_lines = test_ocr_text.split('\n')
print("Lignes AVANT strip:")
for i, line in enumerate(raw_lines):
    if line and len(line.strip()) > 0:
        print(f"{i:2d}: '{line}' (len={len(line)})")
        if line.startswith(' ') or line.startswith('\t'):
            print(f"    -> INDENTÉE!")

print()

# Analyser les lignes APRÈS strip (comme dans la fonction actuelle)
stripped_lines = [l.strip() for l in test_ocr_text.split('\n') if l and len(l.strip()) > 0]
print("Lignes APRÈS strip:")
for i, line in enumerate(stripped_lines):
    print(f"{i:2d}: '{line}'")
    if line.startswith(' ') or line.startswith('\t'):
        print(f"    -> INDENTÉE!")

print()
print("CONCLUSION: Le problème est que .strip() supprime l'indentation!")
print("Il faut modifier la fonction pour préserver l'indentation.")