
import requests
import os
import json

files = [
    {"name": "Mamma_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nc0hqxeh_PXL_20251205_184115055.jpg"},
    {"name": "Mamma_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/fszj1xrd_PXL_20251205_184134943.MP.jpg"},
    {"name": "Mamma_3.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/tk485eeb_PXL_20251205_184303249.jpg"}
]

API_URL = "http://localhost:8001/api"

def test_mammafiore():
    print("🚀 TEST FINAL MAMMAFIORE - STRATÉGIE COLONNE")
    
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
                doc_id = None
                if 'document_id' in data: doc_id = data['document_id']
                elif 'id' in data: doc_id = data['id']
                elif 'document_ids' in data: doc_id = data['document_ids'][0]
                
                print(f"✅ ID: {doc_id}")
                
                # Analyze
                res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                analysis = res_ana.json()
                
                print(f"   📦 Produits trouvés: {len(analysis.get('items', []))}")
                for item in analysis.get('items', []):
                    print(f"   👉 {item['ocr_name']} (Qté: {item['ocr_qty']} | Prix: {item['ocr_price']})")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    test_mammafiore()
