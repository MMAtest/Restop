"""
Module de gestion de l'import des ventes journalières depuis L'Addition.

Flow :
1. POST /api/sales/preview      - Upload fichier Excel sales-analysis -> preview
2. POST /api/sales/mappings     - Sauvegarde un mapping caisse -> recette/produit
3. POST /api/sales/apply        - Applique le décrément stock + crée Rapport Z
4. GET  /api/sales/mappings     - Liste tous les mappings existants
5. GET  /api/sales/history      - Historique des imports

Types de mapping (collection caisse_mappings) :
  - "recette"        : décrémente via fiche technique de la recette
  - "produit_direct" : décrémente directement le stock du produit (1:1 avec qty vendue)
  - "ignore"         : pas de décrément (carafe d'eau, plat du jour générique...)
"""
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import openpyxl
import unicodedata

from daily_specials import resolve_daily_special


sales_router = APIRouter(prefix="/sales", tags=["sales"])

# Pattern poisson au poids (ex: "1200g Daurade royale 13€/100g")
POISSON_POIDS_PATTERN = re.compile(r"^\s*(\d+)\s*g\b.*?(\d+)\s*€?\s*/\s*100\s*g", re.IGNORECASE)

# Pattern viande/volaille au poids (ex: "1800g Volaille", "1400g Cote de bœuf")
POIDS_PREFIX_PATTERN = re.compile(r"^\s*(\d+)\s*g\s+(.+)$", re.IGNORECASE)

# Lignes à ignorer dans le fichier
IGNORE_LINE_PREFIXES = ['*', 'Total', 'Du ', 'Le montant']


# Fuzzy keyword matching : nom simple caisse -> recette BDD
# Si tous les mots du keyword sont dans le nom normalisé, on matche.
FUZZY_KEYWORDS = [
    ('linguine palourdes', 'Linguine aux palourdes'),
    ('linguine', 'Linguine aux palourdes'),
    ('rigatoni truffe', 'Rigatoni à la truffe fraîche'),
    ('rigatoni', 'Rigatoni à la truffe fraîche'),
    ('gnocchi augustine', "Gnocchi d'Augustine"),
    ('gnocchi beurre', 'Gnocchi au beurre'),
    ('gnocchi', "Gnocchi d'Augustine"),
    ('farcis provencaux', 'Nos farcis provençaux'),
    ('farcie provencaux', 'Nos farcis provençaux'),
    ('souris agneau', "La merveilleuse souris d'agneau"),
    ('boeuf wellington', 'Boeuf Wellington à la truffe'),
    ('peche jour', 'Pêche du jour au four'),
    ('poulpe', "Le poulpe d'Augustine"),
    ('cote boeuf aubrac', 'Côte de boeuf Aubrac'),
    ('cote boeuf', 'Côte de boeuf Aubrac'),
    ('jarret veau', 'Jarret de veau du Sud-Ouest'),
    ('volaille', 'Volaille française truffée'),
    ('poissons ligne', 'Poissons de ligne (Arrivage)'),
    ('supions persillade', 'Les Supions en persillade de Mamie'),
    ('supions', 'Les Supions en persillade de Mamie'),
    ('moules gratinees', 'Moules gratinées en persillade'),
    ('moules persillade', 'Moules gratinées en persillade'),
    ('moule', 'Moules gratinées en persillade'),
    ('moules', 'Moules gratinées en persillade'),
    ('crabe sublime', "Le Crabe sublimé d'Augustine"),
    ('tartare thon', 'Tartare de thon & stracciatella'),
    ('sardines grillees', 'Sardines grillées à la flamme'),
    ('sardines', 'Sardines grillées à la flamme'),
    ('panisses', "Les Panisses de l'Estaque"),
    ('panisse', "Les Panisses de l'Estaque"),
    ('fleurs courgettes', 'Fleurs de courgettes farcies'),
    ('fleurs courgette', 'Fleurs de courgettes farcies'),
    ('pate croute', 'Le Pâté en croûte de Mamet'),
    ('pissaladiere', 'La Pissaladière de Mamie Francette'),
    ('buratta tomates datterino', 'Buratta & tomates datterino'),
    ('buratta', 'Buratta & tomates datterino'),
    ('burrata', 'Buratta & tomates datterino'),
    ('pomme terre four', 'Pomme de terre au four'),
    ('ecrase pomme terre', 'Écrasé de pomme de terre'),
    ('puree truffe', 'Purée à la truffe'),
    ('salade verte ail', "Salade verte à l'ail"),
    ('salade verte', "Salade verte à l'ail"),
    ('poelee legumes', 'Poêlée de légumes'),
    ('glace yaourt', "L'incontournable glace yaourt"),
    ('tiramisu', 'Tiramisu de Mamet'),
    ('mousse chocolat', 'Mousse au chocolat'),
    ('riz lait', 'Riz au lait vanille caramel'),
    ('pavlova', "La pavlova d'Augustine"),
    ('escargot', None),  # Marqueur : à mapper manuellement
    ('chapon', 'Poissons de ligne (Arrivage)'),  # Si poisson au poids
]
FUZZY_KEYWORDS_SORTED = sorted(FUZZY_KEYWORDS, key=lambda x: -len(x[0]))


