
import requests
import os

files = [
    {"name": "Check_PrestHyg.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/co5bksnk_PXL_20251208_144451670.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_presthyg_raw():
    print("🚀 DEBUG RAW PREST'HYG")
    for file_info in files:
        r = requests.get(file_info['url'])
        with open(f"/tmp/{file_info['name']}", 'wb') as f: f.write(r.content)
        with open(f"/tmp/{file_info['name']}", 'rb') as f:
            res = requests.post(f"{API_URL}/ocr/upload-document", 
                              files={'file': (file_info['name'], f, 'image/jpeg')},
                              data={'document_type': 'facture_fournisseur'})
            data = res.json()
            if 'texte_extrait' in data:
                print(data['texte_extrait'])

if __name__ == "__main__":
    debug_presthyg_raw()
