"""
Générateur de fiches techniques par IA (Gemini 2.5 Flash via Emergent LLM Key).

Pour chaque recette sans ingrédients, demande à Gemini de proposer
des ingrédients réalistes (nom + quantité + unité) en se basant
EXCLUSIVEMENT sur les produits déjà présents en BDD.

Usage : python generate_recipe_ingredients.py

Note: idempotent - skip les recettes qui ont déjà des ingrédients.
"""
import asyncio
import json
import os
import sys
import uuid
import unicodedata
import re
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv('/app/backend/.env')

# Charger la clé Emergent
sys.path.insert(0, '/app/backend')
try:
    from config_keys import EMERGENT_LLM_KEY
except ImportError:
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

if not EMERGENT_LLM_KEY:
    print("❌ EMERGENT_LLM_KEY introuvable")
    sys.exit(1)


def norm(s):
    s = str(s or "").lower().strip()
    s = s.replace('œ', 'oe').replace('æ', 'ae').replace("’", "'")
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


async def generate_for_recipe(recette, products_compact_list, products_by_norm):
    """Appelle Gemini pour générer les ingrédients d'une recette."""
    session_id = f"recipe-gen-{uuid.uuid4()}"
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=(
            "Tu es un chef de cuisine français expert. Tu connais les recettes classiques "
            "et leurs proportions standards pour 1 portion. Tu réponds toujours UNIQUEMENT "
            "avec un JSON valide, sans texte ni commentaire avant ou après."
        )
    ).with_model("gemini", "gemini-2.5-flash")

    portions = recette.get('portions', 1) or 1
    prompt = f"""Génère la fiche technique de la recette suivante :

RECETTE: "{recette['nom']}"
CATÉGORIE: {recette.get('categorie', '?')}
PORTIONS: {portions}
PRIX DE VENTE: {recette.get('prix_vente', 0)}€

INSTRUCTION CRITIQUE : utilise UNIQUEMENT des ingrédients de cette liste de produits disponibles en stock :
{products_compact_list}

Pour chaque ingrédient nécessaire, retourne :
- "produit_nom" : le nom EXACT du produit tel qu'écrit dans la liste ci-dessus (copie-colle)
- "quantite" : quantité numérique nécessaire (PAR PORTION, pas pour les {portions} portions)
- "unite" : "kg", "g", "L", "mL", "cL", "piece", "pièce" selon ce qui convient

Si un ingrédient classique n'est PAS dans la liste, ignore-le (ne propose JAMAIS un produit absent).

Pour les recettes au poids vendues à la pesée (ex : huîtres, oursins, crustacés à l'unité), utilise les produits "à la pièce" si présents.

Format de réponse (JSON STRICT, rien d'autre) :
{{
  "ingredients": [
    {{"produit_nom": "Pâtes linguine", "quantite": 0.12, "unite": "kg"}},
    {{"produit_nom": "Palourdes", "quantite": 0.2, "unite": "kg"}}
  ]
}}

Si la recette est trop simple pour avoir une fiche technique (ex: juste un produit revendu tel quel), retourne :
{{"ingredients": [{{"produit_nom": "<le seul produit>", "quantite": 1, "unite": "piece"}}]}}
"""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        # Extraire le JSON
        txt = response.strip()
        # Supprimer les fences markdown si présents
        if txt.startswith('```'):
            txt = re.sub(r'^```(?:json)?\s*', '', txt)
            txt = re.sub(r'\s*```$', '', txt)
        data = json.loads(txt)

        ingredients_raw = data.get('ingredients', [])
        if not isinstance(ingredients_raw, list):
            return [], "format_invalide"

        # Mapper chaque ingrédient sur un produit BDD réel
        ingredients_final = []
        unmatched = []
        for ing in ingredients_raw:
            nom_propose = ing.get('produit_nom', '').strip()
            qty = ing.get('quantite', 0)
            unite = ing.get('unite', 'kg')

            if not nom_propose or qty <= 0:
                continue

            # Match exact
            n = norm(nom_propose)
            produit = products_by_norm.get(n)

            # Match plus souple : sous-string
            if not produit:
                for pn, p in products_by_norm.items():
                    if n in pn or pn in n:
                        produit = p
                        break

            if produit:
                ingredients_final.append({
                    "produit_id": produit["id"],
                    "produit_nom": produit["nom"],
                    "ingredient_id": produit["id"],
                    "ingredient_type": "produit",
                    "ingredient_nom": produit["nom"],
                    "quantite": float(qty),
                    "unite": unite,
                })
            else:
                unmatched.append(nom_propose)

        return ingredients_final, unmatched if unmatched else None
    except json.JSONDecodeError as e:
        return [], f"json_error: {e}"
    except Exception as e:
        return [], f"error: {e}"


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    # Charger recettes sans ingrédients
    recettes = await db.recettes.find(
        {"archived": {"$ne": True}, "$or": [
            {"ingredients": {"$exists": False}},
            {"ingredients": []},
            {"ingredients": None}
        ]},
        {"_id": 0}
    ).to_list(200)

    print(f"📋 {len(recettes)} recette(s) sans fiche technique à générer")
    if not recettes:
        print("✅ Rien à faire")
        return

    # Charger produits (excluant les boissons/bar pour les ingrédients de recettes)
    # Sauf pour les desserts qui peuvent utiliser du chocolat, vanille, etc.
    produits = await db.produits.find(
        {"archived": {"$ne": True}},
        {"_id": 0, "id": 1, "nom": 1, "unite": 1, "categorie": 1}
    ).to_list(2000)
    preparations = await db.preparations.find(
        {"archived": {"$ne": True}},
        {"_id": 0, "id": 1, "nom": 1, "unite_preparee": 1}
    ).to_list(500)

    # Index par nom normalisé pour le matching
    products_by_norm = {}
    for p in produits:
        products_by_norm[norm(p["nom"])] = p
    for prep in preparations:
        # On peut aussi utiliser des préparations comme ingrédients de recette
        products_by_norm[norm(prep["nom"])] = {
            "id": prep["id"], "nom": prep["nom"],
            "unite": prep.get("unite_preparee", "kg"),
            "is_preparation": True
        }

    # Liste compacte pour le prompt (filtrer les boissons sauf pour desserts)
    def build_product_list(recette_categorie):
        items = []
        for p in produits:
            cat = p.get("categorie", "")
            # Pour desserts/Pâtisserie : on garde tout (chocolat, vanille...)
            # Pour plats salés : on exclut les boissons bar (vins, cocktails, etc.)
            if recette_categorie == "Dessert":
                items.append(f'- "{p["nom"]}" ({p.get("unite", "kg")})')
            else:
                if cat == "bar":
                    # Garder seulement vins/spiritueux utilisés en cuisine
                    nom_low = p["nom"].lower()
                    if any(k in nom_low for k in ['cognac', 'rhum', 'vin blanc', 'porto', 'champagne', 'pastis']):
                        items.append(f'- "{p["nom"]}" ({p.get("unite", "kg")})')
                else:
                    items.append(f'- "{p["nom"]}" ({p.get("unite", "kg")})')
        # Préparations
        for prep in preparations:
            items.append(f'- "{prep["nom"]}" ({prep.get("unite_preparee", "kg")}, préparation maison)')
        return "\n".join(items)

    # Process par batch de 4 recettes en parallèle
    BATCH_SIZE = 4
    stats = {"success": 0, "no_ingredients": 0, "errors": 0, "unmatched_total": 0}

    for i in range(0, len(recettes), BATCH_SIZE):
        batch = recettes[i:i + BATCH_SIZE]
        print(f"\n--- Batch {i // BATCH_SIZE + 1}/{(len(recettes) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} recettes) ---")

        # Construire les listes compactes (différentes selon catégorie)
        tasks = []
        for r in batch:
            prod_list = build_product_list(r.get("categorie", "Plat"))
            tasks.append(generate_for_recipe(r, prod_list, products_by_norm))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r, result in zip(batch, results):
            if isinstance(result, Exception):
                print(f"  ❌ {r['nom']}: exception {result}")
                stats["errors"] += 1
                continue
            ingredients, error = result

            if not ingredients:
                print(f"  ⚠️ {r['nom']}: aucun ingrédient ({error})")
                stats["no_ingredients"] += 1
                continue

            # Calculer le coût matière
            cout = 0.0
            for ing in ingredients:
                p = await db.produits.find_one({"id": ing["produit_id"]}, {"_id": 0, "prix_achat": 1})
                if p and p.get("prix_achat"):
                    cout += ing["quantite"] * p["prix_achat"]
            cout = round(cout, 2)

            # Calculer coefficient si prix vente > 0
            coef = None
            prix_vente = r.get("prix_vente", 0) or 0
            if prix_vente > 0 and cout > 0:
                coef = round(cout / prix_vente, 3)

            # Persister
            update = {
                "ingredients": ingredients,
                "cout_matiere": cout,
                "ai_generated": True,
                "ai_generated_at": datetime.now(timezone.utc),
            }
            if coef is not None:
                update["coefficient_reel"] = coef

            await db.recettes.update_one({"id": r["id"]}, {"$set": update})

            unmatched_count = len(error) if isinstance(error, list) else 0
            stats["unmatched_total"] += unmatched_count
            stats["success"] += 1

            unmatched_str = f" ⚠️ {unmatched_count} non mappés" if unmatched_count else ""
            print(f"  ✅ {r['nom']}: {len(ingredients)} ingrédients, coût={cout}€{unmatched_str}")

        # Petit délai entre batches pour ne pas surcharger l'API
        if i + BATCH_SIZE < len(recettes):
            await asyncio.sleep(0.5)

    print()
    print("=" * 70)
    print("✅ GÉNÉRATION TERMINÉE")
    print("=" * 70)
    print(f"  ✅ Succès           : {stats['success']}")
    print(f"  ⚠️  Aucun ingrédient: {stats['no_ingredients']}")
    print(f"  ❌ Erreurs          : {stats['errors']}")
    print(f"  ⚠️  Total non mappés (à vérifier manuellement) : {stats['unmatched_total']}")


if __name__ == "__main__":
    asyncio.run(main())
