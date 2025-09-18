#!/usr/bin/env python3
"""
Test final pour validation complète de l'extraction unit_price et total_price
Focus: Workflow complet POST /api/ocr/upload-document et GET /api/ocr/document/{id}
"""

import requests
import json
import base64
from datetime import datetime
import time
import io

# Configuration
BASE_URL = "https://smart-zreports.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class FinalOCRPriceTest:
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

    def create_text_pdf_with_exact_formats(self):
        """Crée un PDF avec exactement les formats demandés dans la review"""
        content = """RAPPORT Z - LA TABLE D'AUGUSTINE
Date: 15/12/2024 - Service Midi

=== ENTRÉES ===
(x3) Linguine aux palourdes 28,00
Burrata di Bufala €18.50 x 2
Supions en persillade €24.00 x 4

=== PLATS ===
4x Supions persillade 24,00
Bœuf Wellington €56.00 x 1
2x Risotto champignons 22,50

=== DESSERTS ===
Tiramisu maison €12.00 x 3
(x2) Tarte citron 14,50

=== BAR ===
Vin rouge Côtes du Rhône €8.50 x 4
3x Pastis Ricard 6,00

TOTAL CA: 687.50€"""
        
        return content.encode('utf-8')

    def test_upload_and_validate_prices(self):
        """Test complet: upload document et validation extraction prix"""
        print("\n=== TEST UPLOAD ET VALIDATION PRIX ===")
        
        try:
            # Créer le document avec les formats exacts
            pdf_content = self.create_text_pdf_with_exact_formats()
            
            # Upload comme fichier texte (simuler PDF)
            files = {
                'file': ('z_report_exact_formats.txt', pdf_content, 'text/plain')
            }
            data = {
                'type_document': 'z_report'
            }
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.created_document_id = result.get('document_id')
                
                self.log_result(
                    "Upload Document Formats Exacts",
                    True,
                    f"Document uploadé avec succès, ID: {self.created_document_id}"
                )
                
                # Analyser immédiatement la réponse
                self.analyze_upload_response(result)
                
                return result
                
            else:
                self.log_result(
                    "Upload Document Formats Exacts",
                    False,
                    f"Erreur upload: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Upload Document Formats Exacts",
                False,
                f"Exception: {str(e)}"
            )
            return None

    def analyze_upload_response(self, upload_result):
        """Analyse la réponse d'upload pour les prix"""
        print("\n--- Analyse Réponse Upload ---")
        
        donnees_parsees = upload_result.get('donnees_parsees', {})
        items_by_category = donnees_parsees.get('items_by_category', {})
        
        if not items_by_category:
            self.log_result(
                "Structure Items by Category",
                False,
                "Aucune catégorie trouvée dans donnees_parsees"
            )
            return
        
        # Analyser chaque catégorie
        total_items = 0
        items_with_unit_price = 0
        items_with_total_price = 0
        items_with_any_price = 0
        
        expected_items = [
            {'name_contains': 'linguine aux palourdes', 'expected_unit_price': 28.00, 'expected_qty': 3},
            {'name_contains': 'burrata di bufala', 'expected_unit_price': 18.50, 'expected_qty': 2},
            {'name_contains': 'supions persillade', 'expected_unit_price': 24.00, 'expected_qty': 4}
        ]
        
        found_expected_items = []
        
        for category, items in items_by_category.items():
            print(f"\nCatégorie: {category} ({len(items)} items)")
            
            for item in items:
                total_items += 1
                name = item.get('name', '')
                qty = item.get('quantity_sold', 0)
                unit_price = item.get('unit_price')
                total_price = item.get('total_price')
                
                print(f"  - {name}: qty={qty}, unit_price={unit_price}, total_price={total_price}")
                
                if unit_price is not None:
                    items_with_unit_price += 1
                if total_price is not None:
                    items_with_total_price += 1
                if unit_price is not None or total_price is not None:
                    items_with_any_price += 1
                
                # Vérifier si c'est un item attendu
                for expected in expected_items:
                    if expected['name_contains'].lower() in name.lower():
                        found_expected_items.append({
                            'expected': expected,
                            'found': item,
                            'price_match': unit_price == expected['expected_unit_price'] if unit_price else False,
                            'qty_match': qty == expected['expected_qty']
                        })
        
        # Résultats globaux
        price_extraction_rate = (items_with_any_price / total_items * 100) if total_items > 0 else 0
        
        self.log_result(
            "Extraction Prix Globale",
            items_with_any_price > 0,
            f"{items_with_any_price}/{total_items} items avec prix ({price_extraction_rate:.1f}%)",
            {
                'total_items': total_items,
                'items_with_unit_price': items_with_unit_price,
                'items_with_total_price': items_with_total_price,
                'items_with_any_price': items_with_any_price
            }
        )
        
        # Validation des items spécifiques
        self.validate_specific_items(found_expected_items, expected_items)

    def validate_specific_items(self, found_items, expected_items):
        """Valide les items spécifiques mentionnés dans la demande"""
        print("\n--- Validation Items Spécifiques ---")
        
        for expected in expected_items:
            name_pattern = expected['name_contains']
            found_match = None
            
            for found in found_items:
                if found['expected'] == expected:
                    found_match = found
                    break
            
            if found_match:
                item = found_match['found']
                price_correct = found_match['price_match']
                qty_correct = found_match['qty_match']
                
                self.log_result(
                    f"Item Spécifique - {name_pattern}",
                    price_correct and qty_correct,
                    f"Trouvé: {item.get('name')}, Prix: {item.get('unit_price')} (attendu: {expected['expected_unit_price']}), Qty: {item.get('quantity_sold')} (attendu: {expected['expected_qty']})",
                    found_match
                )
            else:
                self.log_result(
                    f"Item Spécifique - {name_pattern}",
                    False,
                    f"Item non trouvé dans les résultats"
                )

    def test_document_persistence(self):
        """Test la persistance via GET /api/ocr/document/{id}"""
        print("\n=== TEST PERSISTANCE DOCUMENT ===")
        
        if not self.created_document_id:
            self.log_result(
                "Persistance Document",
                False,
                "Aucun document créé pour tester la persistance"
            )
            return
        
        try:
            # Attendre un peu pour la persistance
            time.sleep(1)
            
            response = requests.get(f"{BASE_URL}/ocr/document/{self.created_document_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Vérifier que les prix sont persistés
                donnees_parsees = document.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                
                if items_by_category:
                    total_items = sum(len(items) for items in items_by_category.values())
                    items_with_prices = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            if item.get('unit_price') is not None or item.get('total_price') is not None:
                                items_with_prices += 1
                    
                    persistence_rate = (items_with_prices / total_items * 100) if total_items > 0 else 0
                    
                    self.log_result(
                        "Persistance Prix",
                        items_with_prices > 0,
                        f"Prix persistés: {items_with_prices}/{total_items} items ({persistence_rate:.1f}%)",
                        {
                            'document_id': self.created_document_id,
                            'total_items': total_items,
                            'items_with_prices': items_with_prices
                        }
                    )
                else:
                    self.log_result(
                        "Persistance Prix",
                        False,
                        "Aucune donnée persistée trouvée"
                    )
            else:
                self.log_result(
                    "Persistance Document",
                    False,
                    f"Erreur récupération: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Persistance Document",
                False,
                f"Exception: {str(e)}"
            )

    def run_complete_test(self):
        """Exécute le test complet selon la demande"""
        print("🎯 TEST FINAL - VALIDATION UNIT_PRICE ET TOTAL_PRICE")
        print("Formats testés: (x3) Linguine aux palourdes 28,00")
        print("                Burrata di Bufala €18.50 x 2")
        print("                4x Supions persillade 24,00")
        print("=" * 70)
        
        # Test principal: upload et validation
        upload_result = self.test_upload_and_validate_prices()
        
        # Test persistance
        if upload_result:
            self.test_document_persistence()
        
        # Résumé final
        self.print_final_summary()

    def print_final_summary(self):
        """Affiche le résumé final selon la demande"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ FINAL - VALIDATION UNIT_PRICE/TOTAL_PRICE")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        # Statut pour test_result.md
        if passed_tests >= total_tests * 0.8:
            status = "✅ VALIDATION RÉUSSIE"
            note = "L'extraction unit_price et total_price fonctionne correctement pour les formats demandés"
        elif passed_tests >= total_tests * 0.5:
            status = "⚠️ VALIDATION PARTIELLE"
            note = "L'extraction unit_price et total_price fonctionne partiellement, améliorations nécessaires"
        else:
            status = "❌ VALIDATION ÉCHOUÉE"
            note = "L'extraction unit_price et total_price ne fonctionne pas correctement"
        
        print(f"\n🎯 STATUT FINAL: {status}")
        print(f"📝 NOTE: {note}")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n📋 POUR TEST_RESULT.MD:")
        print(f"Status: {'working: true' if passed_tests >= total_tests * 0.8 else 'working: false'}")
        print(f"Comment: {note}")

if __name__ == "__main__":
    test_suite = FinalOCRPriceTest()
    test_suite.run_complete_test()