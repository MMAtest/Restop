"""
Correction des 63 produits importes depuis le menu:
1. Relier les doublons aux produits existants
2. Attribuer categorie + fournisseur logiques
3. Creer les preparations manquantes
"""
import asyncio, os, uuid, re
from datetime import datetime
import motor.motor_asyncio

os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['DB_NAME'] = 'test_database'
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]


# === DOUBLONS: ingredient menu -> produit existant ===
DOUBLONS = {
    "Huile de friture": "Huile végétale de friture",
    "Crème liquide": "Crème liquide 35%",
    "Souris d'agneau (400g)": "Souris d'Agneau",
    "Biscuits à la cuillère": "Biscuits cuillères 192 pièces DELOS",
    "Oeufs": "Oeufs entiers",
    "Oeufs (blancs)": "Oeufs entiers",
    "Brousse du Rove": "Brousse fraiche",
    "Chocolat noir": "Noir 64%",
    "Côte de boeuf Aubrac": "Carré Aubrac",
    "Lait entier": "Lait demi écrémé",
    "Pomme de terre": "Pommes de terre",
    "Pommes de terre grenaille": "Pommes de terre",
}

# === CATEGORIES + FOURNISSEURS LOGIQUES ===
CORRECTIONS = {
    # Poissons / Marée
    "Seiches": {"categorie": "marée", "fournisseur": "RM MAR"},
    "Thon frais": {"categorie": "marée", "fournisseur": "RM MAR"},
    "Sardines": {"categorie": "marée", "fournisseur": "RM MAR"},
    "Anchois": {"categorie": "marée", "fournisseur": "RM MAR"},
    "Poisson entier frais": {"categorie": "marée", "fournisseur": "RM MAR"},
    "Poisson de ligne frais": {"categorie": "marée", "fournisseur": "RM MAR"},
    # Boucherie / Viandes
    "Boeuf Limousin haché": {"categorie": "boucherie", "fournisseur": "BOUCHERIE COQUIERES"},
    "Veau haché": {"categorie": "boucherie", "fournisseur": "BOUCHERIE COQUIERES"},
    "Filet de boeuf": {"categorie": "boucherie", "fournisseur": "BOUCHERIE COQUIERES"},
    "Jus de viande": {"categorie": "boucherie", "fournisseur": "BOUCHERIE COQUIERES"},
    "Volaille entière": {"categorie": "boucherie", "fournisseur": "BOUCHERIE COQUIERES"},
    # Fromagerie / Crémerie
    "Stracciatella des Pouilles": {"categorie": "fromagerie", "fournisseur": "MAMMA FIORE"},
    "Buratta": {"categorie": "fromagerie", "fournisseur": "MAMMA FIORE"},
    "Coeur de burrata": {"categorie": "fromagerie", "fournisseur": "MAMMA FIORE"},
    "Glace yaourt": {"categorie": "fromagerie", "fournisseur": "METRO"},
    "Mascarpone": {"categorie": "fromagerie", "fournisseur": "MAMMA FIORE"},
    # Primeur / Légumes / Fruits
    "Citron jaune": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Citron confit": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Fleurs de courgettes": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Tomates datterino": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Salade verte": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Légumes variés": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Légumes de saison": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Ananas frais": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    "Herbes de Provence": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Ail et herbes": {"categorie": "extra", "fournisseur": "TERRE AZUR"},
    # Epicerie / Extra
    "Persillade": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Chapelure": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Cardamome": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Farine de pois-chiche": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Olives noires": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Riz rond": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Café expresso": {"categorie": "extra", "fournisseur": "METRO"},
    "Pop-corns": {"categorie": "extra", "fournisseur": "METRO"},
    "Pain toasté": {"categorie": "extra", "fournisseur": "GRAND RUE"},
    "Sauce tomate Lucia": {"categorie": "extra", "fournisseur": "MAMMA FIORE"},
    "Citron et huile": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Vinaigrette à l'ail": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Caramel beurre salé": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    # Preparations maison (restent en extra, ce sont des sous-recettes)
    "Émulsion homard": {"categorie": "extra", "fournisseur": ""},
    "Farce à pâté": {"categorie": "extra", "fournisseur": ""},
    "Pâte à croûte": {"categorie": "extra", "fournisseur": ""},
    "Gelée": {"categorie": "extra", "fournisseur": ""},
    "Pâte à pain": {"categorie": "extra", "fournisseur": ""},
    "Duxelles de champignons": {"categorie": "extra", "fournisseur": ""},
    "Jus de cuisson aromatisé": {"categorie": "extra", "fournisseur": ""},
    "Beurre noisette": {"categorie": "fromagerie", "fournisseur": "METRO"},
    "Meringue": {"categorie": "extra", "fournisseur": ""},
    "Ganache vanille": {"categorie": "extra", "fournisseur": ""},
    "Truffe fraîche (Aestivum)": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Truffe (Aestivum)": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
    "Truffe fraîche": {"categorie": "extra", "fournisseur": "EPISAVEUR"},
}

