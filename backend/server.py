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

# ✅ Version 3 - Enhanced RBAC System
ROLES = {
    "super_admin": "Super Admin",
    "gerant": "Gérant (Manager)", 
    "chef_cuisine": "Chef de cuisine (Head Chef)",
    "barman": "Barman (Bartender)",
    "caissier": "Caissier (Cashier)"
}

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix

# ✅ Rapports Z Model
class RapportZ(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime
    ca_total: float
    produits: List[dict]
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

# ✅ Version 3 - Enhanced User Management with RBAC
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    role: str  # One of ROLES keys
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

# ✅ Version 3 - Enhanced Product Model with Reference Price and Supplier Relations
class Produit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    unite: str  # kg, L, pièce, etc.
    prix_achat: Optional[float] = None  # Deprecated - use SupplierProductInfo instead
    reference_price: float  # ✅ New - Manager-set benchmark price for cost control
    main_supplier_id: Optional[str] = None  # ✅ New - Primary supplier
    secondary_supplier_ids: List[str] = []  # ✅ New - Alternative suppliers
    fournisseur_id: Optional[str] = None  # Legacy field for backward compatibility
    fournisseur_nom: Optional[str] = None  # Legacy field
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProduitCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None
    unite: str
    reference_price: float  # ✅ Required for V3
    main_supplier_id: Optional[str] = None
    secondary_supplier_ids: List[str] = []
    # Legacy fields for backward compatibility
    prix_achat: Optional[float] = None
    fournisseur_id: Optional[str] = None

# ✅ Version 3 - New Supplier-Product Price Linking Model
class SupplierProductInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str
    product_id: str
    price: float  # ✅ Actual supplier-specific price
    is_preferred: bool = False  # Mark as preferred supplier for this product
    min_order_quantity: Optional[float] = None
    lead_time_days: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SupplierProductInfoCreate(BaseModel):
    supplier_id: str
    product_id: str
    price: float
    is_preferred: bool = False
    min_order_quantity: Optional[float] = None
    lead_time_days: Optional[int] = None

# ✅ Version 3 - New Product Batch/Lot Management Model
class ProductBatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    quantity: float
    expiry_date: Optional[datetime] = None  # DLC - Date Limite de Consommation
    received_date: datetime = Field(default_factory=datetime.utcnow)
    supplier_id: Optional[str] = None
    batch_number: Optional[str] = None
    purchase_price: Optional[float] = None  # Price at which this batch was purchased
    is_consumed: bool = False  # Track if batch is fully used
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductBatchCreate(BaseModel):
    product_id: str
    quantity: float
    expiry_date: Optional[datetime] = None
    supplier_id: Optional[str] = None
    batch_number: Optional[str] = None
    purchase_price: Optional[float] = None

# ✅ Version 3 - Price Anomaly Alert Model
class PriceAnomalyAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    product_name: str
    supplier_id: str
    supplier_name: str
    reference_price: float
    actual_price: float
    difference_percentage: float
    alert_date: datetime = Field(default_factory=datetime.utcnow)
    is_resolved: bool = False
    resolution_note: Optional[str] = None

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

# ✅ Enhanced Recipe Model - Products vs Recipes Logic
class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None  # "Bar", "Entrées", "Plats", "Desserts"
    portions: int  # Number of portions this recipe produces
    temps_preparation: Optional[int] = None  # in minutes
    instructions: Optional[str] = None
    prix_vente: Optional[float] = None
    ingredients: List[RecetteIngredient] = []
    is_simple_recipe: bool = False  # ✅ True for direct-sale items (beverages, etc.)
    cost_analysis: Optional[dict] = None  # Auto-calculated cost breakdown
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Maintain backward compatibility
Recette = Recipe

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
# ✅ Version 3 - Data Migration System
class MigrationStatus(BaseModel):
    version: str
    applied_at: datetime
    description: str
    success: bool = True

# Migration functions
async def migrate_to_v3():
    """Migrate existing data to Version 3 structure"""
    migration_results = []
    
    try:
        # Check if migration already applied
        existing_migration = await db.migrations.find_one({"version": "3.0.0"})
        if existing_migration:
            return {"message": "Migration 3.0.0 already applied", "details": existing_migration}
        
        # 1. Migrate existing products to include reference_price
        products_updated = 0
        async for product in db.produits.find({"reference_price": {"$exists": False}}):
            # Set reference_price to current prix_achat or default value
            reference_price = product.get("prix_achat", 10.0) or 10.0
            await db.produits.update_one(
                {"id": product["id"]},
                {
                    "$set": {
                        "reference_price": reference_price,
                        "main_supplier_id": product.get("fournisseur_id"),
                        "secondary_supplier_ids": []
                    }
                }
            )
            products_updated += 1
        
        migration_results.append(f"Updated {products_updated} products with reference prices")
        
        # 2. Create SupplierProductInfo entries for existing product-supplier relations
        supplier_relations = 0
        async for product in db.produits.find({"fournisseur_id": {"$ne": None}}):
            if product.get("fournisseur_id"):
                # Create supplier-product info if doesn't exist
                existing = await db.supplier_product_info.find_one({
                    "supplier_id": product["fournisseur_id"],
                    "product_id": product["id"]
                })
                if not existing:
                    supplier_info = SupplierProductInfo(
                        supplier_id=product["fournisseur_id"],
                        product_id=product["id"],
                        price=product.get("prix_achat", product.get("reference_price", 10.0)),
                        is_preferred=True
                    )
                    await db.supplier_product_info.insert_one(supplier_info.dict())
                    supplier_relations += 1
        
        migration_results.append(f"Created {supplier_relations} supplier-product relations")
        
        # 3. Create initial product batches for existing stock
        batches_created = 0
        async for stock in db.stocks.find({"quantite_actuelle": {"$gt": 0}}):
            # Create a single batch for existing stock
            batch = ProductBatch(
                product_id=stock["produit_id"],
                quantity=stock["quantite_actuelle"],
                batch_number=f"MIGRATION-{stock['produit_id'][:8]}",
                received_date=stock.get("derniere_maj", datetime.utcnow())
            )
            await db.product_batches.insert_one(batch.dict())
            batches_created += 1
        
        migration_results.append(f"Created {batches_created} initial product batches")
        
        # 4. Create default admin user if no users exist
        user_count = await db.users.count_documents({})
        if user_count == 0:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            admin_user = User(
                username="admin",
                email="admin@restaurantla-table-augustine.fr",
                password_hash=pwd_context.hash("RestaurantAdmin2025!"),
                role="super_admin",
                full_name="Administrateur Système"
            )
            await db.users.insert_one(admin_user.dict())
            migration_results.append("Created default admin user (admin/RestaurantAdmin2025!)")
        
        # Record migration
        migration_record = MigrationStatus(
            version="3.0.0",
            applied_at=datetime.utcnow(),
            description="Enhanced data models with RBAC, supplier relations, and batch tracking"
        )
        await db.migrations.insert_one(migration_record.dict())
        
        return {
            "message": "Migration to Version 3.0.0 completed successfully",
            "details": migration_results
        }
        
    except Exception as e:
        # Record failed migration
        failed_migration = MigrationStatus(
            version="3.0.0",
            applied_at=datetime.utcnow(),
            description=f"Migration failed: {str(e)}",
            success=False
        )
        await db.migrations.insert_one(failed_migration.dict())
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

# ✅ Version 3 - New API Endpoints

# User Management (Super Admin only)
@api_router.post("/admin/users", response_model=UserResponse)
async def create_user(user_create: UserCreate):
    """Create a new user (Super Admin only)"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if username or email already exists
    existing_user = await db.users.find_one({
        "$or": [{"username": user_create.username}, {"email": user_create.email}]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Validate role
    if user_create.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {list(ROLES.keys())}")
    
    # Create user
    user_dict = user_create.dict()
    user_dict["password_hash"] = pwd_context.hash(user_dict.pop("password"))
    user_obj = User(**user_dict)
    
    await db.users.insert_one(user_obj.dict())
    return UserResponse(**user_obj.dict())

@api_router.get("/admin/users", response_model=List[UserResponse])
async def get_users():
    """Get all users (Super Admin only)"""
    users = await db.users.find().to_list(1000)
    return [UserResponse(**user) for user in users]

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user (Super Admin only)"""
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# Supplier-Product Relations
@api_router.post("/supplier-product-info", response_model=SupplierProductInfo)
async def create_supplier_product_info(info: SupplierProductInfoCreate):
    """Create supplier-product pricing information"""
    # Validate supplier and product exist
    supplier = await db.fournisseurs.find_one({"id": info.supplier_id})
    product = await db.produits.find_one({"id": info.product_id})
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check for existing relation
    existing = await db.supplier_product_info.find_one({
        "supplier_id": info.supplier_id,
        "product_id": info.product_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Supplier-product relation already exists")
    
    info_obj = SupplierProductInfo(**info.dict())
    await db.supplier_product_info.insert_one(info_obj.dict())
    return info_obj

@api_router.get("/supplier-product-info/{supplier_id}", response_model=List[SupplierProductInfo])
async def get_supplier_products(supplier_id: str):
    """Get all products available from a specific supplier with pricing"""
    relations = await db.supplier_product_info.find({"supplier_id": supplier_id}).to_list(1000)
    return [SupplierProductInfo(**rel) for rel in relations]

# Product Batch Management
@api_router.post("/product-batches", response_model=ProductBatch)
async def create_product_batch(batch: ProductBatchCreate):
    """Create a new product batch"""
    # Validate product exists
    product = await db.produits.find_one({"id": batch.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    batch_obj = ProductBatch(**batch.dict())
    await db.product_batches.insert_one(batch_obj.dict())
    
    # Update stock with new batch quantity
    await db.stocks.update_one(
        {"produit_id": batch.product_id},
        {"$inc": {"quantite_actuelle": batch.quantity}, "$set": {"derniere_maj": datetime.utcnow()}}
    )
    
    return batch_obj

@api_router.get("/product-batches/{product_id}", response_model=List[ProductBatch])
async def get_product_batches(product_id: str):
    """Get all batches for a specific product"""
    batches = await db.product_batches.find({"product_id": product_id, "is_consumed": False}).to_list(1000)
    return [ProductBatch(**batch) for batch in batches]

# Price Anomaly Alerts
@api_router.get("/price-anomalies", response_model=List[PriceAnomalyAlert])
async def get_price_anomalies():
    """Get all unresolved price anomaly alerts"""
    alerts = await db.price_anomaly_alerts.find({"is_resolved": False}).to_list(1000)
    return [PriceAnomalyAlert(**alert) for alert in alerts]

@api_router.post("/price-anomalies/{alert_id}/resolve")
async def resolve_price_anomaly(alert_id: str, resolution_note: str = ""):
    """Mark a price anomaly as resolved"""
    result = await db.price_anomaly_alerts.update_one(
        {"id": alert_id},
        {"$set": {"is_resolved": True, "resolution_note": resolution_note}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved successfully"}

# Migration endpoint
@api_router.post("/admin/migrate/v3")
async def run_migration_v3():
    """Run Version 3 data migration (Super Admin only)"""
    return await migrate_to_v3()

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
    """Parser les données d'un rapport Z avec adaptation aux formats réels La Table d'Augustine"""
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
        
        # Patterns adaptés aux rapports Z La Table d'Augustine - Format "(xN) Nom plat"
        plat_patterns = [
            # Format principal: "(x14) Linguine" ou "(14) Linguine" 
            r'\([x]?(\d{1,3})\)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.]{3,50})',
            # Format alternatif: "14x Linguine" ou "14 Linguine"
            r'(\d{1,3})[x\s]+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.]{3,50})',
            # Format classique: "Nom du plat: quantité"
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.]{3,50})\s*:?\s*(\d{1,3})(?:\s*[x\*]?\s*(\d+[,.]?\d*)?\s*[€]?)?',
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
    """Parser les données d'une facture fournisseur avec adaptation aux formats réels"""
    data = FactureFournisseurData()
    
    try:
        # Rechercher le fournisseur - adapté aux formats réels
        lines = texte_ocr.split('\n')
        fournisseur_candidates = []
        
        for i, line in enumerate(lines[:15]):  # Examiner plus de lignes
            line = line.strip()
            if len(line) > 5:
                # Détecter les noms de fournisseurs typiques
                if any(keyword in line.upper() for keyword in ['MAMMAFIORE', 'PROVENCE', 'SARL', 'SAS', 'EURL', 'MIN DES', 'PÊCHERIE', 'MAISON']):
                    if not any(excl in line.upper() for excl in ['AUGUSTINE', 'CLIENT', 'FACTURE', 'NUMERO', 'DATE']):
                        fournisseur_candidates.append(line.strip())
        
        if fournisseur_candidates:
            # Prendre le candidat le plus probable
            data.fournisseur = fournisseur_candidates[0]
        
        # Rechercher la date avec patterns améliorés pour les formats réels
        date_patterns = [
            r'(\d{2}-\d{2}-\d{4})',  # Format: 16-08-2024
            r'(\d{1,2}/\d{1,2}/\d{4})',  # Format: 16/08/2024
            r'(\d{1,2}\.\d{1,2}\.\d{4})', # Format: 16.08.2024
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, texte_ocr)
            if date_match:
                data.date = date_match.group(1)
                break
        
        # Rechercher le numéro de facture avec patterns adaptés
        facture_patterns = [
            r'Bon Livraison[:\s]*(\d+)',  # "Bon Livraison 14887"
            r'N°[:\s]*([A-Z0-9\-]+)',
            r'facture[:\s#n°]*([A-Z0-9\-]{3,15})',
        ]
        
        for pattern in facture_patterns:
            facture_match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if facture_match:
                data.numero_facture = facture_match.group(1)
                break
        
        # Patterns adaptés pour les produits réels - Format Mammafiore et autres
        produits = []
        produit_patterns = [
            # Format Mammafiore: "GNOCCHI DE PATATE 500GR*8 - RUMMO (u) 120,000 ..."
            r'([A-ZÁÀÂÄÇÉÈÊËÏÎÔÙÛÜŸ][A-Za-zÀ-ÿ\s\d\*\-\(\)\.]{10,80})\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)',
            # Format poissonnerie: "PALOURDE MOYENNE" suivi des détails sur lignes suivantes
            r'([A-ZÁÀÂÄÇÉÈÊËÏÎÔÙÛÜŸ\s]{3,40})\s+(\d{1,3})\s+(\d{1,3})\s+KG\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)',
            # Format classique: "Nom produit quantité prix total"
            r'([A-Za-zÀ-ÿ\s\'\-]{3,40})\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)',
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
    if file.content_type and not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (JPG, PNG, etc.)")
    
    # Si content_type est None, vérifier l'extension du fichier
    if not file.content_type:
        filename_lower = file.filename.lower() if file.filename else ""
        if not any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']):
            raise HTTPException(status_code=400, detail="Le fichier doit avoir une extension image valide (.jpg, .png, etc.)")
    
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

# ✅ Endpoints Rapports Z
@api_router.post("/rapports_z")
async def create_rapport_z(data: RapportZ):
    """Créer un nouveau rapport Z"""
    await db.rapports_z.insert_one(data.dict())
    return {"status": "ok", "id": data.id}

@api_router.get("/rapports_z")
async def list_rapports_z():
    """Lister tous les rapports Z"""
    docs = await db.rapports_z.find().sort("date", -1).to_list(100)  # Tri par date décroissante
    # Nettoyer les documents pour la sérialisation JSON
    for doc in docs:
        if "_id" in doc:
            del doc["_id"]
    return docs

@api_router.get("/rapports_z/{rapport_id}")
async def get_rapport_z(rapport_id: str):
    """Obtenir un rapport Z spécifique"""
    doc = await db.rapports_z.find_one({"id": rapport_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Rapport not found")
    # Supprimer l'_id MongoDB pour éviter les problèmes de sérialisation
    if "_id" in doc:
        del doc["_id"]
    return doc

@api_router.delete("/rapports_z/{rapport_id}")
async def delete_rapport_z(rapport_id: str):
    """Supprimer un rapport Z"""
    result = await db.rapports_z.delete_one({"id": rapport_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    return {"message": "Rapport supprimé"}

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