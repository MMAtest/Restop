#!/usr/bin/env python3
"""
Script pour créer des documents OCR de test pour les 3 types:
- z_report (Ticket Z)
- facture_fournisseur (Facture Fournisseur)
- mercuriale (Mercuriale)
"""

import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io

BASE_URL = "https://cuisinepro.preview.emergentagent.com/api"

def create_mock_image_content(text_content, width=800, height=600):
    """Créer une image simulée avec du texte"""
    # Créer une image blanche
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Essayer d'utiliser une police par défaut
        font = ImageFont.load_default()
    except:
        font = None
    
    # Diviser le texte en lignes
    lines = text_content.split('\n')
    y_offset = 20
    
    for line in lines:
        if line.strip():
            draw.text((20, y_offset), line, fill='black', font=font)
            y_offset += 25
    
    # Convertir en bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer.getvalue()

def upload_test_document(document_type, filename, text_content):
    """Upload un document de test"""
    print(f"Création document {document_type}: {filename}")
    
    # Créer le contenu image
    image_content = create_mock_image_content(text_content)
    
    # Préparer les données pour l'upload
    files = {
        'file': (filename, image_content, 'image/png')
    }
    data = {
        'document_type': document_type
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ocr/upload-document", files=files, data=data)
        if response.status_code in [200, 201]:
            result = response.json()
            document_id = result.get("document_id")
            print(f"✅ Document créé: {document_id}")
            return document_id
        else:
            print(f"❌ Erreur upload: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception upload: {str(e)}")
        return None

def create_test_documents():
    """Créer tous les documents de test"""
    print("🚀 CRÉATION DES DOCUMENTS OCR DE TEST")
    print("=" * 50)
    
    created_documents = []
    
    # 1. Document Z-Report (Ticket Z)
    z_report_content = """RAPPORT Z - LA TABLE D'AUGUSTINE
Date: 15/12/2024
Heure: 22:30:15
Service: Soir

VENTES PAR CATÉGORIE:

BAR:
x3) Vin rouge Côtes du Rhône 24,00
x2) Pastis Ricard 16,00
x1) Cocktail Mojito 12,00

ENTRÉES:
x4) Supions en persillade 96,00
x3) Fleurs de courgettes 63,00
x2) Burrata des Pouilles 36,00

PLATS:
x5) Linguine aux palourdes 140,00
x2) Bœuf Wellington 112,00
x3) Rigatoni à la truffe 93,00

DESSERTS:
x3) Tiramisu 24,00
x2) Tarte citron 18,00

TOTAL HT: 634,00
TOTAL TTC: 697,40
Nombre de couverts: 22"""
    
    z_doc_id = upload_test_document("z_report", "ticket_z_test.png", z_report_content)
    if z_doc_id:
        created_documents.append({"id": z_doc_id, "type": "z_report"})
    
    # 2. Document Facture Fournisseur
    facture_content = """FACTURE FOURNISSEUR
MAISON ARTIGIANA
Giuseppe Pellegrino
Via Roma 123, Italie
Tel: +39 123 456 789

FACTURE N°: FAC-2024-001
Date: 14/12/2024

PRODUITS:
Burrata des Pouilles 250g x 10 = 180,00€
Mozzarella di Bufala 200g x 8 = 96,00€
Parmesan Reggiano 24 mois 1kg x 3 = 150,00€
Huile d'olive extra vierge 500ml x 5 = 75,00€

SOUS-TOTAL: 501,00€
TVA 20%: 100,20€
TOTAL TTC: 601,20€

Conditions de paiement: 30 jours
Date d'échéance: 13/01/2025"""
    
    facture_doc_id = upload_test_document("facture_fournisseur", "facture_artigiana.png", facture_content)
    if facture_doc_id:
        created_documents.append({"id": facture_doc_id, "type": "facture_fournisseur"})
    
    # 3. Document Mercuriale (optionnel)
    mercuriale_content = """MERCURIALE DES PRIX
MARCHÉ DE RUNGIS
Date: 15/12/2024

LÉGUMES:
Tomates cerises: 4,50€/kg (était 4,20€)
Courgettes: 2,80€/kg (était 3,10€)
Aubergines: 3,20€/kg (était 2,90€)

POISSONS:
Daurade royale: 18,50€/kg (était 17,80€)
Loup de mer: 22,00€/kg (était 21,50€)
Supions: 15,80€/kg (était 16,20€)

VIANDES:
Bœuf Limousin filet: 45,00€/kg (était 43,50€)
Agneau souris: 28,00€/kg (était 27,50€)

Mise à jour des prix effectuée le 15/12/2024"""
    
    mercuriale_doc_id = upload_test_document("mercuriale", "mercuriale_rungis.png", mercuriale_content)
    if mercuriale_doc_id:
        created_documents.append({"id": mercuriale_doc_id, "type": "mercuriale"})
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSUMÉ: {len(created_documents)} documents créés")
    for doc in created_documents:
        print(f"   - {doc['type']}: {doc['id']}")
    
    return created_documents

if __name__ == "__main__":
    # Créer les documents de test
    documents = create_test_documents()
    
    # Sauvegarder les IDs pour référence
    with open("/app/test_ocr_documents.json", "w") as f:
        json.dump(documents, f, indent=2)
    
    print(f"\n💾 IDs des documents sauvegardés dans: /app/test_ocr_documents.json")