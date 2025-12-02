#!/usr/bin/env python3
"""
Debug script pour identifier les problèmes spécifiques du système PRODUITS + PRÉPARATIONS
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "https://cuisinepro.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_execute_preparation_request_format():
    """Test du format de requête pour l'exécution de préparation"""
    print("=== TEST FORMAT REQUÊTE EXÉCUTION PRÉPARATION ===")
    
    # Créer un produit et une préparation de test
    produit_data = {
        "nom": "Test Produit Debug",
        "categorie": "Test",
        "unite": "kg",
        "prix_achat": 5.0
    }
    
    produit_response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
    if produit_response.status_code != 200:
        print(f"❌ Erreur création produit: {produit_response.status_code}")
        return
    
    produit = produit_response.json()
    produit_id = produit["id"]
    print(f"✅ Produit créé: {produit_id}")
    
    # Ajouter du stock
    stock_update = {"quantite_actuelle": 10.0}
    requests.put(f"{BASE_URL}/stocks/{produit_id}", json=stock_update, headers=HEADERS)
    
    # Créer une préparation
    preparation_data = {
        "nom": "Test Préparation Debug",
        "produit_id": produit_id,
        "forme_decoupe": "émincé",
        "quantite_produit_brut": 1.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 0.8,
        "unite_preparee": "kg",
        "perte": 0.2,
        "perte_pourcentage": 20.0,
        "nombre_portions": 4,
        "taille_portion": 0.2,
        "unite_portion": "kg"
    }
    
    prep_response = requests.post(f"{BASE_URL}/preparations", json=preparation_data, headers=HEADERS)
    if prep_response.status_code != 200:
        print(f"❌ Erreur création préparation: {prep_response.status_code}")
        return
    
    preparation = prep_response.json()
    preparation_id = preparation["id"]
    print(f"✅ Préparation créée: {preparation_id}")
    
    # Test 1: Format actuel (avec preparation_id dans le body - INCORRECT)
    execute_data_wrong = {
        "preparation_id": preparation_id,  # Ne devrait pas être là
        "quantite_a_produire": 1.6,
        "notes": "Test format incorrect"
    }
    
    response1 = requests.post(f"{BASE_URL}/preparations/{preparation_id}/execute", 
                             json=execute_data_wrong, headers=HEADERS)
    print(f"Test format avec preparation_id dans body: {response1.status_code}")
    if response1.status_code != 200:
        print(f"   Erreur: {response1.text}")
    
    # Test 2: Format correct (sans preparation_id dans le body)
    execute_data_correct = {
        "quantite_a_produire": 1.6,
        "notes": "Test format correct"
    }
    
    response2 = requests.post(f"{BASE_URL}/preparations/{preparation_id}/execute", 
                             json=execute_data_correct, headers=HEADERS)
    print(f"Test format sans preparation_id dans body: {response2.status_code}")
    if response2.status_code != 200:
        print(f"   Erreur: {response2.text}")
    else:
        result = response2.json()
        print(f"   ✅ Succès: {result.get('success')}")
        print(f"   Quantité produite: {result.get('quantite_produite')}")
    
    # Nettoyage
    requests.delete(f"{BASE_URL}/preparations/{preparation_id}")
    requests.delete(f"{BASE_URL}/produits/{produit_id}")

