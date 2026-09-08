
import requests
import os
import json

# Les 5 nouvelles factures (Batch 3)
files = [
    {"name": "Facture_11.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/1toporwr_PXL_20251208_144719431.jpg"},
    {"name": "Facture_12.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/16bto7qy_PXL_20251208_144705676.jpg"},
    {"name": "Facture_13.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/43bew36x_PXL_20251208_144644840.jpg"},
    {"name": "Facture_14.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/rje1xc9h_PXL_20251208_144639580.jpg"},
    {"name": "Facture_15.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/u9reoshr_PXL_20251208_144708962.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_batch_test_3():
    print("📋 TEST BATCH 3 (5 NOUVELLES FACTURES)")
    print("======================================")

    for info in files:
        print(f"\n🔍 Analyse : {info['name']}")
        try:
            # 1. Download
            r = requests.get(info['url'])
            path = f"/tmp/{info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            # 2. Upload
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                if res.status_code != 200:
                    print(f"   ❌ Erreur Upload: {res.status_code}")
                    continue

                data = res.json()
                doc_id = data.get('document_id') or data.get('id')
                if not doc_id and data.get('document_ids'):
                    doc_id = data['document_ids'][0]
                
                if doc_id:
                    # 3. Analyze
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    print(f"   🏢 Détecté : {analysis.get('supplier_name')}")
                    print(f"   📦 Produits: {len(analysis.get('items', []))} lignes")
                    
                    if len(analysis.get('items', [])) > 0:
                        print("   📝 Détail complet:")
                        for item in analysis.get('items', []):
                            print(f"      - {item['ocr_name'][:60]} | Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€")
                    else:
                        print("   ❌ AUCUN PRODUIT DÉTECTÉ")
                else:
                    print("   ❌ Échec Upload (Pas d'ID)")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    run_batch_test_3()
