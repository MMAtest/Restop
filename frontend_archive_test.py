#!/usr/bin/env python3
"""
Test de simulation des appels frontend vers l'API d'archivage
Simule exactement ce que fait le frontend JavaScript
"""

import requests
import json

# Configuration identique au frontend
BACKEND_URL = "https://resto-inventory-32.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"
HEADERS = {"Content-Type": "application/json"}

def test_frontend_archive_simulation():
    """Simule exactement les appels que fait le frontend"""
    print("🔍 TEST SIMULATION FRONTEND - APPELS D'ARCHIVAGE")
    print("=" * 60)
    
    # 1. Récupérer une recette existante (comme le ferait le frontend)
    print("\n1. Récupération des recettes...")
    try:
        response = requests.get(f"{API}/recettes")
        if response.status_code == 200:
            recettes = response.json()
            if len(recettes) > 0:
                test_recette = recettes[0]
                print(f"✅ Recette trouvée: {test_recette['nom']} (ID: {test_recette['id']})")
                
                # 2. Simuler l'appel d'archivage exact du frontend
                print(f"\n2. Test archivage de la recette '{test_recette['nom']}'...")
                
                archive_payload = {
                    "item_id": test_recette['id'],
                    "item_type": "production",
                    "reason": "Test simulation frontend"
                }
                
                print(f"   Payload envoyé: {json.dumps(archive_payload, indent=2)}")
                print(f"   URL: {API}/archive")
                print(f"   Headers: {HEADERS}")
                
                try:
                    archive_response = requests.post(f"{API}/archive", 
                                                   json=archive_payload, 
                                                   headers=HEADERS)
                    
                    print(f"   Status Code: {archive_response.status_code}")
                    print(f"   Response: {archive_response.text}")
                    
                    if archive_response.status_code == 200:
                        result = archive_response.json()
                        archive_id = result.get("archive_id")
                        print(f"✅ ARCHIVAGE RÉUSSI - Archive ID: {archive_id}")
                        
                        # 3. Vérifier que la recette n'existe plus
                        print(f"\n3. Vérification suppression de la recette...")
                        check_response = requests.get(f"{API}/recettes/{test_recette['id']}")
                        if check_response.status_code == 404:
                            print("✅ Recette correctement supprimée de la collection")
                        else:
                            print(f"❌ Recette encore présente: {check_response.status_code}")
                        
                        # 4. Vérifier que l'archive existe
                        print(f"\n4. Vérification création de l'archive...")
                        archives_response = requests.get(f"{API}/archives")
                        if archives_response.status_code == 200:
                            archives = archives_response.json()
                            our_archive = next((a for a in archives if a["id"] == archive_id), None)
                            if our_archive:
                                print(f"✅ Archive trouvée: {our_archive['item_type']} - {our_archive['original_data']['nom']}")
                            else:
                                print("❌ Archive non trouvée")
                        
                        # 5. Restaurer la recette
                        print(f"\n5. Restauration de la recette...")
                        restore_response = requests.post(f"{API}/restore/{archive_id}", headers=HEADERS)
                        if restore_response.status_code == 200:
                            print("✅ Recette restaurée avec succès")
                            
                            # Vérifier que la recette est de retour
                            final_check = requests.get(f"{API}/recettes/{test_recette['id']}")
                            if final_check.status_code == 200:
                                restored_recette = final_check.json()
                                print(f"✅ Recette restaurée confirmée: {restored_recette['nom']}")
                            else:
                                print("❌ Recette non restaurée")
                        else:
                            print(f"❌ Erreur restauration: {restore_response.status_code} - {restore_response.text}")
                    
                    else:
                        print(f"❌ ARCHIVAGE ÉCHOUÉ: {archive_response.status_code}")
                        print(f"   Erreur: {archive_response.text}")
                        
                        # Analyser l'erreur
                        if archive_response.status_code == 404:
                            print("   → L'ID de la recette n'existe pas")
                        elif archive_response.status_code == 400:
                            print("   → Erreur dans les données envoyées")
                        elif archive_response.status_code == 500:
                            print("   → Erreur serveur backend")
                        else:
                            print(f"   → Erreur inconnue: {archive_response.status_code}")
                
                except requests.exceptions.RequestException as e:
                    print(f"❌ ERREUR RÉSEAU: {str(e)}")
                    print("   → Problème de connexion entre frontend et backend")
                
            else:
                print("❌ Aucune recette trouvée pour le test")
        else:
            print(f"❌ Erreur récupération recettes: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR RÉSEAU INITIALE: {str(e)}")
    
    print("\n" + "=" * 60)
    
    # Test avec un fournisseur aussi
    print("\n🔍 TEST ARCHIVAGE FOURNISSEUR")
    print("=" * 40)
    
    try:
        response = requests.get(f"{API}/fournisseurs")
        if response.status_code == 200:
            fournisseurs = response.json()
            if len(fournisseurs) > 0:
                test_fournisseur = fournisseurs[-1]  # Prendre le dernier
                print(f"✅ Fournisseur trouvé: {test_fournisseur['nom']} (ID: {test_fournisseur['id']})")
                
                archive_payload = {
                    "item_id": test_fournisseur['id'],
                    "item_type": "fournisseur",
                    "reason": "Test simulation frontend fournisseur"
                }
                
                archive_response = requests.post(f"{API}/archive", 
                                               json=archive_payload, 
                                               headers=HEADERS)
                
                if archive_response.status_code == 200:
                    result = archive_response.json()
                    archive_id = result.get("archive_id")
                    print(f"✅ FOURNISSEUR ARCHIVÉ - Archive ID: {archive_id}")
                    
                    # Restaurer immédiatement
                    restore_response = requests.post(f"{API}/restore/{archive_id}", headers=HEADERS)
                    if restore_response.status_code == 200:
                        print("✅ Fournisseur restauré avec succès")
                    else:
                        print(f"❌ Erreur restauration fournisseur: {restore_response.status_code}")
                else:
                    print(f"❌ ARCHIVAGE FOURNISSEUR ÉCHOUÉ: {archive_response.status_code}")
                    print(f"   Erreur: {archive_response.text}")
    
    except Exception as e:
        print(f"❌ Erreur test fournisseur: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")
    print("Si tous les tests ci-dessus sont ✅, alors le problème est uniquement côté frontend JavaScript.")
    print("Si des tests sont ❌, alors il y a un problème backend ou réseau.")
    print("=" * 60)

if __name__ == "__main__":
    test_frontend_archive_simulation()