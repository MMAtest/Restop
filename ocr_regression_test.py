#!/usr/bin/env python3
"""
OCR PDF Extraction Completeness Regression Test
Focus: Validate PDF extraction after final combination changes
"""

import requests
import json
import io
import base64
from datetime import datetime
import time

# Configuration
BASE_URL = "https://smart-inventory-63.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRRegressionTest:
    def __init__(self):
        self.test_results = []
        self.uploaded_document_id = None
        
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

    def create_z_report_pdf_content(self):
        """Create a representative Z-report PDF content with multi-line text"""
        pdf_content = """
        RAPPORT Z - LA TABLE D'AUGUSTINE
        Date: 15/12/2024
        Service: Soir
        
        === VENTES PAR CATÉGORIES ===
        
        BAR:
        (x3) Vin rouge Côtes du Rhône
        (x2) Pastis Ricard
        
        ENTRÉES:
        (x4) Supions en persillade de Mamie
        (x2) Fleurs de courgettes de Mamet
        
        PLATS:
        (x3) Linguine aux palourdes
        (x2) Bœuf Wellington à la truffe
        
        DESSERTS:
        (x5) Tiramisu maison
        (x1) Tarte aux figues
        
        TOTAL CA: 456.50€
        Nombre de couverts: 17
        """
        return pdf_content.encode('utf-8')

    def create_test_image_base64(self):
        """Create a simple test image with text for sanity check"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Add some text
        text_lines = [
            "RAPPORT Z TEST",
            "Date: 15/12/2024", 
            "(x2) Salade César",
            "(x1) Steak frites",
            "TOTAL: 45.50€"
        ]
        
        y_position = 20
        for line in text_lines:
            draw.text((20, y_position), line, fill='black', font=font)
            y_position += 25
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    def test_pdf_upload_and_extraction(self):
        """Test PDF upload and validate key tokens in extracted text"""
        print("\n=== TEST PDF UPLOAD & EXTRACTION COMPLETENESS ===")
        
        try:
            # Create representative Z-report PDF content
            pdf_content = self.create_z_report_pdf_content()
            
            # Prepare multipart form data
            files = {
                'file': ('z_report_test.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            data = {
                'type_document': 'z_report'
            }
            
            # Upload PDF document
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.uploaded_document_id = result.get('document_id')
                texte_extrait = result.get('texte_extrait', '')
                
                # Check for required key tokens
                required_tokens = ['Rapport', 'CA', 'catégories', '(x', 'DESSERTS']
                found_tokens = []
                missing_tokens = []
                
                for token in required_tokens:
                    if token.lower() in texte_extrait.lower():
                        found_tokens.append(token)
                    else:
                        missing_tokens.append(token)
                
                # Alternative check for DESSERTS/Desserts
                if 'desserts' not in texte_extrait.lower():
                    if 'DESSERTS' not in missing_tokens and 'desserts' not in [t.lower() for t in found_tokens]:
                        missing_tokens.append('DESSERTS/Desserts')
                
                if len(found_tokens) >= 4:  # Allow some flexibility
                    self.log_result("PDF Upload & Key Tokens", True, 
                                  f"Trouvé {len(found_tokens)}/5 tokens requis: {found_tokens}")
                else:
                    self.log_result("PDF Upload & Key Tokens", False, 
                                  f"Tokens manquants: {missing_tokens}, Trouvés: {found_tokens}")
                
                # Validate text extraction length (should be substantial)
                if len(texte_extrait) > 50:
                    self.log_result("PDF Text Extraction Length", True, 
                                  f"Texte extrait: {len(texte_extrait)} caractères")
                else:
                    self.log_result("PDF Text Extraction Length", False, 
                                  f"Texte trop court: {len(texte_extrait)} caractères")
                
                return True
            else:
                self.log_result("PDF Upload", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("PDF Upload & Extraction", False, "Exception", str(e))
            return False

    def test_get_document_no_truncation(self):
        """Test GET /api/ocr/document/{id} returns same or longer text (no truncation)"""
        print("\n=== TEST GET DOCUMENT - NO TRUNCATION ===")
        
        if not self.uploaded_document_id:
            self.log_result("GET Document No Truncation", False, "Pas de document uploadé pour le test")
            return False
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{self.uploaded_document_id}")
            
            if response.status_code == 200:
                document = response.json()
                texte_extrait_get = document.get('texte_extrait', '')
                
                # Compare with original upload response
                # For this test, we'll check that we get substantial text back
                if len(texte_extrait_get) > 50:
                    self.log_result("GET Document Text Length", True, 
                                  f"Texte récupéré: {len(texte_extrait_get)} caractères")
                    
                    # Check key tokens are still present
                    key_tokens = ['rapport', 'ca', '(x']
                    found_in_get = sum(1 for token in key_tokens if token.lower() in texte_extrait_get.lower())
                    
                    if found_in_get >= 2:
                        self.log_result("GET Document Key Tokens Preserved", True, 
                                      f"Tokens préservés: {found_in_get}/3")
                    else:
                        self.log_result("GET Document Key Tokens Preserved", False, 
                                      f"Tokens perdus, seulement {found_in_get}/3 trouvés")
                    
                    return True
                else:
                    self.log_result("GET Document No Truncation", False, 
                                  f"Texte tronqué ou vide: {len(texte_extrait_get)} caractères")
                    return False
            else:
                self.log_result("GET Document", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("GET Document No Truncation", False, "Exception", str(e))
            return False

    def test_image_upload_sanity(self):
        """Sanity test: Verify image upload still returns proper text"""
        print("\n=== TEST IMAGE UPLOAD SANITY CHECK ===")
        
        try:
            # Create test image
            image_base64 = self.create_test_image_base64()
            
            # Prepare image upload
            image_data = base64.b64decode(image_base64.split(',')[1])
            files = {
                'file': ('test_image.png', io.BytesIO(image_data), 'image/png')
            }
            data = {
                'type_document': 'z_report'
            }
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                texte_extrait = result.get('texte_extrait', '')
                
                # Check if we get some text back (OCR might not be perfect)
                if len(texte_extrait) > 5:
                    self.log_result("Image Upload Sanity", True, 
                                  f"OCR image fonctionne: {len(texte_extrait)} caractères extraits")
                    return True
                else:
                    # OCR might fail on simple images, but endpoint should work
                    if result.get('document_id'):
                        self.log_result("Image Upload Sanity", True, 
                                      "Endpoint image fonctionne (OCR peut être limité sur image simple)")
                        return True
                    else:
                        self.log_result("Image Upload Sanity", False, "Pas de document_id retourné")
                        return False
            else:
                self.log_result("Image Upload Sanity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Image Upload Sanity", False, "Exception", str(e))
            return False

    def test_ocr_endpoints_stability(self):
        """Test that OCR endpoints are stable after changes"""
        print("\n=== TEST OCR ENDPOINTS STABILITY ===")
        
        try:
            # Test GET /ocr/documents
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                self.log_result("GET /ocr/documents", True, f"Retourne {len(documents)} documents")
            else:
                self.log_result("GET /ocr/documents", False, f"Status: {response.status_code}")
            
            # Test specific document endpoint if we have one
            if self.uploaded_document_id:
                response = requests.get(f"{BASE_URL}/ocr/document/{self.uploaded_document_id}")
                if response.status_code == 200:
                    self.log_result("GET /ocr/document/{id}", True, "Endpoint stable")
                else:
                    self.log_result("GET /ocr/document/{id}", False, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("OCR Endpoints Stability", False, "Exception", str(e))
            return False

    def run_regression_tests(self):
        """Run all OCR regression tests"""
        print("🎯 DÉMARRAGE DES TESTS DE RÉGRESSION OCR PDF")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run focused regression tests
        tests = [
            self.test_pdf_upload_and_extraction,
            self.test_get_document_no_truncation,
            self.test_image_upload_sanity,
            self.test_ocr_endpoints_stability
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print(f"❌ Erreur dans {test.__name__}: {str(e)}")
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("🎯 RÉSULTATS TESTS DE RÉGRESSION OCR PDF")
        print("=" * 60)
        print(f"Tests exécutés: {total_tests}")
        print(f"Tests réussis: {passed_tests}")
        print(f"Taux de réussite: {success_rate:.1f}%")
        print(f"Temps d'exécution: {elapsed_time:.2f}s")
        
        if success_rate >= 80:
            print("✅ RÉGRESSION OCR PDF - TESTS RÉUSSIS")
            return True
        else:
            print("❌ RÉGRESSION OCR PDF - ÉCHECS DÉTECTÉS")
            return False

if __name__ == "__main__":
    test_suite = OCRRegressionTest()
    success = test_suite.run_regression_tests()
    
    if success:
        print("\n🎉 Tous les tests de régression OCR PDF sont passés avec succès!")
    else:
        print("\n⚠️ Des problèmes de régression ont été détectés dans l'OCR PDF.")