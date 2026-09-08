
import requests
import os
import json

# URLs des fichiers fournis par l'utilisateur
files = [
    {"name": "Facture_1.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/jtxmilwc_PXL_20251205_152227061.jpg"},
    {"name": "Facture_2.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/36m8hn9u_PXL_20251205_152635620.jpg"},
    {"name": "Facture_3.jpg", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/i8s5km18_PXL_20251205_152140006.jpg"}
]

API_URL = "http://localhost:8001/api"

def run_test():
    print("🚀 DÉMARRAGE DU CRASH TEST OCR - FICHIERS RÉELS")
    print("------------------------------------------------")

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
                
                doc_id = upload_res.json()['id']
                print(f"✅ Upload réussi (ID: {doc_id})")
                
                # 3. Analyse (Simulation de l'ouverture du Modal de Validation)
                analyze_res = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                
                if analyze_res.status_code != 200:
                    print(f"❌ Erreur Analyse: {analyze_res.text}")
                    continue
                
                analysis = analyze_res.json()
                
                # 4. Affichage des résultats
                print(f"   🏢 Fournisseur détecté : {analysis.get('supplier_name')}")
                print(f"   📅 Date détectée       : {analysis.get('facture_date')}")
                print(f"   📄 N° Facture          : {analysis.get('numero_facture')}")
                print(f"   📦 Produits trouvés    : {len(analysis.get('items', []))}")
                
                print("   --- Détail des 3 premiers produits ---")
                for item in analysis.get('items', [])[:3]:
                    status_icon = "✅" if item['status'] == 'matched' else "🆕"
                    print(f"   {status_icon} Lu: '{item['ocr_name']}' -> Qté: {item['ocr_qty']} | Prix: {item['ocr_price']}€")

        except Exception as e:
            print(f"❌ Exception traitement: {e}")

if __name__ == "__main__":
    run_test()
