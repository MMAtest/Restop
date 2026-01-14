#!/usr/bin/env python3
"""
Test complet de la fonction analyze_z_report_categories et de l'endpoint OCR
avec création d'un vrai fichier PDF pour les tests.
"""

import requests
import json
import sys
import os
import io
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRZReportEnhancedTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_document_id = None
        
    def log_result(self, test_name, success, message="", details=None):
        """Enregistre le résultat d'un test"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")

    def create_test_z_report_pdf(self):
        """Crée un fichier PDF de test avec un rapport Z"""
        buffer = io.BytesIO()
        
        # Créer le PDF avec reportlab
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "RAPPORT DE CLOTURE")
        
        # Date et heure
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, "Date: 01/09/2025")
        c.drawString(50, height - 100, "Heure: 22:59:38")
        
        # Solde de caisse
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 140, "SOLDE DE CAISSE")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 160, "Nombre de couverts: 122,00")
        c.drawString(50, height - 180, "Total HT: 6660,26")
        c.drawString(50, height - 200, "Total TTC: 7433,00")
        
        # Ventes par catégories
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 240, "VENTES PAR CATEGORIES")
        
        c.setFont("Helvetica", 12)
        y_pos = height - 270
        
        # Catégorie Entrées avec productions
        c.drawString(50, y_pos, "x73) Entrees 1450,00")
        y_pos -= 20
        c.drawString(70, y_pos, "  x14) Moules 252,00")
        y_pos -= 20
        c.drawString(70, y_pos, "  x8) Salade Caesar 184,00")
        y_pos -= 30
        
        # Catégorie Boissons Chaudes avec productions
        c.drawString(50, y_pos, "x28) Boissons Chaudes 88,80")
        y_pos -= 20
        c.drawString(70, y_pos, "  x15) Café 45,00")
        y_pos -= 20
        c.drawString(70, y_pos, "  x13) Thé 43,80")
        y_pos -= 30
        
        # Catégorie Plats principaux avec productions
        c.drawString(50, y_pos, "x45) Plats principaux 3200,50")
        y_pos -= 20
        c.drawString(70, y_pos, "  x12) Steak frites 420,00")
        y_pos -= 20
        c.drawString(70, y_pos, "  x8) Poisson grillé 288,00")
        y_pos -= 30
        
        # Catégories Bar (à regrouper)
        c.drawString(50, y_pos, "x22) Bouteille ROUGE 445,60")
        y_pos -= 20
        c.drawString(50, y_pos, "x18) Cocktail 234,50")
        y_pos -= 30
        
        # Catégorie Desserts avec productions
        c.drawString(50, y_pos, "x15) Desserts 312,40")
        y_pos -= 20
        c.drawString(70, y_pos, "  x6) Tiramisu 108,00")
        y_pos -= 20
        c.drawString(70, y_pos, "  x9) Tarte aux pommes 204,40")
        y_pos -= 30
        
        # Total général
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_pos, "TOTAL GENERAL: 7433,00")
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    def test_direct_function_analyze_z_report(self):
        """Test direct de la fonction analyze_z_report_categories avec texte formaté correctement"""
        print("\n=== TEST FONCTION ANALYZE_Z_REPORT_CATEGORIES (DIRECT) ===")
        
        # Texte OCR avec indentation correcte pour les productions
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
        
        try:
            # Importer la fonction depuis le backend
            sys.path.append('/app/backend')
            from server import analyze_z_report_categories
            
            # Appeler la fonction directement
            result = analyze_z_report_categories(test_ocr_text)
            
            # Tests de validation selon les spécifications
            tests_passed = 0
            total_tests = 0
            
            # Test 1: Extraction correcte de la date (01/09/2025)
            total_tests += 1
            if result.get("date_cloture") == "01/09/2025":
                self.log_result("✅ Extraction Date", True, f"Date extraite: {result['date_cloture']}")
                tests_passed += 1
            else:
                self.log_result("❌ Extraction Date", False, f"Date incorrecte: {result.get('date_cloture')}")
            
            # Test 2: Extraction correcte de l'heure (22:59:38)
            total_tests += 1
            if result.get("heure_cloture") == "22:59:38":
                self.log_result("✅ Extraction Heure", True, f"Heure extraite: {result['heure_cloture']}")
                tests_passed += 1
            else:
                self.log_result("❌ Extraction Heure", False, f"Heure incorrecte: {result.get('heure_cloture')}")
            
            # Test 3: Extraction nombre de couverts (122.00)
            total_tests += 1
            if result.get("nombre_couverts") == 122.0:
                self.log_result("✅ Extraction Couverts", True, f"Couverts: {result['nombre_couverts']}")
                tests_passed += 1
            else:
                self.log_result("❌ Extraction Couverts", False, f"Couverts incorrects: {result.get('nombre_couverts')}")
            
            # Test 4: Extraction Total HT (6660.26)
            total_tests += 1
            if result.get("total_ht") == 6660.26:
                self.log_result("✅ Extraction Total HT", True, f"Total HT: {result['total_ht']}€")
                tests_passed += 1
            else:
                self.log_result("❌ Extraction Total HT", False, f"Total HT incorrect: {result.get('total_ht')}")
            
            # Test 5: Extraction Total TTC (7433.00)
            total_tests += 1
            if result.get("total_ttc") == 7433.0:
                self.log_result("✅ Extraction Total TTC", True, f"Total TTC: {result['total_ttc']}€")
                tests_passed += 1
            else:
                self.log_result("❌ Extraction Total TTC", False, f"Total TTC incorrect: {result.get('total_ttc')}")
            
            # Test 6: Détection des catégories avec quantités et prix
            total_tests += 1
            categories_detectees = result.get("categories_detectees", [])
            if len(categories_detectees) >= 5:  # Au moins 5 catégories principales
                self.log_result("✅ Détection Catégories", True, f"{len(categories_detectees)} catégories détectées")
                tests_passed += 1
                
                # Vérifier une catégorie spécifique (Entrées)
                entrees_cat = next((cat for cat in categories_detectees if "Entrees" in cat["nom"]), None)
                if entrees_cat and entrees_cat["quantite"] == 73 and entrees_cat["prix_total"] == 1450.0:
                    self.log_result("✅ Catégorie Entrées", True, f"x{entrees_cat['quantite']}) {entrees_cat['nom']} {entrees_cat['prix_total']}€")
                else:
                    self.log_result("❌ Catégorie Entrées", False, f"Données incorrectes pour Entrées: {entrees_cat}")
            else:
                self.log_result("❌ Détection Catégories", False, f"Seulement {len(categories_detectees)} catégories détectées")
            
            # Test 7: Détection des productions individuelles
            total_tests += 1
            productions_detectees = result.get("productions_detectees", [])
            if len(productions_detectees) >= 6:  # Au moins 6 productions
                self.log_result("✅ Détection Productions", True, f"{len(productions_detectees)} productions détectées")
                tests_passed += 1
                
                # Vérifier une production spécifique (Moules)
                moules_prod = next((prod for prod in productions_detectees if "Moules" in prod["nom"]), None)
                if moules_prod and moules_prod["quantite"] == 14 and moules_prod["prix_total"] == 252.0:
                    self.log_result("✅ Production Moules", True, f"x{moules_prod['quantite']}) {moules_prod['nom']} {moules_prod['prix_total']}€")
                else:
                    self.log_result("❌ Production Moules", False, f"Données incorrectes pour Moules: {moules_prod}")
            else:
                self.log_result("❌ Détection Productions", False, f"Seulement {len(productions_detectees)} productions détectées")
            
            # Test 8: Regroupement correct des boissons dans "Bar"
            total_tests += 1
            analysis = result.get("analysis", {})
            bar_analysis = analysis.get("Bar", {})
            
            # Vérifier que les boissons chaudes, bouteilles et cocktails sont regroupées dans Bar
            expected_bar_ca = 88.80 + 445.60 + 234.50  # Boissons Chaudes + Bouteille ROUGE + Cocktail
            if abs(bar_analysis.get("ca", 0) - expected_bar_ca) < 0.01:
                self.log_result("✅ Regroupement Bar", True, f"CA Bar: {bar_analysis['ca']}€ (attendu: {expected_bar_ca}€)")
                tests_passed += 1
            else:
                self.log_result("❌ Regroupement Bar", False, f"CA Bar incorrect: {bar_analysis.get('ca')}€, attendu: {expected_bar_ca}€")
            
            # Test 9: Structure de retour conforme aux spécifications
            total_tests += 1
            required_fields = [
                "date_cloture", "heure_cloture", "nombre_couverts", "total_ht", "total_ttc",
                "categories_detectees", "productions_detectees", "analysis", "verification",
                "total_categories", "total_productions"
            ]
            
            missing_fields = [field for field in required_fields if field not in result]
            if not missing_fields:
                self.log_result("✅ Structure Retour", True, "Tous les champs requis présents")
                tests_passed += 1
            else:
                self.log_result("❌ Structure Retour", False, f"Champs manquants: {missing_fields}")
            
            # Afficher le résumé du test direct
            success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
            print(f"\n📊 RÉSUMÉ TEST DIRECT: {tests_passed}/{total_tests} tests réussis ({success_rate:.1f}%)")
            
            return result
            
        except ImportError as e:
            self.log_result("❌ Import Fonction", False, f"Impossible d'importer la fonction: {str(e)}")
            return None
        except Exception as e:
            self.log_result("❌ Test Fonction", False, f"Erreur lors du test: {str(e)}")
            return None

    def test_ocr_upload_pdf(self):
        """Test upload d'un document PDF via l'endpoint OCR"""
        print("\n=== TEST UPLOAD PDF ENDPOINT OCR ===")
        
        try:
            # Créer le fichier PDF de test
            pdf_content = self.create_test_z_report_pdf()
            
            # Préparer les données pour l'upload
            files = {
                'file': ('rapport_z_test.pdf', pdf_content, 'application/pdf')
            }
            data = {
                'document_type': 'z_report'
            }
            
            # Upload du document
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                self.created_document_id = document_id
                
                self.log_result("✅ Upload PDF", True, f"Document PDF uploadé avec ID: {document_id}")
                
                # Vérifier que l'analyse est appliquée automatiquement
                texte_extrait = result.get("texte_extrait", "")
                donnees_parsees = result.get("donnees_parsees", {})
                
                if texte_extrait and len(texte_extrait) > 100:
                    self.log_result("✅ Extraction Texte PDF", True, f"Texte extrait: {len(texte_extrait)} caractères")
                else:
                    self.log_result("❌ Extraction Texte PDF", False, "Texte insuffisant extrait du PDF")
                
                if donnees_parsees and isinstance(donnees_parsees, dict):
                    self.log_result("✅ Analyse Automatique PDF", True, "Données parsées automatiquement depuis PDF")
                    
                    # Vérifier le format JSON de retour
                    self.test_json_format_compliance(donnees_parsees)
                else:
                    self.log_result("❌ Analyse Automatique PDF", False, "Données non parsées depuis PDF")
                
                return document_id
                
            else:
                self.log_result("❌ Upload PDF", False, f"Erreur {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("❌ Test Upload PDF", False, f"Exception: {str(e)}")
            return None

    def test_json_format_compliance(self, donnees_parsees):
        """Vérifie la conformité du format JSON de retour"""
        print("\n=== VÉRIFICATION CONFORMITÉ FORMAT JSON ===")
        
        try:
            # Vérifier que z_analysis est présent (nouvelle structure)
            z_analysis = donnees_parsees.get("z_analysis", {})
            if not z_analysis:
                self.log_result("❌ Z Analysis Présente", False, "z_analysis manquant dans donnees_parsees")
                return
            
            # Vérifier la structure JSON selon les spécifications dans z_analysis
            required_json_fields = [
                "date_cloture", "heure_cloture", "nombre_couverts", 
                "total_ht", "total_ttc", "analysis"
            ]
            
            missing_json_fields = [field for field in required_json_fields if field not in z_analysis]
            if not missing_json_fields:
                self.log_result("✅ Format JSON Conforme", True, "Structure JSON conforme dans z_analysis")
            else:
                self.log_result("❌ Format JSON Conforme", False, f"Champs JSON manquants dans z_analysis: {missing_json_fields}")
            
            # Vérifier les types de données
            type_checks = [
                ("date_cloture", str),
                ("heure_cloture", str),
                ("nombre_couverts", (int, float)),
                ("total_ht", (int, float)),
                ("total_ttc", (int, float)),
                ("analysis", dict)
            ]
            
            for field, expected_type in type_checks:
                if field in z_analysis:
                    actual_value = z_analysis[field]
                    if isinstance(actual_value, expected_type):
                        self.log_result(f"✅ Type {field}", True, f"{field}: {type(actual_value).__name__}")
                    else:
                        self.log_result(f"❌ Type {field}", False, f"{field}: {type(actual_value).__name__} au lieu de {expected_type}")
            
            # Vérifier la structure de l'analyse par catégories
            analysis = z_analysis.get("analysis", {})
            expected_categories = ["Bar", "Entrées", "Plats", "Desserts"]
            
            for category in expected_categories:
                if category in analysis:
                    cat_data = analysis[category]
                    if isinstance(cat_data, dict) and "articles" in cat_data and "ca" in cat_data:
                        self.log_result(f"✅ Catégorie {category}", True, f"Articles: {cat_data['articles']}, CA: {cat_data['ca']}€")
                    else:
                        self.log_result(f"❌ Catégorie {category}", False, "Structure incorrecte")
                else:
                    self.log_result(f"⚠️ Catégorie {category}", True, "Catégorie absente (normal si pas de ventes)")
            
        except Exception as e:
            self.log_result("❌ Vérification JSON", False, f"Erreur: {str(e)}")

    def test_document_retrieval_and_processing(self):
        """Test de récupération et traitement du document"""
        print("\n=== TEST RÉCUPÉRATION ET TRAITEMENT DOCUMENT ===")
        
        if not self.created_document_id:
            self.log_result("❌ Récupération Document", False, "Pas de document créé")
            return
        
        try:
            # Récupérer le document via l'API
            response = requests.get(f"{BASE_URL}/ocr/document/{self.created_document_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Vérifier que le document contient les données analysées
                required_doc_fields = ["id", "type_document", "texte_extrait", "donnees_parsees", "statut"]
                missing_doc_fields = [field for field in required_doc_fields if field not in document]
                
                if not missing_doc_fields:
                    self.log_result("✅ Document Complet", True, "Tous les champs présents")
                else:
                    self.log_result("❌ Document Complet", False, f"Champs manquants: {missing_doc_fields}")
                
                # Vérifier le statut de traitement
                if document.get("statut") == "traite":
                    self.log_result("✅ Statut Traitement", True, "Document traité avec succès")
                else:
                    self.log_result("❌ Statut Traitement", False, f"Statut incorrect: {document.get('statut')}")
                
                # Vérifier que les données parsées sont présentes et complètes
                donnees_parsees = document.get("donnees_parsees", {})
                z_analysis = donnees_parsees.get("z_analysis", {})
                
                if z_analysis and "analysis" in z_analysis:
                    self.log_result("✅ Données Parsées Complètes", True, "Analyse complète disponible dans z_analysis")
                    
                    # Test spécifique: vérifier que l'analyse contient les bonnes valeurs
                    analysis = z_analysis.get("analysis", {})
                    if "Bar" in analysis and analysis["Bar"].get("ca", 0) > 0:
                        self.log_result("✅ Analyse Bar Valide", True, f"CA Bar: {analysis['Bar']['ca']}€")
                    else:
                        self.log_result("❌ Analyse Bar Valide", False, "Analyse Bar manquante ou invalide")
                        
                else:
                    self.log_result("❌ Données Parsées Complètes", False, "z_analysis manquant ou incomplet")
                
                # Test du processus Z-report si disponible
                if document.get("type_document") == "z_report":
                    self.test_z_report_processing(self.created_document_id)
                
            else:
                self.log_result("❌ Récupération Document", False, f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("❌ Test Récupération", False, f"Exception: {str(e)}")

    def test_z_report_processing(self, document_id):
        """Test du traitement spécifique des rapports Z"""
        print("\n=== TEST TRAITEMENT RAPPORT Z ===")
        
        try:
            # Test de l'endpoint de traitement Z-report
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{document_id}", headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                if "message" in result:
                    self.log_result("✅ Traitement Z-Report", True, f"Message: {result['message']}")
                else:
                    self.log_result("❌ Traitement Z-Report", False, "Message manquant dans la réponse")
                
                # Vérifier les mises à jour de stock si présentes
                if "stock_updates" in result:
                    stock_updates = result["stock_updates"]
                    if isinstance(stock_updates, list):
                        self.log_result("✅ Mises à jour Stock", True, f"{len(stock_updates)} mises à jour de stock")
                    else:
                        self.log_result("❌ Mises à jour Stock", False, "Format incorrect pour stock_updates")
                
                # Vérifier les avertissements si présents
                if "warnings" in result:
                    warnings = result["warnings"]
                    if isinstance(warnings, list):
                        self.log_result("✅ Avertissements", True, f"{len(warnings)} avertissement(s)")
                    else:
                        self.log_result("❌ Avertissements", False, "Format incorrect pour warnings")
                        
            else:
                self.log_result("❌ Traitement Z-Report", False, f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("❌ Test Traitement Z-Report", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🎯 DÉBUT DES TESTS - FONCTION ANALYZE_Z_REPORT_CATEGORIES OPTIMISÉE")
        print("=" * 80)
        
        # Test 1: Fonction directe avec texte formaté correctement
        function_result = self.test_direct_function_analyze_z_report()
        
        # Test 2: Upload PDF et endpoint OCR complet
        document_id = self.test_ocr_upload_pdf()
        
        # Test 3: Récupération et traitement du document
        self.test_document_retrieval_and_processing()
        
        # Résumé des résultats
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ COMPLET DES TESTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✅ TESTS RÉUSSIS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # Déterminer le statut global
        if success_rate >= 90:
            print("🎉 RÉSULTAT GLOBAL: EXCELLENT - Fonction analyze_z_report_categories entièrement opérationnelle")
        elif success_rate >= 80:
            print("✅ RÉSULTAT GLOBAL: BON - Fonction analyze_z_report_categories fonctionnelle avec améliorations mineures")
        elif success_rate >= 70:
            print("⚠️ RÉSULTAT GLOBAL: ACCEPTABLE - Fonction analyze_z_report_categories nécessite quelques corrections")
        else:
            print("❌ RÉSULTAT GLOBAL: NÉCESSITE DES CORRECTIONS IMPORTANTES")

if __name__ == "__main__":
    # Exécuter les tests
    test_suite = OCRZReportEnhancedTestSuite()
    results = test_suite.run_all_tests()
    
    # Sortir avec le code approprié
    failed_count = len([r for r in results if not r["success"]])
    sys.exit(failed_count)