def fuzzy_match_recette(nom: str) -> Optional[str]:
    """Retourne le nom canonique de recette BDD si on trouve un keyword match."""
    n = normalize_name(nom)
    # Strip common stopwords (de, du, des, le, la, les, à, au)
    stop = {'de', 'du', 'des', 'la', 'le', 'les', 'a', 'au', 'aux', 'en', 'et', 'd', 'l', 'nos', 'sans', 'copie', 'grand', 'petit', 'grande', 'petite'}
    n_clean = ' '.join(w for w in n.split() if w not in stop)
    n_words = set(n_clean.split())
    for kw, target in FUZZY_KEYWORDS_SORTED:
        if target is None:
            continue
        kw_words = set(kw.split())
        if kw_words.issubset(n_words):
            return target
    return None


# ==================== Modèles Pydantic ====================

class MappingCreate(BaseModel):
    caisse_nom: str
    type: str  # "recette" | "produit_direct" | "ignore"
    cible_id: Optional[str] = None  # id recette ou produit, null si type=ignore
    cible_nom: Optional[str] = None


class SalePreviewItem(BaseModel):
    caisse_nom: str
    quantite: int
    ca_ttc: float
    mapping_type: Optional[str] = None  # "recette"|"produit_direct"|"ignore"|None (=non mappé)
    cible_id: Optional[str] = None
    cible_nom: Optional[str] = None
    pattern_match: bool = False
    is_new: bool = False  # True si c'est un nouveau nom jamais vu


class SalesPreviewResponse(BaseModel):
    date_vente: str
    total_ca: float
    total_qty: int
    nb_lignes: int
    items_mapped: List[SalePreviewItem]
    items_unmapped: List[SalePreviewItem]
    items_ignored: List[SalePreviewItem]


class SalesApplyRequest(BaseModel):
    date_vente: str  # ISO date
    items: List[SalePreviewItem]


# ==================== Helpers ====================

