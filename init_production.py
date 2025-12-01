#!/usr/bin/env python3
"""
Script pour initialiser la base de données de production
Utilisation: python3 init_production.py https://votre-app.emergent.host
"""

import sys
import requests

def init_production(base_url):
    """Initialise la base de données de production"""
    
    # Supprimer le slash final si présent
    base_url = base_url.rstrip('/')
    
    print(f"🚀 Initialisation de la base de données production")
    print(f"📍 URL: {base_url}\n")
    
    # 1. Créer les utilisateurs
    print("👥 Étape 1/2: Création des utilisateurs...")
    try:
        response = requests.post(f"{base_url}/api/demo/init-missions-users", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result.get('users_created', 0)} utilisateurs créés")
            print(f"   📧 Vous pouvez vous connecter avec:")
            print(f"      - patron@table-augustine.fr / password123")
            print(f"      - chef@table-augustine.fr / password123")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # 2. Créer les données restaurant
    print("\n🍽️  Étape 2/2: Création des données restaurant...")
    try:
        response = requests.post(f"{base_url}/api/demo/init-real-restaurant-data", timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result.get('fournisseurs_created', 0)} fournisseurs créés")
            print(f"   ✅ {result.get('produits_created', 0)} produits créés")
            print(f"   ✅ {result.get('preparations_created', 0)} préparations créées")
            print(f"   ✅ {result.get('recettes_created', 0)} recettes créées")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n✅ Initialisation terminée avec succès!")
    print(f"\n🌐 Accédez à votre application: {base_url}")
    print(f"📧 Connectez-vous avec: patron@table-augustine.fr / password123")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 init_production.py https://votre-app.emergent.host")
        print("\nExemple: python3 init_production.py https://rest-mgmt-sys.emergent.host")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    if not base_url.startswith('http'):
        print("❌ L'URL doit commencer par http:// ou https://")
        sys.exit(1)
    
    success = init_production(base_url)
    sys.exit(0 if success else 1)
