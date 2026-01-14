#!/usr/bin/env python3
"""
OCR PDF Extraction Completeness Test - Using Existing Documents
Focus: Validate existing PDF extraction completeness after final combination changes
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRCompletenessTest:
    def __init__(self):
        self.test_results = []
        self.existing_pdf_docs = []
        
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

    def find_existing_pdf_documents(self):
        """Find existing PDF documents with substantial text extraction"""
        print("\n=== RECHERCHE DOCUMENTS PDF EXISTANTS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                docs = response.json()
                
                for doc in docs:
                    if (doc.get('file_type') == 'pdf' and 
                        doc.get('texte_extrait') and 
                        len(doc['texte_extrait']) > 200 and 
                        not doc['texte_extrait'].startswith('Erreur')):
                        self.existing_pdf_docs.append(doc)
                
                self.log_result("Find Existing PDF Documents", True, 
                              f"Trouvé {len(self.existing_pdf_docs)} documents PDF avec extraction réussie")
                return len(self.existing_pdf_docs) > 0
            else:
                self.log_result("Find Existing PDF Documents", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Find Existing PDF Documents", False, "Exception", str(e))
            return False

    def test_pdf_extraction_completeness(self):
        """Test PDF extraction completeness with existing documents"""
        print("\n=== TEST COMPLÉTUDE EXTRACTION PDF ===")
        
        if not self.existing_pdf_docs:
            self.log_result("PDF Extraction Completeness", False, "Aucun document PDF existant trouvé")
            return False
        
        completeness_results = []
        
        for i, doc in enumerate(self.existing_pdf_docs[:3]):  # Test first 3 documents
            doc_id = doc.get('id')
            filename = doc.get('nom_fichier', 'Unknown')
            texte_extrait = doc.get('texte_extrait', '')
            
            print(f"\n--- Test Document {i+1}: {filename} ---")
            
            # Check for required key tokens
            required_tokens = ['Rapport', 'CA', 'catégories', '(x', 'Desserts']
            alternative_tokens = ['RAPPORT', 'rapport', 'Total', 'TOTAL', 'Service', 'ENTRÉES', 'PLATS', 'BAR']
            
            found_required = []
            found_alternative = []
            
            text_lower = texte_extrait.lower()
            
            for token in required_tokens:
                if token.lower() in text_lower:
                    found_required.append(token)
            
            for token in alternative_tokens:
                if token.lower() in text_lower:
                    found_alternative.append(token)
            
            # Check for multi-line category detection
            categories_found = []
            category_keywords = ['bar', 'entrées', 'entrees', 'plats', 'desserts']
            for keyword in category_keywords:
                if keyword in text_lower:
                    categories_found.append(keyword.upper())
            
            # Check for quantity patterns (x2), (x14), etc.
            import re
            quantity_patterns = re.findall(r'\([x]?\d+\)', texte_extrait)
            
            # Evaluate completeness
            completeness_score = 0
            details = []
            
            # Text length check
            if len(texte_extrait) > 300:
                completeness_score += 2
                details.append(f"Texte substantiel: {len(texte_extrait)} caractères")
            elif len(texte_extrait) > 200:
                completeness_score += 1
                details.append(f"Texte modéré: {len(texte_extrait)} caractères")
            
            # Required tokens check
            if len(found_required) >= 2:
                completeness_score += 2
                details.append(f"Tokens requis trouvés: {found_required}")
            elif len(found_alternative) >= 3:
                completeness_score += 1
                details.append(f"Tokens alternatifs trouvés: {found_alternative}")
            
            # Category detection
            if len(categories_found) >= 3:
                completeness_score += 2
                details.append(f"Catégories détectées: {categories_found}")
            elif len(categories_found) >= 1:
                completeness_score += 1
                details.append(f"Quelques catégories: {categories_found}")
            
            # Quantity patterns
            if len(quantity_patterns) >= 3:
                completeness_score += 2
                details.append(f"Patterns quantité trouvés: {quantity_patterns[:5]}")
            elif len(quantity_patterns) >= 1:
                completeness_score += 1
                details.append(f"Quelques patterns: {quantity_patterns}")
            
            # Overall assessment
            if completeness_score >= 6:
                result_status = True
                result_msg = f"COMPLÉTUDE EXCELLENTE (Score: {completeness_score}/8)"
            elif completeness_score >= 4:
                result_status = True
                result_msg = f"COMPLÉTUDE ACCEPTABLE (Score: {completeness_score}/8)"
            else:
                result_status = False
                result_msg = f"COMPLÉTUDE INSUFFISANTE (Score: {completeness_score}/8)"
            
            self.log_result(f"PDF Completeness - {filename}", result_status, result_msg, details)
            completeness_results.append(result_status)
        
        # Overall completeness assessment
        successful_docs = sum(completeness_results)
        total_docs = len(completeness_results)
        
        if successful_docs >= total_docs * 0.8:  # 80% success rate
            self.log_result("Overall PDF Extraction Completeness", True, 
                          f"{successful_docs}/{total_docs} documents avec extraction complète")
            return True
        else:
            self.log_result("Overall PDF Extraction Completeness", False, 
                          f"Seulement {successful_docs}/{total_docs} documents avec extraction complète")
            return False

    def test_get_document_no_truncation(self):
        """Test GET /api/ocr/document/{id} returns same or longer text (no truncation)"""
        print("\n=== TEST GET DOCUMENT - NO TRUNCATION ===")
        
        if not self.existing_pdf_docs:
            self.log_result("GET Document No Truncation", False, "Aucun document PDF pour le test")
            return False
        
        truncation_results = []
        
        for doc in self.existing_pdf_docs[:2]:  # Test first 2 documents
            doc_id = doc.get('id')
            filename = doc.get('nom_fichier', 'Unknown')
            original_text_length = len(doc.get('texte_extrait', ''))
            
            try:
                response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                
                if response.status_code == 200:
                    retrieved_doc = response.json()
                    retrieved_text = retrieved_doc.get('texte_extrait', '')
                    retrieved_length = len(retrieved_text)
                    
                    # Check for truncation
                    if retrieved_length >= original_text_length:
                        self.log_result(f"No Truncation - {filename}", True, 
                                      f"Texte préservé: {retrieved_length} chars (original: {original_text_length})")
                        truncation_results.append(True)
                    else:
                        self.log_result(f"No Truncation - {filename}", False, 
                                      f"Texte tronqué: {retrieved_length} chars (original: {original_text_length})")
                        truncation_results.append(False)
                else:
                    self.log_result(f"GET Document - {filename}", False, f"Status: {response.status_code}")
                    truncation_results.append(False)
                    
            except Exception as e:
                self.log_result(f"GET Document - {filename}", False, "Exception", str(e))
                truncation_results.append(False)
        
        # Overall truncation assessment
        if all(truncation_results):
            self.log_result("Overall No Truncation Test", True, "Aucune troncature détectée")
            return True
        else:
            self.log_result("Overall No Truncation Test", False, "Troncature détectée sur certains documents")
            return False

    def test_multi_line_category_detection(self):
        """Test multi-line Z-report category detection working correctly"""
        print("\n=== TEST DÉTECTION CATÉGORIES MULTI-LIGNES ===")
        
        if not self.existing_pdf_docs:
            self.log_result("Multi-line Category Detection", False, "Aucun document PDF pour le test")
            return False
        
        category_results = []
        
        for doc in self.existing_pdf_docs[:3]:
            filename = doc.get('nom_fichier', 'Unknown')
            texte_extrait = doc.get('texte_extrait', '')
            
            # Look for category structure
            categories_detected = []
            lines = texte_extrait.split('\n')
            
            category_keywords = ['BAR', 'ENTRÉES', 'ENTREES', 'PLATS', 'DESSERTS']
            items_after_categories = 0
            
            for i, line in enumerate(lines):
                line_upper = line.strip().upper()
                
                # Check if line is a category header
                for keyword in category_keywords:
                    if keyword in line_upper and len(line.strip()) < 20:  # Likely a header
                        categories_detected.append(keyword)
                        
                        # Check for items in following lines
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j].strip()
                            if ':' in next_line or '(' in next_line:
                                items_after_categories += 1
                                break
            
            # Assessment
            if len(categories_detected) >= 3 and items_after_categories >= 2:
                self.log_result(f"Category Detection - {filename}", True, 
                              f"Catégories détectées: {categories_detected}, Items: {items_after_categories}")
                category_results.append(True)
            elif len(categories_detected) >= 1:
                self.log_result(f"Category Detection - {filename}", True, 
                              f"Quelques catégories: {categories_detected}")
                category_results.append(True)
            else:
                self.log_result(f"Category Detection - {filename}", False, 
                              f"Aucune structure catégorie claire détectée")
                category_results.append(False)
        
        # Overall assessment
        successful_categories = sum(category_results)
        if successful_categories >= len(category_results) * 0.7:  # 70% success
            self.log_result("Overall Multi-line Category Detection", True, 
                          f"{successful_categories}/{len(category_results)} documents avec catégories détectées")
            return True
        else:
            self.log_result("Overall Multi-line Category Detection", False, 
                          f"Seulement {successful_categories}/{len(category_results)} avec catégories")
            return False

    def run_completeness_tests(self):
        """Run all OCR completeness regression tests"""
        print("🎯 TESTS DE COMPLÉTUDE EXTRACTION OCR PDF")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run tests in sequence
        tests = [
            self.find_existing_pdf_documents,
            self.test_pdf_extraction_completeness,
            self.test_get_document_no_truncation,
            self.test_multi_line_category_detection
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ Erreur dans {test.__name__}: {str(e)}")
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("🎯 RÉSULTATS TESTS COMPLÉTUDE OCR PDF")
        print("=" * 60)
        print(f"Tests exécutés: {total_tests}")
        print(f"Tests réussis: {passed_tests}")
        print(f"Taux de réussite: {success_rate:.1f}%")
        print(f"Temps d'exécution: {elapsed_time:.2f}s")
        
        if success_rate >= 85:
            print("✅ COMPLÉTUDE OCR PDF - VALIDATION RÉUSSIE")
            return True
        else:
            print("❌ COMPLÉTUDE OCR PDF - PROBLÈMES DÉTECTÉS")
            return False

if __name__ == "__main__":
    test_suite = OCRCompletenessTest()
    success = test_suite.run_completeness_tests()
    
    if success:
        print("\n🎉 Validation complétude extraction OCR PDF réussie!")
    else:
        print("\n⚠️ Problèmes de complétude détectés dans l'extraction OCR PDF.")