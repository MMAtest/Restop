#!/usr/bin/env python3
"""
Test direct de la fonction analyze_z_report_categories du backend
Test spécifique pour la correction de la détection d'indentation
"""

import requests
import json
import base64
from datetime import datetime
import sys
import os
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRBackendDirectTest:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.document_id = None
        
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
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")

    def create_test_image_with_text(self, text_content):
        """Créer une image de test avec le texte OCR"""
        # Créer une image blanche
        img_width, img_height = 800, 1000
        image = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(image)
        
        try:
            # Essayer d'utiliser une police système
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            # Fallback vers la police par défaut
            font = ImageFont.load_default()
        
        # Dessiner le texte ligne par ligne
        lines = text_content.split('\n')
        y_position = 50
        line_height = 25
        
        for line in lines:
            # Préserver l'indentation en utilisant des espaces
            x_position = 50
            if line.startswith('  '):  # Productions indentées
                x_position = 100
            elif line.startswith('x'):  # Catégories non indentées
                x_position = 50
            
            draw.text((x_position, y_position), line, fill='black', font=font)
            y_position += line_height
        
        # Convertir en bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()

    def test_ocr_function_with_real_api(self):
        """Test de la fonction OCR avec l'API réelle"""
        print("\n🎯 === TEST FONCTION OCR VIA API RÉELLE ===")
        
        # Texte de test avec indentation claire
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

        print(f"📄 Création d'une image de test avec le texte OCR...")
        
        # Créer une image avec le texte
        image_data = self.create_test_image_with_text(test_text)
        
        try:
            # Upload de l'image via l'API OCR
            files = {
                'file': ('test_indentation.png', image_data, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            print("📤 Upload du document OCR...")
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.document_id = result.get("document_id")
                
                self.log_result("Upload Document OCR", True, f"Document créé: {self.document_id}")
                
                # Récupérer le document pour analyser les résultats
                self.analyze_ocr_results()
                
            else:
                self.log_result("Upload Document OCR", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Upload Document OCR", False, f"Exception: {str(e)}")

    def analyze_ocr_results(self):
        """Analyser les résultats de l'OCR"""
        if not self.document_id:
            self.log_result("Analyse Résultats", False, "Pas de document ID")
            return
        
        try:
            print(f"📊 Récupération du document {self.document_id}...")
            response = requests.get(f"{BASE_URL}/ocr/document/{self.document_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Vérifier le texte extrait
                texte_extrait = document.get("texte_extrait", "")
                if len(texte_extrait) > 100:
                    self.log_result("Extraction Texte OCR", True, 
                                  f"Texte extrait: {len(texte_extrait)} caractères")
                else:
                    self.log_result("Extraction Texte OCR", False, 
                                  f"Texte insuffisant: {len(texte_extrait)} caractères")
                
                # Analyser les données parsées
                donnees_parsees = document.get("donnees_parsees", {})
                if donnees_parsees:
                    self.analyze_parsed_data(donnees_parsees)
                else:
                    self.log_result("Données Parsées", False, "Pas de données parsées disponibles")
                    
            else:
                self.log_result("Récupération Document", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Analyse Résultats", False, f"Exception: {str(e)}")

    def analyze_parsed_data(self, donnees_parsees):
        """Analyser les données parsées en détail"""
        print("\n📈 ANALYSE DÉTAILLÉE DES DONNÉES PARSÉES:")
        
        # 1. Vérifier l'extraction des données principales
        self.check_main_data_extraction(donnees_parsees)
        
        # 2. Vérifier la détection des catégories
        self.check_categories_detection(donnees_parsees)
        
        # 3. Vérifier la détection des productions
        self.check_productions_detection(donnees_parsees)
        
        # 4. Vérifier l'analyse par familles
        self.check_family_analysis(donnees_parsees)
        
        # 5. Vérifier la logique séquentielle
        self.check_sequential_logic(donnees_parsees)

    def check_main_data_extraction(self, donnees_parsees):
        """Vérifier l'extraction des données principales"""
        print("\n📊 1. DONNÉES PRINCIPALES:")
        
        # Date de clôture
        date_cloture = donnees_parsees.get("date_cloture")
        if date_cloture and "01/09/2025" in date_cloture:
            self.log_result("Date Clôture", True, f"Date extraite: {date_cloture}")
        else:
            self.log_result("Date Clôture", False, f"Date incorrecte: {date_cloture}")
        
        # Heure de clôture
        heure_cloture = donnees_parsees.get("heure_cloture")
        if heure_cloture and "22:59:38" in heure_cloture:
            self.log_result("Heure Clôture", True, f"Heure extraite: {heure_cloture}")
        else:
            self.log_result("Heure Clôture", False, f"Heure incorrecte: {heure_cloture}")
        
        # Nombre de couverts
        nombre_couverts = donnees_parsees.get("nombre_couverts")
        if nombre_couverts == 122.0:
            self.log_result("Nombre Couverts", True, f"Couverts: {nombre_couverts}")
        else:
            self.log_result("Nombre Couverts", False, f"Couverts incorrect: {nombre_couverts}")
        
        # Total TTC
        total_ttc = donnees_parsees.get("total_ttc")
        if total_ttc == 3574.0:
            self.log_result("Total TTC", True, f"Total TTC: {total_ttc}€")
        else:
            self.log_result("Total TTC", False, f"Total TTC incorrect: {total_ttc}")

    def check_categories_detection(self, donnees_parsees):
        """Vérifier la détection des catégories"""
        print("\n📂 2. DÉTECTION CATÉGORIES:")
        
        categories_detectees = donnees_parsees.get("categories_detectees", [])
        
        # Vérifier le nombre de catégories
        if len(categories_detectees) == 3:
            self.log_result("Nombre Catégories", True, f"3 catégories détectées")
        else:
            self.log_result("Nombre Catégories", False, 
                          f"Attendu: 3, Trouvé: {len(categories_detectees)}")
        
        # Vérifier chaque catégorie attendue
        expected_categories = {
            "Entrees": {"quantite": 25, "prix_total": 850.0},
            "Plats principaux": {"quantite": 45, "prix_total": 2400.0},
            "Desserts": {"quantite": 18, "prix_total": 324.0}
        }
        
        for category in categories_detectees:
            nom = category.get("nom", "")
            quantite = category.get("quantite", 0)
            prix_total = category.get("prix_total", 0)
            indent_level = category.get("indent_level", -1)
            
            # Vérifier que c'est bien une catégorie (indent_level = 0)
            if indent_level == 0:
                self.log_result(f"Catégorie {nom} - Indentation", True, 
                              f"indent_level = 0 (catégorie)")
            else:
                self.log_result(f"Catégorie {nom} - Indentation", False, 
                              f"indent_level = {indent_level} (devrait être 0)")
            
            # Vérifier les valeurs
            for expected_name, expected_values in expected_categories.items():
                if expected_name.lower() in nom.lower():
                    if quantite == expected_values["quantite"]:
                        self.log_result(f"Catégorie {nom} - Quantité", True, 
                                      f"Quantité: {quantite}")
                    else:
                        self.log_result(f"Catégorie {nom} - Quantité", False, 
                                      f"Quantité: {quantite}, attendu: {expected_values['quantite']}")
                    
                    if abs(prix_total - expected_values["prix_total"]) < 0.01:
                        self.log_result(f"Catégorie {nom} - Prix", True, 
                                      f"Prix: {prix_total}€")
                    else:
                        self.log_result(f"Catégorie {nom} - Prix", False, 
                                      f"Prix: {prix_total}€, attendu: {expected_values['prix_total']}€")

    def check_productions_detection(self, donnees_parsees):
        """Vérifier la détection des productions"""
        print("\n🍽️ 3. DÉTECTION PRODUCTIONS:")
        
        productions_detectees = donnees_parsees.get("productions_detectees", [])
        
        # Vérifier le nombre de productions
        if len(productions_detectees) == 8:
            self.log_result("Nombre Productions", True, f"8 productions détectées")
        else:
            self.log_result("Nombre Productions", False, 
                          f"Attendu: 8, Trouvé: {len(productions_detectees)}")
        
        # Vérifier les productions attendues
        expected_productions = [
            {"nom": "Salade Caesar", "quantite": 8, "prix_total": 184.0, "family": "Entrées"},
            {"nom": "Tartare saumon", "quantite": 12, "prix_total": 420.0, "family": "Entrées"},
            {"nom": "Soupe du jour", "quantite": 5, "prix_total": 75.0, "family": "Entrées"},
            {"nom": "Steak frites", "quantite": 12, "prix_total": 420.0, "family": "Plats"},
            {"nom": "Poisson grillé", "quantite": 8, "prix_total": 288.0, "family": "Plats"},
            {"nom": "Pasta truffe", "quantite": 15, "prix_total": 690.0, "family": "Plats"},
            {"nom": "Tiramisu", "quantite": 12, "prix_total": 144.0, "family": "Desserts"},
            {"nom": "Tarte citron", "quantite": 6, "prix_total": 96.0, "family": "Desserts"}
        ]
        
        for production in productions_detectees:
            nom = production.get("nom", "")
            quantite = production.get("quantite", 0)
            prix_total = production.get("prix_total", 0)
            indent_level = production.get("indent_level", -1)
            family = production.get("family", "")
            
            # Vérifier que c'est bien une production (indent_level > 0)
            if indent_level > 0:
                self.log_result(f"Production {nom} - Indentation", True, 
                              f"indent_level = {indent_level} (production)")
            else:
                self.log_result(f"Production {nom} - Indentation", False, 
                              f"indent_level = {indent_level} (devrait être > 0)")
            
            # Trouver la production attendue correspondante
            expected = next((p for p in expected_productions if p["nom"] in nom), None)
            if expected:
                # Vérifier la famille
                if family == expected["family"]:
                    self.log_result(f"Production {nom} - Famille", True, 
                                  f"Famille: {family}")
                else:
                    self.log_result(f"Production {nom} - Famille", False, 
                                  f"Famille: {family}, attendu: {expected['family']}")

    def check_family_analysis(self, donnees_parsees):
        """Vérifier l'analyse par familles"""
        print("\n🏷️ 4. ANALYSE PAR FAMILLES:")
        
        analysis = donnees_parsees.get("analysis", {})
        
        expected_families = {
            "Entrées": {"articles": 25, "ca": 850.0},
            "Plats": {"articles": 45, "ca": 2400.0},
            "Desserts": {"articles": 18, "ca": 324.0}
        }
        
        for family_name, expected_data in expected_families.items():
            family_analysis = analysis.get(family_name, {})
            articles = family_analysis.get("articles", 0)
            ca = family_analysis.get("ca", 0)
            
            if articles == expected_data["articles"]:
                self.log_result(f"Famille {family_name} - Articles", True, 
                              f"Articles: {articles}")
            else:
                self.log_result(f"Famille {family_name} - Articles", False, 
                              f"Articles: {articles}, attendu: {expected_data['articles']}")
            
            if abs(ca - expected_data["ca"]) < 0.01:
                self.log_result(f"Famille {family_name} - CA", True, 
                              f"CA: {ca}€")
            else:
                self.log_result(f"Famille {family_name} - CA", False, 
                              f"CA: {ca}€, attendu: {expected_data['ca']}€")

    def check_sequential_logic(self, donnees_parsees):
        """Vérifier la logique séquentielle"""
        print("\n🔄 5. LOGIQUE SÉQUENTIELLE:")
        
        entrees_end_line = donnees_parsees.get("entrees_end_line")
        desserts_start_line = donnees_parsees.get("desserts_start_line")
        
        if entrees_end_line is not None and desserts_start_line is not None:
            if entrees_end_line < desserts_start_line:
                self.log_result("Bornes Séquentielles", True, 
                              f"Entrées finissent ligne {entrees_end_line}, Desserts commencent ligne {desserts_start_line}")
            else:
                self.log_result("Bornes Séquentielles", False, 
                              f"Ordre incorrect: entrées={entrees_end_line}, desserts={desserts_start_line}")
        else:
            self.log_result("Bornes Séquentielles", False, 
                          f"Bornes non définies: entrées={entrees_end_line}, desserts={desserts_start_line}")

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉMARRAGE DES TESTS OCR BACKEND DIRECT")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Test principal
        self.test_ocr_function_with_real_api()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Résumé des résultats
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS OCR BACKEND DIRECT")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Tests réussis: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Durée totale: {duration:.2f}s")
        
        # Détail des échecs
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ TESTS ÉCHOUÉS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        # Conclusion spécifique
        print("\n🎯 CONCLUSION FONCTION OCR OPTIMISÉE:")
        
        # Analyser les résultats critiques
        critical_tests = [
            "Nombre Catégories", "Nombre Productions", 
            "Production Salade Caesar - Indentation", "Production Steak frites - Indentation",
            "Famille Entrées - Articles", "Famille Plats - Articles", "Famille Desserts - Articles"
        ]
        
        critical_passed = sum(1 for r in self.test_results 
                            if r["success"] and any(ct in r["test"] for ct in critical_tests))
        critical_total = sum(1 for r in self.test_results 
                           if any(ct in r["test"] for ct in critical_tests))
        
        if critical_total > 0:
            critical_rate = (critical_passed / critical_total * 100)
            print(f"🎯 Tests critiques: {critical_passed}/{critical_total} ({critical_rate:.1f}%)")
            
            if critical_rate >= 90:
                print("✅ FONCTION OCR OPTIMISÉE - PROBLÈMES RÉSOLUS: Détection d'indentation corrigée")
            elif critical_rate >= 70:
                print("⚠️  FONCTION OCR OPTIMISÉE - PARTIELLEMENT CORRIGÉE: Quelques problèmes persistent")
            else:
                print("❌ FONCTION OCR OPTIMISÉE - PROBLÈMES PERSISTENT: Corrections importantes nécessaires")
        
        return success_rate >= 70

if __name__ == "__main__":
    print("🎯 TEST DIRECT FONCTION OCR BACKEND")
    print("Test spécifique de la fonction analyze_z_report_categories corrigée")
    print("Vérification de la détection d'indentation améliorée")
    print()
    
    test_suite = OCRBackendDirectTest()
    success = test_suite.run_all_tests()
    
    # Code de sortie
    sys.exit(0 if success else 1)