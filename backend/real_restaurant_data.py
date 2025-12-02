"""
Données réelles du restaurant La Table d'Augustine
À utiliser pour restaurer les vraies données du restaurant
"""

# Fournisseurs réels - UN PAR CATÉGORIE
REAL_FOURNISSEURS = [
    {
        "nom": "Maison Artigiana",
        "categorie": "epicerie",
        "telephone": "04 95 XX XX XX",
        "email": "contact@artigiana.fr"
    },
    {
        "nom": "Pêcherie des Sanguinaires",
        "categorie": "frais",
        "telephone": "04 95 XX XX XX",
        "email": "pecherie@sanguinaires.fr"
    },
    {
        "nom": "Boucherie Maestracci",
        "categorie": "frais",
        "telephone": "04 95 XX XX XX",
        "email": "contact@maestracci.fr"
    },
    {
        "nom": "Maraîcher du Cap Corse",
        "categorie": "légumes",
        "telephone": "04 95 XX XX XX",
        "email": "contact@maraichers-capcorse.fr"
    },
    {
        "nom": "Fromagerie de Corse",
        "categorie": "crêmerie",
        "telephone": "04 95 XX XX XX",
        "email": "info@fromagerie-corse.fr"
    },
    {
        "nom": "Caves & Spiritueux d'Ajaccio",
        "categorie": "boissons",
        "telephone": "04 95 XX XX XX",
        "email": "contact@caves-ajaccio.fr"
    },
    {
        "nom": "Épices & Aromates du Marché",
        "categorie": "épices",
        "telephone": "04 95 XX XX XX",
        "email": "info@epices-marche.fr"
    }
]

