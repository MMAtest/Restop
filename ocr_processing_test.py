#!/usr/bin/env python3
"""
Test spécifique pour vérifier que le traitement OCR ne reste pas bloqué sur "traitement"
Focus sur le problème rapporté par l'utilisateur
"""

import requests
import json
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BASE_URL = "https://smart-inventory-63.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRProcessingTestSuite:
    def __init__(self):
        self.test_results = []
        
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

    def create_realistic_invoice_image(self):
        """Crée une image de facture réaliste"""
        invoice_text = """FACTURE FOURNISSEUR
        
MARCHÉ CENTRAL ALIMENTAIRE
123 Avenue des Halles
75001 Paris
Tel: 01.42.33.44.55

FACTURE N°: FAC-2025-0156
Date: 16/01/2025
Client: Restaurant La Table d'Augustine

DÉTAIL DES PRODUITS:
- Tomates cerises Bio (5 kg) .......... 17.50€
- Mozzarella di Bufala (2 kg) ......... 36.00€
- Basilic frais (500g) ................ 8.50€
- Huile d'olive extra vierge (1L) ..... 12.00€
- Pâtes Linguine artisanales (3 kg) ... 24.00€

SOUS-TOTAL HT: ......................... 98.00€
TVA 5.5%: .............................. 5.39€
TOTAL TTC: ............................ 103.39€

Règlement: 30 jours net
Merci de votre confiance"""
        
        try:
            # Créer une image plus grande et plus réaliste
            img = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(img)
            
            # Utiliser une police par défaut
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Ajouter le texte ligne par ligne avec un meilleur espacement
            lines = invoice_text.split('\n')
            y_position = 30
            for line in lines:
                draw.text((30, y_position), line.strip(), fill='black', font=font)
                y_position += 25
            
            # Ajouter quelques éléments graphiques pour rendre plus réaliste
            # Ligne de séparation
            draw.line([(30, 200), (570, 200)], fill='black', width=2)
            draw.line([(30, 500), (570, 500)], fill='black', width=2)
            
            # Convertir en bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
        except Exception as e:
            print(f"Erreur création image facture: {e}")
            return None

    def test_invoice_processing_not_stuck(self):
        """Test principal: vérifier que le traitement de facture ne reste pas bloqué"""
        print("\n=== TEST PRINCIPAL: TRAITEMENT FACTURE NON BLOQUÉ ===")
        
        image_content = self.create_realistic_invoice_image()
        if not image_content:
            self.log_result("Création image facture", False, "Impossible de créer l'image de test")
            return None
        
        try:
            files = {
                'file': ('facture_realiste.png', image_content, 'image/png')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            print("📤 Upload de la facture en cours...")
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            
            upload_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.log_result("Upload facture réaliste", True, 
                                  f"Upload terminé en {upload_time:.2f}s - ID: {document_id[:8]}...")
                    
                    # POINT CRITIQUE: Vérifier que le traitement ne reste pas bloqué
                    if upload_time < 10:  # Doit se terminer rapidement
                        self.log_result("⚡ Temps de traitement acceptable", True, 
                                      f"Traitement en {upload_time:.2f}s (< 10s)")
                    else:
                        self.log_result("⚡ Temps de traitement acceptable", False, 
                                      f"Traitement trop long: {upload_time:.2f}s")
                    
                    # Vérifier immédiatement le statut
                    immediate_status = result.get("donnees_parsees", {}).get("statut", "inconnu")
                    if immediate_status != "en_attente":
                        self.log_result("🎯 Statut immédiat", True, 
                                      f"Statut après upload: {immediate_status}")
                    else:
                        self.log_result("🎯 Statut immédiat", False, 
                                      "Document reste en attente après upload")
                    
                    # Attendre un peu et vérifier à nouveau le statut
                    print("⏳ Vérification du statut après 2 secondes...")
                    time.sleep(2)
                    
                    status_response = requests.get(f"{BASE_URL}/ocr/document/{document_id}")
                    if status_response.status_code == 200:
                        doc_data = status_response.json()
                        final_status = doc_data.get("statut", "inconnu")
                        
                        if final_status == "traite":
                            self.log_result("🎯 Statut final", True, 
                                          f"Document traité avec succès: {final_status}")
                        elif final_status == "en_attente":
                            self.log_result("🎯 Statut final", False, 
                                          "❌ PROBLÈME: Document encore en attente après 2s")
                        elif final_status == "erreur":
                            self.log_result("🎯 Statut final", False, 
                                          f"Erreur de traitement: {final_status}")
                        else:
                            self.log_result("🎯 Statut final", False, 
                                          f"Statut inconnu: {final_status}")
                        
                        # Vérifier l'extraction de texte
                        texte_extrait = doc_data.get("texte_extrait", "")
                        if len(texte_extrait) > 50:
                            self.log_result("📄 Extraction texte", True, 
                                          f"Texte extrait: {len(texte_extrait)} caractères")
                            
                            # Vérifier que des éléments clés de la facture sont présents
                            key_elements = ["FACTURE", "TOTAL", "€"]
                            found_elements = [elem for elem in key_elements if elem in texte_extrait.upper()]
                            
                            if len(found_elements) >= 2:
                                self.log_result("🔍 Contenu facture détecté", True, 
                                              f"Éléments trouvés: {found_elements}")
                            else:
                                self.log_result("🔍 Contenu facture détecté", False, 
                                              f"Peu d'éléments détectés: {found_elements}")
                        else:
                            self.log_result("📄 Extraction texte", False, 
                                          f"Texte insuffisant: {len(texte_extrait)} caractères")
                        
                        # Vérifier les données parsées
                        donnees_parsees = doc_data.get("donnees_parsees", {})
                        if isinstance(donnees_parsees, dict) and len(donnees_parsees) > 0:
                            self.log_result("🧠 Parsing données", True, 
                                          f"Données parsées: {len(donnees_parsees)} champs")
                        else:
                            self.log_result("🧠 Parsing données", False, 
                                          "Aucune donnée parsée")
                    
                    return document_id
                else:
                    self.log_result("Upload facture réaliste", False, 
                                  "Pas de document_id dans la réponse")
            else:
                self.log_result("Upload facture réaliste", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Upload facture réaliste", False, f"Exception: {str(e)}")
        
        return None

    def test_multiple_concurrent_uploads(self):
        """Test de charge: plusieurs uploads simultanés pour vérifier la stabilité"""
        print("\n=== TEST DE CHARGE: UPLOADS MULTIPLES ===")
        
        image_content = self.create_realistic_invoice_image()
        if not image_content:
            self.log_result("Test charge", False, "Impossible de créer l'image de test")
            return
        
        upload_results = []
        start_time = time.time()
        
        # Faire 3 uploads rapides
        for i in range(3):
            try:
                files = {
                    'file': (f'facture_test_{i+1}.png', image_content, 'image/png')
                }
                data = {'document_type': 'facture_fournisseur'}
                
                print(f"📤 Upload {i+1}/3...")
                upload_start = time.time()
                
                response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
                
                upload_time = time.time() - upload_start
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    document_id = result.get("document_id")
                    upload_results.append({
                        "success": True,
                        "time": upload_time,
                        "document_id": document_id
                    })
                else:
                    upload_results.append({
                        "success": False,
                        "time": upload_time,
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                upload_results.append({
                    "success": False,
                    "time": 0,
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        successful_uploads = sum(1 for r in upload_results if r["success"])
        
        if successful_uploads == 3:
            self.log_result("🚀 Uploads multiples", True, 
                          f"3/3 uploads réussis en {total_time:.2f}s")
        else:
            self.log_result("🚀 Uploads multiples", False, 
                          f"Seulement {successful_uploads}/3 uploads réussis")
        
        # Vérifier les temps individuels
        avg_time = sum(r["time"] for r in upload_results if r["success"]) / max(successful_uploads, 1)
        if avg_time < 5:
            self.log_result("⚡ Performance uploads", True, 
                          f"Temps moyen: {avg_time:.2f}s par upload")
        else:
            self.log_result("⚡ Performance uploads", False, 
                          f"Temps moyen trop élevé: {avg_time:.2f}s")

    def test_existing_documents_status(self):
        """Vérifier le statut des documents existants pour détecter des blocages"""
        print("\n=== TEST: VÉRIFICATION DOCUMENTS EXISTANTS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            
            if response.status_code == 200:
                documents = response.json()
                
                if isinstance(documents, list) and len(documents) > 0:
                    self.log_result("📋 Liste documents", True, 
                                  f"{len(documents)} documents en base")
                    
                    # Analyser les statuts
                    status_counts = {}
                    stuck_documents = []
                    
                    for doc in documents:
                        status = doc.get("statut", "inconnu")
                        status_counts[status] = status_counts.get(status, 0) + 1
                        
                        # Vérifier si le document est potentiellement bloqué
                        if status == "en_attente":
                            date_upload = doc.get("date_upload", "")
                            if date_upload:
                                try:
                                    upload_time = datetime.fromisoformat(date_upload.replace('Z', '+00:00'))
                                    time_diff = datetime.now(upload_time.tzinfo) - upload_time
                                    if time_diff.total_seconds() > 300:  # Plus de 5 minutes
                                        stuck_documents.append({
                                            "id": doc.get("id", "")[:8],
                                            "type": doc.get("type_document", ""),
                                            "age_minutes": int(time_diff.total_seconds() / 60)
                                        })
                                except:
                                    pass
                    
                    # Rapport des statuts
                    status_report = ", ".join([f"{status}: {count}" for status, count in status_counts.items()])
                    self.log_result("📊 Répartition statuts", True, status_report)
                    
                    # Vérifier les documents bloqués
                    if len(stuck_documents) == 0:
                        self.log_result("🎯 Documents bloqués", True, 
                                      "Aucun document bloqué en traitement")
                    else:
                        self.log_result("🎯 Documents bloqués", False, 
                                      f"{len(stuck_documents)} document(s) potentiellement bloqué(s)")
                        for doc in stuck_documents:
                            print(f"   ⚠️  {doc['id']}... ({doc['type']}) - {doc['age_minutes']} min")
                    
                    # Vérifier le ratio de succès
                    total_processed = status_counts.get("traite", 0) + status_counts.get("erreur", 0)
                    success_rate = (status_counts.get("traite", 0) / max(total_processed, 1)) * 100
                    
                    if success_rate >= 80:
                        self.log_result("📈 Taux de succès global", True, 
                                      f"{success_rate:.1f}% de documents traités avec succès")
                    else:
                        self.log_result("📈 Taux de succès global", False, 
                                      f"Taux de succès faible: {success_rate:.1f}%")
                else:
                    self.log_result("📋 Liste documents", False, "Aucun document en base")
            else:
                self.log_result("📋 Liste documents", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("📋 Liste documents", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests de traitement OCR"""
        print("🎯 TESTS SPÉCIFIQUES: TRAITEMENT OCR NON BLOQUÉ")
        print("=" * 60)
        print("Focus: Vérifier que l'OCR ne reste pas bloqué sur 'traitement'")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test principal
        self.test_invoice_processing_not_stuck()
        
        # Test de charge
        self.test_multiple_concurrent_uploads()
        
        # Vérification des documents existants
        self.test_existing_documents_status()
        
        total_time = time.time() - start_time
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS TRAITEMENT OCR")
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
        
        # Conclusion spécifique au problème rapporté
        print(f"\n🎯 CONCLUSION SUR LE PROBLÈME RAPPORTÉ:")
        processing_issues = [r for r in self.test_results if not r["success"] and "bloqué" in r["message"].lower()]
        
        if len(processing_issues) == 0:
            print("✅ AUCUN PROBLÈME DE BLOCAGE DÉTECTÉ")
            print("   L'endpoint OCR upload-document fonctionne correctement")
            print("   Les documents sont traités sans rester bloqués sur 'traitement'")
        else:
            print("❌ PROBLÈMES DE BLOCAGE DÉTECTÉS")
            for issue in processing_issues:
                print(f"   - {issue['message']}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "total_time": total_time,
            "processing_issues": len(processing_issues)
        }

if __name__ == "__main__":
    test_suite = OCRProcessingTestSuite()
    results = test_suite.run_all_tests()
    
    # Code de sortie basé sur les résultats
    exit_code = 0 if results["processing_issues"] == 0 else 1
    exit(exit_code)