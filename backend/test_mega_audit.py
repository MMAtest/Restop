
import requests
import os
import json

# LISTE COMPLÈTE DES 20 FACTURES
# J'ai repris les URLs de tous les batches précédents
all_files = [
    # BATCH 1 (3 factures)
    {"name": "F01_PrestHyg.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jtxmilwc_PXL_20251205_152227061.jpg"},
    {"name": "F02_Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/36m8hn9u_PXL_20251205_152635620.jpg"},
    {"name": "F03_Royaume.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/i8s5km18_PXL_20251205_152140006.jpg"},
    
    # BATCH 2 (3 factures)
    {"name": "F04_Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/pxz5xqc6_PXL_20251205_152614973.jpg"},
    {"name": "F05_Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/lfbmmkx6_PXL_20251205_152553937.jpg"},
    {"name": "F06_TerreAzur.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/5o60p7ai_PXL_20251205_152542601.jpg"},
    
    # BATCH 3 (2 factures)
    {"name": "F07_Metro.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/3bknadcg_PXL_20251205_163403178.jpg"},
    {"name": "F08_Mamma.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jo6u9n8q_PXL_20251205_163348741.jpg"},
    
    # BATCH 4 (3 factures Mammafiore)
    {"name": "F09_Mamma.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nc0hqxeh_PXL_20251205_184115055.jpg"},
    {"name": "F10_Mamma.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/fszj1xrd_PXL_20251205_184134943.MP.jpg"},
    {"name": "F11_Mamma.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/tk485eeb_PXL_20251205_184303249.jpg"},
    
    # BATCH 5 (1 facture Diamant - Photo réelle)
    {"name": "F12_Diamant.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/zn4di4zw_PXL_20251208_144254372.jpg"},
    
    # BATCH 6 (4 factures TerreAzur & co)
    {"name": "F13_TerreAzur.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/7qzrl1gi_PXL_20251205_195145748.jpg"},
    {"name": "F14_TerreAzur.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/lugwodxn_PXL_20251205_195139458.jpg"},
    {"name": "F15_Royaume.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/13regqta_PXL_20251205_195210388.jpg"},
    {"name": "F16_Royaume.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nj75akry_PXL_20251205_195201647.jpg"},
    
    # BATCH 7 (4 dernières factures)
    {"name": "F17_Metro.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nq4nkl1i_PXL_20251208_144517676.jpg"},
    {"name": "F18_Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nqb5ycvi_PXL_20251208_144528773.jpg"},
    {"name": "F19_PrestHyg.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/co5bksnk_PXL_20251208_144451670.jpg"},
    {"name": "F20_Diamant.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/2wbfisvp_PXL_20251208_144254372.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_mega_audit():
    print("📋 AUDIT COMPLET 20 FACTURES")
    print("============================")

    for info in all_files:
        print(f"\n🔍 {info['name']}")
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
                
                data = res.json()
                doc_id = data.get('document_id') or data.get('id')
                if not doc_id and data.get('document_ids'):
                    doc_id = data['document_ids'][0]
                
                if doc_id:
                    # 3. Analyze
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    supplier = analysis.get('supplier_name')
                    items = analysis.get('items', [])
                    
                    print(f"   🏢 {supplier}")
                    print(f"   📦 {len(items)} produits")
                    
                    if items:
                        for item in items:
                            # Affichage compact
                            clean_name = item['ocr_name'].replace('\n', ' ').strip()[:50]
                            print(f"      • {clean_name}")
                    else:
                        print("      ❌ VIDE")
                else:
                    print("      ❌ ERREUR UPLOAD")

        except Exception as e:
            print(f"      ❌ ERREUR: {e}")

if __name__ == "__main__":
    run_mega_audit()
