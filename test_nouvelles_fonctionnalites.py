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
BASE_URL = "https://cuisine-tracker-5.preview.emergentagent.com/api"
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
                        if isinstance(resume, dict) and len(resume) > 0:
                            total_preparations_resume = sum(len(preps) for preps in resume.values())
                            if total_preparations_resume == preparations_creees:
                                self.log_result("Résumé détaillé", True, 
                                              f"Résumé cohérent: {total_preparations_resume} préparations détaillées")
                                
                                # Vérifier qu'on a 2-3 préparations par produit
                                for produit_nom, preparations in resume.items():
                                    if 2 <= len(preparations) <= 3:
                                        self.log_result(f"Préparations pour {produit_nom}", True, 
                                                      f"{len(preparations)} préparations (dans la fourchette 2-3)")
                                    else:
                                        self.log_result(f"Préparations pour {produit_nom}", False, 
                                                      f"{len(preparations)} préparations (hors fourchette 2-3)")
                            else:
                                self.log_result("Résumé détaillé", False, 
                                              f"Incohérence: {total_preparations_resume} dans résumé vs {preparations_creees} créées")
                        else:
                            self.log_result("Résumé détaillé", False, "Résumé vide ou format incorrect")
                    else:
                        self.log_result("Préparations créées", False, "Aucune préparation créée")
                    
                    if preparations_supprimees >= 0:
                        self.log_result("Suppression préparations existantes", True, 
                                      f"{preparations_supprimees} préparations supprimées")
                    else:
                        self.log_result("Suppression préparations existantes", False, 
                                      "Nombre de suppressions invalide")
                        
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
                        actual_products = sum(len(cat_data.get("produits", [])) for cat_data in categories.values())
                        
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
                                required_cat_fields = ["produits", "icone", "total_produits", "prix_moyen"]
                                if all(field in cat_data for field in required_cat_fields):
                                    categories_valides += 1
                                    
                                    # Vérifier les statistiques
                                    produits_cat = cat_data.get("produits", [])
                                    total_produits_cat = cat_data.get("total_produits", 0)
                                    
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
                required_fields = ["status", "message", "diagnostic"]
                if all(field in result for field in required_fields):
                    self.log_result("POST /api/archive/diagnostic - Structure", True, 
                                  "Structure de réponse correcte")
                    
                    status = result.get("status")
                    diagnostic = result.get("diagnostic", {})
                    
                    # Vérifier le statut
                    if status in ["success", "warning", "error"]:
                        self.log_result("Statut diagnostic", True, f"Statut: {status}")
                    else:
                        self.log_result("Statut diagnostic", False, f"Statut invalide: {status}")
                    
                    # Vérifier la structure du diagnostic
                    if isinstance(diagnostic, dict):
                        expected_diagnostic_fields = ["collections_testees", "permissions", "structure_donnees"]
                        diagnostic_fields_present = [f for f in expected_diagnostic_fields if f in diagnostic]
                        
                        if len(diagnostic_fields_present) >= 2:
                            self.log_result("Structure diagnostic", True, 
                                          f"Champs diagnostic présents: {', '.join(diagnostic_fields_present)}")
                            
                            # Vérifier les collections testées
                            collections_testees = diagnostic.get("collections_testees", {})
                            if isinstance(collections_testees, dict):
                                expected_collections = ["produits", "fournisseurs", "recettes"]
                                tested_collections = [col for col in expected_collections if col in collections_testees]
                                
                                if len(tested_collections) >= 2:
                                    self.log_result("Collections testées", True, 
                                                  f"Collections testées: {', '.join(tested_collections)}")
                                    
                                    # Vérifier les détails de chaque collection
                                    for collection in tested_collections:
                                        col_info = collections_testees[collection]
                                        if isinstance(col_info, dict) and "count" in col_info:
                                            count = col_info["count"]
                                            self.log_result(f"Collection {collection}", True, 
                                                          f"{count} éléments dans {collection}")
                                        else:
                                            self.log_result(f"Collection {collection}", False, 
                                                          "Informations collection incomplètes")
                                else:
                                    self.log_result("Collections testées", False, 
                                                  f"Peu de collections testées: {tested_collections}")
                            else:
                                self.log_result("Collections testées", False, 
                                              "Format collections_testees incorrect")
                            
                            # Vérifier les permissions
                            permissions = diagnostic.get("permissions", {})
                            if isinstance(permissions, dict):
                                permission_checks = ["read", "write", "delete"]
                                permissions_ok = [p for p in permission_checks if permissions.get(p) == True]
                                
                                if len(permissions_ok) >= 2:
                                    self.log_result("Permissions système", True, 
                                                  f"Permissions OK: {', '.join(permissions_ok)}")
                                else:
                                    self.log_result("Permissions système", False, 
                                                  f"Permissions insuffisantes: {permissions}")
                            else:
                                self.log_result("Permissions système", False, 
                                              "Format permissions incorrect")
                                
                        else:
                            self.log_result("Structure diagnostic", False, 
                                          f"Champs diagnostic insuffisants: {diagnostic_fields_present}")
                    else:
                        self.log_result("Structure diagnostic", False, 
                                      f"Diagnostic n'est pas un dictionnaire: {type(diagnostic)}")
                        
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
                            formes_attendues = ["julienne", "brunoise", "carré", "émincé", "haché", "sauce", "purée", "cuit", "mariné"]
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