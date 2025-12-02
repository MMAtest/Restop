#!/usr/bin/env python3
"""
Test spécifique des fonctions d'archivage - Diagnostic des problèmes rapportés
Tests des endpoints: POST /api/archive, GET /api/archives, POST /api/restore/{archive_id}
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "https://cuisinepro.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ArchiveTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_id = None
        self.created_produit_id = None
        self.created_recette_id = None
        self.archive_ids = []
        
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
    
    def setup_test_data(self):
        """Créer des données de test pour l'archivage"""
        print("\n=== SETUP - CRÉATION DONNÉES DE TEST ===")
        
        # Créer un fournisseur de test
        fournisseur_data = {
            "nom": "Fournisseur Archive Test",
            "contact": "Jean Archive",
            "email": "jean@archive-test.fr",
            "telephone": "01.23.45.67.89",
            "adresse": "123 Rue Archive, 75001 Paris"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_id = created_fournisseur["id"]
                self.log_result("Setup Fournisseur", True, f"Fournisseur créé: {self.created_fournisseur_id}")
            else:
                self.log_result("Setup Fournisseur", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Fournisseur", False, "Exception", str(e))
            return False
        
        # Créer un produit de test
        produit_data = {
            "nom": "Produit Archive Test",
            "description": "Produit pour tester l'archivage",
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
                self.log_result("Setup Produit", True, f"Produit créé: {self.created_produit_id}")
            else:
                self.log_result("Setup Produit", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Produit", False, "Exception", str(e))
            return False
        
        # Créer une recette de test
        recette_data = {
            "nom": "Recette Archive Test",
            "description": "Recette pour tester l'archivage",
            "categorie": "Plat",
            "portions": 4,
            "temps_preparation": 30,
            "prix_vente": 18.00,
            "ingredients": [
                {
                    "produit_id": self.created_produit_id,
                    "quantite": 500,
                    "unite": "g"
                }
            ]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/recettes", json=recette_data, headers=HEADERS)
            if response.status_code == 200:
                created_recette = response.json()
                self.created_recette_id = created_recette["id"]
                self.log_result("Setup Recette", True, f"Recette créée: {self.created_recette_id}")
            else:
                self.log_result("Setup Recette", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Recette", False, "Exception", str(e))
            return False
        
        return True
    
    def test_archive_produit(self):
        """Test archivage d'un produit"""
        print("\n=== TEST ARCHIVAGE PRODUIT ===")
        
        if not self.created_produit_id:
            self.log_result("Archive Produit", False, "Pas de produit créé pour le test")
            return
        
        archive_request = {
            "item_id": self.created_produit_id,
            "item_type": "produit",
            "reason": "Test d'archivage produit"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                archive_id = result.get("archive_id")
                if archive_id:
                    self.archive_ids.append(archive_id)
                    self.log_result("POST /api/archive (produit)", True, 
                                  f"Produit archivé avec succès, archive_id: {archive_id}")
                    
                    # Vérifier que le produit n'existe plus dans la collection produits
                    time.sleep(0.5)
                    check_response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                    if check_response.status_code == 404:
                        self.log_result("Vérification suppression produit", True, 
                                      "Produit correctement supprimé de la collection")
                    else:
                        self.log_result("Vérification suppression produit", False, 
                                      f"Produit encore présent: {check_response.status_code}")
                else:
                    self.log_result("POST /api/archive (produit)", False, "Pas d'archive_id retourné")
            else:
                self.log_result("POST /api/archive (produit)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/archive (produit)", False, "Exception", str(e))
    
    def test_archive_recette(self):
        """Test archivage d'une recette/production"""
        print("\n=== TEST ARCHIVAGE RECETTE/PRODUCTION ===")
        
        if not self.created_recette_id:
            self.log_result("Archive Recette", False, "Pas de recette créée pour le test")
            return
        
        archive_request = {
            "item_id": self.created_recette_id,
            "item_type": "production",
            "reason": "Test d'archivage recette/production"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                archive_id = result.get("archive_id")
                if archive_id:
                    self.archive_ids.append(archive_id)
                    self.log_result("POST /api/archive (production)", True, 
                                  f"Recette archivée avec succès, archive_id: {archive_id}")
                    
                    # Vérifier que la recette n'existe plus dans la collection recettes
                    time.sleep(0.5)
                    check_response = requests.get(f"{BASE_URL}/recettes/{self.created_recette_id}")
                    if check_response.status_code == 404:
                        self.log_result("Vérification suppression recette", True, 
                                      "Recette correctement supprimée de la collection")
                    else:
                        self.log_result("Vérification suppression recette", False, 
                                      f"Recette encore présente: {check_response.status_code}")
                else:
                    self.log_result("POST /api/archive (production)", False, "Pas d'archive_id retourné")
            else:
                self.log_result("POST /api/archive (production)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/archive (production)", False, "Exception", str(e))
    
    def test_archive_fournisseur(self):
        """Test archivage d'un fournisseur"""
        print("\n=== TEST ARCHIVAGE FOURNISSEUR ===")
        
        if not self.created_fournisseur_id:
            self.log_result("Archive Fournisseur", False, "Pas de fournisseur créé pour le test")
            return
        
        archive_request = {
            "item_id": self.created_fournisseur_id,
            "item_type": "fournisseur",
            "reason": "Test d'archivage fournisseur"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                archive_id = result.get("archive_id")
                if archive_id:
                    self.archive_ids.append(archive_id)
                    self.log_result("POST /api/archive (fournisseur)", True, 
                                  f"Fournisseur archivé avec succès, archive_id: {archive_id}")
                    
                    # Vérifier que le fournisseur n'existe plus dans la collection fournisseurs
                    time.sleep(0.5)
                    check_response = requests.get(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}")
                    if check_response.status_code == 404:
                        self.log_result("Vérification suppression fournisseur", True, 
                                      "Fournisseur correctement supprimé de la collection")
                    else:
                        self.log_result("Vérification suppression fournisseur", False, 
                                      f"Fournisseur encore présent: {check_response.status_code}")
                else:
                    self.log_result("POST /api/archive (fournisseur)", False, "Pas d'archive_id retourné")
            else:
                self.log_result("POST /api/archive (fournisseur)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/archive (fournisseur)", False, "Exception", str(e))
    
    def test_get_archives(self):
        """Test récupération de la liste des archives"""
        print("\n=== TEST RÉCUPÉRATION ARCHIVES ===")
        
        try:
            # Test GET /api/archives (tous les types)
            response = requests.get(f"{BASE_URL}/archives")
            if response.status_code == 200:
                archives = response.json()
                if isinstance(archives, list):
                    self.log_result("GET /api/archives", True, 
                                  f"{len(archives)} archive(s) récupérée(s)")
                    
                    # Vérifier que nos archives sont présentes
                    our_archives = [a for a in archives if a["id"] in self.archive_ids]
                    if len(our_archives) == len(self.archive_ids):
                        self.log_result("Vérification archives créées", True, 
                                      f"Toutes nos {len(self.archive_ids)} archives trouvées")
                        
                        # Vérifier la structure des données
                        if len(our_archives) > 0:
                            archive = our_archives[0]
                            required_fields = ["id", "original_id", "item_type", "original_data", "archived_at"]
                            if all(field in archive for field in required_fields):
                                self.log_result("Structure données archives", True, 
                                              "Tous les champs requis présents")
                            else:
                                missing = [f for f in required_fields if f not in archive]
                                self.log_result("Structure données archives", False, 
                                              f"Champs manquants: {missing}")
                    else:
                        self.log_result("Vérification archives créées", False, 
                                      f"Seulement {len(our_archives)} archives trouvées sur {len(self.archive_ids)}")
                else:
                    self.log_result("GET /api/archives", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /api/archives", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/archives", False, "Exception", str(e))
        
        # Test GET /api/archives avec filtrage par type
        for item_type in ["produit", "production", "fournisseur"]:
            try:
                response = requests.get(f"{BASE_URL}/archives?item_type={item_type}")
                if response.status_code == 200:
                    archives = response.json()
                    if isinstance(archives, list):
                        filtered_archives = [a for a in archives if a["item_type"] == item_type]
                        if len(filtered_archives) == len(archives):
                            self.log_result(f"GET /api/archives?item_type={item_type}", True, 
                                          f"{len(archives)} archive(s) de type {item_type}")
                        else:
                            self.log_result(f"GET /api/archives?item_type={item_type}", False, 
                                          "Filtrage par type incorrect")
                    else:
                        self.log_result(f"GET /api/archives?item_type={item_type}", False, 
                                      "Format de réponse incorrect")
                else:
                    self.log_result(f"GET /api/archives?item_type={item_type}", False, 
                                  f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"GET /api/archives?item_type={item_type}", False, "Exception", str(e))
    
    def test_restore_items(self):
        """Test restauration des éléments archivés"""
        print("\n=== TEST RESTAURATION ARCHIVES ===")
        
        if not self.archive_ids:
            self.log_result("Restore Items", False, "Pas d'archives à restaurer")
            return
        
        # Tester la restauration de chaque archive
        for i, archive_id in enumerate(self.archive_ids):
            try:
                response = requests.post(f"{BASE_URL}/restore/{archive_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_result(f"POST /api/restore/{archive_id}", True, 
                                  f"Archive restaurée: {result.get('message', '')}")
                    
                    # Vérifier que l'archive a été supprimée
                    time.sleep(0.5)
                    check_response = requests.get(f"{BASE_URL}/archives")
                    if check_response.status_code == 200:
                        remaining_archives = check_response.json()
                        if not any(a["id"] == archive_id for a in remaining_archives):
                            self.log_result(f"Vérification suppression archive {i+1}", True, 
                                          "Archive supprimée après restauration")
                        else:
                            self.log_result(f"Vérification suppression archive {i+1}", False, 
                                          "Archive encore présente après restauration")
                else:
                    self.log_result(f"POST /api/restore/{archive_id}", False, 
                                  f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"POST /api/restore/{archive_id}", False, "Exception", str(e))
        
        # Vérifier que les éléments ont été restaurés
        time.sleep(1)
        
        # Vérifier restauration fournisseur
        if self.created_fournisseur_id:
            try:
                response = requests.get(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}")
                if response.status_code == 200:
                    fournisseur = response.json()
                    if fournisseur["nom"] == "Fournisseur Archive Test":
                        self.log_result("Vérification restauration fournisseur", True, 
                                      "Fournisseur correctement restauré")
                    else:
                        self.log_result("Vérification restauration fournisseur", False, 
                                      "Données fournisseur incorrectes")
                else:
                    self.log_result("Vérification restauration fournisseur", False, 
                                  f"Fournisseur non restauré: {response.status_code}")
            except Exception as e:
                self.log_result("Vérification restauration fournisseur", False, "Exception", str(e))
        
        # Vérifier restauration produit
        if self.created_produit_id:
            try:
                response = requests.get(f"{BASE_URL}/produits/{self.created_produit_id}")
                if response.status_code == 200:
                    produit = response.json()
                    if produit["nom"] == "Produit Archive Test":
                        self.log_result("Vérification restauration produit", True, 
                                      "Produit correctement restauré")
                    else:
                        self.log_result("Vérification restauration produit", False, 
                                      "Données produit incorrectes")
                else:
                    self.log_result("Vérification restauration produit", False, 
                                  f"Produit non restauré: {response.status_code}")
            except Exception as e:
                self.log_result("Vérification restauration produit", False, "Exception", str(e))
        
        # Vérifier restauration recette
        if self.created_recette_id:
            try:
                response = requests.get(f"{BASE_URL}/recettes/{self.created_recette_id}")
                if response.status_code == 200:
                    recette = response.json()
                    if recette["nom"] == "Recette Archive Test":
                        self.log_result("Vérification restauration recette", True, 
                                      "Recette correctement restaurée")
                    else:
                        self.log_result("Vérification restauration recette", False, 
                                      "Données recette incorrectes")
                else:
                    self.log_result("Vérification restauration recette", False, 
                                  f"Recette non restaurée: {response.status_code}")
            except Exception as e:
                self.log_result("Vérification restauration recette", False, "Exception", str(e))
    
    def test_error_cases(self):
        """Test des cas d'erreur"""
        print("\n=== TEST CAS D'ERREUR ===")
        
        # Test archivage avec ID inexistant
        archive_request = {
            "item_id": "id-inexistant-12345",
            "item_type": "produit",
            "reason": "Test ID inexistant"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Archive ID inexistant", True, "Erreur 404 correctement retournée")
            else:
                self.log_result("Archive ID inexistant", False, 
                              f"Code d'erreur incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Archive ID inexistant", False, "Exception", str(e))
        
        # Test archivage avec type invalide
        archive_request = {
            "item_id": "test-id",
            "item_type": "type_invalide",
            "reason": "Test type invalide"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/archive", json=archive_request, headers=HEADERS)
            if response.status_code == 400:
                self.log_result("Archive type invalide", True, "Erreur 400 correctement retournée")
            else:
                self.log_result("Archive type invalide", False, 
                              f"Code d'erreur incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Archive type invalide", False, "Exception", str(e))
        
        # Test restauration avec archive_id inexistant
        try:
            response = requests.post(f"{BASE_URL}/restore/archive-inexistant-12345", headers=HEADERS)
            if response.status_code == 404:
                self.log_result("Restore archive inexistante", True, "Erreur 404 correctement retournée")
            else:
                self.log_result("Restore archive inexistante", False, 
                              f"Code d'erreur incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("Restore archive inexistante", False, "Exception", str(e))
    
    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        print("\n=== CLEANUP - NETTOYAGE DONNÉES DE TEST ===")
        
        # Supprimer les éléments restaurés
        if self.created_recette_id:
            try:
                response = requests.delete(f"{BASE_URL}/recettes/{self.created_recette_id}")
                if response.status_code == 200:
                    self.log_result("Cleanup Recette", True, "Recette supprimée")
                else:
                    self.log_result("Cleanup Recette", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Cleanup Recette", False, "Exception", str(e))
        
        if self.created_produit_id:
            try:
                response = requests.delete(f"{BASE_URL}/produits/{self.created_produit_id}")
                if response.status_code == 200:
                    self.log_result("Cleanup Produit", True, "Produit supprimé")
                else:
                    self.log_result("Cleanup Produit", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Cleanup Produit", False, "Exception", str(e))
        
        if self.created_fournisseur_id:
            try:
                response = requests.delete(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}")
                if response.status_code == 200:
                    self.log_result("Cleanup Fournisseur", True, "Fournisseur supprimé")
                else:
                    self.log_result("Cleanup Fournisseur", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Cleanup Fournisseur", False, "Exception", str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests d'archivage"""
        print("🔍 DÉBUT DES TESTS D'ARCHIVAGE - DIAGNOSTIC PROBLÈMES FRONTEND")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_data():
            print("❌ ÉCHEC SETUP - Arrêt des tests")
            return
        
        # Tests d'archivage
        self.test_archive_produit()
        self.test_archive_recette()
        self.test_archive_fournisseur()
        
        # Test récupération archives
        self.test_get_archives()
        
        # Test restauration
        self.test_restore_items()
        
        # Test cas d'erreur
        self.test_error_cases()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Résumé des résultats
        self.print_summary()
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS D'ARCHIVAGE")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
                    if result.get("details"):
                        print(f"      Détails: {result['details']}")
        
        print("\n" + "=" * 80)
        print("🎯 DIAGNOSTIC POUR LE PROBLÈME FRONTEND:")
        
        # Analyser les résultats pour le diagnostic
        archive_tests = [r for r in self.test_results if "POST /api/archive" in r["test"]]
        get_archives_tests = [r for r in self.test_results if "GET /api/archives" in r["test"]]
        restore_tests = [r for r in self.test_results if "POST /api/restore" in r["test"]]
        
        archive_success = all(r["success"] for r in archive_tests)
        get_success = all(r["success"] for r in get_archives_tests)
        restore_success = all(r["success"] for r in restore_tests)
        
        if archive_success and get_success and restore_success:
            print("✅ BACKEND ARCHIVAGE FONCTIONNEL - Le problème est côté FRONTEND")
            print("   - Tous les endpoints d'archivage fonctionnent correctement")
            print("   - Les boutons frontend ne communiquent pas avec l'API")
            print("   - Vérifier les appels JavaScript dans le frontend")
        else:
            print("❌ PROBLÈMES BACKEND IDENTIFIÉS:")
            if not archive_success:
                print("   - Endpoints d'archivage défaillants")
            if not get_success:
                print("   - Récupération des archives défaillante")
            if not restore_success:
                print("   - Restauration défaillante")
        
        print("=" * 80)

if __name__ == "__main__":
    test_suite = ArchiveTestSuite()
    test_suite.run_all_tests()