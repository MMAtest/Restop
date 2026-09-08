
import requests
import os

files = [
    {"name": "Diamant_Final_Check.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/4jyhgxc5_PXL_20251208_144254372.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_diamant_lines():
    print("🚀 SCAN BRUT DIAMANT")
    for file_info in files:
        r = requests.get(file_info['url'])
        with open(f"/tmp/{file_info['name']}", 'wb') as f: f.write(r.content)
        with open(f"/tmp/{file_info['name']}", 'rb') as f:
            res = requests.post(f"{API_URL}/ocr/upload-document", 
                              files={'file': (file_info['name'], f, 'image/jpeg')},
                              data={'document_type': 'facture_fournisseur'})
            data = res.json()
            if 'texte_extrait' in data:
                lines = data['texte_extrait'].split('\n')
                for i, line in enumerate(lines):
                    # On affiche TOUT ce qui contient des chiffres et des lettres
                    if len(line) > 5 and any(c.isdigit() for c in line) and any(c.isalpha() for c in line):
                        print(f"[{i}] {line}")

if __name__ == "__main__":
    debug_diamant_lines()
