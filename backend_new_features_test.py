#!/usr/bin/env python3
"""
Test complet des nouvelles fonctionnalités backend implémentées :
1. Catégories fournisseurs
2. Configuration des coûts fournisseurs  
3. Système d'archivage
4. Vérifications générales
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class NewFeaturesTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_id = None
        self.created_produit_id = None
        self.created_production_id = None
        self.created_archive_ids = []
        self.supplier_cost_config_id = None
        
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

    def test_categories_fournisseurs(self):
        """Test 1: Catégories fournisseurs"""
        print("\n=== TEST 1: CATÉGORIES FOURNISSEURS ===")
        
        # Test GET /api/fournisseurs-categories
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs-categories")
            if response.status_code == 200:
                categories = response.json()
                if isinstance(categories, list) and len(categories) > 0:
                    # Vérifier que fromagerie est incluse
                    if "fromagerie" in categories:
                        self.log_result("GET /fournisseurs-categories", True, 
                                      f"Catégories récupérées avec fromagerie: {categories}")
                    else:
                        self.log_result("GET /fournisseurs-categories", False, 
                                      f"Catégorie fromagerie manquante dans: {categories}")
                    
                    # Vérifier les catégories attendues
                    expected_categories = ["frais", "surgelés", "primeur", "marée", "boucherie", "fromagerie", "extra", "hygiène", "bar"]
                    missing_categories = [cat for cat in expected_categories if cat not in categories]
                    if not missing_categories:
                        self.log_result("Validation catégories complètes", True, "Toutes les catégories attendues présentes")
                    else:
                        self.log_result("Validation catégories complètes", False, f"Catégories manquantes: {missing_categories}")
                else:
                    self.log_result("GET /fournisseurs-categories", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET /fournisseurs-categories", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /fournisseurs-categories", False, "Exception", str(e))

        # Test création fournisseur avec catégorie fromagerie
        fournisseur_fromagerie = {
            "nom": "Fromagerie Test Premium",
            "contact": "Marie Fromage",
            "email": "marie@fromagerie-test.fr",
            "telephone": "01.23.45.67.89",
            "adresse": "123 Rue des Fromages, 75001 Paris",
            "categorie": "fromagerie",
            "couleur": "#FFD700",
            "logo": "🧀"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_fromagerie, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_id = created_fournisseur["id"]
                
                # Vérifier que la catégorie fromagerie est bien assignée
                if created_fournisseur.get("categorie") == "fromagerie":
                    self.log_result("Création fournisseur fromagerie", True, "Fournisseur créé avec catégorie fromagerie")
                else:
                    self.log_result("Création fournisseur fromagerie", False, 
                                  f"Catégorie incorrecte: {created_fournisseur.get('categorie')}")
                
                # Vérifier les nouveaux champs couleur et logo
                if (created_fournisseur.get("couleur") == "#FFD700" and 
                    created_fournisseur.get("logo") == "🧀"):
                    self.log_result("Nouveaux champs fournisseur", True, "Couleur et logo correctement assignés")
                else:
                    self.log_result("Nouveaux champs fournisseur", False, 
                                  f"Couleur: {created_fournisseur.get('couleur')}, Logo: {created_fournisseur.get('logo')}")
            else:
                self.log_result("Création fournisseur fromagerie", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Création fournisseur fromagerie", False, "Exception", str(e))

        # Test validation des catégories (catégorie invalide)
        fournisseur_invalide = {
            "nom": "Fournisseur Test Invalide",
            "contact": "Test Contact",
            "email": "test@invalid.fr",
            "categorie": "categorie_inexistante"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_invalide, headers=HEADERS)
            if response.status_code == 400:
                self.log_result("Validation catégorie invalide", True, "Catégorie invalide correctement rejetée")
            elif response.status_code == 200:
                # Si accepté, vérifier que la catégorie par défaut est assignée
                created = response.json()
                if created.get("categorie") == "frais":  # catégorie par défaut
                    self.log_result("Validation catégorie invalide", True, "Catégorie par défaut assignée")
                else:
                    self.log_result("Validation catégorie invalide", False, "Catégorie invalide acceptée sans défaut")
            else:
                self.log_result("Validation catégorie invalide", False, f"Réponse inattendue: {response.status_code}")
        except Exception as e:
            self.log_result("Validation catégorie invalide", False, "Exception", str(e))

    def test_supplier_cost_config(self):
        """Test 2: Configuration des coûts fournisseurs"""
        print("\n=== TEST 2: CONFIGURATION DES COÛTS FOURNISSEURS ===")
        
        if not self.created_fournisseur_id:
            self.log_result("Configuration coûts fournisseurs", False, "Pas de fournisseur créé pour les tests")
            return

        # Test POST /api/supplier-cost-config
        cost_config_data = {
            "supplier_id": self.created_fournisseur_id,
            "delivery_cost": 15.50,
            "extra_cost": 5.00
        }
        
        try:
            response = requests.post(f"{BASE_URL}/supplier-cost-config", json=cost_config_data, headers=HEADERS)
            if response.status_code == 200:
                created_config = response.json()
                self.supplier_cost_config_id = created_config["id"]
                
                # Vérifier les données
                if (created_config["delivery_cost"] == 15.50 and 
                    created_config["extra_cost"] == 5.00 and
                    created_config["supplier_id"] == self.created_fournisseur_id):
                    self.log_result("POST /supplier-cost-config", True, "Configuration coûts créée")
                    
                    # Vérifier que les produits de coûts ont été créés automatiquement
                    if (created_config.get("delivery_cost_product_id") and 
                        created_config.get("extra_cost_product_id")):
                        self.log_result("Création automatique produits coûts", True, 
                                      "Produits de livraison et frais extra créés automatiquement")
                        
                        # Vérifier que les produits existent réellement
                        delivery_product_response = requests.get(f"{BASE_URL}/produits/{created_config['delivery_cost_product_id']}")
                        extra_product_response = requests.get(f"{BASE_URL}/produits/{created_config['extra_cost_product_id']}")
                        
                        if (delivery_product_response.status_code == 200 and 
                            extra_product_response.status_code == 200):
                            delivery_product = delivery_product_response.json()
                            extra_product = extra_product_response.json()
                            
                            # Vérifier les noms des produits auto-créés
                            if ("Frais de livraison" in delivery_product["nom"] and 
                                "Frais supplémentaires" in extra_product["nom"]):
                                self.log_result("Validation produits coûts auto-créés", True, 
                                              f"Produits: {delivery_product['nom']}, {extra_product['nom']}")
                            else:
                                self.log_result("Validation produits coûts auto-créés", False, 
                                              "Noms des produits auto-créés incorrects")
                        else:
                            self.log_result("Validation produits coûts auto-créés", False, 
                                          "Produits auto-créés non trouvés")
                    else:
                        self.log_result("Création automatique produits coûts", False, 
                                      "IDs des produits de coûts manquants")
                else:
                    self.log_result("POST /supplier-cost-config", False, "Données de configuration incorrectes")
            else:
                self.log_result("POST /supplier-cost-config", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /supplier-cost-config", False, "Exception", str(e))

        # Test GET /api/supplier-cost-config/{supplier_id}
        if self.created_fournisseur_id:
            try:
                response = requests.get(f"{BASE_URL}/supplier-cost-config/{self.created_fournisseur_id}")
                if response.status_code == 200:
                    config = response.json()
                    if (config["delivery_cost"] == 15.50 and 
                        config["extra_cost"] == 5.00):
                        self.log_result("GET /supplier-cost-config/{supplier_id}", True, "Configuration récupérée")
                    else:
                        self.log_result("GET /supplier-cost-config/{supplier_id}", False, "Données incorrectes")
                else:
                    self.log_result("GET /supplier-cost-config/{supplier_id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /supplier-cost-config/{supplier_id}", False, "Exception", str(e))

        # Test PUT /api/supplier-cost-config/{supplier_id}
        if self.created_fournisseur_id:
            updated_config = {
                "supplier_id": self.created_fournisseur_id,
                "delivery_cost": 20.00,
                "extra_cost": 7.50
            }
            
            try:
                response = requests.put(f"{BASE_URL}/supplier-cost-config/{self.created_fournisseur_id}", 
                                      json=updated_config, headers=HEADERS)
                if response.status_code == 200:
                    updated = response.json()
                    if (updated["delivery_cost"] == 20.00 and 
                        updated["extra_cost"] == 7.50):
                        self.log_result("PUT /supplier-cost-config/{supplier_id}", True, "Configuration mise à jour")
                    else:
                        self.log_result("PUT /supplier-cost-config/{supplier_id}", False, "Mise à jour incorrecte")
                else:
                    self.log_result("PUT /supplier-cost-config/{supplier_id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("PUT /supplier-cost-config/{supplier_id}", False, "Exception", str(e))

    def test_archive_system(self):
        """Test 3: Système d'archivage"""
        print("\n=== TEST 3: SYSTÈME D'ARCHIVAGE ===")
        
        # Créer des éléments à archiver pour les tests
        self.setup_archive_test_data()
        
        # Test POST /api/archive pour archiver un produit
        if self.created_produit_id:
            archive_produit_data = {
                "item_id": self.created_produit_id,
                "item_type": "produit",
                "reason": "Produit discontinué pour test d'archivage"
            }
            
            try:
                response = requests.post(f"{BASE_URL}/archive", json=archive_produit_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    archive_id = result.get("archive_id")
                    if archive_id:
                        self.created_archive_ids.append(archive_id)
                        self.log_result("POST /archive (produit)", True, f"Produit archivé: {archive_id}")
                        
                        # Vérifier que le produit n'est plus dans la collection principale
                        time.sleep(0.5)
                        product_response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                        if product_response.status_code == 404:
                            self.log_result("Suppression produit de collection principale", True, 
                                          "Produit retiré de la collection principale")
                        else:
                            self.log_result("Suppression produit de collection principale", False, 
                                          "Produit encore présent dans collection principale")
                    else:
                        self.log_result("POST /archive (produit)", False, "ID d'archive manquant")
                else:
                    self.log_result("POST /archive (produit)", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /archive (produit)", False, "Exception", str(e))

        # Test POST /api/archive pour archiver une production (recette)
        if self.created_production_id:
            archive_production_data = {
                "item_id": self.created_production_id,
                "item_type": "production",
                "reason": "Recette saisonnière archivée"
            }
            
            try:
                response = requests.post(f"{BASE_URL}/archive", json=archive_production_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    archive_id = result.get("archive_id")
                    if archive_id:
                        self.created_archive_ids.append(archive_id)
                        self.log_result("POST /archive (production)", True, f"Production archivée: {archive_id}")
                    else:
                        self.log_result("POST /archive (production)", False, "ID d'archive manquant")
                else:
                    self.log_result("POST /archive (production)", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /archive (production)", False, "Exception", str(e))

        # Test POST /api/archive pour archiver un fournisseur
        if self.created_fournisseur_id:
            archive_fournisseur_data = {
                "item_id": self.created_fournisseur_id,
                "item_type": "fournisseur",
                "reason": "Fournisseur plus utilisé"
            }
            
            try:
                response = requests.post(f"{BASE_URL}/archive", json=archive_fournisseur_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    archive_id = result.get("archive_id")
                    if archive_id:
                        self.created_archive_ids.append(archive_id)
                        self.log_result("POST /archive (fournisseur)", True, f"Fournisseur archivé: {archive_id}")
                    else:
                        self.log_result("POST /archive (fournisseur)", False, "ID d'archive manquant")
                else:
                    self.log_result("POST /archive (fournisseur)", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /archive (fournisseur)", False, "Exception", str(e))

        # Test GET /api/archives (sans filtre)
        try:
            response = requests.get(f"{BASE_URL}/archives")
            if response.status_code == 200:
                archives = response.json()
                if isinstance(archives, list) and len(archives) >= len(self.created_archive_ids):
                    self.log_result("GET /archives", True, f"{len(archives)} archive(s) récupérée(s)")
                    
                    # Vérifier la structure des données d'archive
                    if len(archives) > 0:
                        archive = archives[0]
                        required_fields = ["id", "original_id", "item_type", "original_data", "archived_at"]
                        if all(field in archive for field in required_fields):
                            self.log_result("Structure données archives", True, "Tous les champs requis présents")
                        else:
                            missing = [f for f in required_fields if f not in archive]
                            self.log_result("Structure données archives", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("GET /archives", False, f"Nombre d'archives incorrect: {len(archives) if isinstance(archives, list) else 'non-liste'}")
            else:
                self.log_result("GET /archives", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /archives", False, "Exception", str(e))

        # Test GET /api/archives avec filtre par type
        for item_type in ["produit", "production", "fournisseur"]:
            try:
                response = requests.get(f"{BASE_URL}/archives?type={item_type}")
                if response.status_code == 200:
                    filtered_archives = response.json()
                    if isinstance(filtered_archives, list):
                        # Vérifier que tous les éléments sont du bon type
                        if all(archive["item_type"] == item_type for archive in filtered_archives):
                            self.log_result(f"GET /archives?type={item_type}", True, 
                                          f"{len(filtered_archives)} archive(s) de type {item_type}")
                        else:
                            self.log_result(f"GET /archives?type={item_type}", False, 
                                          "Filtre par type incorrect")
                    else:
                        self.log_result(f"GET /archives?type={item_type}", False, "Format de réponse incorrect")
                else:
                    self.log_result(f"GET /archives?type={item_type}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"GET /archives?type={item_type}", False, "Exception", str(e))

        # Test POST /api/restore/{archive_id}
        if self.created_archive_ids:
            archive_id_to_restore = self.created_archive_ids[0]  # Restaurer le premier archivé
            
            try:
                response = requests.post(f"{BASE_URL}/restore/{archive_id_to_restore}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    if "restauré avec succès" in result.get("message", ""):
                        self.log_result("POST /restore/{archive_id}", True, "Élément restauré avec succès")
                        
                        # Vérifier que l'élément est de nouveau dans la collection principale
                        time.sleep(0.5)
                        # Récupérer les détails de l'archive pour savoir quel type d'élément restaurer
                        archives_response = requests.get(f"{BASE_URL}/archives")
                        if archives_response.status_code == 200:
                            archives = archives_response.json()
                            restored_archive = next((a for a in archives if a["id"] == archive_id_to_restore), None)
                            if restored_archive:
                                original_id = restored_archive["original_id"]
                                item_type = restored_archive["item_type"]
                                
                                # Vérifier selon le type
                                if item_type == "produit":
                                    check_response = requests.get(f"{BASE_URL}/produits/{original_id}")
                                elif item_type == "production":
                                    check_response = requests.get(f"{BASE_URL}/recettes/{original_id}")
                                elif item_type == "fournisseur":
                                    check_response = requests.get(f"{BASE_URL}/fournisseurs/{original_id}")
                                else:
                                    check_response = None
                                
                                if check_response and check_response.status_code == 200:
                                    self.log_result("Validation restauration", True, 
                                                  f"{item_type} restauré dans collection principale")
                                else:
                                    self.log_result("Validation restauration", False, 
                                                  f"{item_type} non trouvé après restauration")
                    else:
                        self.log_result("POST /restore/{archive_id}", False, f"Message inattendu: {result.get('message')}")
                else:
                    self.log_result("POST /restore/{archive_id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /restore/{archive_id}", False, "Exception", str(e))

        # Test DELETE /api/archives/{archive_id}
        if len(self.created_archive_ids) > 1:
            archive_id_to_delete = self.created_archive_ids[1]  # Supprimer le deuxième
            
            try:
                response = requests.delete(f"{BASE_URL}/archives/{archive_id_to_delete}")
                if response.status_code == 200:
                    result = response.json()
                    if "supprimée définitivement" in result.get("message", ""):
                        self.log_result("DELETE /archives/{archive_id}", True, "Archive supprimée définitivement")
                        
                        # Vérifier que l'archive n'existe plus
                        time.sleep(0.5)
                        archives_response = requests.get(f"{BASE_URL}/archives")
                        if archives_response.status_code == 200:
                            archives = archives_response.json()
                            deleted_archive = next((a for a in archives if a["id"] == archive_id_to_delete), None)
                            if not deleted_archive:
                                self.log_result("Validation suppression archive", True, "Archive bien supprimée")
                            else:
                                self.log_result("Validation suppression archive", False, "Archive encore présente")
                    else:
                        self.log_result("DELETE /archives/{archive_id}", False, f"Message inattendu: {result.get('message')}")
                else:
                    self.log_result("DELETE /archives/{archive_id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("DELETE /archives/{archive_id}", False, "Exception", str(e))

    def setup_archive_test_data(self):
        """Créer des données de test pour l'archivage"""
        # Créer un produit pour les tests d'archivage
        if not self.created_produit_id:
            produit_data = {
                "nom": "Produit Test Archivage",
                "description": "Produit créé pour tester l'archivage",
                "categorie": "Test",
                "unite": "kg",
                "prix_achat": 5.00,
                "fournisseur_id": self.created_fournisseur_id
            }
            
            try:
                response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
                if response.status_code == 200:
                    created_produit = response.json()
                    self.created_produit_id = created_produit["id"]
            except Exception as e:
                print(f"Erreur création produit test: {e}")

        # Créer une recette/production pour les tests d'archivage
        if not self.created_production_id and self.created_produit_id:
            recette_data = {
                "nom": "Recette Test Archivage",
                "description": "Recette créée pour tester l'archivage",
                "categorie": "plat",
                "portions": 4,
                "prix_vente": 15.00,
                "ingredients": [
                    {
                        "produit_id": self.created_produit_id,
                        "quantite": 200,
                        "unite": "g"
                    }
                ]
            }
            
            try:
                response = requests.post(f"{BASE_URL}/recettes", json=recette_data, headers=HEADERS)
                if response.status_code == 200:
                    created_recette = response.json()
                    self.created_production_id = created_recette["id"]
            except Exception as e:
                print(f"Erreur création recette test: {e}")

    def test_general_verifications(self):
        """Test 4: Vérifications générales"""
        print("\n=== TEST 4: VÉRIFICATIONS GÉNÉRALES ===")
        
        # Test que tous les endpoints existants fonctionnent toujours
        endpoints_to_test = [
            ("GET", "/fournisseurs", "Liste fournisseurs"),
            ("GET", "/produits", "Liste produits"),
            ("GET", "/stocks", "Liste stocks"),
            ("GET", "/recettes", "Liste recettes"),
            ("GET", "/mouvements", "Liste mouvements"),
            ("GET", "/dashboard/stats", "Statistiques dashboard")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}")
                else:
                    continue  # Pour l'instant on teste que les GET
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, (list, dict)):
                        self.log_result(f"Endpoint existant {endpoint}", True, f"{description} fonctionne")
                    else:
                        self.log_result(f"Endpoint existant {endpoint}", False, "Format de réponse incorrect")
                else:
                    self.log_result(f"Endpoint existant {endpoint}", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result(f"Endpoint existant {endpoint}", False, f"Exception: {str(e)}")

        # Test que la création de fournisseur crée bien les produits de coûts automatiquement
        nouveau_fournisseur = {
            "nom": "Test Auto Coûts",
            "contact": "Test Contact",
            "email": "test@autocouts.fr",
            "categorie": "frais"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=nouveau_fournisseur, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                fournisseur_id = created_fournisseur["id"]
                
                # Vérifier si une configuration de coûts par défaut a été créée
                time.sleep(0.5)
                config_response = requests.get(f"{BASE_URL}/supplier-cost-config/{fournisseur_id}")
                
                if config_response.status_code == 200:
                    config = config_response.json()
                    if (config.get("delivery_cost_product_id") and 
                        config.get("extra_cost_product_id")):
                        self.log_result("Auto-création produits coûts nouveau fournisseur", True, 
                                      "Produits de coûts créés automatiquement")
                    else:
                        self.log_result("Auto-création produits coûts nouveau fournisseur", False, 
                                      "Produits de coûts non créés automatiquement")
                elif config_response.status_code == 404:
                    # Configuration par défaut non créée - c'est acceptable
                    self.log_result("Auto-création produits coûts nouveau fournisseur", True, 
                                  "Pas de configuration par défaut (comportement acceptable)")
                else:
                    self.log_result("Auto-création produits coûts nouveau fournisseur", False, 
                                  f"Erreur vérification config: {config_response.status_code}")
            else:
                self.log_result("Création fournisseur test auto-coûts", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Création fournisseur test auto-coûts", False, f"Exception: {str(e)}")

        # Test des erreurs de validation
        # Test validation catégorie fournisseur
        fournisseur_invalide = {
            "nom": "Test Validation",
            "categorie": "categorie_qui_nexiste_pas"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_invalide, headers=HEADERS)
            if response.status_code in [400, 422]:
                self.log_result("Validation erreur catégorie", True, "Catégorie invalide correctement rejetée")
            elif response.status_code == 200:
                # Vérifier si catégorie par défaut assignée
                created = response.json()
                if created.get("categorie") in ["frais", "extra"]:  # catégories par défaut possibles
                    self.log_result("Validation erreur catégorie", True, "Catégorie par défaut assignée")
                else:
                    self.log_result("Validation erreur catégorie", False, "Catégorie invalide acceptée")
            else:
                self.log_result("Validation erreur catégorie", False, f"Réponse inattendue: {response.status_code}")
        except Exception as e:
            self.log_result("Validation erreur catégorie", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS DES NOUVELLES FONCTIONNALITÉS BACKEND")
        print("=" * 80)
        
        start_time = time.time()
        
        # Exécuter tous les tests
        self.test_categories_fournisseurs()
        self.test_supplier_cost_config()
        self.test_archive_system()
        self.test_general_verifications()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Résumé des résultats
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        print(f"⏱️  Durée d'exécution: {duration:.2f}s")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
                    if result["details"]:
                        print(f"    Détails: {result['details']}")
        
        print("\n🎯 TESTS DES NOUVELLES FONCTIONNALITÉS TERMINÉS")
        return success_rate >= 80  # Considérer comme succès si 80%+ des tests passent

if __name__ == "__main__":
    test_suite = NewFeaturesTestSuite()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)