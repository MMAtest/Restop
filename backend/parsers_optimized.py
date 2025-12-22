"""
Parsers Optimisés pour Extraction Prix et Quantités
Amélioration des 8 parsers existants avec logique robuste
"""

import re
from typing import Optional, Tuple, List

def parse_number_fr(val: str) -> Optional[float]:
    """Parse un nombre français (virgule comme séparateur décimal)"""
    if not val:
        return None
    try:
        val = val.strip()
        # Nettoyer la chaîne
        val = val.replace(',', '.')
        val = val.replace(' ', '')
        val = re.sub(r'[^\d.]', '', val)
        if val:
            return round(float(val), 2)
    except:
        pass
    return None

def extract_quantity_and_unit(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extrait quantité et unité d'une chaîne de texte
    Exemples:
    - "10.0 KG" → (10.0, "kg")
    - "6 PIECE" → (6.0, "pièce")
    - "2.5K" → (2.5, "kg")
    - "500G" → (500.0, "g")
    """
    text = text.upper().strip()
    
    # Pattern : nombre + unité
    patterns = [
        (r'([\d.,]+)\s*KG', 'kg'),
        (r'([\d.,]+)\s*G(?:\s|$)', 'g'),
        (r'([\d.,]+)\s*L(?:\s|$)', 'L'),
        (r'([\d.,]+)\s*PIECE', 'pièce'),
        (r'([\d.,]+)\s*COLIS', 'colis'),
        (r'([\d.,]+)\s*BOTTE', 'botte'),
        (r'([\d.,]+)\s*BUNCH', 'botte'),
        # Formats implicites (ex: "2K" = 2 kg)
        (r'([\d.,]+)K(?:\s|$)', 'kg'),
        # Juste un nombre (défaut = pièce)
        (r'([\d.,]+)', 'pièce')
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, text)
        if match:
            qty = parse_number_fr(match.group(1))
            if qty:
                return (qty, unit)
    
    return (None, None)

def extract_price(text: str) -> Optional[float]:
    """
    Extrait un prix d'une chaîne
    Gère les formats : 12.50, 12,50, 12€50, etc.
    """
    text = text.strip()
    
    # Pattern : nombre avec virgule ou point
    price_patterns = [
        r'([\d]+[.,][\d]{1,2})\s*€?',  # 12.50 ou 12,50
        r'([\d]+)\s*€',  # 12€
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            return parse_number_fr(match.group(1))
    
    # Essai simple : juste un nombre
    return parse_number_fr(text)

def parse_product_line_smart(line: str) -> Optional[dict]:
    """
    Parse une ligne de produit de manière intelligente
    Détecte automatiquement : nom, quantité, unité, prix unitaire, prix total
    
    Formats supportés :
    - "AIL PELE 10.0 KG 5.50 55.00"
    - "CIBOULETTE 10 PIECE 0.80 8.00€"
    - "FRAMBOISE 6.0 PIECE 2.99 17.94 €"
    """
    if not line or len(line.strip()) < 3:
        return None
    
    line = line.strip()
    
    # Essayer de détecter la structure : NOM QUANTITÉ UNITÉ PRIX_U PRIX_TOTAL
    # On cherche les nombres (prix ou quantités)
    numbers = re.findall(r'[\d]+[.,]?[\d]*', line)
    
    if len(numbers) < 2:
        return None  # Pas assez de données numériques
    
    # Stratégie : Les 2-3 premiers nombres sont quantité, les 2 derniers sont prix
    words = line.split()
    
    # Chercher la quantité (premier nombre avec unité)
    qty = None
    unit = None
    qty_index = -1
    
    for i, word in enumerate(words):
        q, u = extract_quantity_and_unit(word + ' ' + (words[i+1] if i+1 < len(words) else ''))
        if q:
            qty = q
            unit = u
            qty_index = i
            break
    
    # Chercher les prix (derniers nombres)
    prix_unitaire = None
    prix_total = None
    
    # Les prix sont généralement à la fin
    price_candidates = []
    for word in words[-4:]:  # Regarder les 4 derniers mots
        p = extract_price(word)
        if p:
            price_candidates.append(p)
    
    if len(price_candidates) >= 2:
        prix_unitaire = price_candidates[-2]
        prix_total = price_candidates[-1]
    elif len(price_candidates) == 1:
        prix_total = price_candidates[0]
        # Calculer prix unitaire si on a la quantité
        if qty and prix_total:
            prix_unitaire = round(prix_total / qty, 2)
    
    # Extraire le nom (tout avant la quantité)
    if qty_index > 0:
        nom = ' '.join(words[:qty_index])
    else:
        # Si pas de quantité détectée, prendre les premiers mots
        nom = ' '.join(words[:max(1, len(words)-4)])
    
    if not nom:
        return None
    
    return {
        "nom": nom.strip(),
        "quantite": qty or 1.0,
        "unite": unit or "pièce",
        "prix_unitaire": prix_unitaire or 0.0,
        "prix_total": prix_total or 0.0,
        "ligne_originale": line
    }

def optimize_parser_results(produits: List[dict]) -> List[dict]:
    """
    Post-traitement pour nettoyer et optimiser les résultats de parsing
    - Recalcule les prix manquants
    - Valide les quantités
    - Normalise les unités
    """
    optimized = []
    
    for prod in produits:
        # Validation quantité
        qty = prod.get("quantite", 0)
        if qty == 0 or qty is None:
            qty = 1.0
        
        # Validation prix
        prix_u = prod.get("prix_unitaire", 0)
        prix_t = prod.get("prix_total", 0)
        
        # Si manque prix unitaire mais on a total : calculer
        if (not prix_u or prix_u == 0) and prix_t and qty:
            prix_u = round(prix_t / qty, 2)
        
        # Si manque total mais on a unitaire : calculer
        if (not prix_t or prix_t == 0) and prix_u and qty:
            prix_t = round(prix_u * qty, 2)
        
        # Normaliser les unités
        unit = prod.get("unite", "pièce").lower()
        unit_map = {
            "k": "kg",
            "kilo": "kg",
            "piece": "pièce",
            "pc": "pièce",
            "bunch": "botte",
            "bouquet": "botte",
            "l": "L",
            "litre": "L",
        }
        unit = unit_map.get(unit, unit)
        
        optimized.append({
            **prod,
            "quantite": qty,
            "unite": unit,
            "prix_unitaire": prix_u,
            "prix_total": prix_t
        })
    
    return optimized

def detect_product_category(product_name: str) -> str:
    """
    Détecte automatiquement la catégorie d'un produit basé sur son nom
    Retourne la catégorie la plus probable
    """
    if not product_name:
        return "Autres"
    
    name_lower = product_name.lower()
    
    # Légumes
    legumes_keywords = [
        'tomate', 'salade', 'laitue', 'carotte', 'courgette', 'aubergine', 
        'poivron', 'concombre', 'oignon', 'ail', 'échalote', 'poireau',
        'épinard', 'chou', 'brocoli', 'chou-fleur', 'haricot', 'petit pois',
        'pomme de terre', 'patate', 'navet', 'radis', 'betterave', 'céleri',
        'asperge', 'artichaut', 'fenouil', 'endive', 'mâche', 'roquette',
        'mesclun', 'cresson', 'pourpier', 'légume', 'légumes'
    ]
    
    # Viandes
    viandes_keywords = [
        'bœuf', 'boeuf', 'veau', 'porc', 'agneau', 'mouton',
        'poulet', 'volaille', 'canard', 'dinde', 'caille', 'pigeon',
        'lapin', 'gibier', 'sanglier', 'cerf', 'chevreuil',
        'côte', 'filet', 'bavette', 'entrecôte', 'jarret', 'épaule',
        'magret', 'cuisse', 'blanc', 'escalope', 'viande', 'charcuterie',
        'jambon', 'saucisse', 'boudin', 'pâté', 'terrine', 'foie gras'
    ]
    
    # Poissons & Fruits de mer
    poissons_keywords = [
        'saumon', 'thon', 'dorade', 'daurade', 'bar', 'loup', 'sole',
        'turbot', 'cabillaud', 'morue', 'lieu', 'merlu', 'colin',
        'truite', 'brochet', 'sandre', 'carpe', 'rouget', 'saint-pierre',
        'saint-jacques', 'coquille', 'moule', 'huître', 'huitre',
        'crevette', 'gambas', 'langoustine', 'homard', 'langouste',
        'crabe', 'tourteau', 'araignée', 'bulot', 'bigorneau',
        'calamar', 'seiche', 'poulpe', 'supion', 'encornet',
        'poisson', 'marée', 'fruits de mer'
    ]
    
    # Crêmerie
    cremerie_keywords = [
        'fromage', 'brie', 'camembert', 'roquefort', 'comté', 'gruyère',
        'parmesan', 'mozzarella', 'chèvre', 'brebis', 'bleu',
        'beurre', 'crème', 'lait', 'yaourt', 'yogurt', 'faisselle',
        'ricotta', 'mascarpone', 'crémeux', 'laitier', 'lactique'
    ]
    
    # Épices & Condiments
    epices_keywords = [
        'sel', 'poivre', 'piment', 'paprika', 'curry', 'curcuma',
        'safran', 'cannelle', 'muscade', 'gingembre', 'vanille',
        'thym', 'romarin', 'basilic', 'persil', 'ciboulette', 'coriandre',
        'menthe', 'aneth', 'estragon', 'laurier', 'origan', 'sarriette',
        'herbe', 'épice', 'condiment', 'aromate',
        'huile', 'vinaigre', 'moutarde', 'sauce', 'mayonnaise'
    ]
    
    # Fruits
    fruits_keywords = [
        'pomme', 'poire', 'orange', 'citron', 'mandarine', 'pamplemousse',
        'banane', 'fraise', 'framboise', 'myrtille', 'cassis', 'groseille',
        'cerise', 'abricot', 'pêche', 'prune', 'raisin', 'melon', 'pastèque',
        'kiwi', 'ananas', 'mangue', 'fruit', 'fruits', 'agrume',
        'figue', 'datte', 'noix', 'noisette', 'amande', 'pistache'
    ]
    
    # Épicerie
    epicerie_keywords = [
        'farine', 'sucre', 'chocolat', 'cacao', 'confiture', 'miel',
        'levure', 'poudre à lever', 'gélatine', 'agar',
        'conserve', 'bocal', 'boîte', 'sec', 'séché'
    ]
    
    # Céréales & Féculents
    cereales_keywords = [
        'riz', 'pâte', 'pâtes', 'spaghetti', 'tagliatelle', 'linguine',
        'blé', 'quinoa', 'boulgour', 'semoule', 'couscous',
        'lentille', 'pois chiche', 'haricot sec', 'fève',
        'pain', 'baguette', 'céréale', 'féculent'
    ]
    
    # Boissons
    boissons_keywords = [
        'eau', 'jus', 'soda', 'coca', 'limonade',
        'vin', 'bière', 'champagne', 'apéritif', 'digestif',
        'café', 'thé', 'tisane', 'infusion',
        'sirop', 'boisson', 'liqueur'
    ]
    
    # Vérifier chaque catégorie
    categories = [
        (legumes_keywords, "Légumes"),
        (viandes_keywords, "Viandes"),
        (poissons_keywords, "Poissons"),
        (cremerie_keywords, "Crêmerie"),
        (epices_keywords, "Épices"),
        (fruits_keywords, "Fruits"),
        (epicerie_keywords, "Épicerie"),
        (cereales_keywords, "Céréales"),
        (boissons_keywords, "Boissons")
    ]
    
    for keywords, category in categories:
        if any(keyword in name_lower for keyword in keywords):
            return category
    
    return "Autres"

def detect_supplier_category(supplier_name: str, products_names: List[str] = None) -> str:
    """
    Détecte la catégorie d'un fournisseur basé sur son nom et les produits
    """
    if not supplier_name:
        return "frais"
    
    name_lower = supplier_name.lower()
    
    # Catégories spécifiques par mots-clés dans le nom
    if any(kw in name_lower for kw in ['primeur', 'légume', 'fruit', 'maraîcher']):
        return "primeur"
    if any(kw in name_lower for kw in ['boucherie', 'viande', 'boucher']):
        return "boucherie"
    if any(kw in name_lower for kw in ['poissonnerie', 'marée', 'mer', 'océan', 'pêcherie']):
        return "maree"
    if any(kw in name_lower for kw in ['fromage', 'crémerie', 'laiterie', 'fromagerie']):
        return "fromagerie"
    if any(kw in name_lower for kw in ['épicerie', 'épicier', 'supermarché', 'metro']):
        return "epicerie"
    if any(kw in name_lower for kw in ['surgelé', 'congélateur', 'frozen']):
        return "surgeles"
    
    # Si on a une liste de produits, détecter par majorité
    if products_names and len(products_names) > 0:
        categories_count = {}
        for prod_name in products_names:
            cat = detect_product_category(prod_name)
            categories_count[cat] = categories_count.get(cat, 0) + 1
        
        # Mapper catégorie produit → catégorie fournisseur
        cat_mapping = {
            "Légumes": "primeur",
            "Fruits": "primeur",
            "Viandes": "boucherie",
            "Poissons": "maree",
            "Crêmerie": "fromagerie"
        }
        
        # Trouver la catégorie majoritaire
        if categories_count:
            main_cat = max(categories_count, key=categories_count.get)
            return cat_mapping.get(main_cat, "frais")
    
    return "frais"  # Défaut

            qty = 1.0
        
        # Validation prix
        prix_u = prod.get("prix_unitaire", 0)
        prix_t = prod.get("prix_total", 0)
        
        # Si manque prix unitaire mais on a total : calculer
        if (not prix_u or prix_u == 0) and prix_t and qty:
            prix_u = round(prix_t / qty, 2)
        
        # Si manque total mais on a unitaire : calculer
        if (not prix_t or prix_t == 0) and prix_u and qty:
            prix_t = round(prix_u * qty, 2)
        
        # Normaliser les unités
        unit = prod.get("unite", "pièce").lower()
        unit_map = {
            "k": "kg",
            "kilo": "kg",
            "piece": "pièce",
            "pc": "pièce",
            "bunch": "botte",
            "bouquet": "botte",
            "l": "L",
            "litre": "L",
        }
        unit = unit_map.get(unit, unit)
        
        optimized.append({
            **prod,
            "quantite": qty,
            "unite": unit,
            "prix_unitaire": prix_u,
            "prix_total": prix_t
        })
    
    return optimized
