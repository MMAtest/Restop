#!/usr/bin/env python3
"""
Test CRUD operations for DataGrid APIs
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://restop-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class CRUDTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_ids = {}
        
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
    
    def test_fournisseur_crud(self):
        """Test CRUD complet pour fournisseurs"""
        print("\n=== TEST CRUD FOURNISSEURS ===")
        
        # CREATE
        fournisseur_data = {
            "nom": "Test CRUD Fournisseur",
            "contact": "Marie Dupont",
            "email": "marie@testcrud.fr",
            "telephone": "01.23.45.67.89",
            "adresse": "123 Rue de Test, 75001 Paris"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_ids['fournisseur'] = created["id"]
                self.log_result("CREATE Fournisseur", True, f"Fournisseur créé: {created['nom']}")
            else:
                self.log_result("CREATE Fournisseur", False, f"Erreur {response.status_code}: {response.text}")
                return
        except Exception as e:
            self.log_result("CREATE Fournisseur", False, f"Exception: {str(e)}")
            return
        
        # READ (GET by ID)
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs/{self.created_ids['fournisseur']}")
            if response.status_code == 200:
                fournisseur = response.json()
                if fournisseur["nom"] == fournisseur_data["nom"]:
                    self.log_result("READ Fournisseur", True, "Fournisseur récupéré correctement")
                else:
                    self.log_result("READ Fournisseur", False, "Données incorrectes")
            else:
                self.log_result("READ Fournisseur", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("READ Fournisseur", False, f"Exception: {str(e)}")
        
        # UPDATE
        updated_data = fournisseur_data.copy()
        updated_data["nom"] = "Test CRUD Fournisseur MODIFIÉ"
        updated_data["email"] = "marie.modifie@testcrud.fr"
        
        try:
            response = requests.put(f"{BASE_URL}/fournisseurs/{self.created_ids['fournisseur']}", 
                                  json=updated_data, headers=HEADERS)
            if response.status_code == 200:
                updated = response.json()
                if updated["nom"] == updated_data["nom"]:
                    self.log_result("UPDATE Fournisseur", True, "Fournisseur modifié avec succès")
                else:
                    self.log_result("UPDATE Fournisseur", False, "Modification non appliquée")
            else:
                self.log_result("UPDATE Fournisseur", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("UPDATE Fournisseur", False, f"Exception: {str(e)}")
    
    def test_produit_crud(self):
        """Test CRUD complet pour produits"""
        print("\n=== TEST CRUD PRODUITS ===")
        
        if 'fournisseur' not in self.created_ids:
            self.log_result("CRUD Produits", False, "Pas de fournisseur créé pour les tests")
            return
        
        # CREATE
        produit_data = {
            "nom": "Test CRUD Produit",
            "description": "Produit pour test CRUD",
            "categorie": "Test",
            "unite": "kg",
            "prix_achat": 7.50,
            "fournisseur_id": self.created_ids['fournisseur']
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_ids['produit'] = created["id"]
                self.log_result("CREATE Produit", True, f"Produit créé: {created['nom']}")
                
                # Vérifier que le stock a été créé automatiquement
                stock_response = requests.get(f"{BASE_URL}/stocks/{created['id']}")
                if stock_response.status_code == 200:
                    stock = stock_response.json()
                    if stock["quantite_actuelle"] == 0.0:
                        self.log_result("Auto-création Stock", True, "Stock créé automatiquement")
                    else:
                        self.log_result("Auto-création Stock", False, f"Stock incorrect: {stock['quantite_actuelle']}")
                else:
                    self.log_result("Auto-création Stock", False, "Stock non créé")
            else:
                self.log_result("CREATE Produit", False, f"Erreur {response.status_code}: {response.text}")
                return
        except Exception as e:
            self.log_result("CREATE Produit", False, f"Exception: {str(e)}")
            return
        
        # READ
        try:
            response = requests.get(f"{BASE_URL}/produits/{self.created_ids['produit']}")
            if response.status_code == 200:
                produit = response.json()
                if produit["nom"] == produit_data["nom"]:
                    self.log_result("READ Produit", True, "Produit récupéré correctement")
                else:
                    self.log_result("READ Produit", False, "Données incorrectes")
            else:
                self.log_result("READ Produit", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("READ Produit", False, f"Exception: {str(e)}")
        
        # UPDATE
        updated_data = produit_data.copy()
        updated_data["nom"] = "Test CRUD Produit MODIFIÉ"
        updated_data["prix_achat"] = 8.75
        
        try:
            response = requests.put(f"{BASE_URL}/produits/{self.created_ids['produit']}", 
                                  json=updated_data, headers=HEADERS)
            if response.status_code == 200:
                updated = response.json()
                if updated["nom"] == updated_data["nom"]:
                    self.log_result("UPDATE Produit", True, "Produit modifié avec succès")
                else:
                    self.log_result("UPDATE Produit", False, "Modification non appliquée")
            else:
                self.log_result("UPDATE Produit", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("UPDATE Produit", False, f"Exception: {str(e)}")
    
    def test_recette_crud(self):
        """Test CRUD complet pour recettes"""
        print("\n=== TEST CRUD RECETTES ===")
        
        if 'produit' not in self.created_ids:
            self.log_result("CRUD Recettes", False, "Pas de produit créé pour les tests")
            return
        
        # CREATE
        recette_data = {
            "nom": "Test CRUD Recette",
            "description": "Recette pour test CRUD",
            "categorie": "Test",
            "portions": 4,
            "temps_preparation": 30,
            "prix_vente": 18.50,
            "instructions": "1. Préparer\n2. Cuire\n3. Servir",
            "ingredients": [
                {
                    "produit_id": self.created_ids['produit'],
                    "quantite": 300,
                    "unite": "g"
                }
            ]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/recettes", json=recette_data, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_ids['recette'] = created["id"]
                self.log_result("CREATE Recette", True, f"Recette créée: {created['nom']}")
                
                # Vérifier l'enrichissement des noms de produits
                if created.get("ingredients") and len(created["ingredients"]) > 0:
                    first_ingredient = created["ingredients"][0]
                    if first_ingredient.get("produit_nom"):
                        self.log_result("Enrichissement Ingrédients", True, "Noms produits enrichis")
                    else:
                        self.log_result("Enrichissement Ingrédients", False, "Noms non enrichis")
            else:
                self.log_result("CREATE Recette", False, f"Erreur {response.status_code}: {response.text}")
                return
        except Exception as e:
            self.log_result("CREATE Recette", False, f"Exception: {str(e)}")
            return
        
        # READ
        try:
            response = requests.get(f"{BASE_URL}/recettes/{self.created_ids['recette']}")
            if response.status_code == 200:
                recette = response.json()
                if recette["nom"] == recette_data["nom"]:
                    self.log_result("READ Recette", True, "Recette récupérée correctement")
                else:
                    self.log_result("READ Recette", False, "Données incorrectes")
            else:
                self.log_result("READ Recette", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("READ Recette", False, f"Exception: {str(e)}")
        
        # UPDATE
        updated_data = {
            "nom": "Test CRUD Recette MODIFIÉE",
            "prix_vente": 22.00,
            "portions": 6,
            "ingredients": recette_data["ingredients"]
        }
        
        try:
            response = requests.put(f"{BASE_URL}/recettes/{self.created_ids['recette']}", 
                                  json=updated_data, headers=HEADERS)
            if response.status_code == 200:
                updated = response.json()
                if updated["nom"] == updated_data["nom"]:
                    self.log_result("UPDATE Recette", True, "Recette modifiée avec succès")
                else:
                    self.log_result("UPDATE Recette", False, "Modification non appliquée")
            else:
                self.log_result("UPDATE Recette", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("UPDATE Recette", False, f"Exception: {str(e)}")
    
    def test_production_capacity(self):
        """Test calculateur de capacité de production"""
        print("\n=== TEST CALCULATEUR PRODUCTION ===")
        
        if 'recette' not in self.created_ids:
            self.log_result("Production Capacity", False, "Pas de recette pour le test")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/recettes/{self.created_ids['recette']}/production-capacity")
            if response.status_code == 200:
                capacity = response.json()
                required_fields = ["recette_nom", "portions_max", "ingredients_status"]
                
                if all(field in capacity for field in required_fields):
                    self.log_result("Production Capacity", True, 
                                  f"Capacité calculée: {capacity['portions_max']} portions max")
                else:
                    missing = [f for f in required_fields if f not in capacity]
                    self.log_result("Production Capacity", False, f"Champs manquants: {missing}")
            else:
                self.log_result("Production Capacity", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Production Capacity", False, f"Exception: {str(e)}")
    
    def test_stock_operations(self):
        """Test opérations sur les stocks"""
        print("\n=== TEST OPÉRATIONS STOCKS ===")
        
        if 'produit' not in self.created_ids:
            self.log_result("Stock Operations", False, "Pas de produit pour les tests")
            return
        
        # Test mise à jour stock
        stock_update = {
            "quantite_actuelle": 50.0,
            "quantite_min": 10.0,
            "quantite_max": 200.0
        }
        
        try:
            response = requests.put(f"{BASE_URL}/stocks/{self.created_ids['produit']}", 
                                  json=stock_update, headers=HEADERS)
            if response.status_code == 200:
                updated_stock = response.json()
                if updated_stock["quantite_actuelle"] == stock_update["quantite_actuelle"]:
                    self.log_result("UPDATE Stock", True, f"Stock mis à jour: {updated_stock['quantite_actuelle']}")
                else:
                    self.log_result("UPDATE Stock", False, "Stock non mis à jour")
            else:
                self.log_result("UPDATE Stock", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("UPDATE Stock", False, f"Exception: {str(e)}")
        
        # Test mouvement d'entrée
        mouvement_entree = {
            "produit_id": self.created_ids['produit'],
            "type": "entree",
            "quantite": 25.0,
            "reference": "TEST-001",
            "fournisseur_id": self.created_ids.get('fournisseur'),
            "commentaire": "Test mouvement entrée"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_entree, headers=HEADERS)
            if response.status_code == 200:
                mouvement = response.json()
                self.log_result("CREATE Mouvement Entrée", True, f"Mouvement créé: +{mouvement['quantite']}")
                
                # Vérifier mise à jour stock
                import time
                time.sleep(0.5)
                stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_ids['produit']}")
                if stock_response.status_code == 200:
                    stock = stock_response.json()
                    expected = 50.0 + 25.0
                    if abs(stock["quantite_actuelle"] - expected) < 0.01:
                        self.log_result("Stock Update après Entrée", True, f"Stock: {stock['quantite_actuelle']}")
                    else:
                        self.log_result("Stock Update après Entrée", False, 
                                      f"Stock incorrect: {stock['quantite_actuelle']}, attendu: {expected}")
            else:
                self.log_result("CREATE Mouvement Entrée", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("CREATE Mouvement Entrée", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests CRUD"""
        print("🔧 TESTS CRUD POUR DATAGRIDS")
        print("=" * 50)
        
        self.test_fournisseur_crud()
        self.test_produit_crud()
        self.test_recette_crud()
        self.test_production_capacity()
        self.test_stock_operations()
        
        self.print_summary()
    
    def print_summary(self):
        """Afficher un résumé des résultats"""
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ TESTS CRUD")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ ÉCHECS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")

if __name__ == "__main__":
    test_suite = CRUDTestSuite()
    test_suite.run_all_tests()