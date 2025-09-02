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
import base64
from PIL import Image, ImageDraw, ImageFont

# Configuration
BASE_URL = "https://resto-inventory-10.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class StockTestSuite:
    def __init__(self):
        self.test_results = []
        self.created_fournisseur_id = None
        self.created_produit_id = None
        self.created_recette_id = None
        self.demo_produits_ids = []
        self.created_document_id = None
        self.created_rapport_id = None
        
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

    def test_table_augustine_demo_data(self):
        """Test spécifique pour les données de démonstration La Table d'Augustine"""
        print("\n=== TEST DONNÉES DÉMONSTRATION LA TABLE D'AUGUSTINE ===")
        
        try:
            response = requests.post(f"{BASE_URL}/demo/init-table-augustine-data", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                if "La Table d'Augustine" in result.get("message", "") and "succès" in result.get("message", ""):
                    self.log_result("POST /demo/init-table-augustine-data", True, 
                                  f"Données créées: {result.get('fournisseurs_crees', 0)} fournisseurs, "
                                  f"{result.get('produits_crees', 0)} produits, {result.get('recettes_creees', 0)} recettes")
                    
                    # Vérifier les fournisseurs authentiques de La Table d'Augustine
                    fournisseurs_response = requests.get(f"{BASE_URL}/fournisseurs")
                    if fournisseurs_response.status_code == 200:
                        fournisseurs = fournisseurs_response.json()
                        expected_suppliers = [
                            "Maison Artigiana", "Pêcherie des Sanguinaires", "Boucherie Limousine du Sud",
                            "Trufficulteurs de Forcalquier", "Maraîchers de Provence", "Fromagerie des Alpilles"
                        ]
                        found_suppliers = [f for f in fournisseurs if f["nom"] in expected_suppliers]
                        
                        if len(found_suppliers) >= 6:
                            self.log_result("Fournisseurs authentiques La Table d'Augustine", True, 
                                          f"{len(found_suppliers)} fournisseurs authentiques créés")
                            
                            # Vérifier les détails d'un fournisseur spécifique
                            artigiana = next((f for f in found_suppliers if f["nom"] == "Maison Artigiana"), None)
                            if artigiana and "Giuseppe Pellegrino" in artigiana.get("contact", ""):
                                self.log_result("Détails fournisseur Artigiana", True, "Contact Giuseppe Pellegrino validé")
                            else:
                                self.log_result("Détails fournisseur Artigiana", False, "Contact incorrect ou manquant")
                        else:
                            self.log_result("Fournisseurs authentiques La Table d'Augustine", False, 
                                          f"Seulement {len(found_suppliers)} fournisseurs trouvés sur 6 attendus")
                    
                    # Vérifier les produits du menu authentique
                    produits_response = requests.get(f"{BASE_URL}/produits")
                    if produits_response.status_code == 200:
                        produits = produits_response.json()
                        expected_products = [
                            "Supions (petits calamars)", "Burrata des Pouilles Artigiana", "Palourdes",
                            "Daurade royale de Corse", "Bœuf Limousin (filet)", "Souris d'agneau",
                            "Jarret de veau", "Fleurs de courgettes", "Tomates anciennes",
                            "Truffe d'été Aestivum", "Linguine artisanales", "Rigatoni",
                            "Huile verte aux herbes", "Farine de pois-chiche"
                        ]
                        found_products = [p for p in produits if p["nom"] in expected_products]
                        
                        if len(found_products) >= 10:
                            self.log_result("Produits menu authentique", True, 
                                          f"{len(found_products)} produits du menu créés")
                            
                            # Vérifier les prix réalistes
                            truffe = next((p for p in found_products if "Truffe" in p["nom"]), None)
                            if truffe and truffe.get("prix_achat", 0) >= 500:
                                self.log_result("Prix produits luxe", True, f"Truffe à {truffe['prix_achat']}€/kg")
                            else:
                                self.log_result("Prix produits luxe", False, "Prix truffe incorrect")
                        else:
                            self.log_result("Produits menu authentique", False, 
                                          f"Seulement {len(found_products)} produits trouvés")
                    
                    # Vérifier les recettes authentiques avec prix corrects
                    recettes_response = requests.get(f"{BASE_URL}/recettes")
                    if recettes_response.status_code == 200:
                        recettes = recettes_response.json()
                        expected_recipes = [
                            ("Supions en persillade de Mamie", 24.00),
                            ("Fleurs de courgettes de Mamet", 21.00),
                            ("Linguine aux palourdes & sauce à l'ail", 28.00),
                            ("Rigatoni à la truffe fraîche de Forcalquier", 31.00),
                            ("Souris d'agneau confite", 36.00),
                            ("Bœuf Wellington à la truffe", 56.00)
                        ]
                        
                        found_recipes = []
                        for recipe_name, expected_price in expected_recipes:
                            recipe = next((r for r in recettes if r["nom"] == recipe_name), None)
                            if recipe:
                                found_recipes.append(recipe)
                                # Vérifier le prix
                                if abs(recipe.get("prix_vente", 0) - expected_price) < 0.01:
                                    self.log_result(f"Prix recette {recipe_name}", True, f"{expected_price}€")
                                else:
                                    self.log_result(f"Prix recette {recipe_name}", False, 
                                                  f"Prix incorrect: {recipe.get('prix_vente')}€ au lieu de {expected_price}€")
                        
                        if len(found_recipes) >= 6:
                            self.log_result("Recettes authentiques La Table d'Augustine", True, 
                                          f"{len(found_recipes)} recettes du menu créées")
                        else:
                            self.log_result("Recettes authentiques La Table d'Augustine", False, 
                                          f"Seulement {len(found_recipes)} recettes trouvées sur 6 attendues")
                    
                    # Test de calcul de capacité de production pour une recette
                    if found_recipes:
                        test_recipe = found_recipes[0]
                        capacity_response = requests.get(f"{BASE_URL}/recettes/{test_recipe['id']}/production-capacity")
                        if capacity_response.status_code == 200:
                            capacity_data = capacity_response.json()
                            if "portions_max" in capacity_data and "ingredients_status" in capacity_data:
                                self.log_result("Calcul production capacity La Table d'Augustine", True, 
                                              f"Capacité calculée pour {test_recipe['nom']}: {capacity_data['portions_max']} portions")
                            else:
                                self.log_result("Calcul production capacity La Table d'Augustine", False, 
                                              "Structure de réponse incorrecte")
                        else:
                            self.log_result("Calcul production capacity La Table d'Augustine", False, 
                                          f"Erreur {capacity_response.status_code}")
                    
                    # Vérifier les relations ingrédients-produits
                    if found_recipes:
                        recipe_with_ingredients = next((r for r in found_recipes if len(r.get("ingredients", [])) > 0), None)
                        if recipe_with_ingredients:
                            ingredients = recipe_with_ingredients["ingredients"]
                            valid_ingredients = [ing for ing in ingredients if ing.get("produit_nom") and ing.get("quantite", 0) > 0]
                            if len(valid_ingredients) == len(ingredients):
                                self.log_result("Relations ingrédients-produits", True, 
                                              f"Tous les ingrédients correctement liés pour {recipe_with_ingredients['nom']}")
                            else:
                                self.log_result("Relations ingrédients-produits", False, 
                                              f"Ingrédients mal liés: {len(valid_ingredients)}/{len(ingredients)}")
                        else:
                            self.log_result("Relations ingrédients-produits", False, "Aucune recette avec ingrédients trouvée")
                    
                else:
                    self.log_result("POST /demo/init-table-augustine-data", False, f"Message inattendu: {result.get('message')}")
            else:
                self.log_result("POST /demo/init-table-augustine-data", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /demo/init-table-augustine-data", False, "Exception", str(e))

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
    
    def create_mock_base64_image(self, text_content):
        """Créer une image base64 simulée avec du texte pour les tests OCR"""
        # Créer une image PNG simple de 100x100 pixels avec du texte
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Créer une image blanche
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Ajouter le texte (utiliser une police par défaut)
        try:
            # Essayer d'utiliser une police par défaut
            font = ImageFont.load_default()
        except:
            font = None
        
        # Diviser le texte en lignes et les dessiner
        lines = text_content.strip().split('\n')
        y_offset = 10
        for line in lines:
            if line.strip():
                draw.text((10, y_offset), line.strip(), fill='black', font=font)
                y_offset += 20
        
        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def test_ocr_document_upload_z_report(self):
        """Test upload et traitement OCR d'un rapport Z"""
        print("\n=== TEST OCR UPLOAD Z-REPORT ===")
        
        # Créer des données simulées de Z-report
        z_report_text = """
        RAPPORT Z - 15/12/2024
        
        Linguine aux palourdes: 3
        Supions en persillade: 2  
        Bœuf Wellington: 1
        Salade Caprese: 4
        
        Total: 84.00€
        Couverts: 10
        """
        
        mock_image_base64 = self.create_mock_base64_image(z_report_text)
        
        try:
            # Simuler un upload de fichier avec des données base64
            files = {
                'file': ('z_report_test.jpg', base64.b64decode(mock_image_base64), 'image/jpeg')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                if "document_id" in result and "texte_extrait" in result:
                    self.created_document_id = result["document_id"]
                    self.log_result("POST /ocr/upload-document (z_report)", True, 
                                  f"Document Z-report traité, ID: {result['document_id'][:8]}...")
                    
                    # Vérifier la structure des données parsées
                    if "donnees_parsees" in result and isinstance(result["donnees_parsees"], dict):
                        parsed_data = result["donnees_parsees"]
                        if "plats_vendus" in parsed_data:
                            self.log_result("Parsing Z-report", True, 
                                          f"Données parsées avec {len(parsed_data.get('plats_vendus', []))} plats")
                        else:
                            self.log_result("Parsing Z-report", False, "Structure de données parsées incorrecte")
                    else:
                        self.log_result("Parsing Z-report", False, "Données parsées manquantes")
                else:
                    self.log_result("POST /ocr/upload-document (z_report)", False, "Réponse incomplète")
            else:
                self.log_result("POST /ocr/upload-document (z_report)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /ocr/upload-document (z_report)", False, "Exception", str(e))
    
    def test_ocr_document_upload_facture(self):
        """Test upload et traitement OCR d'une facture fournisseur"""
        print("\n=== TEST OCR UPLOAD FACTURE FOURNISSEUR ===")
        
        # Créer des données simulées de facture
        facture_text = """
        Maison Artigiana
        Facture N° FAC-2024-001
        Date: 15/12/2024
        
        Burrata 2x 8.50€ = 17.00€
        Mozzarella 1x 12.00€ = 12.00€
        Parmesan 500g x 45.00€ = 22.50€
        
        Total HT: 51.50€
        Total TTC: 56.65€
        """
        
        mock_image_base64 = self.create_mock_base64_image(facture_text)
        
        try:
            files = {
                'file': ('facture_test.jpg', base64.b64decode(mock_image_base64), 'image/jpeg')
            }
            data = {'document_type': 'facture_fournisseur'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                if "document_id" in result and "texte_extrait" in result:
                    self.log_result("POST /ocr/upload-document (facture)", True, 
                                  f"Facture traitée, ID: {result['document_id'][:8]}...")
                    
                    # Vérifier la structure des données parsées
                    if "donnees_parsees" in result and isinstance(result["donnees_parsees"], dict):
                        parsed_data = result["donnees_parsees"]
                        if "produits" in parsed_data and "fournisseur" in parsed_data:
                            self.log_result("Parsing facture", True, 
                                          f"Facture parsée: {parsed_data.get('fournisseur', 'N/A')} avec {len(parsed_data.get('produits', []))} produits")
                        else:
                            self.log_result("Parsing facture", False, "Structure de données parsées incorrecte")
                    else:
                        self.log_result("Parsing facture", False, "Données parsées manquantes")
                else:
                    self.log_result("POST /ocr/upload-document (facture)", False, "Réponse incomplète")
            else:
                self.log_result("POST /ocr/upload-document (facture)", False, 
                              f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /ocr/upload-document (facture)", False, "Exception", str(e))
    
    def test_ocr_documents_list(self):
        """Test récupération de la liste des documents OCR"""
        print("\n=== TEST OCR DOCUMENTS LIST ===")
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/documents")
            if response.status_code == 200:
                documents = response.json()
                if isinstance(documents, list):
                    self.log_result("GET /ocr/documents", True, f"{len(documents)} document(s) récupéré(s)")
                    
                    # Vérifier la structure des documents
                    if len(documents) > 0:
                        doc = documents[0]
                        required_fields = ["id", "type_document", "nom_fichier", "statut", "date_upload"]
                        if all(field in doc for field in required_fields):
                            self.log_result("Structure documents OCR", True, "Tous les champs requis présents")
                        else:
                            missing = [f for f in required_fields if f not in doc]
                            self.log_result("Structure documents OCR", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("GET /ocr/documents", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /ocr/documents", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /ocr/documents", False, "Exception", str(e))
    
    def test_ocr_document_by_id(self):
        """Test récupération d'un document OCR spécifique"""
        print("\n=== TEST OCR DOCUMENT BY ID ===")
        
        if not self.created_document_id:
            self.log_result("GET /ocr/document/{id}", False, "Pas de document créé pour le test")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/ocr/document/{self.created_document_id}")
            if response.status_code == 200:
                document = response.json()
                if "id" in document and document["id"] == self.created_document_id:
                    self.log_result("GET /ocr/document/{id}", True, "Document récupéré correctement")
                    
                    # Vérifier que les données complètes sont présentes
                    if "texte_extrait" in document and "donnees_parsees" in document:
                        self.log_result("Données complètes document", True, "Texte et données parsées présents")
                    else:
                        self.log_result("Données complètes document", False, "Données manquantes")
                else:
                    self.log_result("GET /ocr/document/{id}", False, "Document incorrect")
            else:
                self.log_result("GET /ocr/document/{id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /ocr/document/{id}", False, "Exception", str(e))
    
    def test_ocr_z_report_stock_processing(self):
        """Test traitement automatique des stocks depuis un Z-report"""
        print("\n=== TEST OCR Z-REPORT STOCK PROCESSING ===")
        
        if not self.created_document_id:
            self.log_result("POST /ocr/process-z-report", False, "Pas de document Z-report pour le test")
            return
        
        # S'assurer qu'on a des recettes correspondantes aux plats du Z-report
        # (Les données de démo La Table d'Augustine devraient contenir "Linguine aux palourdes")
        
        try:
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{self.created_document_id}")
            if response.status_code == 200:
                result = response.json()
                if "stock_updates" in result:
                    stock_updates = result["stock_updates"]
                    self.log_result("POST /ocr/process-z-report", True, 
                                  f"Traitement réussi: {len(stock_updates)} mise(s) à jour de stock")
                    
                    # Vérifier la structure des mises à jour
                    if len(stock_updates) > 0:
                        update = stock_updates[0]
                        required_fields = ["produit_nom", "quantite_deduite", "nouvelle_quantite", "plat"]
                        if all(field in update for field in required_fields):
                            self.log_result("Structure stock updates", True, "Détails complets des mises à jour")
                        else:
                            self.log_result("Structure stock updates", False, "Champs manquants dans les mises à jour")
                    
                    # Vérifier les avertissements
                    if "warnings" in result:
                        warnings = result["warnings"]
                        if len(warnings) > 0:
                            self.log_result("Warnings Z-report", True, f"{len(warnings)} avertissement(s) signalé(s)")
                        else:
                            self.log_result("Warnings Z-report", True, "Aucun avertissement")
                else:
                    self.log_result("POST /ocr/process-z-report", False, "Structure de réponse incorrecte")
            else:
                self.log_result("POST /ocr/process-z-report", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /ocr/process-z-report", False, "Exception", str(e))
    
    def test_ocr_document_delete(self):
        """Test suppression d'un document OCR"""
        print("\n=== TEST OCR DOCUMENT DELETE ===")
        
        if not self.created_document_id:
            self.log_result("DELETE /ocr/document/{id}", False, "Pas de document à supprimer")
            return
        
        try:
            response = requests.delete(f"{BASE_URL}/ocr/document/{self.created_document_id}")
            if response.status_code == 200:
                self.log_result("DELETE /ocr/document/{id}", True, "Document OCR supprimé")
                
                # Vérifier que le document n'existe plus
                get_response = requests.get(f"{BASE_URL}/ocr/document/{self.created_document_id}")
                if get_response.status_code == 404:
                    self.log_result("Validation suppression document OCR", True, "Document bien supprimé")
                else:
                    self.log_result("Validation suppression document OCR", False, "Document encore présent")
            else:
                self.log_result("DELETE /ocr/document/{id}", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("DELETE /ocr/document/{id}", False, "Exception", str(e))
    
    def test_ocr_error_handling(self):
        """Test gestion d'erreurs OCR"""
        print("\n=== TEST OCR ERROR HANDLING ===")
        
        # Test avec type de document invalide
        try:
            files = {
                'file': ('test.jpg', b'fake image data', 'image/jpeg')
            }
            data = {'document_type': 'invalid_type'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code == 400:
                self.log_result("OCR type document invalide", True, "Erreur 400 pour type invalide")
            else:
                self.log_result("OCR type document invalide", False, f"Code erreur inattendu: {response.status_code}")
        except Exception as e:
            self.log_result("OCR type document invalide", False, "Exception", str(e))
        
        # Test avec document inexistant
        try:
            fake_id = "fake-document-id-123"
            response = requests.get(f"{BASE_URL}/ocr/document/{fake_id}")
            if response.status_code == 404:
                self.log_result("OCR document inexistant", True, "Erreur 404 pour document inexistant")
            else:
                self.log_result("OCR document inexistant", False, f"Code erreur inattendu: {response.status_code}")
        except Exception as e:
            self.log_result("OCR document inexistant", False, "Exception", str(e))
        
        # Test traitement Z-report avec document inexistant
        try:
            fake_id = "fake-document-id-456"
            response = requests.post(f"{BASE_URL}/ocr/process-z-report/{fake_id}")
            if response.status_code == 404:
                self.log_result("OCR traitement document inexistant", True, "Erreur 404 pour traitement document inexistant")
            else:
                self.log_result("OCR traitement document inexistant", False, f"Code erreur inattendu: {response.status_code}")
        except Exception as e:
            self.log_result("OCR traitement document inexistant", False, "Exception", str(e))
    
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
    
    def test_rapports_z_crud(self):
        """Test complet CRUD des rapports Z - Nouveaux endpoints"""
        print("\n=== TEST API RAPPORTS Z - NOUVEAUX ENDPOINTS ===")
        
        created_rapport_id = None
        
        # Test POST - Création rapport Z
        rapport_data = {
            "date": "2025-01-06T10:00:00",
            "ca_total": 1850.50,
            "produits": [
                {"nom": "Supions Persillade", "quantite": 8, "prix": 24.00},
                {"nom": "Bœuf Wellington", "quantite": 3, "prix": 56.00},
                {"nom": "Linguine aux palourdes", "quantite": 5, "prix": 28.00},
                {"nom": "Salade Caprese", "quantite": 4, "prix": 18.00}
            ]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/rapports_z", json=rapport_data, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                if "id" in result and result.get("status") == "ok":
                    created_rapport_id = result["id"]
                    self.log_result("POST /rapports_z", True, f"Rapport Z créé avec ID: {created_rapport_id[:8]}...")
                    
                    # Vérifier que l'ID est un UUID valide
                    if len(created_rapport_id) == 36 and created_rapport_id.count('-') == 4:
                        self.log_result("UUID génération automatique", True, "ID UUID généré automatiquement")
                    else:
                        self.log_result("UUID génération automatique", False, f"ID invalide: {created_rapport_id}")
                else:
                    self.log_result("POST /rapports_z", False, "Réponse incorrecte", str(result))
            else:
                self.log_result("POST /rapports_z", False, f"Erreur {response.status_code}", response.text)
                return
        except Exception as e:
            self.log_result("POST /rapports_z", False, "Exception lors de la création", str(e))
            return
        
        # Test GET - Liste tous les rapports Z
        try:
            response = requests.get(f"{BASE_URL}/rapports_z")
            if response.status_code == 200:
                rapports = response.json()
                if isinstance(rapports, list) and len(rapports) > 0:
                    self.log_result("GET /rapports_z", True, f"{len(rapports)} rapport(s) Z récupéré(s)")
                    
                    # Vérifier l'ordre (tri par date décroissante)
                    if len(rapports) >= 2:
                        first_date = rapports[0].get("date", "")
                        second_date = rapports[1].get("date", "")
                        if first_date >= second_date:
                            self.log_result("Tri par date décroissante", True, "Rapports triés correctement")
                        else:
                            self.log_result("Tri par date décroissante", False, f"Ordre incorrect: {first_date} vs {second_date}")
                    
                    # Vérifier la structure des données
                    if len(rapports) > 0:
                        rapport = rapports[0]
                        required_fields = ["id", "date", "ca_total", "produits", "created_at"]
                        if all(field in rapport for field in required_fields):
                            self.log_result("Structure données rapports Z", True, "Tous les champs requis présents")
                            
                            # Vérifier que created_at est ajouté automatiquement
                            if rapport.get("created_at"):
                                self.log_result("created_at automatique", True, "Timestamp created_at ajouté")
                            else:
                                self.log_result("created_at automatique", False, "created_at manquant")
                        else:
                            missing = [f for f in required_fields if f not in rapport]
                            self.log_result("Structure données rapports Z", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("GET /rapports_z", False, "Liste vide ou format incorrect")
            else:
                self.log_result("GET /rapports_z", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /rapports_z", False, "Exception", str(e))
        
        # Test GET by ID - Rapport spécifique
        if created_rapport_id:
            try:
                response = requests.get(f"{BASE_URL}/rapports_z/{created_rapport_id}")
                if response.status_code == 200:
                    rapport = response.json()
                    if (rapport.get("ca_total") == rapport_data["ca_total"] and 
                        len(rapport.get("produits", [])) == len(rapport_data["produits"])):
                        self.log_result("GET /rapports_z/{id}", True, "Rapport spécifique récupéré correctement")
                        
                        # Vérifier les données des produits
                        produits = rapport.get("produits", [])
                        if len(produits) > 0:
                            first_produit = produits[0]
                            if ("nom" in first_produit and "quantite" in first_produit and "prix" in first_produit):
                                self.log_result("Structure produits rapport Z", True, "Structure produits correcte")
                            else:
                                self.log_result("Structure produits rapport Z", False, "Structure produits incorrecte")
                    else:
                        self.log_result("GET /rapports_z/{id}", False, "Données incorrectes")
                else:
                    self.log_result("GET /rapports_z/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GET /rapports_z/{id}", False, "Exception", str(e))
        
        # Test GET by ID - ID inexistant (doit retourner 404)
        try:
            fake_id = "00000000-0000-0000-0000-000000000000"
            response = requests.get(f"{BASE_URL}/rapports_z/{fake_id}")
            if response.status_code == 404:
                self.log_result("GET /rapports_z/{id} inexistant", True, "Erreur 404 pour ID inexistant")
            else:
                self.log_result("GET /rapports_z/{id} inexistant", False, f"Code incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("GET /rapports_z/{id} inexistant", False, "Exception", str(e))
        
        # Test DELETE - Suppression rapport
        if created_rapport_id:
            try:
                response = requests.delete(f"{BASE_URL}/rapports_z/{created_rapport_id}")
                if response.status_code == 200:
                    result = response.json()
                    if "supprimé" in result.get("message", ""):
                        self.log_result("DELETE /rapports_z/{id}", True, "Rapport Z supprimé avec succès")
                        
                        # Vérifier que le rapport n'existe plus
                        get_response = requests.get(f"{BASE_URL}/rapports_z/{created_rapport_id}")
                        if get_response.status_code == 404:
                            self.log_result("Validation suppression rapport Z", True, "Rapport bien supprimé")
                        else:
                            self.log_result("Validation suppression rapport Z", False, "Rapport encore présent")
                    else:
                        self.log_result("DELETE /rapports_z/{id}", False, f"Message incorrect: {result}")
                else:
                    self.log_result("DELETE /rapports_z/{id}", False, f"Erreur {response.status_code}", response.text)
            except Exception as e:
                self.log_result("DELETE /rapports_z/{id}", False, "Exception", str(e))
        
        # Test DELETE - ID inexistant (doit retourner 404)
        try:
            fake_id = "00000000-0000-0000-0000-000000000000"
            response = requests.delete(f"{BASE_URL}/rapports_z/{fake_id}")
            if response.status_code == 404:
                self.log_result("DELETE /rapports_z/{id} inexistant", True, "Erreur 404 pour suppression ID inexistant")
            else:
                self.log_result("DELETE /rapports_z/{id} inexistant", False, f"Code incorrect: {response.status_code}")
        except Exception as e:
            self.log_result("DELETE /rapports_z/{id} inexistant", False, "Exception", str(e))
        
        # Test avec données réalistes supplémentaires
        rapport_data_2 = {
            "date": "2025-01-06T14:30:00",
            "ca_total": 2150.75,
            "produits": [
                {"nom": "Rigatoni à la truffe de Forcalquier", "quantite": 6, "prix": 31.00},
                {"nom": "Souris d'agneau confite", "quantite": 4, "prix": 36.00},
                {"nom": "Fleurs de courgettes de Mamet", "quantite": 7, "prix": 21.00}
            ]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/rapports_z", json=rapport_data_2, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                if "id" in result:
                    self.log_result("POST /rapports_z (données réalistes)", True, "Deuxième rapport Z créé avec données La Table d'Augustine")
                    
                    # Vérifier la liste mise à jour
                    list_response = requests.get(f"{BASE_URL}/rapports_z")
                    if list_response.status_code == 200:
                        rapports = list_response.json()
                        if len(rapports) >= 1:  # Au moins le nouveau rapport
                            self.log_result("Liste rapports Z mise à jour", True, f"Liste contient {len(rapports)} rapport(s)")
                        else:
                            self.log_result("Liste rapports Z mise à jour", False, "Liste non mise à jour")
                else:
                    self.log_result("POST /rapports_z (données réalistes)", False, "Réponse incorrecte")
            else:
                self.log_result("POST /rapports_z (données réalistes)", False, f"Erreur {response.status_code}")
        except Exception as e:
            self.log_result("POST /rapports_z (données réalistes)", False, "Exception", str(e))

    def test_analytics_profitability(self):
        """Test API Analytics - Profitability"""
        print("\n=== TEST ANALYTICS PROFITABILITY ===")
        
        try:
            response = requests.get(f"{BASE_URL}/analytics/profitability")
            if response.status_code == 200:
                profitability_data = response.json()
                if isinstance(profitability_data, list):
                    self.log_result("GET /analytics/profitability", True, 
                                  f"{len(profitability_data)} recettes analysées pour profitabilité")
                    
                    # Vérifier la structure des données
                    if len(profitability_data) > 0:
                        recipe_profit = profitability_data[0]
                        required_fields = ["recipe_id", "recipe_name", "ingredient_cost", "profit_margin", 
                                         "profit_percentage", "portions_sold", "total_revenue", "total_profit"]
                        
                        if all(field in recipe_profit for field in required_fields):
                            self.log_result("Structure profitability data", True, "Tous les champs requis présents")
                            
                            # Vérifier la cohérence des calculs
                            selling_price = recipe_profit.get("selling_price", 0)
                            ingredient_cost = recipe_profit.get("ingredient_cost", 0)
                            profit_margin = recipe_profit.get("profit_margin", 0)
                            
                            if selling_price > 0:
                                expected_margin = selling_price - ingredient_cost
                                if abs(profit_margin - expected_margin) < 0.01:
                                    self.log_result("Calcul profit margin", True, 
                                                  f"Marge calculée correctement: {profit_margin:.2f}€")
                                else:
                                    self.log_result("Calcul profit margin", False, 
                                                  f"Marge incorrecte: {profit_margin:.2f}€ vs {expected_margin:.2f}€")
                            
                            # Vérifier le tri par profit_percentage décroissant
                            if len(profitability_data) > 1:
                                first_profit = profitability_data[0]["profit_percentage"]
                                second_profit = profitability_data[1]["profit_percentage"]
                                if first_profit >= second_profit:
                                    self.log_result("Tri profitability", True, "Données triées par profit décroissant")
                                else:
                                    self.log_result("Tri profitability", False, "Tri incorrect")
                        else:
                            missing = [f for f in required_fields if f not in recipe_profit]
                            self.log_result("Structure profitability data", False, f"Champs manquants: {missing}")
                    else:
                        self.log_result("Données profitability", True, "Aucune recette pour analyse (normal si pas de données)")
                else:
                    self.log_result("GET /analytics/profitability", False, "Format de réponse incorrect")
            else:
                self.log_result("GET /analytics/profitability", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /analytics/profitability", False, "Exception", str(e))

    def test_analytics_sales_performance(self):
        """Test API Analytics - Sales Performance"""
        print("\n=== TEST ANALYTICS SALES PERFORMANCE ===")
        
        try:
            response = requests.get(f"{BASE_URL}/analytics/sales-performance?period=monthly")
            if response.status_code == 200:
                sales_data = response.json()
                required_fields = ["period", "total_sales", "total_orders", "average_order_value", 
                                 "top_recipes", "sales_by_category"]
                
                if all(field in sales_data for field in required_fields):
                    self.log_result("GET /analytics/sales-performance", True, 
                                  f"Analyse ventes: {sales_data['total_sales']:.2f}€ total, "
                                  f"{sales_data['total_orders']} commandes")
                    
                    # Vérifier la cohérence des calculs
                    total_sales = sales_data["total_sales"]
                    total_orders = sales_data["total_orders"]
                    avg_order_value = sales_data["average_order_value"]
                    
                    if total_orders > 0:
                        expected_avg = total_sales / total_orders
                        if abs(avg_order_value - expected_avg) < 0.01:
                            self.log_result("Calcul average order value", True, 
                                          f"Panier moyen: {avg_order_value:.2f}€")
                        else:
                            self.log_result("Calcul average order value", False, 
                                          f"Calcul incorrect: {avg_order_value:.2f}€ vs {expected_avg:.2f}€")
                    
                    # Vérifier la structure des top recipes
                    if isinstance(sales_data["top_recipes"], list):
                        if len(sales_data["top_recipes"]) > 0:
                            top_recipe = sales_data["top_recipes"][0]
                            if "name" in top_recipe and "quantity" in top_recipe and "revenue" in top_recipe:
                                self.log_result("Structure top recipes", True, 
                                              f"Top recette: {top_recipe['name']} ({top_recipe['revenue']:.2f}€)")
                            else:
                                self.log_result("Structure top recipes", False, "Champs manquants dans top recipes")
                        else:
                            self.log_result("Top recipes", True, "Aucune recette vendue (normal si pas de rapports Z)")
                    
                    # Vérifier les catégories de ventes
                    if isinstance(sales_data["sales_by_category"], dict):
                        categories = ["Bar", "Entrées", "Plats", "Desserts"]
                        if all(cat in sales_data["sales_by_category"] for cat in categories):
                            self.log_result("Sales by category", True, "Toutes les catégories présentes")
                        else:
                            self.log_result("Sales by category", False, "Catégories manquantes")
                else:
                    missing = [f for f in required_fields if f not in sales_data]
                    self.log_result("GET /analytics/sales-performance", False, f"Champs manquants: {missing}")
            else:
                self.log_result("GET /analytics/sales-performance", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /analytics/sales-performance", False, "Exception", str(e))

    def test_analytics_alerts(self):
        """Test API Analytics - Alert Center"""
        print("\n=== TEST ANALYTICS ALERTS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/analytics/alerts")
            if response.status_code == 200:
                alerts_data = response.json()
                required_fields = ["expiring_products", "price_anomalies", "low_stock_items", 
                                 "unused_stock", "total_alerts"]
                
                if all(field in alerts_data for field in required_fields):
                    self.log_result("GET /analytics/alerts", True, 
                                  f"Centre d'alertes: {alerts_data['total_alerts']} alertes totales")
                    
                    # Vérifier la cohérence du total
                    calculated_total = (len(alerts_data["expiring_products"]) + 
                                      len(alerts_data["price_anomalies"]) + 
                                      len(alerts_data["low_stock_items"]) + 
                                      len(alerts_data["unused_stock"]))
                    
                    if alerts_data["total_alerts"] == calculated_total:
                        self.log_result("Calcul total alerts", True, f"Total cohérent: {calculated_total}")
                    else:
                        self.log_result("Calcul total alerts", False, 
                                      f"Total incorrect: {alerts_data['total_alerts']} vs {calculated_total}")
                    
                    # Vérifier la structure des produits expirants
                    if isinstance(alerts_data["expiring_products"], list):
                        if len(alerts_data["expiring_products"]) > 0:
                            expiring = alerts_data["expiring_products"][0]
                            expiring_fields = ["product_name", "batch_id", "quantity", "expiry_date", 
                                             "days_to_expiry", "urgency"]
                            if all(field in expiring for field in expiring_fields):
                                self.log_result("Structure expiring products", True, 
                                              f"Produit expirant: {expiring['product_name']} "
                                              f"({expiring['days_to_expiry']} jours)")
                            else:
                                self.log_result("Structure expiring products", False, "Champs manquants")
                        else:
                            self.log_result("Expiring products", True, "Aucun produit expirant (bon signe)")
                    
                    # Vérifier les stocks faibles
                    if isinstance(alerts_data["low_stock_items"], list):
                        if len(alerts_data["low_stock_items"]) > 0:
                            low_stock = alerts_data["low_stock_items"][0]
                            low_stock_fields = ["product_name", "current_quantity", "minimum_quantity", "shortage"]
                            if all(field in low_stock for field in low_stock_fields):
                                self.log_result("Structure low stock", True, 
                                              f"Stock faible: {low_stock['product_name']} "
                                              f"({low_stock['current_quantity']}/{low_stock['minimum_quantity']})")
                            else:
                                self.log_result("Structure low stock", False, "Champs manquants")
                        else:
                            self.log_result("Low stock items", True, "Aucun stock critique (bon signe)")
                    
                    # Vérifier les anomalies de prix
                    if isinstance(alerts_data["price_anomalies"], list):
                        if len(alerts_data["price_anomalies"]) > 0:
                            anomaly = alerts_data["price_anomalies"][0]
                            anomaly_fields = ["product_name", "supplier_name", "reference_price", 
                                            "actual_price", "difference_percentage"]
                            if all(field in anomaly for field in anomaly_fields):
                                self.log_result("Structure price anomalies", True, 
                                              f"Anomalie prix: {anomaly['product_name']} "
                                              f"({anomaly['difference_percentage']:.1f}%)")
                            else:
                                self.log_result("Structure price anomalies", False, "Champs manquants")
                        else:
                            self.log_result("Price anomalies", True, "Aucune anomalie de prix")
                else:
                    missing = [f for f in required_fields if f not in alerts_data]
                    self.log_result("GET /analytics/alerts", False, f"Champs manquants: {missing}")
            else:
                self.log_result("GET /analytics/alerts", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /analytics/alerts", False, "Exception", str(e))

    def test_analytics_cost_analysis(self):
        """Test API Analytics - Cost Analysis"""
        print("\n=== TEST ANALYTICS COST ANALYSIS ===")
        
        try:
            response = requests.get(f"{BASE_URL}/analytics/cost-analysis")
            if response.status_code == 200:
                cost_data = response.json()
                required_fields = ["total_inventory_value", "avg_cost_per_recipe", "most_expensive_ingredients", 
                                 "cost_trends", "waste_analysis"]
                
                if all(field in cost_data for field in required_fields):
                    self.log_result("GET /analytics/cost-analysis", True, 
                                  f"Analyse coûts: Inventaire {cost_data['total_inventory_value']:.2f}€, "
                                  f"Coût moyen recette {cost_data['avg_cost_per_recipe']:.2f}€")
                    
                    # Vérifier que les valeurs sont cohérentes
                    inventory_value = cost_data["total_inventory_value"]
                    avg_recipe_cost = cost_data["avg_cost_per_recipe"]
                    
                    if inventory_value >= 0 and avg_recipe_cost >= 0:
                        self.log_result("Valeurs cost analysis", True, "Valeurs positives cohérentes")
                    else:
                        self.log_result("Valeurs cost analysis", False, "Valeurs négatives détectées")
                    
                    # Vérifier la structure des ingrédients les plus chers
                    if isinstance(cost_data["most_expensive_ingredients"], list):
                        if len(cost_data["most_expensive_ingredients"]) > 0:
                            expensive = cost_data["most_expensive_ingredients"][0]
                            expensive_fields = ["name", "unit_price", "category"]
                            if all(field in expensive for field in expensive_fields):
                                self.log_result("Structure expensive ingredients", True, 
                                              f"Ingrédient le plus cher: {expensive['name']} "
                                              f"({expensive['unit_price']:.2f}€)")
                                
                                # Vérifier le tri par prix décroissant
                                if len(cost_data["most_expensive_ingredients"]) > 1:
                                    first_price = cost_data["most_expensive_ingredients"][0]["unit_price"]
                                    second_price = cost_data["most_expensive_ingredients"][1]["unit_price"]
                                    if first_price >= second_price:
                                        self.log_result("Tri expensive ingredients", True, "Tri par prix décroissant")
                                    else:
                                        self.log_result("Tri expensive ingredients", False, "Tri incorrect")
                            else:
                                self.log_result("Structure expensive ingredients", False, "Champs manquants")
                        else:
                            self.log_result("Expensive ingredients", True, "Aucun ingrédient (normal si pas de données)")
                    
                    # Vérifier les tendances de coûts
                    if isinstance(cost_data["cost_trends"], dict):
                        trend_fields = ["monthly_change", "quarterly_change", "highest_cost_category", "lowest_cost_category"]
                        if all(field in cost_data["cost_trends"] for field in trend_fields):
                            trends = cost_data["cost_trends"]
                            self.log_result("Structure cost trends", True, 
                                          f"Évolution mensuelle: {trends['monthly_change']}%, "
                                          f"Catégorie la plus chère: {trends['highest_cost_category']}")
                        else:
                            self.log_result("Structure cost trends", False, "Champs manquants dans cost_trends")
                    
                    # Vérifier l'analyse des déchets
                    if isinstance(cost_data["waste_analysis"], dict):
                        waste_fields = ["estimated_waste_percentage", "estimated_waste_value", "main_waste_sources"]
                        if all(field in cost_data["waste_analysis"] for field in waste_fields):
                            waste = cost_data["waste_analysis"]
                            self.log_result("Structure waste analysis", True, 
                                          f"Gaspillage estimé: {waste['estimated_waste_percentage']}% "
                                          f"({waste['estimated_waste_value']:.2f}€)")
                        else:
                            self.log_result("Structure waste analysis", False, "Champs manquants dans waste_analysis")
                else:
                    missing = [f for f in required_fields if f not in cost_data]
                    self.log_result("GET /analytics/cost-analysis", False, f"Champs manquants: {missing}")
            else:
                self.log_result("GET /analytics/cost-analysis", False, f"Erreur {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /analytics/cost-analysis", False, "Exception", str(e))

    def test_analytics_integration_with_data(self):
        """Test intégration des Analytics avec les données La Table d'Augustine"""
        print("\n=== TEST INTÉGRATION ANALYTICS AVEC DONNÉES LA TABLE D'AUGUSTINE ===")
        
        # D'abord s'assurer que les données La Table d'Augustine sont présentes
        try:
            # Vérifier les produits
            produits_response = requests.get(f"{BASE_URL}/produits")
            if produits_response.status_code == 200:
                produits = produits_response.json()
                augustine_products = [p for p in produits if any(keyword in p["nom"].lower() 
                                    for keyword in ["supions", "burrata", "truffe", "linguine", "palourdes"])]
                
                if len(augustine_products) >= 5:
                    self.log_result("Données La Table d'Augustine présentes", True, 
                                  f"{len(augustine_products)} produits authentiques détectés")
                    
                    # Test profitability avec données réelles
                    profitability_response = requests.get(f"{BASE_URL}/analytics/profitability")
                    if profitability_response.status_code == 200:
                        profitability_data = profitability_response.json()
                        augustine_recipes = [r for r in profitability_data if any(keyword in r["recipe_name"].lower() 
                                           for keyword in ["supions", "linguine", "rigatoni", "wellington", "caprese"])]
                        
                        if len(augustine_recipes) > 0:
                            self.log_result("Profitability avec données La Table d'Augustine", True, 
                                          f"{len(augustine_recipes)} recettes analysées")
                            
                            # Vérifier les calculs avec prix réels
                            for recipe in augustine_recipes[:2]:  # Tester les 2 premières
                                if recipe["selling_price"] and recipe["selling_price"] > 0:
                                    if recipe["ingredient_cost"] > 0:
                                        self.log_result(f"Calcul coût {recipe['recipe_name'][:20]}...", True, 
                                                      f"Coût ingrédients: {recipe['ingredient_cost']:.2f}€, "
                                                      f"Prix vente: {recipe['selling_price']:.2f}€")
                                    else:
                                        self.log_result(f"Calcul coût {recipe['recipe_name'][:20]}...", False, 
                                                      "Coût ingrédients non calculé")
                        else:
                            self.log_result("Profitability avec données La Table d'Augustine", False, 
                                          "Aucune recette La Table d'Augustine dans l'analyse")
                    
                    # Test cost analysis avec produits de luxe
                    cost_response = requests.get(f"{BASE_URL}/analytics/cost-analysis")
                    if cost_response.status_code == 200:
                        cost_data = cost_response.json()
                        expensive_ingredients = cost_data.get("most_expensive_ingredients", [])
                        
                        # Chercher la truffe dans les ingrédients les plus chers
                        truffe_found = any("truffe" in ing["name"].lower() for ing in expensive_ingredients)
                        if truffe_found:
                            truffe_ingredient = next(ing for ing in expensive_ingredients if "truffe" in ing["name"].lower())
                            if truffe_ingredient["unit_price"] >= 500:  # La truffe devrait être très chère
                                self.log_result("Détection produits luxe", True, 
                                              f"Truffe détectée à {truffe_ingredient['unit_price']:.2f}€/kg")
                            else:
                                self.log_result("Détection produits luxe", False, 
                                              f"Prix truffe incorrect: {truffe_ingredient['unit_price']:.2f}€")
                        else:
                            self.log_result("Détection produits luxe", False, "Truffe non détectée dans les plus chers")
                    
                    # Test alerts avec stocks La Table d'Augustine
                    alerts_response = requests.get(f"{BASE_URL}/analytics/alerts")
                    if alerts_response.status_code == 200:
                        alerts_data = alerts_response.json()
                        self.log_result("Alerts avec données La Table d'Augustine", True, 
                                      f"Système d'alertes opérationnel: {alerts_data['total_alerts']} alertes")
                        
                        # Vérifier que les noms de produits dans les alertes correspondent aux produits La Table d'Augustine
                        all_alert_products = []
                        for alert_type in ["expiring_products", "low_stock_items", "unused_stock"]:
                            for item in alerts_data.get(alert_type, []):
                                if "product_name" in item:
                                    all_alert_products.append(item["product_name"])
                        
                        if all_alert_products:
                            augustine_alerts = [p for p in all_alert_products if any(keyword in p.lower() 
                                              for keyword in ["supions", "burrata", "truffe", "linguine", "palourdes"])]
                            if augustine_alerts:
                                self.log_result("Alertes produits La Table d'Augustine", True, 
                                              f"{len(augustine_alerts)} alertes sur produits authentiques")
                            else:
                                self.log_result("Alertes produits La Table d'Augustine", True, 
                                              "Aucune alerte sur produits La Table d'Augustine (bon signe)")
                else:
                    self.log_result("Données La Table d'Augustine présentes", False, 
                                  f"Seulement {len(augustine_products)} produits authentiques trouvés")
            else:
                self.log_result("Vérification données produits", False, f"Erreur {produits_response.status_code}")
                
        except Exception as e:
            self.log_result("Test intégration Analytics", False, "Exception", str(e))

    def test_enhanced_ocr_parsing_apis(self):
        """Test complet des nouvelles APIs Enhanced OCR Parsing - Version 3 Feature #2"""
        print("\n=== TEST VERSION 3 ENHANCED OCR PARSING APIs ===")
        
        # Créer un document OCR de test pour les tests Enhanced
        enhanced_z_report_text = """
        RAPPORT Z - Service Soir - 06/01/2025
        
        === BAR ===
        (x3) Vin rouge Côtes du Rhône
        (x2) Kir Royal
        (x1) Digestif Armagnac
        
        === ENTRÉES ===
        (x4) Supions en persillade de Mamie
        (x2) Salade de tomates anciennes
        
        === PLATS ===
        (x3) Linguine aux palourdes & sauce à l'ail
        (x2) Rigatoni à la truffe fraîche de Forcalquier
        (x1) Bœuf Wellington à la truffe
        
        === DESSERTS ===
        (x2) Tiramisu maison
        (x1) Tarte aux figues
        
        TOTAL CA: 285.50€
        Couverts: 12
        """
        
        # Créer et uploader le document de test
        mock_image_base64 = self.create_mock_base64_image(enhanced_z_report_text)
        test_document_id = None
        
        try:
            files = {
                'file': ('enhanced_z_report_test.jpg', base64.b64decode(mock_image_base64), 'image/jpeg')
            }
            data = {'document_type': 'z_report'}
            
            response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                test_document_id = result.get("document_id")
                self.log_result("Setup Enhanced OCR Document", True, f"Document créé pour tests Enhanced: {test_document_id[:8]}...")
            else:
                self.log_result("Setup Enhanced OCR Document", False, f"Erreur {response.status_code}")
                return
        except Exception as e:
            self.log_result("Setup Enhanced OCR Document", False, f"Exception: {str(e)}")
            return
        
        # Test 1: POST /api/ocr/parse-z-report-enhanced
        print("\n--- Test Enhanced Z Report Parsing ---")
        try:
            response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced?document_id={test_document_id}", 
                                   headers=HEADERS)
            if response.status_code == 200:
                structured_data = response.json()
                
                # Vérifier la structure StructuredZReportData
                required_fields = ["report_date", "service", "items_by_category", "grand_total_sales", "raw_items"]
                if all(field in structured_data for field in required_fields):
                    self.log_result("POST /ocr/parse-z-report-enhanced - Structure", True, "Tous les champs StructuredZReportData présents")
                    
                    # Vérifier la catégorisation automatique
                    categories = structured_data.get("items_by_category", {})
                    expected_categories = ["Bar", "Entrées", "Plats", "Desserts"]
                    if all(cat in categories for cat in expected_categories):
                        self.log_result("Catégorisation automatique", True, f"4 catégories détectées: {list(categories.keys())}")
                        
                        # Vérifier le contenu des catégories
                        total_items = sum(len(items) for items in categories.values())
                        if total_items > 0:
                            self.log_result("Items catégorisés", True, f"{total_items} items répartis dans les catégories")
                            
                            # Vérifier la structure des items
                            for category, items in categories.items():
                                if items:  # Si la catégorie a des items
                                    item = items[0]
                                    item_fields = ["name", "quantity_sold", "category"]
                                    if all(field in item for field in item_fields):
                                        self.log_result(f"Structure items {category}", True, f"Structure StructuredZReportItem correcte")
                                        break
                        else:
                            self.log_result("Items catégorisés", False, "Aucun item détecté")
                    else:
                        missing_cats = [cat for cat in expected_categories if cat not in categories]
                        self.log_result("Catégorisation automatique", False, f"Catégories manquantes: {missing_cats}")
                    
                    # Vérifier l'extraction du service
                    if structured_data.get("service"):
                        self.log_result("Extraction service", True, f"Service détecté: {structured_data['service']}")
                    else:
                        self.log_result("Extraction service", False, "Service non détecté")
                    
                    # Vérifier l'extraction du total
                    if structured_data.get("grand_total_sales"):
                        self.log_result("Extraction total CA", True, f"Total CA: {structured_data['grand_total_sales']}€")
                    else:
                        self.log_result("Extraction total CA", False, "Total CA non détecté")
                        
                else:
                    missing = [f for f in required_fields if f not in structured_data]
                    self.log_result("POST /ocr/parse-z-report-enhanced - Structure", False, f"Champs manquants: {missing}")
            else:
                self.log_result("POST /ocr/parse-z-report-enhanced", False, f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("POST /ocr/parse-z-report-enhanced", False, f"Exception: {str(e)}")
        
        # Test 2: POST /api/ocr/calculate-stock-deductions
        print("\n--- Test Stock Deductions Calculation ---")
        try:
            # Utiliser des données structurées simulées pour le test
            test_structured_data = {
                "report_date": "06/01/2025",
                "service": "Soir",
                "items_by_category": {
                    "Bar": [
                        {"name": "Vin rouge Côtes du Rhône", "quantity_sold": 3, "category": "Bar"},
                        {"name": "Kir Royal", "quantity_sold": 2, "category": "Bar"}
                    ],
                    "Entrées": [
                        {"name": "Supions en persillade de Mamie", "quantity_sold": 4, "category": "Entrées"}
                    ],
                    "Plats": [
                        {"name": "Linguine aux palourdes", "quantity_sold": 3, "category": "Plats"},
                        {"name": "Rigatoni à la truffe", "quantity_sold": 2, "category": "Plats"}
                    ],
                    "Desserts": [
                        {"name": "Tiramisu maison", "quantity_sold": 2, "category": "Desserts"}
                    ]
                },
                "grand_total_sales": 285.50,
                "raw_items": []
            }
            
            response = requests.post(f"{BASE_URL}/ocr/calculate-stock-deductions", 
                                   json=test_structured_data, headers=HEADERS)
            if response.status_code == 200:
                validation_result = response.json()
                
                # Vérifier la structure ZReportValidationResult
                required_fields = ["can_validate", "proposed_deductions", "total_deductions", "warnings", "errors"]
                if all(field in validation_result for field in required_fields):
                    self.log_result("POST /ocr/calculate-stock-deductions - Structure", True, "Structure ZReportValidationResult correcte")
                    
                    # Vérifier les déductions proposées
                    deductions = validation_result.get("proposed_deductions", [])
                    if isinstance(deductions, list):
                        self.log_result("Calcul déductions stock", True, f"{len(deductions)} propositions de déduction calculées")
                        
                        # Vérifier la structure des déductions
                        if deductions:
                            deduction = deductions[0]
                            deduction_fields = ["recipe_name", "quantity_sold", "ingredient_deductions", "warnings"]
                            if all(field in deduction for field in deduction_fields):
                                self.log_result("Structure StockDeductionProposal", True, "Structure déduction correcte")
                                
                                # Vérifier les déductions d'ingrédients
                                ingredient_deductions = deduction.get("ingredient_deductions", [])
                                if ingredient_deductions:
                                    ingredient = ingredient_deductions[0]
                                    ingredient_fields = ["product_name", "current_stock", "deduction", "new_stock"]
                                    if all(field in ingredient for field in ingredient_fields):
                                        self.log_result("Calcul déductions ingrédients", True, "Calculs par ingrédient corrects")
                                    else:
                                        self.log_result("Calcul déductions ingrédients", False, "Structure ingrédient incorrecte")
                            else:
                                self.log_result("Structure StockDeductionProposal", False, "Champs déduction manquants")
                    else:
                        self.log_result("Calcul déductions stock", False, "Format déductions incorrect")
                        
                    # Vérifier la gestion des avertissements
                    warnings = validation_result.get("warnings", [])
                    if isinstance(warnings, list):
                        self.log_result("Gestion avertissements", True, f"{len(warnings)} avertissement(s) générés")
                    else:
                        self.log_result("Gestion avertissements", False, "Format avertissements incorrect")
                        
                else:
                    missing = [f for f in required_fields if f not in validation_result]
                    self.log_result("POST /ocr/calculate-stock-deductions - Structure", False, f"Champs manquants: {missing}")
            else:
                self.log_result("POST /ocr/calculate-stock-deductions", False, f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("POST /ocr/calculate-stock-deductions", False, f"Exception: {str(e)}")
        
        # Test 3: GET /api/ocr/z-report-preview/{document_id}
        print("\n--- Test Z Report Preview ---")
        if test_document_id:
            try:
                response = requests.get(f"{BASE_URL}/ocr/z-report-preview/{test_document_id}")
                if response.status_code == 200:
                    preview_data = response.json()
                    
                    # Vérifier la structure de prévisualisation
                    required_fields = ["document_id", "structured_data", "validation_result", "can_apply", "preview_only"]
                    if all(field in preview_data for field in required_fields):
                        self.log_result("GET /ocr/z-report-preview - Structure", True, "Structure prévisualisation correcte")
                        
                        # Vérifier que c'est bien en mode preview
                        if preview_data.get("preview_only") is True:
                            self.log_result("Mode preview", True, "Mode preview_only activé")
                        else:
                            self.log_result("Mode preview", False, "Mode preview incorrect")
                            
                        # Vérifier la présence des données structurées
                        if preview_data.get("structured_data") and preview_data.get("validation_result"):
                            self.log_result("Données preview complètes", True, "Données structurées et validation présentes")
                        else:
                            self.log_result("Données preview complètes", False, "Données preview incomplètes")
                    else:
                        missing = [f for f in required_fields if f not in preview_data]
                        self.log_result("GET /ocr/z-report-preview - Structure", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("GET /ocr/z-report-preview", False, f"Erreur {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("GET /ocr/z-report-preview", False, f"Exception: {str(e)}")
        
        # Test 4: POST /api/ocr/validate-z-report (sans application)
        print("\n--- Test Z Report Validation (Preview Mode) ---")
        if test_document_id:
            try:
                response = requests.post(f"{BASE_URL}/ocr/validate-z-report?document_id={test_document_id}&apply_deductions=false", 
                                       headers=HEADERS)
                if response.status_code == 200:
                    validation_response = response.json()
                    
                    # Vérifier la structure de validation
                    required_fields = ["document_id", "structured_data", "validation_result", "applied"]
                    if all(field in validation_response for field in required_fields):
                        self.log_result("POST /ocr/validate-z-report (preview)", True, "Structure validation correcte")
                        
                        # Vérifier que les déductions ne sont pas appliquées
                        if validation_response.get("applied") is False:
                            self.log_result("Mode validation preview", True, "Déductions non appliquées en mode preview")
                        else:
                            self.log_result("Mode validation preview", False, "Déductions appliquées incorrectement")
                    else:
                        missing = [f for f in required_fields if f not in validation_response]
                        self.log_result("POST /ocr/validate-z-report (preview)", False, f"Champs manquants: {missing}")
                else:
                    self.log_result("POST /ocr/validate-z-report (preview)", False, f"Erreur {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("POST /ocr/validate-z-report (preview)", False, f"Exception: {str(e)}")
        
        # Test 5: Fuzzy Matching et Pattern Recognition
        print("\n--- Test Enhanced Parsing Logic ---")
        
        # Test avec différents formats de noms de plats
        test_formats = [
            "(x2) Linguine aux palourdes",  # Format standard
            "3x Supions persillade",        # Format alternatif
            "Rigatoni truffe: 1",          # Format avec deux points
            "Bœuf Wellington €56.00 x 1"   # Format avec prix
        ]
        
        for test_format in test_formats:
            test_text = f"RAPPORT Z - 06/01/2025\n{test_format}\nTotal: 50.00€"
            mock_image = self.create_mock_base64_image(test_text)
            
            try:
                files = {
                    'file': ('pattern_test.jpg', base64.b64decode(mock_image), 'image/jpeg')
                }
                data = {'document_type': 'z_report'}
                
                upload_response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
                if upload_response.status_code in [200, 201]:
                    doc_id = upload_response.json().get("document_id")
                    
                    parse_response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced", 
                                                 json={"document_id": doc_id}, headers=HEADERS)
                    if parse_response.status_code == 200:
                        parsed_data = parse_response.json()
                        total_items = sum(len(items) for items in parsed_data.get("items_by_category", {}).values())
                        if total_items > 0:
                            self.log_result(f"Pattern Recognition: {test_format[:20]}...", True, f"{total_items} item(s) détecté(s)")
                        else:
                            self.log_result(f"Pattern Recognition: {test_format[:20]}...", False, "Aucun item détecté")
                    else:
                        self.log_result(f"Pattern Recognition: {test_format[:20]}...", False, f"Erreur parsing {parse_response.status_code}")
                else:
                    self.log_result(f"Pattern Recognition: {test_format[:20]}...", False, f"Erreur upload {upload_response.status_code}")
            except Exception as e:
                self.log_result(f"Pattern Recognition: {test_format[:20]}...", False, f"Exception: {str(e)}")
        
        # Test 6: Integration avec recettes existantes
        print("\n--- Test Integration avec Recettes Existantes ---")
        try:
            # Récupérer les recettes existantes pour tester le matching
            recettes_response = requests.get(f"{BASE_URL}/recettes")
            if recettes_response.status_code == 200:
                recettes = recettes_response.json()
                if recettes:
                    # Utiliser une recette existante pour tester le fuzzy matching
                    test_recipe = recettes[0]
                    recipe_name = test_recipe["nom"]
                    
                    # Créer un Z-report avec le nom de la recette (légèrement modifié)
                    modified_name = recipe_name.replace("aux", "").strip()  # Simplifier le nom
                    integration_test_text = f"""
                    RAPPORT Z - 06/01/2025
                    (x2) {modified_name}
                    Total: 50.00€
                    """
                    
                    mock_image = self.create_mock_base64_image(integration_test_text)
                    files = {
                        'file': ('integration_test.jpg', base64.b64decode(mock_image), 'image/jpeg')
                    }
                    data = {'document_type': 'z_report'}
                    
                    upload_response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
                    if upload_response.status_code in [200, 201]:
                        doc_id = upload_response.json().get("document_id")
                        
                        # Tester le calcul des déductions avec une vraie recette
                        parse_response = requests.post(f"{BASE_URL}/ocr/parse-z-report-enhanced?document_id={doc_id}", 
                                                     headers=HEADERS)
                        if parse_response.status_code == 200:
                            structured_data = parse_response.json()
                            
                            deduction_response = requests.post(f"{BASE_URL}/ocr/calculate-stock-deductions", 
                                                             json=structured_data, headers=HEADERS)
                            if deduction_response.status_code == 200:
                                deduction_result = deduction_response.json()
                                proposed_deductions = deduction_result.get("proposed_deductions", [])
                                
                                if proposed_deductions:
                                    self.log_result("Fuzzy Matching avec recettes", True, 
                                                  f"Recette '{recipe_name}' matchée avec déductions calculées")
                                    
                                    # Vérifier que les ingrédients sont correctement traités
                                    first_deduction = proposed_deductions[0]
                                    ingredient_deductions = first_deduction.get("ingredient_deductions", [])
                                    if ingredient_deductions:
                                        self.log_result("Calcul ingrédients recette réelle", True, 
                                                      f"{len(ingredient_deductions)} ingrédient(s) traités")
                                    else:
                                        self.log_result("Calcul ingrédients recette réelle", False, "Aucun ingrédient traité")
                                else:
                                    self.log_result("Fuzzy Matching avec recettes", False, "Aucune déduction proposée")
                            else:
                                self.log_result("Fuzzy Matching avec recettes", False, f"Erreur calcul déductions {deduction_response.status_code}")
                        else:
                            self.log_result("Fuzzy Matching avec recettes", False, f"Erreur parsing {parse_response.status_code}")
                    else:
                        self.log_result("Fuzzy Matching avec recettes", False, f"Erreur upload {upload_response.status_code}")
                else:
                    self.log_result("Fuzzy Matching avec recettes", False, "Aucune recette disponible pour le test")
            else:
                self.log_result("Fuzzy Matching avec recettes", False, f"Erreur récupération recettes {recettes_response.status_code}")
        except Exception as e:
            self.log_result("Fuzzy Matching avec recettes", False, f"Exception: {str(e)}")
        
        print(f"\n=== FIN TEST VERSION 3 ENHANCED OCR PARSING APIs ===")

    def test_enhanced_ocr_stock_integration(self):
        """Test intégration complète Enhanced OCR avec gestion des stocks"""
        print("\n=== TEST INTÉGRATION ENHANCED OCR - STOCKS ===")
        
        # Ce test nécessite des données La Table d'Augustine pour fonctionner correctement
        # Vérifier d'abord que nous avons des recettes et des stocks
        try:
            recettes_response = requests.get(f"{BASE_URL}/recettes")
            stocks_response = requests.get(f"{BASE_URL}/stocks")
            
            if recettes_response.status_code != 200 or stocks_response.status_code != 200:
                self.log_result("Prérequis intégration OCR-Stocks", False, "Impossible d'accéder aux recettes ou stocks")
                return
                
            recettes = recettes_response.json()
            stocks = stocks_response.json()
            
            if not recettes or not stocks:
                self.log_result("Prérequis intégration OCR-Stocks", False, "Pas de recettes ou stocks disponibles")
                return
                
            self.log_result("Prérequis intégration OCR-Stocks", True, f"{len(recettes)} recettes, {len(stocks)} stocks disponibles")
            
            # Sélectionner une recette avec des ingrédients pour le test
            test_recipe = None
            for recipe in recettes:
                if recipe.get("ingredients") and len(recipe["ingredients"]) > 0:
                    test_recipe = recipe
                    break
            
            if not test_recipe:
                self.log_result("Sélection recette test", False, "Aucune recette avec ingrédients trouvée")
                return
                
            self.log_result("Sélection recette test", True, f"Recette sélectionnée: {test_recipe['nom']}")
            
            # Créer un Z-report réaliste avec cette recette
            realistic_z_report = f"""
            RAPPORT Z - Service Soir - 06/01/2025
            
            === PLATS ===
            (x3) {test_recipe['nom']}
            
            TOTAL CA: {test_recipe.get('prix_vente', 25) * 3:.2f}€
            Couverts: 3
            """
            
            # Uploader et traiter le document
            mock_image = self.create_mock_base64_image(realistic_z_report)
            files = {
                'file': ('integration_stock_test.jpg', base64.b64decode(mock_image), 'image/jpeg')
            }
            data = {'document_type': 'z_report'}
            
            upload_response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
            if upload_response.status_code not in [200, 201]:
                self.log_result("Upload document intégration", False, f"Erreur upload {upload_response.status_code}")
                return
                
            doc_id = upload_response.json().get("document_id")
            self.log_result("Upload document intégration", True, f"Document créé: {doc_id[:8]}...")
            
            # Sauvegarder les stocks actuels pour comparaison
            initial_stocks = {}
            for ingredient in test_recipe["ingredients"]:
                product_id = ingredient["produit_id"]
                stock_response = requests.get(f"{BASE_URL}/stocks/{product_id}")
                if stock_response.status_code == 200:
                    stock_data = stock_response.json()
                    initial_stocks[product_id] = stock_data["quantite_actuelle"]
            
            # Test validation avec application des déductions
            try:
                validation_response = requests.post(f"{BASE_URL}/ocr/validate-z-report", 
                                                  json={"document_id": doc_id, "apply_deductions": True}, 
                                                  headers=HEADERS)
                if validation_response.status_code == 200:
                    validation_result = validation_response.json()
                    
                    if validation_result.get("applied"):
                        self.log_result("Application déductions stocks", True, "Déductions appliquées avec succès")
                        
                        # Vérifier que les stocks ont été mis à jour
                        stocks_updated = 0
                        for ingredient in test_recipe["ingredients"]:
                            product_id = ingredient["produit_id"]
                            stock_response = requests.get(f"{BASE_URL}/stocks/{product_id}")
                            if stock_response.status_code == 200:
                                new_stock = stock_response.json()["quantite_actuelle"]
                                initial_stock = initial_stocks.get(product_id, 0)
                                
                                if new_stock != initial_stock:
                                    stocks_updated += 1
                        
                        if stocks_updated > 0:
                            self.log_result("Mise à jour stocks automatique", True, f"{stocks_updated} stock(s) mis à jour")
                        else:
                            self.log_result("Mise à jour stocks automatique", False, "Aucun stock mis à jour")
                        
                        # Vérifier la création de mouvements de stock
                        mouvements_response = requests.get(f"{BASE_URL}/mouvements")
                        if mouvements_response.status_code == 200:
                            mouvements = mouvements_response.json()
                            # Chercher les mouvements récents avec commentaire de déduction automatique
                            recent_deductions = [m for m in mouvements if 
                                               "Déduction automatique" in m.get("commentaire", "") and
                                               m.get("type") == "sortie"]
                            
                            if recent_deductions:
                                self.log_result("Création mouvements automatiques", True, 
                                              f"{len(recent_deductions)} mouvement(s) de déduction créés")
                            else:
                                self.log_result("Création mouvements automatiques", False, "Aucun mouvement de déduction trouvé")
                        
                        # Vérifier la création du RapportZ
                        if validation_result.get("rapport_z_created"):
                            rapports_response = requests.get(f"{BASE_URL}/rapports_z")
                            if rapports_response.status_code == 200:
                                rapports = rapports_response.json()
                                # Chercher le rapport le plus récent
                                if rapports:
                                    latest_rapport = rapports[0]  # Supposé trié par date décroissante
                                    expected_ca = test_recipe.get('prix_vente', 25) * 3
                                    if abs(latest_rapport.get("ca_total", 0) - expected_ca) < 0.01:
                                        self.log_result("Création RapportZ automatique", True, 
                                                      f"RapportZ créé avec CA {latest_rapport['ca_total']}€")
                                    else:
                                        self.log_result("Création RapportZ automatique", False, "CA incorrect dans RapportZ")
                                else:
                                    self.log_result("Création RapportZ automatique", False, "Aucun RapportZ trouvé")
                        else:
                            self.log_result("Création RapportZ automatique", False, "RapportZ non créé")
                            
                    else:
                        self.log_result("Application déductions stocks", False, "Déductions non appliquées")
                        
                        # Vérifier les raisons (warnings/errors)
                        validation_data = validation_result.get("validation_result", {})
                        warnings = validation_data.get("warnings", [])
                        errors = validation_data.get("errors", [])
                        
                        if warnings or errors:
                            self.log_result("Analyse échec déductions", True, 
                                          f"{len(warnings)} warning(s), {len(errors)} erreur(s) détectées")
                        else:
                            self.log_result("Analyse échec déductions", False, "Aucune explication d'échec")
                else:
                    self.log_result("Application déductions stocks", False, f"Erreur validation {validation_response.status_code}")
                    
            except Exception as e:
                self.log_result("Application déductions stocks", False, f"Exception: {str(e)}")
                
        except Exception as e:
            self.log_result("Test intégration OCR-Stocks", False, f"Exception générale: {str(e)}")

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 DÉBUT DES TESTS BACKEND - GESTION STOCKS RESTAURANT + OCR")
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
        # Note: Demo endpoints not implemented, skipping demo tests
        self.test_recettes_crud()
        self.test_production_capacity_calculator()
        self.test_recettes_excel_export()
        self.test_recettes_excel_import()
        self.test_recette_delete()
        
        # Tests OCR - Système de traitement de documents
        print("\n" + "=" * 60)
        print("🔍 TESTS SYSTÈME OCR - TRAITEMENT DOCUMENTS RESTAURANT")
        print("=" * 60)
        
        self.test_ocr_document_upload_z_report()
        self.test_ocr_document_upload_facture()
        self.test_ocr_documents_list()
        self.test_ocr_document_by_id()
        self.test_ocr_z_report_stock_processing()
        self.test_ocr_document_delete()
        self.test_ocr_error_handling()
        
        # 🆕 NOUVEAUX TESTS VERSION 3 FEATURE #2 - ENHANCED OCR PARSING
        print("\n" + "=" * 60)
        print("🆕 TESTS VERSION 3 ENHANCED OCR PARSING APIs")
        print("=" * 60)
        
        self.test_enhanced_ocr_parsing_apis()
        self.test_enhanced_ocr_stock_integration()
        
        # Tests des nouveaux endpoints Rapports Z
        print("\n" + "=" * 60)
        print("📊 TESTS NOUVEAUX ENDPOINTS RAPPORTS Z")
        print("=" * 60)
        
        self.test_rapports_z_crud()
        
        # 🎯 NOUVEAUX TESTS ANALYTICS & PROFITABILITY VERSION 3
        print("\n" + "="*60)
        print("🎯 TESTS ANALYTICS & PROFITABILITY VERSION 3")
        print("="*60)
        
        self.test_analytics_profitability()
        self.test_analytics_sales_performance()
        self.test_analytics_alerts()
        self.test_analytics_cost_analysis()
        self.test_analytics_integration_with_data()
        
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