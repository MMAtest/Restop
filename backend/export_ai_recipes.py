"""
Export des fiches techniques générées en preview vers un fichier JSON
qui sera intégré dans la migration prod (pour ne pas refaire les appels IA payants).
"""
import asyncio
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    # Récupérer toutes les recettes générées par IA (les 43 nouvelles + déjà existantes)
    recettes = await db.recettes.find(
        {"archived": {"$ne": True}, "ai_generated": True},
        {"_id": 0}
    ).to_list(200)

    # Pour chaque recette, on exporte : nom + ingredients (avec produit_nom au lieu d'ID)
    # Comme ça côté prod on retrouve les produits par nom
    export = []
    for r in recettes:
        ings_export = []
        for ing in r.get('ingredients', []):
            ings_export.append({
                "produit_nom": ing.get("produit_nom"),
                "quantite": ing.get("quantite"),
                "unite": ing.get("unite"),
            })
        export.append({
            "nom": r["nom"],
            "ingredients": ings_export,
            "cout_matiere": r.get("cout_matiere", 0),
            "coefficient_reel": r.get("coefficient_reel"),
        })

    output_path = "/app/backend/data/ai_recipe_ingredients.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    print(f"✅ Export : {len(export)} recettes vers {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
