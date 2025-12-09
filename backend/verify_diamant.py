
import requests
import os
import json

# L'image fournie par l'utilisateur
files = [
    {"name": "Diamant_Final_Check.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/4jyhgxc5_PXL_20251208_144254372.jpg"}
]

API_URL = "http://localhost:8001/api"

def check_diamant():
    print("🚀 VÉRIFICATION ULTIME - DIAMANT DU TERROIR")
    
    for file_info in files:
        try:
            # 1. Download
            r = requests.get(file_info['url'])
            path = f"/tmp/{file_info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            # 2. Upload
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (file_info['name'], f, 'image/jpeg')},
                                  data={'document_type': 'facture_fournisseur'})
                
                data = res.json()
                # Gestion ID robuste (cas multi ou single)
                doc_id = data.get('document_id') or data.get('id')
                if not doc_id and data.get('document_ids'):
                    doc_id = data['document_ids'][0]
                
                if doc_id:
                    print(f"✅ Upload OK (ID: {doc_id})")
                    
                    # 3. Analyse
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    print(f"   🏢 Fournisseur : {analysis.get('supplier_name')}")
                    print(f"   📅 Date        : {analysis.get('facture_date')}")
                    print(f"   📦 Produits    : {len(analysis.get('items', []))}")
                    
                    if len(analysis.get('items', [])) > 0:
                        print("\n   --- DÉTAIL DES PRODUITS ---")
                        for item in analysis.get('items', []):
                            print(f"   💎 {item['ocr_name']}")
                            print(f"      Qté: {item['ocr_qty']} {item['ocr_unit']} | Prix U: {item['ocr_price']}€ | Total: {item['ocr_total']}€")
                    else:
                        print("   ❌ Aucun produit trouvé.")
                        if 'texte_extrait' in data:
                            print("   📝 Extrait texte brut:")
                            lines = data['texte_extrait'].split('\n')
                            for line in lines:
                                if "TRUFFE" in line or "GNOCCHI" in line:
                                    print(f"      LIGNE CIBLE: {line}")

                else:
                    print(f"❌ Erreur Upload (Pas d'ID): {data}")

        except Exception as e:
            print(f"Erreur technique: {e}")

if __name__ == "__main__":
    check_diamant()