# === PREPARATIONS A CREER si elles n'existent pas ===
# Format: nom_preparation -> produit_parent_nom
PREPARATIONS_A_CREER = {
    "Persillade": {"parent": None, "unite": "kg", "forme": "hachée"},
    "Émulsion homard": {"parent": "Fumet de Homard", "unite": "L", "forme": "émulsion"},
    "Farce à pâté": {"parent": None, "unite": "kg", "forme": "farce"},
    "Duxelles de champignons": {"parent": "Champignons de Paris", "unite": "kg", "forme": "duxelles"},
    "Jus de viande": {"parent": None, "unite": "L", "forme": "jus"},
    "Jus de cuisson aromatisé": {"parent": None, "unite": "L", "forme": "jus"},
    "Beurre noisette": {"parent": "Beurre sans marque", "unite": "kg", "forme": "noisette"},
    "Meringue": {"parent": "Oeufs entiers", "unite": "kg", "forme": "meringue"},
    "Ganache vanille": {"parent": "Noir 64%", "unite": "kg", "forme": "ganache"},
    "Caramel beurre salé": {"parent": "Beurre sans marque", "unite": "kg", "forme": "caramel"},
    "Vinaigrette à l'ail": {"parent": None, "unite": "L", "forme": "vinaigrette"},
    "Glace yaourt": {"parent": None, "unite": "kg", "forme": "glace"},
}


