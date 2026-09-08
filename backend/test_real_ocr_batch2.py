
import requests
import os
import json

# URLs des nouveaux fichiers fournis par l'utilisateur
files = [
    {"name": "Facture_4.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/pxz5xqc6_PXL_20251205_152614973.jpg"},
    {"name": "Facture_5.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/lfbmmkx6_PXL_20251205_152553937.jpg"},
    {"name": "Facture_6.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/5o60p7ai_PXL_20251205_152542601.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_test():
    print("🚀 DÉMARRAGE DU CRASH TEST OCR - BATCH 2")
    print("---------------------------------------")

    for file_info in files:
        print(f"\n📸 Traitement de : {file_info['name']}...")
        
        # 1. Téléchargement
        try:
            response = requests.get(file_info['url'])
            if response.status_code != 200:
                print("❌ Erreur téléchargement")
                continue
                
            file_path = f"/tmp/{file_info['name']}"
            with open(file_path, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            print(f"❌ Exception téléchargement: {e}")
            continue

        # 2. Upload OCR
        try:
            with open(file_path, 'rb') as f:
                files_data = {'file': (file_info['name'], f, 'image/jpeg')}
                data = {'document_type': 'facture_fournisseur'}
                
                upload_res = requests.post(f"{API_URL}/ocr/upload-document", files=files_data, data=data)
                
                if upload_res.status_code != 200:
                    print(f"❌ Erreur Upload: {upload_res.text}")
                    continue
                
                response_json = upload_res.json()
                
                doc_id = None
                if 'document_id' in response_json:
                    doc_id = response_json['document_id']
                elif 'id' in response_json:
                    doc_id = response_json['id']
                elif 'document_ids' in response_json and len(response_json['document_ids']) > 0:
                    doc_id = response_json['document_ids'][0]
                
                if not doc_id:
                    print("❌ Pas d'ID retourné")
                    continue

                print(f"✅ Upload réussi (ID: {doc_id})")
                
                # 3. Analyse
                analyze_res = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                
                if analyze_res.status_code != 200:
                    print(f"❌ Erreur Analyse: {analyze_res.text}")
                    continue
                
                analysis = analyze_res.json()
                
                # 4. Affichage des résultats
                print(f"   ---------------------------------------------------")
                print(f"   🏢 Fournisseur : {analysis.get('supplier_name')}")
                print(f"   📅 Date        : {analysis.get('facture_date')}")
                print(f"   📄 N° Facture  : {analysis.get('numero_facture')}")
                print(f"   📦 Produits    : {len(analysis.get('items', []))}")
                print(f"   ---------------------------------------------------")
                
                if len(analysis.get('items', [])) > 0:
                    for item in analysis.get('items', [])[:5]:
                        status_icon = "✅" if item['status'] == 'matched' else "🆕"
                        print(f"   {status_icon} {item['ocr_name']} | {item['ocr_qty']} {item['ocr_unit']} | {item['ocr_price']}€")
                else:
                    print("   ⚠️ Aucun produit structuré détecté.")
                    # Afficher un extrait pour voir si le texte est lisible
                    if 'texte_extrait' in response_json:
                         print(f"   📝 Texte lu (extrait): {response_json['texte_extrait'][:100]}...")

        except Exception as e:
            print(f"❌ Exception traitement: {e}")

if __name__ == "__main__":
    run_test()
