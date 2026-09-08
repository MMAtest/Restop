
import requests
import os
import json

files = [
    {"name": "Diamant.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/h7gmpj1a_Screenshot_20251208-230901.png"}
]

API_URL = "http://localhost:8001/api"

def debug_diamant():
    print("🚀 DEBUG RAW TEXT - LE DIAMANT DU TERROIR")
    
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
                print("--- TEXTE EXTRAIT ---")
                if 'texte_extrait' in data:
                    lines = data['texte_extrait'].split('\n')
                    for line in lines:
                        # On affiche tout pour voir la structure
                        if line.strip():
                            print(f"L: {line.strip()}")
                print("---------------------")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_diamant()
