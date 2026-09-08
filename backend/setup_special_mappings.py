"""
Configure les mappings spécifiques demandés par l'utilisateur :
- St george 1L  -> produit boisson "Eau St George 1L" (créé en sodas/eaux)
- Supp écrasé   -> recette "Écrasé de pomme de terre"
- Caïpi Passion -> ignore
- Moscow Mule   -> ignore
- Plat du jour  -> mapping spécial "daily_special_plat" (résolu via daily_specials)
- Menu enfant   -> mapping spécial "daily_special_menu_enfant"
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')


async def upsert_mapping(db, caisse_nom, type_, cible_id=None, cible_nom=None, **extra):
    update = {
        "caisse_nom": caisse_nom,
        "type": type_,
        "cible_id": cible_id,
        "cible_nom": cible_nom,
        "auto_created": False,
        "updated_at": datetime.now(timezone.utc),
        **extra,
    }
    await db.caisse_mappings.update_one(
        {"caisse_nom": caisse_nom},
        {
            "$set": update,
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True
    )


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    # === 1. St george 1L : créer produit eau si absent + mapping produit_direct ===
    eau = await db.produits.find_one({"nom": "Eau St George 1L"})
    if not eau:
        eau_id = str(uuid.uuid4())
        await db.produits.insert_one({
            "id": eau_id,
            "nom": "Eau St George 1L",
            "categorie": "bar",
            "sous_categorie": "Soda / Eau",
            "unite": "bouteille 1L",
            "prix_achat": 0,
            "prix_vente_caisse": 8,
            "fournisseur": "",
            "stock_min": 0,
            "stock_actuel": 0,
            "dlc": None,
            "notes": "Eau plate Saint George 1L. Importée depuis carte L'Addition.",
            "archived": False,
            "created_at": datetime.now(timezone.utc),
        })
        await db.stock_ingredients.insert_one({
            "id": str(uuid.uuid4()),
            "produit_id": eau_id,
            "produit_nom": "Eau St George 1L",
            "quantite": 0,
            "unite": "bouteille 1L",
            "prix_unitaire": 0,
            "dlc": None,
            "emplacement": "bar",
            "updated_at": datetime.now(timezone.utc),
        })
        print(f"✅ Produit créé: Eau St George 1L")
    else:
        eau_id = eau["id"]
        print(f"⏭ Produit existe: Eau St George 1L")

    await upsert_mapping(db, "St george 1L", "produit_direct", eau_id, "Eau St George 1L")
    print(f"✅ Mapping: 'St george 1L' -> Eau St George 1L (produit_direct)")

    # === 2. Supp écrasé -> Écrasé de pomme de terre ===
    ecrase = await db.recettes.find_one({"nom": "Écrasé de pomme de terre"})
    if ecrase:
        await upsert_mapping(db, "Supp écrasé", "recette", ecrase["id"], ecrase["nom"])
        print(f"✅ Mapping: 'Supp écrasé' -> Écrasé de pomme de terre (recette)")
    else:
        print(f"⚠️ Recette 'Écrasé de pomme de terre' introuvable")

    # === 3. Caïpi Passion + Moscow Mule + Carafe eau -> ignore ===
    for nom in ["Caïpi Passion", "Moscow Mule", "Carafe eau"]:
        await upsert_mapping(db, nom, "ignore")
        print(f"✅ Mapping: '{nom}' -> ignore")

    # === 4. Plat du jour + Menu enfant -> daily_special ===
    # Type custom : "daily_special_plat" et "daily_special_menu_enfant"
    # Le décrément stock résoudra dynamiquement via la collection daily_specials.
    await upsert_mapping(
        db, "Plat du jour", "daily_special",
        cible_id=None, cible_nom="Plat du jour (défini par le chef)",
        daily_special_key="plat_du_jour"
    )
    print(f"✅ Mapping: 'Plat du jour' -> daily_special (résolu via mission chef)")

    await upsert_mapping(
        db, "Menu enfant", "daily_special",
        cible_id=None, cible_nom="Menu enfant (défini par le chef)",
        daily_special_key="menu_enfant"
    )
    print(f"✅ Mapping: 'Menu enfant' -> daily_special (résolu via mission chef)")

    print()
    print("✅ Tous les mappings spécifiques ont été configurés")


if __name__ == "__main__":
    asyncio.run(main())
