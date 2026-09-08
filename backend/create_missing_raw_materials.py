"""
Crée les produits matières premières (MP) manquants pour les fruits de mer
et autres ingrédients nécessaires aux fiches techniques.
Idempotent.
"""
import asyncio
import os
import uuid
import re
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')


# (nom, categorie, unite, prix_achat_estimé, fournisseur)
MP_A_CREER = [
    # === FRUITS DE MER (à la pièce ou kg) ===
    ("Huîtres n°2", "marée", "piece", 0.8, "TERRE AZUR"),
    ("Huîtres n°3", "marée", "piece", 0.6, "TERRE AZUR"),
    ("Bulots cuits", "marée", "kg", 18, "RM MAR"),
    ("Oursin frais", "marée", "piece", 1.5, "RM MAR"),
    ("Tourteau", "marée", "kg", 14, "RM MAR"),
    ("Crevettes roses cuites", "marée", "kg", 22, "RM MAR"),
    ("Gambas crues", "marée", "kg", 28, "RM MAR"),
    ("Homard bleu vivant", "marée", "kg", 65, "RM MAR"),
    ("Saint-Jacques fraîches", "marée", "kg", 35, "RM MAR"),
    ("Sole fraîche", "marée", "kg", 32, "RM MAR"),

    # === VIANDES ===
    ("Filet de boeuf", "boucherie", "kg", 50, "BOUCHERIE COQUIERES"),
    ("Magret de canard", "boucherie", "piece", 18, "BOUCHERIE COQUIERES"),
    ("Foie gras frais", "boucherie", "kg", 65, "BOUCHERIE COQUIERES"),
    ("Chapon entier", "boucherie", "kg", 22, "BOUCHERIE COQUIERES"),

    # === PÂTES & FÉCULENTS ===
    ("Pâte feuilletée", "extra", "kg", 8, "EPISAVEUR"),
    ("Pâte à raviole", "extra", "kg", 12, "EPISAVEUR"),
    ("Pâte à profiterole (pâte à choux)", "extra", "kg", 7, "EPISAVEUR"),
    ("Riz arborio", "extra", "kg", 6, "EPISAVEUR"),
    ("Cèpes frais", "extra", "kg", 25, "TERRE AZUR"),

    # === DESSERTS ===
    ("Glace vanille", "extra", "L", 12, "EPISAVEUR"),
    ("Glace chocolat", "extra", "L", 12, "EPISAVEUR"),
    ("Glace fraise", "extra", "L", 12, "EPISAVEUR"),
    ("Glace italienne", "extra", "L", 8, "EPISAVEUR"),
    ("Spéculoos", "extra", "kg", 15, "EPISAVEUR"),
    ("Fruits rouges", "extra", "kg", 18, "TERRE AZUR"),
    ("Coulis chocolat chaud", "extra", "L", 14, "EPISAVEUR"),
    ("Crème chantilly", "extra", "L", 8, "EPISAVEUR"),

    # === FROMAGES (pour assiette + Mont d'Or) ===
    ("Mont d'Or AOP", "fromagerie", "kg", 22, "MAMMA FIORE"),
    ("Comté affiné", "fromagerie", "kg", 25, "MAMMA FIORE"),
    ("Roquefort", "fromagerie", "kg", 24, "MAMMA FIORE"),
    ("Chèvre frais", "fromagerie", "kg", 18, "MAMMA FIORE"),
    ("Parmesan", "fromagerie", "kg", 26, "MAMMA FIORE"),

    # === BASE CUISINE ===
    ("Beurre noisette préparation", "extra", "kg", 12, "EPISAVEUR"),
    ("Persil plat frais", "extra", "kg", 18, "TERRE AZUR"),
    ("Citron jaune frais", "extra", "kg", 4, "TERRE AZUR"),
    ("Ail frais", "extra", "kg", 8, "TERRE AZUR"),
    ("Échalotes", "extra", "kg", 5, "TERRE AZUR"),
    ("Sauce gribiche", "extra", "L", 14, "EPISAVEUR"),
    ("Mayonnaise maison", "extra", "L", 10, "EPISAVEUR"),
    ("Pain grillé pour fruits de mer", "extra", "piece", 0.3, "GRAND RUE"),
    ("Vinaigre de cidre", "extra", "L", 4, "EPISAVEUR"),
    ("Pastèque", "extra", "kg", 3, "TERRE AZUR"),
    ("Feta", "fromagerie", "kg", 16, "MAMMA FIORE"),
    ("Champignons de Paris", "extra", "kg", 7, "TERRE AZUR"),
    ("Saumon fumé", "marée", "kg", 38, "RM MAR"),
    ("Aneth frais", "extra", "kg", 25, "TERRE AZUR"),
    ("Mange-tout (haricots verts plats)", "extra", "kg", 8, "TERRE AZUR"),
    ("Escargots de Bourgogne", "marée", "kg", 28, "RM MAR"),
    ("Beurre persillé pour escargots", "extra", "kg", 14, "EPISAVEUR"),
    ("Truffe noire fraîche", "extra", "kg", 950, "EPISAVEUR"),
    ("Stracciatella di bufala", "fromagerie", "kg", 28, "MAMMA FIORE"),
    ("Caramel salé", "extra", "L", 10, "EPISAVEUR"),
]


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    created = 0
    skipped = 0

    for nom, categorie, unite, prix, fourn in MP_A_CREER:
        regex = re.compile(f"^{re.escape(nom)}$", re.IGNORECASE)
        existing = await db.produits.find_one({"nom": regex})
        if existing:
            skipped += 1
            continue

        produit_id = str(uuid.uuid4())
        await db.produits.insert_one({
            "id": produit_id, "nom": nom,
            "categorie": categorie, "unite": unite,
            "prix_achat": prix, "fournisseur": fourn,
            "stock_min": 0, "stock_actuel": 0,
            "dlc": None, "notes": "Matière première créée pour fiches techniques recettes",
            "archived": False, "created_at": datetime.now(timezone.utc),
        })
        await db.stock_ingredients.insert_one({
            "id": str(uuid.uuid4()), "produit_id": produit_id, "produit_nom": nom,
            "quantite": 0, "unite": unite, "prix_unitaire": prix,
            "dlc": None, "emplacement": "reserve", "updated_at": datetime.now(timezone.utc),
        })
        created += 1

    print(f"✅ {created} matières premières créées | {skipped} déjà existantes")


if __name__ == "__main__":
    asyncio.run(main())
