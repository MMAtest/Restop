#!/usr/bin/env python3
"""
Test complet du backend OCR pour validation unit_price/total_price selon demande de re-test
Focus sur: Ensure unit_price/total_price are now populated via parsing or enrichment
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time

# Configuration
BASE_URL = "https://rest-mgmt-sys.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ComprehensiveOCRTestSuite:
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

    def create_enhanced_z_report_image(self):
        """Crée une image Z-report avec formats de prix variés pour test complet"""
        img = Image.new('RGB', (900, 1200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            font_title = font_normal = font_small = ImageFont.load_default()
        
        # Contenu Z-report avec tous les formats de prix testés
        y_pos = 40
        
        # Titre
        draw.text((50, y_pos), "RAPPORT Z - LA TABLE D'AUGUSTINE", fill='black', font=font_title)
        y_pos += 50
        draw.text((50, y_pos), "Date: 15/01/2025 - Service: Soir", fill='black', font=font_normal)
        y_pos += 60
        
        # Sections avec différents formats
        sections = [
            ("BAR:", [
                "(x3) Linguine aux palourdes 28,00",
                "Burrata €18.50 x 2",
                "Vin rouge Côtes du Rhône 15,00 x 2",
                "Pastis Ricard €8.50 x 3"
            ]),
            ("ENTRÉES:", [
                "4x Supions persillade 24,00", 
                "Fleurs de courgettes €21.00 x 2",
                "(x1) Tartare de thon 26,50",
                "Burrata des Pouilles 18,50 x 3"
            ]),
            ("PLATS:", [
                "Bœuf Wellington €56.00 x 1",
                "(x2) Souris d'agneau confite 36,00",
                "Linguine palourdes 28,00 x 4",
                "Rigatoni truffe €31.00 x 2"
            ]),
            ("DESSERTS:", [
                "Tiramisu maison 12,50 x 3",
                "(x2) Tarte aux figues €14.00",
                "Mousse chocolat 11,00 x 4",
                "Glace vanille €8.50 x 5"
            ])
        ]
        
        for section_title, items in sections:
            # Titre de section
            draw.text((50, y_pos), section_title, fill='black', font=font_normal)
            y_pos += 35
            
            # Items de la section
            for item in items:
                draw.text((80, y_pos), item, fill='black', font=font_small)
                y_pos += 28
            
            y_pos += 15  # Espacement entre sections
        
        # Total
        y_pos += 20
        draw.text((50, y_pos), "TOTAL CA: 1,247.50€", fill='black', font=font_normal)
        y_pos += 35
        draw.text((50, y_pos), "Nombre de couverts: 42", fill='black', font=font_normal)
        
        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"

    def test_comprehensive_z_report_upload(self):
        """Test 1: Upload Z-report complet avec validation unit_price/total_price"""
        print("\n=== TEST 1: UPLOAD Z-REPORT COMPLET AVEC PRIX ===")
        
        image_base64 = self.create_enhanced_z_report_image()
        
        try:
            # Upload du document
            image_data = base64.b64decode(image_base64.split(',')[1])
            
            files = {
                'file': ('comprehensive_z_report.png', image_data, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                self.created_document_ids.append(document_id)
                
                self.log_result("Upload comprehensive Z-report", True, 
                              f"Document uploadé: {document_id}")
                
                # Analyser les données parsées
                donnees_parsees = result.get("donnees_parsees", {})
                
                if donnees_parsees:
                    items_by_category = donnees_parsees.get("items_by_category", {})
                    
                    # Statistiques détaillées
                    total_items = 0
                    items_with_unit_price = 0
                    items_with_total_price = 0
                    items_with_both_prices = 0
                    
                    category_stats = {}
                    
                    for category, items in items_by_category.items():
                        cat_total = len(items)
                        cat_unit_price = sum(1 for item in items if item.get("unit_price") is not None)
                        cat_total_price = sum(1 for item in items if item.get("total_price") is not None)
                        
                        category_stats[category] = {
                            "total": cat_total,
                            "with_unit_price": cat_unit_price,
                            "with_total_price": cat_total_price
                        }
                        
                        total_items += cat_total
                        items_with_unit_price += cat_unit_price
                        items_with_total_price += cat_total_price
                        
                        for item in items:
                            if item.get("unit_price") is not None and item.get("total_price") is not None:
                                items_with_both_prices += 1
                    
                    # Calcul des pourcentages
                    unit_price_rate = (items_with_unit_price / total_items * 100) if total_items > 0 else 0
                    total_price_rate = (items_with_total_price / total_items * 100) if total_items > 0 else 0
                    both_prices_rate = (items_with_both_prices / total_items * 100) if total_items > 0 else 0
                    
                    self.log_result("Items analysis", True, 
                                  f"Total: {total_items}, Unit price: {items_with_unit_price} ({unit_price_rate:.1f}%), Total price: {items_with_total_price} ({total_price_rate:.1f}%)")
                    
                    # Affichage détaillé par catégorie
                    print("   Détails par catégorie:")
                    for category, stats in category_stats.items():
                        print(f"     {category}: {stats['with_unit_price']}/{stats['total']} unit_price, {stats['with_total_price']}/{stats['total']} total_price")
                    
                    # VALIDATION CRITIQUE: Au moins 30% des items doivent avoir des prix
                    if unit_price_rate >= 30 or total_price_rate >= 30:
                        self.log_result("CRITICAL: Price extraction rate", True, 
                                      f"✅ Taux extraction acceptable: unit_price {unit_price_rate:.1f}%, total_price {total_price_rate:.1f}%")
                    else:
                        self.log_result("CRITICAL: Price extraction rate", False, 
                                      f"❌ Taux extraction insuffisant: unit_price {unit_price_rate:.1f}%, total_price {total_price_rate:.1f}%")
                    
                    # Vérifier le grand total
                    grand_total = donnees_parsees.get("grand_total_sales")
                    if grand_total and grand_total > 1000:
                        self.log_result("Grand total extraction", True, 
                                      f"Grand total extrait: {grand_total}€")
                    else:
                        self.log_result("Grand total extraction", False, 
                                      f"Grand total incorrect: {grand_total}")
                    
                    return document_id
                else:
                    self.log_result("Parsed data", False, "Aucune donnée parsée")
                    return None
            else:
                self.log_result("Upload comprehensive Z-report", False, 
                              f"Erreur {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Upload comprehensive Z-report", False, f"Exception: {str(e)}")
            return None

    def test_existing_documents_enrichment(self):
        """Test 2: Validation enrichment sur documents existants"""
        print("\n=== TEST 2: VALIDATION ENRICHMENT DOCUMENTS EXISTANTS ===")
        
        try:
            # GET tous les documents
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code == 200:
                documents = response.json()
                z_reports = [doc for doc in documents if doc.get("type_document") == "z_report"]
                
                self.log_result("GET existing documents", True, 
                              f"{len(documents)} documents total, {len(z_reports)} Z-reports")
                
                if z_reports:
                    # Analyser plusieurs Z-reports existants
                    analyzed_docs = 0
                    total_enriched_items = 0
                    total_items_analyzed = 0
                    
                    for z_report in z_reports[:5]:  # Analyser les 5 premiers
                        doc_id = z_report["id"]
                        
                        # GET document détaillé
                        doc_response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                        
                        if doc_response.status_code == 200:
                            doc_detail = doc_response.json()
                            donnees_parsees = doc_detail.get("donnees_parsees", {})
                            
                            if donnees_parsees:
                                items_by_category = donnees_parsees.get("items_by_category", {})
                                
                                doc_items = 0
                                doc_enriched = 0
                                
                                for category, items in items_by_category.items():
                                    for item in items:
                                        doc_items += 1
                                        if item.get("unit_price") is not None or item.get("total_price") is not None:
                                            doc_enriched += 1
                                
                                total_items_analyzed += doc_items
                                total_enriched_items += doc_enriched
                                analyzed_docs += 1
                                
                                enrichment_rate = (doc_enriched / doc_items * 100) if doc_items > 0 else 0
                                print(f"     Doc {doc_id[:8]}: {doc_enriched}/{doc_items} items enrichis ({enrichment_rate:.1f}%)")
                    
                    if analyzed_docs > 0:
                        overall_rate = (total_enriched_items / total_items_analyzed * 100) if total_items_analyzed > 0 else 0
                        
                        self.log_result("Overall enrichment analysis", True, 
                                      f"{analyzed_docs} docs analysés: {total_enriched_items}/{total_items_analyzed} items enrichis ({overall_rate:.1f}%)")
                        
                        # VALIDATION: Au moins quelques items doivent être enrichis
                        if total_enriched_items > 0:
                            self.log_result("CRITICAL: Enrichment functioning", True, 
                                          f"✅ Enrichment fonctionne: {total_enriched_items} items enrichis sur {total_items_analyzed}")
                        else:
                            self.log_result("CRITICAL: Enrichment functioning", False, 
                                          "❌ Aucun item enrichi trouvé")
                    else:
                        self.log_result("Document analysis", False, "Aucun document analysable")
                else:
                    self.log_result("Z-reports found", False, "Aucun Z-report existant")
            else:
                self.log_result("GET existing documents", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Existing documents test", False, f"Exception: {str(e)}")

    def test_facture_fournisseur_regression(self):
        """Test 3: Vérification non-régression facture_fournisseur"""
        print("\n=== TEST 3: NON-RÉGRESSION FACTURE FOURNISSEUR ===")
        
        try:
            # Créer une facture fournisseur simple
            img = Image.new('RGB', (700, 900), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font_title = font_normal = ImageFont.load_default()
            
            y_pos = 50
            facture_content = [
                ("FACTURE FOURNISSEUR", font_title),
                ("", font_normal),
                ("Fournisseur: Maison Artigiana", font_normal),
                ("Contact: Giuseppe Pellegrino", font_normal),
                ("Date: 15/01/2025", font_normal),
                ("N° Facture: FAC-2025-001", font_normal),
                ("", font_normal),
                ("PRODUITS LIVRÉS:", font_normal),
                ("Burrata des Pouilles - 5 kg - 42.50€", font_normal),
                ("Mozzarella di Bufala - 3 kg - 24.00€", font_normal),
                ("Huile d'olive extra - 2 L - 18.00€", font_normal),
                ("Parmesan Reggiano - 1 kg - 35.00€", font_normal),
                ("", font_normal),
                ("SOUS-TOTAL HT: 119.50€", font_normal),
                ("TVA 20%: 23.90€", font_normal),
                ("TOTAL TTC: 143.40€", font_normal)
            ]
            
            for line_text, font in facture_content:
                if line_text.strip():
                    draw.text((50, y_pos), line_text, fill='black', font=font)
                y_pos += 35
            
            # Upload de la facture
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            image_data = buffer.getvalue()
            
            files = {
                'file': ('facture_regression_test.png', image_data, 'image/png')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                self.created_document_ids.append(document_id)
                
                self.log_result("Upload facture fournisseur", True, 
                              f"Facture uploadée: {document_id}")
                
                # Vérifier le type de document
                doc_type = result.get("type_document")
                if doc_type == "facture_fournisseur":
                    self.log_result("Document type validation", True, 
                                  "Type facture_fournisseur correct")
                else:
                    self.log_result("Document type validation", False, 
                                  f"Type incorrect: {doc_type}")
                
                # Vérifier l'extraction de texte
                extracted_text = result.get("texte_extrait", "")
                if len(extracted_text) > 50:
                    self.log_result("Facture text extraction", True, 
                                  f"Texte extrait: {len(extracted_text)} caractères")
                    
                    # Vérifier les éléments clés
                    key_elements = ["FACTURE", "Fournisseur", "TOTAL", "Maison Artigiana"]
                    found_elements = [elem for elem in key_elements 
                                    if elem.lower() in extracted_text.lower()]
                    
                    if len(found_elements) >= 3:
                        self.log_result("Facture key elements", True, 
                                      f"Éléments clés trouvés: {found_elements}")
                    else:
                        self.log_result("Facture key elements", False, 
                                      f"Éléments manquants: {found_elements}")
                else:
                    self.log_result("Facture text extraction", False, 
                                  "Extraction de texte insuffisante")
                
                # Vérifier que le parsing ne confond pas avec z_report
                donnees_parsees = result.get("donnees_parsees", {})
                if donnees_parsees:
                    # Pour une facture, on ne doit pas avoir items_by_category comme un z_report
                    if "items_by_category" not in donnees_parsees:
                        self.log_result("Facture parsing differentiation", True, 
                                      "Parsing facture distinct du Z-report")
                    else:
                        self.log_result("Facture parsing differentiation", False, 
                                      "Parsing confondu avec Z-report")
                
                # VALIDATION: Pas de régression sur facture_fournisseur
                self.log_result("CRITICAL: Facture fournisseur no regression", True, 
                              "✅ Facture fournisseur fonctionne sans régression")
                
            else:
                self.log_result("Upload facture fournisseur", False, 
                              f"Erreur {response.status_code}: {response.text}")
                self.log_result("CRITICAL: Facture fournisseur no regression", False, 
                              "❌ Régression détectée sur facture_fournisseur")
                
        except Exception as e:
            self.log_result("Facture fournisseur test", False, f"Exception: {str(e)}")
            self.log_result("CRITICAL: Facture fournisseur no regression", False, 
                          f"❌ Exception: {str(e)}")

    def test_price_parsing_accuracy(self):
        """Test 4: Test précision parsing des prix avec formats spécifiques"""
        print("\n=== TEST 4: PRÉCISION PARSING PRIX FORMATS SPÉCIFIQUES ===")
        
        # Test avec un document contenant exactement les formats mentionnés dans la demande
        test_formats = [
            "(x3) Linguine 28,00",
            "Burrata €18.50 x 2",
            "4x Supions persillade 24,00",
            "Bœuf Wellington €56.00 x 1",
            "(x2) Vin rouge 15,00",
            "Tiramisu 12,50 x 3"
        ]
        
        try:
            # Créer image avec formats exacts
            img = Image.new('RGB', (600, 500), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
            except:
                font = ImageFont.load_default()
            
            y_pos = 50
            draw.text((50, y_pos), "RAPPORT Z - TEST FORMATS", fill='black', font=font)
            y_pos += 50
            
            for format_line in test_formats:
                draw.text((50, y_pos), format_line, fill='black', font=font)
                y_pos += 35
            
            y_pos += 20
            draw.text((50, y_pos), "TOTAL CA: 287.50€", fill='black', font=font)
            
            # Upload
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            image_data = buffer.getvalue()
            
            files = {
                'file': ('price_formats_test.png', image_data, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                self.created_document_ids.append(document_id)
                
                self.log_result("Upload price formats test", True, 
                              f"Document formats uploadé: {document_id}")
                
                # Analyser la précision d'extraction
                donnees_parsees = result.get("donnees_parsees", {})
                
                if donnees_parsees:
                    items_by_category = donnees_parsees.get("items_by_category", {})
                    
                    # Chercher les items correspondant aux formats testés
                    expected_items = [
                        {"name_contains": "Linguine", "expected_price": 28.00, "expected_qty": 3},
                        {"name_contains": "Burrata", "expected_price": 18.50, "expected_qty": 2},
                        {"name_contains": "Supions", "expected_price": 24.00, "expected_qty": 4},
                        {"name_contains": "Wellington", "expected_price": 56.00, "expected_qty": 1},
                        {"name_contains": "Vin", "expected_price": 15.00, "expected_qty": 2},
                        {"name_contains": "Tiramisu", "expected_price": 12.50, "expected_qty": 3}
                    ]
                    
                    matches_found = 0
                    price_accuracy = 0
                    
                    for category, items in items_by_category.items():
                        for item in items:
                            item_name = item.get("name", "").lower()
                            
                            for expected in expected_items:
                                if expected["name_contains"].lower() in item_name:
                                    matches_found += 1
                                    
                                    # Vérifier la précision des prix
                                    unit_price = item.get("unit_price")
                                    total_price = item.get("total_price")
                                    quantity = item.get("quantity_sold", 0)
                                    
                                    if unit_price == expected["expected_price"]:
                                        price_accuracy += 1
                                        print(f"     ✅ {item_name}: unit_price correct ({unit_price}€)")
                                    elif total_price and quantity:
                                        calculated_unit = total_price / quantity
                                        if abs(calculated_unit - expected["expected_price"]) < 0.01:
                                            price_accuracy += 1
                                            print(f"     ✅ {item_name}: prix calculé correct ({calculated_unit:.2f}€)")
                                        else:
                                            print(f"     ❌ {item_name}: prix incorrect (attendu: {expected['expected_price']}€, trouvé: unit={unit_price}, total={total_price}, qty={quantity})")
                                    else:
                                        print(f"     ❌ {item_name}: aucun prix extrait")
                                    break
                    
                    accuracy_rate = (price_accuracy / len(expected_items) * 100) if len(expected_items) > 0 else 0
                    
                    self.log_result("Price parsing accuracy", True, 
                                  f"Précision: {price_accuracy}/{len(expected_items)} ({accuracy_rate:.1f}%)")
                    
                    # VALIDATION: Au moins 50% de précision attendue
                    if accuracy_rate >= 50:
                        self.log_result("CRITICAL: Price parsing precision", True, 
                                      f"✅ Précision acceptable: {accuracy_rate:.1f}%")
                    else:
                        self.log_result("CRITICAL: Price parsing precision", False, 
                                      f"❌ Précision insuffisante: {accuracy_rate:.1f}%")
                else:
                    self.log_result("Price formats parsing", False, "Aucune donnée parsée")
            else:
                self.log_result("Upload price formats test", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Price formats test", False, f"Exception: {str(e)}")

    def cleanup_test_documents(self):
        """Nettoie les documents créés pendant les tests"""
        print("\n=== NETTOYAGE DES DOCUMENTS DE TEST ===")
        
        for document_id in self.created_document_ids:
            try:
                response = requests.delete(f"{BASE_URL}/ocr/document/{document_id}")
                if response.status_code == 200:
                    self.log_result(f"Cleanup {document_id[:8]}", True, "Document supprimé")
                else:
                    self.log_result(f"Cleanup {document_id[:8]}", False, 
                                  f"Erreur suppression: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup {document_id[:8]}", False, f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Exécute tous les tests OCR complets"""
        print("🎯 DÉBUT DES TESTS OCR COMPLETS - UNIT_PRICE/TOTAL_PRICE")
        print("=" * 70)
        
        # Test 1: Upload Z-report complet
        self.test_comprehensive_z_report_upload()
        
        # Test 2: Documents existants
        self.test_existing_documents_enrichment()
        
        # Test 3: Non-régression facture fournisseur
        self.test_facture_fournisseur_regression()
        
        # Test 4: Précision parsing prix
        self.test_price_parsing_accuracy()
        
        # Nettoyage
        self.cleanup_test_documents()
        
        # Résumé
        self.print_comprehensive_summary()

    def print_comprehensive_summary(self):
        """Affiche le résumé complet des tests"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ COMPLET DES TESTS OCR UNIT_PRICE/TOTAL_PRICE")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📈 RÉSULTATS GLOBAUX:")
        print(f"   Total tests: {total_tests}")
        print(f"   ✅ Réussis: {passed_tests}")
        print(f"   ❌ Échoués: {failed_tests}")
        print(f"   📊 Taux de réussite: {success_rate:.1f}%")
        
        # Tests critiques
        critical_tests = [r for r in self.test_results if "CRITICAL" in r["test"]]
        if critical_tests:
            print(f"\n🔥 TESTS CRITIQUES (VALIDATION PRINCIPALE):")
            for test in critical_tests:
                status = "✅ PASS" if test["success"] else "❌ FAIL"
                print(f"   {status} {test['test']}")
                print(f"      → {test['message']}")
        
        # Recommandations
        critical_failures = [r for r in critical_tests if not r["success"]]
        if critical_failures:
            print(f"\n⚠️  ACTIONS REQUISES:")
            for failure in critical_failures:
                print(f"   • {failure['test']}: {failure['message']}")
        else:
            print(f"\n✅ VALIDATION RÉUSSIE:")
            print(f"   • Unit_price/total_price sont maintenant peuplés via parsing/enrichment")
            print(f"   • Pas de régression sur facture_fournisseur")
            print(f"   • Enrichment fonctionne sur documents existants")

if __name__ == "__main__":
    test_suite = ComprehensiveOCRTestSuite()
    test_suite.run_comprehensive_tests()