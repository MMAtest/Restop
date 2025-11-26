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
    {"nom": "Thym", "categorie": "Épices", "unite": "botte", "reference_price": 2.00},
    {"nom": "Romarin", "categorie": "Épices", "unite": "botte", "reference_price": 2.00},
    
    # Huiles et condiments
    {"nom": "Huile d'olive", "categorie": "Épicerie", "unite": "L", "reference_price": 12.00},
    {"nom": "Vinaigre balsamique", "categorie": "Épicerie", "unite": "L", "reference_price": 8.50},
    
    # Bar et spiritueux
    {"nom": "Vodka", "categorie": "Boissons", "unite": "L", "reference_price": 25.00},
    {"nom": "Rhum", "categorie": "Boissons", "unite": "L", "reference_price": 28.00},
    {"nom": "Apérol", "categorie": "Boissons", "unite": "L", "reference_price": 18.00},
    {"nom": "Prosecco", "categorie": "Boissons", "unite": "L", "reference_price": 12.00},
    {"nom": "Triple Sec", "categorie": "Boissons", "unite": "L", "reference_price": 15.00},
    
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

# Productions (recettes) réelles - CARTE COMPLÈTE
REAL_RECETTES = [
    # ENTRÉES
    {
        "nom": "Supions en persillade",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 14.50,
        "ingredients": [
            {"nom": "Supions", "quantite": 0.4, "unite": "kg"},
            {"nom": "Persil", "quantite": 1, "unite": "botte"},
            {"nom": "Ail", "quantite": 0.02, "unite": "kg"}
        ]
    },
    {
        "nom": "Rougets grillés",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 16.50,
        "ingredients": [
            {"nom": "Rougets", "quantite": 0.8, "unite": "kg"},
            {"nom": "Basilic frais", "quantite": 1, "unite": "botte"}
        ]
    },
    {
        "nom": "Salade de saison",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 12.50,
        "ingredients": [
            {"nom": "Tomates cerises", "quantite": 0.3, "unite": "kg"},
            {"nom": "Mozzarella", "quantite": 0.2, "unite": "kg"},
            {"nom": "Basilic frais", "quantite": 1, "unite": "botte"}
        ]
    },
    {
        "nom": "Fleurs de courgettes farcies",
        "categorie": "Entrée",
        "portions": 4,
        "prix_vente": 15.00,
        "ingredients": [
            {"nom": "Courgettes", "quantite": 0.4, "unite": "kg"},
            {"nom": "Brocciu", "quantite": 0.15, "unite": "kg"}
        ]
    },
    
    # PLATS
    {
        "nom": "Linguine aux palourdes",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 22.00,
        "ingredients": [
            {"nom": "Linguine", "quantite": 0.4, "unite": "kg"},
            {"nom": "Palourdes", "quantite": 0.8, "unite": "kg"},
            {"nom": "Ail", "quantite": 0.015, "unite": "kg"},
            {"nom": "Persil", "quantite": 1, "unite": "botte"}
        ]
    },
    {
        "nom": "Rigatoni à la truffe",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 28.50,
        "ingredients": [
            {"nom": "Rigatoni", "quantite": 0.4, "unite": "kg"},
            {"nom": "Parmesan", "quantite": 0.08, "unite": "kg"}
        ]
    },
    {
        "nom": "Bœuf Wellington",
        "categorie": "Plat",
        "portions": 2,
        "prix_vente": 36.00,
        "ingredients": [
            {"nom": "Bœuf (filet)", "quantite": 0.4, "unite": "kg"}
        ]
    },
    {
        "nom": "Souris d'agneau confite",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 32.00,
        "ingredients": [
            {"nom": "Agneau (souris)", "quantite": 1.2, "unite": "kg"},
            {"nom": "Ail", "quantite": 0.03, "unite": "kg"}
        ]
    },
    {
        "nom": "Veau à la milanaise",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 26.00,
        "ingredients": [
            {"nom": "Veau (escalope)", "quantite": 0.6, "unite": "kg"},
            {"nom": "Parmesan", "quantite": 0.05, "unite": "kg"}
        ]
    },
    {
        "nom": "Daurade grillée",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 28.00,
        "ingredients": [
            {"nom": "Daurade", "quantite": 1.2, "unite": "kg"},
            {"nom": "Basilic frais", "quantite": 1, "unite": "botte"}
        ]
    },
    {
        "nom": "Légumes grillés du moment",
        "categorie": "Plat",
        "portions": 4,
        "prix_vente": 18.50,
        "ingredients": [
            {"nom": "Courgettes", "quantite": 0.5, "unite": "kg"},
            {"nom": "Aubergines", "quantite": 0.5, "unite": "kg"},
            {"nom": "Poivrons", "quantite": 0.4, "unite": "kg"}
        ]
    },
    
    # DESSERTS
    {
        "nom": "Tiramisù maison",
        "categorie": "Dessert",
        "portions": 6,
        "prix_vente": 12.00,
        "ingredients": [
            {"nom": "Mozzarella", "quantite": 0.3, "unite": "kg"}  # Mascarpone simplifié
        ]
    },
    {
        "nom": "Panna cotta",
        "categorie": "Dessert",
        "portions": 6,
        "prix_vente": 9.50,
        "ingredients": [
            {"nom": "Mozzarella", "quantite": 0.2, "unite": "kg"}
        ]
    },
    {
        "nom": "Plateau de fromages corses",
        "categorie": "Dessert",
        "portions": 4,
        "prix_vente": 16.00,
        "ingredients": [
            {"nom": "Brocciu", "quantite": 0.2, "unite": "kg"},
            {"nom": "Parmesan", "quantite": 0.15, "unite": "kg"}
        ]
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
