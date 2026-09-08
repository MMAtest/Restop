
import requests
import os
import json

# Les 5 nouvelles factures (Batch 4)
files = [
    {"name": "Facture_16.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/zsfcleqh_PXL_20251208_145043130.jpg"},
    {"name": "Facture_17.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/n7urr4qk_PXL_20251208_144924356.jpg"},
    {"name": "Facture_18.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jewkp47e_PXL_20251208_145059020.jpg"},
    {"name": "Facture_19.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/cvjph4it_PXL_20251208_144946448.jpg"},
    {"name": "Facture_20.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/28nce0q2_PXL_20251208_144911291.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_batch_test_4():
    print("📋 TEST BATCH 4 (5 NOUVELLES FACTURES)")
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
                    print(f"   📅 Date    : {analysis.get('facture_date')}")
                    print(f"   📦 Produits: {len(analysis.get('items', []))} lignes")
                    
                    if len(analysis.get('items', [])) > 0:
                        print("   📝 Détail complet:")
                        for item in analysis.get('items', []):
                            # Affichage plus large pour bien voir les noms
                            print(f"      - {item['ocr_name'][:50]}... | Qté: {item['ocr_qty']} | Prix U: {item['ocr_price']}€")
                    else:
                        print("   ❌ AUCUN PRODUIT DÉTECTÉ")
                else:
                    print("   ❌ Échec Upload (Pas d'ID)")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    run_batch_test_4()
