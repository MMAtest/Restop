
import requests
import os
import json

# Les 4 factures à vérifier
files = [
    {"supplier": "METRO", "name": "Check_Metro.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nq4nkl1i_PXL_20251208_144517676.jpg"},
    {"supplier": "GFD LERDA", "name": "Check_Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nqb5ycvi_PXL_20251208_144528773.jpg"},
    {"supplier": "PREST'HYG", "name": "Check_PrestHyg.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/co5bksnk_PXL_20251208_144451670.jpg"},
    {"supplier": "DIAMANT", "name": "Check_Diamant.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/2wbfisvp_PXL_20251208_144254372.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_verification():
    print("📋 VÉRIFICATION FINALE DES 4 FOURNISSEURS")
    print("=========================================")

    for info in files:
        print(f"\n🔍 Analyse : {info['supplier']}")
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
                doc_id = data.get('document_id') or data.get('id') or (data.get('document_ids')[0] if data.get('document_ids') else None)
                
                if doc_id:
                    # 3. Analyze
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    print(f"   🏢 Détecté : {analysis.get('supplier_name')}")
                    print(f"   📅 Date    : {analysis.get('facture_date')}")
                    print(f"   📦 Produits: {len(analysis.get('items', []))} lignes")
                    
                    # Détail des produits pour vérifier la qualité
                    if len(analysis.get('items', [])) > 0:
                        print("   📝 Détail (Top 3):")
                        for item in analysis.get('items', [])[:3]:
                            print(f"      - {item['ocr_name']} | Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€")
                    else:
                        print("   ❌ AUCUN PRODUIT DÉTECTÉ")
                else:
                    print("   ❌ Échec Upload (Pas d'ID)")

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    run_verification()
