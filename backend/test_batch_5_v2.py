
import requests
import os
import json

# Les 5 nouvelles factures
files = [
    {"name": "Facture_6.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/y1ot7yx9_PXL_20251208_144629317.jpg"},
    {"name": "Facture_7.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/xlid8425_PXL_20251208_144602363.MP.jpg"},
    {"name": "Facture_8.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/7k51zhn3_PXL_20251208_144620031.jpg"},
    {"name": "Facture_9.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/ynojol6u_PXL_20251208_144614486.jpg"},
    {"name": "Facture_10.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/gfl1yxdh_PXL_20251208_144608474.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_batch_test_2():
    print("📋 TEST BATCH 2 (5 FACTURES)")
    print("============================")

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
                    print(f"   📅 Date    : {analysis.get('facture_date')}")
                    print(f"   📦 Produits: {len(analysis.get('items', []))} lignes")
                    
                    if len(analysis.get('items', [])) > 0:
                        print("   📝 Détail (Top 5):")
                        for item in analysis.get('items', [])[:5]:
                            print(f"      - {item['ocr_name'][:40]}... | Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€")
                    else:
                        print("   ❌ AUCUN PRODUIT DÉTECTÉ")
                else:
                    print("   ❌ Échec Upload (Pas d'ID)")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    run_batch_test_2()
