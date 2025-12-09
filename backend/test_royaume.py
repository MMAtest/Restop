
import requests
import os
import json

# Les 2 factures Royaume des Mers
files = [
    {"name": "Royaume_Check_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/d9z2re5f_PXL_20251208_144639580.jpg"},
    {"name": "Royaume_Check_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/yxdy4abq_PXL_20251208_144946448.jpg"}
]

API_URL = "http://localhost:8001/api"

def check_royaume():
    print("🚀 VÉRIFICATION ROYAUME DES MERS (FIX)")
    print("======================================")

    for info in files:
        print(f"\n🔍 Analyse : {info['name']}")
        try:
            # 1. Download
            r = requests.get(info['url'])
            path = f"/tmp/{info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            # 2. Upload (Ouverture propre)
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                data = res.json()
                doc_id = data.get('document_id') or data.get('id')
                if not doc_id and data.get('document_ids'):
                    doc_id = data['document_ids'][0]
                
                if doc_id:
                    # 3. Analyze
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    print(f"   🏢 Détecté : {analysis.get('supplier_name')}")
                    
                    if len(analysis.get('items', [])) > 0:
                        for item in analysis.get('items', []):
                            print(f"      - {item['ocr_name'][:40]}... | Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€ | Total: {item['ocr_total']}€")
                    else:
                        print("   ❌ VIDE")
                        if 'texte_extrait' in data:
                            print(f"   Debug brut: {data['texte_extrait'][:200]}...")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    check_royaume()
