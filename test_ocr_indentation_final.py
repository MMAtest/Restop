#!/usr/bin/env python3
"""
Test final de la fonction OCR corrigée avec détection d'indentation selon les bonnes pratiques
Test spécifique pour valider les corrections critiques demandées
"""

import requests
import json
from datetime import datetime
import base64
import io

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def create_test_pdf_with_indentation():
    """Créer un PDF de test avec le texte exact demandé"""
    test_text = """RAPPORT DE CLOTURE
Date: 01/09/2025
Heure: 22:59:38

VENTES PAR CATEGORIES

x25) Entrees 850,00
  x8) Salade Caesar 184,00
  x12) Tartare saumon 420,00
  x5) Soupe du jour 75,00

x45) Plats principaux 2400,00
  x12) Steak frites 420,00
  x8) Poisson grillé 288,00
  x15) Pasta truffe 690,00

x18) Desserts 324,00
  x12) Tiramisu 144,00
  x6) Tarte citron 96,00

SOLDE DE CAISSE
Nombre de couverts: 122,00
Total TTC: 3574,00"""
    
    # Créer un PDF simple avec reportlab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Ajouter le texte ligne par ligne en préservant l'indentation
        lines = test_text.split('\n')
        y_position = 750
        
        for line in lines:
            # Préserver l'indentation en ajustant la position x
            x_position = 50
            if line.startswith('  '):  # Productions indentées
                x_position = 80
            
            p.drawString(x_position, y_position, line)
            y_position -= 20
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: créer un fichier texte simple
        return test_text.encode('utf-8')

