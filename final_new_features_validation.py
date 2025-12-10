#!/usr/bin/env python3
"""
Test final et complet des nouvelles fonctionnalités backend selon la review request
Validation finale avec corrections des endpoints
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://receipt-scanner-64.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class FinalNewFeaturesValidation:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_id = None
        self.created_produit_id = None
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

    def test_complete_supplier_categories_and_fields(self):
        """Test complet des catégories fournisseurs et nouveaux champs"""
        print("\n=== TEST COMPLET: CATÉGORIES ET NOUVEAUX CHAMPS FOURNISSEURS ===")
        
        # 1. Test endpoint catégories
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs-categories")
            if response.status_code == 200:
                data = response.json()
                categories = data.get("categories", [])
                
                if "fromagerie" in categories and len(categories) >= 9:
                    self.log_result("Endpoint fournisseurs-categories", True, 
                                  f"✅ {len(categories)} catégories incluant fromagerie")
                else:
                    self.log_result("Endpoint fournisseurs-categories", False, 
                                  f"Catégories manquantes: {categories}")
            else:
                self.log_result("Endpoint fournisseurs-categories", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Endpoint fournisseurs-categories", False, f"Exception: {e}")

        # 2. Test création fournisseur fromagerie avec tous les nouveaux champs
        fournisseur_fromagerie = {
            "nom": "Fromagerie Laurent Premium",
            "contact": "Laurent Fromager",
            "email": "laurent@fromagerie-premium.fr",
            "telephone": "04.50.12.34.56",
            "adresse": "Route des Fromages, 74000 Annecy",
            "couleur": "#FFD700",  # Or
            "logo": "🧀🏆",  # Fromage premium
            "categorie": "fromagerie"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_fromagerie, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_fournisseur_id = created["id"]
                
                # Vérifier tous les champs
                checks = [
                    (created.get("couleur") == "#FFD700", "couleur"),
                    (created.get("logo") == "🧀🏆", "logo"),
                    (created.get("categorie") == "fromagerie", "catégorie"),
                    ("created_at" in created, "timestamp")
                ]
                
                all_good = all(check[0] for check in checks)
                if all_good:
                    self.log_result("Création fournisseur fromagerie complet", True, 
                                  "✅ Tous les nouveaux champs correctement assignés")
                else:
                    failed_checks = [check[1] for check in checks if not check[0]]
                    self.log_result("Création fournisseur fromagerie complet", False, 
                                  f"Champs incorrects: {failed_checks}")
            else:
                self.log_result("Création fournisseur fromagerie complet", False, 
                              f"Erreur {response.status_code}: {response.text}")
                return
        except Exception as e:
            self.log_result("Création fournisseur fromagerie complet", False, f"Exception: {e}")
            return

        # 3. Test récupération avec nouveaux champs
        if self.created_fournisseur_id:
            try:
                response = requests.get(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}")
                if response.status_code == 200:
                    fournisseur = response.json()
                    
                    if (fournisseur.get("couleur") == "#FFD700" and 
                        fournisseur.get("logo") == "🧀🏆" and
                        fournisseur.get("categorie") == "fromagerie"):
                        self.log_result("Récupération fournisseur avec nouveaux champs", True, 
                                      "✅ Nouveaux champs persistés correctement")
                    else:
                        self.log_result("Récupération fournisseur avec nouveaux champs", False, 
                                      "Champs non persistés")
                else:
                    self.log_result("Récupération fournisseur avec nouveaux champs", False, 
                                  f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Récupération fournisseur avec nouveaux champs", False, f"Exception: {e}")

    def test_supplier_cost_configuration(self):
        """Test complet de la configuration des coûts fournisseurs"""
        print("\n=== TEST COMPLET: CONFIGURATION COÛTS FOURNISSEURS ===")
        
        if not self.created_fournisseur_id:
            self.log_result("Configuration coûts", False, "Pas de fournisseur créé")
            return

        # 1. Test création configuration coûts
        cost_config = {
            "supplier_id": self.created_fournisseur_id,
            "delivery_cost": 35.00,
            "extra_cost": 12.50
        }
        
        try:
            response = requests.post(f"{BASE_URL}/supplier-cost-config", json=cost_config, headers=HEADERS)
            if response.status_code == 200:
                config = response.json()
                
                if (config.get("delivery_cost") == 35.00 and 
                    config.get("extra_cost") == 12.50):
                    self.log_result("POST supplier-cost-config", True, 
                                  "✅ Configuration coûts créée (livraison: 35€, extra: 12.50€)")
                    
                    # Vérifier création automatique des produits de coûts
                    if (config.get("delivery_cost_product_id") or 
                        config.get("extra_cost_product_id")):
                        self.log_result("Création automatique produits coûts", True, 
                                      "✅ Produits de coûts générés automatiquement")
                    else:
                        self.log_result("Création automatique produits coûts", False, 
                                      "Produits de coûts non générés")
                else:
                    self.log_result("POST supplier-cost-config", False, "Valeurs incorrectes")
            else:
                # Si erreur 400 avec message "déjà existante", c'est normal
                if response.status_code == 400 and "déjà existante" in response.text:
                    self.log_result("POST supplier-cost-config", True, 
                                  "✅ Validation unicité fonctionne (config déjà existante)")
                else:
                    self.log_result("POST supplier-cost-config", False, 
                                  f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("POST supplier-cost-config", False, f"Exception: {e}")

        # 2. Test récupération configuration
        try:
            response = requests.get(f"{BASE_URL}/supplier-cost-config/{self.created_fournisseur_id}")
            if response.status_code == 200:
                config = response.json()
                
                if isinstance(config.get("delivery_cost"), (int, float)) and isinstance(config.get("extra_cost"), (int, float)):
                    self.log_result("GET supplier-cost-config", True, 
                                  f"✅ Configuration récupérée (livraison: {config.get('delivery_cost')}€, extra: {config.get('extra_cost')}€)")
                else:
                    self.log_result("GET supplier-cost-config", False, "Format de données incorrect")
            else:
                self.log_result("GET supplier-cost-config", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET supplier-cost-config", False, f"Exception: {e}")

        # 3. Test modification configuration
        try:
            updated_config = {
                "supplier_id": self.created_fournisseur_id,
                "delivery_cost": 40.00,
                "extra_cost": 15.00
            }
            
            response = requests.put(f"{BASE_URL}/supplier-cost-config/{self.created_fournisseur_id}", 
                                  json=updated_config, headers=HEADERS)
            if response.status_code == 200:
                updated = response.json()
                
                if (updated.get("delivery_cost") == 40.00 and 
                    updated.get("extra_cost") == 15.00):
                    self.log_result("PUT supplier-cost-config", True, 
                                  "✅ Configuration modifiée (livraison: 40€, extra: 15€)")
                else:
                    self.log_result("PUT supplier-cost-config", False, "Modification échouée")
            else:
                self.log_result("PUT supplier-cost-config", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("PUT supplier-cost-config", False, f"Exception: {e}")

    def test_complete_archive_system(self):
        """Test complet du système d'archivage"""
        print("\n=== TEST COMPLET: SYSTÈME D'ARCHIVAGE ===")
        
        # 1. Créer un produit pour les tests
        produit_test = {
            "nom": "Produit Test Archivage Final",
            "description": "Produit pour validation finale archivage",
            "categorie": "Test",
            "unite": "pièce",
            "prix_achat": 25.00
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=produit_test, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_produit_id = created["id"]
                self.log_result("Création produit pour archivage", True, "✅ Produit test créé")
            else:
                self.log_result("Création produit pour archivage", False, f"Erreur {response.status_code}")
                return
        except Exception as e:
            self.log_result("Création produit pour archivage", False, f"Exception: {e}")
            return

        # 2. Test archivage
        archive_request = {
            "item_id": self.created_produit_id,
            "item_type": "produit",
            "reason": "Test final - produit obsolète"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.archived_item_id = result.get("archive_id")
                
                if self.archived_item_id and "archivé avec succès" in result.get("message", ""):
                    self.log_result("POST /archive", True, "✅ Produit archivé avec succès")
                    
                    # Vérifier suppression de la collection principale
                    time.sleep(0.5)
                    check_response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                    if check_response.status_code == 404:
                        self.log_result("Suppression après archivage", True, 
                                      "✅ Produit retiré de la collection principale")
                    else:
                        self.log_result("Suppression après archivage", False, 
                                      "Produit encore accessible")
                else:
                    self.log_result("POST /archive", False, "Réponse incorrecte")
            else:
                self.log_result("POST /archive", False, f"Erreur {response.status_code}: {response.text}")
                return
        except Exception as e:
            self.log_result("POST /archive", False, f"Exception: {e}")
            return

        # 3. Test récupération archives
        try:
            response = requests.get(f"{BASE_URL}/archives")
            if response.status_code == 200:
                archives = response.json()
                
                if isinstance(archives, list) and len(archives) > 0:
                    self.log_result("GET /archives", True, f"✅ {len(archives)} archive(s) récupérée(s)")
                    
                    # Vérifier structure
                    archive = archives[0]
                    required_fields = ["id", "original_id", "item_type", "original_data", "archived_at", "reason"]
                    missing_fields = [field for field in required_fields if field not in archive]
                    
                    if not missing_fields:
                        self.log_result("Structure données archives", True, "✅ Structure complète")
                    else:
                        self.log_result("Structure données archives", False, f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("GET /archives", False, "Aucune archive trouvée")
            else:
                self.log_result("GET /archives", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET /archives", False, f"Exception: {e}")

        # 4. Test filtres archives
        try:
            response = requests.get(f"{BASE_URL}/archives?item_type=produit")
            if response.status_code == 200:
                filtered = response.json()
                
                if isinstance(filtered, list):
                    product_archives = [a for a in filtered if a.get("item_type") == "produit"]
                    
                    if len(product_archives) == len(filtered) and len(filtered) > 0:
                        self.log_result("GET /archives avec filtre", True, 
                                      f"✅ Filtre par type fonctionne: {len(product_archives)} produit(s)")
                    else:
                        self.log_result("GET /archives avec filtre", False, "Filtre défaillant")
                else:
                    self.log_result("GET /archives avec filtre", False, "Format incorrect")
            else:
                self.log_result("GET /archives avec filtre", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("GET /archives avec filtre", False, f"Exception: {e}")

        # 5. Test restauration (avec URL correcte)
        if self.archived_item_id:
            try:
                # Utiliser l'URL correcte avec archive_id dans le path
                response = requests.post(f"{BASE_URL}/restore/{self.archived_item_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    
                    if "restauré avec succès" in result.get("message", ""):
                        self.log_result("POST /restore/{archive_id}", True, "✅ Élément restauré avec succès")
                        
                        # Vérifier que l'élément est de nouveau accessible
                        time.sleep(0.5)
                        check_response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                        if check_response.status_code == 200:
                            restored = check_response.json()
                            if restored.get("nom") == produit_test["nom"]:
                                self.log_result("Vérification restauration", True, 
                                              "✅ Produit restauré et accessible avec données correctes")
                            else:
                                self.log_result("Vérification restauration", False, 
                                              "Données incorrectes après restauration")
                        else:
                            self.log_result("Vérification restauration", False, 
                                          "Produit non accessible après restauration")
                    else:
                        self.log_result("POST /restore/{archive_id}", False, f"Message inattendu: {result}")
                else:
                    self.log_result("POST /restore/{archive_id}", False, f"Erreur {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("POST /restore/{archive_id}", False, f"Exception: {e}")

        # 6. Test suppression définitive archive
        if self.archived_item_id:
            try:
                # Re-archiver pour tester la suppression
                archive_response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
                if archive_response.status_code == 200:
                    new_archive_id = archive_response.json().get("archive_id")
                    
                    # Supprimer définitivement
                    delete_response = requests.delete(f"{BASE_URL}/archives/{new_archive_id}")
                    if delete_response.status_code == 200:
                        self.log_result("DELETE /archives/{id}", True, "✅ Archive supprimée définitivement")
                    else:
                        self.log_result("DELETE /archives/{id}", False, f"Erreur {delete_response.status_code}")
            except Exception as e:
                self.log_result("DELETE /archives/{id}", False, f"Exception: {e}")

    def test_regression_and_validations(self):
        """Test de régression et validations"""
        print("\n=== TEST RÉGRESSION ET VALIDATIONS ===")
        
        # Test endpoints critiques
        critical_endpoints = [
            ("/fournisseurs", "Fournisseurs"),
            ("/produits", "Produits"),
            ("/stocks", "Stocks"),
            ("/recettes", "Recettes"),
            ("/mouvements", "Mouvements"),
            ("/dashboard/stats", "Dashboard")
        ]
        
        for endpoint, name in critical_endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    self.log_result(f"Régression {name}", True, f"✅ Endpoint {endpoint} fonctionnel")
                else:
                    self.log_result(f"Régression {name}", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result(f"Régression {name}", False, f"Exception: {e}")

        # Test gestion d'erreurs
        fake_id = str(uuid.uuid4())
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs/{fake_id}")
            if response.status_code == 404:
                self.log_result("Gestion erreurs 404", True, "✅ Erreur 404 correctement gérée")
            else:
                self.log_result("Gestion erreurs 404", False, f"Status incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Gestion erreurs 404", False, f"Exception: {e}")

        # Test validation champs obligatoires
        invalid_fournisseur = {
            "contact": "Test sans nom",
            "email": "test@example.com"
            # nom manquant
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=invalid_fournisseur, headers=HEADERS)
            if response.status_code in [400, 422]:
                self.log_result("Validation champs obligatoires", True, "✅ Validation nom obligatoire")
            else:
                self.log_result("Validation champs obligatoires", False, f"Validation échouée: {response.status_code}")
        except Exception as e:
            self.log_result("Validation champs obligatoires", False, f"Exception: {e}")

    def run_final_validation(self):
        """Exécute la validation finale complète"""
        print("🎯 VALIDATION FINALE DES NOUVELLES FONCTIONNALITÉS BACKEND")
        print("=" * 80)
        
        start_time = time.time()
        
        # Exécuter tous les tests
        self.test_complete_supplier_categories_and_fields()
        self.test_supplier_cost_configuration()
        self.test_complete_archive_system()
        self.test_regression_and_validations()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Résumé final
        print("\n" + "=" * 80)
        print("🏆 RÉSUMÉ FINAL DE LA VALIDATION")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        print(f"⏱️  Durée: {duration:.2f}s")
        
        # Analyse par fonctionnalité
        print(f"\n📋 ANALYSE PAR FONCTIONNALITÉ:")
        
        categories = {
            "1. Catégories fournisseurs": [r for r in self.test_results if "catégories" in r["test"].lower() or "fromagerie" in r["test"].lower()],
            "2. Nouveaux champs fournisseurs": [r for r in self.test_results if "nouveaux champs" in r["test"].lower() or "récupération fournisseur" in r["test"].lower()],
            "3. Configuration coûts": [r for r in self.test_results if "cost-config" in r["test"].lower() or "coûts" in r["test"].lower()],
            "4. Système archivage": [r for r in self.test_results if "archive" in r["test"].lower() or "restore" in r["test"].lower()],
            "5. Régression": [r for r in self.test_results if "régression" in r["test"].lower() or "validation" in r["test"].lower() or "erreur" in r["test"].lower()]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = len([t for t in tests if t["success"]])
                total = len(tests)
                rate = (passed / total * 100) if total > 0 else 0
                status = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
                print(f"  {status} {category}: {passed}/{total} ({rate:.1f}%)")
        
        # Tests échoués
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS À CORRIGER:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
                    if result.get("details"):
                        print(f"    → {result['details']}")
        
        # Conclusion
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 90:
            print("🟢 EXCELLENT - Toutes les nouvelles fonctionnalités sont opérationnelles")
        elif success_rate >= 80:
            print("🟡 BON - La plupart des fonctionnalités marchent, quelques ajustements mineurs")
        elif success_rate >= 70:
            print("🟠 ACCEPTABLE - Fonctionnalités principales OK, corrections nécessaires")
        else:
            print("🔴 PROBLÉMATIQUE - Corrections importantes requises")
        
        print("\n🏁 VALIDATION TERMINÉE")
        return success_rate >= 75

if __name__ == "__main__":
    validator = FinalNewFeaturesValidation()
    success = validator.run_final_validation()
    exit(0 if success else 1)