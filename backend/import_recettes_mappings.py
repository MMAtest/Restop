"""
Pré-remplit la collection caisse_mappings pour les PLATS (recettes)
en utilisant le matching fuzzy déjà au point.
"""
import asyncio, os, sys, re, unicodedata, uuid
from datetime import datetime
import openpyxl
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

CARTE_PATH = "/app/backend/data/carte_caisse.xlsx"
PLAT_TYPES = {'Poisson', 'Autre plat', 'Dessert', 'Entrée', 'Viande', 'Végétarien', 'Pizza /pâtes', 'Fromage'}

def norm(s):
    s = str(s or "").lower().strip()
    s = s.replace('œ', 'oe').replace('æ', 'ae').replace("’", "'")
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    stop = {'de','du','des','la','le','les','a','au','aux','en','et','d','l','nos','sans','copie','grand','petit','grande','petite'}
    return ' '.join(w for w in s.split() if w not in stop)

KEYWORDS_BDD = {
    'linguine palourdes': 'Linguine aux palourdes',
    'linguine': 'Linguine aux palourdes',
    'rigatoni truffe': 'Rigatoni à la truffe fraîche',
    'rigatoni': 'Rigatoni à la truffe fraîche',
    'gnocchi augustine': "Gnocchi d'Augustine",
    'gnocchi beurre': 'Gnocchi au beurre',
    'gnocchi': "Gnocchi d'Augustine",
    'farcis provencaux': 'Nos farcis provençaux',
    'farcie provencaux': 'Nos farcis provençaux',
    'souris agneau': "La merveilleuse souris d'agneau",
    'boeuf wellington': 'Boeuf Wellington à la truffe',
    'peche jour': 'Pêche du jour au four',
    'poulpe': "Le poulpe d'Augustine",
    'cote boeuf aubrac': 'Côte de boeuf Aubrac',
    'cote boeuf': 'Côte de boeuf Aubrac',
    'jarret veau': 'Jarret de veau du Sud-Ouest',
    'volaille': 'Volaille française truffée',
    'poissons ligne': 'Poissons de ligne (Arrivage)',
    'supions persillade': 'Les Supions en persillade de Mamie',
    'supions': 'Les Supions en persillade de Mamie',
    'moules gratinees': 'Moules gratinées en persillade',
    'moules persillade': 'Moules gratinées en persillade',
    'moule': 'Moules gratinées en persillade',
    'moules': 'Moules gratinées en persillade',
    'crabe sublime': "Le Crabe sublimé d'Augustine",
    'tartare thon': 'Tartare de thon & stracciatella',
    'sardines grillees': 'Sardines grillées à la flamme',
    'sardines': 'Sardines grillées à la flamme',
    'panisses': "Les Panisses de l'Estaque",
    'panisse': "Les Panisses de l'Estaque",
    'fleurs courgettes': 'Fleurs de courgettes farcies',
    'fleurs courgette': 'Fleurs de courgettes farcies',
    'pate croute': 'Le Pâté en croûte de Mamet',
    'pissaladiere': 'La Pissaladière de Mamie Francette',
    'buratta tomates datterino': 'Buratta & tomates datterino',
    'buratta': 'Buratta & tomates datterino',
    'burrata': 'Buratta & tomates datterino',
    'pomme terre four': 'Pomme de terre au four',
    'ecrase pomme terre': 'Écrasé de pomme de terre',
    'puree truffe': 'Purée à la truffe',
    'salade verte ail': "Salade verte à l'ail",
    'salade verte': "Salade verte à l'ail",
    'salade': "Salade verte à l'ail",
    'poelee legumes': 'Poêlée de légumes',
    'legumes': 'Poêlée de légumes',
    'glace yaourt': "L'incontournable glace yaourt",
    'tiramisu': 'Tiramisu de Mamet',
    'mousse chocolat': 'Mousse au chocolat',
    'riz lait': 'Riz au lait vanille caramel',
    'pavlova': "La pavlova d'Augustine",
}
KEYWORDS_SORTED = sorted(KEYWORDS_BDD.items(), key=lambda x: -len(x[0]))


def find_match(nom):
    n = norm(nom)
    n_words = n.split()
    for kw, target in KEYWORDS_SORTED:
        if all(w in n_words for w in kw.split()):
            return target
    return None


# Pattern poisson au poids: "1200g Daurade royale 13€/100g"
POISSON_POIDS_PATTERN = re.compile(r"^\s*\d+\s*g\b.*\d+\s*€?\s*/\s*100\s*g", re.IGNORECASE)


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Charger les recettes pour récupérer leur ID
    recettes = await db.recettes.find({"archived": {"$ne": True}}, {"_id": 0}).to_list(500)
    recettes_by_nom = {r['nom']: r for r in recettes}
    
    # Trouver l'ID de "Poissons de ligne (Arrivage)"
    poisson_arrivage = recettes_by_nom.get('Poissons de ligne (Arrivage)')
    
    wb = openpyxl.load_workbook(CARTE_PATH)
    ws = wb["Visualisation de la carte"]
    rows = list(ws.iter_rows(values_only=True))
    
    created = 0
    skipped = 0
    poids_pattern_count = 0
    unmatched = []
    
    for r in rows[8:]:
        if not r or not r[1]:
            continue
        nom_caisse = str(r[1]).strip()
        prix = r[2]
        type_p = str(r[4] or "").strip()
        cat_caisse = str(r[5] or "").strip()
        
        if type_p not in PLAT_TYPES:
            continue
        
        # Skip si déjà mappé
        existing = await db.caisse_mappings.find_one({"caisse_nom": nom_caisse})
        if existing:
            skipped += 1
            continue
        
        recette_target = None
        is_pattern = False
        
        # 1. Pattern poisson au poids
        if POISSON_POIDS_PATTERN.match(nom_caisse) and poisson_arrivage:
            recette_target = poisson_arrivage
            is_pattern = True
        else:
            # 2. Matching fuzzy par mots-clés
            target_nom = find_match(nom_caisse)
            if target_nom and target_nom in recettes_by_nom:
                recette_target = recettes_by_nom[target_nom]
        
        if recette_target:
            await db.caisse_mappings.insert_one({
                "id": str(uuid.uuid4()),
                "caisse_nom": nom_caisse,
                "type": "recette",
                "cible_id": recette_target['id'],
                "cible_nom": recette_target['nom'],
                "prix_caisse": prix,
                "categorie_caisse": cat_caisse,
                "type_caisse": type_p,
                "auto_created": True,
                "pattern_match": is_pattern,
                "created_at": datetime.utcnow()
            })
            created += 1
            if is_pattern:
                poids_pattern_count += 1
        else:
            unmatched.append({"nom": nom_caisse, "type": type_p, "prix": prix})
    
    print("=" * 70)
    print("✅ PRÉ-MAPPING RECETTES TERMINÉ")
    print("=" * 70)
    print(f"  Mappings créés        : {created}")
    print(f"    - dont via pattern poids: {poids_pattern_count}")
    print(f"  Mappings déjà présents: {skipped}")
    print(f"  Plats non mappés      : {len(unmatched)}")
    print()
    if unmatched:
        print("Plats non mappés (à faire à la main dans l'UI):")
        for it in sorted(unmatched, key=lambda x: x['nom']):
            print(f"  • [{it['type']}] {it['nom']} ({it['prix']}€)")


if __name__ == "__main__":
    asyncio.run(main())
