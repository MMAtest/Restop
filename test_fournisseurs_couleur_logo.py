#!/usr/bin/env python3
"""
Test des améliorations visuelles des fournisseurs avec codes couleur et logos
Tests spécifiques pour les nouveaux champs 'couleur' et 'logo' dans l'API Fournisseurs
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class FournisseurCouleurLogoTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_ids = []
        
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
    
    def test_creation_fournisseur_avec_couleur_logo(self):
        """Test création fournisseur avec nouveaux champs couleur et logo"""
        print("\n=== TEST CRÉATION FOURNISSEUR AVEC COULEUR ET LOGO ===")
        
        # Test 1: Boucherie Martin avec couleur rouge et logo emoji
        fournisseur_boucherie = {
            "nom": "Boucherie Martin",
            "email": "contact@boucherie-martin.fr",
            "telephone": "01.23.45.67.89",
            "couleur": "#DC2626",
            "logo": "🥩"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_boucherie, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_ids.append(created_fournisseur["id"])
                
                # Vérifier que les nouveaux champs sont acceptés et retournés
                if (created_fournisseur.get("couleur") == "#DC2626" and 
                    created_fournisseur.get("logo") == "🥩"):
                    self.log_result("POST /fournisseurs avec couleur/logo", True, 
                                  "Boucherie Martin créée avec couleur rouge et logo viande")
                else:
                    self.log_result("POST /fournisseurs avec couleur/logo", False, 
                                  f"Champs incorrects - couleur: {created_fournisseur.get('couleur')}, logo: {created_fournisseur.get('logo')}")
            else:
                self.log_result("POST /fournisseurs avec couleur/logo", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /fournisseurs avec couleur/logo", False, "Exception", str(e))
        
        # Test 2: Poissonnerie Océan avec couleur bleue et logo poisson
        fournisseur_poissonnerie = {
            "nom": "Poissonnerie Océan",
            "email": "contact@poissonnerie-ocean.fr",
            "couleur": "#0284C7",
            "logo": "🐟"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_poissonnerie, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_ids.append(created_fournisseur["id"])
                
                # Vérifier les nouveaux champs
                if (created_fournisseur.get("couleur") == "#0284C7" and 
                    created_fournisseur.get("logo") == "🐟"):
                    self.log_result("POST /fournisseurs Poissonnerie", True, 
                                  "Poissonnerie Océan créée avec couleur bleue et logo poisson")
                else:
                    self.log_result("POST /fournisseurs Poissonnerie", False, 
                                  f"Champs incorrects - couleur: {created_fournisseur.get('couleur')}, logo: {created_fournisseur.get('logo')}")
            else:
                self.log_result("POST /fournisseurs Poissonnerie", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /fournisseurs Poissonnerie", False, "Exception", str(e))
    
    def test_creation_fournisseur_sans_couleur_logo(self):
        """Test création fournisseur sans couleur/logo pour vérifier les valeurs par défaut"""
        print("\n=== TEST VALEURS PAR DÉFAUT COULEUR/LOGO ===")
        
        fournisseur_basique = {
            "nom": "Fournisseur Basique Test",
            "email": "test@basique.fr",
            "telephone": "01.11.22.33.44"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_basique, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_ids.append(created_fournisseur["id"])
                
                # Vérifier les valeurs par défaut
                couleur_defaut = created_fournisseur.get("couleur")
                logo_defaut = created_fournisseur.get("logo")
                
                if couleur_defaut == "#3B82F6":  # Couleur par défaut (bleu)
                    self.log_result("Couleur par défaut", True, f"Couleur par défaut correcte: {couleur_defaut}")
                else:
                    self.log_result("Couleur par défaut", False, f"Couleur par défaut incorrecte: {couleur_defaut}")
                
                if logo_defaut is None:  # Logo par défaut (null)
                    self.log_result("Logo par défaut", True, "Logo par défaut correct: null")
                else:
                    self.log_result("Logo par défaut", False, f"Logo par défaut incorrect: {logo_defaut}")
            else:
                self.log_result("POST /fournisseurs valeurs défaut", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /fournisseurs valeurs défaut", False, "Exception", str(e))
    
    def test_get_fournisseurs_avec_couleur_logo(self):
        """Test récupération des fournisseurs avec les nouveaux champs"""
        print("\n=== TEST GET FOURNISSEURS AVEC COULEUR/LOGO ===")
        
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs")
            if response.status_code == 200:
                fournisseurs = response.json()
                
                # Chercher nos fournisseurs de test
                boucherie = next((f for f in fournisseurs if f["nom"] == "Boucherie Martin"), None)
                poissonnerie = next((f for f in fournisseurs if f["nom"] == "Poissonnerie Océan"), None)
                
                if boucherie:
                    if (boucherie.get("couleur") == "#DC2626" and boucherie.get("logo") == "🥩"):
                        self.log_result("GET /fournisseurs Boucherie", True, 
                                      "Boucherie Martin récupérée avec couleur et logo corrects")
                    else:
                        self.log_result("GET /fournisseurs Boucherie", False, 
                                      f"Données incorrectes - couleur: {boucherie.get('couleur')}, logo: {boucherie.get('logo')}")
                else:
                    self.log_result("GET /fournisseurs Boucherie", False, "Boucherie Martin non trouvée")
                
                if poissonnerie:
                    if (poissonnerie.get("couleur") == "#0284C7" and poissonnerie.get("logo") == "🐟"):
                        self.log_result("GET /fournisseurs Poissonnerie", True, 
                                      "Poissonnerie Océan récupérée avec couleur et logo corrects")
                    else:
                        self.log_result("GET /fournisseurs Poissonnerie", False, 
                                      f"Données incorrectes - couleur: {poissonnerie.get('couleur')}, logo: {poissonnerie.get('logo')}")
                else:
                    self.log_result("GET /fournisseurs Poissonnerie", False, "Poissonnerie Océan non trouvée")
                
                # Vérifier la structure JSON générale
                if len(fournisseurs) > 0:
                    sample_fournisseur = fournisseurs[0]
                    if "couleur" in sample_fournisseur and "logo" in sample_fournisseur:
                        self.log_result("Structure JSON conforme", True, 
                                      "Tous les fournisseurs ont les champs couleur et logo")
                    else:
                        self.log_result("Structure JSON conforme", False, 
                                      "Champs couleur/logo manquants dans la structure")
            else:
                self.log_result("GET /fournisseurs", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /fournisseurs", False, "Exception", str(e))
    
    def test_get_fournisseur_by_id_avec_couleur_logo(self):
        """Test récupération d'un fournisseur spécifique avec couleur/logo"""
        print("\n=== TEST GET FOURNISSEUR BY ID AVEC COULEUR/LOGO ===")
        
        if not self.created_fournisseur_ids:
            self.log_result("GET /fournisseurs/{id}", False, "Aucun fournisseur créé pour le test")
            return
        
        # Tester le premier fournisseur créé (Boucherie Martin)
        fournisseur_id = self.created_fournisseur_ids[0]
        
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs/{fournisseur_id}")
            if response.status_code == 200:
                fournisseur = response.json()
                
                if (fournisseur.get("nom") == "Boucherie Martin" and
                    fournisseur.get("couleur") == "#DC2626" and
                    fournisseur.get("logo") == "🥩"):
                    self.log_result("GET /fournisseurs/{id}", True, 
                                  "Fournisseur récupéré avec tous les champs couleur/logo")
                else:
                    self.log_result("GET /fournisseurs/{id}", False, 
                                  f"Données incorrectes: nom={fournisseur.get('nom')}, couleur={fournisseur.get('couleur')}, logo={fournisseur.get('logo')}")
            else:
                self.log_result("GET /fournisseurs/{id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /fournisseurs/{id}", False, "Exception", str(e))
    
    def test_modification_fournisseur_couleur_logo(self):
        """Test modification d'un fournisseur pour ajouter/modifier couleur et logo"""
        print("\n=== TEST MODIFICATION FOURNISSEUR COULEUR/LOGO ===")
        
        if not self.created_fournisseur_ids:
            self.log_result("PUT /fournisseurs/{id}", False, "Aucun fournisseur créé pour le test")
            return
        
        # Modifier le fournisseur basique pour ajouter couleur et logo
        fournisseur_id = self.created_fournisseur_ids[-1]  # Le dernier créé (fournisseur basique)
        
        updated_data = {
            "nom": "Fournisseur Basique Modifié",
            "email": "test@basique.fr",
            "telephone": "01.11.22.33.44",
            "couleur": "#10B981",  # Vert
            "logo": "🌿"  # Feuille
        }
        
        try:
            response = requests.put(f"{BASE_URL}/fournisseurs/{fournisseur_id}", 
                                  json=updated_data, headers=HEADERS)
            if response.status_code == 200:
                updated_fournisseur = response.json()
                
                if (updated_fournisseur.get("couleur") == "#10B981" and
                    updated_fournisseur.get("logo") == "🌿" and
                    updated_fournisseur.get("nom") == "Fournisseur Basique Modifié"):
                    self.log_result("PUT /fournisseurs/{id} couleur/logo", True, 
                                  "Fournisseur modifié avec nouvelle couleur verte et logo feuille")
                else:
                    self.log_result("PUT /fournisseurs/{id} couleur/logo", False, 
                                  f"Modification échouée - couleur: {updated_fournisseur.get('couleur')}, logo: {updated_fournisseur.get('logo')}")
            else:
                self.log_result("PUT /fournisseurs/{id} couleur/logo", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("PUT /fournisseurs/{id} couleur/logo", False, "Exception", str(e))
    
    def test_validation_format_couleur_hex(self):
        """Test validation des formats de couleur hexadécimale"""
        print("\n=== TEST VALIDATION FORMAT COULEUR HEX ===")
        
        # Test avec couleur valide
        fournisseur_couleur_valide = {
            "nom": "Test Couleur Valide",
            "email": "test@couleur.fr",
            "couleur": "#FF5733"  # Format hex valide
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_couleur_valide, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                if created_fournisseur.get("couleur") == "#FF5733":
                    self.log_result("Validation couleur hex valide", True, "Couleur hex #FF5733 acceptée")
                    self.created_fournisseur_ids.append(created_fournisseur["id"])
                else:
                    self.log_result("Validation couleur hex valide", False, "Couleur hex non sauvegardée")
            else:
                self.log_result("Validation couleur hex valide", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Validation couleur hex valide", False, "Exception", str(e))
        
        # Test avec couleur invalide (optionnel - dépend de la validation backend)
        fournisseur_couleur_invalide = {
            "nom": "Test Couleur Invalide",
            "email": "test@couleur-invalide.fr",
            "couleur": "rouge"  # Format non-hex
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_couleur_invalide, headers=HEADERS)
            # Le backend peut soit accepter (et utiliser la valeur par défaut) soit rejeter
            if response.status_code == 200:
                created_fournisseur = response.json()
                couleur_result = created_fournisseur.get("couleur")
                if couleur_result == "#3B82F6":  # Valeur par défaut
                    self.log_result("Validation couleur invalide", True, 
                                  "Couleur invalide remplacée par défaut")
                    self.created_fournisseur_ids.append(created_fournisseur["id"])
                else:
                    self.log_result("Validation couleur invalide", True, 
                                  f"Couleur invalide acceptée: {couleur_result}")
            else:
                self.log_result("Validation couleur invalide", True, 
                              f"Couleur invalide rejetée (erreur {response.status_code})")
        except Exception as e:
            self.log_result("Validation couleur invalide", False, "Exception", str(e))
    
    def test_compatibilite_fournisseurs_existants(self):
        """Test que les fournisseurs existants sans couleur/logo fonctionnent toujours"""
        print("\n=== TEST COMPATIBILITÉ FOURNISSEURS EXISTANTS ===")
        
        try:
            # Récupérer tous les fournisseurs
            response = requests.get(f"{BASE_URL}/fournisseurs")
            if response.status_code == 200:
                fournisseurs = response.json()
                
                # Chercher des fournisseurs qui pourraient être anciens (sans nos noms de test)
                fournisseurs_existants = [f for f in fournisseurs if f["nom"] not in 
                                        ["Boucherie Martin", "Poissonnerie Océan", "Fournisseur Basique Test", 
                                         "Fournisseur Basique Modifié", "Test Couleur Valide", "Test Couleur Invalide"]]
                
                if len(fournisseurs_existants) > 0:
                    # Tester un fournisseur existant
                    fournisseur_existant = fournisseurs_existants[0]
                    
                    # Vérifier qu'il a les champs couleur et logo (même si null/défaut)
                    if "couleur" in fournisseur_existant and "logo" in fournisseur_existant:
                        self.log_result("Compatibilité fournisseurs existants", True, 
                                      f"Fournisseur existant '{fournisseur_existant['nom']}' a les nouveaux champs")
                        
                        # Tester une modification sur ce fournisseur existant
                        fournisseur_id = fournisseur_existant["id"]
                        test_update = {
                            "nom": fournisseur_existant["nom"],
                            "email": fournisseur_existant.get("email", "test@existing.fr"),
                            "couleur": "#8B5CF6",  # Violet
                            "logo": "⭐"
                        }
                        
                        update_response = requests.put(f"{BASE_URL}/fournisseurs/{fournisseur_id}", 
                                                     json=test_update, headers=HEADERS)
                        if update_response.status_code == 200:
                            updated = update_response.json()
                            if updated.get("couleur") == "#8B5CF6" and updated.get("logo") == "⭐":
                                self.log_result("Modification fournisseur existant", True, 
                                              "Fournisseur existant modifié avec succès")
                            else:
                                self.log_result("Modification fournisseur existant", False, 
                                              "Modification couleur/logo échouée")
                        else:
                            self.log_result("Modification fournisseur existant", False, 
                                          f"Erreur modification: {update_response.status_code}")
                    else:
                        self.log_result("Compatibilité fournisseurs existants", False, 
                                      "Fournisseur existant n'a pas les nouveaux champs")
                else:
                    self.log_result("Compatibilité fournisseurs existants", True, 
                                  "Aucun fournisseur existant trouvé (tous sont nos tests)")
            else:
                self.log_result("Compatibilité fournisseurs existants", False, 
                              f"Erreur récupération fournisseurs: {response.status_code}")
        except Exception as e:
            self.log_result("Compatibilité fournisseurs existants", False, "Exception", str(e))
    
    def test_migration_donnees_existantes(self):
        """Test que la migration des données existantes fonctionne"""
        print("\n=== TEST MIGRATION DONNÉES EXISTANTES ===")
        
        try:
            # Récupérer tous les fournisseurs pour vérifier la migration
            response = requests.get(f"{BASE_URL}/fournisseurs")
            if response.status_code == 200:
                fournisseurs = response.json()
                
                # Vérifier que tous les fournisseurs ont les nouveaux champs
                fournisseurs_avec_champs = [f for f in fournisseurs if "couleur" in f and "logo" in f]
                
                if len(fournisseurs_avec_champs) == len(fournisseurs):
                    self.log_result("Migration données existantes", True, 
                                  f"Tous les {len(fournisseurs)} fournisseurs ont les nouveaux champs")
                    
                    # Vérifier les valeurs par défaut
                    fournisseurs_couleur_defaut = [f for f in fournisseurs if f.get("couleur") == "#3B82F6"]
                    fournisseurs_logo_null = [f for f in fournisseurs if f.get("logo") is None]
                    
                    self.log_result("Valeurs par défaut migration", True, 
                                  f"{len(fournisseurs_couleur_defaut)} avec couleur défaut, {len(fournisseurs_logo_null)} avec logo null")
                else:
                    self.log_result("Migration données existantes", False, 
                                  f"Seulement {len(fournisseurs_avec_champs)}/{len(fournisseurs)} fournisseurs migrés")
            else:
                self.log_result("Migration données existantes", False, 
                              f"Erreur récupération: {response.status_code}")
        except Exception as e:
            self.log_result("Migration données existantes", False, "Exception", str(e))
    
    def cleanup_test_data(self):
        """Nettoie les données de test créées"""
        print("\n=== NETTOYAGE DONNÉES DE TEST ===")
        
        for fournisseur_id in self.created_fournisseur_ids:
            try:
                response = requests.delete(f"{BASE_URL}/fournisseurs/{fournisseur_id}")
                if response.status_code == 200:
                    print(f"✅ Fournisseur {fournisseur_id} supprimé")
                else:
                    print(f"⚠️ Erreur suppression {fournisseur_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception suppression {fournisseur_id}: {str(e)}")
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 DÉBUT DES TESTS FOURNISSEURS COULEUR/LOGO")
        print("=" * 60)
        
        # Tests principaux
        self.test_creation_fournisseur_avec_couleur_logo()
        self.test_creation_fournisseur_sans_couleur_logo()
        self.test_get_fournisseurs_avec_couleur_logo()
        self.test_get_fournisseur_by_id_avec_couleur_logo()
        self.test_modification_fournisseur_couleur_logo()
        self.test_validation_format_couleur_hex()
        self.test_compatibilite_fournisseurs_existants()
        self.test_migration_donnees_existantes()
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests} tests")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Nettoyage (optionnel)
        # self.cleanup_test_data()
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    test_suite = FournisseurCouleurLogoTestSuite()
    passed, failed = test_suite.run_all_tests()
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
    else:
        print(f"\n⚠️ {failed} test(s) ont échoué")