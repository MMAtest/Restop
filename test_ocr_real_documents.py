#!/usr/bin/env python3

import requests
import json
import os

BACKEND_URL = "https://ocr-joker-1.preview.emergentagent.com/api"
DOCUMENTS_DIR = "/app/ocr_test_documents"

def test_ocr_document(file_path, document_type):
    """Teste l'OCR sur un document spécifique"""
    try:
        print(f"\n{'='*60}")
        print(f"TRAITEMENT: {os.path.basename(file_path)}")
        print(f"TYPE: {document_type}")
        print('='*60)
        
        # Upload du fichier
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'document_type': document_type}
            
            response = requests.post(
                f"{BACKEND_URL}/ocr/upload-document",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SUCCÈS - Extraction OCR réussie:")
            print(f"📄 Fichier: {result['nom_fichier']}")
            print(f"📅 Date upload: {result['date_upload']}")
            print(f"📝 Type document: {result['type_document']}")
            
            # Afficher les données parsées
            donnees = result.get('donnees_parsees', {})
            
            if document_type == 'z_report':
                print(f"\n📊 DONNÉES RAPPORT Z:")
                print(f"📅 Date rapport: {donnees.get('date', 'Non trouvée')}")
                print(f"💰 Total CA: {donnees.get('total_ca', 'Non trouvé')}€")
                print(f"🍽️ Nb couverts: {donnees.get('nb_couverts', 'Non trouvé')}")
                
                plats = donnees.get('plats_vendus', [])
                print(f"🍽️ PLATS VENDUS ({len(plats)} plats):")
                for i, plat in enumerate(plats[:10], 1):  # Top 10
                    print(f"  {i:2d}. {plat['nom']} - Quantité: {plat['quantite']}")
                
                if len(plats) > 10:
                    print(f"     ... et {len(plats) - 10} autres plats")
                    
            elif document_type == 'facture_fournisseur':
                print(f"\n🏢 DONNÉES FACTURE FOURNISSEUR:")
                print(f"🏪 Fournisseur: {donnees.get('fournisseur', 'Non trouvé')}")
                print(f"📅 Date facture: {donnees.get('date', 'Non trouvée')}")
                print(f"🔢 N° facture: {donnees.get('numero_facture', 'Non trouvé')}")
                print(f"💰 Total HT: {donnees.get('total_ht', 'Non trouvé')}€")
                print(f"💰 Total TTC: {donnees.get('total_ttc', 'Non trouvé')}€")
                
                produits = donnees.get('produits', [])
                print(f"📦 PRODUITS ({len(produits)} produits):")
                for i, produit in enumerate(produits[:5], 1):  # Top 5
                    print(f"  {i}. {produit['nom']} - Qté: {produit.get('quantite', 'N/A')} - Prix: {produit.get('prix_unitaire', 'N/A')}€")
                
                if len(produits) > 5:
                    print(f"     ... et {len(produits) - 5} autres produits")
            
            print(f"\n🆔 ID document: {result['id']}")
            return result['id']
            
        else:
            print(f"❌ ERREUR - Code: {response.status_code}")
            print(f"Détail: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return None

def main():
    """Teste tous les documents réels"""
    print("🎯 TEST OCR DOCUMENTS RÉELS LA TABLE D'AUGUSTINE")
    print("=" * 80)
    
    # Documents à traiter
    documents = [
        ("rapport_z.jpeg", "z_report"),
        ("facture_fournisseur_1.jpeg", "facture_fournisseur"),
        ("facture_fournisseur_2.jpeg", "facture_fournisseur"), 
        ("facture_fournisseur_3.jpeg", "facture_fournisseur"),
        ("facture_fournisseur_4.jpeg", "facture_fournisseur"),
    ]
    
    document_ids = []
    success_count = 0
    
    for filename, doc_type in documents:
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        if os.path.exists(file_path):
            doc_id = test_ocr_document(file_path, doc_type)
            if doc_id:
                document_ids.append(doc_id)
                success_count += 1
        else:
            print(f"❌ Fichier non trouvé: {file_path}")
    
    print(f"\n{'='*80}")
    print(f"🎉 RÉSUMÉ FINAL")
    print(f"✅ Documents traités avec succès: {success_count}/{len(documents)}")
    print(f"📄 IDs des documents créés: {document_ids}")
    
    # Test de récupération des documents
    print(f"\n📋 VÉRIFICATION - Liste des documents OCR:")
    try:
        response = requests.get(f"{BACKEND_URL}/ocr/documents")
        if response.status_code == 200:
            documents_list = response.json()
            print(f"📊 Total documents en base: {len(documents_list)}")
            for doc in documents_list[-5:]:  # 5 derniers documents
                print(f"  - {doc['nom_fichier']} ({doc['type_document']}) - {doc['date_upload'][:10]}")
        else:
            print(f"❌ Erreur récupération documents: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception récupération: {str(e)}")

if __name__ == "__main__":
    main()