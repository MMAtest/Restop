
import requests
import os
import json

files = [
    {"name": "TerreAzur_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/7qzrl1gi_PXL_20251205_195145748.jpg"},
    {"name": "TerreAzur_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/lugwodxn_PXL_20251205_195139458.jpg"},
    {"name": "Royaume_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/13regqta_PXL_20251205_195210388.jpg"},
    {"name": "Royaume_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nj75akry_PXL_20251205_195201647.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_raw_optimization():
    print("🚀 DEBUG RAW TEXT - OPTIMISATION FINALE")
    
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
                print("--- EXTRAIT (Lignes avec chiffres) ---")
                if 'texte_extrait' in data:
                    lines = data['texte_extrait'].split('\n')
                    count = 0
                    for line in lines:
                        line = line.strip()
                        # Filtre pour afficher les lignes de produits probables
                        # On cherche des lignes avec des chiffres ET du texte
                        if len(line) > 10 and any(c.isdigit() for c in line):
                            # TerreAzur: code 6 chiffres (113151, 219981...)
                            # Royaume: "Lot:", "PALOURDE", "SEICHE"
                            if any(k in line.upper() for k in ["113151", "219981", "293598", "101624", "SEICHE", "PALOURDE", "LOT:", "3,99"]):
                                print(f"LIGNE CIBLE: {line}")
                print("------------------------------")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_raw_optimization()
