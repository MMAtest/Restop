
import requests
import os
import json

files = [
    {"name": "Mamma_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nc0hqxeh_PXL_20251205_184115055.jpg"},
    {"name": "Mamma_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/fszj1xrd_PXL_20251205_184134943.MP.jpg"},
    {"name": "Mamma_3.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/tk485eeb_PXL_20251205_184303249.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_mammafiore():
    print("🚀 DEBUG RAW TEXT MAMMAFIORE")
    
    for file_info in files:
        print(f"\n📸 {file_info['name']}...")
        try:
            # Download
            r = requests.get(file_info['url'])
            path = f"/tmp/{file_info['name']}"
            with open(path, 'wb') as f:
                f.write(r.content)
                
            # Upload
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (file_info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                data = res.json()
                print("--- DEBUT TEXTE BRUT ---")
                # On affiche les 1000 premiers caractères et surtout la partie produits
                if 'texte_extrait' in data:
                    # Filtrer pour montrer la zone intéressante (autour des codes 1000...)
                    lines = data['texte_extrait'].split('\n')
                    for line in lines:
                        if "10000" in line or "1.71" in line or "3.97" in line:
                            print(f"LIGNE: {line}")
                print("--- FIN TEXTE BRUT ---")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_mammafiore()
