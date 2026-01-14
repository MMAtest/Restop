#!/usr/bin/env python3
"""
Test spécifique pour la validation de l'extraction unit_price/total_price dans le module OCR
Selon la demande de re-test: Ensure unit_price/total_price are now populated via parsing or enrichment
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRUnitPriceTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_document_ids = []
        
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

    def create_z_report_image_with_prices(self):
        """Crée une image de Z-report avec des lignes contenant quantités et prix"""
        # Créer une image avec du texte simulant un Z-report
        img = Image.new('RGB', (800, 1000), color='white')
        draw = ImageDraw.Draw(img)
        
        # Essayer d'utiliser une police par défaut
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Contenu du Z-report avec formats de prix variés
        y_position = 50
        lines = [
            "RAPPORT Z - LA TABLE D'AUGUSTINE",
            "Date: 15/01/2025 - Service: Soir",
            "",
            "VENTES PAR CATÉGORIE:",
            "",
            "BAR:",
            "(x2) Vin rouge Côtes du Rhône 15,00",
            "Pastis Ricard €8.50 x 3", 
            "",
            "ENTRÉES:",
            "(x3) Linguine aux palourdes 28,00",
            "Burrata di Bufala €18.50 x 2",
            "4x Supions persillade 24,00",
            "",
            "PLATS:",
            "Bœuf Wellington €56.00 x 1",
            "(x2) Souris d'agneau confite 36,00",
            "",
            "DESSERTS:",
            "Tiramisu maison 12,50 x 3",
            "(x1) Tarte aux figues €14.00",
            "",
            "TOTAL CA: 687.50€",
            "Nombre de couverts: 21"
        ]
        
        for line in lines:
            if line.strip():
                if "RAPPORT Z" in line or "TOTAL CA" in line:
                    draw.text((50, y_position), line, fill='black', font=font)
                else:
                    draw.text((50, y_position), line, fill='black', font=font_small)
            y_position += 35
        
        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"

    def test_upload_z_report_image_with_prices(self):
        """Test 1: Upload d'une image Z-report avec lignes contenant quantités et prix"""
        print("\n=== TEST 1: UPLOAD Z-REPORT IMAGE AVEC PRIX ===")
        
        # Créer l'image de test
        image_base64 = self.create_z_report_image_with_prices()
        
        try:
            # Simuler l'upload d'un fichier image
            # Décoder le base64 pour créer un fichier
            image_data = base64.b64decode(image_base64.split(',')[1])
            
            files = {
                'file': ('z_report_with_prices.png', image_data, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                self.created_document_ids.append(document_id)
                
                self.log_result("Upload Z-report image", True, 
                              f"Document uploadé avec ID: {document_id}")
                
                # Vérifier que le texte a été extrait
                extracted_text = result.get("texte_extrait", "")
                if len(extracted_text) > 50:
                    self.log_result("Text extraction from image", True, 
                                  f"Texte extrait: {len(extracted_text)} caractères")
                    
                    # Vérifier la présence de patterns de prix dans le texte
                    price_patterns_found = []
                    expected_patterns = [
                        "(x3) Linguine", "28,00", "Burrata", "€18.50 x 2", 
                        "4x Supions", "24,00", "€56.00 x 1"
                    ]
                    
                    for pattern in expected_patterns:
                        if pattern.lower() in extracted_text.lower():
                            price_patterns_found.append(pattern)
                    
                    if len(price_patterns_found) >= 4:
                        self.log_result("Price patterns in extracted text", True, 
                                      f"Patterns trouvés: {price_patterns_found}")
                    else:
                        self.log_result("Price patterns in extracted text", False, 
                                      f"Seulement {len(price_patterns_found)} patterns trouvés: {price_patterns_found}")
                else:
                    self.log_result("Text extraction from image", False, 
                                  f"Texte insuffisant: {len(extracted_text)} caractères")
                
                # Vérifier les données parsées
                donnees_parsees = result.get("donnees_parsees", {})
                if donnees_parsees:
                    items_by_category = donnees_parsees.get("items_by_category", {})
                    
                    # Compter les items avec unit_price et total_price
                    items_with_unit_price = 0
                    items_with_total_price = 0
                    total_items = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            total_items += 1
                            if item.get("unit_price") is not None:
                                items_with_unit_price += 1
                            if item.get("total_price") is not None:
                                items_with_total_price += 1
                    
                    self.log_result("Items parsed", True, 
                                  f"Total items: {total_items}, avec unit_price: {items_with_unit_price}, avec total_price: {items_with_total_price}")
                    
                    # VALIDATION CRITIQUE: Au moins quelques items doivent avoir unit_price et total_price
                    if items_with_unit_price > 0 and items_with_total_price > 0:
                        self.log_result("CRITICAL: Unit/Total prices populated", True, 
                                      f"✅ {items_with_unit_price} items avec unit_price, {items_with_total_price} items avec total_price")
                    else:
                        self.log_result("CRITICAL: Unit/Total prices populated", False, 
                                      f"❌ PROBLÈME: {items_with_unit_price} items avec unit_price, {items_with_total_price} items avec total_price")
                        
                        # Afficher les détails pour debug
                        print("   DEBUG - Items détaillés:")
                        for category, items in items_by_category.items():
                            print(f"     {category}: {len(items)} items")
                            for item in items[:3]:  # Afficher les 3 premiers
                                print(f"       - {item.get('name', 'N/A')}: unit_price={item.get('unit_price')}, total_price={item.get('total_price')}")
                
                return document_id
                
            else:
                self.log_result("Upload Z-report image", False, 
                              f"Erreur {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Upload Z-report image", False, f"Exception: {str(e)}")
            return None

    def test_existing_z_report_enrichment(self):
        """Test 2: GET documents existants et vérification enrichment"""
        print("\n=== TEST 2: DOCUMENTS EXISTANTS ET ENRICHMENT ===")
        
        try:
            # GET /api/ocr/documents
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code == 200:
                documents = response.json()
                self.log_result("GET /ocr/documents", True, 
                              f"{len(documents)} documents trouvés")
                
                # Chercher un z_report existant
                z_reports = [doc for doc in documents if doc.get("type_document") == "z_report"]
                
                if z_reports:
                    # Prendre le premier z_report
                    z_report = z_reports[0]
                    document_id = z_report["id"]
                    
                    self.log_result("Z-report found", True, 
                                  f"Z-report trouvé: {document_id}")
                    
                    # GET /api/ocr/document/{id} pour vérifier l'enrichment
                    doc_response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
                    
                    if doc_response.status_code == 200:
                        document_detail = doc_response.json()
                        
                        self.log_result("GET /ocr/document/{id}", True, 
                                      "Document détaillé récupéré")
                        
                        # Vérifier que l'enrichment a été exécuté
                        donnees_parsees = document_detail.get("donnees_parsees", {})
                        
                        if donnees_parsees:
                            items_by_category = donnees_parsees.get("items_by_category", {})
                            
                            # Compter les items avec prix
                            items_with_prices = 0
                            total_items = 0
                            
                            for category, items in items_by_category.items():
                                for item in items:
                                    total_items += 1
                                    if item.get("unit_price") is not None or item.get("total_price") is not None:
                                        items_with_prices += 1
                            
                            if total_items > 0:
                                percentage = (items_with_prices / total_items) * 100
                                
                                self.log_result("Enrichment verification", True, 
                                              f"Items avec prix: {items_with_prices}/{total_items} ({percentage:.1f}%)")
                                
                                # VALIDATION: Au moins quelques items doivent avoir des prix
                                if items_with_prices > 0:
                                    self.log_result("CRITICAL: Enrichment working", True, 
                                                  f"✅ Enrichment fonctionne: {items_with_prices} items enrichis")
                                else:
                                    self.log_result("CRITICAL: Enrichment working", False, 
                                                  "❌ Aucun item enrichi avec prix")
                            else:
                                self.log_result("Items in document", False, "Aucun item trouvé dans le document")
                        else:
                            self.log_result("Parsed data", False, "Aucune donnée parsée trouvée")
                    else:
                        self.log_result("GET /ocr/document/{id}", False, 
                                      f"Erreur {doc_response.status_code}")
                else:
                    self.log_result("Z-report found", False, "Aucun z_report existant trouvé")
            else:
                self.log_result("GET /ocr/documents", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Existing documents test", False, f"Exception: {str(e)}")

    def test_facture_fournisseur_no_regression(self):
        """Test 3: Vérifier qu'il n'y a pas de régression sur facture_fournisseur"""
        print("\n=== TEST 3: FACTURE FOURNISSEUR - NO REGRESSION ===")
        
        try:
            # Créer une image simple de facture fournisseur
            img = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Contenu facture simple
            y_pos = 50
            facture_lines = [
                "FACTURE FOURNISSEUR",
                "Fournisseur: Maison Artigiana",
                "Date: 15/01/2025",
                "N° Facture: FAC-2025-001",
                "",
                "PRODUITS:",
                "Burrata des Pouilles - 5 kg - 42.50€",
                "Mozzarella di Bufala - 3 kg - 24.00€",
                "Huile d'olive extra - 2 L - 18.00€",
                "",
                "TOTAL HT: 84.50€",
                "TVA 20%: 16.90€", 
                "TOTAL TTC: 101.40€"
            ]
            
            for line in facture_lines:
                if line.strip():
                    draw.text((50, y_pos), line, fill='black', font=font)
                y_pos += 30
            
            # Convertir en base64 et upload
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            image_data = buffer.getvalue()
            
            files = {
                'file': ('facture_test.png', image_data, 'image/png')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                self.log_result("Upload facture fournisseur", True, 
                              f"Facture uploadée: {document_id}")
                
                # Vérifier que le type est correct
                if result.get("type_document") == "facture_fournisseur":
                    self.log_result("Document type facture", True, "Type document correct")
                else:
                    self.log_result("Document type facture", False, 
                                  f"Type incorrect: {result.get('type_document')}")
                
                # Vérifier l'extraction de texte
                extracted_text = result.get("texte_extrait", "")
                if len(extracted_text) > 20:
                    self.log_result("Facture text extraction", True, 
                                  f"Texte extrait: {len(extracted_text)} caractères")
                    
                    # Vérifier la présence d'éléments clés
                    key_elements = ["FACTURE", "Fournisseur", "TOTAL"]
                    found_elements = [elem for elem in key_elements if elem.lower() in extracted_text.lower()]
                    
                    if len(found_elements) >= 2:
                        self.log_result("Facture key elements", True, 
                                      f"Éléments trouvés: {found_elements}")
                    else:
                        self.log_result("Facture key elements", False, 
                                      f"Éléments manquants: {found_elements}")
                else:
                    self.log_result("Facture text extraction", False, 
                                  "Texte insuffisant extrait")
                
                # Vérifier les données parsées (structure facture)
                donnees_parsees = result.get("donnees_parsees", {})
                if donnees_parsees:
                    # Pour une facture, on s'attend à une structure différente du z_report
                    if "fournisseur" in donnees_parsees or "produits" in donnees_parsees:
                        self.log_result("Facture parsing structure", True, 
                                      "Structure facture détectée")
                    else:
                        self.log_result("Facture parsing structure", False, 
                                      "Structure facture non détectée")
                
                self.created_document_ids.append(document_id)
                
            else:
                self.log_result("Upload facture fournisseur", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Facture fournisseur test", False, f"Exception: {str(e)}")

    def test_price_extraction_patterns(self):
        """Test 4: Test spécifique des patterns d'extraction de prix"""
        print("\n=== TEST 4: PATTERNS D'EXTRACTION DE PRIX ===")
        
        # Créer un document avec différents formats de prix pour tester les regex
        test_text = """RAPPORT Z TEST PATTERNS
        
        Formats à tester:
        (x3) Linguine aux palourdes 28,00
        Burrata di Bufala €18.50 x 2  
        4x Supions persillade 24,00
        Bœuf Wellington €56.00 x 1
        Tiramisu maison 12,50 x 3
        (x2) Vin rouge 15,00
        Pastis €8.50 x 3
        
        TOTAL CA: 687.50€"""
        
        try:
            # Simuler l'upload d'un document avec ce texte
            img = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                font = ImageFont.load_default()
            
            y_pos = 50
            for line in test_text.split('\n'):
                if line.strip():
                    draw.text((50, y_pos), line.strip(), fill='black', font=font)
                y_pos += 25
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            image_data = buffer.getvalue()
            
            files = {
                'file': ('price_patterns_test.png', image_data, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                self.log_result("Upload price patterns test", True, 
                              f"Document patterns uploadé: {document_id}")
                
                # Analyser les données parsées pour vérifier l'extraction des prix
                donnees_parsees = result.get("donnees_parsees", {})
                
                if donnees_parsees:
                    items_by_category = donnees_parsees.get("items_by_category", {})
                    
                    # Analyser chaque item pour voir si les prix sont extraits
                    detailed_analysis = []
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            item_name = item.get("name", "")
                            unit_price = item.get("unit_price")
                            total_price = item.get("total_price")
                            quantity = item.get("quantity_sold", 0)
                            
                            analysis = {
                                "name": item_name,
                                "category": category,
                                "quantity": quantity,
                                "unit_price": unit_price,
                                "total_price": total_price,
                                "has_price": unit_price is not None or total_price is not None
                            }
                            detailed_analysis.append(analysis)
                    
                    # Compter les succès d'extraction
                    items_with_prices = sum(1 for item in detailed_analysis if item["has_price"])
                    total_items = len(detailed_analysis)
                    
                    if total_items > 0:
                        success_rate = (items_with_prices / total_items) * 100
                        
                        self.log_result("Price extraction success rate", True, 
                                      f"Taux de succès: {success_rate:.1f}% ({items_with_prices}/{total_items})")
                        
                        # Afficher les détails
                        print("   Détails extraction par item:")
                        for item in detailed_analysis[:5]:  # Afficher les 5 premiers
                            status = "✅" if item["has_price"] else "❌"
                            print(f"     {status} {item['name']}: qty={item['quantity']}, unit_price={item['unit_price']}, total_price={item['total_price']}")
                        
                        # VALIDATION CRITIQUE
                        if success_rate >= 50:  # Au moins 50% des items doivent avoir des prix
                            self.log_result("CRITICAL: Price extraction working", True, 
                                          f"✅ Extraction prix fonctionne: {success_rate:.1f}% de succès")
                        else:
                            self.log_result("CRITICAL: Price extraction working", False, 
                                          f"❌ Extraction prix défaillante: {success_rate:.1f}% de succès")
                    else:
                        self.log_result("Items found", False, "Aucun item trouvé dans le parsing")
                
                self.created_document_ids.append(document_id)
                
            else:
                self.log_result("Upload price patterns test", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Price patterns test", False, f"Exception: {str(e)}")

    def cleanup_test_documents(self):
        """Nettoie les documents créés pendant les tests"""
        print("\n=== NETTOYAGE DES DOCUMENTS DE TEST ===")
        
        for document_id in self.created_document_ids:
            try:
                response = requests.delete(f"{BASE_URL}/ocr/document/{document_id}")
                if response.status_code == 200:
                    self.log_result(f"Cleanup document {document_id[:8]}", True, "Document supprimé")
                else:
                    self.log_result(f"Cleanup document {document_id[:8]}", False, 
                                  f"Erreur suppression: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup document {document_id[:8]}", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests OCR unit_price/total_price"""
        print("🎯 DÉBUT DES TESTS OCR UNIT_PRICE/TOTAL_PRICE")
        print("=" * 60)
        
        # Test 1: Upload image avec prix
        self.test_upload_z_report_image_with_prices()
        
        # Test 2: Documents existants et enrichment
        self.test_existing_z_report_enrichment()
        
        # Test 3: Pas de régression facture fournisseur
        self.test_facture_fournisseur_no_regression()
        
        # Test 4: Patterns d'extraction spécifiques
        self.test_price_extraction_patterns()
        
        # Nettoyage
        self.cleanup_test_documents()
        
        # Résumé des résultats
        self.print_summary()

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS OCR UNIT_PRICE/TOTAL_PRICE")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        # Afficher les tests critiques
        critical_tests = [r for r in self.test_results if "CRITICAL" in r["test"]]
        if critical_tests:
            print(f"\n🔥 TESTS CRITIQUES:")
            for test in critical_tests:
                status = "✅ PASS" if test["success"] else "❌ FAIL"
                print(f"   {status} {test['test']}: {test['message']}")
        
        # Afficher les échecs
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print(f"\n❌ ÉCHECS DÉTAILLÉS:")
            for result in failed_results:
                print(f"   • {result['test']}: {result['message']}")
                if result.get("details"):
                    print(f"     Détails: {result['details']}")

if __name__ == "__main__":
    test_suite = OCRUnitPriceTestSuite()
    test_suite.run_all_tests()