async def main():
    print("=" * 50)
    print("CORRECTION DES PRODUITS IMPORTES")
    print("=" * 50)
    
    # ============================================
    # ETAPE 1: Corriger les doublons
    # ============================================
    print("\n--- ETAPE 1: Correction des doublons ---")
    doublons_fixes = 0
    
    for nom_doublon, nom_existant in DOUBLONS.items():
        # Trouver le doublon (prix 0)
        doublon = await db.produits.find_one({"nom": nom_doublon, "prix_achat": 0})
        if not doublon:
            print(f"  SKIP: '{nom_doublon}' pas trouve")
            continue
        
        # Trouver le produit existant
        existant = await db.produits.find_one({"nom": re.compile(f"^{re.escape(nom_existant)}$", re.IGNORECASE)})
        if not existant:
            # Chercher aussi dans les preparations
            existant_prep = await db.preparations.find_one({"nom": re.compile(f"^{re.escape(nom_existant)}$", re.IGNORECASE)})
            if existant_prep:
                # Mettre a jour les recettes pour pointer vers la prep
                result = await db.recettes.update_many(
                    {"ingredients.produit_id": doublon["id"]},
                    {"$set": {
                        "ingredients.$[elem].produit_id": existant_prep["id"],
                        "ingredients.$[elem].produit_nom": existant_prep["nom"],
                        "ingredients.$[elem].ingredient_id": existant_prep["id"],
                        "ingredients.$[elem].ingredient_nom": existant_prep["nom"],
                        "ingredients.$[elem].ingredient_type": "preparation"
                    }},
                    array_filters=[{"elem.produit_id": doublon["id"]}]
                )
                # Supprimer le doublon
                await db.produits.delete_one({"id": doublon["id"]})
                await db.stock_ingredients.delete_many({"produit_id": doublon["id"]})
                doublons_fixes += 1
                print(f"  FIX: '{nom_doublon}' -> PREP '{existant_prep['nom']}' ({result.modified_count} recettes)")
                continue
            else:
                print(f"  SKIP: Cible '{nom_existant}' pas trouvee")
                continue
        
        # Mettre a jour toutes les recettes qui utilisent le doublon
        result = await db.recettes.update_many(
            {"ingredients.produit_id": doublon["id"]},
            {"$set": {
                "ingredients.$[elem].produit_id": existant["id"],
                "ingredients.$[elem].produit_nom": existant["nom"],
                "ingredients.$[elem].ingredient_id": existant["id"],
                "ingredients.$[elem].ingredient_nom": existant["nom"],
                "ingredients.$[elem].ingredient_type": "produit"
            }},
            array_filters=[{"elem.produit_id": doublon["id"]}]
        )
        
        # Supprimer le doublon et son stock
        await db.produits.delete_one({"id": doublon["id"]})
        await db.stock_ingredients.delete_many({"produit_id": doublon["id"]})
        doublons_fixes += 1
        print(f"  FIX: '{nom_doublon}' -> '{existant['nom']}' ({existant.get('prix_achat',0)}EUR) - {result.modified_count} recettes")
    
    print(f"  Total doublons corriges: {doublons_fixes}")
    
    # ============================================
    # ETAPE 2: Corriger categories + fournisseurs
    # ============================================
    print("\n--- ETAPE 2: Categories + Fournisseurs ---")
    corriges = 0
    
    for nom, correction in CORRECTIONS.items():
        result = await db.produits.update_many(
            {"nom": nom, "prix_achat": 0},
            {"$set": {
                "categorie": correction["categorie"],
                "fournisseur": correction["fournisseur"]
            }}
        )
        if result.modified_count > 0:
            corriges += 1
    
    print(f"  Produits corriges: {corriges}")
    
    # ============================================
    # ETAPE 3: Creer les preparations manquantes
    # ============================================
    print("\n--- ETAPE 3: Preparations manquantes ---")
    preps_creees = 0
    
    for nom_prep, config in PREPARATIONS_A_CREER.items():
        # Verifier si la prep existe deja
        existing = await db.preparations.find_one({"nom": re.compile(f"^{re.escape(nom_prep)}$", re.IGNORECASE)})
        if existing:
            print(f"  EXISTE: '{nom_prep}'")
            continue
        
        # Trouver le produit parent
        parent_id = ""
        if config["parent"]:
            parent = await db.produits.find_one({"nom": re.compile(f"^{re.escape(config['parent'])}$", re.IGNORECASE)})
            if parent:
                parent_id = parent["id"]
        
        # Creer la preparation
        prep_id = str(uuid.uuid4())
        await db.preparations.insert_one({
            "id": prep_id,
            "nom": nom_prep,
            "produit_id": parent_id,
            "forme_decoupe": config["forme"],
            "unite_preparee": config["unite"],
            "ratio_perte": 0,
            "notes": "Preparation maison",
            "archived": False,
            "created_at": datetime.utcnow()
        })
        preps_creees += 1
        print(f"  + PREP: '{nom_prep}' (parent: {config['parent'] or 'aucun'}, forme: {config['forme']})")
    
    print(f"  Preparations creees: {preps_creees}")
    
    # ============================================
    # ETAPE 4: Recalculer les couts des recettes
    # ============================================
    print("\n--- ETAPE 4: Recalcul des couts ---")
    recettes = await db.recettes.find({}, {"_id": 0}).to_list(length=500)
    recalculated = 0
    
    for recette in recettes:
        cout_total = 0
        for ing in recette.get("ingredients", []):
            pid = ing.get("produit_id", "")
            p = await db.produits.find_one({"id": pid}, {"_id": 0, "prix_achat": 1})
            if p and p.get("prix_achat"):
                cout_total += ing.get("quantite", 0) * p["prix_achat"]
        
        update = {"cout_matiere": round(cout_total, 2)}
        portions = recette.get("portions", 1) or 1
        prix_vente = recette.get("prix_vente", 0) or 0
        if prix_vente > 0 and cout_total > 0:
            update["coefficient_reel"] = round((cout_total / portions) / prix_vente, 2)
        
        await db.recettes.update_one({"id": recette["id"]}, {"$set": update})
        recalculated += 1
    
    print(f"  Recettes recalculees: {recalculated}")
    
    # ============================================
    # RESUME FINAL
    # ============================================
    total_p = await db.produits.count_documents({})
    total_p0 = await db.produits.count_documents({"prix_achat": 0})
    total_f = await db.fournisseurs.count_documents({})
    total_r = await db.recettes.count_documents({})
    total_prep = await db.preparations.count_documents({})
    
    print(f"\n{'='*50}")
    print(f"ETAT FINAL")
    print(f"  Produits: {total_p} (dont {total_p0} sans prix)")
    print(f"  Fournisseurs: {total_f}")
    print(f"  Preparations: {total_prep}")
    print(f"  Recettes: {total_r}")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
