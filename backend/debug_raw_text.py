
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def show_raw_text():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    ids = ["aaf33dc2-945f-4031-87f7-cddfecb257b5", "c8f4696a-638d-4926-ac47-e697b4550809"]
    names = ["METRO", "MAMMAFIORE"]
    
    for doc_id, name in zip(ids, names):
        doc = await db.documents_ocr.find_one({"id": doc_id})
        if doc:
            print(f"\n\n=== TEXTE BRUT {name} ===")
            print(doc.get('texte_extrait', 'Pas de texte'))
            print("============================")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(show_raw_text())
    loop.close()
