#!/usr/bin/env python3
"""
Test complet du backend de gestion des stocks pour restaurant
Tests des APIs: Fournisseurs, Produits, Stocks, Mouvements, Export/Import Excel, Dashboard
"""

import requests
import json
import io
import pandas as pd
from datetime import datetime
import time
import os

# Configuration
BASE_URL = "https://7dcd9914-c4fe-4243-9f17-efffeffdde7b.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class StockTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_id = None
        self.created_produit_id = None
        self.created_recette_id = None
        self.demo_produits_ids = []
        
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
    
    def test_fournisseurs_crud(self):
        """Test complet CRUD des fournisseurs"""
        print("\n=== TEST API FOURNISSEURS ===")
        
        # Test POST - Création fournisseur
        fournisseur_data = {
            "nom": "Fournisseur Test Alimentaire",
            "contact": "Jean Dupont",
            "email": "jean.dupont@test-alimentaire.fr",
            "telephone": "01.23.45.67.89",
            "adresse": "123 Rue des Marchés, 75001 Paris"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/fournisseurs", json=fournisseur_data, headers=HEADERS)
            if response.status_code == 200:
                created_fournisseur = response.json()
                self.created_fournisseur_id = created_fournisseur["id"]
                self.log_result("POST /fournisseurs", True, "Fournisseur créé avec succès")
            else:
                self.log_result("POST /fournisseurs", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /fournisseurs", False, "Exception lors de la création", str(e))
            return
        
        # Test GET - Liste fournisseurs
        try:
            response = requests.get(f"{BASE_URL}/fournisseurs")
            if response.status_code == 200:
                fournisseurs = response.json()
                if isinstance(fournisseurs, list) and len(fournisseurs) > 0:
                    self.log_result("GET /fournisseurs", True, f"{len(fournisseurs)} fournisseur(s) récupéré(s)")
                else:
                    self.log_result("GET /fournisseurs", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET /fournisseurs", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /fournisseurs", False, "Exception lors de la récupération", str(e))
        
        # Test GET by ID - Fournisseur spécifique
        if self.created_fournisseur_id:
            try:
                response = requests.get(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}")
                if response.status_code == 200:
                    fournisseur = response.json()
                    if fournisseur["nom"] == fournisseur_data["nom"]:
                        self.log_result("GET /fournisseurs/{id}", True, "Fournisseur récupéré correctement")
                    else:
                        self.log_result("GET /fournisseurs/{id}", False, "Données incorrectes")
                else:
                    self.log_result("GET /fournisseurs/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /fournisseurs/{id}", False, "Exception", str(e))
        
        # Test PUT - Modification fournisseur
        if self.created_fournisseur_id:
            updated_data = fournisseur_data.copy()
            updated_data["nom"] = "Fournisseur Test Modifié"
            updated_data["email"] = "nouveau@test-alimentaire.fr"
            
            try:
                response = requests.put(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}", 
                                      json=updated_data, headers=HEADERS)
                if response.status_code == 200:
                    updated_fournisseur = response.json()
                    if updated_fournisseur["nom"] == updated_data["nom"]:
                        self.log_result("PUT /fournisseurs/{id}", True, "Fournisseur modifié avec succès")
                    else:
                        self.log_result("PUT /fournisseurs/{id}", False, "Modification non appliquée")
                else:
                    self.log_result("PUT /fournisseurs/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("PUT /fournisseurs/{id}", False, "Exception lors de la modification", str(e))
    
    def test_produits_crud(self):
        """Test complet CRUD des produits"""
        print("\n=== TEST API PRODUITS ===")
        
        # Test POST - Création produit
        produit_data = {
            "nom": "Tomates Bio Premium",
            "description": "Tomates biologiques de qualité supérieure",
            "categorie": "Légumes",
            "unite": "kg",
            "prix_achat": 3.50,
            "fournisseur_id": self.created_fournisseur_id
        }
        
        try:
            response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
            if response.status_code == 200:
                created_produit = response.json()
                self.created_produit_id = created_produit["id"]
                # Vérifier que le nom du fournisseur est bien lié
                if created_produit.get("fournisseur_nom"):
                    self.log_result("POST /produits", True, "Produit créé avec liaison fournisseur")
                else:
                    self.log_result("POST /produits", True, "Produit créé (sans liaison fournisseur)")
            else:
                self.log_result("POST /produits", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /produits", False, "Exception lors de la création", str(e))
            return
        
        # Vérifier que le stock a été créé automatiquement
        if self.created_produit_id:
            try:
                response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if response.status_code == 200:
                    stock = response.json()
                    if stock["quantite_actuelle"] == 0.0:
                        self.log_result("Auto-création stock", True, "Stock créé automatiquement à 0")
                    else:
                        self.log_result("Auto-création stock", False, f"Stock incorrect: {stock['quantite_actuelle']}")
                else:
                    self.log_result("Auto-création stock", False, "Stock non créé automatiquement")
            except Exception as e:
                self.log_result("Auto-création stock", False, "Exception", str(e))
        
        # Test GET - Liste produits
        try:
            response = requests.get(f"{BASE_URL}/produits")
            if response.status_code == 200:
                produits = response.json()
                if isinstance(produits, list) and len(produits) > 0:
                    self.log_result("GET /produits", True, f"{len(produits)} produit(s) récupéré(s)")
                else:
                    self.log_result("GET /produits", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET /produits", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /produits", False, "Exception", str(e))
        
        # Test PUT - Modification produit
        if self.created_produit_id:
            updated_data = produit_data.copy()
            updated_data["nom"] = "Tomates Bio Premium Modifiées"
            updated_data["prix_achat"] = 4.00
            
            try:
                response = requests.put(f"{BASE_URL}/produits/{self.created_produit_id}", 
                                      json=updated_data, headers=HEADERS)
                if response.status_code == 200:
                    updated_produit = response.json()
                    if updated_produit["nom"] == updated_data["nom"]:
                        self.log_result("PUT /produits/{id}", True, "Produit modifié avec succès")
                        
                        # Vérifier que le nom a été mis à jour dans le stock
                        stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                        if stock_response.status_code == 200:
                            stock = stock_response.json()
                            if stock["produit_nom"] == updated_data["nom"]:
                                self.log_result("Mise à jour nom dans stock", True, "Nom mis à jour dans stock")
                            else:
                                self.log_result("Mise à jour nom dans stock", False, "Nom non mis à jour dans stock")
                    else:
                        self.log_result("PUT /produits/{id}", False, "Modification non appliquée")
                else:
                    self.log_result("PUT /produits/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("PUT /produits/{id}", False, "Exception", str(e))
    
    def test_stocks_api(self):
        """Test API de gestion des stocks"""
        print("\n=== TEST API STOCKS ===")
        
        # Test GET - Liste stocks
        try:
            response = requests.get(f"{BASE_URL}/stocks")
            if response.status_code == 200:
                stocks = response.json()
                if isinstance(stocks, list):
                    self.log_result("GET /stocks", True, f"{len(stocks)} stock(s) récupéré(s)")
                    
                    # Vérifier la structure des données
                    if len(stocks) > 0:
                        stock = stocks[0]
                        required_fields = ["quantite_actuelle", "quantite_min", "derniere_maj"]
                        if all(field in stock for field in required_fields):
                            self.log_result("Structure données stocks", True, "Tous les champs requis présents")
                        else:
                            self.log_result("Structure données stocks", False, "Champs manquants")
                else:
                    self.log_result("GET /stocks", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /stocks", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /stocks", False, "Exception", str(e))
        
        # Test PUT - Mise à jour stock
        if self.created_produit_id:
            stock_update = {
                "quantite_actuelle": 25.5,
                "quantite_min": 5.0,
                "quantite_max": 100.0
            }
            
            try:
                response = requests.put(f"{BASE_URL}/stocks/{self.created_produit_id}", 
                                      json=stock_update, headers=HEADERS)
                if response.status_code == 200:
                    updated_stock = response.json()
                    if (updated_stock["quantite_actuelle"] == stock_update["quantite_actuelle"] and
                        updated_stock["quantite_min"] == stock_update["quantite_min"]):
                        self.log_result("PUT /stocks/{id}", True, "Stock mis à jour avec succès")
                        
                        # Vérifier que derniere_maj a été mise à jour
                        if "derniere_maj" in updated_stock:
                            self.log_result("Mise à jour derniere_maj", True, "Date de dernière MAJ mise à jour")
                        else:
                            self.log_result("Mise à jour derniere_maj", False, "Date non mise à jour")
                    else:
                        self.log_result("PUT /stocks/{id}", False, "Valeurs non mises à jour correctement")
                else:
                    self.log_result("PUT /stocks/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("PUT /stocks/{id}", False, "Exception", str(e))
    
    def test_mouvements_stock(self):
        """Test API des mouvements de stock"""
        print("\n=== TEST API MOUVEMENTS STOCK ===")
        
        if not self.created_produit_id:
            self.log_result("Mouvements stock", False, "Pas de produit créé pour les tests")
            return
        
        # Test POST - Mouvement d'entrée
        mouvement_entree = {
            "produit_id": self.created_produit_id,
            "type": "entree",
            "quantite": 50.0,
            "reference": "BON-001",
            "fournisseur_id": self.created_fournisseur_id,
            "commentaire": "Livraison hebdomadaire"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_entree, headers=HEADERS)
            if response.status_code == 200:
                mouvement = response.json()
                if mouvement["type"] == "entree" and mouvement["quantite"] == 50.0:
                    self.log_result("POST /mouvements (entrée)", True, "Mouvement d'entrée créé")
                    
                    # Vérifier que le stock a été mis à jour
                    time.sleep(0.5)  # Petite pause pour la mise à jour
                    stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                    if stock_response.status_code == 200:
                        stock = stock_response.json()
                        expected_quantity = 25.5 + 50.0  # quantité précédente + entrée
                        if abs(stock["quantite_actuelle"] - expected_quantity) < 0.01:
                            self.log_result("Mise à jour stock (entrée)", True, f"Stock mis à jour: {stock['quantite_actuelle']}")
                        else:
                            self.log_result("Mise à jour stock (entrée)", False, f"Stock incorrect: {stock['quantite_actuelle']}, attendu: {expected_quantity}")
                else:
                    self.log_result("POST /mouvements (entrée)", False, "Données du mouvement incorrectes")
            else:
                self.log_result("POST /mouvements (entrée)", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /mouvements (entrée)", False, "Exception", str(e))
        
        # Test POST - Mouvement de sortie
        mouvement_sortie = {
            "produit_id": self.created_produit_id,
            "type": "sortie",
            "quantite": 15.0,
            "commentaire": "Utilisation cuisine"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_sortie, headers=HEADERS)
            if response.status_code == 200:
                self.log_result("POST /mouvements (sortie)", True, "Mouvement de sortie créé")
                
                # Vérifier la mise à jour du stock
                time.sleep(0.5)
                stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if stock_response.status_code == 200:
                    stock = stock_response.json()
                    expected_quantity = 75.5 - 15.0  # quantité après entrée - sortie
                    if abs(stock["quantite_actuelle"] - expected_quantity) < 0.01:
                        self.log_result("Mise à jour stock (sortie)", True, f"Stock mis à jour: {stock['quantite_actuelle']}")
                    else:
                        self.log_result("Mise à jour stock (sortie)", False, f"Stock incorrect: {stock['quantite_actuelle']}, attendu: {expected_quantity}")
            else:
                self.log_result("POST /mouvements (sortie)", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /mouvements (sortie)", False, "Exception", str(e))
        
        # Test POST - Ajustement
        mouvement_ajustement = {
            "produit_id": self.created_produit_id,
            "type": "ajustement",
            "quantite": 55.0,
            "commentaire": "Inventaire physique"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/mouvements", json=mouvement_ajustement, headers=HEADERS)
            if response.status_code == 200:
                self.log_result("POST /mouvements (ajustement)", True, "Ajustement créé")
                
                # Vérifier la mise à jour du stock
                time.sleep(0.5)
                stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if stock_response.status_code == 200:
                    stock = stock_response.json()
                    if abs(stock["quantite_actuelle"] - 55.0) < 0.01:
                        self.log_result("Mise à jour stock (ajustement)", True, f"Stock ajusté: {stock['quantite_actuelle']}")
                    else:
                        self.log_result("Mise à jour stock (ajustement)", False, f"Stock incorrect: {stock['quantite_actuelle']}")
            else:
                self.log_result("POST /mouvements (ajustement)", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /mouvements (ajustement)", False, "Exception", str(e))
        
        # Test GET - Historique mouvements
        try:
            response = requests.get(f"{BASE_URL}/mouvements")
            if response.status_code == 200:
                mouvements = response.json()
                if isinstance(mouvements, list) and len(mouvements) >= 3:
                    self.log_result("GET /mouvements", True, f"{len(mouvements)} mouvement(s) dans l'historique")
                    
                    # Vérifier l'ordre (plus récent en premier)
                    if len(mouvements) >= 2:
                        first_date = datetime.fromisoformat(mouvements[0]["date"].replace('Z', '+00:00'))
                        second_date = datetime.fromisoformat(mouvements[1]["date"].replace('Z', '+00:00'))
                        if first_date >= second_date:
                            self.log_result("Ordre chronologique mouvements", True, "Mouvements triés par date décroissante")
                        else:
                            self.log_result("Ordre chronologique mouvements", False, "Ordre incorrect")
                else:
                    self.log_result("GET /mouvements", False, f"Nombre de mouvements incorrect: {len(mouvements) if isinstance(mouvements, list) else 'non-liste'}")
            else:
                self.log_result("GET /mouvements", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /mouvements", False, "Exception", str(e))
    
    def test_export_excel(self):
        """Test export Excel"""
        print("\n=== TEST EXPORT EXCEL ===")
        
        try:
            response = requests.get(f"{BASE_URL}/export/stocks")
            if response.status_code == 200:
                # Vérifier le type de contenu
                content_type = response.headers.get('content-type', '')
                if 'spreadsheet' in content_type or 'excel' in content_type:
                    self.log_result("GET /export/stocks", True, "Fichier Excel généré avec succès")
                    
                    # Vérifier la taille du fichier (doit être > 0)
                    content_length = len(response.content)
                    if content_length > 1000:  # Un fichier Excel valide fait au moins 1KB
                        self.log_result("Taille fichier Excel", True, f"Fichier de {content_length} bytes")
                        
                        # Essayer de lire le contenu Excel
                        try:
                            df = pd.read_excel(io.BytesIO(response.content))
                            if len(df) > 0:
                                required_columns = ["Nom Produit", "Quantité Actuelle", "Quantité Min"]
                                if all(col in df.columns for col in required_columns):
                                    self.log_result("Structure Excel", True, f"Excel valide avec {len(df)} lignes")
                                else:
                                    self.log_result("Structure Excel", False, f"Colonnes manquantes. Colonnes: {list(df.columns)}")
                            else:
                                self.log_result("Contenu Excel", False, "Fichier Excel vide")
                        except Exception as e:
                            self.log_result("Lecture Excel", False, f"Impossible de lire le fichier: {str(e)}")
                    else:
                        self.log_result("Taille fichier Excel", False, f"Fichier trop petit: {content_length} bytes")
                else:
                    self.log_result("GET /export/stocks", False, f"Type de contenu incorrect: {content_type}")
            else:
                self.log_result("GET /export/stocks", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /export/stocks", False, "Exception", str(e))
    
    def test_import_excel(self):
        """Test import Excel"""
        print("\n=== TEST IMPORT EXCEL ===")
        
        if not self.created_produit_id:
            self.log_result("Import Excel", False, "Pas de produit pour tester l'import")
            return
        
        # Créer un fichier Excel de test
        test_data = {
            "Produit ID": [self.created_produit_id],
            "Nom Produit": ["Tomates Bio Premium Modifiées"],
            "Quantité Actuelle": [80.0],
            "Quantité Min": [10.0],
            "Quantité Max": [150.0]
        }
        
        df = pd.DataFrame(test_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Stocks', index=False)
        excel_buffer.seek(0)
        
        try:
            files = {'file': ('test_import.xlsx', excel_buffer.getvalue(), 
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = requests.post(f"{BASE_URL}/import/stocks", files=files)
            if response.status_code == 200:
                result = response.json()
                if "importées avec succès" in result.get("message", ""):
                    self.log_result("POST /import/stocks", True, "Import Excel réussi")
                    
                    # Vérifier que les données ont été mises à jour
                    time.sleep(0.5)
                    stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                    if stock_response.status_code == 200:
                        stock = stock_response.json()
                        if (abs(stock["quantite_actuelle"] - 80.0) < 0.01 and
                            abs(stock["quantite_min"] - 10.0) < 0.01):
                            self.log_result("Validation import Excel", True, "Données importées correctement")
                        else:
                            self.log_result("Validation import Excel", False, 
                                          f"Données incorrectes: actuelle={stock['quantite_actuelle']}, min={stock['quantite_min']}")
                else:
                    self.log_result("POST /import/stocks", False, f"Message d'erreur: {result.get('message')}")
            else:
                self.log_result("POST /import/stocks", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /import/stocks", False, "Exception", str(e))
    
    def test_dashboard_stats(self):
        """Test API statistiques dashboard"""
        print("\n=== TEST DASHBOARD STATS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_produits", "total_fournisseurs", "stocks_faibles", "stocks_recents"]
                
                if all(field in stats for field in required_fields):
                    self.log_result("GET /dashboard/stats", True, "Toutes les statistiques présentes")
                    
                    # Vérifier que les valeurs sont cohérentes
                    if (isinstance(stats["total_produits"], int) and stats["total_produits"] >= 0 and
                        isinstance(stats["total_fournisseurs"], int) and stats["total_fournisseurs"] >= 0):
                        self.log_result("Validation stats", True, 
                                      f"Produits: {stats['total_produits']}, Fournisseurs: {stats['total_fournisseurs']}")
                    else:
                        self.log_result("Validation stats", False, "Valeurs statistiques incorrectes")
                else:
                    missing = [f for f in required_fields if f not in stats]
                    self.log_result("GET /dashboard/stats", False, f"Champs manquants: {missing}")
            else:
                self.log_result("GET /dashboard/stats", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /dashboard/stats", False, "Exception", str(e))
    
    def test_demo_data_initialization(self):
        """Test initialisation des données de démonstration restaurant franco-italien"""
        print("\n=== TEST DONNÉES DÉMONSTRATION RESTAURANT FRANCO-ITALIEN ===")
        
        try:
            response = requests.post(f"{BASE_URL}/demo/init-french-italian-data", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                if "succès" in result.get("message", ""):
                    self.log_result("POST /demo/init-french-italian-data", True, 
                                  f"Données créées: {result.get('fournisseurs_crees', 0)} fournisseurs, "
                                  f"{result.get('produits_crees', 0)} produits, {result.get('recettes_creees', 0)} recettes")
                    
                    # Vérifier que les fournisseurs ont été créés
                    fournisseurs_response = requests.get(f"{BASE_URL}/fournisseurs")
                    if fournisseurs_response.status_code == 200:
                        fournisseurs = fournisseurs_response.json()
                        demo_fournisseurs = [f for f in fournisseurs if f["nom"] in 
                                           ["Fromagerie Laurent", "Boucherie Artisanale", "Pasta & Co", "Marché des Légumes"]]
                        if len(demo_fournisseurs) >= 4:
                            self.log_result("Fournisseurs démo créés", True, f"{len(demo_fournisseurs)} fournisseurs authentiques")
                        else:
                            self.log_result("Fournisseurs démo créés", False, f"Seulement {len(demo_fournisseurs)} fournisseurs trouvés")
                    
                    # Vérifier que les produits ont été créés
                    produits_response = requests.get(f"{BASE_URL}/produits")
                    if produits_response.status_code == 200:
                        produits = produits_response.json()
                        demo_produits = [p for p in produits if p["nom"] in 
                                       ["Mozzarella di Bufala", "Parmesan Reggiano 24 mois", "Spaghetti Artisanaux", 
                                        "Escalope de veau", "Tomates cerises", "Basilic frais"]]
                        if len(demo_produits) >= 6:
                            self.log_result("Produits démo créés", True, f"{len(demo_produits)} produits italiens/français")
                            # Stocker les IDs pour les tests de recettes
                            self.demo_produits_ids = [p["id"] for p in demo_produits[:4]]  # Prendre les 4 premiers
                        else:
                            self.log_result("Produits démo créés", False, f"Seulement {len(demo_produits)} produits trouvés")
                    
                    # Vérifier que les recettes ont été créées
                    recettes_response = requests.get(f"{BASE_URL}/recettes")
                    if recettes_response.status_code == 200:
                        recettes = recettes_response.json()
                        demo_recettes = [r for r in recettes if r["nom"] in 
                                       ["Spaghetti Carbonara", "Risotto aux Champignons", "Escalope Milanaise", "Salade Caprese"]]
                        if len(demo_recettes) >= 4:
                            self.log_result("Recettes démo créées", True, f"{len(demo_recettes)} recettes classiques")
                        else:
                            self.log_result("Recettes démo créées", False, f"Seulement {len(demo_recettes)} recettes trouvées")
                else:
                    self.log_result("POST /demo/init-french-italian-data", False, f"Message inattendu: {result.get('message')}")
            else:
                self.log_result("POST /demo/init-french-italian-data", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /demo/init-french-italian-data", False, "Exception", str(e))

    def test_recettes_crud(self):
        """Test complet CRUD des recettes"""
        print("\n=== TEST API GESTION RECETTES ===")
        
        # S'assurer qu'on a des produits pour les ingrédients
        if not self.demo_produits_ids and self.created_produit_id:
            self.demo_produits_ids = [self.created_produit_id]
        
        if not self.demo_produits_ids:
            self.log_result("Recettes CRUD", False, "Pas de produits disponibles pour créer des recettes")
            return
        
        # Test POST - Création recette avec ingrédients
        recette_data = {
            "nom": "Pasta Primavera Test",
            "description": "Pâtes aux légumes de saison",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 25,
            "prix_vente": 16.50,
            "instructions": "1. Cuire les pâtes\n2. Faire sauter les légumes\n3. Mélanger et servir",
            "ingredients": [
                {
                    "produit_id": self.demo_produits_ids[0],
                    "quantite": 400,
                    "unite": "g"
                }
            ]
        }
        
        if len(self.demo_produits_ids) > 1:
            recette_data["ingredients"].append({
                "produit_id": self.demo_produits_ids[1],
                "quantite": 200,
                "unite": "g"
            })
        
        try:
            response = requests.post(f"{BASE_URL}/recettes", json=recette_data, headers=HEADERS)
            if response.status_code == 200:
                created_recette = response.json()
                self.created_recette_id = created_recette["id"]
                
                # Vérifier l'enrichissement des noms de produits
                if created_recette.get("ingredients") and len(created_recette["ingredients"]) > 0:
                    first_ingredient = created_recette["ingredients"][0]
                    if first_ingredient.get("produit_nom"):
                        self.log_result("POST /recettes", True, "Recette créée avec enrichissement noms produits")
                    else:
                        self.log_result("POST /recettes", True, "Recette créée (sans enrichissement noms)")
                else:
                    self.log_result("POST /recettes", True, "Recette créée sans ingrédients")
            else:
                self.log_result("POST /recettes", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /recettes", False, "Exception lors de la création", str(e))
            return
        
        # Test GET - Liste recettes
        try:
            response = requests.get(f"{BASE_URL}/recettes")
            if response.status_code == 200:
                recettes = response.json()
                if isinstance(recettes, list) and len(recettes) > 0:
                    self.log_result("GET /recettes", True, f"{len(recettes)} recette(s) récupérée(s)")
                    
                    # Vérifier la structure des données
                    if len(recettes) > 0:
                        recette = recettes[0]
                        required_fields = ["nom", "portions", "ingredients"]
                        if all(field in recette for field in required_fields):
                            self.log_result("Structure données recettes", True, "Tous les champs requis présents")
                        else:
                            self.log_result("Structure données recettes", False, "Champs manquants")
                else:
                    self.log_result("GET /recettes", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET /recettes", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /recettes", False, "Exception", str(e))
        
        # Test GET by ID - Recette spécifique
        if self.created_recette_id:
            try:
                response = requests.get(f"{BASE_URL}/recettes/{self.created_recette_id}")
                if response.status_code == 200:
                    recette = response.json()
                    if recette["nom"] == recette_data["nom"]:
                        self.log_result("GET /recettes/{id}", True, "Recette récupérée correctement")
                    else:
                        self.log_result("GET /recettes/{id}", False, "Données incorrectes")
                else:
                    self.log_result("GET /recettes/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /recettes/{id}", False, "Exception", str(e))
        
        # Test PUT - Modification recette
        if self.created_recette_id:
            updated_data = {
                "nom": "Pasta Primavera Modifiée",
                "prix_vente": 18.00,
                "portions": 6,
                "ingredients": recette_data["ingredients"]  # Garder les mêmes ingrédients
            }
            
            try:
                response = requests.put(f"{BASE_URL}/recettes/{self.created_recette_id}", 
                                      json=updated_data, headers=HEADERS)
                if response.status_code == 200:
                    updated_recette = response.json()
                    if (updated_recette["nom"] == updated_data["nom"] and 
                        updated_recette["prix_vente"] == updated_data["prix_vente"]):
                        self.log_result("PUT /recettes/{id}", True, "Recette modifiée avec succès")
                    else:
                        self.log_result("PUT /recettes/{id}", False, "Modification non appliquée")
                else:
                    self.log_result("PUT /recettes/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("PUT /recettes/{id}", False, "Exception lors de la modification", str(e))

    def test_production_capacity_calculator(self):
        """Test calculateur de capacité de production"""
        print("\n=== TEST CALCULATEUR PRODUCTION CAPACITY ===")
        
        if not self.created_recette_id:
            self.log_result("Production capacity", False, "Pas de recette créée pour le test")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/recettes/{self.created_recette_id}/production-capacity")
            if response.status_code == 200:
                capacity_data = response.json()
                required_fields = ["recette_nom", "portions_max", "ingredients_status"]
                
                if all(field in capacity_data for field in required_fields):
                    self.log_result("GET /recettes/{id}/production-capacity", True, 
                                  f"Capacité calculée: {capacity_data['portions_max']} portions max")
                    
                    # Vérifier la structure des ingrédients
                    if isinstance(capacity_data["ingredients_status"], list):
                        if len(capacity_data["ingredients_status"]) > 0:
                            ingredient = capacity_data["ingredients_status"][0]
                            ingredient_fields = ["produit_nom", "quantite_disponible", "quantite_requise_par_portion", "portions_possibles"]
                            if all(field in ingredient for field in ingredient_fields):
                                self.log_result("Structure ingredients_status", True, "Détails ingrédients complets")
                            else:
                                self.log_result("Structure ingredients_status", False, "Champs manquants dans ingrédients")
                        else:
                            self.log_result("Ingredients status", True, "Aucun ingrédient (recette vide)")
                    else:
                        self.log_result("Structure ingredients_status", False, "Format incorrect pour ingredients_status")
                else:
                    missing = [f for f in required_fields if f not in capacity_data]
                    self.log_result("GET /recettes/{id}/production-capacity", False, f"Champs manquants: {missing}")
            else:
                self.log_result("GET /recettes/{id}/production-capacity", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /recettes/{id}/production-capacity", False, "Exception", str(e))

    def test_recettes_excel_export(self):
        """Test export Excel des recettes"""
        print("\n=== TEST EXPORT EXCEL RECETTES ===")
        
        try:
            response = requests.get(f"{BASE_URL}/export/recettes")
            if response.status_code == 200:
                # Vérifier le type de contenu
                content_type = response.headers.get('content-type', '')
                if 'spreadsheet' in content_type or 'excel' in content_type:
                    self.log_result("GET /export/recettes", True, "Fichier Excel recettes généré")
                    
                    # Vérifier la taille du fichier
                    content_length = len(response.content)
                    if content_length > 1000:
                        self.log_result("Taille fichier Excel recettes", True, f"Fichier de {content_length} bytes")
                        
                        # Essayer de lire le contenu Excel
                        try:
                            df = pd.read_excel(io.BytesIO(response.content))
                            if len(df) > 0:
                                required_columns = ["Nom Recette", "Portions", "Produit ID", "Quantité", "Unité"]
                                if all(col in df.columns for col in required_columns):
                                    self.log_result("Structure Excel recettes", True, f"Excel valide avec {len(df)} lignes")
                                else:
                                    self.log_result("Structure Excel recettes", False, f"Colonnes manquantes. Colonnes: {list(df.columns)}")
                            else:
                                self.log_result("Contenu Excel recettes", False, "Fichier Excel vide")
                        except Exception as e:
                            self.log_result("Lecture Excel recettes", False, f"Impossible de lire: {str(e)}")
                    else:
                        self.log_result("Taille fichier Excel recettes", False, f"Fichier trop petit: {content_length} bytes")
                else:
                    self.log_result("GET /export/recettes", False, f"Type de contenu incorrect: {content_type}")
            else:
                self.log_result("GET /export/recettes", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /export/recettes", False, "Exception", str(e))

    def test_recettes_excel_import(self):
        """Test import Excel des recettes"""
        print("\n=== TEST IMPORT EXCEL RECETTES ===")
        
        if not self.demo_produits_ids:
            self.log_result("Import Excel recettes", False, "Pas de produits pour tester l'import")
            return
        
        # Créer un fichier Excel de test pour les recettes
        test_data = {
            "Nom Recette": ["Salade Test Import", "Salade Test Import"],
            "Description": ["Salade fraîche importée", "Salade fraîche importée"],
            "Catégorie": ["entrée", "entrée"],
            "Portions": [2, 2],
            "Temps Préparation": [15, 15],
            "Prix Vente": [12.50, 12.50],
            "Produit ID": [self.demo_produits_ids[0], self.demo_produits_ids[1] if len(self.demo_produits_ids) > 1 else self.demo_produits_ids[0]],
            "Quantité": [200, 100],
            "Unité": ["g", "g"]
        }
        
        df = pd.DataFrame(test_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Recettes', index=False)
        excel_buffer.seek(0)
        
        try:
            files = {'file': ('test_import_recettes.xlsx', excel_buffer.getvalue(), 
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = requests.post(f"{BASE_URL}/import/recettes", files=files)
            if response.status_code == 200:
                result = response.json()
                if "importées avec succès" in result.get("message", ""):
                    self.log_result("POST /import/recettes", True, "Import Excel recettes réussi")
                    
                    # Vérifier que la recette a été créée
                    time.sleep(0.5)
                    recettes_response = requests.get(f"{BASE_URL}/recettes")
                    if recettes_response.status_code == 200:
                        recettes = recettes_response.json()
                        imported_recette = next((r for r in recettes if r["nom"] == "Salade Test Import"), None)
                        if imported_recette:
                            if (imported_recette["portions"] == 2 and 
                                imported_recette["prix_vente"] == 12.50 and
                                len(imported_recette.get("ingredients", [])) >= 1):
                                self.log_result("Validation import recettes", True, "Recette importée correctement")
                            else:
                                self.log_result("Validation import recettes", False, "Données recette incorrectes")
                        else:
                            self.log_result("Validation import recettes", False, "Recette importée non trouvée")
                else:
                    self.log_result("POST /import/recettes", False, f"Message d'erreur: {result.get('message')}")
            else:
                self.log_result("POST /import/recettes", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /import/recettes", False, "Exception", str(e))

    def test_recette_delete(self):
        """Test suppression de recette"""
        print("\n=== TEST SUPPRESSION RECETTE ===")
        
        if not self.created_recette_id:
            self.log_result("DELETE recette", False, "Pas de recette à supprimer")
            return
        
        try:
            response = requests.delete(f"{BASE_URL}/recettes/{self.created_recette_id}")
            if response.status_code == 200:
                self.log_result("DELETE /recettes/{id}", True, "Recette supprimée")
                
                # Vérifier que la recette n'existe plus
                get_response = requests.get(f"{BASE_URL}/recettes/{self.created_recette_id}")
                if get_response.status_code == 404:
                    self.log_result("Validation suppression recette", True, "Recette bien supprimée")
                else:
                    self.log_result("Validation suppression recette", False, "Recette encore présente")
            else:
                self.log_result("DELETE /recettes/{id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("DELETE /recettes/{id}", False, "Exception", str(e))

    def test_cascade_delete(self):
        """Test suppression en cascade"""
        print("\n=== TEST SUPPRESSION EN CASCADE ===")
        
        if not self.created_produit_id:
            self.log_result("Suppression cascade", False, "Pas de produit à supprimer")
            return
        
        # Vérifier qu'il y a des mouvements avant suppression
        try:
            mouvements_response = requests.get(f"{BASE_URL}/mouvements")
            initial_mouvements_count = len(mouvements_response.json()) if mouvements_response.status_code == 200 else 0
            
            # Supprimer le produit
            response = requests.delete(f"{BASE_URL}/produits/{self.created_produit_id}")
            if response.status_code == 200:
                self.log_result("DELETE /produits/{id}", True, "Produit supprimé")
                
                # Vérifier que le stock a été supprimé
                stock_response = requests.get(f"{BASE_URL}/stocks/{self.created_produit_id}")
                if stock_response.status_code == 404:
                    self.log_result("Suppression stock cascade", True, "Stock supprimé automatiquement")
                else:
                    self.log_result("Suppression stock cascade", False, "Stock non supprimé")
                
                # Vérifier que les mouvements ont été supprimés
                time.sleep(0.5)
                mouvements_response = requests.get(f"{BASE_URL}/mouvements")
                if mouvements_response.status_code == 200:
                    final_mouvements = mouvements_response.json()
                    # Filtrer les mouvements du produit supprimé
                    remaining_mouvements = [m for m in final_mouvements if m["produit_id"] != self.created_produit_id]
                    if len(remaining_mouvements) < initial_mouvements_count:
                        self.log_result("Suppression mouvements cascade", True, "Mouvements supprimés automatiquement")
                    else:
                        self.log_result("Suppression mouvements cascade", False, "Mouvements non supprimés")
            else:
                self.log_result("DELETE /produits/{id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Suppression cascade", False, "Exception", str(e))
        
        # Nettoyer le fournisseur de test
        if self.created_fournisseur_id:
            try:
                response = requests.delete(f"{BASE_URL}/fournisseurs/{self.created_fournisseur_id}")
                if response.status_code == 200:
                    self.log_result("Nettoyage fournisseur", True, "Fournisseur de test supprimé")
                else:
                    self.log_result("Nettoyage fournisseur", False, f"Erreur {response.status_code}")
            except Exception as e:
                self.log_result("Nettoyage fournisseur", False, "Exception", str(e))
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 DÉBUT DES TESTS BACKEND - GESTION STOCKS RESTAURANT")
        print(f"URL de base: {BASE_URL}")
        print("=" * 60)
        
        # Tests dans l'ordre logique
        self.test_fournisseurs_crud()
        self.test_produits_crud()
        self.test_stocks_api()
        self.test_mouvements_stock()
        self.test_export_excel()
        self.test_import_excel()
        self.test_dashboard_stats()
        
        # Tests des nouvelles APIs de recettes
        self.test_demo_data_initialization()
        self.test_recettes_crud()
        self.test_production_capacity_calculator()
        self.test_recettes_excel_export()
        self.test_recettes_excel_import()
        self.test_recette_delete()
        
        # Test de suppression en cascade à la fin
        self.test_cascade_delete()
        
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
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
                    if result["details"]:
                        print(f"      Détails: {result['details']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": self.test_results
        }

if __name__ == "__main__":
    test_suite = StockTestSuite()
    results = test_suite.run_all_tests()
    
    # Sauvegarder les résultats
    with open("/app/test_results_backend.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats sauvegardés dans /app/test_results_backend.json")
    
    # Code de sortie basé sur les résultats
    exit(0 if results["failed"] == 0 else 1)