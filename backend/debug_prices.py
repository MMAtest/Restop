
import requests
import os
import re

files = [
    {"name": "TerreAzur_New.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/7qzrl1gi_PXL_20251205_195145748.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_price_location():
    print("🚀 RECHERCHE DES PRIX PERDUS - TERREAZUR")
    
    for file_info in files:
        try:
            r = requests.get(file_info['url'])
            path = f"/tmp/{file_info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (file_info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                data = res.json()
                print("--- TOUS LES NOMBRES DÉCIMAUX TROUVÉS ---")
                if 'texte_extrait' in data:
                    lines = data['texte_extrait'].split('\n')
                    for i, line in enumerate(lines):
                        # Cherche xx,xx ou xx.xx
                        matches = re.findall(r'(\d+[\.,]\d{2})', line)
                        if matches:
                            print(f"Ligne {i}: {matches} -> Contexte: '{line.strip()}'")
                print("-------------------------------------------")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_price_location()
