
import requests
import os
import json

# La nouvelle facture TerreAzur fournie
files = [
    {"name": "TerreAzur_New.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/7qzrl1gi_PXL_20251205_195145748.jpg"}
]

API_URL = "http://localhost:8001/api"

def test_terreazur_full():
    print("🚀 TEST CIBLÉ TERREAZUR - NOUVEAU FICHIER")
    
    for file_info in files:
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
                doc_id = data.get('document_id') or data.get('id') or data.get('document_ids')[0]
                
                # Analyze
                res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                analysis = res_ana.json()
                
                print(f"   📦 Produits trouvés : {len(analysis.get('items', []))}")
                for item in analysis.get('items', []):
                    print(f"   ✅ {item['ocr_name']} (Qté: {item['ocr_qty']} | Prix: {item['ocr_price']})")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    test_terreazur_full()
