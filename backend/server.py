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

# Imports pour OCR
import pytesseract
import cv2
import numpy as np
from PIL import Image
import base64
import re

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
    prix_vente: Optional[float] = None
    instructions: Optional[str] = None
    ingredients: Optional[List[RecetteIngredient]] = None

# Modèles pour l'OCR et traitement de documents
class DocumentOCR(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type_document: str  # "z_report", "facture_fournisseur"
    nom_fichier: str
    image_base64: Optional[str] = None
    texte_extrait: Optional[str] = None
    donnees_parsees: Optional[dict] = None
    statut: str = "en_attente"  # "en_attente", "traite", "erreur"
    date_upload: datetime = Field(default_factory=datetime.utcnow)
    date_traitement: Optional[datetime] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    type_document: str
    texte_extrait: str
    donnees_parsees: dict
    message: str

class ZReportData(BaseModel):
    date: Optional[str] = None
    plats_vendus: List[dict] = []
    total_ca: Optional[float] = None
    nb_couverts: Optional[int] = None

class FactureFournisseurData(BaseModel):
    fournisseur: Optional[str] = None
    date: Optional[str] = None
    numero_facture: Optional[str] = None
    produits: List[dict] = []
    total_ht: Optional[float] = None
    total_ttc: Optional[float] = None

# Configuration OCR
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Configuration de la base de données
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.restaurant_stock

# Fonctions utilitaires pour OCR
def preprocess_image(image):
    """Préprocessing de l'image pour améliorer l'OCR"""
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Appliquer un filtre pour réduire le bruit
    denoised = cv2.medianBlur(gray, 5)
    
    # Améliorer le contraste
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Seuillage adaptatif pour améliorer la lisibilité
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    return binary

def extract_text_from_image(image_base64: str) -> str:
    """Extraire le texte d'une image en base64 avec OCR"""
    try:
        # Décoder l'image base64
        image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Préprocessing de l'image
        processed_image = preprocess_image(image)
        
        # Configuration OCR pour français
        config = '--oem 3 --psm 6 -l fra+eng'
        
        # Extraire le texte
        text = pytesseract.image_to_string(processed_image, config=config)
        
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'extraction OCR: {str(e)}")

def parse_z_report(texte_ocr: str) -> ZReportData:
    """Parser les données d'un rapport Z"""
    data = ZReportData()
    
    try:
        # Rechercher la date
        date_patterns = [
            r'(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})',
            r'(\d{2,4}[/\-.]\d{1,2}[/\-.]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, texte_ocr)
            if date_match:
                data.date = date_match.group(1)
                break
        
        # Patterns améliorés pour les plats vendus
        plat_patterns = [
            # Format: "Nom du plat: quantité" ou "Nom du plat quantité"
            r'([A-ZÁÀÂÄÇÉÈÊËÏÎÔÙÛÜŸ][A-Za-zÀ-ÿ\s\'\-]{3,50})\s*:?\s*(\d{1,3})(?:\s*[x\*]?\s*(\d+[,.]?\d*)?\s*[€]?)?',
            # Format: "quantité x Nom du plat"  
            r'(\d{1,3})\s*[x\*]\s*([A-ZÁÀÂÄÇÉÈÊËÏÎÔÙÛÜŸ][A-Za-zÀ-ÿ\s\'\-]{3,50})',
            # Format: "Nom du plat    quantité    prix"
            r'([A-ZÁÀÂÄÇÉÈÊËÏÎÔÙÛÜŸ][A-Za-zÀ-ÿ\s\'\-]{3,50})\s+(\d{1,3})\s+(\d+[,.]?\d*)',
        ]
        
        plats_vendus = []
        lines = texte_ocr.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Ignorer les lignes qui contiennent clairement des totaux ou des dates
            if re.search(r'total|somme|ca\s|date|rapport|couverts?', line.lower()):
                continue
                
            for pattern in plat_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if len(groups) >= 2:
                        # Déterminer le nom du plat et la quantité
                        if groups[0].isdigit():
                            # Format: quantité + nom
                            quantite = int(groups[0])
                            nom_plat = groups[1].strip()
                        else:
                            # Format: nom + quantité  
                            nom_plat = groups[0].strip()
                            try:
                                quantite = int(groups[1]) if groups[1] and groups[1].isdigit() else 1
                            except:
                                quantite = 1
                        
                        # Nettoyer le nom du plat
                        nom_plat = re.sub(r'[:\-_]+$', '', nom_plat).strip()
                        
                        # Valider que c'est bien un nom de plat (pas un prix ou autre)
                        if (len(nom_plat) > 3 and 
                            not nom_plat.isdigit() and 
                            quantite > 0 and quantite < 999 and
                            not re.match(r'^\d+[,.]?\d*\s*[€]?$', nom_plat)):
                            
                            # Éviter les doublons
                            existing = next((p for p in plats_vendus if p["nom"].lower() == nom_plat.lower()), None)
                            if existing:
                                existing["quantite"] += quantite
                            else:
                                plats_vendus.append({
                                    "nom": nom_plat,
                                    "quantite": quantite,
                                    "ligne_originale": line
                                })
                            break
        
        data.plats_vendus = plats_vendus
        
        # Rechercher le total CA avec patterns améliorés
        ca_patterns = [
            r'total[:\s]*(\d+[,.]?\d*)\s*[€]?',
            r'ca[:\s]*(\d+[,.]?\d*)\s*[€]?',
            r'montant[:\s]*(\d+[,.]?\d*)\s*[€]?',
            r'somme[:\s]*(\d+[,.]?\d*)\s*[€]?'
        ]
        
        for pattern in ca_patterns:
            ca_match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if ca_match:
                ca_str = ca_match.group(1).replace(',', '.')
                try:
                    data.total_ca = float(ca_str)
                    break
                except:
                    continue
        
        # Rechercher le nombre de couverts
        couvert_patterns = [
            r'couverts?[:\s]*(\d+)',
            r'nb[.\s]*couverts?[:\s]*(\d+)',
            r'(\d+)\s*couverts?'
        ]
        
        for pattern in couvert_patterns:
            couvert_match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if couvert_match:
                try:
                    data.nb_couverts = int(couvert_match.group(1))
                    break
                except:
                    continue
        
    except Exception as e:
        print(f"Erreur parsing Z report: {str(e)}")
    
    return data

def parse_facture_fournisseur(texte_ocr: str) -> FactureFournisseurData:
    """Parser les données d'une facture fournisseur"""
    data = FactureFournisseurData()
    
    try:
        # Rechercher le fournisseur dans les premières lignes
        lines = texte_ocr.split('\n')
        for i, line in enumerate(lines[:8]):  # Les 8 premières lignes
            line = line.strip()
            if len(line) > 3 and not line.isdigit() and not re.match(r'^\d{2}[/\-.]', line):
                # Éviter les dates, numéros de facture, etc.
                if any(word in line.lower() for word in ['facture', 'invoice', 'devis', 'bon', 'date', 'n°', 'numero']):
                    continue
                # Si c'est une ligne avec du texte significatif et pas trop générique
                if re.search(r'[a-zA-ZÀ-ÿ]{3,}', line) and len(line.split()) <= 5:
                    data.fournisseur = line
                    break
        
        # Rechercher la date avec patterns améliorés
        date_patterns = [
            r'date[:\s]*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})',
            r'(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if date_match:
                data.date = date_match.group(1)
                break
        
        # Rechercher le numéro de facture
        facture_patterns = [
            r'facture[:\s#n°]*([A-Z0-9\-]{3,15})',
            r'n°[:\s]*([A-Z0-9\-]{3,15})',
            r'invoice[:\s#]*([A-Z0-9\-]{3,15})'
        ]
        
        for pattern in facture_patterns:
            facture_match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if facture_match:
                data.numero_facture = facture_match.group(1)
                break
        
        # Patterns améliorés pour les produits et prix
        produits = []
        produit_patterns = [
            # Format: "Nom produit quantité x prix = total"
            r'([A-Za-zÀ-ÿ\s\'\-]{3,40})\s+(\d{1,3})[x\*]\s*(\d+[,.]?\d*)[€]?\s*=?\s*(\d+[,.]?\d*)\s*[€]?',
            # Format: "Nom produit: quantité x prix€"
            r'([A-Za-zÀ-ÿ\s\'\-]{3,40})[:\s]+(\d{1,3})[x\*]\s*(\d+[,.]?\d*)\s*[€]',
            # Format: "quantité x Nom produit @ prix€"
            r'(\d{1,3})\s*[x\*]\s*([A-Za-zÀ-ÿ\s\'\-]{3,40})\s*[@]\s*(\d+[,.]?\d*)\s*[€]?',
            # Format simple: "Nom produit    prix€"
            r'([A-Za-zÀ-ÿ\s\'\-]{3,40})\s+(\d+[,.]?\d*)\s*[€]'
        ]
        
        for line in texte_ocr.split('\n'):
            line = line.strip()
            if len(line) < 8:  # Ignorer les lignes trop courtes
                continue
            
            # Ignorer les lignes de total/sous-total
            if re.search(r'total|sous.total|tva|€\s*$', line.lower()):
                continue
                
            for pattern in produit_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:
                        try:
                            # Analyser selon le format détecté
                            if groups[0].isdigit():
                                # Format: quantité + nom + prix
                                quantite = float(groups[0])
                                nom_produit = groups[1].strip()
                                prix_unitaire = float(groups[2].replace(',', '.')) if len(groups) > 2 else 0
                            else:
                                # Format: nom + quantité/prix
                                nom_produit = groups[0].strip()
                                if len(groups) >= 4 and groups[1].isdigit():
                                    # Format avec quantité explicite
                                    quantite = float(groups[1])
                                    prix_unitaire = float(groups[2].replace(',', '.'))
                                    total = float(groups[3].replace(',', '.')) if groups[3] else quantite * prix_unitaire
                                else:
                                    # Format simple nom + prix
                                    quantite = 1.0
                                    prix_unitaire = float(groups[1].replace(',', '.'))
                                    total = prix_unitaire
                            
                            # Nettoyer le nom du produit
                            nom_produit = re.sub(r'[:\-_]+$', '', nom_produit).strip()
                            
                            # Valider les données
                            if (len(nom_produit) > 2 and 
                                quantite > 0 and quantite < 9999 and 
                                prix_unitaire >= 0 and
                                not nom_produit.isdigit()):
                                
                                produit = {
                                    "nom": nom_produit,
                                    "quantite": quantite,
                                    "prix_unitaire": prix_unitaire,
                                    "total": quantite * prix_unitaire,
                                    "ligne_originale": line
                                }
                                
                                # Éviter les doublons
                                if not any(p["nom"].lower() == nom_produit.lower() for p in produits):
                                    produits.append(produit)
                                break
                        except (ValueError, IndexError):
                            continue
        
        data.produits = produits
        
        # Rechercher les totaux HT et TTC avec patterns améliorés
        total_patterns = [
            (r'total\s*ht[:\s]*(\d+[,.]?\d*)\s*[€]?', 'ht'),
            (r'total\s*ttc[:\s]*(\d+[,.]?\d*)\s*[€]?', 'ttc'),
            (r'montant\s*ht[:\s]*(\d+[,.]?\d*)\s*[€]?', 'ht'),
            (r'montant\s*ttc[:\s]*(\d+[,.]?\d*)\s*[€]?', 'ttc'),
            (r'sous.total[:\s]*(\d+[,.]?\d*)\s*[€]?', 'ht')
        ]
        
        for pattern, type_total in total_patterns:
            match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if match:
                try:
                    montant = float(match.group(1).replace(',', '.'))
                    if type_total == 'ht':
                        data.total_ht = montant
                    elif type_total == 'ttc':
                        data.total_ttc = montant
                except ValueError:
                    continue
        
    except Exception as e:
        print(f"Erreur parsing facture: {str(e)}")
    
    return data

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

# Endpoint pour réinitialiser les données de La Table d'Augustine
@api_router.post("/demo/init-table-augustine-data")
async def init_table_augustine_demo_data():
    """Initialise des données de démonstration basées sur La Table d'Augustine - Restaurant méditerranéen"""
    
    # Données des fournisseurs réalistes pour La Table d'Augustine
    demo_fournisseurs = [
        {
            "nom": "Maison Artigiana",
            "contact": "Giuseppe Pellegrino",
            "email": "contact@artigiana-burrata.com",
            "telephone": "+39.080.4721234",
            "adresse": "Via dei Trulli 23, 70015 Noci, Bari, Italie"
        },
        {
            "nom": "Pêcherie des Sanguinaires",
            "contact": "Antoine Corsetti",
            "email": "contact@pecherie-sanguinaires.fr",
            "telephone": "04.95.51.32.87",
            "adresse": "Baie des Sanguinaires, 20000 Ajaccio, Corse"
        },
        {
            "nom": "Boucherie Limousine du Sud",
            "contact": "Pierre Dufour",
            "email": "pierre@boucherie-limousine.fr",
            "telephone": "05.55.34.67.89",
            "adresse": "Avenue du Limousin, 87000 Limoges"
        },
        {
            "nom": "Trufficulteurs de Forcalquier",
            "contact": "Marie Trubert",
            "email": "marie@truffes-forcalquier.fr",
            "telephone": "04.92.75.18.45",
            "adresse": "Route des Truffes, 04300 Forcalquier, Alpes-de-Haute-Provence"
        },
        {
            "nom": "Maraîchers de Provence",
            "contact": "Jean-Claude Méditerranée",
            "email": "jc@maraichers-provence.fr",
            "telephone": "04.42.67.23.11",
            "adresse": "Chemin des Oliviers, 13100 Aix-en-Provence"
        },
        {
            "nom": "Fromagerie des Alpilles",
            "contact": "Sylvie Berger",
            "email": "sylvie@fromagerie-alpilles.fr",
            "telephone": "04.90.54.32.76",
            "adresse": "Place du Village, 13520 Les Baux-de-Provence"
        }
    ]
    
    # Créer les fournisseurs
    fournisseurs_ids = {}
    for fournisseur_data in demo_fournisseurs:
        existing = await db.fournisseurs.find_one({"nom": fournisseur_data["nom"]})
        if not existing:
            fournisseur_obj = Fournisseur(**fournisseur_data)
            await db.fournisseurs.insert_one(fournisseur_obj.dict())
            fournisseurs_ids[fournisseur_data["nom"]] = fournisseur_obj.id
        else:
            fournisseurs_ids[fournisseur_data["nom"]] = existing["id"]
    
    # Produits basés sur la carte de La Table d'Augustine
    demo_produits = [
        # Fruits de mer et poissons
        {"nom": "Supions (petits calamars)", "categorie": "Fruits de mer", "unite": "kg", "prix_achat": 22.0, "fournisseur": "Pêcherie des Sanguinaires"},
        {"nom": "Moules de Méditerranée", "categorie": "Fruits de mer", "unite": "kg", "prix_achat": 8.5, "fournisseur": "Pêcherie des Sanguinaires"},
        {"nom": "Sardines fraîches", "categorie": "Poisson", "unite": "kg", "prix_achat": 12.0, "fournisseur": "Pêcherie des Sanguinaires"},
        {"nom": "Daurade royale de Corse", "categorie": "Poisson", "unite": "kg", "prix_achat": 28.0, "fournisseur": "Pêcherie des Sanguinaires"},
        {"nom": "Palourdes", "categorie": "Fruits de mer", "unite": "kg", "prix_achat": 35.0, "fournisseur": "Pêcherie des Sanguinaires"},
        {"nom": "Sole", "categorie": "Poisson", "unite": "kg", "prix_achat": 42.0, "fournisseur": "Pêcherie des Sanguinaires"},
        {"nom": "Poisson du jour", "categorie": "Poisson", "unite": "kg", "prix_achat": 25.0, "fournisseur": "Pêcherie des Sanguinaires"},
        
        # Fromages et produits laitiers  
        {"nom": "Burrata des Pouilles Artigiana", "categorie": "Fromage", "unite": "pièce", "prix_achat": 8.5, "fournisseur": "Maison Artigiana"},
        {"nom": "Stracciatella", "categorie": "Fromage", "unite": "kg", "prix_achat": 24.0, "fournisseur": "Maison Artigiana"},
        {"nom": "Tomme de brebis AOP", "categorie": "Fromage", "unite": "kg", "prix_achat": 18.0, "fournisseur": "Fromagerie des Alpilles"},
        {"nom": "Féta", "categorie": "Fromage", "unite": "kg", "prix_achat": 14.0, "fournisseur": "Fromagerie des Alpilles"},
        {"nom": "Brousse fraîche", "categorie": "Fromage", "unite": "kg", "prix_achat": 12.0, "fournisseur": "Fromagerie des Alpilles"},
        
        # Viandes
        {"nom": "Bœuf Limousin (filet)", "categorie": "Viande", "unite": "kg", "prix_achat": 45.0, "fournisseur": "Boucherie Limousine du Sud"},
        {"nom": "Côte de bœuf Aubarc", "categorie": "Viande", "unite": "kg", "prix_achat": 35.0, "fournisseur": "Boucherie Limousine du Sud"},
        {"nom": "Souris d'agneau", "categorie": "Viande", "unite": "kg", "prix_achat": 18.0, "fournisseur": "Boucherie Limousine du Sud"},
        {"nom": "Jarret de veau", "categorie": "Viande", "unite": "kg", "prix_achat": 22.0, "fournisseur": "Boucherie Limousine du Sud"},
        {"nom": "Porc pour farce", "categorie": "Viande", "unite": "kg", "prix_achat": 12.0, "fournisseur": "Boucherie Limousine du Sud"},
        {"nom": "Foie gras", "categorie": "Charcuterie", "unite": "kg", "prix_achat": 85.0, "fournisseur": "Boucherie Limousine du Sud"},
        
        # Légumes et herbes méditerranéennes
        {"nom": "Fleurs de courgettes", "categorie": "Légume", "unite": "pièce", "prix_achat": 0.8, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Courgettes", "categorie": "Légume", "unite": "kg", "prix_achat": 3.2, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Tomates anciennes", "categorie": "Légume", "unite": "kg", "prix_achat": 6.5, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Pastèque", "categorie": "Fruit", "unite": "kg", "prix_achat": 2.8, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Poivrons colorés", "categorie": "Légume", "unite": "kg", "prix_achat": 4.5, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Blettes", "categorie": "Légume", "unite": "kg", "prix_achat": 3.8, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Pommes de terre grenaille", "categorie": "Légume", "unite": "kg", "prix_achat": 2.5, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Champignons de Paris", "categorie": "Légume", "unite": "kg", "prix_achat": 8.5, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Céleri-rave", "categorie": "Légume", "unite": "kg", "prix_achat": 3.0, "fournisseur": "Maraîchers de Provence"},
        
        # Herbes aromatiques
        {"nom": "Persil plat", "categorie": "Herbes", "unite": "botte", "prix_achat": 1.5, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Menthe fraîche", "categorie": "Herbes", "unite": "botte", "prix_achat": 2.0, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Ail de Provence", "categorie": "Condiment", "unite": "kg", "prix_achat": 12.0, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Raifort", "categorie": "Condiment", "unite": "kg", "prix_achat": 15.0, "fournisseur": "Maraîchers de Provence"},
        
        # Pâtes et farines
        {"nom": "Linguine artisanales", "categorie": "Pâtes", "unite": "kg", "prix_achat": 9.5, "fournisseur": "Maison Artigiana"},
        {"nom": "Rigatoni", "categorie": "Pâtes", "unite": "kg", "prix_achat": 8.8, "fournisseur": "Maison Artigiana"},
        {"nom": "Gnocchi frais", "categorie": "Pâtes", "unite": "kg", "prix_achat": 7.2, "fournisseur": "Maison Artigiana"},
        {"nom": "Farine de pois-chiche", "categorie": "Farine", "unite": "kg", "prix_achat": 6.5, "fournisseur": "Maraîchers de Provence"},
        
        # Produits de luxe
        {"nom": "Truffe d'été Aestivum", "categorie": "Truffe", "unite": "kg", "prix_achat": 800.0, "fournisseur": "Trufficulteurs de Forcalquier"},
        {"nom": "Huile de truffe", "categorie": "Huile", "unite": "L", "prix_achat": 120.0, "fournisseur": "Trufficulteurs de Forcalquier"},
        
        # Condiments et accompagnements
        {"nom": "Huile d'olive extra vierge", "categorie": "Huile", "unite": "L", "prix_achat": 18.0, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Huile verte aux herbes", "categorie": "Huile", "unite": "L", "prix_achat": 25.0, "fournisseur": "Maraîchers de Provence"},
        
        # Desserts
        {"nom": "Pistaches de Sicile", "categorie": "Fruits secs", "unite": "kg", "prix_achat": 28.0, "fournisseur": "Maison Artigiana"},
        {"nom": "Fraises de saison", "categorie": "Fruit", "unite": "kg", "prix_achat": 8.5, "fournisseur": "Maraîchers de Provence"},
        {"nom": "Mascarpone", "categorie": "Produit laitier", "unite": "kg", "prix_achat": 12.5, "fournisseur": "Maison Artigiana"},
        {"nom": "Chocolat noir 70%", "categorie": "Chocolat", "unite": "kg", "prix_achat": 22.0, "fournisseur": "Maison Artigiana"}
    ]
    
    # Créer les produits avec stocks initiaux
    produits_ids = {}
    for produit_data in demo_produits:
        existing = await db.produits.find_one({"nom": produit_data["nom"]})
        if not existing:
            produit_create_data = {
                "nom": produit_data["nom"],
                "categorie": produit_data["categorie"],
                "unite": produit_data["unite"],
                "prix_achat": produit_data["prix_achat"],
                "fournisseur_id": fournisseurs_ids.get(produit_data["fournisseur"])
            }
            
            if produit_create_data["fournisseur_id"]:
                fournisseur = await db.fournisseurs.find_one({"id": produit_create_data["fournisseur_id"]})
                if fournisseur:
                    produit_create_data["fournisseur_nom"] = fournisseur["nom"]
            
            produit_obj = Produit(**produit_create_data)
            await db.produits.insert_one(produit_obj.dict())
            produits_ids[produit_data["nom"]] = produit_obj.id
            
            # Stock initial réaliste selon le type de produit
            import random
            if produit_data["categorie"] in ["Truffe", "Foie gras"]:
                stock_initial = random.uniform(0.5, 3.0)  # Produits rares
            elif produit_data["unite"] == "pièce":
                stock_initial = random.uniform(20, 80)  # Fleurs, burrata, etc.
            elif produit_data["categorie"] in ["Poisson", "Fruits de mer"]:
                stock_initial = random.uniform(5, 15)  # Produits frais
            else:
                stock_initial = random.uniform(10, 50)  # Autres produits
                
            stock_obj = Stock(
                produit_id=produit_obj.id, 
                produit_nom=produit_obj.nom, 
                quantite_actuelle=stock_initial,
                quantite_min=stock_initial * 0.2,
                quantite_max=stock_initial * 3
            )
            await db.stocks.insert_one(stock_obj.dict())
        else:
            produits_ids[produit_data["nom"]] = existing["id"]
    
    # Recettes basées sur la vraie carte de La Table d'Augustine
    demo_recettes = [
        {
            "nom": "Supions en persillade de Mamie",
            "description": "Petits calamars que l'on aime cuisiner chez Mamie, une touche d'ail et de persil, les supions sont sans conteste, notre entrée signature.",
            "categorie": "entrée",
            "portions": 4,
            "temps_preparation": 15,
            "prix_vente": 24.00,
            "instructions": "1. Nettoyer les supions\n2. Faire chauffer l'huile d'olive\n3. Saisir les supions 2 minutes\n4. Ajouter l'ail et le persil\n5. Assaisonner et servir immédiatement",
            "ingredients": [
                {"produit": "Supions (petits calamars)", "quantite": 800, "unite": "g"},
                {"produit": "Ail de Provence", "quantite": 30, "unite": "g"},
                {"produit": "Persil plat", "quantite": 2, "unite": "botte"},
                {"produit": "Huile d'olive extra vierge", "quantite": 80, "unite": "mL"}
            ]
        },
        {
            "nom": "Fleurs de courgettes de Mamet",
            "description": "Fleurs de courgette croustillantes et sa crème de brousse menthe et citron vert. Votre coup de cœur, sans aucun doute",
            "categorie": "entrée",
            "portions": 4,
            "temps_preparation": 25,
            "prix_vente": 21.00,
            "instructions": "1. Préparer la pâte à beignet\n2. Farcir les fleurs avec la brousse\n3. Tremper dans la pâte\n4. Frire à 170°C\n5. Servir avec la crème menthe-citron",
            "ingredients": [
                {"produit": "Fleurs de courgettes", "quantite": 12, "unite": "pièce"},
                {"produit": "Brousse fraîche", "quantite": 200, "unite": "g"},
                {"produit": "Menthe fraîche", "quantite": 1, "unite": "botte"},
                {"produit": "Farine de pois-chiche", "quantite": 150, "unite": "g"}
            ]
        },
        {
            "nom": "Burrata des Pouilles et tomates anciennes",
            "description": "La Maison Artigiana a reçu le prix de la meilleure burrata du monde en 2018 et 2019.",
            "categorie": "entrée",
            "portions": 2,
            "temps_preparation": 10,
            "prix_vente": 18.00,
            "instructions": "1. Sortir la burrata 30 min avant\n2. Trancher les tomates anciennes\n3. Dresser harmonieusement\n4. Arroser d'huile d'olive\n5. Assaisonner délicatement",
            "ingredients": [
                {"produit": "Burrata des Pouilles Artigiana", "quantite": 2, "unite": "pièce"},
                {"produit": "Tomates anciennes", "quantite": 400, "unite": "g"},
                {"produit": "Huile d'olive extra vierge", "quantite": 50, "unite": "mL"}
            ]
        },
        {
            "nom": "Linguine aux palourdes & sauce à l'ail",
            "description": "Un véritable plat gourmand avec une sélection de palourdes minutieuse. Sa sauce à l'ail onctueuse et son beurre monté sont un secret familial.",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 20,
            "prix_vente": 28.00,
            "instructions": "1. Faire dégorger les palourdes\n2. Cuire les linguines al dente\n3. Ouvrir les palourdes au vin blanc\n4. Préparer la sauce à l'ail secrète\n5. Mélanger et monter au beurre",
            "ingredients": [
                {"produit": "Linguine artisanales", "quantite": 400, "unite": "g"},
                {"produit": "Palourdes", "quantite": 1000, "unite": "g"},
                {"produit": "Ail de Provence", "quantite": 40, "unite": "g"},
                {"produit": "Persil plat", "quantite": 1, "unite": "botte"}
            ]
        },
        {
            "nom": "Rigatoni à la truffe fraîche de Forcalquier",
            "description": "Délectez-vous de ce plat mythique de Mamet avec ces truffes fraîches (Aestivum) & sa merveilleuse crème.",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 15,
            "prix_vente": 31.00,
            "instructions": "1. Cuire les rigatoni al dente\n2. Préparer la crème à la truffe\n3. Râper la truffe fraîche\n4. Mélanger délicatement\n5. Servir immédiatement avec copeaux de truffe",
            "ingredients": [
                {"produit": "Rigatoni", "quantite": 400, "unite": "g"},
                {"produit": "Truffe d'été Aestivum", "quantite": 60, "unite": "g"},
                {"produit": "Huile de truffe", "quantite": 20, "unite": "mL"},
                {"produit": "Stracciatella", "quantite": 200, "unite": "g"}
            ]
        },
        {
            "nom": "Gnocchi d'Augustine sauce napolitaine",
            "description": "Un classique chez Mamet: Tomate du soleil & cœur de burrata crémeuse.",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 25,
            "prix_vente": 22.00,
            "instructions": "1. Préparer la sauce tomate napolitaine\n2. Cuire les gnocchi dans l'eau salée\n3. Les faire sauter dans la sauce\n4. Ajouter la stracciatella\n5. Servir bien chaud",
            "ingredients": [
                {"produit": "Gnocchi frais", "quantite": 600, "unite": "g"},
                {"produit": "Tomates anciennes", "quantite": 500, "unite": "g"},
                {"produit": "Stracciatella", "quantite": 150, "unite": "g"},
                {"produit": "Ail de Provence", "quantite": 20, "unite": "g"}
            ]
        },
        {
            "nom": "Souris d'agneau confite",
            "description": "8h de cuisson pour quelques minutes de plaisir. L'emblématique souris d'agneau (400 gr) est le seul plat qui n'est jamais sorti de la carte.",
            "categorie": "plat",
            "portions": 2,
            "temps_preparation": 480,
            "prix_vente": 36.00,
            "instructions": "1. Assaisonner les souris 24h avant\n2. Confit à basse température 8h\n3. Préparer les gnocchi\n4. Réduire le jus de cuisson\n5. Dresser avec le jus réduit",
            "ingredients": [
                {"produit": "Souris d'agneau", "quantite": 800, "unite": "g"},
                {"produit": "Gnocchi frais", "quantite": 400, "unite": "g"},
                {"produit": "Ail de Provence", "quantite": 30, "unite": "g"},
                {"produit": "Huile d'olive extra vierge", "quantite": 100, "unite": "mL"}
            ]
        },
        {
            "nom": "Bœuf Wellington à la truffe",
            "description": "Le 'Filet de bœuf en croûte' tricolore : viande limousine, champignons frais, jus de viande. Le plaisir et ses lettres de noblesse.",
            "categorie": "plat",
            "portions": 4,
            "temps_preparation": 90,
            "prix_vente": 56.00,
            "instructions": "1. Saisir le filet de bœuf\n2. Préparer la duxelles de champignons\n3. Étaler la pâte feuilletée\n4. Assembler avec la truffe\n5. Cuire au four 25 min à 200°C",
            "ingredients": [
                {"produit": "Bœuf Limousin (filet)", "quantite": 800, "unite": "g"},
                {"produit": "Champignons de Paris", "quantite": 300, "unite": "g"},
                {"produit": "Truffe d'été Aestivum", "quantite": 40, "unite": "g"}
            ]
        },
        {
            "nom": "Salade pastèque-féta & menthe ciselée",
            "description": "L'entrée fraîcheur d'Augustine iconique depuis 2020.",
            "categorie": "entrée",
            "portions": 4,
            "temps_preparation": 15,
            "prix_vente": 16.00,
            "instructions": "1. Couper la pastèque en cubes\n2. Émietter la féta\n3. Ciseler la menthe fraîche\n4. Dresser harmonieusement\n5. Arroser d'huile d'olive",
            "ingredients": [
                {"produit": "Pastèque", "quantite": 600, "unite": "g"},
                {"produit": "Féta", "quantite": 200, "unite": "g"},
                {"produit": "Menthe fraîche", "quantite": 2, "unite": "botte"},
                {"produit": "Huile d'olive extra vierge", "quantite": 60, "unite": "mL"}
            ]
        },
        {
            "nom": "Tiramisu de Mamet",
            "description": "Connaissez-vous le Tiramisu d'Augustine ?",
            "categorie": "dessert",
            "portions": 6,
            "temps_preparation": 30,
            "prix_vente": 9.00,
            "instructions": "1. Préparer le café serré\n2. Monter le mascarpone avec les œufs\n3. Tremper les biscuits\n4. Alterner les couches\n5. Réserver au frais 4h minimum",
            "ingredients": [
                {"produit": "Mascarpone", "quantite": 500, "unite": "g"},
                {"produit": "Chocolat noir 70%", "quantite": 100, "unite": "g"}
            ]
        }
    ]
    
    # Créer les recettes
    recettes_count = 0
    for recette_data in demo_recettes:
        existing = await db.recettes.find_one({"nom": recette_data["nom"]})
        if not existing:
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
        "message": "Données de La Table d'Augustine créées avec succès",
        "fournisseurs_crees": len(demo_fournisseurs),
        "produits_crees": len(demo_produits),
        "recettes_creees": recettes_count,
        "restaurant": "La Table d'Augustine - Restaurant méditerranéen avec spécialités provençales et corses"
    }

# Routes pour le traitement OCR
@api_router.post("/ocr/upload-document", response_model=DocumentUploadResponse)
async def upload_and_process_document(
    file: UploadFile = File(...),
    document_type: str = "z_report"  # "z_report" ou "facture_fournisseur"
):
    """Upload et traitement OCR d'un document (photo Z report ou facture)"""
    
    if document_type not in ["z_report", "facture_fournisseur"]:
        raise HTTPException(status_code=400, detail="Type de document invalide. Utilisez 'z_report' ou 'facture_fournisseur'")
    
    # Vérifier le format de fichier
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (JPG, PNG, etc.)")
    
    try:
        # Lire le contenu du fichier
        image_content = await file.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # Extraire le texte avec OCR
        texte_extrait = extract_text_from_image(image_base64)
        
        if not texte_extrait or len(texte_extrait.strip()) < 10:
            raise HTTPException(status_code=400, detail="Impossible d'extraire du texte de l'image. Vérifiez la qualité de l'image.")
        
        # Parser selon le type de document
        donnees_parsees = {}
        if document_type == "z_report":
            z_data = parse_z_report(texte_extrait)
            donnees_parsees = z_data.dict()
        elif document_type == "facture_fournisseur":
            facture_data = parse_facture_fournisseur(texte_extrait)
            donnees_parsees = facture_data.dict()
        
        # Créer le document dans la base
        document = DocumentOCR(
            type_document=document_type,
            nom_fichier=file.filename,
            image_base64=f"data:{file.content_type};base64,{image_base64}",
            texte_extrait=texte_extrait,
            donnees_parsees=donnees_parsees,
            statut="traite",
            date_traitement=datetime.utcnow()
        )
        
        await db.documents_ocr.insert_one(document.dict())
        
        return DocumentUploadResponse(
            document_id=document.id,
            type_document=document_type,
            texte_extrait=texte_extrait,
            donnees_parsees=donnees_parsees,
            message=f"Document {document_type} traité avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")

@api_router.get("/ocr/documents")
async def get_processed_documents(document_type: Optional[str] = None, limit: int = 50):
    """Récupérer l'historique des documents traités"""
    query = {}
    if document_type:
        query["type_document"] = document_type
    
    documents = await db.documents_ocr.find(query).sort("date_upload", -1).limit(limit).to_list(limit)
    
    # Nettoyer les documents pour la sérialisation JSON
    for doc in documents:
        # Supprimer l'_id MongoDB qui cause des problèmes de sérialisation
        if "_id" in doc:
            del doc["_id"]
        # Enlever les images base64 pour alléger la réponse
        if "image_base64" in doc:
            doc["image_base64"] = None
    
    return documents

@api_router.get("/ocr/document/{document_id}")
async def get_document_by_id(document_id: str):
    """Récupérer un document spécifique par son ID"""
    document = await db.documents_ocr.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Supprimer l'_id MongoDB pour éviter les problèmes de sérialisation
    if "_id" in document:
        del document["_id"]
    
    return document

@api_router.post("/ocr/process-z-report/{document_id}")
async def process_z_report_stock_deduction(document_id: str):
    """Traiter un Z report pour déduire automatiquement les stocks"""
    
    # Récupérer le document
    document = await db.documents_ocr.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    if document["type_document"] != "z_report":
        raise HTTPException(status_code=400, detail="Ce document n'est pas un rapport Z")
    
    donnees_parsees = document.get("donnees_parsees", {})
    plats_vendus = donnees_parsees.get("plats_vendus", [])
    
    if not plats_vendus:
        raise HTTPException(status_code=400, detail="Aucun plat trouvé dans le rapport Z")
    
    # Traiter chaque plat vendu
    stock_updates = []
    warnings = []
    
    for plat in plats_vendus:
        nom_plat = plat.get("nom", "").strip()
        quantite_vendue = plat.get("quantite", 0)
        
        if not nom_plat or quantite_vendue <= 0:
            continue
        
        # Rechercher la recette correspondante
        recette = await db.recettes.find_one({
            "$or": [
                {"nom": {"$regex": f".*{nom_plat}.*", "$options": "i"}},
                {"nom": nom_plat}
            ]
        })
        
        if not recette:
            warnings.append(f"Recette non trouvée pour: {nom_plat}")
            continue
        
        # Déduire les ingrédients du stock
        for ingredient in recette.get("ingredients", []):
            produit_id = ingredient.get("produit_id")
            if not produit_id:
                continue
            
            # Calculer la quantité à déduire
            quantite_par_portion = ingredient.get("quantite", 0) / recette.get("portions", 1)
            quantite_a_deduire = quantite_par_portion * quantite_vendue
            
            # Mettre à jour le stock
            stock = await db.stocks.find_one({"produit_id": produit_id})
            if stock:
                nouvelle_quantite = max(0, stock["quantite_actuelle"] - quantite_a_deduire)
                
                await db.stocks.update_one(
                    {"produit_id": produit_id},
                    {"$set": {
                        "quantite_actuelle": nouvelle_quantite,
                        "derniere_maj": datetime.utcnow()
                    }}
                )
                
                # Créer un mouvement de stock
                mouvement = MouvementStock(
                    produit_id=produit_id,
                    produit_nom=ingredient.get("produit_nom", ""),
                    type="sortie",
                    quantite=quantite_a_deduire,
                    reference=f"Z-Report-{document_id[:8]}",
                    commentaire=f"Déduction automatique pour {quantite_vendue}x {nom_plat}",
                    fournisseur_nom="Système automatique"
                )
                
                await db.mouvements_stock.insert_one(mouvement.dict())
                
                stock_updates.append({
                    "produit_nom": ingredient.get("produit_nom", ""),
                    "quantite_deduite": quantite_a_deduire,
                    "nouvelle_quantite": nouvelle_quantite,
                    "plat": nom_plat,
                    "portions_vendues": quantite_vendue
                })
            else:
                warnings.append(f"Stock non trouvé pour le produit ID: {produit_id}")
    
    # Marquer le document comme traité
    await db.documents_ocr.update_one(
        {"id": document_id},
        {"$set": {
            "statut": "stock_traite",
            "date_traitement_stock": datetime.utcnow()
        }}
    )
    
    return {
        "message": f"Traitement terminé. {len(stock_updates)} mises à jour de stock effectuées.",
        "stock_updates": stock_updates,
        "warnings": warnings
    }

@api_router.delete("/ocr/document/{document_id}")
async def delete_document(document_id: str):
    """Supprimer un document OCR"""
    result = await db.documents_ocr.delete_one({"id": document_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return {"message": "Document supprimé"}

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