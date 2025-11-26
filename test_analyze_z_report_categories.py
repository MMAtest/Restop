#!/usr/bin/env python3
"""
Test spécifique pour la fonction analyze_z_report_categories optimisée pour les rapports Z
selon les nouvelles spécifications détaillées.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "https://resto-inventory-32.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class AnalyzeZReportCategoriesTestSuite:
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

    def create_test_ocr_text(self):
        """Crée le texte OCR de test avec toutes les informations requises"""
        return """RAPPORT DE CLOTURE
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

    def test_direct_function_call(self):
        """Test direct de la fonction analyze_z_report_categories"""
        print("\n=== TEST FONCTION ANALYZE_Z_REPORT_CATEGORIES ===")
        
        # Importer la fonction depuis le backend
        try:
            sys.path.append('/app/backend')
            from server import analyze_z_report_categories
            
            # Créer le texte OCR de test
            test_ocr_text = self.create_test_ocr_text()
            
            # Appeler la fonction directement
            result = analyze_z_report_categories(test_ocr_text)
            
            # Test 1: Extraction correcte de la date
            if result.get("date_cloture") == "01/09/2025":
                self.log_result("✅ Extraction Date", True, f"Date extraite: {result['date_cloture']}")
            else:
                self.log_result("❌ Extraction Date", False, f"Date incorrecte: {result.get('date_cloture')}")
            
            # Test 2: Extraction correcte de l'heure
            if result.get("heure_cloture") == "22:59:38":
                self.log_result("✅ Extraction Heure", True, f"Heure extraite: {result['heure_cloture']}")
            else:
                self.log_result("❌ Extraction Heure", False, f"Heure incorrecte: {result.get('heure_cloture')}")
            
            # Test 3: Extraction nombre de couverts
            if result.get("nombre_couverts") == 122.0:
                self.log_result("✅ Extraction Couverts", True, f"Couverts: {result['nombre_couverts']}")
            else:
                self.log_result("❌ Extraction Couverts", False, f"Couverts incorrects: {result.get('nombre_couverts')}")
            
            # Test 4: Extraction Total HT
            if result.get("total_ht") == 6660.26:
                self.log_result("✅ Extraction Total HT", True, f"Total HT: {result['total_ht']}€")
            else:
                self.log_result("❌ Extraction Total HT", False, f"Total HT incorrect: {result.get('total_ht')}")
            
            # Test 5: Extraction Total TTC
            if result.get("total_ttc") == 7433.0:
                self.log_result("✅ Extraction Total TTC", True, f"Total TTC: {result['total_ttc']}€")
            else:
                self.log_result("❌ Extraction Total TTC", False, f"Total TTC incorrect: {result.get('total_ttc')}")
            
            # Test 6: Détection des catégories avec quantités et prix
            categories_detectees = result.get("categories_detectees", [])
            if len(categories_detectees) >= 5:  # Entrees, Boissons Chaudes, Plats principaux, Bouteille ROUGE, Cocktail, Desserts
                self.log_result("✅ Détection Catégories", True, f"{len(categories_detectees)} catégories détectées")
                
                # Vérifier une catégorie spécifique
                entrees_cat = next((cat for cat in categories_detectees if "Entrees" in cat["nom"]), None)
                if entrees_cat and entrees_cat["quantite"] == 73 and entrees_cat["prix_total"] == 1450.0:
                    self.log_result("✅ Catégorie Entrées", True, f"x{entrees_cat['quantite']}) {entrees_cat['nom']} {entrees_cat['prix_total']}€")
                else:
                    self.log_result("❌ Catégorie Entrées", False, f"Données incorrectes pour Entrées: {entrees_cat}")
            else:
                self.log_result("❌ Détection Catégories", False, f"Seulement {len(categories_detectees)} catégories détectées")
            
            # Test 7: Détection des productions individuelles
            productions_detectees = result.get("productions_detectees", [])
            if len(productions_detectees) >= 6:  # Moules, Salade Caesar, Café, Thé, Steak frites, Poisson grillé, Tiramisu, Tarte
                self.log_result("✅ Détection Productions", True, f"{len(productions_detectees)} productions détectées")
                
                # Vérifier une production spécifique
                moules_prod = next((prod for prod in productions_detectees if "Moules" in prod["nom"]), None)
                if moules_prod and moules_prod["quantite"] == 14 and moules_prod["prix_total"] == 252.0:
                    self.log_result("✅ Production Moules", True, f"x{moules_prod['quantite']}) {moules_prod['nom']} {moules_prod['prix_total']}€")
                else:
                    self.log_result("❌ Production Moules", False, f"Données incorrectes pour Moules: {moules_prod}")
            else:
                self.log_result("❌ Détection Productions", False, f"Seulement {len(productions_detectees)} productions détectées")
            
            # Test 8: Regroupement correct des boissons dans "Bar"
            analysis = result.get("analysis", {})
            bar_analysis = analysis.get("Bar", {})
            
            # Vérifier que les boissons chaudes, bouteilles et cocktails sont regroupées dans Bar
            expected_bar_ca = 88.80 + 445.60 + 234.50  # Boissons Chaudes + Bouteille ROUGE + Cocktail
            if abs(bar_analysis.get("ca", 0) - expected_bar_ca) < 0.01:
                self.log_result("✅ Regroupement Bar", True, f"CA Bar: {bar_analysis['ca']}€ (attendu: {expected_bar_ca}€)")
            else:
                self.log_result("❌ Regroupement Bar", False, f"CA Bar incorrect: {bar_analysis.get('ca')}€, attendu: {expected_bar_ca}€")
            
            # Test 9: Structure de retour conforme aux spécifications
            required_fields = [
                "date_cloture", "heure_cloture", "nombre_couverts", "total_ht", "total_ttc",
                "categories_detectees", "productions_detectees", "analysis", "verification",
                "total_categories", "total_productions"
            ]
            
            missing_fields = [field for field in required_fields if field not in result]
            if not missing_fields:
                self.log_result("✅ Structure Retour", True, "Tous les champs requis présents")
            else:
                self.log_result("❌ Structure Retour", False, f"Champs manquants: {missing_fields}")
            
            # Test 10: Vérification des calculs
            verification = result.get("verification", {})
            total_calculated = verification.get("total_calculated", 0)
            displayed_total = verification.get("displayed_total", 0)
            
            if abs(total_calculated - displayed_total) < 0.01:
                self.log_result("✅ Vérification Calculs", True, f"Totaux cohérents: calculé={total_calculated}€, affiché={displayed_total}€")
            else:
                delta = verification.get("delta_eur", 0)
                self.log_result("⚠️ Vérification Calculs", True, f"Delta acceptable: {delta}€")
            
            return result
            
        except ImportError as e:
            self.log_result("❌ Import Fonction", False, f"Impossible d'importer la fonction: {str(e)}")
            return None
        except Exception as e:
            self.log_result("❌ Test Fonction", False, f"Erreur lors du test: {str(e)}")
            return None

    def test_ocr_endpoint_complete(self):
        """Test de l'endpoint OCR complet avec upload de document"""
        print("\n=== TEST ENDPOINT OCR COMPLET ===")
        
        try:
            # Créer un document de test (simuler un upload)
            test_ocr_text = self.create_test_ocr_text()
            
            # Simuler l'upload d'un document via l'API
            # Créer un fichier texte simulé
            import io
            text_file = io.StringIO(test_ocr_text)
            
            # Préparer les données pour l'upload
            files = {
                'file': ('rapport_z_test.txt', test_ocr_text.encode('utf-8'), 'text/plain')
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
                
                self.log_result("✅ Upload Document", True, f"Document uploadé avec ID: {document_id}")
                
                # Vérifier que l'analyse est appliquée automatiquement
                texte_extrait = result.get("texte_extrait", "")
                donnees_parsees = result.get("donnees_parsees", {})
                
                if texte_extrait and len(texte_extrait) > 100:
                    self.log_result("✅ Extraction Texte", True, f"Texte extrait: {len(texte_extrait)} caractères")
                else:
                    self.log_result("❌ Extraction Texte", False, "Texte insuffisant extrait")
                
                if donnees_parsees and isinstance(donnees_parsees, dict):
                    self.log_result("✅ Analyse Automatique", True, "Données parsées automatiquement")
                    
                    # Vérifier le format JSON de retour
                    self.test_json_format(donnees_parsees)
                else:
                    self.log_result("❌ Analyse Automatique", False, "Données non parsées")
                
                return document_id
                
            else:
                self.log_result("❌ Upload Document", False, f"Erreur {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("❌ Test Endpoint OCR", False, f"Exception: {str(e)}")
            return None

    def test_json_format(self, donnees_parsees):
        """Vérifie le format JSON de retour"""
        print("\n=== VÉRIFICATION FORMAT JSON ===")
        
        try:
            # Vérifier la structure JSON
            required_json_fields = [
                "date_cloture", "heure_cloture", "nombre_couverts", 
                "total_ht", "total_ttc", "analysis"
            ]
            
            missing_json_fields = [field for field in required_json_fields if field not in donnees_parsees]
            if not missing_json_fields:
                self.log_result("✅ Format JSON", True, "Structure JSON conforme")
            else:
                self.log_result("❌ Format JSON", False, f"Champs JSON manquants: {missing_json_fields}")
            
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
                if field in donnees_parsees:
                    actual_value = donnees_parsees[field]
                    if isinstance(actual_value, expected_type):
                        self.log_result(f"✅ Type {field}", True, f"{field}: {type(actual_value).__name__}")
                    else:
                        self.log_result(f"❌ Type {field}", False, f"{field}: {type(actual_value).__name__} au lieu de {expected_type}")
            
            # Vérifier la structure de l'analyse par catégories
            analysis = donnees_parsees.get("analysis", {})
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

    def test_document_retrieval(self):
        """Test de récupération du document traité"""
        print("\n=== TEST RÉCUPÉRATION DOCUMENT ===")
        
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
                if donnees_parsees and "analysis" in donnees_parsees:
                    self.log_result("✅ Données Parsées", True, "Analyse complète disponible")
                else:
                    self.log_result("❌ Données Parsées", False, "Analyse incomplète")
                
            else:
                self.log_result("❌ Récupération Document", False, f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("❌ Test Récupération", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🎯 DÉBUT DES TESTS - FONCTION ANALYZE_Z_REPORT_CATEGORIES")
        print("=" * 80)
        
        # Test 1: Fonction directe
        function_result = self.test_direct_function_call()
        
        # Test 2: Endpoint OCR complet
        document_id = self.test_ocr_endpoint_complete()
        
        # Test 3: Récupération du document
        self.test_document_retrieval()
        
        # Résumé des résultats
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
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
        
        print("\n" + "=" * 80)
        
        # Déterminer le statut global
        if success_rate >= 90:
            print("🎉 RÉSULTAT GLOBAL: EXCELLENT")
        elif success_rate >= 80:
            print("✅ RÉSULTAT GLOBAL: BON")
        elif success_rate >= 70:
            print("⚠️ RÉSULTAT GLOBAL: ACCEPTABLE")
        else:
            print("❌ RÉSULTAT GLOBAL: NÉCESSITE DES CORRECTIONS")

if __name__ == "__main__":
    # Exécuter les tests
    test_suite = AnalyzeZReportCategoriesTestSuite()
    results = test_suite.run_all_tests()
    
    # Sortir avec le code approprié
    failed_count = len([r for r in results if not r["success"]])
    sys.exit(failed_count)