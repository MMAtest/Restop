
import requests
import os
import json

# Les 4 factures qui posent problème
files = [
    {"name": "TerreAzur.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/5o60p7ai_PXL_20251205_152542601.jpg"},
    {"name": "Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/pxz5xqc6_PXL_20251205_152614973.jpg"},
    {"name": "Royaume.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/i8s5km18_PXL_20251205_152140006.jpg"},
    {"name": "PrestHyg.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jtxmilwc_PXL_20251205_152227061.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_raw_failures():
    print("🚀 DEBUG RAW TEXT - LES 4 FANTASTIQUES")
    
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
                print("--- EXTRAIT PERTINENT ---")
                if 'texte_extrait' in data:
                    lines = data['texte_extrait'].split('\n')
                    # On affiche les lignes qui contiennent des chiffres et du texte (candidats produits)
                    count = 0
                    for line in lines:
                        line = line.strip()
                        # Filtre simple pour montrer les lignes "produits potentiels"
                        if len(line) > 10 and any(c.isdigit() for c in line):
                            # On ignore les dates et SIRET pour la lisibilité du log
                            if "2025" not in line and "SIRET" not in line:
                                print(f"LIGNE: {line}")
                                count += 1
                                if count > 15: break # On limite à 15 lignes pour ne pas spammer
                print("-------------------------")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_raw_failures()
