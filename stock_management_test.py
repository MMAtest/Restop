#!/usr/bin/env python3
"""
Test spécifique pour la gestion des stocks - Focus sur le problème d'édition des quantités
Tests des APIs: /api/stocks, /api/mouvements avec données réelles
"""

import requests
import json
from datetime import datetime
import time
import os

# Configuration
BASE_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class StockManagementTestSuite:
    def __init__(self):
        self.test_results = []
        self.test_produit_id = None
        self.test_fournisseur_id = None
        
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
        """Créer des données de test réalistes pour les stocks"""
        print("\n=== SETUP DONNÉES DE TEST ===")
        
        # Créer un fournisseur de test
        fournisseur_data = {
            "nom": "Marché Central de Rungis",
            "contact": "Pierre Dubois",
            "email": "pierre.dubois@rungis-marche.fr",
            "telephone": "01.46.87.12.34",
            "adresse": "1 Rue de la Tour, 94150 Rungis"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                self.test_fournisseur_id = response.json()["id"]
                self.log_result("Setup Fournisseur", True, "Fournisseur de test créé")
            else:
                self.log_result("Setup Fournisseur", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Fournisseur", False, "Exception", str(e))
            return False
        
        # Créer un produit de test
        produit_data = {
            "nom": "Tomates Grappe Bio",
            "description": "Tomates grappe biologiques de qualité premium",
            "categorie": "Légumes",
            "unite": "kg",
            "prix_achat": 4.50,
            "fournisseur_id": self.test_fournisseur_id
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
            if response.status_code == 200:
                self.test_produit_id = response.json()["id"]
                self.log_result("Setup Produit", True, "Produit de test créé")
                return True
            else:
                self.log_result("Setup Produit", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Produit", False, "Exception", str(e))
            return False

    def test_stocks_api_endpoints(self):
        """Test des endpoints /api/stocks"""
        print("\n=== TEST ENDPOINTS /api/stocks ===")
        
        # Test GET /api/stocks - Liste des stocks
        try:
            response = requests.get(f"{BASE_URL}/stocks")
            if response.status_code == 200:
                stocks = response.json()
                if isinstance(stocks, list):
                    self.log_result("GET /api/stocks", True, f"{len(stocks)} stock(s) récupéré(s)")
                    
                    # Vérifier la structure des données
                    if len(stocks) > 0:
                        stock = stocks[0]
                        required_fields = ["id", "produit_id", "produit_nom", "quantite_actuelle", "quantite_min", "derniere_maj"]
                        missing_fields = [field for field in required_fields if field not in stock]
                        if not missing_fields:
                            self.log_result("Structure données stocks", True, "Tous les champs requis présents")
                        else:
                            self.log_result("Structure données stocks", False, f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("GET /api/stocks", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /api/stocks", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/stocks", False, "Exception", str(e))
        
        # Test GET /api/stocks/{id} - Stock spécifique
        if self.test_produit_id:
            try:
                response = requests.get(f"{BASE_URL}/stocks/{self.test_produit_id}")
                if response.status_code == 200:
                    stock = response.json()
                    if stock["produit_id"] == self.test_produit_id:
                        self.log_result("GET /api/stocks/{id}", True, f"Stock récupéré: {stock['quantite_actuelle']} {stock.get('unite', 'unités')}")
                    else:
                        self.log_result("GET /api/stocks/{id}", False, "ID produit incorrect dans la réponse")
                else:
                    self.log_result("GET /api/stocks/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /api/stocks/{id}", False, "Exception", str(e))

    def test_stock_quantity_updates(self):
        """Test des mises à jour de quantités - Focus sur le problème d'édition"""
        print("\n=== TEST MISE À JOUR QUANTITÉS STOCKS ===")
        
        if not self.test_produit_id:
            self.log_result("Test quantités", False, "Pas de produit de test disponible")
            return
        
        # Test 1: Mise à jour avec quantité entière
        stock_update_1 = {
            "quantite_actuelle": 25.0,
            "quantite_min": 5.0,
            "quantite_max": 100.0
        }
        
        try:
            response = requests.put(f"{BASE_URL}/stocks/{self.test_produit_id}", 
                                  json=stock_update_1, headers=HEADERS)
            if response.status_code == 200:
                updated_stock = response.json()
                if abs(updated_stock["quantite_actuelle"] - stock_update_1["quantite_actuelle"]) < 0.01:
                    self.log_result("PUT /api/stocks - Quantité entière", True, 
                                  f"Quantité mise à jour: {updated_stock['quantite_actuelle']}")
                else:
                    self.log_result("PUT /api/stocks - Quantité entière", False, 
                                  f"Quantité incorrecte: {updated_stock['quantite_actuelle']} au lieu de {stock_update_1['quantite_actuelle']}")
            else:
                self.log_result("PUT /api/stocks - Quantité entière", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("PUT /api/stocks - Quantité entière", False, "Exception", str(e))
        
        # Test 2: Mise à jour avec quantité décimale
        stock_update_2 = {
            "quantite_actuelle": 12.75,
            "quantite_min": 2.5,
            "quantite_max": 50.0
        }
        
        try:
            response = requests.put(f"{BASE_URL}/stocks/{self.test_produit_id}", 
                                  json=stock_update_2, headers=HEADERS)
            if response.status_code == 200:
                updated_stock = response.json()
                if abs(updated_stock["quantite_actuelle"] - stock_update_2["quantite_actuelle"]) < 0.01:
                    self.log_result("PUT /api/stocks - Quantité décimale", True, 
                                  f"Quantité décimale mise à jour: {updated_stock['quantite_actuelle']}")
                else:
                    self.log_result("PUT /api/stocks - Quantité décimale", False, 
                                  f"Quantité incorrecte: {updated_stock['quantite_actuelle']} au lieu de {stock_update_2['quantite_actuelle']}")
            else:
                self.log_result("PUT /api/stocks - Quantité décimale", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("PUT /api/stocks - Quantité décimale", False, "Exception", str(e))
        
        # Test 3: Mise à jour avec quantité zéro
        stock_update_3 = {
            "quantite_actuelle": 0.0,
            "quantite_min": 1.0,
            "quantite_max": 20.0
        }
        
        try:
            response = requests.put(f"{BASE_URL}/stocks/{self.test_produit_id}", 
                                  json=stock_update_3, headers=HEADERS)
            if response.status_code == 200:
                updated_stock = response.json()
                if abs(updated_stock["quantite_actuelle"] - 0.0) < 0.01:
                    self.log_result("PUT /api/stocks - Quantité zéro", True, 
                                  f"Quantité zéro acceptée: {updated_stock['quantite_actuelle']}")
                else:
                    self.log_result("PUT /api/stocks - Quantité zéro", False, 
                                  f"Quantité incorrecte: {updated_stock['quantite_actuelle']}")
            else:
                self.log_result("PUT /api/stocks - Quantité zéro", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("PUT /api/stocks - Quantité zéro", False, "Exception", str(e))

    def test_mouvements_api_endpoints(self):
        """Test des endpoints /api/mouvements"""
        print("\n=== TEST ENDPOINTS /api/mouvements ===")
        
        # Test GET /api/mouvements - Liste des mouvements
        try:
            response = requests.get(f"{BASE_URL}/mouvements")
            if response.status_code == 200:
                mouvements = response.json()
                if isinstance(mouvements, list):
                    self.log_result("GET /api/mouvements", True, f"{len(mouvements)} mouvement(s) récupéré(s)")
                    
                    # Vérifier la structure des données
                    if len(mouvements) > 0:
                        mouvement = mouvements[0]
                        required_fields = ["id", "produit_id", "type", "quantite", "date"]
                        missing_fields = [field for field in required_fields if field not in mouvement]
                        if not missing_fields:
                            self.log_result("Structure données mouvements", True, "Tous les champs requis présents")
                        else:
                            self.log_result("Structure données mouvements", False, f"Champs manquants: {missing_fields}")
                else:
                    self.log_result("GET /api/mouvements", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /api/mouvements", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/mouvements", False, "Exception", str(e))

    def test_mouvement_creation_with_quantities(self):
        """Test création de mouvements avec différentes quantités"""
        print("\n=== TEST CRÉATION MOUVEMENTS AVEC QUANTITÉS VARIÉES ===")
        
        if not self.test_produit_id:
            self.log_result("Test mouvements", False, "Pas de produit de test disponible")
            return
        
        # Test 1: Mouvement d'entrée avec quantité positive
        mouvement_entree = {
            "produit_id": self.test_produit_id,
            "type": "entree",
            "quantite": 30.5,
            "reference": "BON-2025-001",
            "fournisseur_id": self.test_fournisseur_id,
            "commentaire": "Livraison matinale - Tomates fraîches"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_entree, headers=HEADERS)
            if response.status_code == 200:
                mouvement = response.json()
                if mouvement["type"] == "entree" and abs(mouvement["quantite"] - 30.5) < 0.01:
                    self.log_result("POST /api/mouvements - Entrée positive", True, 
                                  f"Mouvement d'entrée créé: +{mouvement['quantite']} kg")
                    
                    # Vérifier que le stock a été mis à jour
                    time.sleep(0.5)
                    stock_response = requests.get(f"{BASE_URL}/stocks/{self.test_produit_id}")
                    if stock_response.status_code == 200:
                        stock = stock_response.json()
                        expected_quantity = 0.0 + 30.5  # quantité précédente + entrée
                        if abs(stock["quantite_actuelle"] - expected_quantity) < 0.01:
                            self.log_result("Mise à jour stock après entrée", True, 
                                          f"Stock mis à jour: {stock['quantite_actuelle']} kg")
                        else:
                            self.log_result("Mise à jour stock après entrée", False, 
                                          f"Stock incorrect: {stock['quantite_actuelle']} kg, attendu: {expected_quantity} kg")
                else:
                    self.log_result("POST /api/mouvements - Entrée positive", False, "Données du mouvement incorrectes")
            else:
                self.log_result("POST /api/mouvements - Entrée positive", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/mouvements - Entrée positive", False, "Exception", str(e))
        
        # Test 2: Mouvement de sortie avec quantité décimale
        mouvement_sortie = {
            "produit_id": self.test_produit_id,
            "type": "sortie",
            "quantite": 8.25,
            "commentaire": "Utilisation pour salade de tomates - Service midi"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_sortie, headers=HEADERS)
            if response.status_code == 200:
                mouvement = response.json()
                if mouvement["type"] == "sortie" and abs(mouvement["quantite"] - 8.25) < 0.01:
                    self.log_result("POST /api/mouvements - Sortie décimale", True, 
                                  f"Mouvement de sortie créé: -{mouvement['quantite']} kg")
                    
                    # Vérifier la mise à jour du stock
                    time.sleep(0.5)
                    stock_response = requests.get(f"{BASE_URL}/stocks/{self.test_produit_id}")
                    if stock_response.status_code == 200:
                        stock = stock_response.json()
                        expected_quantity = 30.5 - 8.25  # quantité après entrée - sortie
                        if abs(stock["quantite_actuelle"] - expected_quantity) < 0.01:
                            self.log_result("Mise à jour stock après sortie", True, 
                                          f"Stock mis à jour: {stock['quantite_actuelle']} kg")
                        else:
                            self.log_result("Mise à jour stock après sortie", False, 
                                          f"Stock incorrect: {stock['quantite_actuelle']} kg, attendu: {expected_quantity} kg")
                else:
                    self.log_result("POST /api/mouvements - Sortie décimale", False, "Données du mouvement incorrectes")
            else:
                self.log_result("POST /api/mouvements - Sortie décimale", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/mouvements - Sortie décimale", False, "Exception", str(e))
        
        # Test 3: Ajustement avec quantité spécifique (problème principal rapporté)
        mouvement_ajustement = {
            "produit_id": self.test_produit_id,
            "type": "ajustement",
            "quantite": 15.75,
            "commentaire": "Inventaire physique - Ajustement après comptage"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_ajustement, headers=HEADERS)
            if response.status_code == 200:
                mouvement = response.json()
                if mouvement["type"] == "ajustement" and abs(mouvement["quantite"] - 15.75) < 0.01:
                    self.log_result("POST /api/mouvements - Ajustement spécifique", True, 
                                  f"Ajustement créé: ={mouvement['quantite']} kg")
                    
                    # Vérifier la mise à jour du stock (ajustement = quantité absolue)
                    time.sleep(0.5)
                    stock_response = requests.get(f"{BASE_URL}/stocks/{self.test_produit_id}")
                    if stock_response.status_code == 200:
                        stock = stock_response.json()
                        if abs(stock["quantite_actuelle"] - 15.75) < 0.01:
                            self.log_result("Mise à jour stock après ajustement", True, 
                                          f"Stock ajusté correctement: {stock['quantite_actuelle']} kg")
                        else:
                            self.log_result("Mise à jour stock après ajustement", False, 
                                          f"Stock incorrect: {stock['quantite_actuelle']} kg, attendu: 15.75 kg")
                else:
                    self.log_result("POST /api/mouvements - Ajustement spécifique", False, "Données du mouvement incorrectes")
            else:
                self.log_result("POST /api/mouvements - Ajustement spécifique", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/mouvements - Ajustement spécifique", False, "Exception", str(e))

    def test_edge_cases_quantities(self):
        """Test des cas limites pour les quantités"""
        print("\n=== TEST CAS LIMITES QUANTITÉS ===")
        
        if not self.test_produit_id:
            self.log_result("Test cas limites", False, "Pas de produit de test disponible")
            return
        
        # Test 1: Quantité très petite (0.01)
        mouvement_petit = {
            "produit_id": self.test_produit_id,
            "type": "ajustement",
            "quantite": 0.01,
            "commentaire": "Test quantité très petite"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_petit, headers=HEADERS)
            if response.status_code == 200:
                self.log_result("Quantité très petite (0.01)", True, "Quantité très petite acceptée")
            else:
                self.log_result("Quantité très petite (0.01)", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Quantité très petite (0.01)", False, "Exception", str(e))
        
        # Test 2: Quantité avec plusieurs décimales
        mouvement_decimal = {
            "produit_id": self.test_produit_id,
            "type": "ajustement",
            "quantite": 7.123,
            "commentaire": "Test quantité avec 3 décimales"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_decimal, headers=HEADERS)
            if response.status_code == 200:
                mouvement = response.json()
                # Vérifier que la quantité est correctement stockée
                if abs(mouvement["quantite"] - 7.123) < 0.001:
                    self.log_result("Quantité 3 décimales (7.123)", True, f"Quantité précise: {mouvement['quantite']}")
                else:
                    self.log_result("Quantité 3 décimales (7.123)", False, f"Précision perdue: {mouvement['quantite']}")
            else:
                self.log_result("Quantité 3 décimales (7.123)", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Quantité 3 décimales (7.123)", False, "Exception", str(e))
        
        # Test 3: Quantité négative (doit être rejetée pour entrée/sortie)
        mouvement_negatif = {
            "produit_id": self.test_produit_id,
            "type": "entree",
            "quantite": -5.0,
            "commentaire": "Test quantité négative"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_negatif, headers=HEADERS)
            if response.status_code == 400:
                self.log_result("Quantité négative rejetée", True, "Quantité négative correctement rejetée")
            elif response.status_code == 200:
                self.log_result("Quantité négative rejetée", False, "Quantité négative acceptée à tort")
            else:
                self.log_result("Quantité négative rejetée", False, f"Erreur inattendue {response.status_code}")
        except Exception as e:
            self.log_result("Quantité négative rejetée", False, "Exception", str(e))

    def test_product_stock_relationship(self):
        """Test de la relation produit-stock"""
        print("\n=== TEST RELATION PRODUIT-STOCK ===")
        
        if not self.test_produit_id:
            self.log_result("Test relation produit-stock", False, "Pas de produit de test disponible")
            return
        
        # Récupérer les informations du produit
        try:
            produit_response = requests.get(f"{BASE_URL}/produits/{self.test_produit_id}")
            if produit_response.status_code == 200:
                produit = produit_response.json()
                
                # Récupérer les informations du stock correspondant
                stock_response = requests.get(f"{BASE_URL}/stocks/{self.test_produit_id}")
                if stock_response.status_code == 200:
                    stock = stock_response.json()
                    
                    # Vérifier la cohérence des données
                    if stock["produit_id"] == produit["id"]:
                        self.log_result("Liaison produit-stock ID", True, "IDs cohérents")
                    else:
                        self.log_result("Liaison produit-stock ID", False, "IDs incohérents")
                    
                    if stock["produit_nom"] == produit["nom"]:
                        self.log_result("Liaison produit-stock nom", True, "Noms cohérents")
                    else:
                        self.log_result("Liaison produit-stock nom", False, 
                                      f"Noms incohérents: stock='{stock['produit_nom']}', produit='{produit['nom']}'")
                    
                    # Vérifier que l'unité est cohérente
                    if "unite" in stock and stock.get("unite") == produit.get("unite"):
                        self.log_result("Liaison produit-stock unité", True, f"Unité cohérente: {stock['unite']}")
                    else:
                        self.log_result("Liaison produit-stock unité", False, 
                                      f"Unités incohérentes: stock='{stock.get('unite')}', produit='{produit.get('unite')}'")
                else:
                    self.log_result("Récupération stock", False, f"Erreur {stock_response.status_code}")
            else:
                self.log_result("Récupération produit", False, f"Erreur {produit_response.status_code}")
        except Exception as e:
            self.log_result("Test relation produit-stock", False, "Exception", str(e))

    def test_stock_history_consistency(self):
        """Test de la cohérence de l'historique des stocks"""
        print("\n=== TEST COHÉRENCE HISTORIQUE STOCKS ===")
        
        if not self.test_produit_id:
            self.log_result("Test historique", False, "Pas de produit de test disponible")
            return
        
        # Récupérer l'historique des mouvements pour ce produit
        try:
            response = requests.get(f"{BASE_URL}/mouvements")
            if response.status_code == 200:
                tous_mouvements = response.json()
                mouvements_produit = [m for m in tous_mouvements if m["produit_id"] == self.test_produit_id]
                
                if len(mouvements_produit) > 0:
                    self.log_result("Historique mouvements produit", True, 
                                  f"{len(mouvements_produit)} mouvement(s) trouvé(s)")
                    
                    # Calculer le stock théorique basé sur l'historique
                    stock_theorique = 0.0
                    for mouvement in reversed(mouvements_produit):  # Du plus ancien au plus récent
                        if mouvement["type"] == "entree":
                            stock_theorique += mouvement["quantite"]
                        elif mouvement["type"] == "sortie":
                            stock_theorique -= mouvement["quantite"]
                        elif mouvement["type"] == "ajustement":
                            stock_theorique = mouvement["quantite"]  # Ajustement = valeur absolue
                    
                    # Comparer avec le stock actuel
                    stock_response = requests.get(f"{BASE_URL}/stocks/{self.test_produit_id}")
                    if stock_response.status_code == 200:
                        stock_actuel = stock_response.json()["quantite_actuelle"]
                        
                        if abs(stock_actuel - stock_theorique) < 0.01:
                            self.log_result("Cohérence stock-historique", True, 
                                          f"Stock cohérent: actuel={stock_actuel}, théorique={stock_theorique}")
                        else:
                            self.log_result("Cohérence stock-historique", False, 
                                          f"Incohérence: actuel={stock_actuel}, théorique={stock_theorique}")
                    else:
                        self.log_result("Récupération stock actuel", False, "Erreur récupération stock")
                else:
                    self.log_result("Historique mouvements produit", False, "Aucun mouvement trouvé")
            else:
                self.log_result("Récupération historique", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("Test historique", False, "Exception", str(e))

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🧪 DÉBUT DES TESTS GESTION DES STOCKS")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Échec du setup - Arrêt des tests")
            return
        
        # Tests principaux
        self.test_stocks_api_endpoints()
        self.test_stock_quantity_updates()
        self.test_mouvements_api_endpoints()
        self.test_mouvement_creation_with_quantities()
        self.test_edge_cases_quantities()
        self.test_product_stock_relationship()
        self.test_stock_history_consistency()
        
        # Résumé
        self.print_summary()

    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS GESTION DES STOCKS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
                    if result["details"]:
                        print(f"     Détails: {result['details']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_suite = StockManagementTestSuite()
    test_suite.run_all_tests()