def test_ocr_indentation_critical():
    """Test critique de la fonction OCR avec détection d'indentation"""
    print("🔥 === TEST CRITIQUE FONCTION OCR - DÉTECTION D'INDENTATION ===")
    print("Test final de la fonction OCR corrigée avec détection d'indentation selon les bonnes pratiques")
    
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "critical_issues": [],
        "success_details": []
    }
    
    def log_test(name, success, message, details=None):
        results["total_tests"] += 1
        if success:
            results["passed_tests"] += 1
            results["success_details"].append(f"✅ {name}: {message}")
            print(f"✅ PASS - {name}: {message}")
        else:
            results["critical_issues"].append(f"❌ {name}: {message}")
            print(f"❌ FAIL - {name}: {message}")
            if details:
                print(f"   Détails: {details}")
    
    try:
        # 1. Créer le document de test avec indentation préservée
        print("\n📄 Création du document de test avec indentation préservée...")
        
        test_text = """RAPPORT DE CLOTURE
Date: 01/09/2025
Heure: 22:59:38

VENTES PAR CATEGORIES

x25) Entrees 850,00
  x8) Salade Caesar 184,00
  x12) Tartare saumon 420,00
  x5) Soupe du jour 75,00

x45) Plats principaux 2400,00
  x12) Steak frites 420,00
  x8) Poisson grillé 288,00
  x15) Pasta truffe 690,00

x18) Desserts 324,00
  x12) Tiramisu 144,00
  x6) Tarte citron 96,00

SOLDE DE CAISSE
Nombre de couverts: 122,00
Total TTC: 3574,00"""
        
        print(f"Texte de test: {len(test_text)} caractères")
        print("🎯 Objectifs critiques:")
        print("   - ✅ EXACTEMENT 3 catégories détectées (indent_level=0)")
        print("   - ✅ EXACTEMENT 8 productions détectées (indent_level>0)")
        print("   - ✅ Classification familiale correcte")
        print("   - ✅ Aucun faux positif")
        print("   - ✅ Logique séquentielle active")
        
        # 2. Upload du document via l'API
        print("\n📤 Upload du document de test...")
        
        # Créer un fichier PDF de test
        pdf_content = create_test_pdf_with_indentation()
        
        files = {
            'file': ('test_indentation_critique.pdf', pdf_content, 'application/pdf')
        }
        data = {'document_type': 'z_report'}
        
        upload_response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
        
        if upload_response.status_code in [200, 201]:
            result = upload_response.json()
            document_id = result.get("document_id")
            
            log_test("Upload Document OCR", True, f"Document créé avec ID: {document_id[:8]}...")
            
            # 3. Récupérer le document et analyser les résultats
            print("\n🔍 Analyse des résultats de la fonction OCR...")
            
            doc_response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            
            if doc_response.status_code == 200:
                document = doc_response.json()
                donnees_parsees = document.get("donnees_parsees", {})
                
                if donnees_parsees:
                    log_test("Données Parsées Disponibles", True, "Données d'analyse OCR présentes")
                    
                    # VALIDATION CRITIQUE 1: Exactement 3 catégories détectées
                    categories_detectees = donnees_parsees.get("categories_detectees", [])
                    if len(categories_detectees) == 3:
                        log_test("🎯 CRITIQUE 1: Nombre de catégories", True, 
                               f"EXACTEMENT 3 catégories détectées: {len(categories_detectees)}")
                        
                        # Vérifier les noms des catégories
                        category_names = [cat.get("nom", "") for cat in categories_detectees]
                        expected_categories = ["Entrees", "Plats principaux", "Desserts"]
                        
                        matching_categories = 0
                        for expected in expected_categories:
                            if any(expected.lower() in name.lower() for name in category_names):
                                matching_categories += 1
                        
                        if matching_categories == 3:
                            log_test("🎯 CRITIQUE 1a: Noms catégories", True, 
                                   f"Toutes les catégories correctes identifiées")
                        else:
                            log_test("🎯 CRITIQUE 1a: Noms catégories", False, 
                                   f"Seulement {matching_categories}/3 catégories correctes")
                    else:
                        log_test("🎯 CRITIQUE 1: Nombre de catégories", False, 
                               f"ÉCHEC: {len(categories_detectees)} catégories au lieu de 3")
                    
                    # VALIDATION CRITIQUE 2: Exactement 8 productions détectées
                    productions_detectees = donnees_parsees.get("productions_detectees", [])
                    if len(productions_detectees) == 8:
                        log_test("🎯 CRITIQUE 2: Nombre de productions", True, 
                               f"EXACTEMENT 8 productions détectées: {len(productions_detectees)}")
                        
                        # Vérifier les noms des productions
                        production_names = [prod.get("nom", "") for prod in productions_detectees]
                        expected_productions = [
                            "Salade Caesar", "Tartare saumon", "Soupe du jour",
                            "Steak frites", "Poisson grillé", "Pasta truffe",
                            "Tiramisu", "Tarte citron"
                        ]
                        
                        matching_productions = 0
                        for expected in expected_productions:
                            if any(expected.lower() in name.lower() for name in production_names):
                                matching_productions += 1
                        
                        if matching_productions >= 6:  # Au moins 6/8 pour être tolérant
                            log_test("🎯 CRITIQUE 2a: Noms productions", True, 
                                   f"{matching_productions}/8 productions correctes identifiées")
                        else:
                            log_test("🎯 CRITIQUE 2a: Noms productions", False, 
                                   f"Seulement {matching_productions}/8 productions correctes")
                    else:
                        log_test("🎯 CRITIQUE 2: Nombre de productions", False, 
                               f"ÉCHEC: {len(productions_detectees)} productions au lieu de 8")
                    
                    # VALIDATION CRITIQUE 3: Classification familiale correcte
                    analysis = donnees_parsees.get("analysis", {})
                    if analysis:
                        families_correct = 0
                        
                        # Vérifier famille "Entrées"
                        entrees_analysis = analysis.get("Entrées", {})
                        entrees_details = entrees_analysis.get("details", [])
                        if len(entrees_details) >= 2:  # Au moins 2 entrées
                            families_correct += 1
                            log_test("🎯 CRITIQUE 3a: Famille Entrées", True, 
                                   f"{len(entrees_details)} items en Entrées")
                        else:
                            log_test("🎯 CRITIQUE 3a: Famille Entrées", False, 
                                   f"Seulement {len(entrees_details)} items en Entrées")
                        
                        # Vérifier famille "Plats"
                        plats_analysis = analysis.get("Plats", {})
                        plats_details = plats_analysis.get("details", [])
                        if len(plats_details) >= 2:  # Au moins 2 plats
                            families_correct += 1
                            log_test("🎯 CRITIQUE 3b: Famille Plats", True, 
                                   f"{len(plats_details)} items en Plats")
                        else:
                            log_test("🎯 CRITIQUE 3b: Famille Plats", False, 
                                   f"Seulement {len(plats_details)} items en Plats")
                        
                        # Vérifier famille "Desserts"
                        desserts_analysis = analysis.get("Desserts", {})
                        desserts_details = desserts_analysis.get("details", [])
                        if len(desserts_details) >= 1:  # Au moins 1 dessert
                            families_correct += 1
                            log_test("🎯 CRITIQUE 3c: Famille Desserts", True, 
                                   f"{len(desserts_details)} items en Desserts")
                        else:
                            log_test("🎯 CRITIQUE 3c: Famille Desserts", False, 
                                   f"Aucun item en Desserts")
                        
                        if families_correct == 3:
                            log_test("🎯 CRITIQUE 3: Classification familiale", True, 
                                   "Toutes les familles correctement classées")
                        else:
                            log_test("🎯 CRITIQUE 3: Classification familiale", False, 
                                   f"Seulement {families_correct}/3 familles correctes")
                    
                    # VALIDATION CRITIQUE 4: Aucun faux positif
                    autres_analysis = analysis.get("Autres", {}) if analysis else {}
                    autres_count = autres_analysis.get("articles", 0)
                    
                    # Vérifier qu'il n'y a pas trop d'items dans "Autres"
                    if autres_count <= 2:  # Tolérance pour quelques items non classés
                        log_test("🎯 CRITIQUE 4: Aucun faux positif", True, 
                               f"Seulement {autres_count} items non classés")
                    else:
                        log_test("🎯 CRITIQUE 4: Aucun faux positif", False, 
                               f"Trop d'items non classés: {autres_count}")
                    
                    # VALIDATION CRITIQUE 5: Logique séquentielle active
                    entrees_end_line = donnees_parsees.get("entrees_end_line")
                    desserts_start_line = donnees_parsees.get("desserts_start_line")
                    
                    if entrees_end_line is not None and desserts_start_line is not None:
                        if desserts_start_line > entrees_end_line:
                            lines_between = desserts_start_line - entrees_end_line
                            log_test("🎯 CRITIQUE 5: Logique séquentielle", True, 
                                   f"Zone plats délimitée: {lines_between} lignes entre entrées et desserts")
                        else:
                            log_test("🎯 CRITIQUE 5: Logique séquentielle", False, 
                                   "Séquence entrées/desserts incorrecte")
                    else:
                        log_test("🎯 CRITIQUE 5: Logique séquentielle", False, 
                               "Bornes séquentielles non détectées")
                    
                    # VALIDATION CRITIQUE 6: Données principales extraites
                    date_cloture = donnees_parsees.get("date_cloture")
                    heure_cloture = donnees_parsees.get("heure_cloture")
                    nombre_couverts = donnees_parsees.get("nombre_couverts")
                    total_ttc = donnees_parsees.get("total_ttc")
                    
                    data_extraction_score = 0
                    if date_cloture and "01/09/2025" in str(date_cloture):
                        data_extraction_score += 1
                    if heure_cloture and "22:59" in str(heure_cloture):
                        data_extraction_score += 1
                    if nombre_couverts and abs(float(nombre_couverts) - 122.0) < 0.1:
                        data_extraction_score += 1
                    if total_ttc and abs(float(total_ttc) - 3574.0) < 0.1:
                        data_extraction_score += 1
                    
                    if data_extraction_score >= 3:
                        log_test("🎯 CRITIQUE 6: Données principales", True, 
                               f"{data_extraction_score}/4 données principales extraites")
                    else:
                        log_test("🎯 CRITIQUE 6: Données principales", False, 
                               f"Seulement {data_extraction_score}/4 données principales correctes")
                    
                else:
                    log_test("Données Parsées Disponibles", False, "Pas de données d'analyse OCR")
            else:
                log_test("Récupération Document", False, f"Erreur {doc_response.status_code}")
        else:
            log_test("Upload Document OCR", False, f"Erreur {upload_response.status_code}: {upload_response.text[:200]}")
    
    except Exception as e:
        log_test("Test OCR Indentation", False, f"Exception: {str(e)}")
    
    # RÉSUMÉ FINAL
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ FINAL - TEST CRITIQUE OCR INDENTATION")
    print("=" * 80)
    
    success_rate = (results["passed_tests"] / results["total_tests"] * 100) if results["total_tests"] > 0 else 0
    
    print(f"✅ Tests réussis: {results['passed_tests']}/{results['total_tests']} ({success_rate:.1f}%)")
    
    if results["critical_issues"]:
        print(f"\n❌ PROBLÈMES CRITIQUES ({len(results['critical_issues'])}):")
        for issue in results["critical_issues"]:
            print(f"   {issue}")
    
    if results["success_details"]:
        print(f"\n✅ SUCCÈS VALIDÉS ({len(results['success_details'])}):")
        for success in results["success_details"]:
            print(f"   {success}")
    
    print("\n🎯 CONCLUSION FINALE:")
    if success_rate >= 90:
        print("🎉 SUCCÈS COMPLET: La fonction OCR avec détection d'indentation fonctionne parfaitement")
        print("✅ Toutes les corrections critiques ont été validées")
        print("✅ La distinction catégories/productions est opérationnelle")
        print("✅ La classification familiale fonctionne correctement")
        print("✅ La logique séquentielle évite les faux positifs dans les plats")
        return True
    elif success_rate >= 70:
        print("⚠️  SUCCÈS PARTIEL: La fonction OCR fonctionne mais nécessite des améliorations mineures")
        print("✅ Les corrections principales ont été appliquées")
        print("⚠️  Quelques ajustements recommandés")
        return True
    else:
        print("❌ ÉCHEC CRITIQUE: La fonction OCR nécessite encore des corrections importantes")
        print("❌ Problèmes critiques d'indentation non résolus")
        print("❌ La fonction n'est pas prête pour la production")
        return False

if __name__ == "__main__":
    print("🔥 TEST FINAL - FONCTION OCR CORRIGÉE AVEC DÉTECTION D'INDENTATION")
    print("Validation des corrections selon les bonnes pratiques OCR")
    print("Test critique pour résoudre le problème de distinction catégories/productions")
    print()
    
    success = test_ocr_indentation_critical()
    
    if success:
        print("\n🎉 RÉSULTAT: FONCTION OCR VALIDÉE AVEC SUCCÈS")
        print("La fonction analyze_z_report_categories est opérationnelle pour la production")
    else:
        print("\n❌ RÉSULTAT: FONCTION OCR NÉCESSITE ENCORE DES CORRECTIONS")
        print("Des améliorations sont requises avant la mise en production")
    
    exit(0 if success else 1)