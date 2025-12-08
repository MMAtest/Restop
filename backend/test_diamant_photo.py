
import requests
import os
import json

files = [
    {"name": "Diamant_Real.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/zn4di4zw_PXL_20251208_144254372.jpg"}
]

API_URL = "http://localhost:8001/api"

def test_diamant_photo():
    print("🚀 TEST RÉEL - DIAMANT DU TERROIR (PHOTO)")
    
    for file_info in files:
        try:
            # Download
            r = requests.get(file_info['url'])
            path = f"/tmp/{file_info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            # Upload
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (file_info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                data = res.json()
                doc_id = data.get('document_id') or data.get('id') or data.get('document_ids')[0]
                
                # Analyze
                res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                analysis = res_ana.json()
                
                print(f"   🏢 Fournisseur : {analysis.get('supplier_name')}")
                print(f"   📅 Date        : {analysis.get('facture_date')}")
                print(f"   📦 Produits    : {len(analysis.get('items', []))}")
                
                if len(analysis.get('items', [])) > 0:
                    for item in analysis.get('items', []):
                        print(f"   💎 {item['ocr_name']} (Qté: {item['ocr_qty']} {item['ocr_unit']} | Prix: {item['ocr_price']}€)")
                else:
                    # Si échec, on regarde le brut pour calibrer
                    print("   ⚠️ Aucun produit. Extrait brut:")
                    if 'texte_extrait' in data:
                        print(data['texte_extrait'][:500])
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    test_diamant_photo()
