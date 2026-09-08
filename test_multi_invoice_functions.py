#!/usr/bin/env python3
"""
Test direct des fonctions detect_multiple_invoices() et check_invoice_quality()
"""

import sys
import os
sys.path.append('/app/backend')

# Import des fonctions depuis server.py
from server import detect_multiple_invoices, check_invoice_quality

def test_detect_multiple_invoices():
    """Test de la fonction detect_multiple_invoices"""
    print("🔍 TEST DETECT_MULTIPLE_INVOICES")
    print("=" * 50)
    
    # Test 1: Texte avec plusieurs factures METRO
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
    
    print("📝 Test avec texte multi-factures (4 factures attendues)")
    result = detect_multiple_invoices(multi_invoice_text)
    
    print(f"📊 Résultat: {len(result)} facture(s) détectée(s)")
    
    for i, invoice in enumerate(result):
        print(f"\n📄 Facture {i+1}:")
        print(f"   Index: {invoice.get('index', 'N/A')}")
        print(f"   Header: {invoice.get('header', 'N/A')}")
        print(f"   Longueur texte: {len(invoice.get('text_content', ''))}")
        print(f"   Position: {invoice.get('start_position', 'N/A')}-{invoice.get('end_position', 'N/A')}")
        print(f"   Score qualité: {invoice.get('quality_score', 'N/A')}")
        print(f"   Issues qualité: {len(invoice.get('quality_issues', []))}")
        
        # Aperçu du texte
        text_preview = invoice.get('text_content', '')[:100].replace('\n', ' ')
        print(f"   Aperçu: {text_preview}...")
    
    # Test 2: Texte avec une seule facture
    print("\n" + "=" * 50)
    print("📝 Test avec texte facture unique")
    
    single_invoice_text = """
FACTURE N°UNIQUE-001
Date: 05/01/2025
Fournisseur: Fournisseur Unique SARL
Produits:
- Produit A 5kg x 4.00€ = 20.00€
- Produit B 3kg x 6.00€ = 18.00€
Total HT: 38.00€
TVA: 7.60€
NET A PAYER: 45.60€
"""
    
    result_single = detect_multiple_invoices(single_invoice_text)
    print(f"📊 Résultat: {len(result_single)} facture(s) détectée(s)")
    
    if len(result_single) == 1:
        print("✅ Facture unique correctement détectée")
    else:
        print(f"❌ Erreur: {len(result_single)} factures au lieu de 1")
    
    # Test 3: Texte vide ou invalide
    print("\n" + "=" * 50)
    print("📝 Test avec texte invalide")
    
    result_empty = detect_multiple_invoices("")
    print(f"📊 Texte vide: {len(result_empty)} facture(s)")
    
    result_short = detect_multiple_invoices("Texte trop court")
    print(f"📊 Texte court: {len(result_short)} facture(s)")
    
    return len(result) == 4  # Succès si 4 factures détectées

def test_check_invoice_quality():
    """Test de la fonction check_invoice_quality"""
    print("\n🔍 TEST CHECK_INVOICE_QUALITY")
    print("=" * 50)
    
    # Test 1: Facture de bonne qualité
    good_quality_text = """
FACTURE N°12345
Date: 01/01/2025
Fournisseur: Excellent Fournisseur SARL
Adresse: 123 Rue de la Qualité, 75001 Paris
Téléphone: 01.23.45.67.89
Email: contact@excellent-fournisseur.fr

Produits:
- Tomates biologiques 10kg x 2.50€ = 25.00€
- Salade verte 5kg x 3.00€ = 15.00€
- Carottes du jardin 8kg x 1.80€ = 14.40€

Sous-total HT: 54.40€
TVA 20%: 10.88€
TOTAL TTC: 65.28€
NET A PAYER: 65.28€

Conditions de paiement: 30 jours
Merci de votre confiance
"""
    
    print("📝 Test facture de bonne qualité")
    quality_result = check_invoice_quality(good_quality_text)
    
    print(f"✅ Valide: {quality_result['is_valid']}")
    print(f"📊 Score: {quality_result['score']}")
    print(f"⚠️ Issues: {len(quality_result['issues'])}")
    
    if quality_result['issues']:
        for issue in quality_result['issues']:
            print(f"   - {issue}")
    
    # Test 2: Facture de mauvaise qualité
    print("\n" + "-" * 30)
    print("📝 Test facture de mauvaise qualité")
    
    bad_quality_text = """
F@CT#RE N°??? 
D@te: ??/??/????
F0urn1sseur: |||||||||||
@dr3sse: ###########

Pr0du1ts:
- ???????? ??kg x ?.??€ = ??.??€
- |||||||||| ??kg x ?.??€ = ??.??€

T0t@l: ??.??€
"""
    
    bad_quality_result = check_invoice_quality(bad_quality_text)
    
    print(f"✅ Valide: {bad_quality_result['is_valid']}")
    print(f"📊 Score: {bad_quality_result['score']}")
    print(f"⚠️ Issues: {len(bad_quality_result['issues'])}")
    
    if bad_quality_result['issues']:
        for issue in bad_quality_result['issues']:
            print(f"   - {issue}")
    
    # Test 3: Facture très courte
    print("\n" + "-" * 30)
    print("📝 Test facture très courte")
    
    short_text = "FACTURE 123 Total: 50€"
    short_result = check_invoice_quality(short_text)
    
    print(f"✅ Valide: {short_result['is_valid']}")
    print(f"📊 Score: {short_result['score']}")
    print(f"⚠️ Issues: {len(short_result['issues'])}")
    
    # Test 4: Vérification des seuils
    print("\n" + "-" * 30)
    print("📝 Vérification des seuils de qualité")
    
    print(f"Bonne qualité (score {quality_result['score']:.2f}): {'✅ Acceptée' if quality_result['score'] >= 0.6 else '❌ Rejetée'}")
    print(f"Mauvaise qualité (score {bad_quality_result['score']:.2f}): {'✅ Acceptée' if bad_quality_result['score'] >= 0.6 else '❌ Rejetée'}")
    print(f"Facture courte (score {short_result['score']:.2f}): {'✅ Acceptée' if short_result['score'] >= 0.6 else '❌ Rejetée'}")
    
    return (quality_result['is_valid'] and 
            not bad_quality_result['is_valid'] and 
            not short_result['is_valid'])

