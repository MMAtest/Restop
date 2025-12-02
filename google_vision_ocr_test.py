#!/usr/bin/env python3
"""
Test complet de l'intégration Google Cloud Vision API pour OCR
Tests: Connexion Google Cloud, extraction texte améliorée, types de documents, performance
"""

import requests
import json
import io
import base64
from datetime import datetime
import time
import os
from PIL import Image, ImageDraw, ImageFont

# Configuration
BASE_URL = "https://easy-resto-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class GoogleVisionOCRTestSuite:
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
    
    def test_google_cloud_connection(self):
        """Test 1: Vérifier la connexion Google Cloud et les credentials"""
        print("\n=== TEST 1: CONNEXION GOOGLE CLOUD ===")
        
        # Vérifier que le fichier de credentials existe
        credentials_path = "/app/backend/google-vision-credentials.json"
        try:
            if os.path.exists(credentials_path):
                self.log_result("Credentials File Exists", True, f"Fichier trouvé: {credentials_path}")
                
                # Lire et vérifier le contenu
                with open(credentials_path, 'r') as f:
                    creds = json.load(f)
                    
                    # Vérifier les champs essentiels
                    required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
                    missing_fields = [field for field in required_fields if field not in creds]
                    
                    if not missing_fields:
                        self.log_result("Credentials Structure Valid", True, 
                                      f"Projet: {creds.get('project_id')}, Service Account: {creds.get('client_email')}")
                        
                        # Vérifier le projet spécifique
                        if creds.get('project_id') == 'cuisine-tracker':
                            self.log_result("Project ID Correct", True, "Projet 'cuisine-tracker' confirmé")
                        else:
                            self.log_result("Project ID Correct", False, 
                                          f"Projet attendu: 'cuisine-tracker', trouvé: '{creds.get('project_id')}'")
                        
                        # Vérifier le service account
                        expected_sa = "restaurant-ocr-service@cuisine-tracker.iam.gserviceaccount.com"
                        if creds.get('client_email') == expected_sa:
                            self.log_result("Service Account Correct", True, f"Service account: {expected_sa}")
                        else:
                            self.log_result("Service Account Correct", False, 
                                          f"Service account attendu: {expected_sa}, trouvé: {creds.get('client_email')}")
                    else:
                        self.log_result("Credentials Structure Valid", False, 
                                      f"Champs manquants: {missing_fields}")
            else:
                self.log_result("Credentials File Exists", False, f"Fichier non trouvé: {credentials_path}")
        except Exception as e:
            self.log_result("Credentials File Check", False, f"Erreur: {str(e)}")
        
        # Vérifier la variable d'environnement
        try:
            env_var = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if env_var == credentials_path:
                self.log_result("Environment Variable Set", True, f"GOOGLE_APPLICATION_CREDENTIALS={env_var}")
            else:
                self.log_result("Environment Variable Set", False, 
                              f"Attendu: {credentials_path}, trouvé: {env_var}")
        except Exception as e:
            self.log_result("Environment Variable Check", False, f"Erreur: {str(e)}")
    
    def create_test_ticket_z_image(self):
        """Créer une image de test pour Ticket Z avec texte réaliste"""
        img = Image.new('RGB', (800, 1200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Utiliser une police par défaut
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        y = 50
        
        # En-tête
        draw.text((250, y), "LA TABLE D'AUGUSTINE", fill='black', font=font_large)
        y += 40
        draw.text((300, y), "TICKET Z - SERVICE SOIR", fill='black', font=font_medium)
        y += 40
        draw.text((250, y), "Date: 17/11/2024  Heure: 23:45:30", fill='black', font=font_small)
        y += 40
        draw.text((250, y), "Nombre de couverts: 85", fill='black', font=font_small)
        y += 60
        
        # Catégories et productions
        categories = [
            ("x45) Entrées", "1125,00"),
            ("  x12) Supions en persillade", "288,00"),
            ("  x18) Burrata di Bufala", "333,00"),
            ("  x15) Fleurs de courgettes", "315,00"),
            ("x52) Plats", "1872,00"),
            ("  x15) Linguine aux palourdes", "420,00"),
            ("  x20) Rigatoni à la truffe", "620,00"),
            ("  x17) Souris d'agneau confite", "612,00"),
            ("x28) Desserts", "476,00"),
            ("  x12) Tiramisu maison", "180,00"),
            ("  x16) Tarte citron meringuée", "224,00"),
            ("x35) Bar", "892,00"),
            ("  x20) Cocktails maison", "340,00"),
            ("  x15) Vins au verre", "375,00"),
        ]
        
        for line_text, price in categories:
            draw.text((100, y), line_text, fill='black', font=font_small)
            draw.text((600, y), price + " €", fill='black', font=font_small)
            y += 30
        
        y += 40
        draw.text((100, y), "TOTAL HT:", fill='black', font=font_medium)
        draw.text((600, y), "3850,00 €", fill='black', font=font_medium)
        y += 35
        draw.text((100, y), "TOTAL TTC:", fill='black', font=font_medium)
        draw.text((600, y), "4365,00 €", fill='black', font=font_medium)
        
        # Convertir en bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
    
    def create_test_facture_image(self):
        """Créer une image de test pour facture fournisseur"""
        img = Image.new('RGB', (800, 1000), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        y = 50
        
        # En-tête fournisseur
        draw.text((250, y), "MAISON ARTIGIANA", fill='black', font=font_large)
        y += 35
        draw.text((200, y), "Fournisseur Produits Italiens Premium", fill='black', font=font_small)
        y += 50
        
        draw.text((100, y), "FACTURE N°: FAC-2024-11-1234", fill='black', font=font_medium)
        y += 30
        draw.text((100, y), "Date: 17/11/2024", fill='black', font=font_small)
        y += 30
        draw.text((100, y), "Client: La Table d'Augustine", fill='black', font=font_small)
        y += 60
        
        # Produits
        products = [
            ("Burrata di Bufala 250g", "12", "18,50", "222,00"),
            ("Mozzarella di Bufala 500g", "8", "12,00", "96,00"),
            ("Parmesan Reggiano 24 mois", "5", "45,00", "225,00"),
            ("Spaghetti artisanaux 500g", "15", "8,50", "127,50"),
            ("Huile d'olive extra vierge 1L", "6", "22,00", "132,00"),
        ]
        
        draw.text((100, y), "Produit", fill='black', font=font_small)
        draw.text((350, y), "Qté", fill='black', font=font_small)
        draw.text((450, y), "P.U.", fill='black', font=font_small)
        draw.text((600, y), "Total", fill='black', font=font_small)
        y += 30
        
        for prod, qty, pu, total in products:
            draw.text((100, y), prod, fill='black', font=font_small)
            draw.text((350, y), qty, fill='black', font=font_small)
            draw.text((450, y), pu + " €", fill='black', font=font_small)
            draw.text((600, y), total + " €", fill='black', font=font_small)
            y += 25
        
        y += 40
        draw.text((100, y), "TOTAL HT:", fill='black', font=font_medium)
        draw.text((600, y), "802,50 €", fill='black', font=font_medium)
        y += 30
        draw.text((100, y), "TVA 5,5%:", fill='black', font=font_small)
        draw.text((600, y), "44,14 €", fill='black', font=font_small)
        y += 30
        draw.text((100, y), "TOTAL TTC:", fill='black', font=font_medium)
        draw.text((600, y), "846,64 €", fill='black', font=font_medium)
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
    
    def test_ocr_improved_extraction(self):
        """Test 2: OCR amélioré avec Google Vision - Qualité d'extraction"""
        print("\n=== TEST 2: OCR AMÉLIORÉ GOOGLE VISION ===")
        
        # Test avec Ticket Z
        print("\n--- Test Ticket Z ---")
        try:
            image_data = self.create_test_ticket_z_image()
            
            files = {
                'file': ('test_ticket_z.png', image_data, 'image/png')
            }
            data = {
                'document_type': 'z_report'
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.created_document_ids.append(result.get('document_id'))
                
                texte_extrait = result.get('texte_extrait', '')
                donnees_parsees = result.get('donnees_parsees', {})
                
                # Vérifier la qualité de l'extraction
                quality_checks = {
                    "Texte extrait non vide": len(texte_extrait) > 100,
                    "Date détectée": "17/11/2024" in texte_extrait or "2024" in texte_extrait,
                    "Montants détectés": any(price in texte_extrait for price in ["1125", "1872", "476", "892"]),
                    "Catégories détectées": "Entrées" in texte_extrait or "Plats" in texte_extrait,
                    "Temps de traitement": processing_time < 10.0  # Moins de 10 secondes
                }
                
                passed_checks = sum(1 for v in quality_checks.values() if v)
                total_checks = len(quality_checks)
                
                self.log_result("OCR Ticket Z - Google Vision", 
                              passed_checks == total_checks,
                              f"Qualité: {passed_checks}/{total_checks} checks passés, Temps: {processing_time:.2f}s",
                              {"checks": quality_checks, "texte_length": len(texte_extrait)})
                
                # Vérifier le parsing
                if donnees_parsees:
                    z_analysis = donnees_parsees.get('z_analysis', {})
                    if z_analysis:
                        categories_detectees = z_analysis.get('categories_detectees', [])
                        productions_detectees = z_analysis.get('productions_detectees', [])
                        
                        self.log_result("Parsing Ticket Z - Catégories", 
                                      len(categories_detectees) > 0,
                                      f"{len(categories_detectees)} catégories détectées")
                        
                        self.log_result("Parsing Ticket Z - Productions", 
                                      len(productions_detectees) > 0,
                                      f"{len(productions_detectees)} productions détectées")
                    else:
                        self.log_result("Parsing Ticket Z", False, "z_analysis manquant")
                else:
                    self.log_result("Parsing Ticket Z", False, "donnees_parsees vide")
            else:
                self.log_result("OCR Ticket Z - Google Vision", False, 
                              f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("OCR Ticket Z - Google Vision", False, f"Exception: {str(e)}")
        
        # Test avec Facture Fournisseur
        print("\n--- Test Facture Fournisseur ---")
        try:
            image_data = self.create_test_facture_image()
            
            files = {
                'file': ('test_facture.png', image_data, 'image/png')
            }
            data = {
                'document_type': 'facture_fournisseur'
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.created_document_ids.append(result.get('document_id'))
                
                texte_extrait = result.get('texte_extrait', '')
                donnees_parsees = result.get('donnees_parsees', {})
                
                # Vérifier la qualité de l'extraction
                quality_checks = {
                    "Texte extrait non vide": len(texte_extrait) > 100,
                    "Fournisseur détecté": "ARTIGIANA" in texte_extrait or "Artigiana" in texte_extrait,
                    "Numéro facture détecté": "FAC-2024" in texte_extrait or "1234" in texte_extrait,
                    "Produits détectés": "Burrata" in texte_extrait or "Mozzarella" in texte_extrait,
                    "Montants détectés": "802" in texte_extrait or "846" in texte_extrait,
                    "Temps de traitement": processing_time < 10.0
                }
                
                passed_checks = sum(1 for v in quality_checks.values() if v)
                total_checks = len(quality_checks)
                
                self.log_result("OCR Facture - Google Vision", 
                              passed_checks >= total_checks - 1,  # Au moins 5/6 checks
                              f"Qualité: {passed_checks}/{total_checks} checks passés, Temps: {processing_time:.2f}s",
                              {"checks": quality_checks, "texte_length": len(texte_extrait)})
                
                # Vérifier le parsing
                if donnees_parsees:
                    fournisseur = donnees_parsees.get('fournisseur')
                    produits = donnees_parsees.get('produits', [])
                    
                    self.log_result("Parsing Facture - Données", 
                                  fournisseur is not None or len(produits) > 0,
                                  f"Fournisseur: {fournisseur}, Produits: {len(produits)}")
                else:
                    self.log_result("Parsing Facture", False, "donnees_parsees vide")
            else:
                self.log_result("OCR Facture - Google Vision", False, 
                              f"Erreur {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_result("OCR Facture - Google Vision", False, f"Exception: {str(e)}")
    
    def test_ocr_endpoints_compatibility(self):
        """Test 3: Vérifier que tous les endpoints OCR fonctionnent toujours"""
        print("\n=== TEST 3: COMPATIBILITÉ ENDPOINTS OCR ===")
        
        # Test GET /api/ocr/documents
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                self.log_result("GET /ocr/documents", True, 
                              f"{len(documents)} documents trouvés")
            else:
                self.log_result("GET /ocr/documents", False, 
                              f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET /ocr/documents", False, f"Exception: {str(e)}")
        
        # Test GET /api/ocr/document/{id} si on a créé des documents
        if self.created_document_ids:
            doc_id = self.created_document_ids[0]
            try:
                response = requests.get(f"{BASE_URL}/ocr/document/{doc_id}")
                if response.status_code == 200:
                    document = response.json()
                    required_fields = ['id', 'type_document', 'texte_extrait', 'donnees_parsees', 'statut']
                    missing_fields = [f for f in required_fields if f not in document]
                    
                    self.log_result("GET /ocr/document/{id}", 
                                  len(missing_fields) == 0,
                                  f"Document récupéré avec tous les champs requis" if not missing_fields 
                                  else f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("GET /ocr/document/{id}", False, 
                                  f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("GET /ocr/document/{id}", False, f"Exception: {str(e)}")
        
        # Test DELETE /api/ocr/document/{id}
        if len(self.created_document_ids) > 1:
            doc_id = self.created_document_ids[-1]  # Supprimer le dernier
            try:
                response = requests.delete(f"{BASE_URL}/ocr/document/{doc_id}")
                if response.status_code == 200:
                    self.log_result("DELETE /ocr/document/{id}", True, 
                                  "Document supprimé avec succès")
                    self.created_document_ids.remove(doc_id)
                else:
                    self.log_result("DELETE /ocr/document/{id}", False, 
                                  f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("DELETE /ocr/document/{id}", False, f"Exception: {str(e)}")
    
    def test_performance_comparison(self):
        """Test 4: Comparer les performances Google Vision"""
        print("\n=== TEST 4: PERFORMANCE GOOGLE VISION ===")
        
        # Créer une image de test plus complexe
        try:
            image_data = self.create_test_ticket_z_image()
            
            files = {
                'file': ('performance_test.png', image_data, 'image/png')
            }
            data = {
                'document_type': 'z_report'
            }
            
            # Mesurer le temps de traitement
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                texte_extrait = result.get('texte_extrait', '')
                
                # Critères de performance
                performance_metrics = {
                    "Temps total < 15s": total_time < 15.0,
                    "Texte extrait > 200 chars": len(texte_extrait) > 200,
                    "Extraction complète": len(texte_extrait) > 500,
                    "Pas d'erreur API": response.status_code == 200
                }
                
                passed_metrics = sum(1 for v in performance_metrics.values() if v)
                total_metrics = len(performance_metrics)
                
                self.log_result("Performance Google Vision", 
                              passed_metrics >= 3,  # Au moins 3/4 métriques
                              f"Métriques: {passed_metrics}/{total_metrics}, Temps: {total_time:.2f}s",
                              {"metrics": performance_metrics, "texte_length": len(texte_extrait)})
                
                # Nettoyer
                if result.get('document_id'):
                    self.created_document_ids.append(result.get('document_id'))
            else:
                self.log_result("Performance Google Vision", False, 
                              f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Performance Google Vision", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test 5: Gestion des erreurs API Google Cloud"""
        print("\n=== TEST 5: GESTION ERREURS GOOGLE CLOUD ===")
        
        # Test avec fichier invalide
        try:
            invalid_data = b"This is not a valid image"
            files = {
                'file': ('invalid.txt', invalid_data, 'text/plain')
            }
            data = {
                'document_type': 'z_report'
            }
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            # On s'attend à une erreur ou un traitement gracieux
            if response.status_code in [400, 422, 500]:
                self.log_result("Gestion Fichier Invalide", True, 
                              f"Erreur appropriée retournée: {response.status_code}")
            elif response.status_code == 200:
                result = response.json()
                # Vérifier si l'erreur est dans le message
                if 'erreur' in result.get('message', '').lower() or result.get('statut') == 'erreur':
                    self.log_result("Gestion Fichier Invalide", True, 
                                  "Erreur gérée gracieusement dans la réponse")
                else:
                    self.log_result("Gestion Fichier Invalide", False, 
                                  "Fichier invalide accepté sans erreur")
            else:
                self.log_result("Gestion Fichier Invalide", False, 
                              f"Code inattendu: {response.status_code}")
        except Exception as e:
            self.log_result("Gestion Fichier Invalide", True, 
                          f"Exception levée comme attendu: {str(e)[:100]}")
    
    def cleanup(self):
        """Nettoyer les documents de test créés"""
        print("\n=== NETTOYAGE ===")
        for doc_id in self.created_document_ids:
            try:
                response = requests.delete(f"{BASE_URL}/ocr/document/{doc_id}")
                if response.status_code == 200:
                    print(f"✅ Document {doc_id} supprimé")
            except:
                pass
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "="*80)
        print("RÉSUMÉ DES TESTS GOOGLE VISION OCR")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nTotal tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
                    if result.get('details'):
                        print(f"    Détails: {result['details']}")
        
        print("\n" + "="*80)
        
        return success_rate >= 80.0  # Succès si au moins 80% des tests passent

def main():
    """Fonction principale"""
    print("="*80)
    print("TEST INTÉGRATION GOOGLE CLOUD VISION API - LA TABLE D'AUGUSTINE")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    suite = GoogleVisionOCRTestSuite()
    
    try:
        # Exécuter tous les tests
        suite.test_google_cloud_connection()
        suite.test_ocr_improved_extraction()
        suite.test_ocr_endpoints_compatibility()
        suite.test_performance_comparison()
        suite.test_error_handling()
        
        # Nettoyer
        suite.cleanup()
        
        # Afficher le résumé
        success = suite.print_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrompus par l'utilisateur")
        suite.cleanup()
        return 1
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {str(e)}")
        suite.cleanup()
        return 1

if __name__ == "__main__":
    exit(main())
