"""
Ajoute en BDD les ~42 recettes manquantes identifiées dans la carte L'Addition.
Idempotent : ne crée pas de doublon si la recette existe déjà.

Note : les recettes sont créées avec nom + catégorie + prix de vente uniquement.
Les ingrédients (fiche technique) sont à compléter manuellement depuis l'UI.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Liste des recettes à créer : (nom, categorie, prix_vente, [variantes_prix optionnelles])
RECETTES_A_AJOUTER = [
    # POISSONS / FRUITS DE MER
    ("Huîtres n°2 (par 6)", "Entrée", 16),
    ("Huîtres n°2 (par 12)", "Entrée", 30),
    ("Huîtres n°3 (par 6)", "Entrée", 15),
    ("Huîtres n°3 (par 12)", "Entrée", 28),
    ("Moules (par 12)", "Entrée", 10),
    ("Bulots (par 12)", "Entrée", 8),
    ("Oursin (à l'unité)", "Entrée", 4.5),
    ("Oursins (portion)", "Plat", 31),
    ("Tourteau", "Entrée", 15),
    ("Crevettes tièdes", "Entrée", 18),
    ("Crevettes (par 6)", "Entrée", 8),
    ("Crevettes (par 12)", "Entrée", 15),
    ("Gambas", "Plat", 45),
    ("Homard bleu (entrée)", "Entrée", 24),
    ("Homard bleu (plat)", "Plat", 66),
    ("Sole meunière", "Plat", 38),
    ("Risotto Saint-Jacques", "Plat", 38),
    ("Saint-Jacques poêlées", "Plat", 33),
    ("Raviole de poisson", "Plat", 32),
    ("Plateau dégustation", "Entrée", 34),

    # VIANDES
    ("Filet de boeuf", "Plat", 37),
    ("Magret de canard", "Plat", 38),
    ("Foie gras poêlé", "Entrée", 35),
    ("Pithiviers", "Plat", 69),
    ("Chapon volaille", "Plat", 69),

    # ENTRÉES
    ("Assiette de beurre", "Entrée", 9),
    ("Escargots", "Entrée", 22),
    ("Saumon gravlax", "Entrée", 24),
    ("Mange-tout", "Entrée", 21),

    # PÂTES & AUTRES
    ("Gnocchi à la truffe", "Plat", 26),
    ("Gnocchi nature", "Plat", 25),
    ("Ravioli aux cèpes", "Plat", 25),

    # FROMAGES
    ("Assiette de fromages", "Fromage", 15),
    ("Mont d'Or", "Fromage", 29),
    ("Stracciatella (fromage)", "Fromage", 12),

    # VÉGÉTARIEN
    ("Pastèque fêta", "Entrée", 14),
    ("Poêlée de champignons", "Autres", 11),
    ("Garniture gnocchi", "Autres", 8),

    # DESSERTS
    ("Profiteroles", "Dessert", 13),
    ("Omelette norvégienne", "Dessert", 15),
    ("Promenons-nous dans les bois", "Dessert", 15),
    ("Sundae", "Dessert", 3),
    ("Glace yaourt spéculos", "Dessert", 13),
]


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    created = 0
    skipped = 0
    by_cat = {}

    for nom, cat, prix in RECETTES_A_AJOUTER:
        # Idempotence : skip si recette avec ce nom existe déjà
        existing = await db.recettes.find_one({"nom": nom})
        if existing:
            skipped += 1
            continue

        recette = {
            "id": str(uuid.uuid4()),
            "nom": nom,
            "categorie": cat,
            "portions": 1,
            "prix_vente": prix,
            "temps_preparation": None,
            "description": f"Recette importée automatiquement depuis la carte L'Addition. À compléter avec la fiche technique.",
            "ingredients": [],
            "instructions": None,
            "cout_matiere": 0,
            "coefficient_prevu": None,
            "coefficient_reel": None,
            "archived": False,
            "created_at": datetime.now(timezone.utc),
        }
        await db.recettes.insert_one(recette)
        created += 1
        by_cat[cat] = by_cat.get(cat, 0) + 1

    print("=" * 70)
    print("✅ RECETTES MANQUANTES AJOUTÉES")
    print("=" * 70)
    print(f"  Créées      : {created}")
    print(f"  Déjà existantes (skip) : {skipped}")
    print()
    print("Répartition par catégorie :")
    for cat in sorted(by_cat.keys()):
        print(f"  • {cat:<15} {by_cat[cat]} recette(s)")


if __name__ == "__main__":
    asyncio.run(main())
