#!/usr/bin/env python3
"""
Test complet et final pour validation de l'extraction unit_price et total_price
Focus: Analyse des documents existants et validation de la fonctionnalité
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://receipt-scanner-64.preview.emergentagent.com/api"

class ComprehensiveOCRPriceTest:
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

    def test_existing_documents_price_extraction(self):
        """Test l'extraction de prix sur tous les documents Z-report existants"""
        print("\n=== ANALYSE DOCUMENTS Z-REPORT EXISTANTS ===")
        
        try:
            # Récupérer tous les documents
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code != 200:
                self.log_result(
                    "Récupération Documents",
                    False,
                    f"Erreur récupération: {response.status_code}"
                )
                return
            
            documents = response.json()
            z_reports = [doc for doc in documents if doc.get('type_document') == 'z_report']
            
            self.log_result(
                "Documents Z-Report Trouvés",
                len(z_reports) > 0,
                f"{len(z_reports)} documents Z-report trouvés"
            )
            
            # Analyser chaque document Z-report
            total_documents = 0
            documents_with_prices = 0
            total_items_all_docs = 0
            total_items_with_prices = 0
            
            analysis_details = []
            
            for doc in z_reports[:5]:  # Analyser les 5 premiers
                doc_id = doc.get('id')
                filename = doc.get('nom_fichier', 'Unknown')
                
                print(f"\n--- Analyse Document: {filename} ---")
                
                # Récupérer le document complet
                doc_response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                
                if doc_response.status_code == 200:
                    full_doc = doc_response.json()
                    total_documents += 1
                    
                    # Analyser les données parsées
                    donnees_parsees = full_doc.get('donnees_parsees', {})
                    items_by_category = donnees_parsees.get('items_by_category', {})
                    
                    doc_total_items = 0
                    doc_items_with_prices = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            doc_total_items += 1
                            total_items_all_docs += 1
                            
                            unit_price = item.get('unit_price')
                            total_price = item.get('total_price')
                            
                            if unit_price is not None or total_price is not None:
                                doc_items_with_prices += 1
                                total_items_with_prices += 1
                    
                    if doc_items_with_prices > 0:
                        documents_with_prices += 1
                    
                    doc_price_rate = (doc_items_with_prices / doc_total_items * 100) if doc_total_items > 0 else 0
                    
                    analysis_details.append({
                        'filename': filename,
                        'doc_id': doc_id,
                        'total_items': doc_total_items,
                        'items_with_prices': doc_items_with_prices,
                        'price_rate': doc_price_rate
                    })
                    
                    print(f"  Items: {doc_total_items}, Avec prix: {doc_items_with_prices} ({doc_price_rate:.1f}%)")
            
            # Résultats globaux
            overall_price_rate = (total_items_with_prices / total_items_all_docs * 100) if total_items_all_docs > 0 else 0
            
            self.log_result(
                "Extraction Prix Documents Existants",
                total_items_with_prices > 0,
                f"{total_items_with_prices}/{total_items_all_docs} items avec prix ({overall_price_rate:.1f}%) sur {total_documents} documents",
                analysis_details
            )
            
            return analysis_details
            
        except Exception as e:
            self.log_result(
                "Analyse Documents Existants",
                False,
                f"Exception: {str(e)}"
            )
            return []

    def test_specific_document_detailed_analysis(self):
        """Analyse détaillée d'un document spécifique pour comprendre la structure"""
        print("\n=== ANALYSE DÉTAILLÉE DOCUMENT SPÉCIFIQUE ===")
        
        # Utiliser le document PDF existant qui a le plus d'items
        doc_id = "7b34298a-2458-46d0-af8f-696f79290c65"  # ztableaugustinedigital.pdf
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Analyser le texte extrait
                texte_extrait = document.get('texte_extrait', '')
                
                self.log_result(
                    "Texte Extrait Disponible",
                    len(texte_extrait) > 0,
                    f"Texte extrait: {len(texte_extrait)} caractères"
                )
                
                # Analyser les données parsées
                donnees_parsees = document.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                grand_total = donnees_parsees.get('grand_total_sales')
                
                # Vérifier la structure des items
                structure_analysis = {}
                sample_items = []
                
                for category, items in items_by_category.items():
                    category_info = {
                        'count': len(items),
                        'items_with_unit_price': 0,
                        'items_with_total_price': 0,
                        'sample_items': []
                    }
                    
                    for i, item in enumerate(items):
                        if item.get('unit_price') is not None:
                            category_info['items_with_unit_price'] += 1
                        if item.get('total_price') is not None:
                            category_info['items_with_total_price'] += 1
                        
                        # Garder quelques exemples
                        if i < 3:
                            category_info['sample_items'].append({
                                'name': item.get('name'),
                                'quantity_sold': item.get('quantity_sold'),
                                'unit_price': item.get('unit_price'),
                                'total_price': item.get('total_price')
                            })
                    
                    structure_analysis[category] = category_info
                
                self.log_result(
                    "Structure Données Parsées",
                    len(items_by_category) > 0,
                    f"Catégories: {list(items_by_category.keys())}, Grand Total: {grand_total}",
                    structure_analysis
                )
                
                # Rechercher des patterns de prix dans le texte brut
                self.analyze_price_patterns_in_text(texte_extrait)
                
                return structure_analysis
                
            else:
                self.log_result(
                    "Récupération Document Spécifique",
                    False,
                    f"Erreur: {response.status_code}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Analyse Document Spécifique",
                False,
                f"Exception: {str(e)}"
            )
            return None

    def analyze_price_patterns_in_text(self, text):
        """Analyse les patterns de prix dans le texte brut"""
        print("\n--- Analyse Patterns Prix dans Texte ---")
        
        import re
        
        # Patterns de prix à rechercher
        price_patterns = [
            r'€\s*\d+[,.]?\d*',  # €12.50, €12,50
            r'\d+[,.]?\d*\s*€',  # 12.50€, 12,50€
            r'\d+[,.]?\d*\s*x\s*\d+',  # 12.50 x 2
            r'\(x\d+\)',  # (x3)
            r'\d+x\s',  # 4x
        ]
        
        found_patterns = {}
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_patterns[pattern] = matches[:5]  # Garder les 5 premiers
        
        self.log_result(
            "Patterns Prix dans Texte",
            len(found_patterns) > 0,
            f"{len(found_patterns)} types de patterns trouvés",
            found_patterns
        )

    def test_api_endpoints_availability(self):
        """Test la disponibilité des endpoints OCR"""
        print("\n=== TEST DISPONIBILITÉ ENDPOINTS OCR ===")
        
        endpoints_to_test = [
            ("/ocr/documents", "GET"),
            ("/ocr/upload-document", "POST")  # Juste vérifier que l'endpoint existe
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}")
                    success = response.status_code in [200, 400, 422]  # 400/422 sont OK pour POST sans données
                else:
                    # Pour POST, juste vérifier que l'endpoint existe (pas 404)
                    response = requests.post(f"{BASE_URL}{endpoint}")
                    success = response.status_code != 404
                
                self.log_result(
                    f"Endpoint {method} {endpoint}",
                    success,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_result(
                    f"Endpoint {method} {endpoint}",
                    False,
                    f"Exception: {str(e)}"
                )

    def run_comprehensive_test(self):
        """Exécute le test complet"""
        print("🎯 TEST COMPLET - VALIDATION EXTRACTION UNIT_PRICE/TOTAL_PRICE")
        print("Focus: Validation des champs unit_price et total_price dans donnees_parsees.items_by_category")
        print("=" * 80)
        
        # Test 1: Disponibilité des endpoints
        self.test_api_endpoints_availability()
        
        # Test 2: Analyse des documents existants
        existing_docs_analysis = self.test_existing_documents_price_extraction()
        
        # Test 3: Analyse détaillée d'un document
        detailed_analysis = self.test_specific_document_detailed_analysis()
        
        # Résumé final
        self.print_comprehensive_summary()

    def print_comprehensive_summary(self):
        """Affiche le résumé complet pour test_result.md"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ COMPLET - VALIDATION UNIT_PRICE/TOTAL_PRICE OCR")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        # Analyse spécifique pour les prix
        price_extraction_working = False
        for result in self.test_results:
            if "Extraction Prix" in result['test'] and result['success']:
                price_extraction_working = True
                break
        
        # Déterminer le statut final
        if price_extraction_working and passed_tests >= total_tests * 0.7:
            final_status = "working: true"
            status_emoji = "✅"
            conclusion = "L'extraction unit_price et total_price fonctionne correctement"
        elif passed_tests >= total_tests * 0.5:
            final_status = "working: false"
            status_emoji = "⚠️"
            conclusion = "L'extraction unit_price et total_price fonctionne partiellement - améliorations nécessaires"
        else:
            final_status = "working: false"
            status_emoji = "❌"
            conclusion = "L'extraction unit_price et total_price ne fonctionne pas correctement"
        
        print(f"\n{status_emoji} STATUT FINAL: {final_status}")
        print(f"📝 CONCLUSION: {conclusion}")
        
        # Détails pour test_result.md
        print(f"\n📋 MISE À JOUR POUR TEST_RESULT.MD:")
        print(f"Task: API OCR Module Complet")
        print(f"Status: {final_status}")
        print(f"Comment: {conclusion}")
        
        if failed_tests > 0:
            print(f"\n❌ PROBLÈMES IDENTIFIÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if not price_extraction_working:
            print("  - Vérifier les patterns regex dans parse_z_report_enhanced()")
            print("  - Améliorer l'extraction OCR pour les formats (x3) Name 28,00")
            print("  - Tester avec des documents PDF de meilleure qualité")
        else:
            print("  - Fonctionnalité validée pour les formats de base")
            print("  - Continuer les tests avec différents formats de documents")

if __name__ == "__main__":
    test_suite = ComprehensiveOCRPriceTest()
    test_suite.run_comprehensive_test()