"""
Script d'import des boissons depuis la carte L'Addition.
Crée les produits BDD avec sous-catégories miroir de la caisse,
puis enregistre les mappings caisse -> produits dans la collection caisse_mappings.

Usage : python import_boissons.py
"""
import asyncio
import os
import sys
import re
import unicodedata
import uuid
from datetime import datetime
import openpyxl
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

CARTE_PATH = "/app/backend/data/carte_caisse.xlsx"

# Mapping catégorie caisse -> (categorie_principale, sous_categorie, unite)
CATEGORY_MAPPING = {
    "Verre & Pichets ROUGE": ("bar", "Vin au verre - Rouge", "verre"),
    "Verres & Pichets de BLANC": ("bar", "Vin au verre - Blanc", "verre"),
    "Verres & Pichets de ROSÉ": ("bar", "Vin au verre - Rosé", "verre"),
    "Bouteille ROUGE": ("bar", "Vin bouteille - Rouge", "bouteille"),
    "Bouteille BLANC": ("bar", "Vin bouteille - Blanc", "bouteille"),
    "Bouteilles ROSÉ": ("bar", "Vin bouteille - Rosé", "bouteille"),
    "Bouteille alcool": ("bar", "Spiritueux bouteille", "bouteille"),
    "Alcools Forts": ("bar", "Spiritueux", "verre"),
    "Bière Pression": ("bar", "Bière pression", "verre"),
    "Cocktail": ("bar", "Cocktail", "verre"),
    "Apéritifs": ("bar", "Apéritif", "verre"),
    "Digestifs": ("bar", "Digestif", "verre"),
    "Boissons fraîches": ("bar", "Soda / Eau", "bouteille"),
    "Boissons Chaudes": ("bar", "Boisson chaude", "tasse"),
    "Pago": ("bar", "Jus PAGO", "bouteille"),
}

PLAT_TYPES = {'Poisson', 'Autre plat', 'Dessert', 'Entrée', 'Viande', 'Végétarien', 'Pizza /pâtes', 'Fromage'}


def detect_unit_from_name(nom):
    """Détecte 25cl, 50cl, 1L dans le nom du produit"""
    n = nom.lower()
    if '50cl' in n or '50 cl' in n:
        return 'verre 50cl'
    if '25cl' in n or '25 cl' in n:
        return 'verre 25cl'
    if '1l' in n or '1 l' in n:
        return 'bouteille 1L'
    if 'btl' in n or 'bouteille' in n:
        return 'bouteille'
    return None


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    wb = openpyxl.load_workbook(CARTE_PATH)
    ws = wb["Visualisation de la carte"]
    rows = list(ws.iter_rows(values_only=True))

    # Stats
    created_produits = 0
    skipped_existing = 0
    created_mappings = 0
    by_subcat = {}

    for r in rows[8:]:
        if not r or not r[1]:
            continue
        nom_caisse = str(r[1]).strip()
        prix = r[2]
        type_p = str(r[4] or "").strip()
        cat_caisse = str(r[5] or "").strip()

        # Skip plats (gérés via recettes), skip Menu/services
        if type_p in PLAT_TYPES:
            continue
        if type_p in ('Menu', 'Prestation de service'):
            continue

        # Trouver mapping catégorie
        mapping = CATEGORY_MAPPING.get(cat_caisse)
        if not mapping:
            # Heuristique fallback selon le type
            if type_p == 'Vin':
                mapping = ("bar", "Vin (autre)", "verre")
            elif type_p == 'Bière':
                mapping = ("bar", "Bière", "verre")
            elif type_p in ('Soda', 'Eau'):
                mapping = ("bar", "Soda / Eau", "bouteille")
            elif type_p == 'Café' or type_p == 'Autre boisson chaude':
                mapping = ("bar", "Boisson chaude", "tasse")
            elif type_p == 'Cocktail':
                mapping = ("bar", "Cocktail", "verre")
            elif type_p == 'Spiritueux':
                mapping = ("bar", "Spiritueux", "verre")
            else:
                continue

        categorie, sous_categorie, unite_default = mapping

        # Affiner unité avec format
        u = detect_unit_from_name(nom_caisse) or unite_default

        # Vérifier si produit déjà existe (matching exact + insensible casse)
        regex = re.compile(f"^{re.escape(nom_caisse)}$", re.IGNORECASE)
        existing = await db.produits.find_one({"nom": regex})
        if existing:
            produit_id = existing["id"]
            skipped_existing += 1
            # Mettre à jour la sous-catégorie si manquante
            if not existing.get('sous_categorie'):
                await db.produits.update_one(
                    {"id": produit_id},
                    {"$set": {"sous_categorie": sous_categorie, "categorie": categorie}}
                )
        else:
            produit_id = str(uuid.uuid4())
            await db.produits.insert_one({
                "id": produit_id,
                "nom": nom_caisse,
                "categorie": categorie,
                "sous_categorie": sous_categorie,
                "unite": u,
                "prix_achat": 0,  # Option 1: prix d'achat à compléter par l'utilisateur
                "prix_vente_caisse": prix,  # Garde le prix de vente caisse pour info
                "fournisseur": "",
                "stock_min": 0,
                "stock_actuel": 0,
                "dlc": None,
                "notes": f"Importé depuis carte L'Addition - Type: {type_p}",
                "archived": False,
                "created_at": datetime.utcnow()
            })
            await db.stock_ingredients.insert_one({
                "id": str(uuid.uuid4()),
                "produit_id": produit_id,
                "produit_nom": nom_caisse,
                "quantite": 0,
                "unite": u,
                "prix_unitaire": 0,
                "dlc": None,
                "emplacement": "bar",
                "updated_at": datetime.utcnow()
            })
            created_produits += 1
            by_subcat[sous_categorie] = by_subcat.get(sous_categorie, 0) + 1

        # Créer le mapping caisse -> produit
        existing_map = await db.caisse_mappings.find_one({"caisse_nom": nom_caisse})
        if not existing_map:
            await db.caisse_mappings.insert_one({
                "id": str(uuid.uuid4()),
                "caisse_nom": nom_caisse,
                "type": "produit_direct",
                "cible_id": produit_id,
                "cible_nom": nom_caisse,
                "prix_caisse": prix,
                "categorie_caisse": cat_caisse,
                "type_caisse": type_p,
                "auto_created": True,
                "created_at": datetime.utcnow()
            })
            created_mappings += 1

    print("=" * 70)
    print("✅ IMPORT BOISSONS TERMINÉ")
    print("=" * 70)
    print(f"  Produits créés    : {created_produits}")
    print(f"  Produits existants: {skipped_existing} (sous-catégorie ajoutée)")
    print(f"  Mappings créés    : {created_mappings}")
    print()
    print("Répartition par sous-catégorie :")
    for sc in sorted(by_subcat.keys()):
        print(f"  • {sc:<35} {by_subcat[sc]} produit(s)")


if __name__ == "__main__":
    asyncio.run(main())
