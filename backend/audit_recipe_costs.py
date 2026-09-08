"""
Audit des fiches techniques générées par IA :
- Détecte les coûts aberrants (cout_matiere > 1.5 × prix_vente)
- Identifie les ingrédients suspects (quantité × prix unitaire >> normale)
- Tente une correction automatique : si une quantité semble être en kg
  alors qu'elle devrait être en g (ex: 0.2kg de truffe = 190€ -> probablement 0.002kg = 2g)
- Marque les recettes nécessitant une revue manuelle
"""
import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    recettes = await db.recettes.find(
        {"archived": {"$ne": True}, "ai_generated": True},
        {"_id": 0}
    ).to_list(200)

    print(f"📋 {len(recettes)} recettes générées par IA à auditer")
    print()

    suspects = []
    auto_corriges = 0
    revue_manuelle = []

    for r in recettes:
        prix_vente = r.get('prix_vente', 0) or 0
        cout = r.get('cout_matiere', 0) or 0

        # Critère d'aberration : coût > 1.5 × prix de vente
        # (un coût matière normal est entre 25-35% du prix de vente)
        if prix_vente == 0 or cout <= prix_vente * 1.5:
            continue

        suspects.append(r)
        print(f"⚠️ {r['nom']}: cout={cout}€ vs prix_vente={prix_vente}€")

        # Trouver l'ingrédient le plus coûteux
        ingredients = r.get('ingredients', [])
        ing_costs = []
        for ing in ingredients:
            p = await db.produits.find_one({"id": ing.get("produit_id")}, {"_id": 0, "prix_achat": 1, "unite": 1, "nom": 1})
            if p and p.get("prix_achat"):
                cost = ing["quantite"] * p["prix_achat"]
                ing_costs.append({
                    "ing": ing,
                    "cost": cost,
                    "prix_achat": p["prix_achat"],
                    "produit_unite": p.get("unite", "kg"),
                    "produit_nom": p["nom"]
                })
        ing_costs.sort(key=lambda x: -x["cost"])

        # Stratégie d'auto-correction :
        # Pour les ingrédients qui contribuent > 50% du surcoût,
        # diviser leur quantité par 1000 si elle est suspecte (ex: 0.2 kg de truffe à 950€/kg = 190€)
        # ou par 10/100 selon contexte
        modified = False
        new_ingredients = list(ingredients)
        for idx, ic in enumerate(ing_costs[:3]):  # top 3 plus chers
            if ic["cost"] < cout * 0.4:
                continue
            # Si le produit a une unité en kg et qu'il s'agit de truffe / produit cher
            # 0.2 kg = 200g de truffe -> probable que ce soit 2g, donc /100
            if ic["prix_achat"] > 100 and ic["ing"]["quantite"] >= 0.05:
                # Diviser par 100 (kg -> 10g shavings est plus réaliste)
                old_qty = ic["ing"]["quantite"]
                new_qty = old_qty / 100
                # Trouver et remplacer
                for new_ing in new_ingredients:
                    if new_ing.get("produit_id") == ic["ing"].get("produit_id"):
                        new_ing["quantite"] = round(new_qty, 4)
                        # Note : si l'unité était "kg", on peut convertir l'affichage en g
                        if new_ing.get("unite", "").lower() == "kg" and new_qty < 0.05:
                            new_ing["unite"] = "kg"  # garder kg en unité de stock
                        modified = True
                        print(f"   🔧 {ic['produit_nom']}: {old_qty}kg → {new_qty}kg (correction /100)")
                        break
            elif ic["prix_achat"] > 30 and ic["ing"]["quantite"] >= 0.5:
                # Produits chers (boucherie) avec qty >= 500g -> probable que ce soit 50-100g
                old_qty = ic["ing"]["quantite"]
                new_qty = old_qty / 10
                for new_ing in new_ingredients:
                    if new_ing.get("produit_id") == ic["ing"].get("produit_id"):
                        new_ing["quantite"] = round(new_qty, 4)
                        modified = True
                        print(f"   🔧 {ic['produit_nom']}: {old_qty} → {new_qty} (correction /10)")
                        break

        if modified:
            # Recalculer le coût
            new_cout = 0.0
            for ing in new_ingredients:
                p = await db.produits.find_one({"id": ing.get("produit_id")}, {"_id": 0, "prix_achat": 1})
                if p and p.get("prix_achat"):
                    new_cout += ing["quantite"] * p["prix_achat"]
            new_cout = round(new_cout, 2)

            new_coef = round(new_cout / prix_vente, 3) if prix_vente > 0 else None

            update = {
                "ingredients": new_ingredients,
                "cout_matiere": new_cout,
                "ai_corrected": True,
                "ai_corrected_at": datetime.now(timezone.utc),
            }
            if new_coef is not None:
                update["coefficient_reel"] = new_coef

            await db.recettes.update_one({"id": r["id"]}, {"$set": update})
            auto_corriges += 1
            print(f"   ✅ Nouveau coût : {new_cout}€ (au lieu de {cout}€)")
            # Si toujours trop cher après correction, on ajoute à revue manuelle
            if new_cout > prix_vente * 1.5:
                revue_manuelle.append({"nom": r["nom"], "cout": new_cout, "prix_vente": prix_vente})
        else:
            revue_manuelle.append({"nom": r["nom"], "cout": cout, "prix_vente": prix_vente})

    print()
    print("=" * 70)
    print("✅ AUDIT TERMINÉ")
    print("=" * 70)
    print(f"  Total recettes IA   : {len(recettes)}")
    print(f"  Coûts suspects      : {len(suspects)}")
    print(f"  Auto-corrigés       : {auto_corriges}")
    print(f"  À revoir manuellement (toujours suspects): {len(revue_manuelle)}")
    if revue_manuelle:
        print()
        print("Recettes à vérifier manuellement dans l'UI :")
        for r in revue_manuelle:
            ratio = r["cout"] / r["prix_vente"] if r["prix_vente"] > 0 else 0
            print(f"   • {r['nom']:<40} coût={r['cout']}€ / vente={r['prix_vente']}€ (ratio {ratio:.1f})")


if __name__ == "__main__":
    asyncio.run(main())
