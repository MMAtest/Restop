
import requests
import os
import json

# URLs des nouveaux fichiers (Batch 3)
files = [
    {"name": "Facture_7.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/3bknadcg_PXL_20251205_163403178.jpg"},
    {"name": "Facture_8.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jo6u9n8q_PXL_20251205_163348741.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_test():
    print("🚀 DÉMARRAGE DU CRASH TEST OCR - BATCH 3 (METRO/MAMMAFIORE)")
    print("-----------------------------------------------------------")

    for file_info in files:
        print(f"\n📸 Traitement de : {file_info['name']}...")
        
        try:
            response = requests.get(file_info['url'])
            file_path = f"/tmp/{file_info['name']}"
            with open(file_path, 'wb') as f:
                f.write(response.content)
        except:
            print("❌ Erreur download")
            continue

        try:
            with open(file_path, 'rb') as f:
                files_data = {'file': (file_info['name'], f, 'image/jpeg')}
                data = {'document_type': 'facture_fournisseur'}
                
                upload_res = requests.post(f"{API_URL}/ocr/upload-document", files=files_data, data=data)
                response_json = upload_res.json()
                
                doc_id = None
                if 'document_id' in response_json: doc_id = response_json['document_id']
                elif 'id' in response_json: doc_id = response_json['id']
                elif 'document_ids' in response_json: doc_id = response_json['document_ids'][0]
                
                if not doc_id:
                    print("❌ Pas d'ID")
                    continue

                print(f"✅ Upload réussi (ID: {doc_id})")
                
                analyze_res = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                analysis = analyze_res.json()
                
                print(f"   ---------------------------------------------------")
                print(f"   🏢 Fournisseur : {analysis.get('supplier_name')}")
                print(f"   📅 Date        : {analysis.get('facture_date')}")
                print(f"   📦 Produits    : {len(analysis.get('items', []))}")
                print(f"   ---------------------------------------------------")
                
                if len(analysis.get('items', [])) > 0:
                    for item in analysis.get('items', [])[:5]:
                        print(f"   ✅ {item['ocr_name']} | {item['ocr_qty']} | {item['ocr_price']}€")
                else:
                    print("   ⚠️ Aucun produit détecté.")
                    if 'texte_extrait' in response_json:
                         print(f"   📝 Extrait: {response_json['texte_extrait'][:100]}...")

        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    run_test()