def test_stock_preparation_response_format():
    """Test du format de réponse pour la création de stock préparation"""
    print("\n=== TEST FORMAT RÉPONSE STOCK PRÉPARATION ===")
    
    # Créer une préparation de test
    produit_data = {
        "nom": "Test Produit Stock Prep",
        "categorie": "Test",
        "unite": "kg",
        "prix_achat": 5.0
    }
    
    produit_response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
    produit = produit_response.json()
    produit_id = produit["id"]
    
    preparation_data = {
        "nom": "Test Préparation Stock",
        "produit_id": produit_id,
        "forme_decoupe": "émincé",
        "quantite_produit_brut": 1.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 0.8,
        "unite_preparee": "kg",
        "perte": 0.2,
        "perte_pourcentage": 20.0,
        "nombre_portions": 4,
        "taille_portion": 0.2,
        "unite_portion": "kg"
    }
    
    prep_response = requests.post(f"{BASE_URL}/preparations", json=preparation_data, headers=HEADERS)
    preparation = prep_response.json()
    preparation_id = preparation["id"]
    
    # Créer un stock de préparation
    stock_prep_data = {
        "preparation_id": preparation_id,
        "quantite_actuelle": 2.0,
        "quantite_min": 0.5,
        "dlc": (datetime.now() + timedelta(days=2)).isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/stock-preparations", json=stock_prep_data, headers=HEADERS)
    print(f"POST /stock-preparations status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Réponse actuelle: {result}")
        
        # Vérifier si on a l'ID pour récupérer l'objet complet
        if "id" in result:
            stock_id = result["id"]
            get_response = requests.get(f"{BASE_URL}/stock-preparations/{stock_id}")
            if get_response.status_code == 200:
                full_stock = get_response.json()
                print(f"Objet complet: {json.dumps(full_stock, indent=2)}")
                
                # Vérifier les champs requis
                required_fields = ["preparation_id", "quantite_actuelle", "unite", "dlc", "statut"]
                missing_fields = [f for f in required_fields if f not in full_stock]
                if missing_fields:
                    print(f"❌ Champs manquants: {missing_fields}")
                else:
                    print(f"✅ Tous les champs requis présents")
    else:
        print(f"❌ Erreur: {response.text}")
    
    # Nettoyage
    requests.delete(f"{BASE_URL}/preparations/{preparation_id}")
    requests.delete(f"{BASE_URL}/produits/{produit_id}")

def test_recette_ingredient_compatibility():
    """Test de la compatibilité des formats d'ingrédients dans les recettes"""
    print("\n=== TEST COMPATIBILITÉ INGRÉDIENTS RECETTES ===")
    
    # Créer un produit de test
    produit_data = {
        "nom": "Test Produit Recette",
        "categorie": "Test",
        "unite": "kg",
        "prix_achat": 5.0
    }
    
    produit_response = requests.post(f"{BASE_URL}/produits", json=produit_data, headers=HEADERS)
    produit = produit_response.json()
    produit_id = produit["id"]
    
    # Test 1: Nouveau format (avec ingredient_id et ingredient_type)
    recette_new_format = {
        "nom": "Recette Nouveau Format",
        "categorie": "Test",
        "portions": 2,
        "prix_vente": 15.0,
        "ingredients": [
            {
                "ingredient_id": produit_id,
                "ingredient_type": "produit",
                "quantite": 0.5,
                "unite": "kg"
            }
        ]
    }
    
    response1 = requests.post(f"{BASE_URL}/recettes", json=recette_new_format, headers=HEADERS)
    print(f"Nouveau format: {response1.status_code}")
    if response1.status_code != 200:
        print(f"   Erreur: {response1.text}")
    else:
        recette1 = response1.json()
        print(f"   ✅ Recette créée: {recette1['id']}")
        requests.delete(f"{BASE_URL}/recettes/{recette1['id']}")
    
    # Test 2: Ancien format (avec produit_id seulement)
    recette_old_format = {
        "nom": "Recette Ancien Format",
        "categorie": "Test",
        "portions": 2,
        "prix_vente": 15.0,
        "ingredients": [
            {
                "produit_id": produit_id,  # Ancien format
                "quantite": 0.5,
                "unite": "kg"
            }
        ]
    }
    
    response2 = requests.post(f"{BASE_URL}/recettes", json=recette_old_format, headers=HEADERS)
    print(f"Ancien format: {response2.status_code}")
    if response2.status_code != 200:
        print(f"   Erreur: {response2.text}")
    else:
        recette2 = response2.json()
        print(f"   ✅ Recette créée: {recette2['id']}")
        requests.delete(f"{BASE_URL}/recettes/{recette2['id']}")
    
    # Nettoyage
    requests.delete(f"{BASE_URL}/produits/{produit_id}")

if __name__ == "__main__":
    print("🔍 DEBUG DES PROBLÈMES SYSTÈME PRODUITS + PRÉPARATIONS")
    print("=" * 60)
    
    test_execute_preparation_request_format()
    test_stock_preparation_response_format()
    test_recette_ingredient_compatibility()
    
    print("\n✅ DEBUG TERMINÉ")