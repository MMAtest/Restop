#!/usr/bin/env python3
"""
Test des nouvelles fonctionnalités implémentées pour La Table d'Augustine
Tests spécifiques pour:
1. Auto-génération des préparations (POST /api/preparations/auto-generate)
2. Produits par catégories (GET /api/produits/by-categories)
3. Diagnostic d'archivage (POST /api/archive/diagnostic)
4. Vérifier les préparations existantes (GET /api/preparations)
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class NouvellesFonctionnalitesTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_preparations_ids = []
        
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

    def test_auto_generation_preparations(self):
        """Test 1: Auto-génération des préparations"""
        print("\n=== TEST 1: AUTO-GÉNÉRATION DES PRÉPARATIONS ===")
        
        try:
            # Vérifier d'abord qu'on a des produits avec catégories
            produits_response = requests.get(f"{BASE_URL}/produits")
            if produits_response.status_code != 200:
                self.log_result("Vérification produits existants", False, 
                              f"Impossible de récupérer les produits: {produits_response.status_code}")
                return
            
            produits = produits_response.json()
            produits_avec_categories = [p for p in produits if p.get("categorie")]
            
            if len(produits_avec_categories) == 0:
                self.log_result("Produits avec catégories", False, 
                              "Aucun produit avec catégorie trouvé pour l'auto-génération")
                return
            
            self.log_result("Produits avec catégories", True, 
                          f"{len(produits_avec_categories)} produits avec catégories disponibles")
            
            # Test de l'auto-génération
            response = requests.post(f"{BASE_URL}/preparations/auto-generate", headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["success", "message", "preparations_created", "details"]
                if all(field in result for field in required_fields):
                    self.log_result("POST /api/preparations/auto-generate - Structure", True, 
                                  "Structure de réponse correcte")
                    
                    # Vérifier le contenu
                    preparations_creees = result.get("preparations_created", 0)
                    details = result.get("details", {})
                    
                    if preparations_creees > 0:
                        self.log_result("Préparations créées", True, 
                                      f"{preparations_creees} préparations créées")
                        
                        # Vérifier le résumé détaillé
                        if isinstance(details, dict) and len(details) > 0:
                            total_products_processed = details.get("total_products_processed", 0)
                            sample_preparations = details.get("sample_preparations", [])
                            
                            if total_products_processed > 0:
                                self.log_result("Produits traités", True, 
                                              f"{total_products_processed} produits traités")
                            
                            if len(sample_preparations) > 0:
                                self.log_result("Échantillon préparations", True, 
                                              f"{len(sample_preparations)} exemples de préparations créées")
                                
                                # Vérifier qu'on a différentes formes de découpe
                                formes_trouvees = set()
                                for prep_name in sample_preparations[:10]:  # Analyser les 10 premiers
                                    if "filets" in prep_name.lower():
                                        formes_trouvees.add("filets")
                                    elif "émincés" in prep_name.lower():
                                        formes_trouvees.add("émincés")
                                    elif "marinés" in prep_name.lower():
                                        formes_trouvees.add("marinés")
                                
                                if len(formes_trouvees) >= 2:
                                    self.log_result("Variété formes de découpe", True, 
                                                  f"Formes trouvées: {', '.join(formes_trouvees)}")
                                else:
                                    self.log_result("Variété formes de découpe", False, 
                                                  f"Peu de variété: {', '.join(formes_trouvees)}")
                            else:
                                self.log_result("Échantillon préparations", False, "Aucun exemple fourni")
                        else:
                            self.log_result("Détails génération", False, "Détails vides ou format incorrect")
                    else:
                        self.log_result("Préparations créées", False, "Aucune préparation créée")
                    
                    # Vérifier le succès
                    if result.get("success") == True:
                        self.log_result("Succès génération", True, "Génération marquée comme réussie")
                    else:
                        self.log_result("Succès génération", False, "Génération non marquée comme réussie")
                        
                else:
                    missing_fields = [f for f in required_fields if f not in result]
                    self.log_result("POST /api/preparations/auto-generate - Structure", False, 
                                  f"Champs manquants: {missing_fields}")
            else:
                self.log_result("POST /api/preparations/auto-generate", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/preparations/auto-generate", False, 
                          f"Exception: {str(e)}")

    def test_produits_by_categories(self):
        """Test 2: Produits par catégories"""
        print("\n=== TEST 2: PRODUITS PAR CATÉGORIES ===")
        
        try:
            response = requests.get(f"{BASE_URL}/produits/by-categories")
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["categories", "total_categories", "total_products"]
                if all(field in result for field in required_fields):
                    self.log_result("GET /api/produits/by-categories - Structure", True, 
                                  "Structure de réponse correcte")
                    
                    categories = result.get("categories", {})
                    total_categories = result.get("total_categories", 0)
                    total_products = result.get("total_products", 0)
                    
                    # Vérifier que categories est un dictionnaire
                    if isinstance(categories, dict):
                        self.log_result("Format catégories", True, "Categories au format dictionnaire")
                        
                        # Vérifier la cohérence des totaux
                        actual_categories = len(categories)
                        actual_products = sum(len(cat_data.get("products", [])) for cat_data in categories.values())
                        
                        if actual_categories == total_categories:
                            self.log_result("Total catégories cohérent", True, 
                                          f"{total_categories} catégories")
                        else:
                            self.log_result("Total catégories cohérent", False, 
                                          f"Incohérence: {actual_categories} vs {total_categories}")
                        
                        if actual_products == total_products:
                            self.log_result("Total produits cohérent", True, 
                                          f"{total_products} produits")
                        else:
                            self.log_result("Total produits cohérent", False, 
                                          f"Incohérence: {actual_products} vs {total_products}")
                        
                        # Vérifier la structure de chaque catégorie
                        categories_valides = 0
                        for cat_name, cat_data in categories.items():
                            if isinstance(cat_data, dict):
                                required_cat_fields = ["products", "icon", "total_products"]
                                if all(field in cat_data for field in required_cat_fields):
                                    categories_valides += 1
                                    
                                    # Vérifier les statistiques
                                    produits_cat = cat_data.get("products", [])
                                    total_produits_cat = cat_data.get("total_products", 0)
                                    
                                    if len(produits_cat) == total_produits_cat:
                                        self.log_result(f"Catégorie {cat_name} - Cohérence", True, 
                                                      f"{total_produits_cat} produits")
                                    else:
                                        self.log_result(f"Catégorie {cat_name} - Cohérence", False, 
                                                      f"Incohérence: {len(produits_cat)} vs {total_produits_cat}")
                        
                        if categories_valides == len(categories):
                            self.log_result("Structure catégories détaillée", True, 
                                          f"Toutes les {categories_valides} catégories bien structurées")
                        else:
                            self.log_result("Structure catégories détaillée", False, 
                                          f"Seulement {categories_valides}/{len(categories)} catégories valides")
                        
                        # Vérifier les catégories attendues pour un restaurant
                        expected_categories = ["Légumes", "Viandes", "Poissons", "Fromages", "Épices"]
                        found_expected = [cat for cat in expected_categories if cat in categories]
                        
                        if len(found_expected) >= 3:
                            self.log_result("Catégories restaurant attendues", True, 
                                          f"Catégories trouvées: {', '.join(found_expected)}")
                        else:
                            self.log_result("Catégories restaurant attendues", False, 
                                          f"Peu de catégories attendues: {', '.join(found_expected)}")
                            
                    else:
                        self.log_result("Format catégories", False, 
                                      f"Categories n'est pas un dictionnaire: {type(categories)}")
                else:
                    missing_fields = [f for f in required_fields if f not in result]
                    self.log_result("GET /api/produits/by-categories - Structure", False, 
                                  f"Champs manquants: {missing_fields}")
            else:
                self.log_result("GET /api/produits/by-categories", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("GET /api/produits/by-categories", False, 
                          f"Exception: {str(e)}")

    def test_archive_diagnostic(self):
        """Test 3: Diagnostic d'archivage"""
        print("\n=== TEST 3: DIAGNOSTIC D'ARCHIVAGE ===")
        
        try:
            response = requests.post(f"{BASE_URL}/archive/diagnostic", headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier la structure de la réponse
                required_fields = ["system_status", "tests"]
                if all(field in result for field in required_fields):
                    self.log_result("POST /api/archive/diagnostic - Structure", True, 
                                  "Structure de réponse correcte")
                    
                    system_status = result.get("system_status")
                    tests = result.get("tests", [])
                    
                    # Vérifier le statut système
                    if system_status == "running":
                        self.log_result("Statut système", True, f"Système: {system_status}")
                    else:
                        self.log_result("Statut système", False, f"Statut inattendu: {system_status}")
                    
                    # Vérifier les tests
                    if isinstance(tests, list) and len(tests) > 0:
                        self.log_result("Tests diagnostic", True, f"{len(tests)} tests exécutés")
                        
                        # Analyser chaque test
                        tests_reussis = 0
                        for test in tests:
                            if isinstance(test, dict) and test.get("status") == "success":
                                tests_reussis += 1
                                test_name = test.get("name", "Test inconnu")
                                self.log_result(f"Test {test_name}", True, "Réussi")
                                
                                # Vérifier les détails spécifiques
                                if test_name == "Collections Count":
                                    details = test.get("details", {})
                                    if isinstance(details, dict):
                                        collections_testees = ["produits", "recettes", "fournisseurs", "archives"]
                                        collections_trouvees = [col for col in collections_testees if col in details]
                                        
                                        if len(collections_trouvees) >= 3:
                                            self.log_result("Collections testées", True, 
                                                          f"Collections: {', '.join(collections_trouvees)}")
                                        else:
                                            self.log_result("Collections testées", False, 
                                                          f"Peu de collections: {collections_trouvees}")
                            else:
                                test_name = test.get("name", "Test inconnu")
                                self.log_result(f"Test {test_name}", False, 
                                              f"Statut: {test.get('status', 'inconnu')}")
                        
                        if tests_reussis == len(tests):
                            self.log_result("Tous tests diagnostic", True, 
                                          f"{tests_reussis}/{len(tests)} tests réussis")
                        else:
                            self.log_result("Tous tests diagnostic", False, 
                                          f"Seulement {tests_reussis}/{len(tests)} tests réussis")
                    else:
                        self.log_result("Tests diagnostic", False, "Aucun test ou format incorrect")
                        
                else:
                    missing_fields = [f for f in required_fields if f not in result]
                    self.log_result("POST /api/archive/diagnostic - Structure", False, 
                                  f"Champs manquants: {missing_fields}")
            else:
                self.log_result("POST /api/archive/diagnostic", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/archive/diagnostic", False, 
                          f"Exception: {str(e)}")

    def test_preparations_existantes(self):
        """Test 4: Vérifier les préparations existantes"""
        print("\n=== TEST 4: VÉRIFIER LES PRÉPARATIONS EXISTANTES ===")
        
        try:
            response = requests.get(f"{BASE_URL}/preparations")
            
            if response.status_code == 200:
                preparations = response.json()
                
                # Vérifier que c'est une liste
                if isinstance(preparations, list):
                    self.log_result("GET /api/preparations - Format", True, 
                                  f"Liste de {len(preparations)} préparations")
                    
                    if len(preparations) > 0:
                        # Vérifier la structure des préparations
                        preparation_sample = preparations[0]
                        required_fields = [
                            "id", "nom", "produit_id", "produit_nom", "forme_decoupe",
                            "quantite_produit_brut", "unite_produit_brut", "quantite_preparee", 
                            "unite_preparee", "perte", "perte_pourcentage", "nombre_portions",
                            "taille_portion", "unite_portion", "date_preparation"
                        ]
                        
                        fields_present = [f for f in required_fields if f in preparation_sample]
                        
                        if len(fields_present) >= 10:  # Au moins 10 champs sur 16
                            self.log_result("Structure préparations", True, 
                                          f"{len(fields_present)}/{len(required_fields)} champs requis présents")
                            
                            # Vérifier la cohérence des données
                            preparations_coherentes = 0
                            for prep in preparations[:5]:  # Tester les 5 premières
                                # Vérifier les quantités
                                quantite_brut = prep.get("quantite_produit_brut", 0)
                                quantite_preparee = prep.get("quantite_preparee", 0)
                                perte = prep.get("perte", 0)
                                perte_pourcentage = prep.get("perte_pourcentage", 0)
                                
                                # Vérifier la cohérence: quantite_brut - perte ≈ quantite_preparee
                                if quantite_brut > 0 and quantite_preparee > 0:
                                    if abs((quantite_brut - perte) - quantite_preparee) < 0.1:
                                        preparations_coherentes += 1
                                    
                                    # Vérifier le pourcentage de perte
                                    expected_perte_pct = (perte / quantite_brut) * 100
                                    if abs(expected_perte_pct - perte_pourcentage) < 1.0:
                                        self.log_result(f"Cohérence perte {prep.get('nom', 'N/A')}", True, 
                                                      f"Perte: {perte_pourcentage:.1f}%")
                                    else:
                                        self.log_result(f"Cohérence perte {prep.get('nom', 'N/A')}", False, 
                                                      f"Incohérence perte: {perte_pourcentage}% vs {expected_perte_pct:.1f}%")
                            
                            if preparations_coherentes >= len(preparations[:5]) * 0.8:  # 80% cohérentes
                                self.log_result("Cohérence données préparations", True, 
                                              f"{preparations_coherentes}/{len(preparations[:5])} préparations cohérentes")
                            else:
                                self.log_result("Cohérence données préparations", False, 
                                              f"Seulement {preparations_coherentes}/{len(preparations[:5])} préparations cohérentes")
                            
                            # Vérifier les formes de découpe
                            formes_decoupe = [prep.get("forme_decoupe") for prep in preparations if prep.get("forme_decoupe")]
                            formes_attendues = ["julienne", "brunoise", "carre", "emince", "hache", "sauce", "puree", "cuit", "marine", "filets", "concasse", "rape"]
                            formes_valides = [f for f in formes_decoupe if f in formes_attendues]
                            
                            if len(formes_valides) >= len(formes_decoupe) * 0.7:  # 70% de formes valides
                                self.log_result("Formes de découpe valides", True, 
                                              f"{len(formes_valides)}/{len(formes_decoupe)} formes valides")
                            else:
                                self.log_result("Formes de découpe valides", False, 
                                              f"Seulement {len(formes_valides)}/{len(formes_decoupe)} formes valides")
                            
                            # Vérifier les liaisons avec les recettes existantes
                            recettes_response = requests.get(f"{BASE_URL}/recettes")
                            if recettes_response.status_code == 200:
                                recettes = recettes_response.json()
                                produits_dans_recettes = set()
                                for recette in recettes:
                                    for ingredient in recette.get("ingredients", []):
                                        produits_dans_recettes.add(ingredient.get("produit_id"))
                                
                                produits_dans_preparations = set(prep.get("produit_id") for prep in preparations)
                                produits_communs = produits_dans_recettes.intersection(produits_dans_preparations)
                                
                                if len(produits_communs) > 0:
                                    self.log_result("Cohérence avec recettes existantes", True, 
                                                  f"{len(produits_communs)} produits communs entre préparations et recettes")
                                else:
                                    self.log_result("Cohérence avec recettes existantes", False, 
                                                  "Aucun produit commun entre préparations et recettes")
                            
                        else:
                            self.log_result("Structure préparations", False, 
                                          f"Seulement {len(fields_present)}/{len(required_fields)} champs requis présents")
                    else:
                        self.log_result("Préparations disponibles", False, 
                                      "Aucune préparation trouvée - Exécuter d'abord l'auto-génération")
                else:
                    self.log_result("GET /api/preparations - Format", False, 
                                  f"Réponse n'est pas une liste: {type(preparations)}")
            else:
                self.log_result("GET /api/preparations", False, 
                              f"Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("GET /api/preparations", False, 
                          f"Exception: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests des nouvelles fonctionnalités"""
        print("🚀 DÉBUT DES TESTS DES NOUVELLES FONCTIONNALITÉS - LA TABLE D'AUGUSTINE")
        print("=" * 80)
        
        # Vérifier d'abord que les données de La Table d'Augustine sont présentes
        self.verify_table_augustine_data()
        
        # Exécuter les tests des nouvelles fonctionnalités
        self.test_auto_generation_preparations()
        self.test_produits_by_categories()
        self.test_archive_diagnostic()
        self.test_preparations_existantes()
        
        # Résumé des résultats
        self.print_summary()

    def verify_table_augustine_data(self):
        """Vérifier que les données de La Table d'Augustine sont présentes"""
        print("\n=== VÉRIFICATION DONNÉES LA TABLE D'AUGUSTINE ===")
        
        try:
            # Vérifier les produits
            produits_response = requests.get(f"{BASE_URL}/produits")
            if produits_response.status_code == 200:
                produits = produits_response.json()
                produits_augustine = [p for p in produits if any(keyword in p.get("nom", "").lower() 
                                    for keyword in ["supions", "burrata", "truffe", "linguine", "rigatoni"])]
                
                if len(produits_augustine) >= 3:
                    self.log_result("Données La Table d'Augustine - Produits", True, 
                                  f"{len(produits_augustine)} produits authentiques trouvés")
                else:
                    self.log_result("Données La Table d'Augustine - Produits", False, 
                                  f"Seulement {len(produits_augustine)} produits authentiques trouvés")
            
            # Vérifier les recettes
            recettes_response = requests.get(f"{BASE_URL}/recettes")
            if recettes_response.status_code == 200:
                recettes = recettes_response.json()
                recettes_augustine = [r for r in recettes if any(keyword in r.get("nom", "").lower() 
                                    for keyword in ["supions", "fleurs", "linguine", "rigatoni", "wellington"])]
                
                if len(recettes_augustine) >= 3:
                    self.log_result("Données La Table d'Augustine - Recettes", True, 
                                  f"{len(recettes_augustine)} recettes authentiques trouvées")
                else:
                    self.log_result("Données La Table d'Augustine - Recettes", False, 
                                  f"Seulement {len(recettes_augustine)} recettes authentiques trouvées")
                    
        except Exception as e:
            self.log_result("Vérification données La Table d'Augustine", False, 
                          f"Exception: {str(e)}")

    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS DES NOUVELLES FONCTIONNALITÉS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print(f"\n✅ TESTS RÉUSSIS ({passed_tests}):")
        for result in self.test_results:
            if result["success"]:
                print(f"   - {result['test']}: {result['message']}")

if __name__ == "__main__":
    test_suite = NouvellesFonctionnalitesTestSuite()
    test_suite.run_all_tests()