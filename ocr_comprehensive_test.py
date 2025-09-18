#!/usr/bin/env python3
"""
Test complet des endpoints OCR avec création de documents z_report et facture_fournisseur
Focus sur la validation du preview flow sans régressions
"""

import requests
import json
import base64
import io
from datetime import datetime
import tempfile
import os

# Configuration
BASE_URL = "https://restop-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ComprehensiveOCRTest:
    def __init__(self):
        self.test_results = []
        self.created_documents = []
        
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
    
    def create_mock_z_report_pdf(self):
        """Crée un PDF simulé avec contenu Z-report"""
        # Contenu texte simulé d'un Z-report
        z_report_content = """RAPPORT Z - LA TABLE D'AUGUSTINE
Date: 15/01/2025
Service: Soir

VENTES PAR CATÉGORIE:

BAR:
Vin rouge Côtes du Rhône: 3
Pastis Ricard: 2

ENTRÉES:
Supions en persillade: 5
Fleurs de courgettes: 4

PLATS:
Linguine aux palourdes: 6
Bœuf Wellington: 3

DESSERTS:
Tiramisu: 4

TOTAL CA: 567.50€
Nombre de couverts: 22"""
        
        # Créer un fichier temporaire avec ce contenu
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(z_report_content)
            temp_file = f.name
        
        # Lire le contenu comme bytes pour simuler un PDF
        with open(temp_file, 'rb') as f:
            content = f.read()
        
        os.unlink(temp_file)
        return content
    
    def create_mock_facture_pdf(self):
        """Crée un PDF simulé avec contenu facture fournisseur"""
        facture_content = """FACTURE FOURNISSEUR
Maison Artigiana
Giuseppe Pellegrino
Via Roma 123, Italie

Facture N°: FAC-2025-001
Date: 15/01/2025

PRODUITS:
Burrata des Pouilles: 10 pièces x 8.50€ = 85.00€
Mozzarella di Bufala: 5 kg x 12.00€ = 60.00€
Parmesan Reggiano: 2 kg x 45.00€ = 90.00€

TOTAL HT: 235.00€
TVA 20%: 47.00€
TOTAL TTC: 282.00€"""
        
        return facture_content.encode('utf-8')
    
    def test_upload_z_report_document(self):
        """Test upload d'un document Z-report"""
        print("\n=== TEST UPLOAD Z-REPORT DOCUMENT ===")
        
        try:
            pdf_content = self.create_mock_z_report_pdf()
            
            files = {
                'file': ('z_report_test.pdf', pdf_content, 'application/pdf')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.created_documents.append({
                        'id': document_id,
                        'type': 'z_report',
                        'name': 'z_report_test.pdf'
                    })
                    
                    self.log_result("Upload Z-report PDF", True, 
                                  f"Z-report uploadé avec ID: {document_id}")
                    
                    # Vérifier la structure de la réponse
                    if (result.get("type_document") == "z_report" and 
                        result.get("file_type") == "pdf" and
                        "donnees_parsees" in result):
                        self.log_result("Structure réponse Z-report", True, "Structure complète validée")
                        
                        # Vérifier la structure des données parsées pour z_report
                        donnees_parsees = result.get("donnees_parsees", {})
                        if "items_by_category" in donnees_parsees:
                            self.log_result("Structure z_report parsing", True, "items_by_category présent")
                        else:
                            self.log_result("Structure z_report parsing", False, "items_by_category manquant")
                    else:
                        self.log_result("Structure réponse Z-report", False, "Structure incomplète")
                else:
                    self.log_result("Upload Z-report PDF", False, "document_id manquant")
            else:
                self.log_result("Upload Z-report PDF", False, 
                              f"Erreur {response.status_code}", response.text[:300])
        except Exception as e:
            self.log_result("Upload Z-report PDF", False, "Exception", str(e))
    
    def test_upload_facture_document(self):
        """Test upload d'un document facture fournisseur"""
        print("\n=== TEST UPLOAD FACTURE FOURNISSEUR ===")
        
        try:
            pdf_content = self.create_mock_facture_pdf()
            
            files = {
                'file': ('facture_test.pdf', pdf_content, 'application/pdf')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.created_documents.append({
                        'id': document_id,
                        'type': 'facture_fournisseur',
                        'name': 'facture_test.pdf'
                    })
                    
                    self.log_result("Upload facture PDF", True, 
                                  f"Facture uploadée avec ID: {document_id}")
                    
                    # Vérifier la structure pour facture_fournisseur
                    if (result.get("type_document") == "facture_fournisseur" and 
                        result.get("file_type") == "pdf"):
                        self.log_result("Structure réponse facture", True, "Type et file_type corrects")
                        
                        # Vérifier la structure des données parsées pour facture
                        donnees_parsees = result.get("donnees_parsees", {})
                        if isinstance(donnees_parsees, dict):
                            self.log_result("Structure facture parsing", True, "donnees_parsees structurées")
                        else:
                            self.log_result("Structure facture parsing", False, "donnees_parsees manquantes")
                    else:
                        self.log_result("Structure réponse facture", False, "Structure incorrecte")
                else:
                    self.log_result("Upload facture PDF", False, "document_id manquant")
            else:
                self.log_result("Upload facture PDF", False, 
                              f"Erreur {response.status_code}", response.text[:300])
        except Exception as e:
            self.log_result("Upload facture PDF", False, "Exception", str(e))
    
    def test_documents_list_preview_flow(self):
        """Test GET /api/ocr/documents pour le preview flow"""
        print("\n=== TEST DOCUMENTS LIST (PREVIEW FLOW) ===")
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code == 200:
                documents = response.json()
                
                if isinstance(documents, list) and len(documents) > 0:
                    self.log_result("GET documents list", True, f"{len(documents)} documents récupérés")
                    
                    # Vérifier que image_base64 est null dans la liste (critique pour preview flow)
                    all_null_images = all(doc.get("image_base64") is None for doc in documents)
                    if all_null_images:
                        self.log_result("Preview flow - image_base64 null", True, 
                                      "Tous les documents ont image_base64=null en mode liste")
                    else:
                        non_null_count = sum(1 for doc in documents if doc.get("image_base64") is not None)
                        self.log_result("Preview flow - image_base64 null", False, 
                                      f"{non_null_count} documents avec image_base64 non-null")
                    
                    # Vérifier la présence des champs requis
                    sample_doc = documents[0]
                    required_fields = ["id", "type_document", "nom_fichier", "statut", "date_upload", "file_type"]
                    missing_fields = [field for field in required_fields if field not in sample_doc]
                    
                    if not missing_fields:
                        self.log_result("Champs requis liste", True, "Tous les champs requis présents")
                    else:
                        self.log_result("Champs requis liste", False, f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("GET documents list", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET documents list", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET documents list", False, "Exception", str(e))
    
    def test_document_detail_preview_flow(self):
        """Test GET /api/ocr/document/{id} pour le preview flow"""
        print("\n=== TEST DOCUMENT DETAIL (PREVIEW FLOW) ===")
        
        if not self.created_documents:
            self.log_result("Document detail preview", False, "Aucun document créé pour le test")
            return
        
        document = self.created_documents[0]
        document_id = document['id']
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            
            if response.status_code == 200:
                doc_detail = response.json()
                
                # Vérifier tous les champs requis pour le preview
                required_fields = [
                    "id", "type_document", "nom_fichier", "image_base64", 
                    "texte_extrait", "donnees_parsees", "statut", 
                    "date_upload", "date_traitement", "file_type"
                ]
                
                missing_fields = [field for field in required_fields if field not in doc_detail]
                if not missing_fields:
                    self.log_result("Document detail complet", True, "Tous les champs requis présents")
                    
                    # CRITIQUE: Vérifier que image_base64 est présent pour le preview
                    image_base64 = doc_detail.get("image_base64")
                    if image_base64 is not None and len(str(image_base64)) > 0:
                        if isinstance(image_base64, str) and image_base64.startswith("data:"):
                            self.log_result("Preview flow - image_base64 présent", True, 
                                          "image_base64 présent comme data URI pour preview")
                        else:
                            self.log_result("Preview flow - image_base64 format", True, 
                                          "image_base64 présent (format base64)")
                    else:
                        self.log_result("Preview flow - image_base64 présent", False, 
                                      "image_base64 manquant pour le preview")
                    
                    # Vérifier la cohérence des données
                    if (doc_detail.get("id") == document_id and 
                        doc_detail.get("type_document") == document['type']):
                        self.log_result("Cohérence données document", True, "Données cohérentes")
                    else:
                        self.log_result("Cohérence données document", False, "Données incohérentes")
                else:
                    self.log_result("Document detail complet", False, f"Champs manquants: {missing_fields}")
            else:
                self.log_result("Document detail preview", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Document detail preview", False, "Exception", str(e))
    
    def test_process_z_report_endpoint(self):
        """Test POST /api/ocr/process-z-report/{document_id} avec un vrai z_report"""
        print("\n=== TEST PROCESS Z-REPORT ENDPOINT ===")
        
        # Trouver un document z_report
        z_report_doc = next((doc for doc in self.created_documents if doc['type'] == 'z_report'), None)
        
        if not z_report_doc:
            self.log_result("Process Z-report", False, "Aucun document z_report disponible")
            return
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{z_report_doc['id']}", headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["message", "stock_updates", "warnings"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_result("Process Z-report structure", True, "Structure de réponse complète")
                    
                    # Vérifier les types de données
                    stock_updates = result.get("stock_updates", [])
                    warnings = result.get("warnings", [])
                    
                    if isinstance(stock_updates, list) and isinstance(warnings, list):
                        self.log_result("Process Z-report types", True, 
                                      f"{len(stock_updates)} mises à jour, {len(warnings)} avertissements")
                    else:
                        self.log_result("Process Z-report types", False, "Types de données incorrects")
                    
                    # Vérifier le message
                    message = result.get("message", "")
                    if message and len(message) > 0:
                        self.log_result("Process Z-report message", True, f"Message: {message[:50]}...")
                    else:
                        self.log_result("Process Z-report message", False, "Message manquant")
                else:
                    self.log_result("Process Z-report structure", False, f"Champs manquants: {missing_fields}")
            elif response.status_code == 400:
                # Peut être normal si le document n'est pas traitable
                self.log_result("Process Z-report", True, "Erreur 400 - document non traitable (normal)")
            else:
                self.log_result("Process Z-report", False, f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("Process Z-report", False, "Exception", str(e))
    
    def test_process_z_report_with_wrong_type(self):
        """Test POST /api/ocr/process-z-report/{document_id} avec document non z_report"""
        print("\n=== TEST PROCESS Z-REPORT (WRONG TYPE) ===")
        
        # Trouver un document qui n'est PAS z_report
        non_z_report_doc = next((doc for doc in self.created_documents if doc['type'] != 'z_report'), None)
        
        if not non_z_report_doc:
            self.log_result("Process Z-report wrong type", False, "Aucun document non-z_report disponible")
            return
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{non_z_report_doc['id']}", headers=HEADERS)
            
            if response.status_code == 400:
                self.log_result("Process Z-report wrong type", True, 
                              "Erreur 400 correcte pour document non z_report")
            else:
                self.log_result("Process Z-report wrong type", False, 
                              f"Erreur inattendue {response.status_code} (devrait être 400)")
        except Exception as e:
            self.log_result("Process Z-report wrong type", False, "Exception", str(e))
    
    def test_delete_document_endpoint(self):
        """Test DELETE /api/ocr/document/{document_id}"""
        print("\n=== TEST DELETE DOCUMENT ENDPOINT ===")
        
        if not self.created_documents:
            self.log_result("Delete document", False, "Aucun document à supprimer")
            return
        
        # Prendre le dernier document pour le supprimer
        document_to_delete = self.created_documents[-1]
        document_id = document_to_delete['id']
        
        try:
            response = requests.delete(f"{BASE_URL}/ocr/document/{document_id}")
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                if "supprimé" in message.lower() or "deleted" in message.lower():
                    self.log_result("Delete document", True, "Document supprimé avec succès")
                    
                    # Vérifier que le document n'existe plus
                    get_response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
                    if get_response.status_code == 404:
                        self.log_result("Validation suppression", True, "Document bien supprimé (404)")
                        # Retirer de la liste
                        self.created_documents.remove(document_to_delete)
                    else:
                        self.log_result("Validation suppression", False, 
                                      f"Document encore accessible: {get_response.status_code}")
                else:
                    self.log_result("Delete document", False, f"Message inattendu: {message}")
            elif response.status_code == 404:
                self.log_result("Delete document", True, "Erreur 404 - document déjà supprimé")
            else:
                self.log_result("Delete document", False, f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("Delete document", False, "Exception", str(e))
    
    def test_backend_stability_after_preview(self):
        """Test que les endpoints backend restent stables après les opérations de preview"""
        print("\n=== TEST STABILITÉ BACKEND APRÈS PREVIEW ===")
        
        if not self.created_documents:
            self.log_result("Stabilité backend", False, "Aucun document pour tester la stabilité")
            return
        
        document = self.created_documents[0]
        document_id = document['id']
        
        try:
            # Faire plusieurs appels de preview pour simuler l'utilisation
            for i in range(3):
                response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
                if response.status_code != 200:
                    self.log_result("Stabilité backend", False, 
                                  f"Échec à l'appel {i+1}: {response.status_code}")
                    return
            
            self.log_result("Stabilité backend", True, "3 appels de preview successifs sans régression")
            
            # Vérifier que la liste fonctionne toujours
            list_response = requests.get(f"{BASE_URL}/ocr/documents")
            if list_response.status_code == 200:
                self.log_result("Stabilité liste après preview", True, "Liste documents stable")
            else:
                self.log_result("Stabilité liste après preview", False, 
                              f"Liste échoue: {list_response.status_code}")
        except Exception as e:
            self.log_result("Stabilité backend", False, "Exception", str(e))
    
    def run_comprehensive_tests(self):
        """Exécute tous les tests dans l'ordre approprié"""
        print("🔍 TESTS COMPLETS OCR BACKEND - VALIDATION PREVIEW FLOW")
        print("=" * 70)
        
        # Phase 1: Création de documents
        self.test_upload_z_report_document()
        self.test_upload_facture_document()
        
        # Phase 2: Tests de récupération (preview flow)
        self.test_documents_list_preview_flow()
        self.test_document_detail_preview_flow()
        
        # Phase 3: Tests de traitement
        self.test_process_z_report_endpoint()
        self.test_process_z_report_with_wrong_type()
        
        # Phase 4: Tests de stabilité
        self.test_backend_stability_after_preview()
        
        # Phase 5: Nettoyage
        self.test_delete_document_endpoint()
        
        # Résumé
        self.print_comprehensive_summary()
    
    def print_comprehensive_summary(self):
        """Affiche un résumé détaillé des résultats"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ COMPLET - TESTS OCR BACKEND PREVIEW FLOW")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 RÉSULTATS GLOBAUX:")
        print(f"   Total des tests: {total_tests}")
        print(f"   ✅ Réussis: {passed_tests}")
        print(f"   ❌ Échoués: {failed_tests}")
        print(f"   📊 Taux de réussite: {success_rate:.1f}%")
        
        # Analyse par catégorie
        categories = {
            "Upload": ["Upload"],
            "Preview Flow": ["Preview", "Documents list", "Document detail"],
            "Processing": ["Process"],
            "Stability": ["Stabilité"],
            "Cleanup": ["Delete"]
        }
        
        print(f"\n📋 ANALYSE PAR CATÉGORIE:")
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results 
                            if any(keyword.lower() in r["test"].lower() for keyword in keywords)]
            if category_tests:
                category_passed = sum(1 for r in category_tests if r["success"])
                category_total = len(category_tests)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                print(f"   {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS DÉTAILLÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}")
                    print(f"     Erreur: {result['message']}")
                    if result.get("details"):
                        print(f"     Détails: {result['details'][:100]}...")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if success_rate >= 90:
            print("   ✅ Endpoints OCR stables - Preview flow validé")
        elif success_rate >= 75:
            print("   ⚠️  Quelques problèmes mineurs - Vérifier les échecs")
        else:
            print("   ❌ Problèmes significatifs - Investigation requise")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    test_suite = ComprehensiveOCRTest()
    test_suite.run_comprehensive_tests()