# Produits réels (ingrédients)
REAL_PRODUITS = [
    # Poissons et fruits de mer
    {"nom": "Supions", "categorie": "Poissons", "unite": "kg", "reference_price": 18.50},
    {"nom": "Moules", "categorie": "Poissons", "unite": "kg", "reference_price": 8.00},
    {"nom": "Saint-Jacques", "categorie": "Poissons", "unite": "kg", "reference_price": 65.00},
    {"nom": "Crabe", "categorie": "Poissons", "unite": "kg", "reference_price": 45.00},
    {"nom": "Palourdes", "categorie": "Poissons", "unite": "kg", "reference_price": 12.00},
    {"nom": "Rougets", "categorie": "Poissons", "unite": "kg", "reference_price": 22.00},
    {"nom": "Daurade", "categorie": "Poissons", "unite": "kg", "reference_price": 16.00},
    {"nom": "Sole", "categorie": "Poissons", "unite": "kg", "reference_price": 42.00},
    {"nom": "Poisson du jour", "categorie": "Poissons", "unite": "kg", "reference_price": 28.00},
    
    # Viandes
    {"nom": "Bœuf (filet)", "categorie": "Viandes", "unite": "kg", "reference_price": 35.00},
    {"nom": "Bœuf (côte)", "categorie": "Viandes", "unite": "kg", "reference_price": 42.00},
    {"nom": "Veau (escalope)", "categorie": "Viandes", "unite": "kg", "reference_price": 28.00},
    {"nom": "Veau (jarret)", "categorie": "Viandes", "unite": "kg", "reference_price": 22.00},
    {"nom": "Agneau (souris)", "categorie": "Viandes", "unite": "kg", "reference_price": 24.00},
    {"nom": "Magret de canard", "categorie": "Viandes", "unite": "kg", "reference_price": 32.00},
    {"nom": "Foie gras de canard", "categorie": "Viandes", "unite": "kg", "reference_price": 85.00},
    {"nom": "Cuisses de grenouilles", "categorie": "Viandes", "unite": "kg", "reference_price": 38.00},
    {"nom": "Sanguins (gibier)", "categorie": "Viandes", "unite": "kg", "reference_price": 28.00},
    
    # Légumes
    {"nom": "Tomates cerises", "categorie": "Légumes", "unite": "kg", "reference_price": 4.50},
    {"nom": "Courgettes", "categorie": "Légumes", "unite": "kg", "reference_price": 2.80},
    {"nom": "Aubergines", "categorie": "Légumes", "unite": "kg", "reference_price": 3.20},
    {"nom": "Poivrons", "categorie": "Légumes", "unite": "kg", "reference_price": 3.50},
    {"nom": "Oignons", "categorie": "Légumes", "unite": "kg", "reference_price": 1.50},
    {"nom": "Pommes de terre", "categorie": "Légumes", "unite": "kg", "reference_price": 1.80},
    
    # Pâtes et féculents
    {"nom": "Linguine", "categorie": "Épicerie", "unite": "kg", "reference_price": 3.80},
    {"nom": "Rigatoni", "categorie": "Épicerie", "unite": "kg", "reference_price": 3.90},
    {"nom": "Gnocchi", "categorie": "Épicerie", "unite": "kg", "reference_price": 4.50},
    {"nom": "Farine de pois chiche", "categorie": "Épicerie", "unite": "kg", "reference_price": 3.20},
    {"nom": "Pâte feuilletée", "categorie": "Épicerie", "unite": "kg", "reference_price": 5.00},
    
    # Produits laitiers
    {"nom": "Parmesan", "categorie": "Crêmerie", "unite": "kg", "reference_price": 32.00},
    {"nom": "Comté", "categorie": "Crêmerie", "unite": "kg", "reference_price": 28.00},
    {"nom": "Mozzarella", "categorie": "Crêmerie", "unite": "kg", "reference_price": 8.50},
    {"nom": "Mascarpone", "categorie": "Crêmerie", "unite": "kg", "reference_price": 12.00},
    {"nom": "Brocciu", "categorie": "Crêmerie", "unite": "kg", "reference_price": 15.00},
    {"nom": "Beurre", "categorie": "Crêmerie", "unite": "kg", "reference_price": 8.00},
    {"nom": "Crème fraîche", "categorie": "Crêmerie", "unite": "L", "reference_price": 6.00},
    {"nom": "Yaourt", "categorie": "Crêmerie", "unite": "kg", "reference_price": 5.00},
    {"nom": "Lait", "categorie": "Crêmerie", "unite": "L", "reference_price": 1.50},
    {"nom": "Œufs", "categorie": "Crêmerie", "unite": "kg", "reference_price": 3.50},
    
    # Épices et aromates
    {"nom": "Basilic frais", "categorie": "Épices", "unite": "botte", "reference_price": 2.50},
    {"nom": "Persil", "categorie": "Épices", "unite": "botte", "reference_price": 1.80},
    {"nom": "Ail", "categorie": "Épices", "unite": "kg", "reference_price": 6.00},
    {"nom": "Thym", "categorie": "Épices", "unite": "botte", "reference_price": 2.00},
    {"nom": "Romarin", "categorie": "Épices", "unite": "botte", "reference_price": 2.00},
    
    # Huiles et condiments
    {"nom": "Huile d'olive", "categorie": "Épicerie", "unite": "L", "reference_price": 12.00},
    {"nom": "Vinaigre balsamique", "categorie": "Épicerie", "unite": "L", "reference_price": 8.50},
    {"nom": "Truffe (Uncinatum)", "categorie": "Épicerie", "unite": "kg", "reference_price": 450.00},
    {"nom": "Marrons", "categorie": "Épicerie", "unite": "kg", "reference_price": 12.00},
    {"nom": "Farine", "categorie": "Épicerie", "unite": "kg", "reference_price": 1.80},
    {"nom": "Sucre", "categorie": "Épicerie", "unite": "kg", "reference_price": 2.00},
    {"nom": "Sel", "categorie": "Épicerie", "unite": "kg", "reference_price": 1.00},
    {"nom": "Poivre", "categorie": "Épicerie", "unite": "kg", "reference_price": 15.00},
    {"nom": "Grand Marnier", "categorie": "Boissons", "unite": "L", "reference_price": 35.00},
    
    # Bar et spiritueux
    {"nom": "Vodka", "categorie": "Boissons", "unite": "L", "reference_price": 25.00},
    {"nom": "Rhum", "categorie": "Boissons", "unite": "L", "reference_price": 28.00},
    {"nom": "Apérol", "categorie": "Boissons", "unite": "L", "reference_price": 18.00},
    {"nom": "Prosecco", "categorie": "Boissons", "unite": "L", "reference_price": 12.00},
    {"nom": "Triple Sec", "categorie": "Boissons", "unite": "L", "reference_price": 15.00},
    
    # Vins au verre (1 verre = 1/6 bouteille)
    {"nom": "Château de Fonscolombe - Coteaux d'Aix", "categorie": "Boissons", "unite": "verre", "reference_price": 9.50},
    {"nom": "Domaine de La Ferme Blanche - Cassis Rosé", "categorie": "Boissons", "unite": "verre", "reference_price": 12.00},
    {"nom": "Domaine Guillaman - Côtes de Gascogne Rosé", "categorie": "Boissons", "unite": "verre", "reference_price": 9.00},
    {"nom": "Vignobles Marrenon - Luberon Rosé", "categorie": "Boissons", "unite": "verre", "reference_price": 9.00},
    {"nom": "MamET Les vieilles vignes - IGP Méditerranée Blanc", "categorie": "Boissons", "unite": "verre", "reference_price": 9.00},
    {"nom": "Domaine Perrin - Côtes du Rhône Rouge", "categorie": "Boissons", "unite": "verre", "reference_price": 8.50},
    {"nom": "Secret de Lunès - Pinot Noir", "categorie": "Boissons", "unite": "verre", "reference_price": 9.00},
    {"nom": "Vignobles Marrenon - Luberon Rouge", "categorie": "Boissons", "unite": "verre", "reference_price": 11.00},
    
    # Vins en bouteille (75cl)
    {"nom": "Château de Fonscolombe - Coteaux d'Aix (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 45.00},
    {"nom": "Domaine de La Ferme Blanche - Cassis Rosé (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 55.00},
    {"nom": "Domaine Guillaman - Côtes de Gascogne Rosé (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 42.00},
    {"nom": "Vignobles Marrenon - Luberon Rosé (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 38.00},
    {"nom": "Mas de Cadenet - Côtes de Provence Blanc (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 52.00},
    {"nom": "MamET Les vieilles vignes - IGP Méditerranée Blanc (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 40.00},
    {"nom": "Château de Brégançon - Côtes de Provence Blanc (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 58.00},
    {"nom": "Domaine Vincent Girardin - Meursault (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 95.00},
    {"nom": "Domaine Perrin - Côtes du Rhône Rouge (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 38.00},
    {"nom": "Secret de Lunès - Pinot Noir (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 40.00},
    {"nom": "Vignobles Marrenon - Luberon Rouge (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 48.00},
    {"nom": "Domaine Vincent Girardin - Bourgogne (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 85.00},
    
    # Champagnes (75cl)
    {"nom": "Louis Roederer - Brut Premier (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 75.00},
    {"nom": "Veuve Clicquot - Yellow Label (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 80.00},
    {"nom": "Moët & Chandon - Imperial Brut (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 70.00},
    {"nom": "Ruinart - Blanc de Blancs (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 95.00},
    {"nom": "Louis Roederer - Cristal (Bouteille)", "categorie": "Boissons", "unite": "bouteille", "reference_price": 350.00},
    
    # Mixeurs et jus
    {"nom": "Ginger Beer", "categorie": "Boissons", "unite": "L", "reference_price": 3.50},
    {"nom": "Jus de Cranberry", "categorie": "Boissons", "unite": "L", "reference_price": 4.00},
    {"nom": "Jus d'orange", "categorie": "Boissons", "unite": "L", "reference_price": 3.00},
    {"nom": "Purée de Passion", "categorie": "Boissons", "unite": "L", "reference_price": 8.00},
    {"nom": "Crème de fraise", "categorie": "Boissons", "unite": "L", "reference_price": 10.00},
    {"nom": "Crème de pêche", "categorie": "Boissons", "unite": "L", "reference_price": 10.00},
    {"nom": "Menthe fraîche", "categorie": "Épices", "unite": "kg", "reference_price": 15.00},
]

# Préparations réelles
REAL_PREPARATIONS = [
    {
        "nom": "Tomates cerises lavées et coupées",
        "produit_brut": "Tomates cerises",
        "forme_decoupe": "carré",
        "quantite_produit_brut": 1.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 0.85,
        "unite_preparee": "kg",
        "perte": 0.15,
        "perte_pourcentage": 15.0,
        "nombre_portions": 8,
        "taille_portion": 0.106,
        "unite_portion": "kg",
        "dlc_jours": 2
    },
    {
        "nom": "Légumes grillés (courgettes, aubergines)",
        "produit_brut": "Courgettes",
        "forme_decoupe": "émincé",
        "quantite_produit_brut": 2.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 1.6,
        "unite_preparee": "kg",
        "perte": 0.4,
        "perte_pourcentage": 20.0,
        "nombre_portions": 16,
        "taille_portion": 0.1,
        "unite_portion": "kg",
        "dlc_jours": 3
    },
    {
        "nom": "Pâte à crêpes",
        "produit_brut": "Farine",
        "forme_decoupe": "mélange",
        "quantite_produit_brut": 0.5,  # 500g farine
        "unite_produit_brut": "kg",
        "quantite_preparee": 1.5,  # 1.5L de pâte
        "unite_preparee": "L",
        "perte": 0.0,
        "perte_pourcentage": 0.0,
        "nombre_portions": 12,
        "taille_portion": 0.125,  # 125ml par crêpe
        "unite_portion": "L",
        "dlc_jours": 2,
        "ingredients_supplementaires": [
            {"nom": "Lait", "quantite": 0.75, "unite": "L"},
            {"nom": "Œufs", "quantite": 0.2, "unite": "kg"},  # ~4 œufs
            {"nom": "Sucre", "quantite": 0.05, "unite": "kg"},
            {"nom": "Grand Marnier", "quantite": 0.03, "unite": "L"}
        ]
    },
    {
        "nom": "Sauce tomate maison",
        "produit_brut": "Tomates cerises",
        "forme_decoupe": "concassé",
        "quantite_produit_brut": 2.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 1.5,
        "unite_preparee": "L",
        "perte": 0.5,
        "perte_pourcentage": 25.0,
        "nombre_portions": 15,
        "taille_portion": 0.1,  # 100ml par portion
        "unite_portion": "L",
        "dlc_jours": 5,
        "ingredients_supplementaires": [
            {"nom": "Thym", "quantite": 1, "unite": "botte"},
            {"nom": "Romarin", "quantite": 1, "unite": "botte"},
            {"nom": "Sel", "quantite": 0.02, "unite": "kg"},
            {"nom": "Poivre", "quantite": 0.005, "unite": "kg"}
        ]
    },
    # NOUVELLES PRÉPARATIONS AJOUTÉES
    {
        "nom": "Pommes de terre épluchées et coupées",
        "produit_brut": "Pommes de terre",
        "forme_decoupe": "carré",
        "quantite_produit_brut": 1.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 0.82,
        "unite_preparee": "kg",
        "perte": 0.18,
        "perte_pourcentage": 18.0,
        "nombre_portions": 8,
        "taille_portion": 0.103,
        "unite_portion": "kg",
        "dlc_jours": 1
    },
    {
        "nom": "Persillade (ail et persil)",
        "produit_brut": "Persil",
        "forme_decoupe": "haché",
        "quantite_produit_brut": 0.2,
        "unite_produit_brut": "kg",
        "quantite_preparee": 0.18,
        "unite_preparee": "kg",
        "perte": 0.02,
        "perte_pourcentage": 10.0,
        "nombre_portions": 20,
        "taille_portion": 0.009,
        "unite_portion": "kg",
        "dlc_jours": 1,
        "ingredients_supplementaires": [
            {"nom": "Ail", "quantite": 0.05, "unite": "kg"}
        ]
    },
    {
        "nom": "Purée de pommes de terre",
        "produit_brut": "Pommes de terre",
        "forme_decoupe": "purée",
        "quantite_produit_brut": 2.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 2.2,
        "unite_preparee": "kg",
        "perte": 0.2,
        "perte_pourcentage": 10.0,
        "nombre_portions": 15,
        "taille_portion": 0.147,
        "unite_portion": "kg",
        "dlc_jours": 2,
        "ingredients_supplementaires": [
            {"nom": "Beurre", "quantite": 0.15, "unite": "kg"},
            {"nom": "Lait", "quantite": 0.3, "unite": "L"}
        ]
    },
    {
        "nom": "Oignons émincés caramélisés",
        "produit_brut": "Oignons",
        "forme_decoupe": "émincé",
        "quantite_produit_brut": 1.0,
        "unite_produit_brut": "kg",
        "quantite_preparee": 0.35,
        "unite_preparee": "kg",
        "perte": 0.65,
        "perte_pourcentage": 65.0,
        "nombre_portions": 7,
        "taille_portion": 0.05,
        "unite_portion": "kg",
        "dlc_jours": 3
    }
]

# Productions (recettes) réelles - CARTE COMPLÈTE
REAL_RECETTES = [
    # ENTRÉES - CARTE COMPLÈTE
    {
        "nom": "Supions en persillade de Mamie",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 26.00,
        "ingredients": [
            {"nom": "Supions", "quantite": 0.4, "unite": "kg"},
            {"nom": "Persillade (ail et persil)", "quantite": 0.04, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "Moules gratinées en persillade",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 18.00,
        "ingredients": [
            {"nom": "Moules", "quantite": 1.2, "unite": "kg"},
            {"nom": "Persillade (ail et persil)", "quantite": 0.04, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "Saint-Jacques façon Mr Paul Bocuse",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 27.00,
        "ingredients": [
            {"nom": "Saint-Jacques", "quantite": 0.4, "unite": "kg"},
            {"nom": "Beurre", "quantite": 0.05, "unite": "kg"}
        ]
    },
    {
        "nom": "Le crabe sublimé d'Augustine",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 29.00,
        "ingredients": [
            {"nom": "Crabe", "quantite": 0.8, "unite": "kg"}
        ]
    },
    {
        "nom": "Les panisses de l'Estaque",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 15.00,
        "ingredients": [
            {"nom": "Farine de pois chiche", "quantite": 0.25, "unite": "kg"},
            {"nom": "Huile d'olive", "quantite": 0.1, "unite": "L"}
        ]
    },
    {
        "nom": "Le pâté en croûte de Mamet Augustine",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 18.00,
        "ingredients": [
            {"nom": "Veau (escalope)", "quantite": 0.3, "unite": "kg"},
            {"nom": "Pâte feuilletée", "quantite": 0.4, "unite": "kg"}
        ]
    },
    {
        "nom": "La soupe à l'oignon, foie gras & Comté",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 19.00,
        "ingredients": [
            {"nom": "Oignons émincés caramélisés", "quantite": 0.21, "unite": "kg", "ingredient_type": "preparation"},
            {"nom": "Foie gras de canard", "quantite": 0.1, "unite": "kg"},
            {"nom": "Comté", "quantite": 0.1, "unite": "kg"}
        ]
    },
    {
        "nom": "Cuisses de grenouilles à la française",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 24.00,
        "ingredients": [
            {"nom": "Cuisses de grenouilles", "quantite": 0.6, "unite": "kg"},
            {"nom": "Persillade (ail et persil)", "quantite": 0.04, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "La fameuse poêlée de sanguins des chasseurs",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 23.00,
        "ingredients": [
            {"nom": "Sanguins (gibier)", "quantite": 0.8, "unite": "kg"},
            {"nom": "Oignons émincés caramélisés", "quantite": 0.07, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "Foie gras de canard IGP",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 28.00,
        "ingredients": [
            {"nom": "Foie gras de canard", "quantite": 0.4, "unite": "kg"}
        ]
    },
    
    # PLATS - CARTE COMPLÈTE
    {
        "nom": "Pêche du jour au four façon grand-mère",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 33.00,
        "ingredients": [
            {"nom": "Poisson du jour", "quantite": 1.2, "unite": "kg"},
            {"nom": "Pommes de terre épluchées et coupées", "quantite": 0.35, "unite": "kg", "ingredient_type": "preparation"},
            {"nom": "Tomates cerises lavées et coupées", "quantite": 0.17, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "La sole meunière, l'excellence",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 48.00,
        "ingredients": [
            {"nom": "Sole", "quantite": 1.2, "unite": "kg"},
            {"nom": "Beurre", "quantite": 0.1, "unite": "kg"}
        ]
    },
    {
        "nom": "Linguine aux palourdes & sauce à l'ail",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 29.00,
        "ingredients": [
            {"nom": "Linguine", "quantite": 0.4, "unite": "kg"},
            {"nom": "Palourdes", "quantite": 0.8, "unite": "kg"},
            {"nom": "Persillade (ail et persil)", "quantite": 0.036, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "Rigatoni à la truffe fraîche de Bourgogne",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 35.00,
        "ingredients": [
            {"nom": "Rigatoni", "quantite": 0.4, "unite": "kg"},
            {"nom": "Parmesan", "quantite": 0.08, "unite": "kg"}
        ]
    },
    {
        "nom": "Gnocchi d'Augustine sauce napolitaine",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 25.00,
        "ingredients": [
            {"nom": "Gnocchi", "quantite": 0.6, "unite": "kg"},
            {"nom": "Sauce tomate maison", "quantite": 0.3, "unite": "L", "ingredient_type": "preparation"},
            {"nom": "Basilic frais", "quantite": 1, "unite": "botte"}
        ]
    },
    {
        "nom": "Nos farcis provençaux",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 31.00,
        "ingredients": [
            {"nom": "Légumes grillés (courgettes, aubergines)", "quantite": 0.48, "unite": "kg", "ingredient_type": "preparation"},
            {"nom": "Tomates cerises lavées et coupées", "quantite": 0.26, "unite": "kg", "ingredient_type": "preparation"}
        ]
    },
    {
        "nom": "La merveilleuse souris d'agneau",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 36.00,
        "ingredients": [
            {"nom": "Agneau (souris)", "quantite": 1.2, "unite": "kg"},
            {"nom": "Ail", "quantite": 0.03, "unite": "kg"}
        ]
    },
    {
        "nom": "Le fameux boeuf Wellington à la truffe",
        "categorie": "Plat",
        "portions": 2,
        "prix_vente": 56.00,
        "ingredients": [
            {"nom": "Bœuf (filet)", "quantite": 0.4, "unite": "kg"}
        ]
    },
    {
        "nom": "Magret de canard de la ferme du Puntoun",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 42.00,
        "ingredients": [
            {"nom": "Magret de canard", "quantite": 0.8, "unite": "kg"}
        ]
    },
    {
        "nom": "Côte de boeuf Aubrac",
        "categorie": "Plat",
        "portions": 2,
        "prix_vente": 110.00,
        "ingredients": [
            {"nom": "Bœuf (filet)", "quantite": 1.0, "unite": "kg"}
        ]
    },
    {
        "nom": "Jarret de veau du Sud Ouest",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 80.00,
        "ingredients": [
            {"nom": "Veau (escalope)", "quantite": 1.5, "unite": "kg"}
        ]
    },
    {
        "nom": "Écrasé de pomme de terre",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 6.00,
        "ingredients": [
            {"nom": "Pommes de terre épluchées et coupées", "quantite": 0.66, "unite": "kg", "ingredient_type": "preparation"},
            {"nom": "Beurre", "quantite": 0.05, "unite": "kg"}
        ]
    },
    {
        "nom": "Poêlée de légumes",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 6.00,
        "ingredients": [
            {"nom": "Légumes grillés (courgettes, aubergines)", "quantite": 0.8, "unite": "kg", "ingredient_type": "preparation"},
            {"nom": "Poivrons", "quantite": 0.4, "unite": "kg"}
        ]
    },
    {
        "nom": "Purée à la truffe (Uncinatum)",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 11.00,
        "ingredients": [
            {"nom": "Purée de pommes de terre", "quantite": 0.59, "unite": "kg", "ingredient_type": "preparation"},
            {"nom": "Truffe (Uncinatum)", "quantite": 0.015, "unite": "kg"}
        ]
    },
    {
        "nom": "Gnocchi artisanaux au beurre",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 11.00,
        "ingredients": [
            {"nom": "Gnocchi", "quantite": 0.6, "unite": "kg"},
            {"nom": "Beurre", "quantite": 0.08, "unite": "kg"}
        ]
    },
    
    # DESSERTS - CARTE COMPLÈTE
    {
        "nom": "La glace yaourt dessert signature",
        "categorie": "Dessert",
        "portions": 4,
        "prix_vente": 13.00,
        "ingredients": [
            {"nom": "Yaourt", "quantite": 0.5, "unite": "kg"}
        ]
    },
    {
        "nom": "Tiramisu de Mamet",
        "categorie": "Dessert",
        "portions": 6,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Mozzarella", "quantite": 0.3, "unite": "kg"}
        ]
    },
    {
        "nom": "Crêpe Suzette recette de 1961",
        "categorie": "Dessert",
        "portions": 4,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Pâte à crêpes", "quantite": 0.5, "unite": "L", "ingredient_type": "preparation"},
            {"nom": "Jus d'orange", "quantite": 0.2, "unite": "L"},
            {"nom": "Beurre", "quantite": 0.05, "unite": "kg"},
            {"nom": "Grand Marnier", "quantite": 0.03, "unite": "L"}
        ]
    },
    {
        "nom": "Mont Blanc classique",
        "categorie": "Dessert",
        "portions": 4,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Marrons", "quantite": 0.4, "unite": "kg"},
            {"nom": "Crème fraîche", "quantite": 0.2, "unite": "L"}
        ]
    },
    
    # VINS AU VERRE (aussi disponibles en bouteille)
    {
        "nom": "Château de Fonscolombe - Coteaux d'Aix (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 9.50,
        "ingredients": []
    },
    {
        "nom": "Domaine de La Ferme Blanche - Cassis Rosé (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Guillaman - Côtes de Gascogne Rosé (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 9.00,
        "ingredients": []
    },
    {
        "nom": "Vignobles Marrenon - Luberon Rosé (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 9.00,
        "ingredients": []
    },
    {
        "nom": "MamET Les vieilles vignes - IGP Méditerranée Blanc (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 9.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Perrin - Côtes du Rhône Rouge (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 8.50,
        "ingredients": []
    },
    {
        "nom": "Secret de Lunès - Pinot Noir (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 9.00,
        "ingredients": []
    },
    {
        "nom": "Vignobles Marrenon - Luberon Rouge (Verre)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 11.00,
        "ingredients": []
    },
    
    # VINS EN BOUTEILLE (75cl) - ROSÉS
    {
        "nom": "Château de Fonscolombe - Coteaux d'Aix (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 26.00,
        "ingredients": []
    },
    {
        "nom": "Domaine de La Ferme Blanche - Cassis Rosé (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 32.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Guillaman - Côtes de Gascogne Rosé (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 25.00,
        "ingredients": []
    },
    {
        "nom": "Vignobles Marrenon - Luberon Rosé (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 25.00,
        "ingredients": []
    },
    {
        "nom": "Clos real - Côtes de Provence Biodynamie (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 45.00,
        "ingredients": []
    },
    
    # VINS EN BOUTEILLE (75cl) - BLANCS
    {
        "nom": "MamET Les vieilles vignes - IGP Méditerranée (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 25.00,
        "ingredients": []
    },
    {
        "nom": "Domaine du Murinais Blanc (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 52.00,
        "ingredients": []
    },
    {
        "nom": "Domaine de La Ferme Blanche - Cassis Blanc (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 46.00,
        "ingredients": []
    },
    {
        "nom": "Vignobles Marrenon - Luberon Blanc (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 34.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Guillaman - Côtes de Gascogne Blanc (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 35.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Roc de l'Abbaye - Pouilly Fumé (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 58.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Vincent Girardin - Meursault (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 109.00,
        "ingredients": []
    },
    
    # VINS EN BOUTEILLE (75cl) - ROUGES
    {
        "nom": "Domaine Perrin - Côtes du Rhône (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 23.00,
        "ingredients": []
    },
    {
        "nom": "Secret de Lunès - Pinot Noir (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 24.00,
        "ingredients": []
    },
    {
        "nom": "Vignobles Marrenon - Luberon Rouge (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 27.00,
        "ingredients": []
    },
    {
        "nom": "Secret de Lunès - Pays d'Oc (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 36.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Perrin - Côtes du Rhône 75cl (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 44.00,
        "ingredients": []
    },
    {
        "nom": "Domaine de La Garenne - Bandol (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 54.00,
        "ingredients": []
    },
    {
        "nom": "Domaine des Evigneaux - Rasteau (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 56.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Vincent Girardin - Bourgogne (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 67.00,
        "ingredients": []
    },
    {
        "nom": "Château Maucoil - Châteauneuf du Pape (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 89.00,
        "ingredients": []
    },
    {
        "nom": "Domaine Yves Cuilleron - Côte Rôtie (Bouteille)",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 97.00,
        "ingredients": []
    },
    
    # CHAMPAGNES (75cl)
    {
        "nom": "Mumm Cordon Rouge - Blanc de Blanc",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 110.00,
        "ingredients": []
    },
    {
        "nom": "Perrier Jouët - Brut",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 160.00,
        "ingredients": []
    },
    {
        "nom": "Dom Pérignon - Brut",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 350.00,
        "ingredients": []
    },
    
    # COCKTAILS & BAR
    {
        "nom": "Moscow Mule",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Vodka", "quantite": 0.05, "unite": "L"},
            {"nom": "Ginger Beer", "quantite": 0.15, "unite": "L"}
        ]
    },
    {
        "nom": "Cosmopolitain",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Vodka", "quantite": 0.05, "unite": "L"},
            {"nom": "Triple Sec", "quantite": 0.02, "unite": "L"},
            {"nom": "Jus de Cranberry", "quantite": 0.05, "unite": "L"}
        ]
    },
    {
        "nom": "Caïpi Passion",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Vodka", "quantite": 0.05, "unite": "L"},
            {"nom": "Purée de Passion", "quantite": 0.03, "unite": "L"}
        ]
    },
    {
        "nom": "Spritz d'Augustine",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 11.00,
        "ingredients": [
            {"nom": "Apérol", "quantite": 0.06, "unite": "L"},
            {"nom": "Jus d'orange", "quantite": 0.05, "unite": "L"},
            {"nom": "Prosecco", "quantite": 0.1, "unite": "L"}
        ]
    },
    {
        "nom": "Mojito de Mamie",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Rhum", "quantite": 0.05, "unite": "L"},
            {"nom": "Menthe fraîche", "quantite": 0.01, "unite": "kg"}
        ]
    },
    {
        "nom": "Le Rossini Mio",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Prosecco", "quantite": 0.1, "unite": "L"},
            {"nom": "Crème de fraise", "quantite": 0.03, "unite": "L"}
        ]
    },
    {
        "nom": "Le Bellini",
        "categorie": "Bar",
        "portions": 1,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Prosecco", "quantite": 0.1, "unite": "L"},
            {"nom": "Crème de pêche", "quantite": 0.03, "unite": "L"}
        ]
    }
]
