#!/usr/bin/env python3
"""
Test complet des 3 nouveaux endpoints d'intégration automatique des données OCR
Tests des APIs: 
- POST /api/ocr/process-z-report/{document_id}
- POST /api/ocr/process-facture/{document_id}  
- POST /api/ocr/process-mercuriale/{document_id}
"""

import requests
import json
import time
from datetime import datetime
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BASE_URL = "https://easy-resto-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class OCRIntegrationTestSuite:
    def __init__(self):
        self.test_results = []
        self.available_documents = []
        self.z_report_documents = []
        self.facture_documents = []
        self.mercuriale_documents = []
        
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

    def phase_1_verify_endpoints_available(self):
        """Phase 1: Vérification endpoints disponibles"""
        print("\n=== PHASE 1: VÉRIFICATION ENDPOINTS DISPONIBLES ===")
        
        # Test GET /api/ocr/documents pour obtenir des document_id existants
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                if isinstance(documents, list):
                    self.available_documents = documents
                    self.log_result("GET /api/ocr/documents", True, 
                                  f"{len(documents)} documents OCR disponibles")
                    
                    # Séparer par type de document
                    self.z_report_documents = [d for d in documents if d.get("type_document") == "z_report"]
                    self.facture_documents = [d for d in documents if d.get("type_document") == "facture_fournisseur"]
                    self.mercuriale_documents = [d for d in documents if d.get("type_document") == "mercuriale"]
                    
                    self.log_result("Documents Z-Report disponibles", len(self.z_report_documents) > 0,
                                  f"{len(self.z_report_documents)} documents z_report trouvés")
                    self.log_result("Documents Facture disponibles", len(self.facture_documents) > 0,
                                  f"{len(self.facture_documents)} documents facture_fournisseur trouvés")
                    self.log_result("Documents Mercuriale disponibles", len(self.mercuriale_documents) > 0,
                                  f"{len(self.mercuriale_documents)} documents mercuriale trouvés")
                    
                    # Afficher quelques exemples de documents
                    if self.z_report_documents:
                        sample_z = self.z_report_documents[0]
                        print(f"   Exemple Z-Report: ID={sample_z.get('id')}, nom={sample_z.get('nom_fichier')}")
                    
                    if self.facture_documents:
                        sample_f = self.facture_documents[0]
                        print(f"   Exemple Facture: ID={sample_f.get('id')}, nom={sample_f.get('nom_fichier')}")
                        
                    if self.mercuriale_documents:
                        sample_m = self.mercuriale_documents[0]
                        print(f"   Exemple Mercuriale: ID={sample_m.get('id')}, nom={sample_m.get('nom_fichier')}")
                        
                else:
                    self.log_result("GET /api/ocr/documents", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /api/ocr/documents", False, 
                              f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("GET /api/ocr/documents", False, f"Exception: {str(e)}")

    def phase_2_test_processing_ticket_z(self):
        """Phase 2: Test Processing Ticket Z"""
        print("\n=== PHASE 2: TEST PROCESSING TICKET Z ===")
        
        if not self.z_report_documents:
            self.log_result("Processing Ticket Z", False, 
                          "Aucun document z_report disponible pour les tests")
            return
        
        # Sélectionner un document avec type_document="z_report"
        test_document = self.z_report_documents[0]
        document_id = test_document.get("id")
        
        print(f"Test avec document Z-Report: {document_id} ({test_document.get('nom_fichier')})")
        
        # Récupérer l'état initial des stocks pour comparaison
        initial_stocks = self.get_current_stocks()
        initial_rapports_z = self.get_current_rapports_z()
        initial_mouvements = self.get_current_mouvements()
        
        try:
            # POST /api/ocr/process-z-report/{document_id}
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{document_id}", 
                                   headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["success", "productions_matched", "stock_deductions", "warnings"]
                missing_fields = [f for f in required_fields if f not in result]
                
                if not missing_fields:
                    self.log_result("POST /api/ocr/process-z-report structure", True,
                                  "Tous les champs requis présents dans la réponse")
                    
                    # Vérifier le succès
                    if result.get("success"):
                        self.log_result("Processing Z-Report success", True, "Processing réussi")
                        
                        # Vérifier productions_matched
                        productions_matched = result.get("productions_matched", [])
                        self.log_result("Productions matched", len(productions_matched) > 0,
                                      f"{len(productions_matched)} productions matchées")
                        
                        # Vérifier stock_deductions
                        stock_deductions = result.get("stock_deductions", [])
                        self.log_result("Stock deductions", len(stock_deductions) > 0,
                                      f"{len(stock_deductions)} déductions de stock")
                        
                        # Vérifier rapport_z_id
                        rapport_z_id = result.get("rapport_z_id")
                        if rapport_z_id:
                            self.log_result("Rapport Z créé", True, f"Rapport Z ID: {rapport_z_id}")
                        else:
                            self.log_result("Rapport Z créé", False, "Aucun rapport_z_id retourné")
                        
                        # Vérifier warnings/errors
                        warnings = result.get("warnings", [])
                        errors = result.get("errors", [])
                        if warnings:
                            print(f"   Warnings: {warnings}")
                        if errors:
                            print(f"   Errors: {errors}")
                        
                        # Attendre un peu pour que les mises à jour se propagent
                        time.sleep(2)
                        
                        # Vérifier que les stocks ont été mis à jour
                        self.verify_stock_updates(initial_stocks, "sortie")
                        
                        # Vérifier qu'un rapport Z a été créé
                        self.verify_rapport_z_creation(initial_rapports_z)
                        
                        # Vérifier que des mouvements de stock "sortie" ont été créés
                        self.verify_mouvement_creation(initial_mouvements, "sortie")
                        
                    else:
                        self.log_result("Processing Z-Report success", False, 
                                      f"Processing échoué: {result.get('message', 'Raison inconnue')}")
                else:
                    self.log_result("POST /api/ocr/process-z-report structure", False,
                                  f"Champs manquants: {missing_fields}")
            else:
                self.log_result("POST /api/ocr/process-z-report", False,
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/ocr/process-z-report", False, f"Exception: {str(e)}")

    def phase_3_test_processing_facture_fournisseur(self):
        """Phase 3: Test Processing Facture Fournisseur"""
        print("\n=== PHASE 3: TEST PROCESSING FACTURE FOURNISSEUR ===")
        
        if not self.facture_documents:
            self.log_result("Processing Facture Fournisseur", False,
                          "Aucun document facture_fournisseur disponible pour les tests")
            return
        
        # Sélectionner un document avec type_document="facture_fournisseur"
        test_document = self.facture_documents[0]
        document_id = test_document.get("id")
        
        print(f"Test avec document Facture: {document_id} ({test_document.get('nom_fichier')})")
        
        # Récupérer l'état initial pour comparaison
        initial_stocks = self.get_current_stocks()
        initial_orders = self.get_current_orders()
        initial_mouvements = self.get_current_mouvements()
        
        try:
            # POST /api/ocr/process-facture/{document_id}
            response = requests.post(f"{BASE_URL}/ocr/process-facture/{document_id}",
                                   headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["success", "supplier_id", "products_matched", "products_created", 
                                 "stock_entries_created", "price_alerts", "warnings"]
                missing_fields = [f for f in required_fields if f not in result]
                
                if not missing_fields:
                    self.log_result("POST /api/ocr/process-facture structure", True,
                                  "Tous les champs requis présents dans la réponse")
                    
                    # Vérifier le succès
                    if result.get("success"):
                        self.log_result("Processing Facture success", True, "Processing réussi")
                        
                        # Vérifier supplier_id (matché ou créé)
                        supplier_id = result.get("supplier_id")
                        if supplier_id:
                            self.log_result("Supplier matched/created", True, f"Supplier ID: {supplier_id}")
                        else:
                            self.log_result("Supplier matched/created", False, "Aucun supplier_id retourné")
                        
                        # Vérifier products_matched
                        products_matched = result.get("products_matched", [])
                        self.log_result("Products matched", len(products_matched) > 0,
                                      f"{len(products_matched)} produits matchés")
                        
                        # Vérifier products_created
                        products_created = result.get("products_created", 0)
                        self.log_result("Products created", products_created >= 0,
                                      f"{products_created} nouveaux produits créés")
                        
                        # Vérifier stock_entries_created
                        stock_entries_created = result.get("stock_entries_created", 0)
                        self.log_result("Stock entries created", stock_entries_created >= 0,
                                      f"{stock_entries_created} entrées de stock créées")
                        
                        # Vérifier price_alerts
                        price_alerts = result.get("price_alerts", [])
                        self.log_result("Price alerts", True,
                                      f"{len(price_alerts)} alertes de prix générées")
                        
                        # Vérifier order_id
                        order_id = result.get("order_id")
                        if order_id:
                            self.log_result("Order created", True, f"Commande créée: {order_id}")
                        else:
                            self.log_result("Order created", False, "Aucune commande créée")
                        
                        # Attendre un peu pour que les mises à jour se propagent
                        time.sleep(2)
                        
                        # Vérifier que les stocks ont été augmentés
                        self.verify_stock_updates(initial_stocks, "entree")
                        
                        # Vérifier que des mouvements de stock "entree" ont été créés
                        self.verify_mouvement_creation(initial_mouvements, "entree")
                        
                        # Vérifier qu'une commande fournisseur a été créée
                        self.verify_order_creation(initial_orders)
                        
                    else:
                        self.log_result("Processing Facture success", False,
                                      f"Processing échoué: {result.get('message', 'Raison inconnue')}")
                else:
                    self.log_result("POST /api/ocr/process-facture structure", False,
                                  f"Champs manquants: {missing_fields}")
            else:
                self.log_result("POST /api/ocr/process-facture", False,
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/ocr/process-facture", False, f"Exception: {str(e)}")

    def phase_4_test_processing_mercuriale(self):
        """Phase 4: Test Processing Mercuriale (si documents disponibles)"""
        print("\n=== PHASE 4: TEST PROCESSING MERCURIALE ===")
        
        if not self.mercuriale_documents:
            self.log_result("Processing Mercuriale", False,
                          "Aucun document mercuriale disponible pour les tests")
            print("   Note: Pas de documents mercuriale disponibles - test sauté")
            return
        
        # Sélectionner un document avec type_document="mercuriale"
        test_document = self.mercuriale_documents[0]
        document_id = test_document.get("id")
        
        print(f"Test avec document Mercuriale: {document_id} ({test_document.get('nom_fichier')})")
        
        # Récupérer l'état initial des produits pour comparaison des prix
        initial_produits = self.get_current_produits()
        
        try:
            # POST /api/ocr/process-mercuriale/{document_id}
            response = requests.post(f"{BASE_URL}/ocr/process-mercuriale/{document_id}",
                                   headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["success", "prices_updated", "price_changes", "warnings"]
                missing_fields = [f for f in required_fields if f not in result]
                
                if not missing_fields:
                    self.log_result("POST /api/ocr/process-mercuriale structure", True,
                                  "Tous les champs requis présents dans la réponse")
                    
                    # Vérifier le succès
                    if result.get("success"):
                        self.log_result("Processing Mercuriale success", True, "Processing réussi")
                        
                        # Vérifier prices_updated
                        prices_updated = result.get("prices_updated", 0)
                        self.log_result("Prices updated", prices_updated >= 0,
                                      f"{prices_updated} prix mis à jour")
                        
                        # Vérifier price_changes
                        price_changes = result.get("price_changes", [])
                        self.log_result("Price changes", len(price_changes) >= 0,
                                      f"{len(price_changes)} changements de prix détaillés")
                        
                        # Attendre un peu pour que les mises à jour se propagent
                        time.sleep(2)
                        
                        # Vérifier que les prix de référence ont été mis à jour
                        self.verify_price_updates(initial_produits)
                        
                    else:
                        self.log_result("Processing Mercuriale success", False,
                                      f"Processing échoué: {result.get('message', 'Raison inconnue')}")
                else:
                    self.log_result("POST /api/ocr/process-mercuriale structure", False,
                                  f"Champs manquants: {missing_fields}")
            else:
                self.log_result("POST /api/ocr/process-mercuriale", False,
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/ocr/process-mercuriale", False, f"Exception: {str(e)}")

    def phase_5_validation_workflow_complet(self):
        """Phase 5: Validation workflow complet"""
        print("\n=== PHASE 5: VALIDATION WORKFLOW COMPLET ===")
        
        # Test des cas d'erreur
        self.test_error_cases()
        
        # Vérifier la cohérence des données après processing
        self.verify_data_consistency()

    def test_error_cases(self):
        """Tester les cas d'erreur (document_id invalide, mauvais type)"""
        print("\n--- Test des cas d'erreur ---")
        
        # Test avec document_id invalide
        invalid_id = "invalid-document-id-12345"
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{invalid_id}",
                                   headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Error case - Invalid document ID", True,
                              "Erreur 404 correctement retournée pour ID invalide")
            else:
                self.log_result("Error case - Invalid document ID", False,
                              f"Code d'erreur inattendu: {response.status_code}")
        except Exception as e:
            self.log_result("Error case - Invalid document ID", False, f"Exception: {str(e)}")
        
        # Test avec mauvais type de document (utiliser un document facture pour process-z-report)
        if self.facture_documents:
            facture_id = self.facture_documents[0].get("id")
            try:
                response = requests.post(f"{BASE_URL}/ocr/process-z-report/{facture_id}",
                                       headers=HEADERS)
                if response.status_code == 400:
                    self.log_result("Error case - Wrong document type", True,
                                  "Erreur 400 correctement retournée pour mauvais type")
                else:
                    self.log_result("Error case - Wrong document type", False,
                                  f"Code d'erreur inattendu: {response.status_code}")
            except Exception as e:
                self.log_result("Error case - Wrong document type", False, f"Exception: {str(e)}")

    def verify_data_consistency(self):
        """Vérifier la cohérence des données après processing"""
        print("\n--- Vérification cohérence des données ---")
        
        # Vérifier que les documents traités ont leur statut passé à "integre"
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                processed_docs = [d for d in documents if d.get("statut") == "integre"]
                
                if len(processed_docs) > 0:
                    self.log_result("Document status update", True,
                                  f"{len(processed_docs)} documents avec statut 'integre'")
                else:
                    self.log_result("Document status update", False,
                                  "Aucun document avec statut 'integre' trouvé")
            else:
                self.log_result("Document status verification", False,
                              f"Erreur lors de la vérification: {response.status_code}")
        except Exception as e:
            self.log_result("Document status verification", False, f"Exception: {str(e)}")

    # Méthodes utilitaires pour récupérer l'état actuel des données
    
    def get_current_stocks(self):
        """Récupérer l'état actuel des stocks"""
        try:
            response = requests.get(f"{BASE_URL}/stocks")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_current_rapports_z(self):
        """Récupérer l'état actuel des rapports Z"""
        try:
            response = requests.get(f"{BASE_URL}/rapports_z")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_current_mouvements(self):
        """Récupérer l'état actuel des mouvements"""
        try:
            response = requests.get(f"{BASE_URL}/mouvements")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_current_orders(self):
        """Récupérer l'état actuel des commandes"""
        try:
            response = requests.get(f"{BASE_URL}/orders")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_current_produits(self):
        """Récupérer l'état actuel des produits"""
        try:
            response = requests.get(f"{BASE_URL}/produits")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    # Méthodes de vérification des mises à jour
    
    def verify_stock_updates(self, initial_stocks, movement_type):
        """Vérifier que les stocks ont été mis à jour"""
        try:
            current_stocks = self.get_current_stocks()
            
            # Comparer les quantités (simplification - on vérifie juste qu'il y a eu des changements)
            changes_detected = False
            for current_stock in current_stocks:
                initial_stock = next((s for s in initial_stocks if s.get("produit_id") == current_stock.get("produit_id")), None)
                if initial_stock:
                    if current_stock.get("quantite_actuelle") != initial_stock.get("quantite_actuelle"):
                        changes_detected = True
                        break
            
            if changes_detected:
                self.log_result(f"Stock updates ({movement_type})", True,
                              "Changements détectés dans les stocks")
            else:
                self.log_result(f"Stock updates ({movement_type})", False,
                              "Aucun changement détecté dans les stocks")
                
        except Exception as e:
            self.log_result(f"Stock updates ({movement_type})", False, f"Exception: {str(e)}")

    def verify_rapport_z_creation(self, initial_rapports):
        """Vérifier qu'un rapport Z a été créé"""
        try:
            current_rapports = self.get_current_rapports_z()
            
            if len(current_rapports) > len(initial_rapports):
                self.log_result("Rapport Z creation", True,
                              f"Nouveau rapport Z créé ({len(current_rapports)} vs {len(initial_rapports)})")
            else:
                self.log_result("Rapport Z creation", False,
                              "Aucun nouveau rapport Z détecté")
                
        except Exception as e:
            self.log_result("Rapport Z creation", False, f"Exception: {str(e)}")

    def verify_mouvement_creation(self, initial_mouvements, movement_type):
        """Vérifier que des mouvements ont été créés"""
        try:
            current_mouvements = self.get_current_mouvements()
            
            # Chercher de nouveaux mouvements du type spécifié
            new_mouvements = []
            for mouvement in current_mouvements:
                if mouvement.get("type") == movement_type:
                    # Vérifier si ce mouvement existait déjà
                    existing = next((m for m in initial_mouvements 
                                   if m.get("id") == mouvement.get("id")), None)
                    if not existing:
                        new_mouvements.append(mouvement)
            
            if len(new_mouvements) > 0:
                self.log_result(f"Mouvement creation ({movement_type})", True,
                              f"{len(new_mouvements)} nouveaux mouvements de type '{movement_type}'")
            else:
                self.log_result(f"Mouvement creation ({movement_type})", False,
                              f"Aucun nouveau mouvement de type '{movement_type}' détecté")
                
        except Exception as e:
            self.log_result(f"Mouvement creation ({movement_type})", False, f"Exception: {str(e)}")

    def verify_order_creation(self, initial_orders):
        """Vérifier qu'une commande a été créée"""
        try:
            current_orders = self.get_current_orders()
            
            if len(current_orders) > len(initial_orders):
                self.log_result("Order creation", True,
                              f"Nouvelle commande créée ({len(current_orders)} vs {len(initial_orders)})")
            else:
                self.log_result("Order creation", False,
                              "Aucune nouvelle commande détectée")
                
        except Exception as e:
            self.log_result("Order creation", False, f"Exception: {str(e)}")

    def verify_price_updates(self, initial_produits):
        """Vérifier que les prix de référence ont été mis à jour"""
        try:
            current_produits = self.get_current_produits()
            
            # Comparer les prix de référence
            price_changes = 0
            for current_produit in current_produits:
                initial_produit = next((p for p in initial_produits if p.get("id") == current_produit.get("id")), None)
                if initial_produit:
                    if current_produit.get("reference_price") != initial_produit.get("reference_price"):
                        price_changes += 1
            
            if price_changes > 0:
                self.log_result("Price updates", True,
                              f"{price_changes} prix de référence mis à jour")
            else:
                self.log_result("Price updates", False,
                              "Aucun prix de référence mis à jour")
                
        except Exception as e:
            self.log_result("Price updates", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécuter tous les tests dans l'ordre"""
        print("🚀 DÉBUT DES TESTS D'INTÉGRATION OCR")
        print("=" * 60)
        
        start_time = time.time()
        
        # Exécuter les phases de test
        self.phase_1_verify_endpoints_available()
        self.phase_2_test_processing_ticket_z()
        self.phase_3_test_processing_facture_fournisseur()
        self.phase_4_test_processing_mercuriale()
        self.phase_5_validation_workflow_complet()
        
        # Résumé des résultats
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS D'INTÉGRATION OCR")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        print(f"⏱️ Durée totale: {duration:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n🎯 TESTS D'INTÉGRATION OCR TERMINÉS")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "duration": duration,
            "results": self.test_results
        }

if __name__ == "__main__":
    # Exécuter les tests
    test_suite = OCRIntegrationTestSuite()
    results = test_suite.run_all_tests()
    
    # Sauvegarder les résultats
    with open("/app/ocr_integration_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats sauvegardés dans: /app/ocr_integration_test_results.json")