
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_users():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    users = await db.users.find().to_list(100)
    print(f"Nombre d'utilisateurs trouvés: {len(users)}")
    for user in users:
        print(f"User: {user.get('username')} | Role: {user.get('role')} | Email: {user.get('email')}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(check_users())
    loop.close()
