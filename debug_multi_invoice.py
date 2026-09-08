#!/usr/bin/env python3
"""
Debug de la fonction detect_multiple_invoices
"""

import re

def debug_detect_multiple_invoices(text_content):
    """Version debug de detect_multiple_invoices"""
    print("🔍 DEBUG DETECT_MULTIPLE_INVOICES")
    print("=" * 50)
    print(f"📝 Texte d'entrée: {len(text_content)} caractères")
    print(f"Aperçu: {text_content[:200]}...")
    
    # Patterns améliorés basés sur l'analyse du PDF METRO
    invoice_separators = [
        # Patterns spécifiques METRO et autres fournisseurs français
        r'METRO\s+(?:FRANCE\s+)?[A-Z\s]*(?:FACTURE|Facture)',
        r'(?:FACTURE|Facture)\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
        r'(?:INVOICE|Invoice)\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
        r'BON\s*DE\s*LIVRAISON\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
        r'BL\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
        # Patterns pour fournisseurs spécifiques
        r'LE\s+DIAMANT\s+DU\s+TERROIR',
        r'RM\s+MAREE',
        r'GFD\s+LERDA',
        r'LE\s+ROYAUME\s+DES\s+MERS',
        # Patterns génériques d'en-têtes de factures
        r'(?:^|\n)\s*[A-Z][A-Z\s&]+(?:SARL|SAS|SA|EURL)\s*(?:\n|$)',
        # Totaux qui indiquent la fin d'une facture
        r'NET\s*[AÀ]\s*PAYER\s*:?\s*\d+[,.]?\d*\s*€?',
        r'TOTAL\s*TTC\s*:?\s*\d+[,.]?\d*\s*€?',
        r'MONTANT\s*TOTAL\s*:?\s*\d+[,.]?\d*\s*€?'
    ]
    
    # Rechercher tous les indicateurs de factures
    invoice_positions = []
    
    print("\n🔍 Recherche des patterns:")
    for i, pattern in enumerate(invoice_separators):
        matches = list(re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE))
        print(f"Pattern {i}: {pattern}")
        print(f"   Matches: {len(matches)}")
        
        for match in matches:
            match_text = match.group().strip()
            print(f"   - Position {match.start()}: '{match_text}'")
            invoice_positions.append({
                'type': 'header' if i < 10 else 'footer',
                'position': match.start(),
                'text': match_text,
                'pattern_index': i
            })
    
    print(f"\n📊 Total positions trouvées: {len(invoice_positions)}")
    
    # Filtrer et nettoyer les positions
    if len(invoice_positions) > 1:
        print("✅ Plusieurs positions détectées - traitement multi-factures")
        
        # Trier par position
        invoice_positions.sort(key=lambda x: x['position'])
        
        print("\n📋 Positions triées:")
        for pos in invoice_positions:
            print(f"   Position {pos['position']}: {pos['text']} (type: {pos['type']})")
        
        # Grouper les headers proches (même facture)
        grouped_positions = []
        current_group = [invoice_positions[0]]
        
        for pos in invoice_positions[1:]:
            # Si la position est dans les 500 caractères suivants, c'est probablement la même facture
            if pos['position'] - current_group[-1]['position'] <= 500:
                current_group.append(pos)
                print(f"   Groupé avec précédent: {pos['text']}")
            else:
                grouped_positions.append(current_group)
                current_group = [pos]
                print(f"   Nouveau groupe: {pos['text']}")
        
        grouped_positions.append(current_group)
        
        print(f"\n📊 {len(grouped_positions)} groupes de factures détectés")
        
        for i, group in enumerate(grouped_positions):
            print(f"   Groupe {i+1}: {len(group)} éléments")
            for elem in group:
                print(f"      - {elem['text']}")
        
        return len(grouped_positions)
    else:
        print("❌ Une seule position ou aucune - facture unique")
        return 1

# Test avec le texte multi-factures
multi_invoice_text = """
METRO FRANCE FACTURE N°12345
Date: 01/01/2025
Fournisseur: METRO Cash & Carry France
Produits:
- Tomates 10kg x 2.50€ = 25.00€
- Salade 5kg x 3.00€ = 15.00€
Total HT: 40.00€
TVA: 8.00€
NET A PAYER: 48.00€

METRO FRANCE FACTURE N°12346
Date: 02/01/2025
Fournisseur: METRO Cash & Carry France
Produits:
- Pommes 8kg x 2.80€ = 22.40€
- Carottes 6kg x 1.50€ = 9.00€
Total HT: 31.40€
TVA: 6.28€
NET A PAYER: 37.68€

LE DIAMANT DU TERROIR
BON DE LIVRAISON N°67890
Date: 03/01/2025
Produits de qualité premium
Produits:
- Fromage de chèvre 2kg x 15.00€ = 30.00€
- Miel artisanal 1kg x 12.00€ = 12.00€
TOTAL TTC: 42.00€

GFD LERDA INVOICE ABC123
Date: 04/01/2025
Spécialités italiennes authentiques
Produits:
- Parmesan Reggiano 1kg x 25.00€ = 25.00€
- Huile d'olive extra vierge 500ml x 8.00€ = 8.00€
MONTANT TOTAL: 33.00€
"""

if __name__ == "__main__":
    result = debug_detect_multiple_invoices(multi_invoice_text)