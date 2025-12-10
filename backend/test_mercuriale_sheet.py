
import sys
import os
import csv

# Ajouter le chemin pour importer le module server
sys.path.append('/app/backend')
from server import parse_mercuriale_fournisseur

def test_google_sheet_mercuriale():
    print("🚀 TEST MERCURIALE GOOGLE SHEET")
    print("===============================")
    
    # 1. Lire le CSV et simuler un texte OCR
    csv_path = "/tmp/mercuriale_test.csv"
    ocr_text_simulated = ""
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            print("--- CONTENU DU FICHIER ---")
            for row in reader:
                # On recolle les colonnes avec des espaces pour simuler une ligne lue
                line = " ".join(row)
                print(f"Ligne : {line}")
                ocr_text_simulated += line + "\n"
            print("--------------------------\n")
            
        # 2. Tester le Parser
        print("🧠 Analyse par le système...")
        result = parse_mercuriale_fournisseur(ocr_text_simulated)
        
        print(f"\n✅ RÉSULTAT :")
        print(f"   Fournisseur détecté : {result.get('fournisseur_detecte')}")
        print(f"   Produits détectés   : {len(result.get('produits_detectes', []))}")
        
        if result.get('produits_detectes'):
            print("\n   --- Détail ---")
            for p in result['produits_detectes']:
                print(f"   • {p['nom']} | {p['prix_achat']}€ / {p['unite']} ({p['categorie']})")
        else:
            print("\n   ❌ Aucun produit extrait. Le format n'est pas reconnu.")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    test_google_sheet_mercuriale()
