
import requests
import os
import json

# Les 5 nouvelles factures
files = [
    {"name": "Facture_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/zxm4y92b_PXL_20251208_144534235.jpg"},
    {"name": "Facture_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/vfkhe3nf_PXL_20251208_144541179.jpg"},
    {"name": "Facture_3.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/vjg13pgt_PXL_20251208_144557942.jpg"},
    {"name": "Facture_4.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/2uottd06_PXL_20251208_144553549.MP.jpg"},
    {"name": "Facture_5.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/yf5ltps8_PXL_20251208_144547015.MP.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_batch_test():
    print("📋 TEST BATCH 5 FACTURES")
    print("========================")

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
                # Gestion multi-factures
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
    run_batch_test()
