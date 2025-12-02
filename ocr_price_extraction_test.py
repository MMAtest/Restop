#!/usr/bin/env python3
"""
Test spécifique pour l'extraction des prix unitaires et totaux dans les rapports Z OCR
Focus: Validation unit_price et total_price dans donnees_parsees.items_by_category
"""

import requests
import json
import base64
from datetime import datetime
import time

# Configuration
BASE_URL = "https://cuisinepro.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRPriceExtractionTest:
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

    def create_test_z_report_image(self):
        """Crée une image de test avec les formats de lignes spécifiés"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Créer une image blanche
        width, height = 400, 600
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Texte du rapport Z avec les formats demandés
        z_report_text = [
            "RAPPORT Z - SERVICE MIDI",
            "Date: 15/12/2024",
            "",
            "=== ENTRÉES ===",
            "(x3) Linguine aux palourdes 28,00",
            "Burrata di Bufala €18.50 x 2",
            "",
            "=== PLATS ===", 
            "4x Supions persillade 24,00",
            "Bœuf Wellington €56.00 x 1",
            "2x Risotto champignons 22,50",
            "",
            "=== DESSERTS ===",
            "Tiramisu maison €12.00 x 3",
            "(x2) Tarte citron 14,50",
            "",
            "=== BAR ===",
            "Vin rouge Côtes du Rhône €8.50 x 4",
            "3x Pastis Ricard 6,00",
            "",
            "TOTAL CA: 456.50€"
        ]
        
        # Dessiner le texte
        y_position = 20
        line_height = 25
        
        try:
            # Essayer d'utiliser une police par défaut
            font = ImageFont.load_default()
        except:
            font = None
            
        for line in z_report_text:
            draw.text((20, y_position), line, fill='black', font=font)
            y_position += line_height
        
        # Convertir en base64
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{image_base64}"

    def test_ocr_upload_with_price_extraction(self):
        """Test upload OCR et extraction des prix unitaires/totaux"""
        print("\n=== TEST OCR UPLOAD AVEC EXTRACTION PRIX ===")
        
        try:
            # Créer l'image de test
            image_base64 = self.create_test_z_report_image()
            
            # Préparer les données pour l'upload
            files = {
                'file': ('test_z_report.png', base64.b64decode(image_base64.split(',')[1]), 'image/png')
            }
            data = {
                'type_document': 'z_report'
            }
            
            # Upload du document
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.created_document_id = result.get('document_id')
                
                # Vérifier la structure de base
                self.log_result(
                    "OCR Upload Document",
                    True,
                    f"Document uploadé avec succès, ID: {self.created_document_id}"
                )
                
                # Vérifier les données parsées
                donnees_parsees = result.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                
                if not items_by_category:
                    self.log_result(
                        "Items by Category Structure",
                        False,
                        "Aucune catégorie trouvée dans donnees_parsees.items_by_category"
                    )
                    return
                
                self.log_result(
                    "Items by Category Structure",
                    True,
                    f"Catégories trouvées: {list(items_by_category.keys())}"
                )
                
                # Analyser chaque catégorie pour les prix
                price_extraction_results = []
                total_items_with_prices = 0
                total_items = 0
                
                for category, items in items_by_category.items():
                    print(f"\n--- Analyse catégorie: {category} ---")
                    
                    for item in items:
                        total_items += 1
                        item_name = item.get('name', 'Nom inconnu')
                        unit_price = item.get('unit_price')
                        total_price = item.get('total_price')
                        quantity = item.get('quantity_sold', 0)
                        
                        print(f"  Item: {item_name}")
                        print(f"    Quantité: {quantity}")
                        print(f"    Prix unitaire: {unit_price}")
                        print(f"    Prix total: {total_price}")
                        
                        # Vérifier si les prix sont extraits
                        has_unit_price = unit_price is not None
                        has_total_price = total_price is not None
                        
                        if has_unit_price or has_total_price:
                            total_items_with_prices += 1
                            
                        price_extraction_results.append({
                            'category': category,
                            'name': item_name,
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'total_price': total_price,
                            'has_unit_price': has_unit_price,
                            'has_total_price': has_total_price
                        })
                
                # Évaluer les résultats d'extraction des prix
                price_extraction_rate = (total_items_with_prices / total_items * 100) if total_items > 0 else 0
                
                self.log_result(
                    "Prix Extraction Rate",
                    price_extraction_rate > 50,  # Au moins 50% des items doivent avoir des prix
                    f"{total_items_with_prices}/{total_items} items avec prix ({price_extraction_rate:.1f}%)",
                    price_extraction_results
                )
                
                # Tests spécifiques pour les formats demandés
                self.test_specific_price_formats(price_extraction_results)
                
                return result
                
            else:
                self.log_result(
                    "OCR Upload Document",
                    False,
                    f"Erreur upload: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result(
                "OCR Upload Document",
                False,
                f"Exception: {str(e)}"
            )
            return None

    def test_specific_price_formats(self, price_results):
        """Test des formats spécifiques mentionnés dans la demande"""
        print("\n=== TEST FORMATS PRIX SPÉCIFIQUES ===")
        
        # Formats à tester selon la demande
        expected_items = [
            {'name_contains': 'Linguine aux palourdes', 'expected_price': 28.00},
            {'name_contains': 'Burrata di Bufala', 'expected_price': 18.50},
            {'name_contains': 'Supions persillade', 'expected_price': 24.00}
        ]
        
        for expected in expected_items:
            found = False
            for item in price_results:
                if expected['name_contains'].lower() in item['name'].lower():
                    found = True
                    unit_price = item['unit_price']
                    total_price = item['total_price']
                    
                    # Vérifier si au moins un prix est extrait
                    has_price = unit_price is not None or total_price is not None
                    
                    # Vérifier si le prix correspond (avec tolérance)
                    price_match = False
                    if unit_price is not None:
                        price_match = abs(unit_price - expected['expected_price']) < 0.01
                    elif total_price is not None and item['quantity'] > 0:
                        calculated_unit_price = total_price / item['quantity']
                        price_match = abs(calculated_unit_price - expected['expected_price']) < 0.01
                    
                    self.log_result(
                        f"Format Prix - {expected['name_contains']}",
                        has_price and price_match,
                        f"Prix extrait: {unit_price or 'N/A'}, Total: {total_price or 'N/A'}, Attendu: {expected['expected_price']}",
                        item
                    )
                    break
            
            if not found:
                self.log_result(
                    f"Format Prix - {expected['name_contains']}",
                    False,
                    "Item non trouvé dans les résultats d'extraction"
                )

    def test_document_persistence(self):
        """Test de la persistance via GET /api/ocr/document/{id}"""
        print("\n=== TEST PERSISTANCE DOCUMENT ===")
        
        if not self.created_document_id:
            self.log_result(
                "Document Persistence",
                False,
                "Aucun document créé pour tester la persistance"
            )
            return
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{self.created_document_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Vérifier que les données parsées sont persistées
                donnees_parsees = document.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                
                if items_by_category:
                    # Compter les items avec prix dans la version persistée
                    total_items_with_prices = 0
                    total_items = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            total_items += 1
                            if item.get('unit_price') is not None or item.get('total_price') is not None:
                                total_items_with_prices += 1
                    
                    self.log_result(
                        "Document Persistence",
                        total_items_with_prices > 0,
                        f"Document persisté avec {total_items_with_prices}/{total_items} items avec prix",
                        {
                            'document_id': self.created_document_id,
                            'categories': list(items_by_category.keys()),
                            'total_items': total_items,
                            'items_with_prices': total_items_with_prices
                        }
                    )
                else:
                    self.log_result(
                        "Document Persistence",
                        False,
                        "Données parsées non trouvées dans le document persisté"
                    )
            else:
                self.log_result(
                    "Document Persistence",
                    False,
                    f"Erreur récupération document: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Document Persistence",
                False,
                f"Exception: {str(e)}"
            )

    def run_all_tests(self):
        """Exécute tous les tests OCR prix"""
        print("🎯 DÉBUT DES TESTS OCR EXTRACTION PRIX UNITAIRES/TOTAUX")
        print("=" * 60)
        
        # Test principal d'upload et extraction
        upload_result = self.test_ocr_upload_with_price_extraction()
        
        # Test de persistance
        if upload_result:
            time.sleep(1)  # Attendre un peu pour la persistance
            self.test_document_persistence()
        
        # Résumé des résultats
        self.print_summary()

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS OCR PRIX")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n🎯 CONCLUSION:")
        if passed_tests == total_tests:
            print("✅ TOUS LES TESTS OCR PRIX RÉUSSIS - Extraction unit_price/total_price fonctionnelle")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ TESTS OCR PRIX MAJORITAIREMENT RÉUSSIS - Quelques améliorations nécessaires")
        else:
            print("❌ TESTS OCR PRIX ÉCHOUÉS - Extraction prix nécessite corrections")

if __name__ == "__main__":
    test_suite = OCRPriceExtractionTest()
    test_suite.run_all_tests()