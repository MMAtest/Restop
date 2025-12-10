#!/usr/bin/env python3
"""
Test spécifique des endpoints OCR backend pour validation du preview flow
Tests demandés: GET /api/ocr/documents, GET /api/ocr/document/{id}, POST /api/ocr/upload-document, 
POST /api/ocr/process-z-report/{document_id}, DELETE /api/ocr/document/{document_id}
"""

import requests
import json
import base64
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os

# Configuration
BASE_URL = "https://receipt-scanner-64.preview.emergentagent.com/api"
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
    
    def create_test_image(self, text_content="Test Z-Report\nSupions persillade: 3\nTotal: 45.50€"):
        """Crée une image de test avec du texte pour OCR"""
        # Créer une image simple avec du texte
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Essayer d'utiliser une police par défaut
            font = ImageFont.load_default()
        except:
            font = None
        
        # Écrire le texte
        lines = text_content.split('\n')
        y_position = 50
        for line in lines:
            draw.text((20, y_position), line, fill='black', font=font)
            y_position += 30
        
        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def create_test_pdf_content(self):
        """Crée un contenu PDF simple pour les tests"""
        # Contenu PDF minimal simulé (en réalité, on utiliserait une vraie librairie PDF)
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        return pdf_content
    
    def test_ocr_upload_document_image(self):
        """Test POST /api/ocr/upload-document avec image"""
        print("\n=== TEST POST /api/ocr/upload-document (IMAGE) ===")
        
        try:
            # Créer une image de test
            image_content = self.create_test_image("Z-Report Test\nSupions persillade: 4\nLinguine palourdes: 2\nTotal CA: 78.50€")
            
            files = {
                'file': ('test_z_report.png', image_content, 'image/png')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.created_document_ids.append(document_id)
                    self.log_result("POST /ocr/upload-document (image)", True, 
                                  f"Document image uploadé avec ID: {document_id}")
                    
                    # Vérifier les champs requis dans la réponse
                    required_fields = ["document_id", "type_document", "texte_extrait", "donnees_parsees", "file_type"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        self.log_result("Structure réponse upload image", True, "Tous les champs requis présents")
                        
                        # Vérifier que file_type est correct
                        if result.get("file_type") == "image":
                            self.log_result("File type image", True, "file_type correctement défini à 'image'")
                        else:
                            self.log_result("File type image", False, f"file_type incorrect: {result.get('file_type')}")
                        
                        # Vérifier que donnees_parsees a une structure z_report
                        donnees_parsees = result.get("donnees_parsees", {})
                        if isinstance(donnees_parsees, dict) and "items_by_category" in donnees_parsees:
                            self.log_result("Structure donnees_parsees z_report", True, "Structure z_report détectée")
                        else:
                            self.log_result("Structure donnees_parsees z_report", False, "Structure z_report manquante")
                    else:
                        self.log_result("Structure réponse upload image", False, f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("POST /ocr/upload-document (image)", False, "document_id manquant dans la réponse")
            else:
                self.log_result("POST /ocr/upload-document (image)", False, 
                              f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("POST /ocr/upload-document (image)", False, "Exception", str(e))
    
    def test_ocr_upload_document_pdf(self):
        """Test POST /api/ocr/upload-document avec PDF"""
        print("\n=== TEST POST /api/ocr/upload-document (PDF) ===")
        
        try:
            # Créer un PDF de test simple
            pdf_content = self.create_test_pdf_content()
            
            files = {
                'file': ('test_facture.pdf', pdf_content, 'application/pdf')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.created_document_ids.append(document_id)
                    self.log_result("POST /ocr/upload-document (PDF)", True, 
                                  f"Document PDF uploadé avec ID: {document_id}")
                    
                    # Vérifier que file_type est correct pour PDF
                    if result.get("file_type") == "pdf":
                        self.log_result("File type PDF", True, "file_type correctement défini à 'pdf'")
                    else:
                        self.log_result("File type PDF", False, f"file_type incorrect: {result.get('file_type')}")
                    
                    # Vérifier que donnees_parsees a une structure facture_fournisseur
                    donnees_parsees = result.get("donnees_parsees", {})
                    if isinstance(donnees_parsees, dict):
                        self.log_result("Structure donnees_parsees facture", True, "Structure facture détectée")
                    else:
                        self.log_result("Structure donnees_parsees facture", False, "Structure facture manquante")
                else:
                    self.log_result("POST /ocr/upload-document (PDF)", False, "document_id manquant dans la réponse")
            else:
                self.log_result("POST /ocr/upload-document (PDF)", False, 
                              f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("POST /ocr/upload-document (PDF)", False, "Exception", str(e))
    
    def test_ocr_get_documents_list(self):
        """Test GET /api/ocr/documents - doit retourner liste avec image_base64 null"""
        print("\n=== TEST GET /api/ocr/documents ===")
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code == 200:
                documents = response.json()
                
                if isinstance(documents, list):
                    self.log_result("GET /ocr/documents", True, f"{len(documents)} document(s) récupéré(s)")
                    
                    if len(documents) > 0:
                        # Vérifier que image_base64 est null dans la liste
                        first_doc = documents[0]
                        required_fields = ["id", "type_document", "nom_fichier", "statut", "date_upload", "file_type"]
                        
                        missing_fields = [field for field in required_fields if field not in first_doc]
                        if not missing_fields:
                            self.log_result("Structure document liste", True, "Tous les champs requis présents")
                        else:
                            self.log_result("Structure document liste", False, f"Champs manquants: {missing_fields}")
                        
                        # CRITIQUE: Vérifier que image_base64 est null en mode liste
                        if first_doc.get("image_base64") is None:
                            self.log_result("image_base64 null en liste", True, "image_base64 correctement null en mode liste")
                        else:
                            self.log_result("image_base64 null en liste", False, "image_base64 ne devrait pas être présent en mode liste")
                    else:
                        self.log_result("Documents disponibles", False, "Aucun document trouvé pour les tests")
                else:
                    self.log_result("GET /ocr/documents", False, "Format de réponse incorrect (pas une liste)")
            else:
                self.log_result("GET /ocr/documents", False, f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("GET /ocr/documents", False, "Exception", str(e))
    
    def test_ocr_get_document_by_id(self):
        """Test GET /api/ocr/document/{id} - doit retourner document complet avec image_base64"""
        print("\n=== TEST GET /api/ocr/document/{id} ===")
        
        if not self.created_document_ids:
            self.log_result("GET /ocr/document/{id}", False, "Aucun document créé pour le test")
            return
        
        document_id = self.created_document_ids[0]
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            
            if response.status_code == 200:
                document = response.json()
                
                # Vérifier tous les champs requis pour un document complet
                required_fields = [
                    "id", "type_document", "nom_fichier", "image_base64", 
                    "texte_extrait", "donnees_parsees", "statut", 
                    "date_upload", "date_traitement", "file_type"
                ]
                
                missing_fields = [field for field in required_fields if field not in document]
                if not missing_fields:
                    self.log_result("GET /ocr/document/{id}", True, "Document complet récupéré avec tous les champs")
                    
                    # CRITIQUE: Vérifier que image_base64 est présent et non null
                    image_base64 = document.get("image_base64")
                    if image_base64 is not None:
                        if isinstance(image_base64, str) and len(image_base64) > 0:
                            # Vérifier si c'est un data URI valide
                            if image_base64.startswith("data:"):
                                self.log_result("image_base64 présent", True, "image_base64 présent comme data URI")
                            else:
                                self.log_result("image_base64 format", True, "image_base64 présent (format base64)")
                        else:
                            self.log_result("image_base64 présent", False, "image_base64 vide")
                    else:
                        self.log_result("image_base64 présent", False, "image_base64 manquant dans le document individuel")
                    
                    # Vérifier le type de fichier
                    file_type = document.get("file_type")
                    if file_type in ["image", "pdf"]:
                        self.log_result("file_type valide", True, f"file_type: {file_type}")
                    else:
                        self.log_result("file_type valide", False, f"file_type invalide: {file_type}")
                    
                    # Vérifier la structure des donnees_parsees
                    donnees_parsees = document.get("donnees_parsees")
                    if isinstance(donnees_parsees, dict) and len(donnees_parsees) > 0:
                        self.log_result("donnees_parsees structure", True, "donnees_parsees présentes et structurées")
                    else:
                        self.log_result("donnees_parsees structure", False, "donnees_parsees manquantes ou vides")
                else:
                    self.log_result("GET /ocr/document/{id}", False, f"Champs manquants: {missing_fields}")
            elif response.status_code == 404:
                self.log_result("GET /ocr/document/{id}", False, "Document non trouvé (404)")
            else:
                self.log_result("GET /ocr/document/{id}", False, f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("GET /ocr/document/{id}", False, "Exception", str(e))
    
    def test_ocr_process_z_report(self):
        """Test POST /api/ocr/process-z-report/{document_id} - seulement pour z_report"""
        print("\n=== TEST POST /api/ocr/process-z-report/{document_id} ===")
        
        # Trouver un document z_report parmi ceux créés
        z_report_id = None
        for doc_id in self.created_document_ids:
            try:
                doc_response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                if doc_response.status_code == 200:
                    doc = doc_response.json()
                    if doc.get("type_document") == "z_report":
                        z_report_id = doc_id
                        break
            except:
                continue
        
        if not z_report_id:
            self.log_result("POST /ocr/process-z-report/{id}", False, "Aucun document z_report disponible pour le test")
            return
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{z_report_id}", headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier les champs requis dans la réponse
                required_fields = ["message", "stock_updates", "warnings"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_result("POST /ocr/process-z-report/{id}", True, "Z-report traité avec succès")
                    
                    # Vérifier la structure des stock_updates
                    stock_updates = result.get("stock_updates", [])
                    if isinstance(stock_updates, list):
                        self.log_result("stock_updates structure", True, f"{len(stock_updates)} mise(s) à jour de stock")
                    else:
                        self.log_result("stock_updates structure", False, "stock_updates n'est pas une liste")
                    
                    # Vérifier la structure des warnings
                    warnings = result.get("warnings", [])
                    if isinstance(warnings, list):
                        self.log_result("warnings structure", True, f"{len(warnings)} avertissement(s)")
                    else:
                        self.log_result("warnings structure", False, "warnings n'est pas une liste")
                else:
                    self.log_result("POST /ocr/process-z-report/{id}", False, f"Champs manquants: {missing_fields}")
            elif response.status_code == 400:
                # Vérifier que l'erreur est appropriée pour un non-z_report
                self.log_result("POST /ocr/process-z-report/{id}", True, "Erreur 400 appropriée pour document non z_report")
            else:
                self.log_result("POST /ocr/process-z-report/{id}", False, f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("POST /ocr/process-z-report/{id}", False, "Exception", str(e))
    
    def test_ocr_process_z_report_wrong_type(self):
        """Test POST /api/ocr/process-z-report/{document_id} avec document non z_report (doit échouer)"""
        print("\n=== TEST POST /api/ocr/process-z-report/{id} (WRONG TYPE) ===")
        
        # Trouver un document qui n'est PAS z_report
        non_z_report_id = None
        for doc_id in self.created_document_ids:
            try:
                doc_response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                if doc_response.status_code == 200:
                    doc = doc_response.json()
                    if doc.get("type_document") != "z_report":
                        non_z_report_id = doc_id
                        break
            except:
                continue
        
        if not non_z_report_id:
            self.log_result("POST /ocr/process-z-report/{id} (wrong type)", False, "Aucun document non-z_report disponible")
            return
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{non_z_report_id}", headers=HEADERS)
            
            if response.status_code == 400:
                self.log_result("POST /ocr/process-z-report/{id} (wrong type)", True, 
                              "Erreur 400 correcte pour document non z_report")
            elif response.status_code == 404:
                self.log_result("POST /ocr/process-z-report/{id} (wrong type)", True, 
                              "Erreur 404 correcte pour document inexistant")
            else:
                self.log_result("POST /ocr/process-z-report/{id} (wrong type)", False, 
                              f"Erreur inattendue {response.status_code} (devrait être 400)")
        except Exception as e:
            self.log_result("POST /ocr/process-z-report/{id} (wrong type)", False, "Exception", str(e))
    
    def test_ocr_delete_document(self):
        """Test DELETE /api/ocr/document/{document_id}"""
        print("\n=== TEST DELETE /api/ocr/document/{document_id} ===")
        
        if not self.created_document_ids:
            self.log_result("DELETE /ocr/document/{id}", False, "Aucun document à supprimer")
            return
        
        # Prendre le dernier document créé pour le supprimer
        document_id = self.created_document_ids[-1]
        
        try:
            response = requests.delete(f"{BASE_URL}/ocr/document/{document_id}")
            
            if response.status_code == 200:
                result = response.json()
                if "supprimé" in result.get("message", "").lower():
                    self.log_result("DELETE /ocr/document/{id}", True, "Document supprimé avec succès")
                    
                    # Vérifier que le document n'existe plus
                    get_response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
                    if get_response.status_code == 404:
                        self.log_result("Validation suppression", True, "Document bien supprimé (404 lors de GET)")
                        # Retirer de la liste des documents créés
                        self.created_document_ids.remove(document_id)
                    else:
                        self.log_result("Validation suppression", False, "Document encore accessible après suppression")
                else:
                    self.log_result("DELETE /ocr/document/{id}", False, f"Message de suppression inattendu: {result.get('message')}")
            elif response.status_code == 404:
                self.log_result("DELETE /ocr/document/{id}", True, "Erreur 404 correcte pour document inexistant")
            else:
                self.log_result("DELETE /ocr/document/{id}", False, f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("DELETE /ocr/document/{id}", False, "Exception", str(e))
    
    def test_ocr_delete_nonexistent_document(self):
        """Test DELETE /api/ocr/document/{document_id} avec ID inexistant"""
        print("\n=== TEST DELETE /api/ocr/document/{id} (INEXISTANT) ===")
        
        fake_id = "nonexistent-document-id-12345"
        
        try:
            response = requests.delete(f"{BASE_URL}/ocr/document/{fake_id}")
            
            if response.status_code == 404:
                self.log_result("DELETE /ocr/document/{id} (inexistant)", True, "Erreur 404 correcte pour document inexistant")
            else:
                self.log_result("DELETE /ocr/document/{id} (inexistant)", False, 
                              f"Erreur inattendue {response.status_code} (devrait être 404)")
        except Exception as e:
            self.log_result("DELETE /ocr/document/{id} (inexistant)", False, "Exception", str(e))
    
    def run_all_tests(self):
        """Exécute tous les tests OCR dans l'ordre approprié"""
        print("🔍 DÉBUT DES TESTS OCR BACKEND ENDPOINTS")
        print("=" * 60)
        
        # Tests d'upload (créent des documents)
        self.test_ocr_upload_document_image()
        self.test_ocr_upload_document_pdf()
        
        # Tests de récupération
        self.test_ocr_get_documents_list()
        self.test_ocr_get_document_by_id()
        
        # Tests de traitement
        self.test_ocr_process_z_report()
        self.test_ocr_process_z_report_wrong_type()
        
        # Tests de suppression
        self.test_ocr_delete_nonexistent_document()
        self.test_ocr_delete_document()
        
        # Résumé des résultats
        self.print_summary()
    
    def print_summary(self):
        """Affiche un résumé des résultats de tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS OCR BACKEND")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_suite = OCRTestSuite()
    test_suite.run_all_tests()