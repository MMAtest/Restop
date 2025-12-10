
import requests
import os
import json

# Les 6 nouvelles factures pour test final
files = [
    {"name": "Test_Final_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nxzzc7fu_PXL_20251205_184115055.jpg"},
    {"name": "Test_Final_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/1zu5x1g8_PXL_20251205_184115055.jpg"},
    {"name": "Test_Final_3.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/72ibu7x3_PXL_20251205_152227061.jpg"},
    {"name": "Test_Final_4.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/7e4umf23_PXL_20251205_152140006.jpg"},
    {"name": "Test_Final_5.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/h9wiq00z_PXL_20251205_152542601.jpg"},
    {"name": "Test_Final_6.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/8zvakan7_PXL_20251205_152127913.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_test_final_verification():
    print("📋 TEST BATCH FINAL - VERIFICATION GLOBALE")
    print("=========================================")

    for info in files:
        print(f"\n🔍 Analyse : {info['name']}")
        try:
            # 1. Download
            r = requests.get(info['url'])
            if r.status_code != 200:
                print(f"   ❌ Erreur téléchargement: {r.status_code}")
                continue
                
            path = f"/tmp/{info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            # 2. Upload
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                if res.status_code != 200:
                    print(f"   ❌ Erreur Upload: {res.status_code}")
                    try: print(res.json())
                    except: pass
                    continue

                data = res.json()
                doc_id = data.get('document_id') or data.get('id')
                if not doc_id and data.get('document_ids'):
                    doc_id = data['document_ids'][0]
                
                if doc_id:
                    # 3. Analyze
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    if res_ana.status_code != 200:
                        print(f"   ❌ Erreur Analyse: {res_ana.status_code}")
                        continue
                        
                    analysis = res_ana.json()
                    
                    print(f"   🏢 Détecté : {analysis.get('supplier_name')}")
                    print(f"   📅 Date    : {analysis.get('facture_date')}")
                    items = analysis.get('items', [])
                    print(f"   📦 Produits: {len(items)} lignes")
                    
                    if len(items) > 0:
                        print("   📝 Détail (Top 5):")
                        for item in items[:5]:
                            # Clean name for display
                            name = item['ocr_name'].replace('\n', ' ')
                            if len(name) > 40: name = name[:37] + "..."
                            print(f"      - {name} | Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€")
                    else:
                        print("   ❌ AUCUN PRODUIT DÉTECTÉ")
                else:
                    print("   ❌ Échec Upload (Pas d'ID)")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    run_test_final_verification()
