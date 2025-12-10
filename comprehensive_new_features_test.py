#!/usr/bin/env python3
"""
Test complet et final des nouvelles fonctionnalités backend implémentées selon la review request
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://receipt-scanner-64.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ComprehensiveNewFeaturesTest:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_id = None
        self.created_produit_id = None
        self.supplier_cost_config_id = None
        self.archived_item_id = None
        
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
        """Test 1: Catégories fournisseurs avec endpoint GET /api/fournisseurs-categories"""
        print("\n=== TEST 1: CATÉGORIES FOURNISSEURS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs-categories")
            if response.status_code == 200:
                data = response.json()
                
                # Le format attendu est {"categories": [...]}
                if "categories" in data and isinstance(data["categories"], list):
                    categories = data["categories"]
                    expected_categories = ["frais", "surgelés", "primeur", "marée", "boucherie", "fromagerie", "extra", "hygiène", "bar"]
                    
                    if all(cat in categories for cat in expected_categories):
                        self.log_result("GET /fournisseurs-categories", True, 
                                      f"Toutes les {len(categories)} catégories présentes, incluant fromagerie")
                        
                        # Vérifier spécifiquement la nouvelle catégorie fromagerie
                        if "fromagerie" in categories:
                            self.log_result("Nouvelle catégorie fromagerie", True, "Catégorie fromagerie disponible")
                        else:
                            self.log_result("Nouvelle catégorie fromagerie", False, "Catégorie fromagerie manquante")
                    else:
                        missing = [cat for cat in expected_categories if cat not in categories]
                        self.log_result("GET /fournisseurs-categories", False, f"Catégories manquantes: {missing}")
                else:
                    self.log_result("GET /fournisseurs-categories", False, f"Format incorrect: {data}")
            else:
                self.log_result("GET /fournisseurs-categories", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /fournisseurs-categories", False, "Exception", str(e))

    def test_fournisseurs_nouveaux_champs(self):
        """Test 2: Création fournisseurs avec nouveaux champs couleur et logo"""
        print("\n=== TEST 2: NOUVEAUX CHAMPS FOURNISSEURS ===")
        
        # Test création avec fromagerie et nouveaux champs
        fournisseur_fromagerie = {
            "nom": "Fromagerie des Alpages",
            "contact": "Jean Fromager",
            "email": "contact@fromagerie-alpages.fr",
            "telephone": "04.76.12.34.56",
            "adresse": "Route des Alpages, 73000 Chambéry",
            "couleur": "#FFA500",  # Orange
            "logo": "🧀",  # Emoji fromage
            "categorie": "fromagerie"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_fromagerie, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_id = created_fournisseur["id"]
                
                # Vérifier tous les nouveaux champs
                if (created_fournisseur.get("couleur") == "#FFA500" and 
                    created_fournisseur.get("logo") == "🧀" and
                    created_fournisseur.get("categorie") == "fromagerie"):
                    self.log_result("Création fournisseur fromagerie avec nouveaux champs", True, 
                                  "Fournisseur fromagerie créé avec couleur orange et logo fromage")
                else:
                    self.log_result("Création fournisseur fromagerie avec nouveaux champs", False, 
                                  f"Champs incorrects: couleur={created_fournisseur.get('couleur')}, "
                                  f"logo={created_fournisseur.get('logo')}, categorie={created_fournisseur.get('categorie')}")
            else:
                self.log_result("Création fournisseur fromagerie avec nouveaux champs", False, 
                              f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("Création fournisseur fromagerie avec nouveaux champs", False, "Exception", str(e))
            return

        # Test valeurs par défaut
        fournisseur_default = {
            "nom": "Fournisseur Test Défaut",
            "contact": "Test Contact"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_default, headers=HEADERS)
            if response.status_code == 200:
                created_default = response.json()
                
                # Vérifier les valeurs par défaut
                if (created_default.get("couleur") == "#3B82F6" and  # Bleu par défaut
                    created_default.get("categorie") == "frais"):  # Catégorie par défaut
                    self.log_result("Valeurs par défaut nouveaux champs", True, 
                                  "Couleur par défaut #3B82F6 et catégorie frais appliquées")
                else:
                    self.log_result("Valeurs par défaut nouveaux champs", False, 
                                  f"Valeurs par défaut incorrectes: couleur={created_default.get('couleur')}, "
                                  f"categorie={created_default.get('categorie')}")
            else:
                self.log_result("Valeurs par défaut nouveaux champs", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Valeurs par défaut nouveaux champs", False, "Exception", str(e))

    def test_supplier_cost_config(self):
        """Test 3: Configuration des coûts fournisseurs"""
        print("\n=== TEST 3: CONFIGURATION COÛTS FOURNISSEURS ===")
        
        if not self.created_fournisseur_id:
            self.log_result("Configuration coûts fournisseurs", False, "Pas de fournisseur créé")
            return

        # Test POST - Création configuration
        cost_config_data = {
            "supplier_id": self.created_fournisseur_id,
            "delivery_cost": 25.00,
            "extra_cost": 8.50
        }
        
        try:
            response = requests.post(f"{BASE_URL}/supplier-cost-config", json=cost_config_data, headers=HEADERS)
            if response.status_code == 200:
                created_config = response.json()
                self.supplier_cost_config_id = created_config["id"]
                
                if (created_config.get("delivery_cost") == 25.00 and 
                    created_config.get("extra_cost") == 8.50):
                    self.log_result("POST /supplier-cost-config", True, 
                                  "Configuration coûts créée: livraison 25€, extra 8.50€")
                    
                    # Vérifier création automatique des produits de coûts
                    if (created_config.get("delivery_cost_product_id") and 
                        created_config.get("extra_cost_product_id")):
                        self.log_result("Création automatique produits coûts", True, 
                                      "Produits de coûts automatiquement générés")
                    else:
                        self.log_result("Création automatique produits coûts", False, 
                                      "Produits de coûts non générés")
                else:
                    self.log_result("POST /supplier-cost-config", False, "Valeurs incorrectes")
            else:
                self.log_result("POST /supplier-cost-config", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /supplier-cost-config", False, "Exception", str(e))
            return

        # Test GET - Récupération configuration
        try:
            response = requests.get(f"{BASE_URL}/supplier-cost-config/{self.created_fournisseur_id}")
            if response.status_code == 200:
                config = response.json()
                
                if (config.get("delivery_cost") == 25.00 and 
                    config.get("extra_cost") == 8.50):
                    self.log_result("GET /supplier-cost-config/{supplier_id}", True, 
                                  "Configuration récupérée correctement")
                else:
                    self.log_result("GET /supplier-cost-config/{supplier_id}", False, 
                                  f"Données incorrectes: delivery={config.get('delivery_cost')}, extra={config.get('extra_cost')}")
            else:
                self.log_result("GET /supplier-cost-config/{supplier_id}", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET /supplier-cost-config/{supplier_id}", False, "Exception", str(e))

        # Test PUT - Modification configuration
        if self.supplier_cost_config_id:
            updated_config = {
                "supplier_id": self.created_fournisseur_id,
                "delivery_cost": 30.00,
                "extra_cost": 10.00
            }
            
            try:
                response = requests.put(f"{BASE_URL}/supplier-cost-config/{self.created_fournisseur_id}", 
                                      json=updated_config, headers=HEADERS)
                if response.status_code == 200:
                    updated = response.json()
                    
                    if (updated.get("delivery_cost") == 30.00 and 
                        updated.get("extra_cost") == 10.00):
                        self.log_result("PUT /supplier-cost-config/{supplier_id}", True, 
                                      "Configuration modifiée: livraison 30€, extra 10€")
                    else:
                        self.log_result("PUT /supplier-cost-config/{supplier_id}", False, "Modification échouée")
                else:
                    self.log_result("PUT /supplier-cost-config/{supplier_id}", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("PUT /supplier-cost-config/{supplier_id}", False, "Exception", str(e))

    def test_archive_system(self):
        """Test 4: Système d'archivage complet"""
        print("\n=== TEST 4: SYSTÈME D'ARCHIVAGE ===")
        
        # Créer un produit pour les tests d'archivage
        produit_test = {
            "nom": "Produit Test Archivage",
            "description": "Produit créé spécifiquement pour tester l'archivage",
            "categorie": "Test",
            "unite": "kg",
            "prix_achat": 15.00
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=produit_test, headers=HEADERS)
            if response.status_code == 200:
                created_produit = response.json()
                self.created_produit_id = created_produit["id"]
                self.log_result("Création produit pour archivage", True, "Produit test créé")
            else:
                self.log_result("Création produit pour archivage", False, f"Erreur {response.status_code}")
                return
        except Exception as e:
            self.log_result("Création produit pour archivage", False, "Exception", str(e))
            return

        # Test POST /archive - Archivage
        archive_request = {
            "item_id": self.created_produit_id,
            "item_type": "produit",
            "reason": "Test archivage - produit obsolète"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.archived_item_id = result.get("archive_id")
                
                if self.archived_item_id and "archivé avec succès" in result.get("message", ""):
                    self.log_result("POST /archive", True, "Produit archivé avec succès")
                    
                    # Vérifier que le produit n'est plus dans la collection principale
                    time.sleep(0.5)
                    check_response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                    if check_response.status_code == 404:
                        self.log_result("Suppression après archivage", True, 
                                      "Produit retiré de la collection principale")
                    else:
                        self.log_result("Suppression après archivage", False, 
                                      "Produit encore accessible")
                else:
                    self.log_result("POST /archive", False, "Réponse incorrecte")
            else:
                self.log_result("POST /archive", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /archive", False, "Exception", str(e))
            return

        # Test GET /archives - Récupération archives
        try:
            response = requests.get(f"{BASE_URL}/archives")
            if response.status_code == 200:
                archives = response.json()
                
                if isinstance(archives, list) and len(archives) > 0:
                    self.log_result("GET /archives", True, f"{len(archives)} archive(s) récupérée(s)")
                    
                    # Vérifier la structure des données
                    archive = archives[0]
                    required_fields = ["id", "original_id", "item_type", "original_data", "archived_at"]
                    
                    if all(field in archive for field in required_fields):
                        self.log_result("Structure données archives", True, "Structure complète")
                    else:
                        missing = [field for field in required_fields if field not in archive]
                        self.log_result("Structure données archives", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("GET /archives", False, "Aucune archive trouvée")
            else:
                self.log_result("GET /archives", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET /archives", False, "Exception", str(e))

        # Test GET /archives avec filtres
        try:
            response = requests.get(f"{BASE_URL}/archives?item_type=produit")
            if response.status_code == 200:
                filtered_archives = response.json()
                
                if isinstance(filtered_archives, list):
                    # Vérifier que le filtre fonctionne
                    product_archives = [a for a in filtered_archives if a.get("item_type") == "produit"]
                    
                    if len(product_archives) == len(filtered_archives):
                        self.log_result("GET /archives avec filtre", True, 
                                      f"Filtre par type fonctionne: {len(product_archives)} produit(s)")
                    else:
                        self.log_result("GET /archives avec filtre", False, "Filtre par type défaillant")
                else:
                    self.log_result("GET /archives avec filtre", False, "Format incorrect")
            else:
                self.log_result("GET /archives avec filtre", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET /archives avec filtre", False, "Exception", str(e))

        # Test POST /restore - Restauration
        if self.archived_item_id:
            restore_request = {
                "archive_id": self.archived_item_id
            }
            
            try:
                response = requests.post(f"{BASE_URL}/restore", json=restore_request, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    
                    if "restauré avec succès" in result.get("message", ""):
                        self.log_result("POST /restore", True, "Élément restauré avec succès")
                        
                        # Vérifier que l'élément est de nouveau accessible
                        time.sleep(0.5)
                        check_response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                        if check_response.status_code == 200:
                            restored_product = check_response.json()
                            if restored_product.get("nom") == produit_test["nom"]:
                                self.log_result("Vérification restauration", True, 
                                              "Produit restauré et accessible")
                            else:
                                self.log_result("Vérification restauration", False, 
                                              "Données incorrectes après restauration")
                        else:
                            self.log_result("Vérification restauration", False, 
                                          "Produit non accessible après restauration")
                    else:
                        self.log_result("POST /restore", False, f"Message inattendu: {result.get('message')}")
                else:
                    self.log_result("POST /restore", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("POST /restore", False, "Exception", str(e))

        # Test DELETE /archives - Suppression définitive
        if self.archived_item_id:
            # Re-archiver pour tester la suppression
            try:
                archive_response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
                if archive_response.status_code == 200:
                    new_archive_id = archive_response.json().get("archive_id")
                    
                    # Supprimer définitivement
                    delete_response = requests.delete(f"{BASE_URL}/archives/{new_archive_id}")
                    if delete_response.status_code == 200:
                        self.log_result("DELETE /archives/{id}", True, "Archive supprimée définitivement")
                    else:
                        self.log_result("DELETE /archives/{id}", False, f"Erreur {delete_response.status_code}")
            except Exception as e:
                self.log_result("DELETE /archives/{id}", False, "Exception", str(e))

    def test_regression_verification(self):
        """Test 5: Vérifications de régression - endpoints existants"""
        print("\n=== TEST 5: VÉRIFICATIONS DE RÉGRESSION ===")
        
        # Test endpoints critiques existants
        endpoints_to_test = [
            ("/fournisseurs", "Liste fournisseurs"),
            ("/produits", "Liste produits"),
            ("/stocks", "Liste stocks"),
            ("/recettes", "Liste recettes"),
            ("/mouvements", "Liste mouvements"),
            ("/dashboard/stats", "Statistiques dashboard")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) or isinstance(data, dict):
                        self.log_result(f"Régression {endpoint}", True, f"{description} fonctionne")
                    else:
                        self.log_result(f"Régression {endpoint}", False, "Format de réponse incorrect")
                else:
                    self.log_result(f"Régression {endpoint}", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result(f"Régression {endpoint}", False, f"Exception: {str(e)}")

        # Test validation des erreurs
        fake_id = str(uuid.uuid4())
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs/{fake_id}")
            if response.status_code == 404:
                self.log_result("Gestion erreurs 404", True, "Erreur 404 correctement retournée")
            else:
                self.log_result("Gestion erreurs 404", False, f"Status incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Gestion erreurs 404", False, "Exception", str(e))

    def test_corrections_recentes(self):
        """Test 6: Corrections récentes mentionnées dans la review request"""
        print("\n=== TEST 6: CORRECTIONS RÉCENTES ===")
        
        # Test des paniers moyens ajustés (entre 40€ et 90€)
        # Vérifier via les statistiques du dashboard
        try:
            response = requests.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                
                # Chercher des indicateurs de panier moyen
                panier_indicators = []
                for key, value in stats.items():
                    if ("panier" in key.lower() or "moyen" in key.lower() or "average" in key.lower()) and isinstance(value, (int, float)):
                        panier_indicators.append((key, value))
                
                if panier_indicators:
                    for key, value in panier_indicators:
                        if 40.0 <= value <= 90.0:
                            self.log_result("Paniers moyens ajustés", True, 
                                          f"{key}: {value}€ (dans la fourchette 40-90€)")
                        else:
                            self.log_result("Paniers moyens ajustés", False, 
                                          f"{key}: {value}€ (hors fourchette 40-90€)")
                else:
                    self.log_result("Paniers moyens ajustés", False, 
                                  "Aucun indicateur de panier moyen trouvé")
            else:
                self.log_result("Paniers moyens ajustés", False, f"Erreur dashboard: {response.status_code}")
        except Exception as e:
            self.log_result("Paniers moyens ajustés", False, "Exception", str(e))

        # Test correction erreur JavaScript "toFixed" pour mode production
        # Vérifier que les endpoints retournent des nombres correctement formatés
        try:
            response = requests.get(f"{BASE_URL}/stocks")
            if response.status_code == 200:
                stocks = response.json()
                if isinstance(stocks, list) and len(stocks) > 0:
                    # Vérifier que les quantités sont des nombres valides
                    valid_numbers = True
                    for stock in stocks[:5]:  # Tester les 5 premiers
                        qty = stock.get("quantite_actuelle")
                        if qty is not None and not isinstance(qty, (int, float)):
                            valid_numbers = False
                            break
                    
                    if valid_numbers:
                        self.log_result("Correction toFixed JavaScript", True, 
                                      "Quantités retournées comme nombres valides")
                    else:
                        self.log_result("Correction toFixed JavaScript", False, 
                                      "Problème de format des nombres")
                else:
                    self.log_result("Correction toFixed JavaScript", False, "Pas de données de stock")
            else:
                self.log_result("Correction toFixed JavaScript", False, f"Erreur stocks: {response.status_code}")
        except Exception as e:
            self.log_result("Correction toFixed JavaScript", False, "Exception", str(e))

    def run_all_tests(self):
        """Exécute tous les tests des nouvelles fonctionnalités"""
        print("🚀 DÉBUT DES TESTS COMPLETS DES NOUVELLES FONCTIONNALITÉS BACKEND")
        print("=" * 80)
        
        start_time = time.time()
        
        # Exécuter tous les tests
        self.test_categories_fournisseurs()
        self.test_fournisseurs_nouveaux_champs()
        self.test_supplier_cost_config()
        self.test_archive_system()
        self.test_regression_verification()
        self.test_corrections_recentes()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Résumé des résultats
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ FINAL DES TESTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        print(f"⏱️  Durée d'exécution: {duration:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
                    if result.get("details"):
                        print(f"    Détails: {result['details']}")
        
        # Résumé par catégorie
        print(f"\n📋 RÉSUMÉ PAR FONCTIONNALITÉ:")
        categories = {
            "Catégories fournisseurs": [r for r in self.test_results if "catégories" in r["test"].lower() or "fromagerie" in r["test"].lower()],
            "Nouveaux champs fournisseurs": [r for r in self.test_results if "nouveaux champs" in r["test"].lower() or "couleur" in r["test"].lower() or "défaut" in r["test"].lower()],
            "Configuration coûts": [r for r in self.test_results if "cost-config" in r["test"].lower() or "coûts" in r["test"].lower()],
            "Système archivage": [r for r in self.test_results if "archive" in r["test"].lower() or "restore" in r["test"].lower()],
            "Vérifications régression": [r for r in self.test_results if "régression" in r["test"].lower() or "erreur" in r["test"].lower()],
            "Corrections récentes": [r for r in self.test_results if "panier" in r["test"].lower() or "toFixed" in r["test"].lower()]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = len([t for t in tests if t["success"]])
                total = len(tests)
                rate = (passed / total * 100) if total > 0 else 0
                print(f"  {category}: {passed}/{total} ({rate:.1f}%)")
        
        print("\n🏁 TESTS TERMINÉS")
        return success_rate >= 75  # Considérer comme succès si 75%+ des tests passent

if __name__ == "__main__":
    test_suite = ComprehensiveNewFeaturesTest()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)