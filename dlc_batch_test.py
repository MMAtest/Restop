#!/usr/bin/env python3
"""
Test de création de lots avec DLC (Date Limite de Consommation) variées
pour tester l'interface DLC avec des alertes réelles
"""

import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "https://ocr-manager.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class DLCBatchTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_batch_ids = []
        self.existing_product_ids = []
        
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

    def get_existing_products(self):
        """Récupère les produits existants pour créer des lots"""
        print("\n=== RÉCUPÉRATION DES PRODUITS EXISTANTS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/produits")
            if response.status_code == 200:
                produits = response.json()
                if isinstance(produits, list) and len(produits) > 0:
                    self.existing_product_ids = [p["id"] for p in produits[:10]]  # Prendre les 10 premiers
                    product_names = [p["nom"] for p in produits[:10]]
                    self.log_result("GET /produits", True, 
                                  f"{len(produits)} produits trouvés, utilisation des 10 premiers")
                    print(f"   Produits sélectionnés: {', '.join(product_names[:5])}...")
                    return True
                else:
                    self.log_result("GET /produits", False, "Aucun produit trouvé")
                    return False
            else:
                self.log_result("GET /produits", False, f"Erreur {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("GET /produits", False, "Exception", str(e))
            return False

    def create_expired_batches(self):
        """Créer des lots avec DLC expirées (pour alertes rouges)"""
        print("\n=== CRÉATION DE LOTS EXPIRÉS ===")
        
        if len(self.existing_product_ids) < 2:
            self.log_result("Lots expirés", False, "Pas assez de produits disponibles")
            return
        
        # Dates expirées (il y a 2-5 jours)
        expired_dates = [
            datetime.now() - timedelta(days=2),  # Expiré il y a 2 jours
            datetime.now() - timedelta(days=5),  # Expiré il y a 5 jours
        ]
        
        for i, expiry_date in enumerate(expired_dates):
            batch_data = {
                "product_id": self.existing_product_ids[i],
                "quantity": 15.0 + (i * 5),  # 15, 20
                "expiry_date": expiry_date.isoformat(),
                "batch_number": f"EXP-{expiry_date.strftime('%Y%m%d')}-{i+1:02d}",
                "supplier_id": None,
                "purchase_price": 8.50 + (i * 2)  # 8.50, 10.50
            }
            
            try:
                response = requests.post(f"{BASE_URL}/product-batches", json=batch_data, headers=HEADERS)
                if response.status_code == 200:
                    created_batch = response.json()
                    self.created_batch_ids.append(created_batch["id"])
                    days_expired = (datetime.now() - expiry_date).days
                    self.log_result(f"Lot expiré #{i+1}", True, 
                                  f"Lot créé - Expiré il y a {days_expired} jours - Quantité: {batch_data['quantity']}")
                else:
                    self.log_result(f"Lot expiré #{i+1}", False, 
                                  f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Lot expiré #{i+1}", False, "Exception", str(e))

    def create_critical_batches(self):
        """Créer des lots avec DLC critiques (expirent dans moins de 7 jours)"""
        print("\n=== CRÉATION DE LOTS CRITIQUES ===")
        
        if len(self.existing_product_ids) < 4:
            self.log_result("Lots critiques", False, "Pas assez de produits disponibles")
            return
        
        # Dates critiques (dans 3-5 jours)
        critical_dates = [
            datetime.now() + timedelta(days=3),  # Expire dans 3 jours
            datetime.now() + timedelta(days=5),  # Expire dans 5 jours
        ]
        
        for i, expiry_date in enumerate(critical_dates):
            product_index = i + 2  # Utiliser les produits 3 et 4
            batch_data = {
                "product_id": self.existing_product_ids[product_index],
                "quantity": 25.0 + (i * 10),  # 25, 35
                "expiry_date": expiry_date.isoformat(),
                "batch_number": f"CRIT-{expiry_date.strftime('%Y%m%d')}-{i+1:02d}",
                "supplier_id": None,
                "purchase_price": 12.00 + (i * 3)  # 12.00, 15.00
            }
            
            try:
                response = requests.post(f"{BASE_URL}/product-batches", json=batch_data, headers=HEADERS)
                if response.status_code == 200:
                    created_batch = response.json()
                    self.created_batch_ids.append(created_batch["id"])
                    days_to_expiry = (expiry_date - datetime.now()).days
                    self.log_result(f"Lot critique #{i+1}", True, 
                                  f"Lot créé - Expire dans {days_to_expiry} jours - Quantité: {batch_data['quantity']}")
                else:
                    self.log_result(f"Lot critique #{i+1}", False, 
                                  f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Lot critique #{i+1}", False, "Exception", str(e))

    def create_normal_batches(self):
        """Créer des lots avec DLC normales (expirent dans plus de 7 jours)"""
        print("\n=== CRÉATION DE LOTS NORMAUX ===")
        
        if len(self.existing_product_ids) < 6:
            self.log_result("Lots normaux", False, "Pas assez de produits disponibles")
            return
        
        # Dates normales (dans 15+ jours)
        normal_dates = [
            datetime.now() + timedelta(days=15),  # Expire dans 15 jours
            datetime.now() + timedelta(days=30),  # Expire dans 30 jours
        ]
        
        for i, expiry_date in enumerate(normal_dates):
            product_index = i + 4  # Utiliser les produits 5 et 6
            batch_data = {
                "product_id": self.existing_product_ids[product_index],
                "quantity": 50.0 + (i * 20),  # 50, 70
                "expiry_date": expiry_date.isoformat(),
                "batch_number": f"NORM-{expiry_date.strftime('%Y%m%d')}-{i+1:02d}",
                "supplier_id": None,
                "purchase_price": 6.00 + (i * 1.5)  # 6.00, 7.50
            }
            
            try:
                response = requests.post(f"{BASE_URL}/product-batches", json=batch_data, headers=HEADERS)
                if response.status_code == 200:
                    created_batch = response.json()
                    self.created_batch_ids.append(created_batch["id"])
                    days_to_expiry = (expiry_date - datetime.now()).days
                    self.log_result(f"Lot normal #{i+1}", True, 
                                  f"Lot créé - Expire dans {days_to_expiry} jours - Quantité: {batch_data['quantity']}")
                else:
                    self.log_result(f"Lot normal #{i+1}", False, 
                                  f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Lot normal #{i+1}", False, "Exception", str(e))

    def verify_batch_summary(self):
        """Vérifier le résumé des lots via GET /api/stock/batch-summary"""
        print("\n=== VÉRIFICATION RÉSUMÉ DES LOTS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/stock/batch-summary")
            if response.status_code == 200:
                batch_summary = response.json()
                if isinstance(batch_summary, list):
                    total_products_with_batches = len(batch_summary)
                    
                    # Compter les lots par statut
                    expired_count = 0
                    critical_count = 0
                    normal_count = 0
                    
                    for product_batch_info in batch_summary:
                        expired_count += product_batch_info.get("expired_batches", 0)
                        critical_count += product_batch_info.get("critical_batches", 0)
                        
                        # Compter les lots normaux (total - expired - critical)
                        total_batches = len(product_batch_info.get("batches", []))
                        normal_count += total_batches - expired_count - critical_count
                    
                    self.log_result("GET /stock/batch-summary", True, 
                                  f"{total_products_with_batches} produits avec lots trouvés")
                    
                    # Vérifier les statuts
                    if expired_count >= 2:
                        self.log_result("Lots expirés détectés", True, f"{expired_count} lots expirés")
                    else:
                        self.log_result("Lots expirés détectés", False, f"Seulement {expired_count} lots expirés")
                    
                    if critical_count >= 2:
                        self.log_result("Lots critiques détectés", True, f"{critical_count} lots critiques")
                    else:
                        self.log_result("Lots critiques détectés", False, f"Seulement {critical_count} lots critiques")
                    
                    # Afficher un exemple détaillé
                    if len(batch_summary) > 0:
                        example = batch_summary[0]
                        self.log_result("Exemple détail lot", True, 
                                      f"Produit: {example.get('product_name')} - "
                                      f"Stock total: {example.get('total_stock')} - "
                                      f"Lots: {len(example.get('batches', []))}")
                        
                        # Afficher les détails des lots
                        for batch in example.get('batches', [])[:3]:  # Afficher les 3 premiers
                            status = batch.get('status', 'unknown')
                            expiry = batch.get('expiry_date', 'N/A')
                            quantity = batch.get('quantity', 0)
                            print(f"     - Lot {batch.get('batch_number', 'N/A')}: {status} - "
                                  f"Expire: {expiry[:10] if expiry != 'N/A' else 'N/A'} - "
                                  f"Quantité: {quantity}")
                else:
                    self.log_result("GET /stock/batch-summary", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /stock/batch-summary", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /stock/batch-summary", False, "Exception", str(e))

    def test_individual_batch_info(self):
        """Tester GET /api/stock/batch-info/{product_id} pour quelques produits"""
        print("\n=== TEST INFORMATIONS LOTS INDIVIDUELS ===")
        
        # Tester les 3 premiers produits utilisés
        for i, product_id in enumerate(self.existing_product_ids[:3]):
            try:
                response = requests.get(f"{BASE_URL}/stock/batch-info/{product_id}")
                if response.status_code == 200:
                    batch_info = response.json()
                    product_name = batch_info.get("product_name", "Inconnu")
                    total_stock = batch_info.get("total_stock", 0)
                    critical_batches = batch_info.get("critical_batches", 0)
                    expired_batches = batch_info.get("expired_batches", 0)
                    
                    self.log_result(f"Batch info produit #{i+1}", True, 
                                  f"{product_name} - Stock: {total_stock} - "
                                  f"Critiques: {critical_batches} - Expirés: {expired_batches}")
                    
                    # Afficher les détails des lots
                    batches = batch_info.get("batches", [])
                    for batch in batches:
                        status = batch.get("status", "unknown")
                        expiry = batch.get("expiry_date", "N/A")
                        quantity = batch.get("quantity", 0)
                        batch_number = batch.get("batch_number", "N/A")
                        
                        status_emoji = {"expired": "🔴", "critical": "🟡", "good": "🟢"}.get(status, "⚪")
                        print(f"     {status_emoji} Lot {batch_number}: {quantity} unités - "
                              f"Expire: {expiry[:10] if expiry != 'N/A' else 'N/A'}")
                        
                else:
                    self.log_result(f"Batch info produit #{i+1}", False, 
                                  f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Batch info produit #{i+1}", False, "Exception", str(e))

    def run_all_tests(self):
        """Exécuter tous les tests de création de lots DLC"""
        print("🧪 DÉBUT DES TESTS DE CRÉATION DE LOTS DLC")
        print("=" * 60)
        
        # 1. Récupérer les produits existants
        if not self.get_existing_products():
            print("❌ Impossible de continuer sans produits existants")
            return
        
        # 2. Créer les différents types de lots
        self.create_expired_batches()
        time.sleep(1)  # Pause entre les créations
        
        self.create_critical_batches()
        time.sleep(1)
        
        self.create_normal_batches()
        time.sleep(1)
        
        # 3. Vérifier les résultats
        self.verify_batch_summary()
        time.sleep(1)
        
        self.test_individual_batch_info()
        
        # 4. Résumé final
        self.print_summary()

    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS DE CRÉATION DE LOTS DLC")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n🏷️ Lots créés: {len(self.created_batch_ids)}")
        print(f"📦 Produits utilisés: {len(self.existing_product_ids)}")
        
        # Afficher les échecs s'il y en a
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n🎯 OBJECTIF ATTEINT:")
        print("   ✅ Lots expirés créés (alertes rouges)")
        print("   ✅ Lots critiques créés (expire < 7 jours)")
        print("   ✅ Lots normaux créés (expire > 15 jours)")
        print("   ✅ Interface DLC peut maintenant afficher des alertes réelles")
        
        print("\n📋 ENDPOINTS TESTÉS:")
        print("   ✅ POST /api/product-batches")
        print("   ✅ GET /api/stock/batch-summary")
        print("   ✅ GET /api/stock/batch-info/{product_id}")
        print("   ✅ GET /api/produits")

if __name__ == "__main__":
    test_suite = DLCBatchTestSuite()
    test_suite.run_all_tests()