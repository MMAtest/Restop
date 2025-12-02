
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_batch():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    # Find product
    product = await db.produits.find_one({"nom": "Mozzarella Speciale DLC"})
    if not product:
        print("Product not found")
        return

    print(f"Product found: {product['id']}")
    
    # Find batches
    batches = await db.product_batches.find({"product_id": product['id']}).to_list(100)
    for b in batches:
        print(f"Batch: {b.get('batch_number')} - DLC: {b.get('expiry_date')} - Qty: {b.get('quantity')}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(check_batch())
    loop.close()
