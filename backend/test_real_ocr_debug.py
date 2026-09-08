
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
    print("🚀 DÉMARRAGE DU CRASH TEST OCR (DEBUG) - FICHIERS RÉELS")
    print("-------------------------------------------------------")

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
                
                print("   Envoi au serveur...")
                upload_res = requests.post(f"{API_URL}/ocr/upload-document", files=files_data, data=data)
                
                print(f"   Status Code: {upload_res.status_code}")
                try:
                    response_json = upload_res.json()
                    # print(f"   Response: {json.dumps(response_json, indent=2)}") # Trop verbeux si base64
                except:
                    print(f"   Raw Response: {upload_res.text[:200]}...")
                
                if upload_res.status_code != 200:
                    print(f"❌ Erreur Upload: {upload_res.text}")
                    continue
                
                # Gestion de la réponse multi-factures ou simple
                doc_id = None
                if 'id' in response_json:
                    doc_id = response_json['id']
                elif 'document_ids' in response_json and len(response_json['document_ids']) > 0:
                    doc_id = response_json['document_ids'][0] # On prend le premier
                    print(f"   ℹ️ Multi-factures détecté, analyse du premier doc.")
                else:
                    print(f"❌ Pas d'ID trouvé dans la réponse")
                    continue

                print(f"✅ Upload réussi (ID: {doc_id})")
                
                # 3. Analyse (Simulation de l'ouverture du Modal de Validation)
                analyze_res = requests.post(f"{API_URL}/ocr/analyze-facture/{doc_id}")
                
                if analyze_res.status_code != 200:
                    print(f"❌ Erreur Analyse: {analyze_res.text}")
                    continue
                
                analysis = analyze_res.json()
                
                # 4. Affichage des résultats
                print(f"   ---------------------------------------------------")
                print(f"   🏢 Fournisseur détecté : {analysis.get('supplier_name')}")
                print(f"   📅 Date détectée       : {analysis.get('facture_date')}")
                print(f"   📄 N° Facture          : {analysis.get('numero_facture')}")
                print(f"   📦 Produits trouvés    : {len(analysis.get('items', []))}")
                print(f"   ---------------------------------------------------")
                
                if len(analysis.get('items', [])) > 0:
                    print("   --- Détail des produits trouvés ---")
                    for item in analysis.get('items', []):
                        status_icon = "✅" if item['status'] == 'matched' else "🆕"
                        print(f"   {status_icon} Lu: '{item['ocr_name']}'")
                        print(f"       Qté: {item['ocr_qty']} {item['ocr_unit']} | Prix: {item['ocr_price']}€ | Total: {item['ocr_total']}€")
                else:
                    print("   ⚠️ Aucun produit détecté automatiquement.")
                    print("   💡 Causes possibles : Photo floue, écriture manuscrite, format non standard.")

        except Exception as e:
            print(f"❌ Exception traitement: {e}")

if __name__ == "__main__":
    run_test()
