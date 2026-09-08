
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

async def insert_dummy_doc():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    doc_id = str(uuid.uuid4())
    
    document = {
        "id": doc_id,
        "nom_fichier": "facture_test_dlc.pdf",
        "type_document": "facture_fournisseur",
        "statut": "traite",
        "date_upload": datetime.utcnow(),
        "donnees_parsees": {
            "fournisseur": "Fournisseur Test DLC",
            "date": "02/12/2025",
            "numero_facture": "F2025-001",
            "produits": [
                {
                    "nom": "Mozzarella Test DLC",
                    "quantite": 10,
                    "unite": "kg",
                    "prix_unitaire": 15.0,
                    "prix_total": 150.0
                }
            ]
        }
    }
    
    await db.documents_ocr.insert_one(document)
    print(doc_id)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(insert_dummy_doc())
    loop.close()
