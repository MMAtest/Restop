
import requests
import os
import json

# Un fichier représentatif par fournisseur
files = [
    {"supplier": "METRO", "name": "Audit_Metro.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/3bknadcg_PXL_20251205_163403178.jpg"},
    {"supplier": "MAMMAFIORE", "name": "Audit_Mamma.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/nc0hqxeh_PXL_20251205_184115055.jpg"},
    {"supplier": "TERREAZUR", "name": "Audit_TerreAzur.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/5o60p7ai_PXL_20251205_152542601.jpg"},
    {"supplier": "GFD LERDA", "name": "Audit_Lerda.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/pxz5xqc6_PXL_20251205_152614973.jpg"},
    {"supplier": "ROYAUME DES MERS", "name": "Audit_Royaume.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/i8s5km18_PXL_20251205_152140006.jpg"},
    {"supplier": "PREST'HYG", "name": "Audit_PrestHyg.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jtxmilwc_PXL_20251205_152227061.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_audit():
    print("📋 AUDIT FINAL - ÉTAT DES LIEUX DES 6 FOURNISSEURS")
    print("===================================================")

    for info in files:
        print(f"\n🔍 Test : {info['supplier']}")
        try:
            # Download
            r = requests.get(info['url'])
            path = f"/tmp/{info['name']}"
            with open(path, 'wb') as f:
                f.write(r.content)
                
            # Upload & Analyze
            with open(path, 'rb') as f:
                res_up = requests.post(f"{API_URL}/ocr/upload-document", 
                                     files={'file': (info['name'], f, 'image/jpeg')},
                                     data={'document_type': 'facture_fournisseur'})
                
                data_up = res_up.json()
                doc_id = data_up.get('document_id') or data_up.get('id')
                
                if not doc_id and 'document_ids' in data_up:
                    doc_id = data_up['document_ids'][0]
                
                if doc_id:
                    res_ana = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                    analysis = res_ana.json()
                    
                    # Scoring
                    nom_ok = "✅" if analysis.get('supplier_name') != "Fournisseur inconnu" else "❌"
                    date_ok = "✅" if analysis.get('facture_date') else "❌"
                    nb_prods = len(analysis.get('items', []))
                    prod_ok = "✅" if nb_prods > 0 else "⚠️"
                    
                    print(f"   > ID Fournisseur : {nom_ok} ({analysis.get('supplier_name')})")
                    print(f"   > Date Facture   : {date_ok} ({analysis.get('facture_date')})")
                    print(f"   > Produits       : {prod_ok} ({nb_prods} lignes détectées)")
                    
                    if nb_prods > 0:
                        print(f"   > Exemple        : {analysis['items'][0]['ocr_name']} ({analysis['items'][0]['ocr_price']}€)")
                else:
                    print("   ❌ Erreur technique (Upload failed)")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    run_audit()
