"""
Données réelles du restaurant La Table d'Augustine
À utiliser pour restaurer les vraies données du restaurant
"""

# Fournisseurs réels
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
    }
]

# Produits réels (ingrédients)
REAL_PRODUITS = [
    # Poissons
    {"nom": "Supions", "categorie": "Poissons", "unite": "kg", "reference_price": 18.50},
    {"nom": "Palourdes", "categorie": "Poissons", "unite": "kg", "reference_price": 12.00},
    {"nom": "Rougets", "categorie": "Poissons", "unite": "kg", "reference_price": 22.00},
    {"nom": "Daurade", "categorie": "Poissons", "unite": "kg", "reference_price": 16.00},
    
    # Viandes
    {"nom": "Bœuf (filet)", "categorie": "Viandes", "unite": "kg", "reference_price": 35.00},
    {"nom": "Veau (escalope)", "categorie": "Viandes", "unite": "kg", "reference_price": 28.00},
    {"nom": "Agneau (souris)", "categorie": "Viandes", "unite": "kg", "reference_price": 24.00},
    
    # Légumes
    {"nom": "Tomates cerises", "categorie": "Légumes", "unite": "kg", "reference_price": 4.50},
    {"nom": "Courgettes", "categorie": "Légumes", "unite": "kg", "reference_price": 2.80},
    {"nom": "Aubergines", "categorie": "Légumes", "unite": "kg", "reference_price": 3.20},
    {"nom": "Poivrons", "categorie": "Légumes", "unite": "kg", "reference_price": 3.50},
    
    # Pâtes et féculents
    {"nom": "Linguine", "categorie": "Épicerie", "unite": "kg", "reference_price": 3.80},
    {"nom": "Rigatoni", "categorie": "Épicerie", "unite": "kg", "reference_price": 3.90},
    
    # Produits laitiers
    {"nom": "Parmesan", "categorie": "Crêmerie", "unite": "kg", "reference_price": 32.00},
    {"nom": "Mozzarella", "categorie": "Crêmerie", "unite": "kg", "reference_price": 8.50},
    {"nom": "Brocciu", "categorie": "Crêmerie", "unite": "kg", "reference_price": 15.00},
    
    # Épices et aromates
    {"nom": "Basilic frais", "categorie": "Épices", "unite": "botte", "reference_price": 2.50},
    {"nom": "Persil", "categorie": "Épices", "unite": "botte", "reference_price": 1.80},
    {"nom": "Ail", "categorie": "Épices", "unite": "kg", "reference_price": 6.00},
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
        "taille_portion": 0.106,  # 106g par portion
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
        "taille_portion": 0.1,  # 100g par portion
        "unite_portion": "kg",
        "dlc_jours": 3
    }
]

# Productions (recettes) réelles
REAL_RECETTES = [
    {
        "nom": "Supions en persillade",
        "categorie": "Entrée",
        "portions": 4,
        "ingredients": [
            {"nom": "Supions", "quantite": 0.4, "unite": "kg"},
            {"nom": "Persil", "quantite": 1, "unite": "botte"},
            {"nom": "Ail", "quantite": 0.02, "unite": "kg"}
        ]
    },
    {
        "nom": "Linguine aux palourdes",
        "categorie": "Plat",
        "portions": 4,
        "ingredients": [
            {"nom": "Linguine", "quantite": 0.4, "unite": "kg"},
            {"nom": "Palourdes", "quantite": 0.8, "unite": "kg"},
            {"nom": "Ail", "quantite": 0.015, "unite": "kg"},
            {"nom": "Persil", "quantite": 1, "unite": "botte"}
        ]
    },
    {
        "nom": "Bœuf Wellington",
        "categorie": "Plat",
        "portions": 2,
        "ingredients": [
            {"nom": "Bœuf (filet)", "quantite": 0.4, "unite": "kg"}
        ]
    },
    {
        "nom": "Rigatoni à la truffe",
        "categorie": "Plat",
        "portions": 4,
        "ingredients": [
            {"nom": "Rigatoni", "quantite": 0.4, "unite": "kg"},
            {"nom": "Parmesan", "quantite": 0.08, "unite": "kg"}
        ]
    }
]
