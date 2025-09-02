#!/usr/bin/env python3
"""
Test de validation spécifique pour l'extraction des prix unitaires et totaux dans les rapports Z OCR
Focus: Validation unit_price et total_price dans donnees_parsees.items_by_category selon la demande
"""

import requests
import json
import base64
from datetime import datetime
import time
import io

# Configuration
BASE_URL = "https://kitchen-manager-3.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRPriceValidationTest:
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

    def create_text_based_z_report_pdf(self):
        """Crée un PDF simple avec du texte pour tester l'extraction de prix"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Contenu du rapport Z avec les formats spécifiés
            y_position = 750
            line_height = 20
            
            lines = [
                "RAPPORT Z - LA TABLE D'AUGUSTINE",
                "Date: 15/12/2024 - Service Midi",
                "",
                "=== ENTRÉES ===",
                "(x3) Linguine aux palourdes 28,00",
                "Burrata di Bufala €18.50 x 2",
                "Supions en persillade €24.00 x 4",
                "",
                "=== PLATS ===", 
                "4x Supions persillade 24,00",
                "Bœuf Wellington €56.00 x 1",
                "2x Risotto champignons 22,50",
                "Escalope milanaise €32.00 x 3",
                "",
                "=== DESSERTS ===",
                "Tiramisu maison €12.00 x 3",
                "(x2) Tarte citron 14,50",
                "Glace vanille €8.50 x 5",
                "",
                "=== BAR ===",
                "Vin rouge Côtes du Rhône €8.50 x 4",
                "3x Pastis Ricard 6,00",
                "Cocktail Spritz €12.00 x 2",
                "",
                "TOTAL CA: 687.50€"
            ]
            
            for line in lines:
                if line.strip():  # Skip empty lines for PDF
                    p.drawString(50, y_position, line)
                y_position -= line_height
            
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback: create a simple text file as PDF content
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
Escalope milanaise €32.00 x 3

=== DESSERTS ===
Tiramisu maison €12.00 x 3
(x2) Tarte citron 14,50
Glace vanille €8.50 x 5

=== BAR ===
Vin rouge Côtes du Rhône €8.50 x 4
3x Pastis Ricard 6,00
Cocktail Spritz €12.00 x 2

TOTAL CA: 687.50€"""
            return content.encode('utf-8')

    def test_existing_document_price_extraction(self):
        """Test l'extraction de prix sur un document existant"""
        print("\n=== TEST DOCUMENT EXISTANT - EXTRACTION PRIX ===")
        
        # Utiliser le document PDF existant
        existing_doc_id = "7b34298a-2458-46d0-af8f-696f79290c65"  # ztableaugustinedigital.pdf
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{existing_doc_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Analyser les données parsées
                donnees_parsees = document.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                
                if not items_by_category:
                    self.log_result(
                        "Document Existant - Structure",
                        False,
                        "Aucune catégorie trouvée dans le document existant"
                    )
                    return
                
                # Analyser l'extraction de prix
                total_items = 0
                items_with_unit_price = 0
                items_with_total_price = 0
                items_with_any_price = 0
                
                price_analysis = {}
                
                for category, items in items_by_category.items():
                    category_analysis = {
                        'total_items': len(items),
                        'items_with_unit_price': 0,
                        'items_with_total_price': 0,
                        'items_with_any_price': 0,
                        'sample_items': []
                    }
                    
                    for item in items:
                        total_items += 1
                        unit_price = item.get('unit_price')
                        total_price = item.get('total_price')
                        
                        if unit_price is not None:
                            items_with_unit_price += 1
                            category_analysis['items_with_unit_price'] += 1
                        
                        if total_price is not None:
                            items_with_total_price += 1
                            category_analysis['items_with_total_price'] += 1
                        
                        if unit_price is not None or total_price is not None:
                            items_with_any_price += 1
                            category_analysis['items_with_any_price'] += 1
                        
                        # Garder quelques exemples
                        if len(category_analysis['sample_items']) < 3:
                            category_analysis['sample_items'].append({
                                'name': item.get('name', 'N/A'),
                                'quantity': item.get('quantity_sold', 0),
                                'unit_price': unit_price,
                                'total_price': total_price
                            })
                    
                    price_analysis[category] = category_analysis
                
                # Évaluer les résultats
                price_extraction_rate = (items_with_any_price / total_items * 100) if total_items > 0 else 0
                
                self.log_result(
                    "Document Existant - Analyse Prix",
                    items_with_any_price > 0,  # Au moins quelques items doivent avoir des prix
                    f"Prix extraits: {items_with_any_price}/{total_items} items ({price_extraction_rate:.1f}%)",
                    {
                        'total_items': total_items,
                        'items_with_unit_price': items_with_unit_price,
                        'items_with_total_price': items_with_total_price,
                        'items_with_any_price': items_with_any_price,
                        'by_category': price_analysis
                    }
                )
                
                # Test spécifique pour les formats demandés
                self.test_specific_format_detection(items_by_category)
                
                return document
                
            else:
                self.log_result(
                    "Document Existant - Récupération",
                    False,
                    f"Erreur récupération: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Document Existant - Exception",
                False,
                f"Exception: {str(e)}"
            )
            return None

    def test_specific_format_detection(self, items_by_category):
        """Test la détection des formats spécifiques mentionnés dans la demande"""
        print("\n=== TEST FORMATS SPÉCIFIQUES ===")
        
        # Formats à rechercher selon la demande
        target_patterns = [
            {'pattern': 'linguine', 'expected_in': ['Entrées', 'Plats']},
            {'pattern': 'burrata', 'expected_in': ['Entrées']},
            {'pattern': 'supions', 'expected_in': ['Entrées', 'Plats']},
            {'pattern': 'palourdes', 'expected_in': ['Entrées', 'Plats']}
        ]
        
        found_patterns = []
        
        for pattern_info in target_patterns:
            pattern = pattern_info['pattern']
            found = False
            
            for category, items in items_by_category.items():
                for item in items:
                    item_name = item.get('name', '').lower()
                    if pattern in item_name:
                        found = True
                        found_patterns.append({
                            'pattern': pattern,
                            'found_in_category': category,
                            'item_name': item.get('name'),
                            'quantity': item.get('quantity_sold', 0),
                            'unit_price': item.get('unit_price'),
                            'total_price': item.get('total_price'),
                            'has_price': item.get('unit_price') is not None or item.get('total_price') is not None
                        })
                        break
                if found:
                    break
            
            self.log_result(
                f"Format Détection - {pattern}",
                found,
                f"Pattern '{pattern}' {'trouvé' if found else 'non trouvé'} dans les items"
            )
        
        # Analyser les prix pour les patterns trouvés
        patterns_with_prices = [p for p in found_patterns if p['has_price']]
        
        self.log_result(
            "Formats avec Prix",
            len(patterns_with_prices) > 0,
            f"{len(patterns_with_prices)}/{len(found_patterns)} patterns trouvés ont des prix extraits",
            found_patterns
        )

    def test_upload_new_document_with_prices(self):
        """Test upload d'un nouveau document avec formats de prix spécifiques"""
        print("\n=== TEST UPLOAD NOUVEAU DOCUMENT AVEC PRIX ===")
        
        try:
            # Créer un document PDF avec les formats demandés
            pdf_content = self.create_text_based_z_report_pdf()
            
            # Upload du document
            files = {
                'file': ('test_z_report_prices.pdf', pdf_content, 'application/pdf')
            }
            data = {
                'type_document': 'z_report'
            }
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.created_document_id = result.get('document_id')
                
                self.log_result(
                    "Upload Nouveau Document",
                    True,
                    f"Document uploadé avec succès, ID: {self.created_document_id}"
                )
                
                # Analyser les prix extraits
                donnees_parsees = result.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                
                if items_by_category:
                    total_items = sum(len(items) for items in items_by_category.values())
                    items_with_prices = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            if item.get('unit_price') is not None or item.get('total_price') is not None:
                                items_with_prices += 1
                    
                    price_rate = (items_with_prices / total_items * 100) if total_items > 0 else 0
                    
                    self.log_result(
                        "Nouveau Document - Prix Extraits",
                        items_with_prices > 0,
                        f"{items_with_prices}/{total_items} items avec prix ({price_rate:.1f}%)",
                        {
                            'document_id': self.created_document_id,
                            'categories': list(items_by_category.keys()),
                            'total_items': total_items,
                            'items_with_prices': items_with_prices
                        }
                    )
                else:
                    self.log_result(
                        "Nouveau Document - Structure",
                        False,
                        "Aucune catégorie trouvée dans le nouveau document"
                    )
                
                return result
                
            else:
                self.log_result(
                    "Upload Nouveau Document",
                    False,
                    f"Erreur upload: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Upload Nouveau Document",
                False,
                f"Exception: {str(e)}"
            )
            return None

    def test_document_persistence_with_prices(self):
        """Test la persistance des prix via GET /api/ocr/document/{id}"""
        print("\n=== TEST PERSISTANCE PRIX ===")
        
        if not self.created_document_id:
            self.log_result(
                "Persistance Prix",
                False,
                "Aucun document créé pour tester la persistance"
            )
            return
        
        try:
            # Attendre un peu pour la persistance
            time.sleep(2)
            
            response = requests.get(f"{BASE_URL}/ocr/document/{self.created_document_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Vérifier la persistance des prix
                donnees_parsees = document.get('donnees_parsees', {})
                items_by_category = donnees_parsees.get('items_by_category', {})
                
                if items_by_category:
                    total_items = sum(len(items) for items in items_by_category.values())
                    items_with_prices = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            if item.get('unit_price') is not None or item.get('total_price') is not None:
                                items_with_prices += 1
                    
                    self.log_result(
                        "Persistance Prix",
                        items_with_prices > 0,
                        f"Prix persistés: {items_with_prices}/{total_items} items",
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
                    "Persistance Prix",
                    False,
                    f"Erreur récupération: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Persistance Prix",
                False,
                f"Exception: {str(e)}"
            )

    def run_all_tests(self):
        """Exécute tous les tests de validation OCR prix"""
        print("🎯 DÉBUT VALIDATION OCR EXTRACTION PRIX UNITAIRES/TOTAUX")
        print("=" * 70)
        
        # Test 1: Analyser un document existant
        existing_doc = self.test_existing_document_price_extraction()
        
        # Test 2: Upload nouveau document avec formats spécifiques
        new_doc = self.test_upload_new_document_with_prices()
        
        # Test 3: Vérifier la persistance
        if new_doc:
            self.test_document_persistence_with_prices()
        
        # Résumé des résultats
        self.print_summary()

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ VALIDATION OCR PRIX UNITAIRES/TOTAUX")
        print("=" * 70)
        
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
        
        print(f"\n🎯 CONCLUSION VALIDATION:")
        if passed_tests >= total_tests * 0.8:
            print("✅ VALIDATION OCR PRIX MAJORITAIREMENT RÉUSSIE")
            print("   Les formats unit_price et total_price sont détectés dans les items")
        elif passed_tests >= total_tests * 0.5:
            print("⚠️ VALIDATION OCR PRIX PARTIELLE")
            print("   Certains formats de prix sont détectés mais des améliorations sont nécessaires")
        else:
            print("❌ VALIDATION OCR PRIX ÉCHOUÉE")
            print("   L'extraction unit_price/total_price nécessite des corrections importantes")

if __name__ == "__main__":
    test_suite = OCRPriceValidationTest()
    test_suite.run_all_tests()