def normalize_name(s: str) -> str:
    """Normalisation pour comparaison robuste."""
    s = str(s or "").lower().strip()
    s = s.replace('œ', 'oe').replace('æ', 'ae').replace("’", "'")
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def parse_sales_xlsx(content: bytes) -> Dict[str, Any]:
    """
    Parse un fichier de ventes L'Addition. Supporte 2 formats :
    
    1. "sales-analysis" : 1 sheet, header simple (nom, CA TTC, qty, ...)
    2. "Products" : multi-sheets, on lit "ProductAnalytics" (Etablissement, Clé, ID, ..., Nom produit, Quantité totale, Total TTC, ...)
    
    Détection automatique via les sheet_names.
    
    Note : pour les produits au poids (pattern "13€/100g" ou poissons entiers),
    le rapport Products exprime la "Quantité totale" en GRAMMES.
    On convertit alors qty -> nombre de services (qty / 1000, arrondi).
    """
    try:
        xl = pd.ExcelFile(BytesIO(content), engine='openpyxl')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fichier illisible: {e}")

    sheet_names = xl.sheet_names

    # Détection produit au poids (pattern explicit OU poisson entier connu)
    weight_pattern = re.compile(r"\d+\s*€?\s*/\s*100\s*g", re.IGNORECASE)
    fish_entier_keywords = [
        'loup entier', 'daurade royale', 'sole entière', 'sole entiere',
        'st pierre', 'st-pierre', 'saint pierre', 'pagre', 'chapon',
        'turbot', 'rouget', 'maigre entier'
    ]

    def is_weight_based(nom: str) -> bool:
        n = nom.lower()
        if weight_pattern.search(nom):
            return True
        return any(k in n for k in fish_entier_keywords)

    # === Format "Products" : multi-sheets avec "ProductAnalytics" ===
    if "ProductAnalytics" in sheet_names:
        df = pd.read_excel(xl, sheet_name="ProductAnalytics", engine='openpyxl', header=0)
        if 'Nom produit' not in df.columns or 'Quantité totale' not in df.columns:
            raise HTTPException(status_code=400, detail="Sheet 'ProductAnalytics' invalide (colonnes manquantes)")

        date_vente = datetime.now(timezone.utc).date().isoformat()
        if "Accueil" in sheet_names:
            try:
                df_accueil = pd.read_excel(xl, sheet_name="Accueil", engine='openpyxl', header=None)
                txt = " ".join(str(v) for v in df_accueil.values.flatten() if pd.notna(v))
                m = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", txt)
                if m:
                    date_vente = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            except Exception:
                pass

        items = []
        for _, row in df.iterrows():
            nom = row.get('Nom produit')
            if pd.isna(nom):
                continue
            nom = str(nom).strip()
            if not nom or nom in ('Total', '_', 'nan'):
                continue
            if str(row.get('Etablissement', '')).strip() == 'Total':
                continue
            try:
                qty_raw = row.get('Quantité totale', 0)
                qty_int = int(qty_raw) if pd.notna(qty_raw) else 0
            except (ValueError, TypeError):
                qty_int = 0
            try:
                ca_raw = row.get('Total TTC', 0)
                ca = float(ca_raw) if pd.notna(ca_raw) else 0
            except (ValueError, TypeError):
                ca = 0
            if qty_int <= 0:
                continue

            # Auto-conversion grammes -> services pour les produits au poids
            if is_weight_based(nom) and qty_int >= 100:
                weight_grams = qty_int
                # Convertir en services : on suppose 1 service = ~1 kg de poisson entier
                # (un loup entier = 1-2 kg, un pagre = ~1 kg)
                # Donc qty_services = round(weight_grams / 1000), min 1
                services = max(1, round(weight_grams / 1000))
                items.append({
                    "nom": nom,
                    "qty": services,
                    "ca": round(ca, 2),
                    "weight_grams": weight_grams,  # info pour affichage
                    "auto_converted": True,
                })
            else:
                items.append({"nom": nom, "qty": qty_int, "ca": round(ca, 2)})

        return {"date": date_vente, "items": items}

    # === Format "sales-analysis" (legacy) : 1 sheet, header simple ===
    df = pd.read_excel(BytesIO(content), engine='openpyxl', header=0)
    if df.shape[1] < 5:
        raise HTTPException(status_code=400, detail="Format de fichier inattendu (colonnes manquantes)")

    df.columns = ['nom', 'ca_ttc', 'ca_ht', 'ca_brut', 'qty', 'offerts', 'remises', 'taux'] + list(df.columns[8:])

    first_col_header = df.columns[0] if isinstance(df.columns[0], str) else ""
    date_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(first_col_header))
    if date_match:
        d, m, y = date_match.groups()
        date_vente = f"{y}-{m}-{d}"
    else:
        date_vente = datetime.now(timezone.utc).date().isoformat()

    items = []
    for _, row in df.iterrows():
        nom = row.get('nom')
        if pd.isna(nom):
            continue
        nom = str(nom).strip()
        if not nom or any(nom.startswith(p) for p in IGNORE_LINE_PREFIXES):
            continue
        try:
            qty = int(row.get('qty', 0)) if not pd.isna(row.get('qty')) else 0
        except (ValueError, TypeError):
            qty = 0
        try:
            ca = float(row.get('ca_ttc', 0)) if not pd.isna(row.get('ca_ttc')) else 0
        except (ValueError, TypeError):
            ca = 0
        if qty <= 0:
            continue
        items.append({"nom": nom, "qty": qty, "ca": round(ca, 2)})

    return {"date": date_vente, "items": items}


