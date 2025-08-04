from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import io
import pandas as pd
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models pour la gestion des stocks
class Fournisseur(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FournisseurCreate(BaseModel):
    nom: str
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None

class Produit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    unite: str  # kg, L, pièce, etc.
    prix_achat: Optional[float] = None
    fournisseur_id: Optional[str] = None
    fournisseur_nom: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProduitCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    unite: str
    prix_achat: Optional[float] = None
    fournisseur_id: Optional[str] = None

class Stock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    produit_id: str
    produit_nom: Optional[str] = None
    quantite_actuelle: float
    quantite_min: float = 0.0
    quantite_max: Optional[float] = None
    derniere_maj: datetime = Field(default_factory=datetime.utcnow)

class StockCreate(BaseModel):
    produit_id: str
    quantite_actuelle: float
    quantite_min: float = 0.0
    quantite_max: Optional[float] = None

class StockUpdate(BaseModel):
    quantite_actuelle: Optional[float] = None
    quantite_min: Optional[float] = None
    quantite_max: Optional[float] = None

class MouvementStock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    produit_id: str
    produit_nom: Optional[str] = None
    type: str  # "entree", "sortie", "ajustement"
    quantite: float
    date: datetime = Field(default_factory=datetime.utcnow)
    reference: Optional[str] = None
    fournisseur_id: Optional[str] = None
    commentaire: Optional[str] = None

class MouvementCreate(BaseModel):
    produit_id: str
    type: str
    quantite: float
    reference: Optional[str] = None
    fournisseur_id: Optional[str] = None
    commentaire: Optional[str] = None

# Models pour la gestion des recettes
class RecetteIngredient(BaseModel):
    produit_id: str
    produit_nom: Optional[str] = None
    quantite: float
    unite: str

class Recette(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None  # "entrée", "plat", "dessert", "boisson"
    portions: int  # Nombre de portions que la recette produit
    temps_preparation: Optional[int] = None  # en minutes
    instructions: Optional[str] = None
    prix_vente: Optional[float] = None
    ingredients: List[RecetteIngredient] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RecetteCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    portions: int
    temps_preparation: Optional[int] = None
    instructions: Optional[str] = None
    prix_vente: Optional[float] = None
    ingredients: List[RecetteIngredient] = []

class RecetteUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    categorie: Optional[str] = None
    portions: Optional[int] = None
    temps_preparation: Optional[int] = None
    instructions: Optional[str] = None
    prix_vente: Optional[float] = None
    ingredients: Optional[List[RecetteIngredient]] = None

# Routes pour les fournisseurs
@api_router.post("/fournisseurs", response_model=Fournisseur)
async def create_fournisseur(fournisseur: FournisseurCreate):
    fournisseur_dict = fournisseur.dict()
    fournisseur_obj = Fournisseur(**fournisseur_dict)
    await db.fournisseurs.insert_one(fournisseur_obj.dict())
    return fournisseur_obj

@api_router.get("/fournisseurs", response_model=List[Fournisseur])
async def get_fournisseurs():
    fournisseurs = await db.fournisseurs.find().to_list(1000)
    return [Fournisseur(**f) for f in fournisseurs]

@api_router.get("/fournisseurs/{fournisseur_id}", response_model=Fournisseur)
async def get_fournisseur(fournisseur_id: str):
    fournisseur = await db.fournisseurs.find_one({"id": fournisseur_id})
    if not fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return Fournisseur(**fournisseur)

@api_router.put("/fournisseurs/{fournisseur_id}", response_model=Fournisseur)
async def update_fournisseur(fournisseur_id: str, fournisseur: FournisseurCreate):
    result = await db.fournisseurs.update_one(
        {"id": fournisseur_id},
        {"$set": fournisseur.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    
    updated_fournisseur = await db.fournisseurs.find_one({"id": fournisseur_id})
    return Fournisseur(**updated_fournisseur)

@api_router.delete("/fournisseurs/{fournisseur_id}")
async def delete_fournisseur(fournisseur_id: str):
    result = await db.fournisseurs.delete_one({"id": fournisseur_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return {"message": "Fournisseur supprimé"}

# Routes pour les produits
@api_router.post("/produits", response_model=Produit)
async def create_produit(produit: ProduitCreate):
    produit_dict = produit.dict()
    
    # Récupérer le nom du fournisseur si spécifié
    if produit.fournisseur_id:
        fournisseur = await db.fournisseurs.find_one({"id": produit.fournisseur_id})
        if fournisseur:
            produit_dict["fournisseur_nom"] = fournisseur["nom"]
    
    produit_obj = Produit(**produit_dict)
    await db.produits.insert_one(produit_obj.dict())
    
    # Créer automatiquement une entrée stock à 0
    stock_obj = Stock(produit_id=produit_obj.id, produit_nom=produit_obj.nom, quantite_actuelle=0.0)
    await db.stocks.insert_one(stock_obj.dict())
    
    return produit_obj

@api_router.get("/produits", response_model=List[Produit])
async def get_produits():
    produits = await db.produits.find().to_list(1000)
    return [Produit(**p) for p in produits]

@api_router.get("/produits/{produit_id}", response_model=Produit)
async def get_produit(produit_id: str):
    produit = await db.produits.find_one({"id": produit_id})
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return Produit(**produit)

@api_router.put("/produits/{produit_id}", response_model=Produit)
async def update_produit(produit_id: str, produit: ProduitCreate):
    produit_dict = produit.dict()
    
    # Récupérer le nom du fournisseur si spécifié
    if produit.fournisseur_id:
        fournisseur = await db.fournisseurs.find_one({"id": produit.fournisseur_id})
        if fournisseur:
            produit_dict["fournisseur_nom"] = fournisseur["nom"]
    
    result = await db.produits.update_one(
        {"id": produit_id},
        {"$set": produit_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    updated_produit = await db.produits.find_one({"id": produit_id})
    
    # Mettre à jour le nom du produit dans le stock
    await db.stocks.update_one(
        {"produit_id": produit_id},
        {"$set": {"produit_nom": updated_produit["nom"]}}
    )
    
    return Produit(**updated_produit)

@api_router.delete("/produits/{produit_id}")
async def delete_produit(produit_id: str):
    # Supprimer aussi le stock associé
    await db.stocks.delete_one({"produit_id": produit_id})
    await db.mouvements_stock.delete_many({"produit_id": produit_id})
    
    result = await db.produits.delete_one({"id": produit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"message": "Produit supprimé"}

# Routes pour les stocks
@api_router.get("/stocks", response_model=List[Stock])
async def get_stocks():
    stocks = await db.stocks.find().to_list(1000)
    return [Stock(**s) for s in stocks]

@api_router.get("/stocks/{produit_id}", response_model=Stock)
async def get_stock(produit_id: str):
    stock = await db.stocks.find_one({"produit_id": produit_id})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock non trouvé")
    return Stock(**stock)

@api_router.put("/stocks/{produit_id}", response_model=Stock)
async def update_stock(produit_id: str, stock_update: StockUpdate):
    update_dict = {k: v for k, v in stock_update.dict().items() if v is not None}
    update_dict["derniere_maj"] = datetime.utcnow()
    
    result = await db.stocks.update_one(
        {"produit_id": produit_id},
        {"$set": update_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Stock non trouvé")
    
    updated_stock = await db.stocks.find_one({"produit_id": produit_id})
    return Stock(**updated_stock)

# Routes pour les mouvements de stock
@api_router.post("/mouvements", response_model=MouvementStock)
async def create_mouvement(mouvement: MouvementCreate):
    mouvement_dict = mouvement.dict()
    
    # Récupérer le nom du produit
    produit = await db.produits.find_one({"id": mouvement.produit_id})
    if produit:
        mouvement_dict["produit_nom"] = produit["nom"]
    
    mouvement_obj = MouvementStock(**mouvement_dict)
    await db.mouvements_stock.insert_one(mouvement_obj.dict())
    
    # Mettre à jour le stock
    stock = await db.stocks.find_one({"produit_id": mouvement.produit_id})
    if stock:
        nouvelle_quantite = stock["quantite_actuelle"]
        if mouvement.type == "entree":
            nouvelle_quantite += mouvement.quantite
        elif mouvement.type == "sortie":
            nouvelle_quantite -= mouvement.quantite
        elif mouvement.type == "ajustement":
            nouvelle_quantite = mouvement.quantite
        
        await db.stocks.update_one(
            {"produit_id": mouvement.produit_id},
            {"$set": {"quantite_actuelle": max(0, nouvelle_quantite), "derniere_maj": datetime.utcnow()}}
        )
    
    return mouvement_obj

@api_router.get("/mouvements", response_model=List[MouvementStock])
async def get_mouvements():
    mouvements = await db.mouvements_stock.find().sort("date", -1).to_list(1000)
    return [MouvementStock(**m) for m in mouvements]

# Routes pour les recettes
@api_router.post("/recettes", response_model=Recette)
async def create_recette(recette: RecetteCreate):
    # Enrichir les ingrédients avec les noms des produits
    enriched_ingredients = []
    for ingredient in recette.ingredients:
        produit = await db.produits.find_one({"id": ingredient.produit_id})
        if produit:
            ingredient_dict = ingredient.dict()
            ingredient_dict["produit_nom"] = produit["nom"]
            enriched_ingredients.append(RecetteIngredient(**ingredient_dict))
        else:
            enriched_ingredients.append(ingredient)
    
    recette_dict = recette.dict()
    recette_dict["ingredients"] = [ing.dict() for ing in enriched_ingredients]
    
    recette_obj = Recette(**recette_dict)
    await db.recettes.insert_one(recette_obj.dict())
    return recette_obj

@api_router.get("/recettes", response_model=List[Recette])
async def get_recettes():
    recettes = await db.recettes.find().to_list(1000)
    return [Recette(**r) for r in recettes]

@api_router.get("/recettes/{recette_id}", response_model=Recette)
async def get_recette(recette_id: str):
    recette = await db.recettes.find_one({"id": recette_id})
    if not recette:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    return Recette(**recette)

@api_router.put("/recettes/{recette_id}", response_model=Recette)
async def update_recette(recette_id: str, recette_update: RecetteUpdate):
    update_dict = {k: v for k, v in recette_update.dict().items() if v is not None}
    
    # Si des ingrédients sont fournis, enrichir avec les noms des produits
    if "ingredients" in update_dict and update_dict["ingredients"]:
        enriched_ingredients = []
        for ingredient in update_dict["ingredients"]:
            if isinstance(ingredient, dict):
                produit = await db.produits.find_one({"id": ingredient.get("produit_id")})
                if produit:
                    ingredient["produit_nom"] = produit["nom"]
                enriched_ingredients.append(ingredient)
            else:
                produit = await db.produits.find_one({"id": ingredient.produit_id})
                if produit:
                    ingredient_dict = ingredient.dict()
                    ingredient_dict["produit_nom"] = produit["nom"]
                    enriched_ingredients.append(ingredient_dict)
        update_dict["ingredients"] = enriched_ingredients
    
    result = await db.recettes.update_one(
        {"id": recette_id},
        {"$set": update_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    
    updated_recette = await db.recettes.find_one({"id": recette_id})
    return Recette(**updated_recette)

@api_router.delete("/recettes/{recette_id}")
async def delete_recette(recette_id: str):
    result = await db.recettes.delete_one({"id": recette_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    return {"message": "Recette supprimée"}

# Calculateur de production de recettes
@api_router.get("/recettes/{recette_id}/production-capacity")
async def get_recipe_production_capacity(recette_id: str):
    """Calculer combien de portions peuvent être produites avec le stock actuel"""
    recette = await db.recettes.find_one({"id": recette_id})
    if not recette:
        raise HTTPException(status_code=404, detail="Recette non trouvée")
    
    # Récupérer tous les stocks des ingrédients
    min_portions = float('inf')
    ingredient_status = []
    
    for ingredient in recette.get("ingredients", []):
        stock = await db.stocks.find_one({"produit_id": ingredient["produit_id"]})
        if stock:
            # Calculer combien de portions possibles avec cet ingrédient
            quantite_disponible = stock["quantite_actuelle"]
            quantite_requise_par_portion = ingredient["quantite"] / recette["portions"]
            
            if quantite_requise_par_portion > 0:
                portions_possibles = int(quantite_disponible / quantite_requise_par_portion)
                min_portions = min(min_portions, portions_possibles)
            else:
                portions_possibles = float('inf')
            
            ingredient_status.append({
                "produit_nom": ingredient.get("produit_nom", "Produit inconnu"),
                "quantite_disponible": quantite_disponible,
                "quantite_requise_par_portion": quantite_requise_par_portion,
                "quantite_requise_total": quantite_requise_par_portion * 1,  # Pour 1 portion
                "portions_possibles": portions_possibles,
                "unite": ingredient["unite"]
            })
        else:
            # Ingrédient non en stock
            min_portions = 0
            ingredient_status.append({
                "produit_nom": ingredient.get("produit_nom", "Produit inconnu"),
                "quantite_disponible": 0,
                "quantite_requise_par_portion": ingredient["quantite"] / recette["portions"],
                "quantite_requise_total": ingredient["quantite"] / recette["portions"],
                "portions_possibles": 0,
                "unite": ingredient["unite"]
            })
    
    if min_portions == float('inf'):
        min_portions = 0
    
    return {
        "recette_nom": recette["nom"],
        "portions_max": max(0, int(min_portions)),
        "ingredients_status": ingredient_status
    }

# Routes pour l'export/import Excel
@api_router.get("/export/stocks")
async def export_stocks():
    # Récupérer toutes les données
    stocks = await db.stocks.find().to_list(1000)
    produits = await db.produits.find().to_list(1000)
    fournisseurs = await db.fournisseurs.find().to_list(1000)
    
    # Créer un dictionnaire pour un accès rapide
    produits_dict = {p["id"]: p for p in produits}
    fournisseurs_dict = {f["id"]: f for f in fournisseurs}
    
    # Préparer les données pour Excel
    data = []
    for stock in stocks:
        produit = produits_dict.get(stock["produit_id"], {})
        fournisseur = fournisseurs_dict.get(produit.get("fournisseur_id"), {})
        
        data.append({
            "Produit ID": stock["produit_id"],
            "Nom Produit": produit.get("nom", ""),
            "Description": produit.get("description", ""),
            "Catégorie": produit.get("categorie", ""),
            "Unité": produit.get("unite", ""),
            "Prix Achat": produit.get("prix_achat", ""),
            "Fournisseur": fournisseur.get("nom", ""),
            "Quantité Actuelle": stock["quantite_actuelle"],
            "Quantité Min": stock["quantite_min"],
            "Quantité Max": stock.get("quantite_max", "")
        })
    
    # Créer le fichier Excel
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Stocks', index=False)
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="stocks_export.xlsx"'
    }
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

@api_router.post("/import/stocks")
async def import_stocks(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx ou .xls")
    
    try:
        # Lire le fichier Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Vérifier si le produit existe
                produit_id = str(row.get("Produit ID", ""))
                if not produit_id:
                    continue
                
                produit = await db.produits.find_one({"id": produit_id})
                if not produit:
                    errors.append(f"Ligne {index + 2}: Produit ID {produit_id} non trouvé")
                    continue
                
                # Mettre à jour le stock
                quantite_actuelle = float(row.get("Quantité Actuelle", 0))
                quantite_min = float(row.get("Quantité Min", 0))
                quantite_max = row.get("Quantité Max")
                quantite_max = float(quantite_max) if quantite_max and str(quantite_max) != 'nan' else None
                
                await db.stocks.update_one(
                    {"produit_id": produit_id},
                    {"$set": {
                        "quantite_actuelle": quantite_actuelle,
                        "quantite_min": quantite_min,
                        "quantite_max": quantite_max,
                        "derniere_maj": datetime.utcnow()
                    }}
                )
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Ligne {index + 2}: {str(e)}")
        
        return {
            "message": f"{imported_count} lignes importées avec succès",
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la lecture du fichier: {str(e)}")

@api_router.post("/import/recettes")
async def import_recettes(file: UploadFile = File(...)):
    """Import de recettes depuis Excel
    Format attendu: Nom Recette | Description | Catégorie | Portions | Temps Préparation | Prix Vente | Produit ID | Quantité | Unité
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx ou .xls")
    
    try:
        # Lire le fichier Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        imported_count = 0
        errors = []
        recettes_dict = {}
        
        for index, row in df.iterrows():
            try:
                nom_recette = str(row.get("Nom Recette", "")).strip()
                if not nom_recette:
                    continue
                
                # Créer ou mettre à jour la recette
                if nom_recette not in recettes_dict:
                    recettes_dict[nom_recette] = {
                        "nom": nom_recette,
                        "description": str(row.get("Description", "")) or None,
                        "categorie": str(row.get("Catégorie", "")) or None,
                        "portions": int(row.get("Portions", 1)),
                        "temps_preparation": int(row.get("Temps Préparation", 0)) if row.get("Temps Préparation") else None,
                        "prix_vente": float(row.get("Prix Vente", 0)) if row.get("Prix Vente") else None,
                        "ingredients": []
                    }
                
                # Ajouter l'ingrédient
                produit_id = str(row.get("Produit ID", "")).strip()
                quantite = float(row.get("Quantité", 0))
                unite = str(row.get("Unité", "")).strip()
                
                if produit_id and quantite > 0:
                    # Vérifier que le produit existe
                    produit = await db.produits.find_one({"id": produit_id})
                    if produit:
                        recettes_dict[nom_recette]["ingredients"].append({
                            "produit_id": produit_id,
                            "produit_nom": produit["nom"],
                            "quantite": quantite,
                            "unite": unite
                        })
                    else:
                        errors.append(f"Ligne {index + 2}: Produit ID {produit_id} non trouvé pour la recette {nom_recette}")
                
            except Exception as e:
                errors.append(f"Ligne {index + 2}: {str(e)}")
        
        # Sauvegarder les recettes
        for nom_recette, recette_data in recettes_dict.items():
            try:
                # Vérifier si la recette existe déjà
                existing_recette = await db.recettes.find_one({"nom": nom_recette})
                if existing_recette:
                    # Mettre à jour la recette existante
                    await db.recettes.update_one(
                        {"nom": nom_recette},
                        {"$set": recette_data}
                    )
                else:
                    # Créer une nouvelle recette
                    recette_obj = Recette(**recette_data)
                    await db.recettes.insert_one(recette_obj.dict())
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Erreur lors de la sauvegarde de la recette {nom_recette}: {str(e)}")
        
        return {
            "message": f"{imported_count} recettes importées avec succès",
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la lecture du fichier: {str(e)}")

@api_router.get("/export/recettes")
async def export_recettes():
    """Export des recettes vers Excel"""
    # Récupérer toutes les recettes
    recettes = await db.recettes.find().to_list(1000)
    
    # Préparer les données pour Excel
    data = []
    for recette in recettes:
        if recette.get("ingredients"):
            for ingredient in recette["ingredients"]:
                data.append({
                    "Nom Recette": recette["nom"],
                    "Description": recette.get("description", ""),
                    "Catégorie": recette.get("categorie", ""),
                    "Portions": recette["portions"],
                    "Temps Préparation": recette.get("temps_preparation", ""),
                    "Prix Vente": recette.get("prix_vente", ""),
                    "Produit ID": ingredient["produit_id"],
                    "Nom Produit": ingredient.get("produit_nom", ""),
                    "Quantité": ingredient["quantite"],
                    "Unité": ingredient["unite"]
                })
        else:
            # Recette sans ingrédients
            data.append({
                "Nom Recette": recette["nom"],
                "Description": recette.get("description", ""),
                "Catégorie": recette.get("categorie", ""),
                "Portions": recette["portions"],
                "Temps Préparation": recette.get("temps_preparation", ""),
                "Prix Vente": recette.get("prix_vente", ""),
                "Produit ID": "",
                "Nom Produit": "",
                "Quantité": "",
                "Unité": ""
            })
    
    # Créer le fichier Excel
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Recettes', index=False)
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="recettes_export.xlsx"'
    }
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    total_produits = await db.produits.count_documents({})
    total_fournisseurs = await db.fournisseurs.count_documents({})
    
    # Stocks faibles (quantité actuelle <= quantité minimum)
    stocks_faibles = await db.stocks.count_documents({
        "$expr": {"$lte": ["$quantite_actuelle", "$quantite_min"]}
    })
    
    # Stocks récents (modifiés dans les 7 derniers jours)
    from datetime import timedelta
    date_limite = datetime.utcnow() - timedelta(days=7)
    stocks_recents = await db.stocks.count_documents({
        "derniere_maj": {"$gte": date_limite}
    })
    
    return {
        "total_produits": total_produits,
        "total_fournisseurs": total_fournisseurs,
        "stocks_faibles": stocks_faibles,
        "stocks_recents": stocks_recents
    }

# Endpoint pour initialiser des données de démonstration (restaurant français-italien)
@api_router.post("/demo/init-french-italian-data")
async def init_french_italian_demo_data():
    """Initialise des données de démonstration pour un restaurant français-italien"""
    
    # Données des fournisseurs
    demo_fournisseurs = [
        {
            "nom": "Fromagerie Laurent",
            "contact": "M. Laurent Dubois",
            "email": "laurent@fromagerie-laurent.fr",
            "telephone": "01.45.67.89.12",
            "adresse": "12 Rue de la Fromagerie, 75011 Paris"
        },
        {
            "nom": "Boucherie Artisanale",
            "contact": "Mme Marie Rousseau",
            "email": "marie@boucherie-artisan.fr",
            "telephone": "01.42.35.78.90",
            "adresse": "8 Avenue de la République, 75012 Paris"
        },
        {
            "nom": "Pasta & Co",
            "contact": "Giuseppe Rossi",
            "email": "giuseppe@pastaeco.it",
            "telephone": "+39.02.1234567",
            "adresse": "Via Milano 45, 20100 Milano, Italia"
        },
        {
            "nom": "Marché des Légumes",
            "contact": "Pierre Martin",
            "email": "pierre@marche-legumes.fr",
            "telephone": "01.48.92.15.30",
            "adresse": "Place du Marché, 94200 Ivry-sur-Seine"
        }
    ]
    
    # Créer les fournisseurs
    fournisseurs_ids = {}
    for fournisseur_data in demo_fournisseurs:
        # Vérifier si le fournisseur existe déjà
        existing = await db.fournisseurs.find_one({"nom": fournisseur_data["nom"]})
        if not existing:
            fournisseur_obj = Fournisseur(**fournisseur_data)
            await db.fournisseurs.insert_one(fournisseur_obj.dict())
            fournisseurs_ids[fournisseur_data["nom"]] = fournisseur_obj.id
        else:
            fournisseurs_ids[fournisseur_data["nom"]] = existing["id"]
    
    # Données des produits
    demo_produits = [
        # Fromages et produits laitiers
        {"nom": "Mozzarella di Bufala", "categorie": "Fromage", "unite": "kg", "prix_achat": 18.5, "fournisseur": "Fromagerie Laurent"},
        {"nom": "Parmesan Reggiano 24 mois", "categorie": "Fromage", "unite": "kg", "prix_achat": 35.0, "fournisseur": "Fromagerie Laurent"},
        {"nom": "Beurre doux", "categorie": "Produit laitier", "unite": "kg", "prix_achat": 6.2, "fournisseur": "Fromagerie Laurent"},
        {"nom": "Crème fraîche 35%", "categorie": "Produit laitier", "unite": "L", "prix_achat": 4.8, "fournisseur": "Fromagerie Laurent"},
        
        # Viandes
        {"nom": "Escalope de veau", "categorie": "Viande", "unite": "kg", "prix_achat": 28.0, "fournisseur": "Boucherie Artisanale"},
        {"nom": "Poitrine de porc fumée", "categorie": "Viande", "unite": "kg", "prix_achat": 12.5, "fournisseur": "Boucherie Artisanale"},
        {"nom": "Jambon de Parme", "categorie": "Charcuterie", "unite": "kg", "prix_achat": 45.0, "fournisseur": "Boucherie Artisanale"},
        
        # Pâtes et riz
        {"nom": "Spaghetti Artisanaux", "categorie": "Pâtes", "unite": "kg", "prix_achat": 8.5, "fournisseur": "Pasta & Co"},
        {"nom": "Tagliatelles aux œufs", "categorie": "Pâtes", "unite": "kg", "prix_achat": 9.2, "fournisseur": "Pasta & Co"},
        {"nom": "Risotto Carnaroli", "categorie": "Riz", "unite": "kg", "prix_achat": 6.8, "fournisseur": "Pasta & Co"},
        {"nom": "Gnocchi frais", "categorie": "Pâtes", "unite": "kg", "prix_achat": 7.5, "fournisseur": "Pasta & Co"},
        
        # Légumes
        {"nom": "Tomates cerises", "categorie": "Légume", "unite": "kg", "prix_achat": 4.2, "fournisseur": "Marché des Légumes"},
        {"nom": "Basilic frais", "categorie": "Herbes", "unite": "paquet", "prix_achat": 1.8, "fournisseur": "Marché des Légumes"},
        {"nom": "Roquette", "categorie": "Salade", "unite": "kg", "prix_achat": 12.0, "fournisseur": "Marché des Légumes"},
        {"nom": "Champignons de Paris", "categorie": "Légume", "unite": "kg", "prix_achat": 5.5, "fournisseur": "Marché des Légumes"},
        {"nom": "Courgettes", "categorie": "Légume", "unite": "kg", "prix_achat": 2.8, "fournisseur": "Marché des Légumes"},
        {"nom": "Aubergines", "categorie": "Légume", "unite": "kg", "prix_achat": 3.5, "fournisseur": "Marché des Légumes"},
        
        # Condiments et huiles
        {"nom": "Huile d'olive extra vierge", "categorie": "Huile", "unite": "L", "prix_achat": 15.0, "fournisseur": "Pasta & Co"},
        {"nom": "Vinaigre balsamique", "categorie": "Condiment", "unite": "L", "prix_achat": 25.0, "fournisseur": "Pasta & Co"},
        {"nom": "Ail", "categorie": "Condiment", "unite": "kg", "prix_achat": 8.0, "fournisseur": "Marché des Légumes"}
    ]
    
    # Créer les produits avec stocks initiaux
    produits_ids = {}
    for produit_data in demo_produits:
        # Vérifier si le produit existe déjà
        existing = await db.produits.find_one({"nom": produit_data["nom"]})
        if not existing:
            produit_create_data = {
                "nom": produit_data["nom"],
                "categorie": produit_data["categorie"],
                "unite": produit_data["unite"],
                "prix_achat": produit_data["prix_achat"],
                "fournisseur_id": fournisseurs_ids.get(produit_data["fournisseur"])
            }
            
            # Récupérer le nom du fournisseur
            if produit_create_data["fournisseur_id"]:
                fournisseur = await db.fournisseurs.find_one({"id": produit_create_data["fournisseur_id"]})
                if fournisseur:
                    produit_create_data["fournisseur_nom"] = fournisseur["nom"]
            
            produit_obj = Produit(**produit_create_data)
            await db.produits.insert_one(produit_obj.dict())
            produits_ids[produit_data["nom"]] = produit_obj.id
            
            # Créer un stock initial réaliste
            import random
            stock_initial = random.uniform(10, 50)  # Stock entre 10 et 50 unités
            stock_obj = Stock(
                produit_id=produit_obj.id, 
                produit_nom=produit_obj.nom, 
                quantite_actuelle=stock_initial,
                quantite_min=5.0,
                quantite_max=100.0
            )
            await db.stocks.insert_one(stock_obj.dict())
        else:
            produits_ids[produit_data["nom"]] = existing["id"]
    
    # Créer des recettes typiques franco-italiennes
    demo_recettes = [
        {
            "nom": "Spaghetti Carbonara",
            "description": "Recette traditionnelle italienne avec œufs, parmesan et pancetta",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 20,
            "prix_vente": 18.50,
            "instructions": "1. Faire bouillir l'eau salée\n2. Cuire les spaghettis al dente\n3. Faire revenir la pancetta\n4. Mélanger œufs et parmesan\n5. Incorporer hors du feu",
            "ingredients": [
                {"produit": "Spaghetti Artisanaux", "quantite": 400, "unite": "g"},
                {"produit": "Parmesan Reggiano 24 mois", "quantite": 100, "unite": "g"},
                {"produit": "Poitrine de porc fumée", "quantite": 150, "unite": "g"}
            ]
        },
        {
            "nom": "Risotto aux Champignons",
            "description": "Risotto crémeux aux champignons de saison",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 35,
            "prix_vente": 16.00,
            "instructions": "1. Faire chauffer le bouillon\n2. Faire revenir les champignons\n3. Toaster le riz\n4. Ajouter louche par louche\n5. Incorporer beurre et parmesan",
            "ingredients": [
                {"produit": "Risotto Carnaroli", "quantite": 320, "unite": "g"},
                {"produit": "Champignons de Paris", "quantite": 300, "unite": "g"},
                {"produit": "Parmesan Reggiano 24 mois", "quantite": 80, "unite": "g"},
                {"produit": "Beurre doux", "quantite": 50, "unite": "g"}
            ]
        },
        {
            "nom": "Escalope Milanaise",
            "description": "Escalope de veau panée à la milanaise",
            "categorie": "plat",
            "portions": 2,
            "temps_preparation": 25,
            "prix_vente": 24.00,
            "instructions": "1. Aplatir les escalopes\n2. Passer dans l'œuf battu\n3. Paner au parmesan\n4. Faire dorer à la poêle\n5. Servir avec roquette",
            "ingredients": [
                {"produit": "Escalope de veau", "quantite": 400, "unite": "g"},
                {"produit": "Parmesan Reggiano 24 mois", "quantite": 50, "unite": "g"},
                {"produit": "Roquette", "quantite": 100, "unite": "g"}
            ]
        },
        {
            "nom": "Salade Caprese",
            "description": "Salade italienne tomate, mozzarella, basilic",
            "categorie": "entrée",
            "portions": 4,
            "temps_preparation": 10,
            "prix_vente": 12.50,
            "instructions": "1. Trancher tomates et mozzarella\n2. Alterner sur l'assiette\n3. Parsemer de basilic\n4. Arroser d'huile d'olive\n5. Assaisonner",
            "ingredients": [
                {"produit": "Mozzarella di Bufala", "quantite": 250, "unite": "g"},
                {"produit": "Tomates cerises", "quantite": 400, "unite": "g"},
                {"produit": "Basilic frais", "quantite": 2, "unite": "paquet"},
                {"produit": "Huile d'olive extra vierge", "quantite": 50, "unite": "mL"}
            ]
        }
    ]
    
    # Créer les recettes
    recettes_count = 0
    for recette_data in demo_recettes:
        # Vérifier si la recette existe déjà
        existing = await db.recettes.find_one({"nom": recette_data["nom"]})
        if not existing:
            # Préparer les ingrédients avec les IDs des produits
            ingredients_with_ids = []
            for ingredient in recette_data["ingredients"]:
                produit_id = produits_ids.get(ingredient["produit"])
                if produit_id:
                    produit = await db.produits.find_one({"id": produit_id})
                    ingredients_with_ids.append({
                        "produit_id": produit_id,
                        "produit_nom": produit["nom"] if produit else ingredient["produit"],
                        "quantite": ingredient["quantite"],
                        "unite": ingredient["unite"]
                    })
            
            recette_create_data = {
                "nom": recette_data["nom"],
                "description": recette_data["description"],
                "categorie": recette_data["categorie"],
                "portions": recette_data["portions"],
                "temps_preparation": recette_data["temps_preparation"],
                "prix_vente": recette_data["prix_vente"],
                "instructions": recette_data["instructions"],
                "ingredients": ingredients_with_ids
            }
            
            recette_obj = Recette(**recette_create_data)
            await db.recettes.insert_one(recette_obj.dict())
            recettes_count += 1
    
    return {
        "message": "Données de démonstration créées avec succès",
        "fournisseurs_crees": len([f for f in demo_fournisseurs]),
        "produits_crees": len([p for p in demo_produits]),
        "recettes_creees": recettes_count
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()