
import requests
import os
import json

files = [
    {"name": "Metro_Bold.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/brcpgfch_PXL_20251208_144911291.jpg"},
    {"name": "RM_Maree.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/apedw6i3_PXL_20251208_144857702.jpg"}
]

API_URL = "http://localhost:8001/api"

def check_bold():
    print("🚀 TEST FACTURES ET QUESTION GRAS")
    print("=================================")

    for info in files:
        print(f"\n🔍 Analyse : {info['name']}")
        try:
            r = requests.get(info['url'])
            path = f"/tmp/{info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            res = requests.post(f"{API_URL}/ocr/upload-document", 
                              files={'file': (info['name'], f, 'image/jpeg')},
                              data={'document_type': 'facture_fournisseur'})
            
            data = res.json()
            doc_id = data.get('document_id') or data.get('id')
            if not doc_id and data.get('document_ids'): doc_id = data['document_ids'][0]
            
            if doc_id:
                res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                analysis = res_ana.json()
                
                print(f"   🏢 Détecté : {analysis.get('supplier_name')}")
                print(f"   📦 Produits: {len(analysis.get('items', []))} lignes")
                
                if len(analysis.get('items', [])) > 0:
                    for item in analysis.get('items', []):
                        print(f"      - {item['ocr_name'][:40]}... | Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€")
                else:
                    print("   ❌ VIDE")
                    if 'texte_extrait' in data:
                        print(f"   Extrait brut: {data['texte_extrait'][:300]}")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    check_bold()