# ==================== Routes ====================

def setup_sales_routes(db):
    """Initialise les routes avec accès DB. Appelé depuis server.py."""

    @sales_router.post("/preview")
    async def preview_sales_upload(file: UploadFile = File(...)):
        """
        Upload du fichier sales-analysis L'Addition.
        Parse + applique mappings existants + détecte pattern poisson au poids.
        Retourne une preview SANS modifier le stock.
        """
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Format Excel (.xlsx) requis")

        content = await file.read()
        parsed = parse_sales_xlsx(content)
        items = parsed["items"]

        # Charger tous les mappings existants
        mappings = await db.caisse_mappings.find({}, {"_id": 0}).to_list(length=2000)
        mappings_by_nom = {m["caisse_nom"]: m for m in mappings}

        # Trouver l'ID "Poissons de ligne (Arrivage)" pour pattern matching
        recette_arrivage = await db.recettes.find_one(
            {"nom": "Poissons de ligne (Arrivage)"},
            {"_id": 0, "id": 1, "nom": 1}
        )

        # Charger toutes les recettes (pour fuzzy match)
        all_recettes = await db.recettes.find({"archived": {"$ne": True}}, {"_id": 0, "id": 1, "nom": 1}).to_list(500)
        recettes_by_nom = {r["nom"]: r for r in all_recettes}

        items_mapped, items_unmapped, items_ignored = [], [], []

        for it in items:
            nom = it["nom"]
            qty = it["qty"]
            ca = it["ca"]

            preview_item = {
                "caisse_nom": nom,
                "quantite": qty,
                "ca_ttc": ca,
                "mapping_type": None,
                "cible_id": None,
                "cible_nom": None,
                "pattern_match": False,
                "is_new": False,
                "weight_grams": it.get("weight_grams"),
                "auto_converted": it.get("auto_converted", False),
            }

            # 1. Mapping exact existant
            existing = mappings_by_nom.get(nom)
            if existing:
                preview_item["mapping_type"] = existing["type"]
                preview_item["cible_id"] = existing.get("cible_id")
                preview_item["cible_nom"] = existing.get("cible_nom")
                preview_item["pattern_match"] = existing.get("pattern_match", False)
                # Pour les daily_special, on tente de résoudre dès la preview
                if existing["type"] == "daily_special":
                    key = existing.get("daily_special_key")
                    if key:
                        rec_id, rec_nom = await resolve_daily_special(db, key, parsed["date"])
                        if rec_id:
                            preview_item["cible_id"] = rec_id
                            preview_item["cible_nom"] = rec_nom
                            preview_item["daily_special_resolved"] = True
                        else:
                            preview_item["daily_special_resolved"] = False
                            preview_item["daily_special_key"] = key
                if existing["type"] == "ignore":
                    items_ignored.append(preview_item)
                else:
                    items_mapped.append(preview_item)
                continue

            # 2. Pattern poisson au poids (ex: "1500g St pierre 13€/100g") OU produit poisson au poids (Products report)
            #    On considère qu'un item "auto_converted" (= poisson entier vendu en grammes) est aussi un poisson de ligne
            is_poisson_arrivage = (
                POISSON_POIDS_PATTERN.match(nom)
                or it.get("auto_converted")  # déjà détecté comme poisson au poids dans le parser
                or "/100g" in nom.lower()
            )
            if is_poisson_arrivage and recette_arrivage:
                preview_item["mapping_type"] = "recette"
                preview_item["cible_id"] = recette_arrivage["id"]
                preview_item["cible_nom"] = recette_arrivage["nom"]
                preview_item["pattern_match"] = True
                items_mapped.append(preview_item)
                continue

            # 3. Pattern viande au poids (ex: "1800g Volaille", "1400g Cote de bœuf")
            poids_match = POIDS_PREFIX_PATTERN.match(nom)
            nom_pour_fuzzy = nom
            if poids_match:
                nom_pour_fuzzy = poids_match.group(2)  # Le nom sans le préfixe poids

            # 4. Fuzzy match par mots-clés sur recettes BDD
            target_nom = fuzzy_match_recette(nom_pour_fuzzy)
            if target_nom and target_nom in recettes_by_nom:
                target = recettes_by_nom[target_nom]
                preview_item["mapping_type"] = "recette"
                preview_item["cible_id"] = target["id"]
                preview_item["cible_nom"] = target["nom"]
                preview_item["pattern_match"] = bool(poids_match)
                items_mapped.append(preview_item)
                continue

            # 5. Non mappé (nouveau)
            preview_item["is_new"] = True
            items_unmapped.append(preview_item)

        return {
            "date_vente": parsed["date"],
            "total_ca": round(sum(it["ca"] for it in items), 2),
            "total_qty": sum(it["qty"] for it in items),
            "nb_lignes": len(items),
            "items_mapped": items_mapped,
            "items_unmapped": items_unmapped,
            "items_ignored": items_ignored,
        }

    @sales_router.post("/mappings")
    async def save_mapping(mapping: MappingCreate):
        """Crée ou met à jour un mapping caisse -> recette/produit/ignore/daily_special."""
        if mapping.type not in ("recette", "produit_direct", "ignore", "daily_special"):
            raise HTTPException(status_code=400, detail="Type invalide")

        if mapping.type == "produit_direct" and not mapping.cible_id:
            raise HTTPException(status_code=400, detail="cible_id requis pour produit_direct")
        if mapping.type == "recette" and not mapping.cible_id:
            raise HTTPException(status_code=400, detail="cible_id requis pour recette")

        # Si recette, vérifier qu'elle existe et récupérer le nom canonique
        if mapping.type == "recette":
            r = await db.recettes.find_one({"id": mapping.cible_id}, {"_id": 0, "nom": 1})
            if not r:
                raise HTTPException(status_code=404, detail="Recette non trouvée")
            mapping.cible_nom = r["nom"]
        elif mapping.type == "produit_direct":
            p = await db.produits.find_one({"id": mapping.cible_id}, {"_id": 0, "nom": 1})
            if not p:
                raise HTTPException(status_code=404, detail="Produit non trouvé")
            mapping.cible_nom = p["nom"]

        # Upsert
        await db.caisse_mappings.update_one(
            {"caisse_nom": mapping.caisse_nom},
            {"$set": {
                "caisse_nom": mapping.caisse_nom,
                "type": mapping.type,
                "cible_id": mapping.cible_id,
                "cible_nom": mapping.cible_nom,
                "auto_created": False,
                "updated_at": datetime.now(timezone.utc),
            }, "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc),
            }},
            upsert=True
        )
        return {"success": True, "caisse_nom": mapping.caisse_nom, "type": mapping.type}

    @sales_router.get("/mappings")
    async def list_mappings():
        """Liste tous les mappings existants."""
        mappings = await db.caisse_mappings.find({}, {"_id": 0}).sort("caisse_nom", 1).to_list(length=5000)
        return {"mappings": mappings, "count": len(mappings)}

    @sales_router.delete("/mappings/{caisse_nom}")
    async def delete_mapping(caisse_nom: str):
        """Supprime un mapping (le caisse_nom redeviendra non-mappé)."""
        r = await db.caisse_mappings.delete_one({"caisse_nom": caisse_nom})
        return {"deleted": r.deleted_count > 0}

    @sales_router.post("/apply")
    async def apply_sales(request: SalesApplyRequest):
        """
        Applique le décrément stock pour les items mappés (recette + produit_direct).
        - recette : décrémente chaque ingrédient par (qty_recette × qty_vendue)
        - produit_direct : décrémente le stock du produit par qty_vendue
        - ignore : pas de décrément
        Crée également un rapport Z synthétique.
        """
        items = request.items
        if not items:
            raise HTTPException(status_code=400, detail="Aucun item à appliquer")

        log_recettes = []     # [{recette, qty_vendue, ingredients_decrementes}]
        log_produits = []     # [{produit, qty_decrementee}]
        log_ignored = []      # [{caisse_nom, qty}]
        warnings = []

        ca_total = 0.0
        qty_total = 0

        for item in items:
            ca_total += item.ca_ttc
            qty_total += item.quantite

            if item.mapping_type == "ignore":
                log_ignored.append({"caisse_nom": item.caisse_nom, "qty": item.quantite})
                continue

            # daily_special : résoudre dynamiquement via la collection daily_specials
            if item.mapping_type == "daily_special":
                # Récupérer la clé depuis le mapping en BDD
                map_doc = await db.caisse_mappings.find_one({"caisse_nom": item.caisse_nom}, {"_id": 0})
                key = map_doc.get("daily_special_key") if map_doc else None
                if not key:
                    warnings.append(f"daily_special_key manquant pour {item.caisse_nom}")
                    log_ignored.append({"caisse_nom": item.caisse_nom, "qty": item.quantite, "reason": "no_key"})
                    continue
                rec_id, rec_nom = await resolve_daily_special(db, key, request.date_vente)
                if not rec_id:
                    warnings.append(
                        f"⚠️ {item.caisse_nom} ({item.quantite}x): mission chef non complétée pour le {request.date_vente} "
                        f"-> stock NON décrémenté"
                    )
                    log_ignored.append({
                        "caisse_nom": item.caisse_nom, "qty": item.quantite,
                        "reason": f"daily_special_not_set ({key})"
                    })
                    continue
                # On reroute vers la logique 'recette' avec la cible résolue
                item.mapping_type = "recette"
                item.cible_id = rec_id
                item.cible_nom = rec_nom

            if item.mapping_type == "recette":
                # Charger la recette
                recette = await db.recettes.find_one({"id": item.cible_id}, {"_id": 0})
                if not recette:
                    warnings.append(f"Recette introuvable: {item.cible_nom}")
                    continue

                portions = recette.get("portions", 1) or 1
                ingredients_decrementes = []

                for ing in recette.get("ingredients", []):
                    produit_id = ing.get("produit_id") or ing.get("ingredient_id")
                    qty_ing = ing.get("quantite", 0) or 0
                    unite_ing = ing.get("unite", "")
                    if not produit_id or qty_ing <= 0:
                        continue

                    # Quantité totale à décrémenter = qty_par_portion × nb_ventes / portions
                    qty_total_decrement = (qty_ing / portions) * item.quantite

                    # Décrémenter stock_actuel du produit
                    p = await db.produits.find_one({"id": produit_id}, {"_id": 0, "nom": 1, "stock_actuel": 1})
                    if not p:
                        warnings.append(f"Produit ingrédient introuvable: {produit_id}")
                        continue

                    new_stock = max(0, (p.get("stock_actuel", 0) or 0) - qty_total_decrement)
                    await db.produits.update_one(
                        {"id": produit_id},
                        {"$set": {"stock_actuel": new_stock}}
                    )

                    # Décrémenter aussi stock_ingredients si existe
                    si = await db.stock_ingredients.find_one({"produit_id": produit_id}, {"_id": 0, "quantite": 1})
                    if si:
                        new_qty = max(0, (si.get("quantite", 0) or 0) - qty_total_decrement)
                        await db.stock_ingredients.update_one(
                            {"produit_id": produit_id},
                            {"$set": {"quantite": new_qty, "updated_at": datetime.now(timezone.utc)}}
                        )

                    ingredients_decrementes.append({
                        "produit_nom": p.get("nom"),
                        "qty": round(qty_total_decrement, 4),
                        "unite": unite_ing
                    })

                log_recettes.append({
                    "recette_nom": item.cible_nom,
                    "caisse_nom": item.caisse_nom,
                    "qty_vendue": item.quantite,
                    "ingredients_decrementes": ingredients_decrementes
                })

            elif item.mapping_type == "produit_direct":
                p = await db.produits.find_one({"id": item.cible_id}, {"_id": 0, "nom": 1, "stock_actuel": 1})
                if not p:
                    warnings.append(f"Produit introuvable: {item.cible_nom}")
                    continue
                new_stock = max(0, (p.get("stock_actuel", 0) or 0) - item.quantite)
                await db.produits.update_one(
                    {"id": item.cible_id},
                    {"$set": {"stock_actuel": new_stock}}
                )
                # Décrémenter aussi stock_ingredients si existe
                si = await db.stock_ingredients.find_one({"produit_id": item.cible_id}, {"_id": 0, "quantite": 1})
                if si:
                    new_qty = max(0, (si.get("quantite", 0) or 0) - item.quantite)
                    await db.stock_ingredients.update_one(
                        {"produit_id": item.cible_id},
                        {"$set": {"quantite": new_qty, "updated_at": datetime.now(timezone.utc)}}
                    )
                log_produits.append({
                    "produit_nom": p.get("nom"),
                    "caisse_nom": item.caisse_nom,
                    "qty_decrementee": item.quantite
                })
            else:
                # Item non mappé reçu dans apply -> on l'ignore (devrait pas arriver)
                warnings.append(f"Item non mappé ignoré: {item.caisse_nom}")

        # Créer un rapport Z synthétique
        rapport_id = str(uuid.uuid4())
        await db.rapports_z.insert_one({
            "id": rapport_id,
            "date": datetime.fromisoformat(request.date_vente),
            "ca_total": round(ca_total, 2),
            "produits": [
                {"nom": it.caisse_nom, "qty": it.quantite, "ca": it.ca_ttc, "type": it.mapping_type}
                for it in items
            ],
            "source": "import_ventes_caisse",
            "stock_decremente": True,
            "nb_recettes": len(log_recettes),
            "nb_produits_directs": len(log_produits),
            "nb_ignored": len(log_ignored),
            "created_at": datetime.now(timezone.utc),
        })

        # Journal d'audit
        await db.sales_imports_log.insert_one({
            "id": str(uuid.uuid4()),
            "rapport_z_id": rapport_id,
            "date_vente": request.date_vente,
            "ca_total": round(ca_total, 2),
            "qty_total": qty_total,
            "nb_recettes_decrementes": len(log_recettes),
            "nb_produits_decrementes": len(log_produits),
            "nb_ignored": len(log_ignored),
            "warnings": warnings,
            "log_recettes": log_recettes,
            "log_produits": log_produits,
            "log_ignored": log_ignored,
            "created_at": datetime.now(timezone.utc),
        })

        return {
            "success": True,
            "rapport_z_id": rapport_id,
            "ca_total": round(ca_total, 2),
            "qty_total": qty_total,
            "stats": {
                "recettes_decrementees": len(log_recettes),
                "produits_decrementes": len(log_produits),
                "items_ignored": len(log_ignored),
                "warnings": len(warnings),
            },
            "warnings": warnings[:20],  # Limiter
        }

    @sales_router.get("/history")
    async def sales_history(limit: int = 50):
        """Historique des imports de ventes."""
        logs = await db.sales_imports_log.find(
            {}, {"_id": 0, "log_recettes": 0, "log_produits": 0, "log_ignored": 0}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
        return {"history": logs}

    @sales_router.get("/history/{rapport_z_id}")
    async def sales_history_detail(rapport_z_id: str):
        """Détail complet d'un import."""
        log = await db.sales_imports_log.find_one({"rapport_z_id": rapport_z_id}, {"_id": 0})
        if not log:
            raise HTTPException(status_code=404, detail="Import non trouvé")
        return log

    return sales_router
