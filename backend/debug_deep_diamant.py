
import requests
import os

files = [
    {"name": "Diamant_Test.png", "url": "https://customer-assets.emergentagent.com/job_81ceab0b-36c5-44c6-b922-a4dd99271433/artifacts/h7gmpj1a_Screenshot_20251208-230901.png"}
]

API_URL = "http://localhost:8001/api"

def debug_deep_diamant():
    print("🚀 DEBUG PROFOND - DIAMANT")
    
    for file_info in files:
        try:
            r = requests.get(file_info['url'])
            path = f"/tmp/{file_info['name']}"
            with open(path, 'wb') as f: f.write(r.content)
                
            with open(path, 'rb') as f:
                res = requests.post(f"{API_URL}/ocr/upload-document", 
                                  files={'file': (file_info['name'], f, 'image/png')},
                                  data={'document_type': 'facture_fournisseur'})
                
                data = res.json()
                print(f"Status Upload: {res.status_code}")
                
                txt = data.get('texte_extrait', '')
                print(f"Longueur texte extrait: {len(txt)}")
                
                if len(txt) > 0:
                    print("--- DÉBUT DU TEXTE ---")
                    print(txt[:500])
                    print("--- FIN DU TEXTE ---")
                else:
                    print("❌ L'OCR n'a RIEN lu du tout.")
                    
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_deep_diamant()
