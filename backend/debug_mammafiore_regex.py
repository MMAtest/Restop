
import requests
import os
import json

files = [
    {"name": "Mamma_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nc0hqxeh_PXL_20251205_184115055.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_mammafiore_regex():
    print("🚀 DEBUG MAMMAFIORE REGEX")
    
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
                print("--- ANALYSE LIGNE PAR LIGNE ---")
                if 'texte_extrait' in data:
                    lines = data['texte_extrait'].split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        # Test de ma regex actuelle
                        import re
                        match = re.search(r'(10\d{8,9})', line)
                        
                        if "10000" in line:
                            print(f"[{i}] BRUT: '{line}'")
                            if match:
                                print(f"    ✅ MATCH: {match.group(1)}")
                            else:
                                print(f"    ❌ NO MATCH avec r'(10\d{{8,9}})'")
                                
                print("--- FIN ANALYSE ---")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_mammafiore_regex()
