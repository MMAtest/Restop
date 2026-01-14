#!/usr/bin/env python3
"""
Test spécifique pour les grilles de données (DataGrids) - Problème de données vides
Tests des endpoints: GET /api/produits, GET /api/fournisseurs, GET /api/recettes
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class DataGridTestSuite:
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
    
    def test_produits_datagrid_api(self):
        """Test spécifique de l'API GET /api/produits pour DataGrid"""
        print("\n=== TEST API PRODUITS POUR DATAGRID ===")
        
        try:
            response = requests.get(f"{BASE_URL}/produits")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                produits = response.json()
                print(f"Response Type: {type(produits)}")
                print(f"Response Length: {len(produits) if isinstance(produits, list) else 'N/A'}")
                
                if isinstance(produits, list):
                    if len(produits) > 0:
                        self.log_result("GET /api/produits - Data Available", True, 
                                      f"{len(produits)} produits récupérés")
                        
                        # Analyser la structure du premier produit
                        first_product = produits[0]
                        print(f"Premier produit: {json.dumps(first_product, indent=2, default=str)}")
                        
                        # Vérifier les champs requis pour AG-Grid
                        required_fields = ["id", "nom"]
                        optional_fields = ["description", "categorie", "unite", "prix_achat", "fournisseur_nom"]
                        
                        missing_required = [field for field in required_fields if field not in first_product]
                        present_optional = [field for field in optional_fields if field in first_product]
                        
                        if not missing_required:
                            self.log_result("Produits - Structure Required Fields", True, 
                                          f"Tous les champs requis présents: {required_fields}")
                        else:
                            self.log_result("Produits - Structure Required Fields", False, 
                                          f"Champs requis manquants: {missing_required}")
                        
                        self.log_result("Produits - Optional Fields", True, 
                                      f"Champs optionnels présents: {present_optional}")
                        
                        # Vérifier les types de données
                        data_types_ok = True
                        type_issues = []
                        
                        if not isinstance(first_product.get("id"), str):
                            data_types_ok = False
                            type_issues.append(f"id: {type(first_product.get('id'))}")
                        
                        if not isinstance(first_product.get("nom"), str):
                            data_types_ok = False
                            type_issues.append(f"nom: {type(first_product.get('nom'))}")
                        
                        if data_types_ok:
                            self.log_result("Produits - Data Types", True, "Types de données corrects")
                        else:
                            self.log_result("Produits - Data Types", False, f"Types incorrects: {type_issues}")
                        
                        # Vérifier quelques exemples de données
                        sample_products = produits[:3]
                        for i, product in enumerate(sample_products):
                            print(f"Produit {i+1}: {product.get('nom', 'SANS NOM')} - ID: {product.get('id', 'SANS ID')}")
                        
                    else:
                        self.log_result("GET /api/produits - Empty Data", False, 
                                      "Liste des produits vide - C'est le problème principal!")
                        print("⚠️  PROBLÈME IDENTIFIÉ: La liste des produits est vide")
                else:
                    self.log_result("GET /api/produits - Wrong Format", False, 
                                  f"Format de réponse incorrect: {type(produits)}")
                    print(f"Réponse reçue: {produits}")
            else:
                self.log_result("GET /api/produits - HTTP Error", False, 
                              f"Erreur HTTP {response.status_code}")
                print(f"Response Text: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_result("GET /api/produits - Network Error", False, 
                          f"Erreur réseau: {str(e)}")
        except Exception as e:
            self.log_result("GET /api/produits - Exception", False, 
                          f"Exception: {str(e)}")
    
    def test_fournisseurs_datagrid_api(self):
        """Test spécifique de l'API GET /api/fournisseurs pour DataGrid"""
        print("\n=== TEST API FOURNISSEURS POUR DATAGRID ===")
        
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                fournisseurs = response.json()
                print(f"Response Type: {type(fournisseurs)}")
                print(f"Response Length: {len(fournisseurs) if isinstance(fournisseurs, list) else 'N/A'}")
                
                if isinstance(fournisseurs, list):
                    if len(fournisseurs) > 0:
                        self.log_result("GET /api/fournisseurs - Data Available", True, 
                                      f"{len(fournisseurs)} fournisseurs récupérés")
                        
                        # Analyser la structure du premier fournisseur
                        first_supplier = fournisseurs[0]
                        print(f"Premier fournisseur: {json.dumps(first_supplier, indent=2, default=str)}")
                        
                        # Vérifier les champs requis pour AG-Grid
                        required_fields = ["id", "nom"]
                        optional_fields = ["contact", "email", "telephone", "adresse"]
                        
                        missing_required = [field for field in required_fields if field not in first_supplier]
                        present_optional = [field for field in optional_fields if field in first_supplier]
                        
                        if not missing_required:
                            self.log_result("Fournisseurs - Structure Required Fields", True, 
                                          f"Tous les champs requis présents: {required_fields}")
                        else:
                            self.log_result("Fournisseurs - Structure Required Fields", False, 
                                          f"Champs requis manquants: {missing_required}")
                        
                        self.log_result("Fournisseurs - Optional Fields", True, 
                                      f"Champs optionnels présents: {present_optional}")
                        
                        # Vérifier quelques exemples de données
                        sample_suppliers = fournisseurs[:3]
                        for i, supplier in enumerate(sample_suppliers):
                            print(f"Fournisseur {i+1}: {supplier.get('nom', 'SANS NOM')} - Contact: {supplier.get('contact', 'SANS CONTACT')}")
                        
                    else:
                        self.log_result("GET /api/fournisseurs - Empty Data", False, 
                                      "Liste des fournisseurs vide - Problème pour DataGrid!")
                        print("⚠️  PROBLÈME IDENTIFIÉ: La liste des fournisseurs est vide")
                else:
                    self.log_result("GET /api/fournisseurs - Wrong Format", False, 
                                  f"Format de réponse incorrect: {type(fournisseurs)}")
                    print(f"Réponse reçue: {fournisseurs}")
            else:
                self.log_result("GET /api/fournisseurs - HTTP Error", False, 
                              f"Erreur HTTP {response.status_code}")
                print(f"Response Text: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_result("GET /api/fournisseurs - Network Error", False, 
                          f"Erreur réseau: {str(e)}")
        except Exception as e:
            self.log_result("GET /api/fournisseurs - Exception", False, 
                          f"Exception: {str(e)}")
    
    def test_recettes_datagrid_api(self):
        """Test spécifique de l'API GET /api/recettes pour DataGrid"""
        print("\n=== TEST API RECETTES POUR DATAGRID ===")
        
        try:
            response = requests.get(f"{BASE_URL}/recettes")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                recettes = response.json()
                print(f"Response Type: {type(recettes)}")
                print(f"Response Length: {len(recettes) if isinstance(recettes, list) else 'N/A'}")
                
                if isinstance(recettes, list):
                    if len(recettes) > 0:
                        self.log_result("GET /api/recettes - Data Available", True, 
                                      f"{len(recettes)} recettes récupérées")
                        
                        # Analyser la structure de la première recette
                        first_recipe = recettes[0]
                        print(f"Première recette: {json.dumps(first_recipe, indent=2, default=str)}")
                        
                        # Vérifier les champs requis pour AG-Grid
                        required_fields = ["id", "nom"]
                        optional_fields = ["description", "categorie", "portions", "prix_vente", "ingredients"]
                        
                        missing_required = [field for field in required_fields if field not in first_recipe]
                        present_optional = [field for field in optional_fields if field in first_recipe]
                        
                        if not missing_required:
                            self.log_result("Recettes - Structure Required Fields", True, 
                                          f"Tous les champs requis présents: {required_fields}")
                        else:
                            self.log_result("Recettes - Structure Required Fields", False, 
                                          f"Champs requis manquants: {missing_required}")
                        
                        self.log_result("Recettes - Optional Fields", True, 
                                      f"Champs optionnels présents: {present_optional}")
                        
                        # Vérifier la structure des ingrédients si présents
                        if "ingredients" in first_recipe and isinstance(first_recipe["ingredients"], list):
                            if len(first_recipe["ingredients"]) > 0:
                                first_ingredient = first_recipe["ingredients"][0]
                                ingredient_fields = ["produit_id", "quantite", "unite"]
                                missing_ingredient_fields = [field for field in ingredient_fields if field not in first_ingredient]
                                
                                if not missing_ingredient_fields:
                                    self.log_result("Recettes - Ingredients Structure", True, 
                                                  f"Structure ingrédients correcte: {ingredient_fields}")
                                else:
                                    self.log_result("Recettes - Ingredients Structure", False, 
                                                  f"Champs ingrédients manquants: {missing_ingredient_fields}")
                            else:
                                self.log_result("Recettes - Ingredients", True, "Recette sans ingrédients")
                        
                        # Vérifier quelques exemples de données
                        sample_recipes = recettes[:3]
                        for i, recipe in enumerate(sample_recipes):
                            ingredients_count = len(recipe.get("ingredients", []))
                            print(f"Recette {i+1}: {recipe.get('nom', 'SANS NOM')} - {ingredients_count} ingrédients - Prix: {recipe.get('prix_vente', 'N/A')}€")
                        
                    else:
                        self.log_result("GET /api/recettes - Empty Data", False, 
                                      "Liste des recettes vide - Problème pour DataGrid!")
                        print("⚠️  PROBLÈME IDENTIFIÉ: La liste des recettes est vide")
                else:
                    self.log_result("GET /api/recettes - Wrong Format", False, 
                                  f"Format de réponse incorrect: {type(recettes)}")
                    print(f"Réponse reçue: {recettes}")
            else:
                self.log_result("GET /api/recettes - HTTP Error", False, 
                              f"Erreur HTTP {response.status_code}")
                print(f"Response Text: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_result("GET /api/recettes - Network Error", False, 
                          f"Erreur réseau: {str(e)}")
        except Exception as e:
            self.log_result("GET /api/recettes - Exception", False, 
                          f"Exception: {str(e)}")
    
    def test_cors_and_headers(self):
        """Test des headers CORS et autres problèmes potentiels"""
        print("\n=== TEST CORS ET HEADERS ===")
        
        try:
            # Test avec headers OPTIONS pour CORS
            response = requests.options(f"{BASE_URL}/produits")
            print(f"OPTIONS Status Code: {response.status_code}")
            print(f"CORS Headers: {dict(response.headers)}")
            
            if response.status_code in [200, 204]:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                if any(cors_headers.values()):
                    self.log_result("CORS Headers", True, f"Headers CORS présents: {cors_headers}")
                else:
                    self.log_result("CORS Headers", False, "Aucun header CORS détecté")
            else:
                self.log_result("CORS Preflight", False, f"Preflight OPTIONS échoué: {response.status_code}")
                
        except Exception as e:
            self.log_result("CORS Test", False, f"Exception: {str(e)}")
    
    def test_create_sample_data(self):
        """Créer des données de test pour vérifier si les APIs fonctionnent"""
        print("\n=== TEST CRÉATION DONNÉES ÉCHANTILLON ===")
        
        # Créer un fournisseur de test
        fournisseur_data = {
            "nom": "Test Fournisseur DataGrid",
            "contact": "Jean Test",
            "email": "test@datagrid.fr",
            "telephone": "01.23.45.67.89"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                fournisseur_id = created_fournisseur["id"]
                self.log_result("Create Test Fournisseur", True, f"Fournisseur créé: {fournisseur_id}")
                
                # Créer un produit de test
                produit_data = {
                    "nom": "Test Produit DataGrid",
                    "description": "Produit pour tester DataGrid",
                    "categorie": "Test",
                    "unite": "kg",
                    "prix_achat": 5.50,
                    "fournisseur_id": fournisseur_id
                }
                
                prod_response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
                if prod_response.status_code == 200:
                    created_produit = prod_response.json()
                    produit_id = created_produit["id"]
                    self.log_result("Create Test Produit", True, f"Produit créé: {produit_id}")
                    
                    # Créer une recette de test
                    recette_data = {
                        "nom": "Test Recette DataGrid",
                        "description": "Recette pour tester DataGrid",
                        "categorie": "Test",
                        "portions": 4,
                        "prix_vente": 15.00,
                        "ingredients": [
                            {
                                "produit_id": produit_id,
                                "quantite": 200,
                                "unite": "g"
                            }
                        ]
                    }
                    
                    rec_response = requests.post(f"{BASE_URL}/recettes", json=recette_data, headers=HEADERS)
                    if rec_response.status_code == 200:
                        created_recette = rec_response.json()
                        self.log_result("Create Test Recette", True, f"Recette créée: {created_recette['id']}")
                    else:
                        self.log_result("Create Test Recette", False, f"Erreur: {rec_response.status_code}")
                else:
                    self.log_result("Create Test Produit", False, f"Erreur: {prod_response.status_code}")
            else:
                self.log_result("Create Test Fournisseur", False, f"Erreur: {response.status_code}")
                
        except Exception as e:
            self.log_result("Create Sample Data", False, f"Exception: {str(e)}")
    
    def test_demo_data_initialization(self):
        """Initialiser les données de démonstration pour avoir du contenu"""
        print("\n=== TEST INITIALISATION DONNÉES DÉMO ===")
        
        try:
            # Essayer d'initialiser les données La Table d'Augustine
            response = requests.post(f"{BASE_URL}/demo/init-table-augustine-data", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Init Demo Data - La Table d'Augustine", True, 
                              f"Données créées: {result.get('message', 'Succès')}")
            else:
                # Essayer les données franco-italiennes en fallback
                response2 = requests.post(f"{BASE_URL}/demo/init-french-italian-data", headers=HEADERS)
                if response2.status_code == 200:
                    result2 = response2.json()
                    self.log_result("Init Demo Data - Franco-Italien", True, 
                                  f"Données créées: {result2.get('message', 'Succès')}")
                else:
                    self.log_result("Init Demo Data", False, 
                                  f"Échec des deux endpoints de démo: {response.status_code}, {response2.status_code}")
                    
        except Exception as e:
            self.log_result("Init Demo Data", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests dans l'ordre logique"""
        print("🔍 DIAGNOSTIC DES GRILLES DE DONNÉES VIDES")
        print("=" * 60)
        
        # 1. Tester d'abord les APIs actuelles
        self.test_produits_datagrid_api()
        self.test_fournisseurs_datagrid_api()
        self.test_recettes_datagrid_api()
        
        # 2. Tester CORS
        self.test_cors_and_headers()
        
        # 3. Initialiser des données de démo si les listes sont vides
        self.test_demo_data_initialization()
        
        # 4. Créer des données de test si nécessaire
        self.test_create_sample_data()
        
        # 5. Re-tester les APIs après création de données
        print("\n" + "=" * 60)
        print("🔄 RE-TEST APRÈS CRÉATION DE DONNÉES")
        print("=" * 60)
        
        self.test_produits_datagrid_api()
        self.test_fournisseurs_datagrid_api()
        self.test_recettes_datagrid_api()
        
        # Résumé des résultats
        self.print_summary()
    
    def print_summary(self):
        """Afficher un résumé des résultats de test"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS DATAGRID")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        # Afficher les échecs critiques
        critical_failures = [r for r in self.test_results if not r["success"] and "Empty Data" in r["test"]]
        if critical_failures:
            print("\n🚨 PROBLÈMES CRITIQUES IDENTIFIÉS:")
            for failure in critical_failures:
                print(f"   - {failure['test']}: {failure['message']}")
        
        # Afficher les succès importants
        data_successes = [r for r in self.test_results if r["success"] and "Data Available" in r["test"]]
        if data_successes:
            print("\n✅ DONNÉES DISPONIBLES:")
            for success in data_successes:
                print(f"   - {success['test']}: {success['message']}")

if __name__ == "__main__":
    test_suite = DataGridTestSuite()
    test_suite.run_all_tests()