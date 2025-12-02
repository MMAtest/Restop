#!/usr/bin/env python3
"""
Test spécifique pour les corrections du système OCR
Focus sur les corrections MongoDB ObjectId et amélioration du parsing
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Configuration
BASE_URL = "https://easy-resto-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRTestSuite:
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
    
    def create_mock_base64_image(self, text_content):
        """Créer une image base64 simulée avec du texte pour les tests OCR"""
        # Créer une image blanche
        img = Image.new('RGB', (500, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Ajouter le texte
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Diviser le texte en lignes et les dessiner
        lines = text_content.strip().split('\n')
        y_offset = 10
        for line in lines:
            if line.strip():
                draw.text((10, y_offset), line.strip(), fill='black', font=font)
                y_offset += 20
        
        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def test_ocr_documents_list_serialization(self):
        """Test 1: Vérifier que GET /api/ocr/documents fonctionne sans erreur ObjectId"""
        print("\n=== TEST MONGODB OBJECTID SERIALIZATION FIX ===")
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                if isinstance(documents, list):
                    self.log_result("GET /api/ocr/documents", True, 
                                  f"Liste récupérée avec succès: {len(documents)} document(s)")
                    
                    # Vérifier qu'il n'y a pas d'erreur de sérialisation ObjectId
                    if len(documents) > 0:
                        doc = documents[0]
                        if "_id" not in doc:
                            self.log_result("ObjectId serialization fix", True, 
                                          "Aucun _id MongoDB dans la réponse JSON")
                        else:
                            self.log_result("ObjectId serialization fix", False, 
                                          "_id MongoDB présent dans la réponse")
                    else:
                        self.log_result("ObjectId serialization fix", True, 
                                      "Pas de documents existants pour tester la sérialisation")
                else:
                    self.log_result("GET /api/ocr/documents", False, 
                                  f"Format de réponse incorrect: {type(documents)}")
            else:
                self.log_result("GET /api/ocr/documents", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/ocr/documents", False, "Exception", str(e))
    
    def test_enhanced_z_report_parsing(self):
        """Test 2: Vérifier l'amélioration du parsing Z-report avec noms de plats réalistes"""
        print("\n=== TEST ENHANCED Z-REPORT PARSING ===")
        
        # Données réalistes de La Table d'Augustine
        z_report_text = """
        RAPPORT Z - 15/12/2024
        Restaurant La Table d'Augustine
        
        Linguine aux palourdes: 3
        Supions en persillade: 2  
        Rigatoni à la truffe: 1
        Bœuf Wellington à la truffe: 1
        Fleurs de courgettes de Mamet: 2
        Souris d'agneau confite: 1
        
        Total CA: 184.00€
        Couverts: 10
        """
        
        mock_image_base64 = self.create_mock_base64_image(z_report_text)
        
        try:
            files = {
                'file': ('z_report_augustine.jpg', base64.b64decode(mock_image_base64), 'image/jpeg')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                if "document_id" in result:
                    self.created_document_ids.append(result["document_id"])
                    self.log_result("POST /ocr/upload-document (Z-report)", True, 
                                  f"Document traité, ID: {result['document_id'][:8]}...")
                    
                    # Vérifier le parsing amélioré
                    if "donnees_parsees" in result:
                        parsed_data = result["donnees_parsees"]
                        plats_vendus = parsed_data.get("plats_vendus", [])
                        
                        # Vérifier que les noms de plats complexes sont bien extraits
                        expected_dishes = [
                            "Linguine aux palourdes",
                            "Supions en persillade", 
                            "Rigatoni à la truffe",
                            "Bœuf Wellington à la truffe",
                            "Fleurs de courgettes de Mamet",
                            "Souris d'agneau confite"
                        ]
                        
                        found_dishes = [plat["nom"] for plat in plats_vendus]
                        correctly_parsed = 0
                        
                        for expected in expected_dishes:
                            if any(expected.lower() in found.lower() for found in found_dishes):
                                correctly_parsed += 1
                        
                        if correctly_parsed >= 4:  # Au moins 4 sur 6
                            self.log_result("Enhanced Z-report parsing", True, 
                                          f"{correctly_parsed}/{len(expected_dishes)} plats correctement parsés")
                            
                            # Vérifier les quantités
                            linguine = next((p for p in plats_vendus if "linguine" in p["nom"].lower()), None)
                            if linguine and linguine.get("quantite") == 3:
                                self.log_result("Z-report quantities parsing", True, 
                                              f"Quantité Linguine correcte: {linguine['quantite']}")
                            else:
                                self.log_result("Z-report quantities parsing", False, 
                                              "Quantités incorrectes ou manquantes")
                        else:
                            self.log_result("Enhanced Z-report parsing", False, 
                                          f"Seulement {correctly_parsed}/{len(expected_dishes)} plats parsés")
                            self.log_result("Found dishes", False, f"Trouvés: {found_dishes}")
                    else:
                        self.log_result("POST /ocr/upload-document (Z-report)", False, 
                                      "Données parsées manquantes")
                else:
                    self.log_result("POST /ocr/upload-document (Z-report)", False, 
                                  "Document ID manquant dans la réponse")
            else:
                self.log_result("POST /ocr/upload-document (Z-report)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /ocr/upload-document (Z-report)", False, "Exception", str(e))
    
    def test_enhanced_invoice_parsing(self):
        """Test 3: Vérifier l'amélioration du parsing facture avec extraction produits"""
        print("\n=== TEST ENHANCED INVOICE PARSING ===")
        
        # Données réalistes de facture fournisseur
        facture_text = """
        Maison Artigiana
        Giuseppe Pellegrino
        Facture N° FAC-2024-001
        Date: 15/12/2024
        
        Burrata 2x 8.50€ = 17.00€
        Mozzarella 1kg x 24.00€ = 24.00€
        Parmesan Reggiano 500g x 45.00€ = 22.50€
        Truffe d'été 100g x 8.00€ = 8.00€
        
        Total HT: 71.50€
        Total TTC: 78.65€
        """
        
        mock_image_base64 = self.create_mock_base64_image(facture_text)
        
        try:
            files = {
                'file': ('facture_artigiana.jpg', base64.b64decode(mock_image_base64), 'image/jpeg')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                if "document_id" in result:
                    self.created_document_ids.append(result["document_id"])
                    self.log_result("POST /ocr/upload-document (Facture)", True, 
                                  f"Facture traitée, ID: {result['document_id'][:8]}...")
                    
                    # Vérifier le parsing amélioré
                    if "donnees_parsees" in result:
                        parsed_data = result["donnees_parsees"]
                        
                        # Vérifier le fournisseur
                        if parsed_data.get("fournisseur") == "Maison Artigiana":
                            self.log_result("Invoice supplier parsing", True, 
                                          f"Fournisseur correctement identifié: {parsed_data['fournisseur']}")
                        else:
                            self.log_result("Invoice supplier parsing", False, 
                                          f"Fournisseur incorrect: {parsed_data.get('fournisseur')}")
                        
                        # Vérifier les produits
                        produits = parsed_data.get("produits", [])
                        expected_products = ["Burrata", "Mozzarella", "Parmesan Reggiano", "Truffe"]
                        
                        found_products = [p["nom"] for p in produits]
                        correctly_parsed = 0
                        
                        for expected in expected_products:
                            if any(expected.lower() in found.lower() for found in found_products):
                                correctly_parsed += 1
                        
                        if correctly_parsed >= 3:  # Au moins 3 sur 4
                            self.log_result("Enhanced invoice parsing", True, 
                                          f"{correctly_parsed}/{len(expected_products)} produits correctement parsés")
                            
                            # Vérifier les quantités et prix
                            burrata = next((p for p in produits if "burrata" in p["nom"].lower()), None)
                            if burrata and burrata.get("quantite") == 2.0 and burrata.get("prix_unitaire") == 8.50:
                                self.log_result("Invoice quantities/prices parsing", True, 
                                              f"Burrata: {burrata['quantite']}x {burrata['prix_unitaire']}€")
                            else:
                                self.log_result("Invoice quantities/prices parsing", False, 
                                              "Quantités/prix incorrects")
                        else:
                            self.log_result("Enhanced invoice parsing", False, 
                                          f"Seulement {correctly_parsed}/{len(expected_products)} produits parsés")
                            self.log_result("Found products", False, f"Trouvés: {found_products}")
                        
                        # Vérifier les totaux
                        if parsed_data.get("total_ht") == 71.50 and parsed_data.get("total_ttc") == 78.65:
                            self.log_result("Invoice totals parsing", True, 
                                          f"Totaux corrects: HT={parsed_data['total_ht']}€, TTC={parsed_data['total_ttc']}€")
                        else:
                            self.log_result("Invoice totals parsing", False, 
                                          f"Totaux incorrects: HT={parsed_data.get('total_ht')}, TTC={parsed_data.get('total_ttc')}")
                    else:
                        self.log_result("POST /ocr/upload-document (Facture)", False, 
                                      "Données parsées manquantes")
                else:
                    self.log_result("POST /ocr/upload-document (Facture)", False, 
                                  "Document ID manquant")
            else:
                self.log_result("POST /ocr/upload-document (Facture)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /ocr/upload-document (Facture)", False, "Exception", str(e))
    
    def test_document_retrieval_by_id(self):
        """Test 4: Vérifier que GET /api/ocr/document/{id} fonctionne sans erreur ObjectId"""
        print("\n=== TEST DOCUMENT RETRIEVAL BY ID ===")
        
        if not self.created_document_ids:
            self.log_result("GET /api/ocr/document/{id}", False, 
                          "Aucun document créé pour tester la récupération")
            return
        
        document_id = self.created_document_ids[0]
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            if response.status_code == 200:
                document = response.json()
                if isinstance(document, dict):
                    self.log_result("GET /api/ocr/document/{id}", True, 
                                  f"Document récupéré avec succès: {document.get('type_document', 'N/A')}")
                    
                    # Vérifier qu'il n'y a pas d'erreur de sérialisation ObjectId
                    if "_id" not in document:
                        self.log_result("Document ObjectId serialization fix", True, 
                                      "Aucun _id MongoDB dans la réponse JSON")
                    else:
                        self.log_result("Document ObjectId serialization fix", False, 
                                      "_id MongoDB présent dans la réponse")
                    
                    # Vérifier la structure complète
                    required_fields = ["id", "type_document", "nom_fichier", "texte_extrait", "donnees_parsees"]
                    missing_fields = [field for field in required_fields if field not in document]
                    
                    if not missing_fields:
                        self.log_result("Document structure validation", True, 
                                      "Tous les champs requis présents")
                    else:
                        self.log_result("Document structure validation", False, 
                                      f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("GET /api/ocr/document/{id}", False, 
                                  f"Format de réponse incorrect: {type(document)}")
            else:
                self.log_result("GET /api/ocr/document/{id}", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/ocr/document/{id}", False, "Exception", str(e))
    
    def test_z_report_stock_processing(self):
        """Test 5: Vérifier le traitement des stocks basé sur Z-report avec noms améliorés"""
        print("\n=== TEST Z-REPORT STOCK PROCESSING ===")
        
        # Trouver un document Z-report créé
        z_report_doc_id = None
        for doc_id in self.created_document_ids:
            try:
                response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                if response.status_code == 200:
                    doc = response.json()
                    if doc.get("type_document") == "z_report":
                        z_report_doc_id = doc_id
                        break
            except:
                continue
        
        if not z_report_doc_id:
            self.log_result("Z-report stock processing", False, 
                          "Aucun document Z-report disponible pour le traitement")
            return
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{z_report_doc_id}")
            if response.status_code == 200:
                result = response.json()
                if "stock_updates" in result:
                    stock_updates = result["stock_updates"]
                    warnings = result.get("warnings", [])
                    
                    self.log_result("POST /ocr/process-z-report/{id}", True, 
                                  f"Traitement terminé: {len(stock_updates)} mises à jour, {len(warnings)} avertissements")
                    
                    # Analyser les avertissements pour voir si les noms de plats sont mieux reconnus
                    recipe_not_found_warnings = [w for w in warnings if "Recette non trouvée" in w]
                    
                    if len(recipe_not_found_warnings) < 4:  # Moins de 4 recettes non trouvées sur 6
                        self.log_result("Recipe matching improvement", True, 
                                      f"Amélioration du matching: seulement {len(recipe_not_found_warnings)} recettes non trouvées")
                    else:
                        self.log_result("Recipe matching improvement", False, 
                                      f"Trop de recettes non trouvées: {len(recipe_not_found_warnings)}")
                        # Afficher les avertissements pour debug
                        for warning in recipe_not_found_warnings[:3]:
                            print(f"   Warning: {warning}")
                    
                    # Si des mises à jour ont été effectuées, vérifier qu'elles sont cohérentes
                    if stock_updates:
                        first_update = stock_updates[0]
                        required_update_fields = ["produit_nom", "quantite_deduite", "nouvelle_quantite", "plat"]
                        if all(field in first_update for field in required_update_fields):
                            self.log_result("Stock update structure", True, 
                                          f"Structure correcte: {first_update['plat']} -> {first_update['quantite_deduite']} déduite")
                        else:
                            self.log_result("Stock update structure", False, 
                                          "Structure de mise à jour incorrecte")
                else:
                    self.log_result("POST /ocr/process-z-report/{id}", False, 
                                  "Réponse sans stock_updates")
            else:
                self.log_result("POST /ocr/process-z-report/{id}", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /ocr/process-z-report/{id}", False, "Exception", str(e))
    
    def cleanup_test_documents(self):
        """Nettoyer les documents de test créés"""
        print("\n=== NETTOYAGE DOCUMENTS TEST ===")
        
        for doc_id in self.created_document_ids:
            try:
                response = requests.delete(f"{BASE_URL}/ocr/document/{doc_id}")
                if response.status_code == 200:
                    self.log_result(f"DELETE document {doc_id[:8]}", True, "Document supprimé")
                else:
                    self.log_result(f"DELETE document {doc_id[:8]}", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result(f"DELETE document {doc_id[:8]}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests OCR"""
        print("🔍 DÉBUT DES TESTS OCR SYSTEM FIXES")
        print("=" * 60)
        
        # Tests dans l'ordre logique
        self.test_ocr_documents_list_serialization()
        self.test_enhanced_z_report_parsing()
        self.test_enhanced_invoice_parsing()
        self.test_document_retrieval_by_id()
        self.test_z_report_stock_processing()
        
        # Nettoyage
        self.cleanup_test_documents()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS OCR")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests} tests")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    test_suite = OCRTestSuite()
    passed, failed = test_suite.run_all_tests()
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS OCR SONT PASSÉS!")
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué sur {passed + failed}")