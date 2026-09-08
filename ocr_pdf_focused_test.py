#!/usr/bin/env python3
"""
Test spécifique pour vérifier la complétude de l'extraction OCR PDF 
en utilisant le document existant ztableauaugustinedigital.pdf
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRPDFCompletenessTest:
    def __init__(self):
        self.test_results = []
        
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

    def test_existing_pdf_extraction_completeness(self):
        """Test de complétude sur le PDF existant ztableauaugustinedigital.pdf"""
        print("\n=== TEST COMPLÉTUDE EXTRACTION PDF EXISTANT ===")
        
        try:
            # Récupérer la liste des documents pour trouver le PDF
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code != 200:
                self.log_result("Get OCR Documents", False, f"Échec récupération liste (HTTP {response.status_code})")
                return None
            
            documents = response.json()
            
            # Trouver le document PDF ztableauaugustinedigital.pdf
            target_pdf = None
            for doc in documents:
                if doc.get('nom_fichier') == 'ztableauaugustinedigital.pdf' and doc.get('file_type') == 'pdf':
                    target_pdf = doc
                    break
            
            if not target_pdf:
                self.log_result("Find Target PDF", False, "Document ztableauaugustinedigital.pdf non trouvé")
                return None
            
            document_id = target_pdf['id']
            texte_extrait = target_pdf.get('texte_extrait', '')
            
            print(f"📄 Document trouvé: {document_id[:8]}...")
            print(f"📏 Longueur texte extrait: {len(texte_extrait)} caractères")
            print(f"📝 Aperçu texte: {texte_extrait[:100]}...")
            
            # Vérifications de complétude spécifiques au contenu attendu
            completeness_checks = {
                "Longueur substantielle (>400 chars)": len(texte_extrait) > 400,
                "Contient titre rapport": any(phrase in texte_extrait for phrase in ['RAPPORT Z', 'LA TABLE', 'AUGUSTINE']),
                "Contient date": any(date_pattern in texte_extrait for date_pattern in ['15/12/2024', '2024', 'Service']),
                "Contient catégorie BAR": 'BAR' in texte_extrait,
                "Contient catégorie ENTRÉES": any(word in texte_extrait for word in ['ENTRÉES', 'ENTREES']),
                "Contient catégorie PLATS": 'PLATS' in texte_extrait,
                "Contient catégorie DESSERTS": 'DESSERTS' in texte_extrait,
                "Contient items spécifiques": any(item in texte_extrait for item in ['Supions', 'Linguine', 'Wellington', 'Tiramisu']),
                "Contient boissons": any(drink in texte_extrait for drink in ['Vin rouge', 'Pastis', 'Côtes du Rhône']),
                "Contient total CA": any(total in texte_extrait for total in ['TOTAL CA', '456.50', 'CA:']),
                "Contient nombre couverts": any(couverts in texte_extrait for couverts in ['couverts', '18'])
            }
            
            passed_checks = sum(1 for check in completeness_checks.values() if check)
            total_checks = len(completeness_checks)
            
            success_threshold = 8  # Au moins 8/11 vérifications doivent passer
            
            if passed_checks >= success_threshold:
                self.log_result("PDF Extraction Completeness", True, 
                              f"Extraction complète validée ({passed_checks}/{total_checks} vérifications passées, {len(texte_extrait)} caractères)",
                              {
                                  "document_id": document_id,
                                  "texte_length": len(texte_extrait),
                                  "checks_passed": f"{passed_checks}/{total_checks}",
                                  "passed_checks": [check for check, result in completeness_checks.items() if result],
                                  "failed_checks": [check for check, result in completeness_checks.items() if not result]
                              })
            else:
                self.log_result("PDF Extraction Completeness", False, 
                              f"Extraction incomplète ({passed_checks}/{total_checks} vérifications passées)",
                              {
                                  "failed_checks": [check for check, result in completeness_checks.items() if not result],
                                  "texte_extrait_sample": texte_extrait[:300]
                              })
            
            return document_id, texte_extrait
            
        except Exception as e:
            self.log_result("PDF Extraction Completeness", False, "Exception", str(e))
            return None, None

    def test_get_document_full_texte_extrait(self, document_id):
        """Test GET /api/ocr/document/{id} pour vérifier texte_extrait complet"""
        print("\n=== TEST GET DOCUMENT TEXTE_EXTRAIT COMPLET ===")
        
        if not document_id:
            self.log_result("GET Document Full texte_extrait", False, "Pas de document_id disponible")
            return
        
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                document_data = response.json()
                texte_extrait = document_data.get('texte_extrait', '')
                
                # Vérifications du contenu complet retourné par l'API
                api_checks = {
                    "Réponse rapide (<2s)": response_time < 2.0,
                    "Document ID correct": document_data.get('id') == document_id,
                    "Type document z_report": document_data.get('type_document') == 'z_report',
                    "File type PDF": document_data.get('file_type') == 'pdf',
                    "Texte extrait présent": len(texte_extrait) > 0,
                    "Texte extrait long (>400 chars)": len(texte_extrait) > 400,
                    "Données parsées présentes": document_data.get('donnees_parsees') is not None,
                    "Statut traité": document_data.get('statut') == 'traite',
                    "Nom fichier correct": 'ztableauaugustinedigital.pdf' in document_data.get('nom_fichier', ''),
                    "Contient catégories multiples": len([cat for cat in ['BAR', 'ENTRÉES', 'PLATS', 'DESSERTS'] if cat in texte_extrait]) >= 3
                }
                
                passed_checks = sum(1 for check in api_checks.values() if check)
                total_checks = len(api_checks)
                
                if passed_checks >= 8:  # Au moins 80% des vérifications
                    self.log_result("GET Document Full texte_extrait", True, 
                                  f"API retourne texte_extrait complet ({passed_checks}/{total_checks} vérifications, {len(texte_extrait)} chars, {response_time:.2f}s)",
                                  {
                                      "response_time": response_time,
                                      "texte_length": len(texte_extrait),
                                      "categories_found": [cat for cat in ['BAR', 'ENTRÉES', 'PLATS', 'DESSERTS'] if cat in texte_extrait]
                                  })
                else:
                    self.log_result("GET Document Full texte_extrait", False, 
                                  f"API retourne contenu incomplet ({passed_checks}/{total_checks} vérifications)",
                                  {
                                      "failed_checks": [check for check, result in api_checks.items() if not result],
                                      "response_time": response_time
                                  })
            else:
                self.log_result("GET Document Full texte_extrait", False, 
                              f"Échec récupération document (HTTP {response.status_code})", response.text)
                
        except Exception as e:
            self.log_result("GET Document Full texte_extrait", False, "Exception", str(e))

    def test_multi_line_category_detection(self, texte_extrait):
        """Test spécifique pour détecter les lignes de catégories multiples"""
        print("\n=== TEST DÉTECTION CATÉGORIES MULTIPLES ===")
        
        if not texte_extrait:
            self.log_result("Multi-line Category Detection", False, "Pas de texte extrait disponible")
            return
        
        try:
            # Analyser le texte pour détecter les catégories et leurs items
            categories_found = {}
            lines = texte_extrait.split('\n')
            
            current_category = None
            for line in lines:
                line = line.strip()
                
                # Détecter les en-têtes de catégories
                if any(cat in line.upper() for cat in ['BAR:', 'ENTRÉES:', 'PLATS:', 'DESSERTS:']):
                    if 'BAR' in line.upper():
                        current_category = 'BAR'
                    elif 'ENTRÉES' in line.upper() or 'ENTREES' in line.upper():
                        current_category = 'ENTRÉES'
                    elif 'PLATS' in line.upper():
                        current_category = 'PLATS'
                    elif 'DESSERTS' in line.upper():
                        current_category = 'DESSERTS'
                    
                    if current_category:
                        categories_found[current_category] = []
                
                # Détecter les items sous chaque catégorie
                elif current_category and line and ':' in line and any(char.isdigit() for char in line):
                    categories_found[current_category].append(line)
            
            # Vérifications de détection
            detection_checks = {
                "Au moins 3 catégories détectées": len(categories_found) >= 3,
                "Catégorie BAR avec items": 'BAR' in categories_found and len(categories_found['BAR']) > 0,
                "Catégorie ENTRÉES avec items": 'ENTRÉES' in categories_found and len(categories_found['ENTRÉES']) > 0,
                "Catégorie PLATS avec items": 'PLATS' in categories_found and len(categories_found['PLATS']) > 0,
                "Catégorie DESSERTS avec items": 'DESSERTS' in categories_found and len(categories_found['DESSERTS']) > 0,
                "Total items > 5": sum(len(items) for items in categories_found.values()) > 5,
                "Items contiennent quantités": any(':' in item and any(char.isdigit() for char in item) for items in categories_found.values() for item in items)
            }
            
            passed_checks = sum(1 for check in detection_checks.values() if check)
            total_checks = len(detection_checks)
            
            if passed_checks >= 5:  # Au moins 5/7 vérifications
                self.log_result("Multi-line Category Detection", True, 
                              f"Catégories multiples détectées ({passed_checks}/{total_checks} vérifications, {len(categories_found)} catégories)",
                              {
                                  "categories_found": {cat: len(items) for cat, items in categories_found.items()},
                                  "total_items": sum(len(items) for items in categories_found.values()),
                                  "sample_items": {cat: items[:2] for cat, items in categories_found.items() if items}
                              })
            else:
                self.log_result("Multi-line Category Detection", False, 
                              f"Détection catégories insuffisante ({passed_checks}/{total_checks} vérifications)",
                              {
                                  "categories_found": categories_found,
                                  "failed_checks": [check for check, result in detection_checks.items() if not result]
                              })
                
        except Exception as e:
            self.log_result("Multi-line Category Detection", False, "Exception", str(e))

    def test_ocr_endpoints_stability_post_changes(self):
        """Test de stabilité des endpoints OCR après les changements"""
        print("\n=== TEST STABILITÉ ENDPOINTS POST-CHANGEMENTS ===")
        
        try:
            endpoints_to_test = [
                ("/ocr/documents", "GET"),
                ("/ocr/document/83bc025a-8ad7-42dd-b494-c476673e735e", "GET")  # Test avec un ID existant
            ]
            
            stability_results = {}
            
            for endpoint, method in endpoints_to_test:
                try:
                    start_time = time.time()
                    if method == "GET":
                        response = requests.get(f"{BASE_URL}{endpoint}")
                    response_time = time.time() - start_time
                    
                    stability_results[endpoint] = {
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code == 200,
                        "fast": response_time < 2.0
                    }
                    
                except Exception as e:
                    stability_results[endpoint] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Évaluer la stabilité globale
            stable_endpoints = sum(1 for result in stability_results.values() if result.get('success', False))
            total_endpoints = len(endpoints_to_test)
            
            if stable_endpoints == total_endpoints:
                self.log_result("OCR Endpoints Stability Post-Changes", True, 
                              f"Tous les endpoints stables ({stable_endpoints}/{total_endpoints})",
                              stability_results)
            else:
                self.log_result("OCR Endpoints Stability Post-Changes", False, 
                              f"Endpoints instables ({stable_endpoints}/{total_endpoints})",
                              stability_results)
                
        except Exception as e:
            self.log_result("OCR Endpoints Stability Post-Changes", False, "Exception", str(e))

    def run_focused_tests(self):
        """Exécuter les tests focalisés sur la complétude OCR PDF"""
        print("🎯 TESTS FOCALISÉS - COMPLÉTUDE EXTRACTION OCR PDF")
        print("=" * 60)
        
        # Test principal: Vérifier complétude extraction PDF existant
        document_id, texte_extrait = self.test_existing_pdf_extraction_completeness()
        
        # Test API GET document complet
        self.test_get_document_full_texte_extrait(document_id)
        
        # Test détection catégories multiples
        self.test_multi_line_category_detection(texte_extrait)
        
        # Test stabilité endpoints
        self.test_ocr_endpoints_stability_post_changes()
        
        # Résumé
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ - TESTS COMPLÉTUDE OCR PDF")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échecs: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        # Résumé spécifique aux améliorations OCR
        key_results = []
        for result in self.test_results:
            if 'Completeness' in result['test'] or 'texte_extrait' in result['test']:
                key_results.append(f"  🔍 {result['test']}: {'✅' if result['success'] else '❌'}")
        
        if key_results:
            print("\n🎯 RÉSULTATS CLÉS - COMPLÉTUDE EXTRACTION:")
            for result in key_results:
                print(result)
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_suite = OCRPDFCompletenessTest()
    results = test_suite.run_focused_tests()