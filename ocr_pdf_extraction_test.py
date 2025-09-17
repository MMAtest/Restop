#!/usr/bin/env python3
"""
Test spécifique pour la complétude de l'extraction OCR PDF après améliorations
Focus: Vérifier que texte_extrait est plus complet et contient les lignes de catégories multiples
"""

import requests
import json
import io
import time
import base64
from datetime import datetime

# Configuration
BASE_URL = "https://restop-stock.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRPDFExtractionTest:
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

    def create_multi_line_z_report_pdf_content(self):
        """Créer un contenu PDF simulé avec plusieurs catégories pour test"""
        # Simuler un contenu PDF riche avec plusieurs catégories
        pdf_content = """
RAPPORT Z - LA TABLE D'AUGUSTINE
Date: 15/12/2024
Service: Soir

CA par catégories:

=== BAR ===
(x3) Vin rouge Côtes du Rhône        €8.50
(x2) Cocktail Spritz                  €12.00
(x1) Whisky single malt               €15.00

=== ENTRÉES ===
(x4) Supions en persillade de Mamie   €24.00
(x2) Fleurs de courgettes de Mamet    €21.00
(x3) Burrata di Bufala                €18.50

=== PLATS ===
(x2) Linguine aux palourdes           €28.00
(x1) Rigatoni à la truffe Forcalquier €31.00
(x1) Bœuf Wellington à la truffe      €56.00

=== DESSERTS ===
(x2) Tiramisu maison                  €9.50
(x1) Tarte citron meringuée           €8.00

TOTAL CA: 456.50€
Nombre de couverts: 12
        """.strip()
        
        return pdf_content.encode('utf-8')

    def test_pdf_upload_extraction_completeness(self):
        """Test principal: Upload PDF et vérification complétude extraction"""
        print("\n=== TEST COMPLÉTUDE EXTRACTION PDF OCR ===")
        
        try:
            # Créer un PDF simulé avec contenu multi-catégories
            pdf_content = self.create_multi_line_z_report_pdf_content()
            
            # Upload du document PDF
            files = {
                'file': ('z_report_multi_categories.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            data = {
                'type_document': 'z_report'
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            upload_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                document_id = response_data.get('document_id')
                texte_extrait = response_data.get('texte_extrait', '')
                
                self.created_document_ids.append(document_id)
                
                # Vérifications de complétude
                completeness_checks = {
                    "Longueur texte extrait": len(texte_extrait) > 200,  # Minimum attendu
                    "Contient 'CA par catégories'": 'CA par catégories' in texte_extrait or 'ca par catégories' in texte_extrait.lower(),
                    "Contient section BAR": 'BAR' in texte_extrait or 'bar' in texte_extrait.lower(),
                    "Contient section ENTRÉES": 'ENTRÉES' in texte_extrait or 'entrées' in texte_extrait.lower() or 'entrees' in texte_extrait.lower(),
                    "Contient section PLATS": 'PLATS' in texte_extrait or 'plats' in texte_extrait.lower(),
                    "Contient section DESSERTS": 'DESSERTS' in texte_extrait or 'desserts' in texte_extrait.lower(),
                    "Contient 'Supions'": 'Supions' in texte_extrait or 'supions' in texte_extrait.lower(),
                    "Contient 'Linguine'": 'Linguine' in texte_extrait or 'linguine' in texte_extrait.lower(),
                    "Contient 'Boissons' ou items bar": any(item in texte_extrait.lower() for item in ['vin', 'cocktail', 'whisky', 'boissons']),
                    "Contient total CA": 'TOTAL CA' in texte_extrait or 'total ca' in texte_extrait.lower() or '456.50' in texte_extrait
                }
                
                passed_checks = sum(1 for check in completeness_checks.values() if check)
                total_checks = len(completeness_checks)
                
                # Performance check
                performance_ok = upload_time < 5.0  # Moins de 5 secondes
                
                if passed_checks >= 7:  # Au moins 70% des vérifications passent
                    self.log_result("PDF Upload & Extraction Completeness", True, 
                                  f"Extraction complète réussie ({passed_checks}/{total_checks} vérifications passées, {len(texte_extrait)} caractères extraits, {upload_time:.2f}s)",
                                  {
                                      "document_id": document_id,
                                      "texte_length": len(texte_extrait),
                                      "upload_time": upload_time,
                                      "checks_passed": f"{passed_checks}/{total_checks}",
                                      "failed_checks": [check for check, result in completeness_checks.items() if not result],
                                      "texte_sample": texte_extrait[:200] + "..." if len(texte_extrait) > 200 else texte_extrait
                                  })
                else:
                    self.log_result("PDF Upload & Extraction Completeness", False, 
                                  f"Extraction incomplète ({passed_checks}/{total_checks} vérifications passées)",
                                  {
                                      "failed_checks": [check for check, result in completeness_checks.items() if not result],
                                      "texte_extrait": texte_extrait
                                  })
                
                # Test performance séparément
                if performance_ok:
                    self.log_result("PDF Extraction Performance", True, f"Performance acceptable ({upload_time:.2f}s < 5s)")
                else:
                    self.log_result("PDF Extraction Performance", False, f"Performance lente ({upload_time:.2f}s >= 5s)")
                
                return document_id, texte_extrait
                
            else:
                self.log_result("PDF Upload & Extraction Completeness", False, 
                              f"Échec upload (HTTP {response.status_code})", response.text)
                return None, None
                
        except Exception as e:
            self.log_result("PDF Upload & Extraction Completeness", False, "Exception", str(e))
            return None, None

    def test_get_document_full_content(self, document_id):
        """Test GET /api/ocr/document/{id} pour vérifier le contenu complet"""
        print("\n=== TEST GET DOCUMENT COMPLET ===")
        
        if not document_id:
            self.log_result("GET Document Full Content", False, "Pas de document_id disponible")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
            
            if response.status_code == 200:
                document_data = response.json()
                texte_extrait = document_data.get('texte_extrait', '')
                
                # Vérifications du contenu complet
                content_checks = {
                    "Document ID présent": document_data.get('id') == document_id,
                    "Type document correct": document_data.get('type_document') == 'z_report',
                    "Texte extrait non vide": len(texte_extrait) > 0,
                    "Texte extrait substantiel": len(texte_extrait) > 150,
                    "Données parsées présentes": document_data.get('donnees_parsees') is not None,
                    "Statut traité": document_data.get('statut') in ['traite', 'en_attente'],
                    "File type défini": document_data.get('file_type') == 'pdf'
                }
                
                passed_checks = sum(1 for check in content_checks.values() if check)
                total_checks = len(content_checks)
                
                if passed_checks >= 6:  # Au moins 85% des vérifications
                    self.log_result("GET Document Full Content", True, 
                                  f"Document complet récupéré ({passed_checks}/{total_checks} vérifications, {len(texte_extrait)} caractères)",
                                  {
                                      "document_structure": list(document_data.keys()),
                                      "texte_length": len(texte_extrait)
                                  })
                else:
                    self.log_result("GET Document Full Content", False, 
                                  f"Document incomplet ({passed_checks}/{total_checks} vérifications)",
                                  {
                                      "failed_checks": [check for check, result in content_checks.items() if not result],
                                      "document_data": document_data
                                  })
            else:
                self.log_result("GET Document Full Content", False, 
                              f"Échec récupération (HTTP {response.status_code})", response.text)
                
        except Exception as e:
            self.log_result("GET Document Full Content", False, "Exception", str(e))

    def test_image_ocr_no_regression(self):
        """Test de non-régression pour l'OCR d'images"""
        print("\n=== TEST NON-RÉGRESSION OCR IMAGES ===")
        
        try:
            # Créer une image simulée avec du texte
            image_content = self.create_test_image_with_text()
            
            files = {
                'file': ('test_image.png', io.BytesIO(image_content), 'image/png')
            }
            data = {
                'type_document': 'z_report'
            }
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                response_data = response.json()
                texte_extrait = response_data.get('texte_extrait', '')
                
                # Vérifications de base pour les images
                image_checks = {
                    "Texte extrait non vide": len(texte_extrait) > 0,
                    "File type image": response_data.get('file_type') == 'image',
                    "Document ID généré": response_data.get('document_id') is not None
                }
                
                passed_checks = sum(1 for check in image_checks.values() if check)
                
                if passed_checks == len(image_checks):
                    self.log_result("Image OCR No Regression", True, 
                                  f"OCR image fonctionne ({len(texte_extrait)} caractères extraits)")
                else:
                    self.log_result("Image OCR No Regression", False, 
                                  f"Régression détectée ({passed_checks}/{len(image_checks)} vérifications)")
            else:
                self.log_result("Image OCR No Regression", False, 
                              f"Échec upload image (HTTP {response.status_code})")
                
        except Exception as e:
            self.log_result("Image OCR No Regression", False, "Exception", str(e))

    def create_test_image_with_text(self):
        """Créer une image de test simple avec du texte"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Créer une image simple avec du texte
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Texte simple pour test
            text = "RAPPORT Z\nSupions: 2\nLinguine: 1\nTOTAL: 52.00€"
            draw.text((20, 20), text, fill='black')
            
            # Convertir en bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except ImportError:
            # Fallback si PIL n'est pas disponible
            return b"PNG_PLACEHOLDER_DATA"

    def test_ocr_endpoints_stability(self):
        """Test de stabilité des endpoints OCR"""
        print("\n=== TEST STABILITÉ ENDPOINTS OCR ===")
        
        try:
            # Test GET /api/ocr/documents
            response = requests.get(f"{BASE_URL}/ocr/documents")
            documents_ok = response.status_code == 200
            
            if documents_ok:
                documents = response.json()
                self.log_result("GET /ocr/documents Stability", True, 
                              f"Endpoint stable ({len(documents)} documents listés)")
            else:
                self.log_result("GET /ocr/documents Stability", False, 
                              f"Endpoint instable (HTTP {response.status_code})")
            
            # Test avec un document existant si disponible
            if self.created_document_ids:
                doc_id = self.created_document_ids[0]
                response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                
                if response.status_code == 200:
                    self.log_result("GET /ocr/document/{id} Stability", True, "Endpoint stable")
                else:
                    self.log_result("GET /ocr/document/{id} Stability", False, 
                                  f"Endpoint instable (HTTP {response.status_code})")
            
        except Exception as e:
            self.log_result("OCR Endpoints Stability", False, "Exception", str(e))

    def cleanup_test_documents(self):
        """Nettoyer les documents de test créés"""
        print("\n=== NETTOYAGE DOCUMENTS TEST ===")
        
        for doc_id in self.created_document_ids:
            try:
                response = requests.delete(f"{BASE_URL}/ocr/document/{doc_id}")
                if response.status_code == 200:
                    print(f"✅ Document {doc_id[:8]}... supprimé")
                else:
                    print(f"⚠️ Échec suppression document {doc_id[:8]}...")
            except Exception as e:
                print(f"❌ Erreur suppression {doc_id[:8]}...: {str(e)}")

    def run_all_tests(self):
        """Exécuter tous les tests OCR PDF"""
        print("🎯 DÉBUT DES TESTS OCR PDF EXTRACTION COMPLETENESS")
        print("=" * 60)
        
        # Test principal: Upload et extraction PDF
        document_id, texte_extrait = self.test_pdf_upload_extraction_completeness()
        
        # Test récupération document complet
        self.test_get_document_full_content(document_id)
        
        # Test non-régression images
        self.test_image_ocr_no_regression()
        
        # Test stabilité endpoints
        self.test_ocr_endpoints_stability()
        
        # Résumé des résultats
        self.print_summary()
        
        # Nettoyage
        self.cleanup_test_documents()
        
        return self.test_results

    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS OCR PDF EXTRACTION")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échecs: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_suite = OCRPDFExtractionTest()
    results = test_suite.run_all_tests()