def test_integration():
    """Test d'intégration des deux fonctions"""
    print("\n🔗 TEST D'INTÉGRATION")
    print("=" * 50)
    
    # Texte avec plusieurs factures de qualités différentes
    mixed_quality_text = """
METRO FRANCE FACTURE N°GOOD-001
Date: 01/01/2025
Fournisseur: METRO Cash & Carry France
Adresse: 123 Avenue des Professionnels, 75001 Paris
Produits de qualité:
- Tomates fraîches 10kg x 2.50€ = 25.00€
- Salade iceberg 5kg x 3.00€ = 15.00€
Total HT: 40.00€
TVA 20%: 8.00€
NET A PAYER: 48.00€

F@CT#RE N°B@D-002
D@te: ??/??/????
F0urn1sseur: |||||||||||
Pr0du1ts:
- ???????? x ?.??€
T0t@l: ??.??€

LE DIAMANT DU TERROIR FACTURE N°EXCELLENT-003
Date: 03/01/2025
Fournisseur: Le Diamant du Terroir SARL
Spécialiste des produits du terroir français
Adresse: 456 Route des Vignobles, 33000 Bordeaux
Produits premium:
- Fromage de chèvre fermier 2kg x 15.00€ = 30.00€
- Miel de lavande artisanal 1kg x 12.00€ = 12.00€
- Confiture de figues maison 500g x 8.00€ = 4.00€
Sous-total HT: 46.00€
TVA 5.5%: 2.53€
TOTAL TTC: 48.53€
NET A PAYER: 48.53€
Merci de votre confiance
"""
    
    print("📝 Test avec factures de qualités mixtes")
    
    # Détecter les factures
    invoices = detect_multiple_invoices(mixed_quality_text)
    print(f"📊 {len(invoices)} factures détectées")
    
    # Analyser la qualité de chaque facture
    good_quality_count = 0
    bad_quality_count = 0
    
    for i, invoice in enumerate(invoices):
        quality = check_invoice_quality(invoice['text_content'])
        print(f"\n📄 Facture {invoice['index']}:")
        print(f"   Header: {invoice['header']}")
        print(f"   Score qualité: {quality['score']:.2f}")
        print(f"   Statut: {'✅ Acceptée' if quality['is_valid'] else '❌ Rejetée'}")
        
        if quality['is_valid']:
            good_quality_count += 1
        else:
            bad_quality_count += 1
            print(f"   Issues: {', '.join(quality['issues'])}")
    
    print(f"\n📊 Résumé:")
    print(f"   Factures acceptées: {good_quality_count}")
    print(f"   Factures rejetées: {bad_quality_count}")
    print(f"   Total détectées: {len(invoices)}")
    
    return len(invoices) >= 2 and good_quality_count >= 1 and bad_quality_count >= 1

if __name__ == "__main__":
    print("🎯 TEST DES FONCTIONS MULTI-INVOICE OCR")
    print("=" * 80)
    
    # Exécuter les tests
    test1_success = test_detect_multiple_invoices()
    test2_success = test_check_invoice_quality()
    test3_success = test_integration()
    
    # Résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    print(f"✅ Test detect_multiple_invoices: {'RÉUSSI' if test1_success else 'ÉCHOUÉ'}")
    print(f"✅ Test check_invoice_quality: {'RÉUSSI' if test2_success else 'ÉCHOUÉ'}")
    print(f"✅ Test intégration: {'RÉUSSI' if test3_success else 'ÉCHOUÉ'}")
    
    total_success = sum([test1_success, test2_success, test3_success])
    print(f"\n📈 Taux de réussite: {total_success}/3 ({total_success/3*100:.1f}%)")
    
    if total_success == 3:
        print("🎉 TOUS LES TESTS RÉUSSIS - Fonctions multi-invoice opérationnelles!")
    else:
        print("⚠️ CERTAINS TESTS ÉCHOUÉS - Vérification nécessaire")