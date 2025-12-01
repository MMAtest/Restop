#!/usr/bin/env python3
"""
Test complet des nouvelles fonctionnalités Version 3 du backend ResTop
Tests des APIs: Migration V3, User Management RBAC, Supplier-Product Relations, 
Product Batch Management, Price Anomaly Alerts
"""

import requests
import json
from datetime import datetime, timedelta
import time
import os

# Configuration
BASE_URL = "https://rest-mgmt-sys.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class V3TestSuite:
    def __init__(self):
        self.test_results = []
        self.created_user_id = None
        self.created_supplier_id = None
        self.created_product_id = None
        self.created_batch_id = None
        self.created_alert_id = None
        
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
    
    def test_migration_v3(self):
        """Test migration vers Version 3"""
        print("\n=== TEST MIGRATION VERSION 3 ===")
        
        try:
            response = requests.post(f"{BASE_URL}/admin/migrate/v3", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                if "Migration to Version 3.0.0 completed successfully" in result.get("message", "") or \
                   "Migration 3.0.0 already applied" in result.get("message", ""):
                    self.log_result("POST /admin/migrate/v3", True, 
                                  f"Migration réussie: {result.get('message', '')}")
                    
                    # Vérifier les détails de migration
                    if "details" in result:
                        details = result["details"]
                        if isinstance(details, list) and len(details) > 0:
                            self.log_result("Migration details", True, 
                                          f"Migration avec {len(details)} étapes: {', '.join(details[:3])}")
                        else:
                            self.log_result("Migration details", True, "Migration déjà appliquée")
                    else:
                        self.log_result("Migration details", True, "Migration déjà appliquée")
                else:
                    self.log_result("POST /admin/migrate/v3", False, f"Message inattendu: {result.get('message')}")
            else:
                self.log_result("POST /admin/migrate/v3", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /admin/migrate/v3", False, "Exception lors de la migration", str(e))
    
    def test_user_management_rbac(self):
        """Test système de gestion des utilisateurs avec RBAC"""
        print("\n=== TEST USER MANAGEMENT RBAC ===")
        
        # Test POST - Création utilisateur avec rôle
        user_data = {
            "username": "chef_test_v3",
            "email": "chef.test@la-table-augustine.fr",
            "password": "ChefPassword2025!",
            "role": "chef_cuisine",
            "full_name": "Chef de Cuisine Test"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/admin/users", json=user_data, headers=HEADERS)
            if response.status_code == 200:
                created_user = response.json()
                self.created_user_id = created_user["id"]
                
                # Vérifier la structure de réponse
                required_fields = ["id", "username", "email", "role", "full_name", "is_active", "created_at"]
                if all(field in created_user for field in required_fields):
                    if created_user["role"] == "chef_cuisine" and created_user["is_active"]:
                        self.log_result("POST /admin/users", True, 
                                      f"Utilisateur créé avec rôle {created_user['role']}")
                    else:
                        self.log_result("POST /admin/users", False, "Rôle ou statut incorrect")
                else:
                    missing = [f for f in required_fields if f not in created_user]
                    self.log_result("POST /admin/users", False, f"Champs manquants: {missing}")
            else:
                self.log_result("POST /admin/users", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /admin/users", False, "Exception lors de la création", str(e))
            return
        
        # Test validation des rôles - Rôle invalide
        invalid_user_data = user_data.copy()
        invalid_user_data["username"] = "invalid_role_user"
        invalid_user_data["email"] = "invalid@test.fr"
        invalid_user_data["role"] = "invalid_role"
        
        try:
            response = requests.post(f"{BASE_URL}/admin/users", json=invalid_user_data, headers=HEADERS)
            if response.status_code == 400:
                self.log_result("Validation rôle invalide", True, "Rôle invalide correctement rejeté")
            else:
                self.log_result("Validation rôle invalide", False, f"Rôle invalide accepté: {response.status_code}")
        except Exception as e:
            self.log_result("Validation rôle invalide", False, "Exception", str(e))
        
        # Test GET - Liste des utilisateurs
        try:
            response = requests.get(f"{BASE_URL}/admin/users")
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list) and len(users) > 0:
                    self.log_result("GET /admin/users", True, f"{len(users)} utilisateur(s) récupéré(s)")
                    
                    # Vérifier qu'on trouve notre utilisateur créé
                    created_user_found = any(u["id"] == self.created_user_id for u in users)
                    if created_user_found:
                        self.log_result("Utilisateur dans liste", True, "Utilisateur créé trouvé dans la liste")
                    else:
                        self.log_result("Utilisateur dans liste", False, "Utilisateur créé non trouvé")
                else:
                    self.log_result("GET /admin/users", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET /admin/users", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /admin/users", False, "Exception", str(e))
        
        # Test des différents rôles RBAC
        roles_to_test = [
            ("super_admin", "Super Admin"),
            ("gerant", "Gérant Manager"),
            ("barman", "Barman Bartender"),
            ("caissier", "Caissier Cashier")
        ]
        
        for role_key, role_description in roles_to_test:
            test_user_data = {
                "username": f"test_{role_key}",
                "email": f"{role_key}@la-table-augustine.fr",
                "password": "TestPassword2025!",
                "role": role_key,
                "full_name": f"Test {role_description}"
            }
            
            try:
                response = requests.post(f"{BASE_URL}/admin/users", json=test_user_data, headers=HEADERS)
                if response.status_code == 200:
                    user = response.json()
                    if user["role"] == role_key:
                        self.log_result(f"Création rôle {role_key}", True, f"Utilisateur {role_key} créé")
                    else:
                        self.log_result(f"Création rôle {role_key}", False, "Rôle incorrect")
                else:
                    self.log_result(f"Création rôle {role_key}", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result(f"Création rôle {role_key}", False, "Exception", str(e))
    
    def test_enhanced_product_model(self):
        """Test modèle Product amélioré avec reference_price et relations fournisseurs"""
        print("\n=== TEST ENHANCED PRODUCT MODEL ===")
        
        # D'abord créer un fournisseur pour les tests
        supplier_data = {
            "nom": "Fournisseur Test V3",
            "contact": "Contact V3",
            "email": "v3@test.fr",
            "telephone": "01.23.45.67.89"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=supplier_data, headers=HEADERS)
            if response.status_code == 200:
                supplier = response.json()
                self.created_supplier_id = supplier["id"]
                self.log_result("Création fournisseur pour tests V3", True, "Fournisseur créé")
            else:
                self.log_result("Création fournisseur pour tests V3", False, f"Erreur {response.status_code}")
                return
        except Exception as e:
            self.log_result("Création fournisseur pour tests V3", False, "Exception", str(e))
            return
        
        # Test création produit avec nouveau modèle V3
        enhanced_product_data = {
            "nom": "Produit Enhanced V3",
            "description": "Produit avec modèle V3 amélioré",
            "categorie": "Test V3",
            "unite": "kg",
            "reference_price": 25.50,  # Nouveau champ V3
            "main_supplier_id": self.created_supplier_id,  # Nouveau champ V3
            "secondary_supplier_ids": [],  # Nouveau champ V3
            # Champs legacy pour compatibilité
            "prix_achat": 24.00,
            "fournisseur_id": self.created_supplier_id
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=enhanced_product_data, headers=HEADERS)
            if response.status_code == 200:
                created_product = response.json()
                self.created_product_id = created_product["id"]
                
                # Vérifier les nouveaux champs V3
                v3_fields = ["reference_price", "main_supplier_id", "secondary_supplier_ids"]
                if all(field in created_product for field in v3_fields):
                    if (created_product["reference_price"] == 25.50 and 
                        created_product["main_supplier_id"] == self.created_supplier_id):
                        self.log_result("POST /produits (V3 enhanced)", True, 
                                      f"Produit V3 créé avec reference_price: {created_product['reference_price']}€")
                    else:
                        self.log_result("POST /produits (V3 enhanced)", False, "Valeurs V3 incorrectes")
                else:
                    missing = [f for f in v3_fields if f not in created_product]
                    self.log_result("POST /produits (V3 enhanced)", False, f"Champs V3 manquants: {missing}")
                
                # Vérifier la compatibilité backward
                legacy_fields = ["prix_achat", "fournisseur_id", "fournisseur_nom"]
                legacy_present = [f for f in legacy_fields if f in created_product]
                if len(legacy_present) >= 2:  # Au moins prix_achat et fournisseur_id
                    self.log_result("Backward compatibility", True, f"Champs legacy présents: {legacy_present}")
                else:
                    self.log_result("Backward compatibility", False, "Champs legacy manquants")
            else:
                self.log_result("POST /produits (V3 enhanced)", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /produits (V3 enhanced)", False, "Exception", str(e))
            return
    
    def test_supplier_product_relations(self):
        """Test relations Supplier-Product avec pricing spécifique"""
        print("\n=== TEST SUPPLIER-PRODUCT RELATIONS ===")
        
        if not self.created_supplier_id or not self.created_product_id:
            self.log_result("Supplier-Product Relations", False, "Pas de fournisseur/produit pour les tests")
            return
        
        # Test POST - Création relation supplier-product
        supplier_product_data = {
            "supplier_id": self.created_supplier_id,
            "product_id": self.created_product_id,
            "price": 23.75,
            "is_preferred": True,
            "min_order_quantity": 10.0,
            "lead_time_days": 3
        }
        
        try:
            response = requests.post(f"{BASE_URL}/supplier-product-info", json=supplier_product_data, headers=HEADERS)
            if response.status_code == 200:
                relation = response.json()
                
                # Vérifier la structure de réponse
                required_fields = ["id", "supplier_id", "product_id", "price", "is_preferred", "created_at"]
                if all(field in relation for field in required_fields):
                    if (relation["price"] == 23.75 and relation["is_preferred"] == True):
                        self.log_result("POST /supplier-product-info", True, 
                                      f"Relation créée: prix {relation['price']}€, préféré: {relation['is_preferred']}")
                    else:
                        self.log_result("POST /supplier-product-info", False, "Valeurs incorrectes")
                else:
                    missing = [f for f in required_fields if f not in relation]
                    self.log_result("POST /supplier-product-info", False, f"Champs manquants: {missing}")
            else:
                self.log_result("POST /supplier-product-info", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /supplier-product-info", False, "Exception", str(e))
            return
        
        # Test validation - Relation déjà existante
        try:
            response = requests.post(f"{BASE_URL}/supplier-product-info", json=supplier_product_data, headers=HEADERS)
            if response.status_code == 400:
                self.log_result("Validation relation existante", True, "Relation dupliquée correctement rejetée")
            else:
                self.log_result("Validation relation existante", False, f"Relation dupliquée acceptée: {response.status_code}")
        except Exception as e:
            self.log_result("Validation relation existante", False, "Exception", str(e))
        
        # Test GET - Récupération produits d'un fournisseur
        try:
            response = requests.get(f"{BASE_URL}/supplier-product-info/{self.created_supplier_id}")
            if response.status_code == 200:
                relations = response.json()
                if isinstance(relations, list) and len(relations) > 0:
                    self.log_result("GET /supplier-product-info/{supplier_id}", True, 
                                  f"{len(relations)} relation(s) trouvée(s)")
                    
                    # Vérifier qu'on trouve notre relation
                    our_relation = next((r for r in relations if r["product_id"] == self.created_product_id), None)
                    if our_relation:
                        self.log_result("Relation dans liste", True, "Relation créée trouvée")
                    else:
                        self.log_result("Relation dans liste", False, "Relation créée non trouvée")
                else:
                    self.log_result("GET /supplier-product-info/{supplier_id}", False, "Aucune relation trouvée")
            else:
                self.log_result("GET /supplier-product-info/{supplier_id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /supplier-product-info/{supplier_id}", False, "Exception", str(e))
        
        # Test validation - Fournisseur inexistant
        try:
            fake_supplier_data = supplier_product_data.copy()
            fake_supplier_data["supplier_id"] = "fake-supplier-id"
            response = requests.post(f"{BASE_URL}/supplier-product-info", json=fake_supplier_data, headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Validation fournisseur inexistant", True, "Fournisseur inexistant correctement rejeté")
            else:
                self.log_result("Validation fournisseur inexistant", False, f"Fournisseur inexistant accepté: {response.status_code}")
        except Exception as e:
            self.log_result("Validation fournisseur inexistant", False, "Exception", str(e))
    
    def test_product_batch_management(self):
        """Test gestion des lots/batches de produits"""
        print("\n=== TEST PRODUCT BATCH MANAGEMENT ===")
        
        if not self.created_product_id:
            self.log_result("Product Batch Management", False, "Pas de produit pour les tests")
            return
        
        # Test POST - Création batch avec date d'expiration
        expiry_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        batch_data = {
            "product_id": self.created_product_id,
            "quantity": 50.0,
            "expiry_date": expiry_date,
            "supplier_id": self.created_supplier_id,
            "batch_number": "BATCH-V3-001",
            "purchase_price": 22.50
        }
        
        try:
            response = requests.post(f"{BASE_URL}/product-batches", json=batch_data, headers=HEADERS)
            if response.status_code == 200:
                batch = response.json()
                self.created_batch_id = batch["id"]
                
                # Vérifier la structure de réponse
                required_fields = ["id", "product_id", "quantity", "expiry_date", "received_date", "created_at"]
                if all(field in batch for field in required_fields):
                    if (batch["quantity"] == 50.0 and batch["batch_number"] == "BATCH-V3-001"):
                        self.log_result("POST /product-batches", True, 
                                      f"Batch créé: {batch['quantity']}kg, lot {batch['batch_number']}")
                        
                        # Vérifier que le stock a été mis à jour
                        time.sleep(0.5)
                        stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_product_id}")
                        if stock_response.status_code == 200:
                            stock = stock_response.json()
                            if stock["quantite_actuelle"] >= 50.0:
                                self.log_result("Mise à jour stock batch", True, 
                                              f"Stock mis à jour: {stock['quantite_actuelle']}")
                            else:
                                self.log_result("Mise à jour stock batch", False, 
                                              f"Stock non mis à jour: {stock['quantite_actuelle']}")
                    else:
                        self.log_result("POST /product-batches", False, "Valeurs incorrectes")
                else:
                    missing = [f for f in required_fields if f not in batch]
                    self.log_result("POST /product-batches", False, f"Champs manquants: {missing}")
            else:
                self.log_result("POST /product-batches", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /product-batches", False, "Exception", str(e))
            return
        
        # Test GET - Récupération batches d'un produit
        try:
            response = requests.get(f"{BASE_URL}/product-batches/{self.created_product_id}")
            if response.status_code == 200:
                batches = response.json()
                if isinstance(batches, list) and len(batches) > 0:
                    self.log_result("GET /product-batches/{product_id}", True, 
                                  f"{len(batches)} batch(es) trouvé(s)")
                    
                    # Vérifier qu'on trouve notre batch
                    our_batch = next((b for b in batches if b["id"] == self.created_batch_id), None)
                    if our_batch:
                        # Vérifier les détails du batch
                        if (our_batch["batch_number"] == "BATCH-V3-001" and 
                            our_batch["is_consumed"] == False):
                            self.log_result("Détails batch", True, "Batch avec détails corrects")
                        else:
                            self.log_result("Détails batch", False, "Détails batch incorrects")
                    else:
                        self.log_result("Batch dans liste", False, "Batch créé non trouvé")
                else:
                    self.log_result("GET /product-batches/{product_id}", False, "Aucun batch trouvé")
            else:
                self.log_result("GET /product-batches/{product_id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /product-batches/{product_id}", False, "Exception", str(e))
        
        # Test validation - Produit inexistant
        try:
            fake_batch_data = batch_data.copy()
            fake_batch_data["product_id"] = "fake-product-id"
            response = requests.post(f"{BASE_URL}/product-batches", json=fake_batch_data, headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Validation produit inexistant batch", True, "Produit inexistant correctement rejeté")
            else:
                self.log_result("Validation produit inexistant batch", False, f"Produit inexistant accepté: {response.status_code}")
        except Exception as e:
            self.log_result("Validation produit inexistant batch", False, "Exception", str(e))
    
    def test_price_anomaly_alerts(self):
        """Test système d'alertes d'anomalies de prix"""
        print("\n=== TEST PRICE ANOMALY ALERTS ===")
        
        # Créer manuellement une alerte pour les tests (normalement créée automatiquement)
        # En production, ces alertes seraient créées lors de la détection d'écarts de prix
        
        # Test GET - Récupération alertes non résolues
        try:
            response = requests.get(f"{BASE_URL}/price-anomalies")
            if response.status_code == 200:
                alerts = response.json()
                if isinstance(alerts, list):
                    self.log_result("GET /price-anomalies", True, 
                                  f"{len(alerts)} alerte(s) d'anomalie de prix")
                    
                    # Si on a des alertes, tester la résolution
                    if len(alerts) > 0:
                        test_alert = alerts[0]
                        self.created_alert_id = test_alert["id"]
                        
                        # Vérifier la structure d'une alerte
                        required_fields = ["id", "product_id", "product_name", "supplier_id", 
                                         "reference_price", "actual_price", "difference_percentage", 
                                         "alert_date", "is_resolved"]
                        if all(field in test_alert for field in required_fields):
                            self.log_result("Structure alerte", True, 
                                          f"Alerte complète: {test_alert['product_name']} "
                                          f"({test_alert['difference_percentage']:.1f}% d'écart)")
                        else:
                            missing = [f for f in required_fields if f not in test_alert]
                            self.log_result("Structure alerte", False, f"Champs manquants: {missing}")
                    else:
                        self.log_result("Alertes disponibles", True, "Aucune alerte (système sain)")
                else:
                    self.log_result("GET /price-anomalies", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /price-anomalies", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /price-anomalies", False, "Exception", str(e))
        
        # Test POST - Résolution d'alerte (si on en a une)
        if self.created_alert_id:
            try:
                resolution_note = "Prix vérifié et validé par le gérant"
                response = requests.post(f"{BASE_URL}/price-anomalies/{self.created_alert_id}/resolve", 
                                       params={"resolution_note": resolution_note})
                if response.status_code == 200:
                    result = response.json()
                    if "resolved successfully" in result.get("message", ""):
                        self.log_result("POST /price-anomalies/{id}/resolve", True, "Alerte résolue avec succès")
                        
                        # Vérifier que l'alerte n'apparaît plus dans les non résolues
                        time.sleep(0.5)
                        alerts_response = requests.get(f"{BASE_URL}/price-anomalies")
                        if alerts_response.status_code == 200:
                            remaining_alerts = alerts_response.json()
                            resolved_alert_found = any(a["id"] == self.created_alert_id for a in remaining_alerts)
                            if not resolved_alert_found:
                                self.log_result("Validation résolution alerte", True, "Alerte retirée de la liste")
                            else:
                                self.log_result("Validation résolution alerte", False, "Alerte encore présente")
                    else:
                        self.log_result("POST /price-anomalies/{id}/resolve", False, "Message de résolution incorrect")
                else:
                    self.log_result("POST /price-anomalies/{id}/resolve", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("POST /price-anomalies/{id}/resolve", False, "Exception", str(e))
        
        # Test validation - Alerte inexistante
        try:
            response = requests.post(f"{BASE_URL}/price-anomalies/fake-alert-id/resolve", 
                                   params={"resolution_note": "Test"})
            if response.status_code == 404:
                self.log_result("Validation alerte inexistante", True, "Alerte inexistante correctement rejetée")
            else:
                self.log_result("Validation alerte inexistante", False, f"Alerte inexistante acceptée: {response.status_code}")
        except Exception as e:
            self.log_result("Validation alerte inexistante", False, "Exception", str(e))
    
    def test_backward_compatibility(self):
        """Test compatibilité backward avec les anciennes APIs"""
        print("\n=== TEST BACKWARD COMPATIBILITY ===")
        
        # Test création produit avec ancien format (sans champs V3)
        legacy_product_data = {
            "nom": "Produit Legacy Test",
            "description": "Test compatibilité backward",
            "categorie": "Legacy",
            "unite": "pièce",
            "prix_achat": 15.00,
            "fournisseur_id": self.created_supplier_id
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=legacy_product_data, headers=HEADERS)
            if response.status_code == 200:
                legacy_product = response.json()
                
                # Vérifier que les champs V3 sont présents avec des valeurs par défaut
                if "reference_price" in legacy_product:
                    # Le reference_price devrait être défini (probablement égal à prix_achat)
                    if legacy_product["reference_price"] > 0:
                        self.log_result("Backward compatibility produit", True, 
                                      f"Produit legacy créé avec reference_price: {legacy_product['reference_price']}")
                    else:
                        self.log_result("Backward compatibility produit", False, "reference_price non défini")
                else:
                    self.log_result("Backward compatibility produit", False, "Champ reference_price manquant")
                
                # Vérifier que les anciens champs sont toujours présents
                if legacy_product.get("prix_achat") == 15.00:
                    self.log_result("Champs legacy préservés", True, "Anciens champs toujours présents")
                else:
                    self.log_result("Champs legacy préservés", False, "Anciens champs modifiés")
            else:
                self.log_result("Backward compatibility produit", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Backward compatibility produit", False, "Exception", str(e))
        
        # Test que les anciennes APIs fonctionnent toujours
        try:
            # Test ancien endpoint dashboard
            response = requests.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                if "total_produits" in stats and "total_fournisseurs" in stats:
                    self.log_result("API legacy dashboard", True, "Ancien endpoint dashboard fonctionne")
                else:
                    self.log_result("API legacy dashboard", False, "Structure dashboard modifiée")
            else:
                self.log_result("API legacy dashboard", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("API legacy dashboard", False, "Exception", str(e))
    
    def test_data_migration_validation(self):
        """Test validation que la migration a préservé les données existantes"""
        print("\n=== TEST VALIDATION MIGRATION DONNÉES ===")
        
        # Vérifier que les produits existants ont été migrés avec reference_price
        try:
            response = requests.get(f"{BASE_URL}/produits")
            if response.status_code == 200:
                products = response.json()
                if len(products) > 0:
                    # Vérifier que tous les produits ont un reference_price
                    products_with_ref_price = [p for p in products if "reference_price" in p and p["reference_price"] > 0]
                    migration_success_rate = len(products_with_ref_price) / len(products) * 100
                    
                    if migration_success_rate >= 90:  # Au moins 90% des produits migrés
                        self.log_result("Migration reference_price", True, 
                                      f"{migration_success_rate:.1f}% des produits ont reference_price")
                    else:
                        self.log_result("Migration reference_price", False, 
                                      f"Seulement {migration_success_rate:.1f}% des produits migrés")
                    
                    # Vérifier que les champs legacy sont préservés
                    products_with_legacy = [p for p in products if "prix_achat" in p or "fournisseur_id" in p]
                    legacy_preservation_rate = len(products_with_legacy) / len(products) * 100
                    
                    if legacy_preservation_rate >= 80:
                        self.log_result("Préservation données legacy", True, 
                                      f"{legacy_preservation_rate:.1f}% des produits ont données legacy")
                    else:
                        self.log_result("Préservation données legacy", False, 
                                      f"Seulement {legacy_preservation_rate:.1f}% avec données legacy")
                else:
                    self.log_result("Validation migration produits", True, "Aucun produit (base vide)")
            else:
                self.log_result("Validation migration produits", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Validation migration produits", False, "Exception", str(e))
        
        # Vérifier que les stocks existants sont préservés
        try:
            response = requests.get(f"{BASE_URL}/stocks")
            if response.status_code == 200:
                stocks = response.json()
                if len(stocks) > 0:
                    # Vérifier l'intégrité des stocks
                    valid_stocks = [s for s in stocks if "quantite_actuelle" in s and "derniere_maj" in s]
                    stock_integrity_rate = len(valid_stocks) / len(stocks) * 100
                    
                    if stock_integrity_rate >= 95:
                        self.log_result("Intégrité stocks post-migration", True, 
                                      f"{stock_integrity_rate:.1f}% des stocks intègres")
                    else:
                        self.log_result("Intégrité stocks post-migration", False, 
                                      f"Seulement {stock_integrity_rate:.1f}% des stocks intègres")
                else:
                    self.log_result("Validation stocks migration", True, "Aucun stock (base vide)")
            else:
                self.log_result("Validation stocks migration", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Validation stocks migration", False, "Exception", str(e))
    
    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        print("\n=== NETTOYAGE DONNÉES TEST ===")
        
        # Supprimer l'utilisateur de test
        if self.created_user_id:
            try:
                response = requests.delete(f"{BASE_URL}/admin/users/{self.created_user_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage utilisateur", True, "Utilisateur test supprimé")
                else:
                    self.log_result("Nettoyage utilisateur", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage utilisateur", False, "Exception", str(e))
        
        # Supprimer le produit de test
        if self.created_product_id:
            try:
                response = requests.delete(f"{BASE_URL}/produits/{self.created_product_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage produit", True, "Produit test supprimé")
                else:
                    self.log_result("Nettoyage produit", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage produit", False, "Exception", str(e))
        
        # Supprimer le fournisseur de test
        if self.created_supplier_id:
            try:
                response = requests.delete(f"{BASE_URL}/fournisseurs/{self.created_supplier_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage fournisseur", True, "Fournisseur test supprimé")
                else:
                    self.log_result("Nettoyage fournisseur", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage fournisseur", False, "Exception", str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests V3"""
        print("🚀 DÉBUT DES TESTS VERSION 3 BACKEND APIs")
        print("=" * 60)
        
        # Tests dans l'ordre logique
        self.test_migration_v3()
        self.test_user_management_rbac()
        self.test_enhanced_product_model()
        self.test_supplier_product_relations()
        self.test_product_batch_management()
        self.test_price_anomaly_alerts()
        self.test_backward_compatibility()
        self.test_data_migration_validation()
        
        # Nettoyage
        self.cleanup_test_data()
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS VERSION 3")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🎯 TESTS VERSION 3 TERMINÉS")
        return success_rate >= 80  # Considérer comme succès si >= 80%

if __name__ == "__main__":
    test_suite = V3TestSuite()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)