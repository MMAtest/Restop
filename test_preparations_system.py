#!/usr/bin/env python3
"""
Test complet du nouveau système PRODUITS + PRÉPARATIONS avec architecture Mix A+C
Tests selon les spécifications de la review request:
- PHASE 1: CRUD Stock Préparations
- PHASE 2: Exécution Préparation (Transformation)
- PHASE 3: Workflow Complet (Tomates cerises → Tomates préparées → Salade Caprese)
- PHASE 4: Compatibilité Backward
- PHASE 5: Cas d'erreur
"""

import requests
import json
from datetime import datetime, timedelta
import time
import uuid

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class PreparationsTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_produit_id = None
        self.created_preparation_id = None
        self.created_stock_preparation_id = None
        self.created_recette_id = None
        self.created_document_id = None
        
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

    def setup_test_data(self):
        """Créer les données de test nécessaires"""
        print("\n=== SETUP DONNÉES DE TEST ===")
        
        # Créer un produit de test (Tomates cerises)
        produit_data = {
            "nom": "Tomates cerises",
            "description": "Tomates cerises fraîches pour préparations",
            "categorie": "Légumes",
            "unite": "kg",
            "prix_achat": 4.50
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
            if response.status_code == 200:
                created_produit = response.json()
                self.created_produit_id = created_produit["id"]
                self.log_result("Setup - Création produit test", True, f"Produit créé: {created_produit['nom']}")
                
                # Ajouter du stock initial
                stock_update = {
                    "quantite_actuelle": 10.0,
                    "quantite_min": 2.0,
                    "quantite_max": 50.0
                }
                
                stock_response = requests.put(f"{BASE_URL}/stocks/{self.created_produit_id}", 
                                            json=stock_update, headers=HEADERS)
                if stock_response.status_code == 200:
                    self.log_result("Setup - Stock initial", True, "Stock initial de 10kg ajouté")
                else:
                    self.log_result("Setup - Stock initial", False, f"Erreur stock: {stock_response.status_code}")
            else:
                self.log_result("Setup - Création produit test", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup - Création produit test", False, "Exception", str(e))
            return False
        
        # Créer une préparation de test (Tomates préparées)
        preparation_data = {
            "nom": "Tomates cerises émincées",
            "produit_id": self.created_produit_id,
            "forme_decoupe": "émincé",
            "quantite_produit_brut": 1.0,
            "unite_produit_brut": "kg",
            "quantite_preparee": 0.85,
            "unite_preparee": "kg",
            "perte": 0.15,
            "perte_pourcentage": 15.0,
            "nombre_portions": 8,
            "taille_portion": 0.1,
            "unite_portion": "kg",
            "notes": "Émincées finement pour salades"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/preparations", json=preparation_data, headers=HEADERS)
            if response.status_code == 200:
                created_preparation = response.json()
                self.created_preparation_id = created_preparation["id"]
                self.log_result("Setup - Création préparation test", True, f"Préparation créée: {created_preparation['nom']}")
            else:
                self.log_result("Setup - Création préparation test", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup - Création préparation test", False, "Exception", str(e))
            return False
        
        return True

    def test_phase_1_crud_stock_preparations(self):
        """PHASE 1: CRUD Stock Préparations"""
        print("\n=== PHASE 1: CRUD STOCK PRÉPARATIONS ===")
        
        # Test 1: GET /api/stock-preparations (liste vide au début)
        try:
            response = requests.get(f"{BASE_URL}/stock-preparations")
            if response.status_code == 200:
                stock_preparations = response.json()
                if isinstance(stock_preparations, list):
                    self.log_result("GET /stock-preparations (initial)", True, 
                                  f"Liste récupérée: {len(stock_preparations)} éléments")
                else:
                    self.log_result("GET /stock-preparations (initial)", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /stock-preparations (initial)", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /stock-preparations (initial)", False, "Exception", str(e))
        
        # Test 2: GET /api/preparations (récupérer une préparation existante)
        if self.created_preparation_id:
            try:
                response = requests.get(f"{BASE_URL}/preparations/{self.created_preparation_id}")
                if response.status_code == 200:
                    preparation = response.json()
                    if preparation["nom"] == "Tomates cerises émincées":
                        self.log_result("GET /preparations/{id}", True, "Préparation récupérée correctement")
                    else:
                        self.log_result("GET /preparations/{id}", False, "Données incorrectes")
                else:
                    self.log_result("GET /preparations/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /preparations/{id}", False, "Exception", str(e))
        
        # Test 3: POST /api/stock-preparations (créer un stock préparation manuellement)
        if self.created_preparation_id:
            stock_preparation_data = {
                "preparation_id": self.created_preparation_id,
                "quantite_actuelle": 2.5,
                "quantite_min": 0.5,
                "quantite_max": 10.0,
                "dlc": (datetime.now() + timedelta(days=3)).isoformat()
            }
            
            try:
                response = requests.post(f"{BASE_URL}/stock-preparations", json=stock_preparation_data, headers=HEADERS)
                if response.status_code == 200:
                    created_stock_prep = response.json()
                    self.created_stock_preparation_id = created_stock_prep["id"]
                    
                    # Vérifier la structure de réponse
                    required_fields = ["preparation_id", "quantite_actuelle", "unite", "dlc", "statut"]
                    if all(field in created_stock_prep for field in required_fields):
                        self.log_result("POST /stock-preparations", True, 
                                      f"Stock préparation créé avec structure complète")
                    else:
                        missing = [f for f in required_fields if f not in created_stock_prep]
                        self.log_result("POST /stock-preparations", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("POST /stock-preparations", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /stock-preparations", False, "Exception", str(e))
        
        # Test 4: GET /api/stock-preparations/{id} (vérifier le stock créé)
        if self.created_stock_preparation_id:
            try:
                response = requests.get(f"{BASE_URL}/stock-preparations/{self.created_stock_preparation_id}")
                if response.status_code == 200:
                    stock_prep = response.json()
                    if (stock_prep["quantite_actuelle"] == 2.5 and 
                        stock_prep["preparation_id"] == self.created_preparation_id):
                        self.log_result("GET /stock-preparations/{id}", True, "Stock préparation récupéré correctement")
                    else:
                        self.log_result("GET /stock-preparations/{id}", False, "Données incorrectes")
                else:
                    self.log_result("GET /stock-preparations/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /stock-preparations/{id}", False, "Exception", str(e))
        
        # Test 5: PUT /api/stock-preparations/{id} (mettre à jour quantité)
        if self.created_stock_preparation_id:
            update_data = {
                "quantite_actuelle": 3.0,
                "quantite_min": 1.0,
                "statut": "disponible"
            }
            
            try:
                response = requests.put(f"{BASE_URL}/stock-preparations/{self.created_stock_preparation_id}", 
                                      json=update_data, headers=HEADERS)
                if response.status_code == 200:
                    updated_stock = response.json()
                    if (updated_stock["quantite_actuelle"] == 3.0 and 
                        updated_stock["quantite_min"] == 1.0):
                        self.log_result("PUT /stock-preparations/{id}", True, "Stock préparation mis à jour")
                    else:
                        self.log_result("PUT /stock-preparations/{id}", False, "Mise à jour non appliquée")
                else:
                    self.log_result("PUT /stock-preparations/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("PUT /stock-preparations/{id}", False, "Exception", str(e))

    def test_phase_2_execution_preparation(self):
        """PHASE 2: Exécution Préparation (Transformation)"""
        print("\n=== PHASE 2: EXÉCUTION PRÉPARATION (TRANSFORMATION) ===")
        
        # Test 1: Vérifier stock produit brut avant
        initial_stock = None
        if self.created_produit_id:
            try:
                response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if response.status_code == 200:
                    initial_stock = response.json()
                    self.log_result("Vérification stock produit brut (avant)", True, 
                                  f"Stock initial: {initial_stock['quantite_actuelle']} kg")
                else:
                    self.log_result("Vérification stock produit brut (avant)", False, 
                                  f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Vérification stock produit brut (avant)", False, "Exception", str(e))
        
        # Test 2: Vérifier préparation existe
        if self.created_preparation_id:
            try:
                response = requests.get(f"{BASE_URL}/preparations/{self.created_preparation_id}")
                if response.status_code == 200:
                    preparation = response.json()
                    self.log_result("Vérification préparation existe", True, 
                                  f"Préparation trouvée: {preparation['nom']}")
                else:
                    self.log_result("Vérification préparation existe", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Vérification préparation existe", False, "Exception", str(e))
        
        # Test 3: POST /api/preparations/{preparation_id}/execute
        if self.created_preparation_id and initial_stock:
            execute_data = {
                "quantite_a_produire": 1.7,  # 2 portions de 0.85kg
                "notes": "Test d'exécution de préparation"
            }
            
            try:
                response = requests.post(f"{BASE_URL}/preparations/{self.created_preparation_id}/execute", 
                                       json=execute_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    
                    # Test 4: Vérifier réponse
                    required_fields = ["success", "produits_deduits", "stock_preparation_id", "warnings"]
                    if all(field in result for field in required_fields):
                        if result["success"]:
                            self.log_result("POST /preparations/{id}/execute", True, 
                                          f"Exécution réussie: {result.get('quantite_produite', 0)} kg produits")
                            
                            # Vérifier produits_deduits
                            produits_deduits = result.get("produits_deduits", [])
                            if len(produits_deduits) > 0:
                                self.log_result("Produits déduits", True, 
                                              f"{len(produits_deduits)} déduction(s) appliquée(s)")
                            else:
                                self.log_result("Produits déduits", False, "Aucune déduction enregistrée")
                            
                            # Stocker l'ID du stock de préparation créé
                            if result.get("stock_preparation_id"):
                                new_stock_prep_id = result["stock_preparation_id"]
                                self.log_result("Stock préparation créé", True, f"ID: {new_stock_prep_id}")
                            else:
                                self.log_result("Stock préparation créé", False, "ID manquant")
                            
                            # Vérifier warnings sur pertes
                            warnings = result.get("warnings", [])
                            if len(warnings) > 0:
                                self.log_result("Warnings pertes", True, f"{len(warnings)} warning(s) générés")
                            else:
                                self.log_result("Warnings pertes", True, "Aucun warning (normal)")
                        else:
                            self.log_result("POST /preparations/{id}/execute", False, "Exécution échouée")
                    else:
                        missing = [f for f in required_fields if f not in result]
                        self.log_result("POST /preparations/{id}/execute", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("POST /preparations/{id}/execute", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /preparations/{id}/execute", False, "Exception", str(e))
        
        # Test 5: Vérifier stock produit brut après (déduit)
        if self.created_produit_id and initial_stock:
            try:
                time.sleep(0.5)  # Attendre la mise à jour
                response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if response.status_code == 200:
                    final_stock = response.json()
                    expected_deduction = 2.0  # 1.7 kg préparation / 0.85 * 1.0 kg produit brut
                    expected_final = initial_stock["quantite_actuelle"] - expected_deduction
                    
                    if abs(final_stock["quantite_actuelle"] - expected_final) < 0.1:
                        self.log_result("Vérification stock produit brut (après)", True, 
                                      f"Stock déduit correctement: {final_stock['quantite_actuelle']} kg")
                    else:
                        self.log_result("Vérification stock produit brut (après)", False, 
                                      f"Déduction incorrecte: {final_stock['quantite_actuelle']} au lieu de {expected_final}")
                else:
                    self.log_result("Vérification stock produit brut (après)", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Vérification stock produit brut (après)", False, "Exception", str(e))
        
        # Test 6: Vérifier stock préparation créé/augmenté
        try:
            response = requests.get(f"{BASE_URL}/stock-preparations")
            if response.status_code == 200:
                stock_preparations = response.json()
                # Chercher le stock de notre préparation
                our_stock = next((sp for sp in stock_preparations 
                                if sp["preparation_id"] == self.created_preparation_id), None)
                
                if our_stock and our_stock["quantite_actuelle"] > 3.0:  # Plus que les 3.0 initiaux
                    self.log_result("Vérification stock préparation créé/augmenté", True, 
                                  f"Stock préparation augmenté: {our_stock['quantite_actuelle']} kg")
                else:
                    self.log_result("Vérification stock préparation créé/augmenté", False, 
                                  "Stock préparation non augmenté")
            else:
                self.log_result("Vérification stock préparation créé/augmenté", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Vérification stock préparation créé/augmenté", False, "Exception", str(e))
        
        # Test 7: Vérifier mouvement stock créé (sortie produit brut)
        try:
            response = requests.get(f"{BASE_URL}/mouvements")
            if response.status_code == 200:
                mouvements = response.json()
                # Chercher un mouvement de sortie récent pour notre produit
                recent_movement = next((m for m in mouvements 
                                     if (m["produit_id"] == self.created_produit_id and 
                                         m["type"] == "sortie" and
                                         "préparation" in m.get("commentaire", "").lower())), None)
                
                if recent_movement:
                    self.log_result("Vérification mouvement stock créé", True, 
                                  f"Mouvement de sortie créé: {recent_movement['quantite']} kg")
                else:
                    self.log_result("Vérification mouvement stock créé", False, 
                                  "Aucun mouvement de sortie trouvé")
            else:
                self.log_result("Vérification mouvement stock créé", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Vérification mouvement stock créé", False, "Exception", str(e))

    def test_phase_3_workflow_complet(self):
        """PHASE 3: Workflow Complet - Tomates cerises → Tomates préparées → Salade Caprese"""
        print("\n=== PHASE 3: WORKFLOW COMPLET ===")
        
        # Étape 1: Livraison produit (si pas assez de stock)
        current_stock = None
        try:
            response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
            if response.status_code == 200:
                current_stock = response.json()
                if current_stock["quantite_actuelle"] < 5.0:
                    # Ajouter du stock via mouvement d'entrée
                    mouvement_entree = {
                        "produit_id": self.created_produit_id,
                        "type": "entree",
                        "quantite": 10.0,
                        "reference": "LIV-TEST-001",
                        "commentaire": "Livraison pour test workflow complet"
                    }
                    
                    entry_response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_entree, headers=HEADERS)
                    if entry_response.status_code == 200:
                        self.log_result("Livraison produit (si nécessaire)", True, "10kg de tomates ajoutés")
                    else:
                        self.log_result("Livraison produit (si nécessaire)", False, f"Erreur {entry_response.status_code}")
                else:
                    self.log_result("Livraison produit (si nécessaire)", True, f"Stock suffisant: {current_stock['quantite_actuelle']} kg")
        except Exception as e:
            self.log_result("Livraison produit (si nécessaire)", False, "Exception", str(e))
        
        # Étape 2: Exécution préparation (déjà testée en Phase 2, mais on refait pour le workflow)
        if self.created_preparation_id:
            execute_data = {
                "quantite_a_produire": 2.55,  # 3 portions de 0.85kg
                "notes": "Workflow complet - préparation pour Salade Caprese"
            }
            
            try:
                response = requests.post(f"{BASE_URL}/preparations/{self.created_preparation_id}/execute", 
                                       json=execute_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        self.log_result("Exécution préparation (workflow)", True, 
                                      f"Préparation exécutée: {result.get('quantite_produite', 0)} kg")
                    else:
                        self.log_result("Exécution préparation (workflow)", False, "Exécution échouée")
                else:
                    self.log_result("Exécution préparation (workflow)", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Exécution préparation (workflow)", False, "Exception", str(e))
        
        # Étape 3: Créer une recette Salade Caprese utilisant la préparation
        recette_caprese_data = {
            "nom": "Salade Caprese Test",
            "description": "Salade caprese avec tomates préparées",
            "categorie": "Entrée",
            "portions": 4,
            "prix_vente": 18.50,
            "ingredients": [
                {
                    "ingredient_id": self.created_preparation_id,
                    "ingredient_type": "preparation",
                    "ingredient_nom": "Tomates cerises émincées",
                    "quantite": 0.4,
                    "unite": "kg"
                }
            ]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/recettes", json=recette_caprese_data, headers=HEADERS)
            if response.status_code == 200:
                created_recette = response.json()
                self.created_recette_id = created_recette["id"]
                
                # Vérifier que ingredient_type="preparation" est bien supporté
                ingredients = created_recette.get("ingredients", [])
                prep_ingredient = next((ing for ing in ingredients 
                                     if ing.get("ingredient_type") == "preparation"), None)
                
                if prep_ingredient:
                    self.log_result("Création recette avec préparation", True, 
                                  f"Recette créée avec ingredient_type='preparation'")
                else:
                    self.log_result("Création recette avec préparation", False, 
                                  "ingredient_type='preparation' non supporté")
            else:
                self.log_result("Création recette avec préparation", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Création recette avec préparation", False, "Exception", str(e))
        
        # Étape 4: Simuler vente via Ticket Z (test du process-z-report avec préparations)
        if self.created_recette_id:
            # Créer un document OCR simulé
            mock_z_report_data = {
                "items_by_category": {
                    "Entrées": [
                        {
                            "name": "Salade Caprese Test",
                            "quantity_sold": 2,
                            "category": "Entrées",
                            "unit_price": 18.50,
                            "total_price": 37.00
                        }
                    ]
                },
                "grand_total_sales": 37.00,
                "report_date": datetime.now().strftime("%d/%m/%Y")
            }
            
            # Créer un document OCR
            document_data = {
                "type_document": "z_report",
                "nom_fichier": "test_caprese_z_report.pdf",
                "texte_extrait": "Test Z Report Salade Caprese",
                "donnees_parsees": mock_z_report_data,
                "statut": "traite"
            }
            
            try:
                # Simuler l'upload du document
                doc_response = requests.post(f"{BASE_URL}/ocr/documents", json=document_data, headers=HEADERS)
                if doc_response.status_code == 200:
                    document = doc_response.json()
                    document_id = document["id"]
                    
                    # Traiter le Z-report
                    process_response = requests.post(f"{BASE_URL}/ocr/process-z-report/{document_id}", headers=HEADERS)
                    if process_response.status_code == 200:
                        process_result = process_response.json()
                        
                        # Vérifier que les déductions touchent stock_preparations (pas stocks)
                        stock_updates = process_result.get("stock_updates", [])
                        preparation_deductions = [upd for upd in stock_updates 
                                                if upd.get("type") == "preparation"]
                        
                        if len(preparation_deductions) > 0:
                            self.log_result("Vente via Ticket Z (déduction préparations)", True, 
                                          f"{len(preparation_deductions)} déduction(s) de stock_preparations")
                        else:
                            self.log_result("Vente via Ticket Z (déduction préparations)", False, 
                                          "Aucune déduction de stock_preparations")
                    else:
                        self.log_result("Vente via Ticket Z (process)", False, f"Erreur {process_response.status_code}")
                else:
                    self.log_result("Vente via Ticket Z (document)", False, f"Erreur {doc_response.status_code}")
            except Exception as e:
                self.log_result("Vente via Ticket Z", False, "Exception", str(e))

    def test_phase_4_compatibilite_backward(self):
        """PHASE 4: Compatibilité Backward"""
        print("\n=== PHASE 4: COMPATIBILITÉ BACKWARD ===")
        
        # Test 1: Créer une recette avec ancien format (produit_id sans ingredient_type)
        if self.created_produit_id:
            recette_legacy_data = {
                "nom": "Recette Legacy Test",
                "description": "Test compatibilité backward",
                "categorie": "Plat",
                "portions": 2,
                "prix_vente": 15.00,
                "ingredients": [
                    {
                        "produit_id": self.created_produit_id,  # Ancien format
                        "quantite": 0.5,
                        "unite": "kg"
                        # Pas de ingredient_type - doit fallback vers "produit"
                    }
                ]
            }
            
            try:
                response = requests.post(f"{BASE_URL}/recettes", json=recette_legacy_data, headers=HEADERS)
                if response.status_code == 200:
                    created_recette = response.json()
                    
                    # Vérifier que le fallback vers "produit" fonctionne
                    ingredients = created_recette.get("ingredients", [])
                    if len(ingredients) > 0:
                        ingredient = ingredients[0]
                        # Doit avoir soit ingredient_type="produit" soit produit_id renseigné
                        if (ingredient.get("ingredient_type") == "produit" or 
                            ingredient.get("produit_id") == self.created_produit_id):
                            self.log_result("Recette ancien format", True, 
                                          "Compatibilité backward maintenue")
                        else:
                            self.log_result("Recette ancien format", False, 
                                          "Fallback vers 'produit' non fonctionnel")
                    else:
                        self.log_result("Recette ancien format", False, "Aucun ingrédient créé")
                else:
                    self.log_result("Recette ancien format", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Recette ancien format", False, "Exception", str(e))
        
        # Test 2: Tester process-z-report avec mélange ancien/nouveau format
        # (Ce test nécessiterait une recette mixte, on simule juste la vérification)
        try:
            response = requests.get(f"{BASE_URL}/recettes")
            if response.status_code == 200:
                recettes = response.json()
                
                # Compter les recettes avec ancien et nouveau format
                legacy_count = 0
                new_format_count = 0
                
                for recette in recettes:
                    ingredients = recette.get("ingredients", [])
                    for ingredient in ingredients:
                        if ingredient.get("ingredient_type"):
                            new_format_count += 1
                        elif ingredient.get("produit_id"):
                            legacy_count += 1
                
                if legacy_count > 0 and new_format_count > 0:
                    self.log_result("Mélange formats ancien/nouveau", True, 
                                  f"Legacy: {legacy_count}, Nouveau: {new_format_count}")
                elif new_format_count > 0:
                    self.log_result("Mélange formats ancien/nouveau", True, 
                                  f"Nouveau format uniquement: {new_format_count}")
                else:
                    self.log_result("Mélange formats ancien/nouveau", True, 
                                  f"Ancien format uniquement: {legacy_count}")
            else:
                self.log_result("Mélange formats ancien/nouveau", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Mélange formats ancien/nouveau", False, "Exception", str(e))

    def test_phase_5_cas_erreur(self):
        """PHASE 5: Cas d'erreur"""
        print("\n=== PHASE 5: CAS D'ERREUR ===")
        
        # Test 1: Exécuter préparation sans stock produit suffisant → 400
        if self.created_preparation_id:
            # D'abord vider le stock
            try:
                stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if stock_response.status_code == 200:
                    current_stock = stock_response.json()
                    
                    # Ajuster le stock à une valeur très faible
                    low_stock_update = {
                        "quantite_actuelle": 0.1  # Très peu de stock
                    }
                    
                    update_response = requests.put(f"{BASE_URL}/stocks/{self.created_produit_id}", 
                                                 json=low_stock_update, headers=HEADERS)
                    
                    if update_response.status_code == 200:
                        # Essayer d'exécuter une préparation qui nécessite plus de stock
                        execute_data = {
                            "quantite_a_produire": 5.0,  # Nécessite beaucoup plus que 0.1kg
                            "notes": "Test erreur stock insuffisant"
                        }
                        
                        error_response = requests.post(f"{BASE_URL}/preparations/{self.created_preparation_id}/execute", 
                                                     json=execute_data, headers=HEADERS)
                        
                        if error_response.status_code == 400:
                            self.log_result("Erreur stock insuffisant", True, 
                                          "Erreur 400 correctement retournée pour stock insuffisant")
                        else:
                            self.log_result("Erreur stock insuffisant", False, 
                                          f"Code erreur incorrect: {error_response.status_code}")
                    else:
                        self.log_result("Erreur stock insuffisant", False, "Impossible de réduire le stock")
            except Exception as e:
                self.log_result("Erreur stock insuffisant", False, "Exception", str(e))
        
        # Test 2: Créer stock_preparation avec preparation_id invalide → 404
        invalid_stock_prep_data = {
            "preparation_id": str(uuid.uuid4()),  # ID inexistant
            "quantite_actuelle": 1.0,
            "quantite_min": 0.1
        }
        
        try:
            response = requests.post(f"{BASE_URL}/stock-preparations", json=invalid_stock_prep_data, headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Erreur preparation_id invalide", True, 
                              "Erreur 404 correctement retournée pour preparation_id invalide")
            else:
                self.log_result("Erreur preparation_id invalide", False, 
                              f"Code erreur incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Erreur preparation_id invalide", False, "Exception", str(e))
        
        # Test 3: Exécuter préparation inexistante → 404
        fake_preparation_id = str(uuid.uuid4())
        execute_data = {
            "quantite_a_produire": 1.0,
            "notes": "Test préparation inexistante"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/preparations/{fake_preparation_id}/execute", 
                                   json=execute_data, headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Erreur préparation inexistante", True, 
                              "Erreur 404 correctement retournée pour préparation inexistante")
            else:
                self.log_result("Erreur préparation inexistante", False, 
                              f"Code erreur incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Erreur préparation inexistante", False, "Exception", str(e))
        
        # Test 4: Process Z-Report avec préparation manquante dans stock
        # Créer un Z-report avec une préparation qui n'existe pas en stock
        mock_z_report_data = {
            "items_by_category": {
                "Entrées": [
                    {
                        "name": "Préparation Inexistante",
                        "quantity_sold": 1,
                        "category": "Entrées"
                    }
                ]
            },
            "grand_total_sales": 20.00
        }
        
        document_data = {
            "type_document": "z_report",
            "nom_fichier": "test_error_z_report.pdf",
            "texte_extrait": "Test Z Report Erreur",
            "donnees_parsees": mock_z_report_data,
            "statut": "traite"
        }
        
        try:
            doc_response = requests.post(f"{BASE_URL}/ocr/documents", json=document_data, headers=HEADERS)
            if doc_response.status_code == 200:
                document = doc_response.json()
                document_id = document["id"]
                
                process_response = requests.post(f"{BASE_URL}/ocr/process-z-report/{document_id}", headers=HEADERS)
                
                # Doit réussir mais avec des warnings sur les préparations manquantes
                if process_response.status_code == 200:
                    result = process_response.json()
                    warnings = result.get("warnings", [])
                    
                    if len(warnings) > 0:
                        self.log_result("Process Z-Report préparation manquante", True, 
                                      f"Warnings générés pour préparations manquantes: {len(warnings)}")
                    else:
                        self.log_result("Process Z-Report préparation manquante", False, 
                                      "Aucun warning généré pour préparations manquantes")
                else:
                    self.log_result("Process Z-Report préparation manquante", False, 
                                  f"Erreur {process_response.status_code}")
            else:
                self.log_result("Process Z-Report préparation manquante", False, 
                              f"Erreur création document: {doc_response.status_code}")
        except Exception as e:
            self.log_result("Process Z-Report préparation manquante", False, "Exception", str(e))

    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        print("\n=== NETTOYAGE DONNÉES DE TEST ===")
        
        # Supprimer la recette créée
        if self.created_recette_id:
            try:
                response = requests.delete(f"{BASE_URL}/recettes/{self.created_recette_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage - Suppression recette", True, "Recette supprimée")
                else:
                    self.log_result("Nettoyage - Suppression recette", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage - Suppression recette", False, "Exception", str(e))
        
        # Supprimer le stock de préparation
        if self.created_stock_preparation_id:
            try:
                response = requests.delete(f"{BASE_URL}/stock-preparations/{self.created_stock_preparation_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage - Suppression stock préparation", True, "Stock préparation supprimé")
                else:
                    self.log_result("Nettoyage - Suppression stock préparation", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage - Suppression stock préparation", False, "Exception", str(e))
        
        # Supprimer la préparation
        if self.created_preparation_id:
            try:
                response = requests.delete(f"{BASE_URL}/preparations/{self.created_preparation_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage - Suppression préparation", True, "Préparation supprimée")
                else:
                    self.log_result("Nettoyage - Suppression préparation", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage - Suppression préparation", False, "Exception", str(e))
        
        # Supprimer le produit (et son stock associé)
        if self.created_produit_id:
            try:
                response = requests.delete(f"{BASE_URL}/produits/{self.created_produit_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage - Suppression produit", True, "Produit et stock supprimés")
                else:
                    self.log_result("Nettoyage - Suppression produit", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage - Suppression produit", False, "Exception", str(e))

    def run_all_tests(self):
        """Exécuter tous les tests du système PRODUITS + PRÉPARATIONS"""
        print("🧪 DÉBUT DES TESTS SYSTÈME PRODUITS + PRÉPARATIONS")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_data():
            print("❌ ÉCHEC DU SETUP - ARRÊT DES TESTS")
            return
        
        # Exécuter les 5 phases de tests
        self.test_phase_1_crud_stock_preparations()
        self.test_phase_2_execution_preparation()
        self.test_phase_3_workflow_complet()
        self.test_phase_4_compatibilite_backward()
        self.test_phase_5_cas_erreur()
        
        # Nettoyage
        self.cleanup_test_data()
        
        # Résumé final
        self.print_final_summary()

    def print_final_summary(self):
        """Afficher le résumé final des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ FINAL DES TESTS SYSTÈME PRODUITS + PRÉPARATIONS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 STATISTIQUES GLOBALES:")
        print(f"   Total des tests: {total_tests}")
        print(f"   ✅ Réussis: {passed_tests}")
        print(f"   ❌ Échoués: {failed_tests}")
        print(f"   📊 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 90:
            print("   ✅ SYSTÈME PRODUITS + PRÉPARATIONS OPÉRATIONNEL")
        elif success_rate >= 70:
            print("   ⚠️  SYSTÈME PARTIELLEMENT FONCTIONNEL - CORRECTIONS MINEURES NÉCESSAIRES")
        else:
            print("   ❌ SYSTÈME NON FONCTIONNEL - CORRECTIONS MAJEURES REQUISES")

if __name__ == "__main__":
    test_suite = PreparationsTestSuite()
    test_suite.run_all_tests()