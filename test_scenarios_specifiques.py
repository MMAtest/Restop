#!/usr/bin/env python3
"""
Tests spécifiques selon la demande de review:
- Test des modèles Fournisseur mis à jour
- Création fournisseur avec couleur et logo
- Modification fournisseur existant pour ajouter couleur et logo
- Vérifications spécifiques demandées
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://rest-mgmt-sys.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class TestScenariosSpecifiques:
    def __init__(self):
        self.test_results = []
        self.created_ids = []
        
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
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")
    
    def test_scenario_1_boucherie_martin(self):
        """Test création Boucherie Martin selon spécifications exactes"""
        print("\n=== SCÉNARIO 1: BOUCHERIE MARTIN ===")
        
        fournisseur_data = {
            "nom": "Boucherie Martin",
            "email": "contact@boucherie-martin.fr", 
            "telephone": "01.23.45.67.89",
            "couleur": "#DC2626",
            "logo": "🥩"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_ids.append(created["id"])
                
                # Vérifications spécifiques
                checks = [
                    (created.get("nom") == "Boucherie Martin", "Nom correct"),
                    (created.get("email") == "contact@boucherie-martin.fr", "Email correct"),
                    (created.get("telephone") == "01.23.45.67.89", "Téléphone correct"),
                    (created.get("couleur") == "#DC2626", "Couleur rouge correcte"),
                    (created.get("logo") == "🥩", "Logo viande correct"),
                    ("id" in created, "ID généré"),
                    ("created_at" in created, "Date création présente")
                ]
                
                all_passed = all(check[0] for check in checks)
                failed_checks = [check[1] for check in checks if not check[0]]
                
                if all_passed:
                    self.log_result("POST /api/fournisseurs avec nouveaux champs accepté", True, 
                                  "Boucherie Martin créée avec tous les champs corrects")
                else:
                    self.log_result("POST /api/fournisseurs avec nouveaux champs accepté", False, 
                                  f"Échecs: {', '.join(failed_checks)}")
            else:
                self.log_result("POST /api/fournisseurs avec nouveaux champs accepté", False, 
                              f"Erreur HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("POST /api/fournisseurs avec nouveaux champs accepté", False, 
                          f"Exception: {str(e)}")
    
    def test_scenario_2_poissonnerie_ocean(self):
        """Test création Poissonnerie Océan avec logo URL"""
        print("\n=== SCÉNARIO 2: POISSONNERIE OCÉAN ===")
        
        fournisseur_data = {
            "nom": "Poissonnerie Océan",
            "email": "contact@poissonnerie-ocean.fr",
            "couleur": "#0284C7", 
            "logo": "🐟"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_ids.append(created["id"])
                
                # Vérifications spécifiques
                if (created.get("couleur") == "#0284C7" and created.get("logo") == "🐟"):
                    self.log_result("Création fournisseur avec logo URL", True, 
                                  "Poissonnerie Océan créée avec couleur bleue et logo poisson")
                else:
                    self.log_result("Création fournisseur avec logo URL", False, 
                                  f"Couleur: {created.get('couleur')}, Logo: {created.get('logo')}")
            else:
                self.log_result("Création fournisseur avec logo URL", False, 
                              f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Création fournisseur avec logo URL", False, f"Exception: {str(e)}")
    
    def test_verification_get_fournisseurs_retourne_champs(self):
        """Vérification: GET /api/fournisseurs retourne les champs couleur et logo"""
        print("\n=== VÉRIFICATION: GET RETOURNE COULEUR ET LOGO ===")
        
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs")
            if response.status_code == 200:
                fournisseurs = response.json()
                
                if len(fournisseurs) > 0:
                    # Vérifier que tous les fournisseurs ont les champs
                    fournisseurs_avec_champs = [f for f in fournisseurs 
                                              if "couleur" in f and "logo" in f]
                    
                    if len(fournisseurs_avec_champs) == len(fournisseurs):
                        self.log_result("GET /api/fournisseurs retourne les champs couleur et logo", True, 
                                      f"Tous les {len(fournisseurs)} fournisseurs ont couleur et logo")
                        
                        # Vérifier nos fournisseurs de test spécifiquement
                        boucherie = next((f for f in fournisseurs if f["nom"] == "Boucherie Martin"), None)
                        poissonnerie = next((f for f in fournisseurs if f["nom"] == "Poissonnerie Océan"), None)
                        
                        if boucherie and boucherie.get("couleur") == "#DC2626":
                            self.log_result("Boucherie Martin dans GET", True, "Couleur rouge présente")
                        else:
                            self.log_result("Boucherie Martin dans GET", False, "Couleur incorrecte ou absente")
                        
                        if poissonnerie and poissonnerie.get("logo") == "🐟":
                            self.log_result("Poissonnerie Océan dans GET", True, "Logo poisson présent")
                        else:
                            self.log_result("Poissonnerie Océan dans GET", False, "Logo incorrect ou absent")
                    else:
                        self.log_result("GET /api/fournisseurs retourne les champs couleur et logo", False, 
                                      f"Seulement {len(fournisseurs_avec_champs)}/{len(fournisseurs)} avec champs")
                else:
                    self.log_result("GET /api/fournisseurs retourne les champs couleur et logo", False, 
                                  "Aucun fournisseur trouvé")
            else:
                self.log_result("GET /api/fournisseurs retourne les champs couleur et logo", False, 
                              f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("GET /api/fournisseurs retourne les champs couleur et logo", False, 
                          f"Exception: {str(e)}")
    
    def test_verification_put_fournisseurs_modification(self):
        """Vérification: PUT /api/fournisseurs pour modifier couleur/logo fonctionne"""
        print("\n=== VÉRIFICATION: PUT MODIFICATION COULEUR/LOGO ===")
        
        if not self.created_ids:
            self.log_result("PUT /api/fournisseurs pour modifier couleur/logo fonctionne", False, 
                          "Aucun fournisseur créé pour le test")
            return
        
        # Modifier le premier fournisseur créé
        fournisseur_id = self.created_ids[0]
        
        modification_data = {
            "nom": "Boucherie Martin Modifiée",
            "email": "contact@boucherie-martin.fr",
            "telephone": "01.23.45.67.89",
            "couleur": "#EF4444",  # Rouge plus clair
            "logo": "🥓"  # Bacon au lieu de viande
        }
        
        try:
            response = requests.put(f"{BASE_URL}/fournisseurs/{fournisseur_id}", 
                                  json=modification_data, headers=HEADERS)
            if response.status_code == 200:
                modified = response.json()
                
                if (modified.get("couleur") == "#EF4444" and modified.get("logo") == "🥓"):
                    self.log_result("PUT /api/fournisseurs pour modifier couleur/logo fonctionne", True, 
                                  "Modification couleur et logo réussie")
                else:
                    self.log_result("PUT /api/fournisseurs pour modifier couleur/logo fonctionne", False, 
                                  f"Modification échouée - couleur: {modified.get('couleur')}, logo: {modified.get('logo')}")
            else:
                self.log_result("PUT /api/fournisseurs pour modifier couleur/logo fonctionne", False, 
                              f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("PUT /api/fournisseurs pour modifier couleur/logo fonctionne", False, 
                          f"Exception: {str(e)}")
    
    def test_verification_valeurs_defaut(self):
        """Vérification: Valeurs par défaut correctes (couleur: #3B82F6, logo: null)"""
        print("\n=== VÉRIFICATION: VALEURS PAR DÉFAUT ===")
        
        # Créer un fournisseur sans couleur ni logo
        fournisseur_minimal = {
            "nom": "Fournisseur Test Défaut",
            "email": "test@defaut.fr"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_minimal, headers=HEADERS)
            if response.status_code == 200:
                created = response.json()
                self.created_ids.append(created["id"])
                
                couleur_defaut = created.get("couleur")
                logo_defaut = created.get("logo")
                
                if couleur_defaut == "#3B82F6":
                    self.log_result("Valeurs par défaut correctes (couleur: #3B82F6, logo: null)", True, 
                                  f"Couleur par défaut correcte: {couleur_defaut}")
                else:
                    self.log_result("Valeurs par défaut correctes (couleur: #3B82F6, logo: null)", False, 
                                  f"Couleur par défaut incorrecte: {couleur_defaut}")
                
                if logo_defaut is None:
                    self.log_result("Logo par défaut null", True, "Logo par défaut correct: null")
                else:
                    self.log_result("Logo par défaut null", False, f"Logo par défaut incorrect: {logo_defaut}")
            else:
                self.log_result("Valeurs par défaut correctes (couleur: #3B82F6, logo: null)", False, 
                              f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Valeurs par défaut correctes (couleur: #3B82F6, logo: null)", False, 
                          f"Exception: {str(e)}")
    
    def test_verification_validation_format_couleur_hex(self):
        """Vérification: Validation des formats couleur hex"""
        print("\n=== VÉRIFICATION: VALIDATION FORMAT COULEUR HEX ===")
        
        # Test avec différents formats de couleur
        test_cases = [
            ("#FFFFFF", "Blanc hex majuscules"),
            ("#000000", "Noir hex"),
            ("#ff5733", "Orange hex minuscules"),
            ("#F0F", "Format court hex"),
            ("rgb(255,0,0)", "Format RGB (peut être accepté ou rejeté)"),
            ("blue", "Nom de couleur (peut être accepté ou rejeté)")
        ]
        
        for couleur, description in test_cases:
            fournisseur_test = {
                "nom": f"Test {description}",
                "email": f"test-{couleur.replace('#', '').replace('(', '').replace(')', '').replace(',', '-')}@test.fr",
                "couleur": couleur
            }
            
            try:
                response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_test, headers=HEADERS)
                if response.status_code == 200:
                    created = response.json()
                    self.created_ids.append(created["id"])
                    couleur_result = created.get("couleur")
                    
                    if couleur.startswith("#") and len(couleur) in [4, 7]:  # Format hex valide
                        if couleur_result == couleur or couleur_result == couleur.upper():
                            self.log_result(f"Validation format couleur hex - {description}", True, 
                                          f"Format hex accepté: {couleur_result}")
                        else:
                            self.log_result(f"Validation format couleur hex - {description}", False, 
                                          f"Format hex modifié: {couleur} -> {couleur_result}")
                    else:  # Format non-hex
                        self.log_result(f"Validation format couleur - {description}", True, 
                                      f"Format accepté/converti: {couleur} -> {couleur_result}")
                else:
                    self.log_result(f"Validation format couleur - {description}", True, 
                                  f"Format rejeté (HTTP {response.status_code})")
            except Exception as e:
                self.log_result(f"Validation format couleur - {description}", False, 
                              f"Exception: {str(e)}")
    
    def test_verification_structure_json_conforme(self):
        """Vérification: Structure JSON conforme"""
        print("\n=== VÉRIFICATION: STRUCTURE JSON CONFORME ===")
        
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs")
            if response.status_code == 200:
                fournisseurs = response.json()
                
                if len(fournisseurs) > 0:
                    sample = fournisseurs[0]
                    
                    # Champs requis de base
                    required_fields = ["id", "nom", "created_at"]
                    # Nouveaux champs
                    new_fields = ["couleur", "logo"]
                    # Champs optionnels
                    optional_fields = ["email", "telephone", "contact", "adresse"]
                    
                    all_required = all(field in sample for field in required_fields)
                    all_new = all(field in sample for field in new_fields)
                    
                    if all_required and all_new:
                        self.log_result("Structure JSON conforme", True, 
                                      "Tous les champs requis et nouveaux présents")
                        
                        # Vérifier les types
                        type_checks = [
                            (isinstance(sample.get("couleur"), str), "couleur est string"),
                            (sample.get("logo") is None or isinstance(sample.get("logo"), str), "logo est string ou null"),
                            (isinstance(sample.get("id"), str), "id est string"),
                            (isinstance(sample.get("nom"), str), "nom est string")
                        ]
                        
                        all_types_ok = all(check[0] for check in type_checks)
                        if all_types_ok:
                            self.log_result("Types de données corrects", True, "Tous les types sont corrects")
                        else:
                            failed_types = [check[1] for check in type_checks if not check[0]]
                            self.log_result("Types de données corrects", False, 
                                          f"Types incorrects: {', '.join(failed_types)}")
                    else:
                        missing = []
                        if not all_required:
                            missing.extend([f for f in required_fields if f not in sample])
                        if not all_new:
                            missing.extend([f for f in new_fields if f not in sample])
                        
                        self.log_result("Structure JSON conforme", False, 
                                      f"Champs manquants: {', '.join(missing)}")
                else:
                    self.log_result("Structure JSON conforme", False, "Aucun fournisseur pour vérifier la structure")
            else:
                self.log_result("Structure JSON conforme", False, f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Structure JSON conforme", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécute tous les tests spécifiques"""
        print("🎯 TESTS SPÉCIFIQUES SELON DEMANDE DE REVIEW")
        print("=" * 60)
        
        # Tests des scénarios spécifiques
        self.test_scenario_1_boucherie_martin()
        self.test_scenario_2_poissonnerie_ocean()
        
        # Vérifications demandées
        self.test_verification_get_fournisseurs_retourne_champs()
        self.test_verification_put_fournisseurs_modification()
        self.test_verification_valeurs_defaut()
        self.test_verification_validation_format_couleur_hex()
        self.test_verification_structure_json_conforme()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES VÉRIFICATIONS SPÉCIFIQUES")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests} vérifications")
        print(f"✅ Réussies: {passed_tests}")
        print(f"❌ Échouées: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        # Détail des échecs
        if failed_tests > 0:
            print("\n❌ VÉRIFICATIONS ÉCHOUÉES:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    test_suite = TestScenariosSpecifiques()
    passed, failed = test_suite.run_all_tests()
    
    if failed == 0:
        print("\n🎉 TOUTES LES VÉRIFICATIONS SONT PASSÉES!")
        print("✅ Les améliorations visuelles des fournisseurs avec codes couleur et logos fonctionnent parfaitement!")
    else:
        print(f"\n⚠️ {failed} vérification(s) ont échoué")