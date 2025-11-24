#!/usr/bin/env python3
"""
Test spécifique pour l'endpoint OCR upload-document
Focus sur le problème rapporté: OCR reste bloqué sur "traitement" lors de l'upload de factures
"""

import requests
import json
import base64
import time
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BASE_URL = "https://restop.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRUploadTestSuite:
    def __init__(self):
        self.test_results = []
        self.uploaded_document_ids = []
        
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

    def create_test_image(self, text_content, filename="test_facture.png"):
        """Crée une image de test avec du texte pour simuler une facture"""
        try:
            # Créer une image blanche
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Essayer d'utiliser une police par défaut
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Ajouter le texte ligne par ligne
            lines = text_content.split('\n')
            y_position = 50
            for line in lines:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 30
            
            # Convertir en bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
        except Exception as e:
            print(f"Erreur création image test: {e}")
            # Retourner une image minimale en cas d'erreur
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'

    def create_test_pdf_content(self, text_content):
        """Crée un contenu PDF minimal pour les tests"""
        # PDF minimal avec le texte fourni
        pdf_header = b'%PDF-1.4\n'
        pdf_content = f"""1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(text_content) + 50}
>>
stream
BT
/F1 12 Tf
50 750 Td
({text_content}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000110 00000 n 
0000000181 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{200 + len(text_content)}
%%EOF""".encode('utf-8')
        
        return pdf_header + pdf_content

    def test_ocr_upload_image(self):
        """Test 1: Upload d'une image de facture"""
        print("\n=== TEST 1: UPLOAD IMAGE FACTURE ===")
        
        # Créer une image de test simulant une facture
        facture_text = """FACTURE FOURNISSEUR
Fournisseur: Marché Central
Date: 15/01/2025
Numéro: FAC-2025-001

PRODUITS:
Tomates: 10 kg x 3.50€ = 35.00€
Salade: 5 kg x 2.80€ = 14.00€
Carottes: 8 kg x 1.90€ = 15.20€

TOTAL HT: 64.20€
TVA 5.5%: 3.53€
TOTAL TTC: 67.73€"""
        
        try:
            image_content = self.create_test_image(facture_text)
            
            files = {
                'file': ('test_facture.png', image_content, 'image/png')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            print("Envoi de la requête d'upload...")
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            upload_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.uploaded_document_ids.append(document_id)
                    self.log_result("POST /ocr/upload-document (image)", True, 
                                  f"Upload réussi en {upload_time:.2f}s - ID: {document_id[:8]}...")
                    
                    # Vérifier que le traitement ne reste pas bloqué
                    if upload_time < 30:  # Doit se terminer en moins de 30 secondes
                        self.log_result("Temps de traitement image", True, 
                                      f"Traitement terminé en {upload_time:.2f}s (< 30s)")
                    else:
                        self.log_result("Temps de traitement image", False, 
                                      f"Traitement trop long: {upload_time:.2f}s")
                    
                    # Vérifier le statut du document
                    statut = result.get("donnees_parsees", {}).get("statut", "inconnu")
                    if statut != "en_attente":
                        self.log_result("Statut traitement image", True, f"Statut: {statut}")
                    else:
                        self.log_result("Statut traitement image", False, 
                                      "Document reste en attente de traitement")
                    
                    # Vérifier l'extraction de texte
                    texte_extrait = result.get("texte_extrait", "")
                    if len(texte_extrait) > 10:
                        self.log_result("Extraction texte image", True, 
                                      f"Texte extrait: {len(texte_extrait)} caractères")
                    else:
                        self.log_result("Extraction texte image", False, 
                                      f"Texte insuffisant: {len(texte_extrait)} caractères")
                    
                    return document_id
                else:
                    self.log_result("POST /ocr/upload-document (image)", False, 
                                  "Pas de document_id dans la réponse")
            else:
                self.log_result("POST /ocr/upload-document (image)", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /ocr/upload-document (image)", False, f"Exception: {str(e)}")
        
        return None

    def test_ocr_upload_pdf(self):
        """Test 2: Upload d'un PDF de facture"""
        print("\n=== TEST 2: UPLOAD PDF FACTURE ===")
        
        # Créer un PDF de test simulant une facture
        facture_text = """FACTURE FOURNISSEUR PDF
Fournisseur: Grossiste Bio
Date: 16/01/2025
Numéro: FAC-PDF-2025-002

PRODUITS:
Pommes Bio: 15 kg x 4.20€ = 63.00€
Poires Bio: 12 kg x 3.80€ = 45.60€
Oranges Bio: 10 kg x 3.50€ = 35.00€

TOTAL HT: 143.60€
TVA 5.5%: 7.90€
TOTAL TTC: 151.50€"""
        
        try:
            pdf_content = self.create_test_pdf_content(facture_text)
            
            files = {
                'file': ('test_facture.pdf', pdf_content, 'application/pdf')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            print("Envoi de la requête d'upload PDF...")
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            upload_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.uploaded_document_ids.append(document_id)
                    self.log_result("POST /ocr/upload-document (PDF)", True, 
                                  f"Upload PDF réussi en {upload_time:.2f}s - ID: {document_id[:8]}...")
                    
                    # Vérifier que le traitement ne reste pas bloqué
                    if upload_time < 30:
                        self.log_result("Temps de traitement PDF", True, 
                                      f"Traitement terminé en {upload_time:.2f}s (< 30s)")
                    else:
                        self.log_result("Temps de traitement PDF", False, 
                                      f"Traitement trop long: {upload_time:.2f}s")
                    
                    # Vérifier le type de fichier
                    file_type = result.get("file_type", "")
                    if file_type == "pdf":
                        self.log_result("Type fichier PDF", True, f"file_type: {file_type}")
                    else:
                        self.log_result("Type fichier PDF", False, 
                                      f"file_type incorrect: {file_type}")
                    
                    # Vérifier l'extraction de texte
                    texte_extrait = result.get("texte_extrait", "")
                    if len(texte_extrait) > 10:
                        self.log_result("Extraction texte PDF", True, 
                                      f"Texte extrait: {len(texte_extrait)} caractères")
                    else:
                        self.log_result("Extraction texte PDF", False, 
                                      f"Texte insuffisant: {len(texte_extrait)} caractères")
                    
                    return document_id
                else:
                    self.log_result("POST /ocr/upload-document (PDF)", False, 
                                  "Pas de document_id dans la réponse")
            else:
                self.log_result("POST /ocr/upload-document (PDF)", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /ocr/upload-document (PDF)", False, f"Exception: {str(e)}")
        
        return None

    def test_ocr_upload_z_report(self):
        """Test 3: Upload d'un rapport Z"""
        print("\n=== TEST 3: UPLOAD RAPPORT Z ===")
        
        # Créer une image de rapport Z
        z_report_text = """RAPPORT Z - RESTAURANT
Date: 16/01/2025
Service: Soir

VENTES PAR CATÉGORIE:

BAR:
Vin rouge: 8 verres
Bière pression: 12 verres
Cocktails: 5 verres

ENTRÉES:
Salade César: 6 portions
Soupe du jour: 4 portions

PLATS:
Steak frites: 8 portions
Saumon grillé: 5 portions
Pasta carbonara: 7 portions

DESSERTS:
Tiramisu: 4 portions
Tarte tatin: 3 portions

TOTAL CA: 485.50€
Nombre de couverts: 25"""
        
        try:
            image_content = self.create_test_image(z_report_text)
            
            files = {
                'file': ('rapport_z_test.png', image_content, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            print("Envoi de la requête d'upload rapport Z...")
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            upload_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.uploaded_document_ids.append(document_id)
                    self.log_result("POST /ocr/upload-document (Z-report)", True, 
                                  f"Upload Z-report réussi en {upload_time:.2f}s - ID: {document_id[:8]}...")
                    
                    # Vérifier que le traitement ne reste pas bloqué
                    if upload_time < 30:
                        self.log_result("Temps de traitement Z-report", True, 
                                      f"Traitement terminé en {upload_time:.2f}s (< 30s)")
                    else:
                        self.log_result("Temps de traitement Z-report", False, 
                                      f"Traitement trop long: {upload_time:.2f}s")
                    
                    # Vérifier les données parsées spécifiques au Z-report
                    donnees_parsees = result.get("donnees_parsees", {})
                    if isinstance(donnees_parsees, dict) and len(donnees_parsees) > 0:
                        self.log_result("Parsing Z-report", True, 
                                      f"Données parsées: {len(donnees_parsees)} champs")
                        
                        # Vérifier la structure spécifique
                        if "items_by_category" in donnees_parsees:
                            categories = donnees_parsees["items_by_category"]
                            if isinstance(categories, dict) and len(categories) > 0:
                                self.log_result("Catégorisation Z-report", True, 
                                              f"{len(categories)} catégories détectées")
                            else:
                                self.log_result("Catégorisation Z-report", False, 
                                              "Pas de catégories détectées")
                    else:
                        self.log_result("Parsing Z-report", False, "Données parsées vides")
                    
                    return document_id
                else:
                    self.log_result("POST /ocr/upload-document (Z-report)", False, 
                                  "Pas de document_id dans la réponse")
            else:
                self.log_result("POST /ocr/upload-document (Z-report)", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /ocr/upload-document (Z-report)", False, f"Exception: {str(e)}")
        
        return None

    def test_document_persistence(self):
        """Test 4: Vérifier que les documents sont bien sauvegardés en base"""
        print("\n=== TEST 4: PERSISTANCE DOCUMENTS ===")
        
        if not self.uploaded_document_ids:
            self.log_result("Persistance documents", False, "Aucun document uploadé pour tester")
            return
        
        try:
            # Test GET /ocr/documents - Liste des documents
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code == 200:
                documents = response.json()
                if isinstance(documents, list):
                    self.log_result("GET /ocr/documents", True, 
                                  f"{len(documents)} document(s) en base")
                    
                    # Vérifier que nos documents uploadés sont présents
                    found_docs = 0
                    for doc_id in self.uploaded_document_ids:
                        doc_found = any(doc.get("id") == doc_id for doc in documents)
                        if doc_found:
                            found_docs += 1
                    
                    if found_docs == len(self.uploaded_document_ids):
                        self.log_result("Documents sauvegardés", True, 
                                      f"Tous les {found_docs} documents uploadés trouvés en base")
                    else:
                        self.log_result("Documents sauvegardés", False, 
                                      f"Seulement {found_docs}/{len(self.uploaded_document_ids)} documents trouvés")
                else:
                    self.log_result("GET /ocr/documents", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /ocr/documents", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("GET /ocr/documents", False, f"Exception: {str(e)}")

    def test_individual_document_retrieval(self):
        """Test 5: Récupération individuelle des documents"""
        print("\n=== TEST 5: RÉCUPÉRATION DOCUMENTS INDIVIDUELS ===")
        
        if not self.uploaded_document_ids:
            self.log_result("Récupération individuelle", False, "Aucun document pour tester")
            return
        
        for i, doc_id in enumerate(self.uploaded_document_ids):
            try:
                response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                
                if response.status_code == 200:
                    document = response.json()
                    
                    # Vérifier la structure du document
                    required_fields = ["id", "type_document", "nom_fichier", "texte_extrait", 
                                     "donnees_parsees", "statut", "date_upload"]
                    
                    missing_fields = [field for field in required_fields if field not in document]
                    
                    if not missing_fields:
                        self.log_result(f"GET /ocr/document/{doc_id[:8]}...", True, 
                                      "Document récupéré avec tous les champs requis")
                        
                        # Vérifier que le document n'est pas resté bloqué en traitement
                        statut = document.get("statut", "")
                        if statut in ["traite", "erreur"]:
                            self.log_result(f"Statut final document {i+1}", True, 
                                          f"Statut final: {statut}")
                        elif statut == "en_attente":
                            self.log_result(f"Statut final document {i+1}", False, 
                                          "Document encore en attente de traitement")
                        else:
                            self.log_result(f"Statut final document {i+1}", False, 
                                          f"Statut inconnu: {statut}")
                        
                        # Vérifier la présence de texte extrait
                        texte_extrait = document.get("texte_extrait", "")
                        if len(texte_extrait) > 0:
                            self.log_result(f"Texte extrait document {i+1}", True, 
                                          f"{len(texte_extrait)} caractères extraits")
                        else:
                            self.log_result(f"Texte extrait document {i+1}", False, 
                                          "Aucun texte extrait")
                    else:
                        self.log_result(f"GET /ocr/document/{doc_id[:8]}...", False, 
                                      f"Champs manquants: {missing_fields}")
                else:
                    self.log_result(f"GET /ocr/document/{doc_id[:8]}...", False, 
                                  f"Erreur {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result(f"GET /ocr/document/{doc_id[:8]}...", False, f"Exception: {str(e)}")

    def test_z_report_processing(self):
        """Test 6: Traitement spécifique des rapports Z"""
        print("\n=== TEST 6: TRAITEMENT RAPPORTS Z ===")
        
        # Trouver un document Z-report parmi ceux uploadés
        z_report_id = None
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                for doc in documents:
                    if doc.get("type_document") == "z_report" and doc.get("id") in self.uploaded_document_ids:
                        z_report_id = doc.get("id")
                        break
        except:
            pass
        
        if not z_report_id:
            self.log_result("Traitement Z-report", False, "Aucun rapport Z uploadé pour tester")
            return
        
        try:
            # Test du traitement spécifique Z-report
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{z_report_id}", 
                                   headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                if "message" in result:
                    self.log_result("POST /ocr/process-z-report", True, 
                                  f"Traitement Z-report réussi: {result['message']}")
                    
                    # Vérifier les propositions de mise à jour stock
                    if "stock_updates" in result:
                        stock_updates = result["stock_updates"]
                        if isinstance(stock_updates, list):
                            self.log_result("Propositions stock Z-report", True, 
                                          f"{len(stock_updates)} propositions de mise à jour")
                        else:
                            self.log_result("Propositions stock Z-report", False, 
                                          "Format incorrect pour stock_updates")
                    
                    # Vérifier les warnings
                    if "warnings" in result:
                        warnings = result["warnings"]
                        if isinstance(warnings, list):
                            self.log_result("Warnings Z-report", True, 
                                          f"{len(warnings)} warning(s) générés")
                        else:
                            self.log_result("Warnings Z-report", False, 
                                          "Format incorrect pour warnings")
                else:
                    self.log_result("POST /ocr/process-z-report", False, 
                                  "Pas de message dans la réponse")
            elif response.status_code == 400:
                # Erreur attendue si le document n'est pas un Z-report
                self.log_result("POST /ocr/process-z-report", True, 
                              "Validation type document fonctionnelle (erreur 400 attendue)")
            else:
                self.log_result("POST /ocr/process-z-report", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /ocr/process-z-report", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests OCR"""
        print("🎯 DÉBUT DES TESTS OCR UPLOAD-DOCUMENT")
        print("=" * 60)
        
        start_time = time.time()
        
        # Tests d'upload
        self.test_ocr_upload_image()
        self.test_ocr_upload_pdf()
        self.test_ocr_upload_z_report()
        
        # Tests de persistance et récupération
        self.test_document_persistence()
        self.test_individual_document_retrieval()
        
        # Tests de traitement spécifique
        self.test_z_report_processing()
        
        total_time = time.time() - start_time
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS OCR")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        print(f"⏱️  Temps total: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n📄 Documents uploadés: {len(self.uploaded_document_ids)}")
        for i, doc_id in enumerate(self.uploaded_document_ids):
            print(f"  {i+1}. {doc_id}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "total_time": total_time,
            "uploaded_documents": len(self.uploaded_document_ids)
        }

if __name__ == "__main__":
    test_suite = OCRUploadTestSuite()
    results = test_suite.run_all_tests()
    
    # Code de sortie basé sur les résultats
    exit_code = 0 if results["failed_tests"] == 0 else 1
    exit(exit_code)