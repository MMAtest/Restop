#!/usr/bin/env python3
"""
Test frontend API connectivity and CORS
"""

import requests
import json
from datetime import datetime

# Configuration from frontend .env
FRONTEND_BACKEND_URL = "https://resto-inventory-32.preview.emergentagent.com"
API_BASE = f"{FRONTEND_BACKEND_URL}/api"

class FrontendAPITest:
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
    
    def test_frontend_backend_connectivity(self):
        """Test la connectivité depuis le point de vue frontend"""
        print("\n=== TEST CONNECTIVITÉ FRONTEND → BACKEND ===")
        
        # Headers que le frontend utiliserait
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://resto-inventory-32.preview.emergentagent.com',  # Simulate frontend origin
            'Referer': 'https://resto-inventory-32.preview.emergentagent.com/'
        }
        
        # Test 1: GET /api/produits (comme DataGridsPage le fait)
        try:
            response = requests.get(f"{API_BASE}/produits", headers=headers)
            print(f"GET /api/produits - Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Frontend GET /api/produits", True, 
                              f"Récupéré {len(data)} produits")
                
                # Vérifier les headers CORS
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                if any(cors_headers.values()):
                    self.log_result("CORS Headers Present", True, f"Headers: {cors_headers}")
                else:
                    self.log_result("CORS Headers Present", False, "Aucun header CORS détecté")
                    
            else:
                self.log_result("Frontend GET /api/produits", False, 
                              f"Erreur HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Frontend GET /api/produits", False, f"Exception: {str(e)}")
        
        # Test 2: GET /api/fournisseurs
        try:
            response = requests.get(f"{API_BASE}/fournisseurs", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Frontend GET /api/fournisseurs", True, 
                              f"Récupéré {len(data)} fournisseurs")
            else:
                self.log_result("Frontend GET /api/fournisseurs", False, 
                              f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Frontend GET /api/fournisseurs", False, f"Exception: {str(e)}")
        
        # Test 3: GET /api/recettes
        try:
            response = requests.get(f"{API_BASE}/recettes", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Frontend GET /api/recettes", True, 
                              f"Récupéré {len(data)} recettes")
            else:
                self.log_result("Frontend GET /api/recettes", False, 
                              f"Erreur HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Frontend GET /api/recettes", False, f"Exception: {str(e)}")
    
    def test_preflight_requests(self):
        """Test les requêtes preflight CORS"""
        print("\n=== TEST REQUÊTES PREFLIGHT CORS ===")
        
        # Simuler une requête preflight
        headers = {
            'Origin': 'https://resto-inventory-32.preview.emergentagent.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'content-type'
        }
        
        try:
            response = requests.options(f"{API_BASE}/produits", headers=headers)
            print(f"OPTIONS /api/produits - Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code in [200, 204]:
                self.log_result("CORS Preflight", True, "Preflight réussi")
            else:
                self.log_result("CORS Preflight", False, 
                              f"Preflight échoué: {response.status_code}")
                
        except Exception as e:
            self.log_result("CORS Preflight", False, f"Exception: {str(e)}")
    
    def test_data_structure_compatibility(self):
        """Test la compatibilité des structures de données avec AG-Grid"""
        print("\n=== TEST COMPATIBILITÉ STRUCTURES DONNÉES ===")
        
        try:
            # Test structure produits
            response = requests.get(f"{API_BASE}/produits")
            if response.status_code == 200:
                products = response.json()
                if len(products) > 0:
                    first_product = products[0]
                    
                    # Champs requis pour ProductsDataGrid
                    required_fields = ['id', 'nom', 'categorie', 'unite', 'prix_achat', 'fournisseur_nom', 'created_at']
                    missing_fields = [field for field in required_fields if field not in first_product]
                    
                    if not missing_fields:
                        self.log_result("Structure Produits Compatible", True, 
                                      "Tous les champs requis présents")
                    else:
                        self.log_result("Structure Produits Compatible", False, 
                                      f"Champs manquants: {missing_fields}")
                    
                    # Vérifier les types de données
                    type_issues = []
                    if not isinstance(first_product.get('id'), str):
                        type_issues.append(f"id: {type(first_product.get('id'))}")
                    if not isinstance(first_product.get('nom'), str):
                        type_issues.append(f"nom: {type(first_product.get('nom'))}")
                    
                    if not type_issues:
                        self.log_result("Types Données Produits", True, "Types corrects")
                    else:
                        self.log_result("Types Données Produits", False, f"Types incorrects: {type_issues}")
                        
        except Exception as e:
            self.log_result("Structure Produits Compatible", False, f"Exception: {str(e)}")
    
    def test_axios_simulation(self):
        """Simuler les appels axios du frontend"""
        print("\n=== TEST SIMULATION AXIOS FRONTEND ===")
        
        # Simuler exactement ce que fait DataGridsPage.jsx
        try:
            # Simuler process.env.REACT_APP_BACKEND_URL
            BACKEND_URL = "https://resto-inventory-32.preview.emergentagent.com"
            API = f"{BACKEND_URL}/api"
            
            print(f"BACKEND_URL utilisé: {BACKEND_URL}")
            print(f"API URL: {API}")
            
            # Test fetchProducts()
            response = requests.get(f"{API}/produits")
            if response.status_code == 200:
                products = response.json()
                self.log_result("Axios Simulation - fetchProducts", True, 
                              f"Récupéré {len(products)} produits")
                
                # Simuler setProducts(response.data)
                print(f"Simulation setProducts() avec {len(products)} éléments")
                
            else:
                self.log_result("Axios Simulation - fetchProducts", False, 
                              f"Erreur {response.status_code}")
                
            # Test fetchSuppliers()
            response = requests.get(f"{API}/fournisseurs")
            if response.status_code == 200:
                suppliers = response.json()
                self.log_result("Axios Simulation - fetchSuppliers", True, 
                              f"Récupéré {len(suppliers)} fournisseurs")
            else:
                self.log_result("Axios Simulation - fetchSuppliers", False, 
                              f"Erreur {response.status_code}")
                
            # Test fetchRecipes()
            response = requests.get(f"{API}/recettes")
            if response.status_code == 200:
                recipes = response.json()
                self.log_result("Axios Simulation - fetchRecipes", True, 
                              f"Récupéré {len(recipes)} recettes")
            else:
                self.log_result("Axios Simulation - fetchRecipes", False, 
                              f"Erreur {response.status_code}")
                
        except Exception as e:
            self.log_result("Axios Simulation", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🌐 TESTS CONNECTIVITÉ FRONTEND-BACKEND")
        print("=" * 60)
        
        self.test_frontend_backend_connectivity()
        self.test_preflight_requests()
        self.test_data_structure_compatibility()
        self.test_axios_simulation()
        
        self.print_summary()
    
    def print_summary(self):
        """Afficher un résumé des résultats"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ TESTS FRONTEND-BACKEND")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ PROBLÈMES IDENTIFIÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n🔍 DIAGNOSTIC:")
        if passed_tests == total_tests:
            print("✅ Tous les tests passent - Le problème n'est PAS côté backend")
            print("✅ Les APIs retournent des données correctement")
            print("✅ La structure des données est compatible avec AG-Grid")
            print("🔍 Le problème est probablement côté frontend (JavaScript/React)")
        else:
            print("⚠️  Des problèmes ont été détectés côté backend/connectivité")

if __name__ == "__main__":
    test_suite = FrontendAPITest()
    test_suite.run_all_tests()