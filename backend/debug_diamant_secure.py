
import requests
import os
import json

files = [
    {"name": "Diamant_Real.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/zn4di4zw_PXL_20251208_144254372.jpg"}
]

API_URL = "http://localhost:8001/api"

def debug_diamant_secure():
    print("🚀 DEBUG SÉCURISÉ - DIAMANT")
    
    for file_info in files:
        try:
            # Download
            r = requests.get(file_info['url'])
            path = f"/tmp/{file_info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            # Upload
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (file_info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                print(f"Upload Status: {res.status_code}")
                data = res.json()
                print(f"JSON Response: {json.dumps(data, indent=2)[:500]}...") # Affiche le début du JSON
                
                # Gestion robuste de l'ID
                doc_id = data.get('document_id') or data.get('id')
                if not doc_id and 'document_ids' in data and len(data['document_ids']) > 0:
                    doc_id = data['document_ids'][0]
                
                print(f"Doc ID: {doc_id}")
                
                if doc_id:
                    # Analyze
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    print(f"   🏢 Fournisseur : {analysis.get('supplier_name')}")
                    print(f"   📦 Produits : {len(analysis.get('items', []))}")
                    
                    # Affichage Brut si vide
                    if len(analysis.get('items', [])) == 0:
                        print("\n--- TEXTE BRUT ---")
                        if 'texte_extrait' in data:
                            lines = data['texte_extrait'].split('\n')
                            for line in lines:
                                if any(c.isdigit() for c in line) and len(line) > 10:
                                    print(f"L: {line.strip()}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    debug_diamant_secure()
