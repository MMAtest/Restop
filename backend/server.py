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
from datetime import datetime, timedelta
import io
import pandas as pd
import json

# Imports pour OCR
import pytesseract
import cv2
import numpy as np
from PIL import Image
import PyPDF2
import pdfplumber
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
    reference_price: Optional[float] = 10.0  # ✅ New - Manager-set benchmark price for cost control
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
    reference_price: Optional[float] = None  # ✅ Optional for backward compatibility
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
    file_type: str = "image"  # "image" ou "pdf" - nouveau champ V3

class DocumentUploadResponse(BaseModel):
    document_id: str
    type_document: str
    texte_extrait: str
    donnees_parsees: dict
    message: str
    file_type: str  # Add file_type to response

# ✅ Version 3 Feature #2 - Enhanced OCR Models for Structured Parsing
class StructuredZReportItem(BaseModel):
    name: str
    quantity_sold: int
    category: str  # "Bar", "Entrées", "Plats", "Desserts"
    unit_price: Optional[float] = None
    total_price: Optional[float] = None

class StructuredZReportData(BaseModel):
    report_date: Optional[str] = None
    service: Optional[str] = None  # "Midi", "Soir", etc.
    items_by_category: dict = {}  # {"Bar": [...], "Entrées": [...], etc.}
    grand_total_sales: Optional[float] = None
    raw_items: List[dict] = []  # Original parsed items for reference

class StockDeductionProposal(BaseModel):
    recipe_name: str
    quantity_sold: int
    ingredient_deductions: List[dict]  # [{"product_name": "", "current_stock": 0, "deduction": 0, "new_stock": 0}]
    warnings: List[str] = []  # Warnings about insufficient stock, etc.

class ZReportValidationResult(BaseModel):
    can_validate: bool
    proposed_deductions: List[StockDeductionProposal]
    total_deductions: int
    warnings: List[str] = []
    errors: List[str] = []

# Backward compatibility - Legacy ZReportData model
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

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using multiple methods for best results"""
    extracted_text = ""
    
    try:
        # Method 1: Try pdfplumber first (better for complex layouts)
        import io
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
        
        if extracted_text.strip():
            print(f"✅ PDF text extracted with pdfplumber: {len(extracted_text)} characters")
            return extracted_text
            
    except Exception as e:
        print(f"⚠️ pdfplumber failed: {str(e)}")
    
    try:
        # Method 2: Fallback to PyPDF2
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n"
        
        if extracted_text.strip():
            print(f"✅ PDF text extracted with PyPDF2: {len(extracted_text)} characters")
            return extracted_text
            
    except Exception as e:
        print(f"⚠️ PyPDF2 failed: {str(e)}")
    
    if not extracted_text.strip():
        print("❌ No text could be extracted from PDF - might be image-based PDF")
        return "Erreur: Impossible d'extraire le texte du PDF. Il s'agit peut-être d'un PDF contenant uniquement des images."
    
    return extracted_text

def detect_file_type(filename: str, content_type: str = None) -> str:
    """Detect if file is image or PDF"""
    filename_lower = filename.lower() if filename else ""
    
    # Check by content type first
    if content_type:
        if content_type.startswith('image/'):
            return 'image'
        elif content_type == 'application/pdf':
            return 'pdf'
    
    # Check by file extension
    if filename_lower.endswith(('.pdf',)):
        return 'pdf'
    elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
        return 'image'
    
    # Default to image for backward compatibility
    return 'image'

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

# ✅ Version 3 - Analytics & Profitability Models
class RecipeProfitability(BaseModel):
    recipe_id: str
    recipe_name: str
    selling_price: Optional[float] = None
    ingredient_cost: float
    profit_margin: float
    profit_percentage: float
    portions_sold: int = 0
    total_revenue: float = 0
    total_profit: float = 0

class SalesPerformance(BaseModel):
    period: str  # "daily", "weekly", "monthly"
    total_sales: float
    total_orders: int
    average_order_value: float
    top_recipes: List[dict]
    sales_by_category: dict
    growth_percentage: Optional[float] = None

class AlertCenter(BaseModel):
    expiring_products: List[dict]  # Products with short DLC
    price_anomalies: List[dict]    # Price deviations
    low_stock_items: List[dict]    # Items below minimum stock
    unused_stock: List[dict]       # Items with no recent movement
    total_alerts: int

class CostAnalysis(BaseModel):
    total_inventory_value: float
    avg_cost_per_recipe: float
    most_expensive_ingredients: List[dict]
    cost_trends: dict
    waste_analysis: dict

# ✅ Version 3 Feature #3 - Advanced Stock Management Models
class AdvancedStockAdjustment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    adjustment_type: str  # "ingredient" or "prepared_dish"
    target_id: str  # product_id for ingredient, recipe_id for prepared_dish
    target_name: str
    adjustment_reason: str
    quantity_adjusted: float
    user_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ingredient_deductions: List[dict] = []  # For prepared_dish adjustments

class StockAdjustmentRequest(BaseModel):
    adjustment_type: str  # "ingredient" or "prepared_dish" 
    target_id: str
    quantity_adjusted: float
    adjustment_reason: str
    user_name: Optional[str] = "System"

class BatchStockInfo(BaseModel):
    product_id: str
    product_name: str
    total_stock: float
    batches: List[dict]  # ProductBatch info with expiry status
    critical_batches: int  # Count of batches expiring soon
    expired_batches: int  # Count of expired batches

# ✅ Version 3 Feature #3 - Advanced Stock Management API Endpoints

@api_router.post("/stock/advanced-adjustment", response_model=AdvancedStockAdjustment)
async def create_advanced_stock_adjustment(adjustment: StockAdjustmentRequest):
    """Create advanced stock adjustment - ingredient or prepared dish"""
    try:
        adjustment_record = AdvancedStockAdjustment(
            adjustment_type=adjustment.adjustment_type,
            target_id=adjustment.target_id,
            target_name="",
            adjustment_reason=adjustment.adjustment_reason,
            quantity_adjusted=adjustment.quantity_adjusted,
            user_name=adjustment.user_name
        )
        
        if adjustment.adjustment_type == "ingredient":
            # Direct ingredient adjustment
            product = await db.produits.find_one({"id": adjustment.target_id})
            if not product:
                raise HTTPException(status_code=404, detail="Produit non trouvé")
            
            adjustment_record.target_name = product["nom"]
            
            # Update stock directly
            stock = await db.stocks.find_one({"produit_id": adjustment.target_id})
            if stock:
                new_quantity = max(0, stock["quantite_actuelle"] + adjustment.quantity_adjusted)
                await db.stocks.update_one(
                    {"produit_id": adjustment.target_id},
                    {
                        "$set": {
                            "quantite_actuelle": new_quantity,
                            "derniere_maj": datetime.utcnow()
                        }
                    }
                )
                
                # Create stock movement
                movement_type = "entree" if adjustment.quantity_adjusted > 0 else "sortie"
                mouvement = MouvementStock(
                    produit_id=adjustment.target_id,
                    produit_nom=product["nom"],
                    type=movement_type,
                    quantite=abs(adjustment.quantity_adjusted),
                    commentaire=f"Ajustement avancé: {adjustment.adjustment_reason}"
                )
                await db.mouvements_stock.insert_one(mouvement.dict())
            else:
                raise HTTPException(status_code=404, detail="Stock non trouvé pour ce produit")
                
        elif adjustment.adjustment_type == "prepared_dish":
            # Prepared dish adjustment - deduct all ingredients
            recipe = await db.recettes.find_one({"id": adjustment.target_id})
            if not recipe:
                raise HTTPException(status_code=404, detail="Recette non trouvée")
            
            adjustment_record.target_name = recipe["nom"]
            ingredient_deductions = []
            
            # Calculate ingredient deductions
            portions_adjusted = abs(adjustment.quantity_adjusted)
            recipe_portions = recipe.get("portions", 1)
            
            for ingredient in recipe.get("ingredients", []):
                # Calculate deduction per portion
                qty_per_portion = ingredient["quantite"] / recipe_portions
                total_deduction = qty_per_portion * portions_adjusted
                
                # Update stock
                stock = await db.stocks.find_one({"produit_id": ingredient["produit_id"]})
                if stock:
                    current_stock = stock["quantite_actuelle"]
                    new_stock = max(0, current_stock - total_deduction)
                    
                    await db.stocks.update_one(
                        {"produit_id": ingredient["produit_id"]},
                        {
                            "$set": {
                                "quantite_actuelle": new_stock,
                                "derniere_maj": datetime.utcnow()
                            }
                        }
                    )
                    
                    # Create stock movement
                    mouvement = MouvementStock(
                        produit_id=ingredient["produit_id"],
                        produit_nom=ingredient.get("produit_nom", "Ingrédient"),
                        type="sortie",
                        quantite=total_deduction,
                        commentaire=f"Déduction plat préparé: {recipe['nom']} (x{portions_adjusted}) - {adjustment.adjustment_reason}"
                    )
                    await db.mouvements_stock.insert_one(mouvement.dict())
                    
                    ingredient_deductions.append({
                        "product_id": ingredient["produit_id"],
                        "product_name": ingredient.get("produit_nom", "Ingrédient"),
                        "quantity_deducted": total_deduction,
                        "previous_stock": current_stock,
                        "new_stock": new_stock
                    })
            
            adjustment_record.ingredient_deductions = ingredient_deductions
        else:
            raise HTTPException(status_code=400, detail="Type d'ajustement invalide")
        
        # Save adjustment record
        await db.advanced_stock_adjustments.insert_one(adjustment_record.dict())
        
        return adjustment_record
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajustement: {str(e)}")

@api_router.get("/stock/adjustments-history", response_model=List[AdvancedStockAdjustment])
async def get_stock_adjustments_history():
    """Get history of all stock adjustments"""
    try:
        adjustments = await db.advanced_stock_adjustments.find().sort("created_at", -1).to_list(1000)
        return [AdvancedStockAdjustment(**adj) for adj in adjustments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

@api_router.get("/stock/batch-info/{product_id}", response_model=BatchStockInfo)
async def get_product_batch_info(product_id: str):
    """Get batch information for a specific product"""
    try:
        product = await db.produits.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        
        # Get stock info
        stock = await db.stocks.find_one({"produit_id": product_id})
        total_stock = stock["quantite_actuelle"] if stock else 0
        
        # Get batches
        batches = await db.product_batches.find({
            "product_id": product_id,
            "is_consumed": False
        }).sort("expiry_date", 1).to_list(1000)
        
        # Process batch information
        processed_batches = []
        critical_count = 0
        expired_count = 0
        now = datetime.utcnow()
        critical_threshold = now + timedelta(days=7)
        
        for batch in batches:
            batch_info = {
                "id": batch["id"],
                "quantity": batch["quantity"],
                "received_date": batch["received_date"].isoformat(),
                "expiry_date": batch["expiry_date"].isoformat() if batch.get("expiry_date") else None,
                "batch_number": batch.get("batch_number"),
                "supplier_id": batch.get("supplier_id"),
                "status": "good"
            }
            
            if batch.get("expiry_date"):
                if batch["expiry_date"] < now:
                    batch_info["status"] = "expired"
                    expired_count += 1
                elif batch["expiry_date"] < critical_threshold:
                    batch_info["status"] = "critical"
                    critical_count += 1
            
            processed_batches.append(batch_info)
        
        return BatchStockInfo(
            product_id=product_id,
            product_name=product["nom"],
            total_stock=total_stock,
            batches=processed_batches,
            critical_batches=critical_count,
            expired_batches=expired_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des lots: {str(e)}")

@api_router.get("/stock/batch-summary", response_model=List[BatchStockInfo])
async def get_batch_summary():
    """Get batch summary for all products with batches"""
    try:
        # Get all products with batches
        pipeline = [
            {"$lookup": {
                "from": "product_batches",
                "localField": "id",
                "foreignField": "product_id",
                "as": "batches"
            }},
            {"$match": {"batches": {"$ne": []}}},
            {"$limit": 100}
        ]
        
        # Since we're using motor, we need to do this differently
        products = await db.produits.find().to_list(1000)
        batch_summaries = []
        
        for product in products:
            # Check if product has batches
            has_batches = await db.product_batches.count_documents({
                "product_id": product["id"],
                "is_consumed": False
            })
            
            if has_batches > 0:
                batch_info = await get_product_batch_info(product["id"])
                batch_summaries.append(batch_info)
        
        return batch_summaries[:50]  # Limit to first 50 for performance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du résumé des lots: {str(e)}")

@api_router.put("/stock/consume-batch/{batch_id}")
async def consume_batch(batch_id: str, quantity_consumed: float):
    """Mark a batch as partially or fully consumed"""
    try:
        batch = await db.product_batches.find_one({"id": batch_id})
        if not batch:
            raise HTTPException(status_code=404, detail="Lot non trouvé")
        
        remaining_quantity = batch["quantity"] - quantity_consumed
        
        if remaining_quantity <= 0:
            # Mark batch as fully consumed
            await db.product_batches.update_one(
                {"id": batch_id},
                {"$set": {"is_consumed": True, "quantity": 0}}
            )
        else:
            # Update remaining quantity
            await db.product_batches.update_one(
                {"id": batch_id},
                {"$set": {"quantity": remaining_quantity}}
            )
        
        # Update total stock
        await db.stocks.update_one(
            {"produit_id": batch["product_id"]},
            {
                "$inc": {"quantite_actuelle": -quantity_consumed},
                "$set": {"derniere_maj": datetime.utcnow()}
            }
        )
        
        # Create stock movement
        product = await db.produits.find_one({"id": batch["product_id"]})
        mouvement = MouvementStock(
            produit_id=batch["product_id"],
            produit_nom=product["nom"] if product else "Produit",
            type="sortie",
            quantite=quantity_consumed,
            commentaire=f"Consommation lot {batch.get('batch_number', batch_id[:8])}"
        )
        await db.mouvements_stock.insert_one(mouvement.dict())
        
        return {"message": "Lot mis à jour avec succès", "remaining_quantity": max(0, remaining_quantity)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la consommation: {str(e)}")

# ✅ Version 3 Feature #2 - Enhanced OCR API Endpoints

@api_router.post("/ocr/parse-z-report-enhanced", response_model=StructuredZReportData)
async def parse_z_report_enhanced_endpoint(document_id: str):
    """Parse Z report with enhanced structured extraction"""
    try:
        document = await db.documents_ocr.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        if document["type_document"] != "z_report":
            raise HTTPException(status_code=400, detail="Le document doit être un rapport Z")
        
        if not document.get("texte_extrait"):
            raise HTTPException(status_code=400, detail="Aucun texte extrait disponible")
        
        # Parse with enhanced function
        structured_data = parse_z_report_enhanced(document["texte_extrait"])
        
        # Update document with structured data
        await db.documents_ocr.update_one(
            {"id": document_id},
            {"$set": {"donnees_parsees": structured_data.dict(), "statut": "traite"}}
        )
        
        return structured_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du parsing: {str(e)}")

@api_router.post("/ocr/calculate-stock-deductions", response_model=ZReportValidationResult)
async def calculate_stock_deductions_endpoint(structured_data: StructuredZReportData):
    """Calculate proposed stock deductions based on structured Z report data"""
    try:
        validation_result = await calculate_stock_deductions(structured_data)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des déductions: {str(e)}")

@api_router.post("/ocr/validate-z-report")
async def validate_z_report_endpoint(document_id: str, apply_deductions: bool = False):
    """Validate Z report and optionally apply stock deductions"""
    try:
        # Get the document
        document = await db.documents_ocr.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Parse with enhanced function
        structured_data = parse_z_report_enhanced(document["texte_extrait"])
        
        # Calculate deductions
        validation_result = await calculate_stock_deductions(structured_data)
        
        response = {
            "document_id": document_id,
            "structured_data": structured_data.dict(),
            "validation_result": validation_result.dict(),
            "applied": False
        }
        
        # Apply deductions if requested and validation is successful
        if apply_deductions and validation_result.can_validate:
            deduction_result = await apply_stock_deductions(validation_result)
            response["deduction_result"] = deduction_result
            response["applied"] = deduction_result.get("success", False)
            
            # Create RapportZ entry if deductions were applied successfully
            if deduction_result.get("success"):
                rapport_z = RapportZ(
                    date=datetime.utcnow(),
                    ca_total=structured_data.grand_total_sales or 0,
                    produits=[
                        {
                            "nom": item["name"],
                            "quantite": item["quantity_sold"],
                            "prix": item.get("unit_price", 0),
                            "categorie": item["category"]
                        }
                        for category_items in structured_data.items_by_category.values()
                        for item in category_items
                    ]
                )
                await db.rapports_z.insert_one(rapport_z.dict())
                response["rapport_z_created"] = True
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la validation: {str(e)}")

@api_router.get("/ocr/z-report-preview/{document_id}", response_model=dict)
async def get_z_report_preview(document_id: str):
    """Get a preview of structured Z report data without applying changes"""
    try:
        document = await db.documents_ocr.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        if document["type_document"] != "z_report":
            raise HTTPException(status_code=400, detail="Le document doit être un rapport Z")
        
        # Parse with enhanced function
        structured_data = parse_z_report_enhanced(document["texte_extrait"])
        
        # Calculate potential deductions
        validation_result = await calculate_stock_deductions(structured_data)
        
        return {
            "document_id": document_id,
            "structured_data": structured_data.dict(),
            "validation_result": validation_result.dict(),
            "can_apply": validation_result.can_validate,
            "preview_only": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'aperçu: {str(e)}")

# ✅ Version 3 - Analytics & Profitability API Endpoints

@api_router.get("/analytics/profitability", response_model=List[RecipeProfitability])
async def get_recipe_profitability():
    """Calculate profitability for all recipes"""
    recipes = await db.recettes.find().to_list(1000)
    profitability_data = []
    
    for recipe in recipes:
        # Calculate ingredient cost
        ingredient_cost = 0.0
        for ingredient in recipe.get("ingredients", []):
            # Get product price from supplier info or reference price
            product = await db.produits.find_one({"id": ingredient["produit_id"]})
            if product:
                # Try to get best supplier price, fallback to reference price
                supplier_info = await db.supplier_product_info.find_one({
                    "product_id": ingredient["produit_id"],
                    "is_preferred": True
                })
                unit_price = supplier_info["price"] if supplier_info else product.get("reference_price", 0)
                ingredient_cost += (ingredient["quantite"] / recipe["portions"]) * unit_price
        
        # Calculate profitability
        selling_price = recipe.get("prix_vente", 0) or 0
        profit_margin = selling_price - ingredient_cost
        profit_percentage = (profit_margin / selling_price * 100) if selling_price > 0 else 0
        
        # Get sales data from Rapports Z (simplified for now)
        portions_sold = 0
        rapports = await db.rapports_z.find().to_list(1000)
        for rapport in rapports:
            for produit in rapport.get("produits", []):
                if recipe["nom"].lower() in produit.get("nom", "").lower():
                    portions_sold += produit.get("quantite", 0)
        
        total_revenue = portions_sold * selling_price
        total_profit = portions_sold * profit_margin
        
        profitability_data.append(RecipeProfitability(
            recipe_id=recipe["id"],
            recipe_name=recipe["nom"],
            selling_price=selling_price,
            ingredient_cost=ingredient_cost,
            profit_margin=profit_margin,
            profit_percentage=profit_percentage,
            portions_sold=portions_sold,
            total_revenue=total_revenue,
            total_profit=total_profit
        ))
    
    # Sort by profit percentage descending
    profitability_data.sort(key=lambda x: x.profit_percentage, reverse=True)
    return profitability_data

@api_router.get("/analytics/sales-performance", response_model=SalesPerformance)
async def get_sales_performance(period: str = "monthly"):
    """Get sales performance analysis"""
    # Get all Rapports Z
    rapports = await db.rapports_z.find().to_list(1000)
    
    if not rapports:
        return SalesPerformance(
            period=period,
            total_sales=0,
            total_orders=0,
            average_order_value=0,
            top_recipes=[],
            sales_by_category={}
        )
    
    # Calculate totals
    total_sales = sum(rapport.get("ca_total", 0) for rapport in rapports)
    total_orders = len(rapports)
    average_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # Calculate top recipes
    recipe_sales = {}
    category_sales = {"Bar": 0, "Entrées": 0, "Plats": 0, "Desserts": 0}
    
    for rapport in rapports:
        for produit in rapport.get("produits", []):
            recipe_name = produit.get("nom", "")
            quantity = produit.get("quantite", 0)
            price = produit.get("prix", 0)
            
            if recipe_name not in recipe_sales:
                recipe_sales[recipe_name] = {"quantity": 0, "revenue": 0}
            
            recipe_sales[recipe_name]["quantity"] += quantity
            recipe_sales[recipe_name]["revenue"] += quantity * price
            
            # Categorize (simplified logic)
            if any(word in recipe_name.lower() for word in ["vin", "bière", "cocktail", "apéritif"]):
                category_sales["Bar"] += quantity * price
            elif any(word in recipe_name.lower() for word in ["entrée", "salade", "soup"]):
                category_sales["Entrées"] += quantity * price
            elif any(word in recipe_name.lower() for word in ["dessert", "glace", "tarte", "gâteau"]):
                category_sales["Desserts"] += quantity * price
            else:
                category_sales["Plats"] += quantity * price
    
    # Get top 5 recipes
    top_recipes = sorted(
        [{"name": name, **data} for name, data in recipe_sales.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:5]
    
    return SalesPerformance(
        period=period,
        total_sales=total_sales,
        total_orders=total_orders,
        average_order_value=average_order_value,
        top_recipes=top_recipes,
        sales_by_category=category_sales
    )

@api_router.get("/analytics/alerts", response_model=AlertCenter)
async def get_alert_center():
    """Get all alerts for management dashboard"""
    alerts = AlertCenter(
        expiring_products=[],
        price_anomalies=[],
        low_stock_items=[],
        unused_stock=[],
        total_alerts=0
    )
    
    # Get expiring products (next 7 days)
    from datetime import datetime, timedelta
    expiry_threshold = datetime.utcnow() + timedelta(days=7)
    
    expiring_batches = await db.product_batches.find({
        "expiry_date": {"$lte": expiry_threshold, "$ne": None},
        "is_consumed": False
    }).to_list(1000)
    
    for batch in expiring_batches:
        product = await db.produits.find_one({"id": batch["product_id"]})
        if product:
            days_to_expiry = (batch["expiry_date"] - datetime.utcnow()).days
            alerts.expiring_products.append({
                "product_name": product["nom"],
                "batch_id": batch["id"],
                "quantity": batch["quantity"],
                "expiry_date": batch["expiry_date"].isoformat(),
                "days_to_expiry": days_to_expiry,
                "urgency": "critical" if days_to_expiry <= 2 else "warning"
            })
    
    # Get price anomalies
    price_anomalies = await db.price_anomaly_alerts.find({"is_resolved": False}).to_list(1000)
    for anomaly in price_anomalies:
        alerts.price_anomalies.append({
            "product_name": anomaly["product_name"],
            "supplier_name": anomaly["supplier_name"],
            "reference_price": anomaly["reference_price"],
            "actual_price": anomaly["actual_price"],
            "difference_percentage": anomaly["difference_percentage"],
            "alert_date": anomaly["alert_date"].isoformat()
        })
    
    # Get low stock items
    stocks = await db.stocks.find().to_list(1000)
    for stock in stocks:
        if stock["quantite_actuelle"] <= stock["quantite_min"] and stock["quantite_min"] > 0:
            product = await db.produits.find_one({"id": stock["produit_id"]})
            alerts.low_stock_items.append({
                "product_name": product["nom"] if product else "Produit inconnu",
                "current_quantity": stock["quantite_actuelle"],
                "minimum_quantity": stock["quantite_min"],
                "shortage": stock["quantite_min"] - stock["quantite_actuelle"]
            })
    
    # Get unused stock (no movements in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_movements = await db.mouvements_stock.find({
        "date": {"$gte": thirty_days_ago}
    }).to_list(1000)
    
    moved_product_ids = set(mov["produit_id"] for mov in recent_movements)
    
    for stock in stocks:
        if stock["produit_id"] not in moved_product_ids and stock["quantite_actuelle"] > 0:
            product = await db.produits.find_one({"id": stock["produit_id"]})
            alerts.unused_stock.append({
                "product_name": product["nom"] if product else "Produit inconnu",
                "quantity": stock["quantite_actuelle"],
                "last_update": stock["derniere_maj"].isoformat(),
                "days_unused": (datetime.utcnow() - stock["derniere_maj"]).days
            })
    
    alerts.total_alerts = (len(alerts.expiring_products) + len(alerts.price_anomalies) + 
                          len(alerts.low_stock_items) + len(alerts.unused_stock))
    
    return alerts

@api_router.get("/analytics/cost-analysis", response_model=CostAnalysis)
async def get_cost_analysis():
    """Get comprehensive cost analysis"""
    # Calculate total inventory value
    stocks = await db.stocks.find().to_list(1000)
    total_inventory_value = 0.0
    
    for stock in stocks:
        product = await db.produits.find_one({"id": stock["produit_id"]})
        if product:
            unit_price = product.get("reference_price", 0)
            total_inventory_value += stock["quantite_actuelle"] * unit_price
    
    # Calculate average cost per recipe
    recipes = await db.recettes.find().to_list(1000)
    total_recipe_cost = 0.0
    recipe_count = 0
    
    expensive_ingredients = []
    
    for recipe in recipes:
        recipe_cost = 0.0
        for ingredient in recipe.get("ingredients", []):
            product = await db.produits.find_one({"id": ingredient["produit_id"]})
            if product:
                unit_price = product.get("reference_price", 0)
                ingredient_cost = (ingredient["quantite"] / recipe["portions"]) * unit_price
                recipe_cost += ingredient_cost
                
                expensive_ingredients.append({
                    "name": product["nom"],
                    "unit_price": unit_price,
                    "category": product.get("categorie", "Non classé")
                })
        
        total_recipe_cost += recipe_cost
        recipe_count += 1
    
    avg_cost_per_recipe = total_recipe_cost / recipe_count if recipe_count > 0 else 0
    
    # Get most expensive ingredients (top 10)
    expensive_ingredients.sort(key=lambda x: x["unit_price"], reverse=True)
    most_expensive = expensive_ingredients[:10]
    
    # Simple cost trends (mock data for now)
    cost_trends = {
        "monthly_change": 2.5,  # +2.5% this month
        "quarterly_change": 7.8,  # +7.8% this quarter
        "highest_cost_category": "Viandes et Poissons",
        "lowest_cost_category": "Épices et Assaisonnements"
    }
    
    # Simple waste analysis
    waste_analysis = {
        "estimated_waste_percentage": 8.5,
        "estimated_waste_value": total_inventory_value * 0.085,
        "main_waste_sources": ["Produits périssables", "Surproduction", "Erreurs de préparation"]
    }
    
    return CostAnalysis(
        total_inventory_value=total_inventory_value,
        avg_cost_per_recipe=avg_cost_per_recipe,
        most_expensive_ingredients=most_expensive,
        cost_trends=cost_trends,
        waste_analysis=waste_analysis
    )

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

def parse_z_report_enhanced(texte_ocr: str) -> StructuredZReportData:
    """Enhanced Z report parser with structured data extraction and categorization"""
    structured_data = StructuredZReportData()
    
    try:
        # Extract report date
        date_patterns = [
            r'(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})',
            r'(\d{2,4}[/\-.]\d{1,2}[/\-.]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, texte_ocr)
            if date_match:
                structured_data.report_date = date_match.group(1)
                break
        
        # Extract service (Midi, Soir, etc.)
        service_patterns = [
            r'service\s+(midi|soir|matin|après-midi)',
            r'(midi|soir|matin|après-midi)\s+service',
            r'(déjeuner|dîner|petit-déjeuner)'
        ]
        
        for pattern in service_patterns:
            service_match = re.search(pattern, texte_ocr, re.IGNORECASE)
            if service_match:
                service_text = service_match.group(1).lower()
                # Normalize service names
                if service_text in ['midi', 'déjeuner']:
                    structured_data.service = "Midi"
                elif service_text in ['soir', 'dîner']:
                    structured_data.service = "Soir"
                elif service_text in ['matin', 'petit-déjeuner']:
                    structured_data.service = "Matin"
                elif service_text == 'après-midi':
                    structured_data.service = "Après-midi"
                break
        
        # Enhanced item extraction with better pattern recognition
        item_patterns = [
            # Format: "(x14) Linguine aux palourdes"
            r'\([x]?(\d{1,3})\)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,50})',
            # Format: "14x Linguine aux palourdes" or "14 Linguine"
            r'(\d{1,3})[x\s]+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,50})',
            # Format: "Linguine aux palourdes: 14"
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,50})\s*:?\s*(\d{1,3})',
            # Format: "Linguine aux palourdes €28.00 x 14"
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,50})\s*€?(\d+[,.]?\d*)\s*x?\s*(\d{1,3})'
        ]
        
        raw_items = []
        lines = texte_ocr.split('\n')
        
        # Extract grand total - Patterns améliorés pour tous formats
        total_patterns = [
            r'total\s*ca\s*:?\s*€?(\d+[,.]?\d*)',  # "TOTAL CA: 456.50€"  
            r'ca\s*total\s*:?\s*€?(\d+[,.]?\d*)',  # "CA TOTAL: 456.50€"
            r'total\s*:?\s*€?(\d+[,.]?\d*)',       # "TOTAL: 456.50€"
            r'montant\s*total\s*:?\s*€?(\d+[,.]?\d*)', # "MONTANT TOTAL: 456.50€"
            r'grand\s*total\s*:?\s*€?(\d+[,.]?\d*)',   # "GRAND TOTAL: 456.50€"
            r'€\s*(\d+[,.]?\d*)\s*total',          # "€ 456.50 TOTAL"
            r'(\d+[,.]?\d*)\s*€\s*total'           # "456.50 € TOTAL"
        ]
        
        for line in lines:
            line = line.strip()
            for pattern in total_patterns:
                total_match = re.search(pattern, line.lower())
                if total_match:
                    try:
                        structured_data.grand_total_sales = float(total_match.group(1).replace(',', '.'))
                    except ValueError:
                        pass
        
        # Process each line for items
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Skip lines that are clearly totals, dates, or headers
            if re.search(r'total|somme|ca\s|date|rapport|couverts?|service', line.lower()):
                continue
            
            # Try each pattern
            for pattern_index, pattern in enumerate(item_patterns):
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if pattern_index == 3:  # Special case for price pattern
                        if len(groups) >= 3:
                            name = groups[0].strip()
                            price = float(groups[1].replace(',', '.'))
                            quantity = int(groups[2])
                        else:
                            continue
                    else:
                        # Determine quantity and name based on pattern
                        if groups[0].isdigit():
                            quantity = int(groups[0])
                            name = groups[1].strip()
                        else:
                            name = groups[0].strip()
                            try:
                                quantity = int(groups[1]) if len(groups) > 1 and groups[1].isdigit() else 1
                            except (ValueError, IndexError):
                                quantity = 1
                        price = None
                    
                    # Clean up the name
                    name = re.sub(r'\s+', ' ', name)
                    name = name.strip('.,;:-')
                    
                    if len(name) >= 3 and quantity > 0:
                        # Categorize the item
                        category = categorize_menu_item(name)
                        
                        item = {
                            "name": name,
                            "quantity_sold": quantity,
                            "category": category,
                            "unit_price": price,
                            "total_price": price * quantity if price else None,
                            "raw_line": line
                        }
                        raw_items.append(item)
                        break
        
        # Group items by category
        structured_data.items_by_category = {
            "Bar": [],
            "Entrées": [],
            "Plats": [],
            "Desserts": []
        }
        
        for item in raw_items:
            category = item["category"]
            structured_item = StructuredZReportItem(
                name=item["name"],
                quantity_sold=item["quantity_sold"],
                category=category,
                unit_price=item.get("unit_price"),
                total_price=item.get("total_price")
            )
            structured_data.items_by_category[category].append(structured_item.dict())
        
        structured_data.raw_items = raw_items
        
        return structured_data
        
    except Exception as e:
        print(f"Erreur lors du parsing structuré Z-report: {str(e)}")
        # Return empty structured data in case of error
        return StructuredZReportData()

def categorize_menu_item(item_name: str) -> str:
    """Categorize menu items based on name patterns - Enhanced for French cuisine"""
    name_lower = item_name.lower()
    
    # Bar/Beverages - Mots-clés étendus
    bar_keywords = [
        'vin', 'wine', 'bière', 'beer', 'cocktail', 'apéritif', 'digestif',
        'whisky', 'vodka', 'gin', 'rhum', 'champagne', 'prosecco', 'kir',
        'pastis', 'ricard', 'mojito', 'sangria', 'eau', 'soda', 'coca',
        'jus', 'café', 'thé', 'expresso', 'cappuccino', 'alcool', 'rosé',
        'blanc', 'rouge', 'côtes', 'bordeaux', 'bourgogne', 'muscadet'
    ]
    
    # Entrées - Mots-clés étendus pour cuisine française
    entree_keywords = [
        'entrée', 'salade', 'soupe', 'velouté', 'tartare', 'carpaccio',
        'toast', 'bruschetta', 'antipasti', 'terrine', 'foie gras',
        'escargot', 'huître', 'crevette', 'saumon fumé', 'charcuterie',
        'supions', 'calamars', 'poulpe', 'fleurs de courgettes', # Ajouts spécifiques
        'fleur', 'persillade', 'tapenade', 'rillettes', 'pâté',
        'amuse-bouche', 'mise en bouche', 'bouchée', 'feuilleté'
    ]
    
    # Desserts - Mots-clés étendus  
    dessert_keywords = [
        'dessert', 'tarte', 'gâteau', 'mousse', 'tiramisu', 'panna cotta',
        'glace', 'sorbet', 'crème', 'flan', 'fondant', 'mille-feuille',
        'éclair', 'profiterole', 'macaron', 'fruit', 'café gourmand',
        'charlotte', 'clafoutis', 'soufflé', 'bavarois', 'parfait'
    ]
    
    # Check categories with priority order
    for keyword in bar_keywords:
        if keyword in name_lower:
            return "Bar"
    
    for keyword in entree_keywords:
        if keyword in name_lower:
            return "Entrées"
    
    for keyword in dessert_keywords:
        if keyword in name_lower:
            return "Desserts"
    
    # Default to "Plats" (main dishes)
    return "Plats"

async def calculate_stock_deductions(structured_report: StructuredZReportData) -> ZReportValidationResult:
    """Calculate proposed stock deductions based on sold items and recipe ingredients"""
    result = ZReportValidationResult(
        can_validate=True,
        proposed_deductions=[],
        total_deductions=0,
        warnings=[],
        errors=[]
    )
    
    try:
        # Get all recipes for matching
        recipes = await db.recettes.find().to_list(1000)
        recipe_dict = {recipe["nom"].lower(): recipe for recipe in recipes}
        
        # Process each sold item
        all_items = []
        for category, items in structured_report.items_by_category.items():
            all_items.extend(items)
        
        for item in all_items:
            item_name = item["name"].lower()
            quantity_sold = item["quantity_sold"]
            
            # Try to find matching recipe
            matching_recipe = None
            best_match_ratio = 0
            
            for recipe_name, recipe in recipe_dict.items():
                # Direct match
                if item_name == recipe_name:
                    matching_recipe = recipe
                    break
                # Partial match (simple fuzzy matching)
                elif item_name in recipe_name or recipe_name in item_name:
                    # Calculate simple match ratio
                    match_ratio = len(set(item_name.split()) & set(recipe_name.split())) / max(len(item_name.split()), len(recipe_name.split()))
                    if match_ratio > best_match_ratio and match_ratio > 0.3:
                        best_match_ratio = match_ratio
                        matching_recipe = recipe
            
            if matching_recipe:
                # Calculate ingredient deductions
                ingredient_deductions = []
                warnings = []
                recipe_portions = matching_recipe.get("portions", 1)
                
                for ingredient in matching_recipe.get("ingredients", []):
                    # Get current stock
                    stock = await db.stocks.find_one({"produit_id": ingredient["produit_id"]})
                    if stock:
                        # Calculate required quantity per sold portion
                        qty_per_portion = ingredient["quantite"] / recipe_portions
                        total_deduction = qty_per_portion * quantity_sold
                        
                        current_stock = stock["quantite_actuelle"]
                        new_stock = current_stock - total_deduction
                        
                        ingredient_deductions.append({
                            "product_id": ingredient["produit_id"],
                            "product_name": ingredient.get("produit_nom", "Produit inconnu"),
                            "current_stock": current_stock,
                            "deduction": total_deduction,
                            "new_stock": max(0, new_stock),
                            "unit": ingredient.get("unite", "")
                        })
                        
                        # Check for insufficient stock
                        if new_stock < 0:
                            warnings.append(f"Stock insuffisant pour {ingredient.get('produit_nom', 'Produit')}: {current_stock} disponible, {total_deduction:.2f} requis")
                            result.can_validate = False
                    else:
                        warnings.append(f"Stock non trouvé pour {ingredient.get('produit_nom', 'Produit')}")
                
                proposal = StockDeductionProposal(
                    recipe_name=matching_recipe["nom"],
                    quantity_sold=quantity_sold,
                    ingredient_deductions=ingredient_deductions,
                    warnings=warnings
                )
                result.proposed_deductions.append(proposal)
                result.total_deductions += len(ingredient_deductions)
            else:
                result.warnings.append(f"Aucune recette trouvée pour '{item['name']}'")
        
        if not result.proposed_deductions:
            result.warnings.append("Aucune déduction de stock possible - aucune recette correspondante trouvée")
        
        return result
        
    except Exception as e:
        result.errors.append(f"Erreur lors du calcul des déductions: {str(e)}")
        result.can_validate = False
        return result

async def apply_stock_deductions(validation_result: ZReportValidationResult) -> dict:
    """Apply the proposed stock deductions to the database"""
    if not validation_result.can_validate:
        return {"success": False, "message": "Validation impossible - vérifiez les alertes"}
    
    applied_deductions = 0
    errors = []
    
    try:
        for proposal in validation_result.proposed_deductions:
            for deduction in proposal.ingredient_deductions:
                # Update stock
                result = await db.stocks.update_one(
                    {"produit_id": deduction["product_id"]},
                    {
                        "$set": {
                            "quantite_actuelle": deduction["new_stock"],
                            "derniere_maj": datetime.utcnow()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    # Create stock movement record
                    mouvement = MouvementStock(
                        produit_id=deduction["product_id"],
                        produit_nom=deduction["product_name"],
                        type="sortie",
                        quantite=deduction["deduction"],
                        commentaire=f"Déduction automatique - vente {proposal.recipe_name} (x{proposal.quantity_sold})"
                    )
                    await db.mouvements_stock.insert_one(mouvement.dict())
                    applied_deductions += 1
                else:
                    errors.append(f"Impossible de mettre à jour le stock pour {deduction['product_name']}")
        
        return {
            "success": True,
            "message": f"{applied_deductions} déductions appliquées avec succès",
            "applied_deductions": applied_deductions,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de l'application des déductions: {str(e)}",
            "errors": [str(e)]
        }

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
    
    # ✅ V3 Enhancement: Set reference_price if not provided (backward compatibility)
    if not produit_dict.get("reference_price"):
        produit_dict["reference_price"] = produit_dict.get("prix_achat", 10.0) or 10.0
    
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
    """Upload et traitement OCR d'un document (image ou PDF) - Rapport Z ou facture"""
    
    if document_type not in ["z_report", "facture_fournisseur"]:
        raise HTTPException(status_code=400, detail="Type de document invalide. Utilisez 'z_report' ou 'facture_fournisseur'")
    
    # Détecter le type de fichier
    file_type = detect_file_type(file.filename, file.content_type)
    
    # Vérifier le format de fichier (accepter images ET PDF)
    if file.content_type:
        if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image (JPG, PNG, etc.) ou un PDF")
    else:
        # Si content_type est None, vérifier l'extension du fichier
        filename_lower = file.filename.lower() if file.filename else ""
        if not any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.pdf']):
            raise HTTPException(status_code=400, detail="Le fichier doit avoir une extension valide (.jpg, .png, .pdf, etc.)")
    
    try:
        # Lire le contenu du fichier
        file_content = await file.read()
        
        # Extraire le texte selon le type de fichier
        if file_type == 'pdf':
            print(f"📄 Processing PDF file: {file.filename}")
            texte_extrait = extract_text_from_pdf(file_content)
            # Pour les PDF, on stocke le contenu comme base64 mais avec prefix PDF
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            data_uri = f"data:application/pdf;base64,{content_base64}"
        else:
            print(f"🖼️ Processing image file: {file.filename}")
            image_base64 = base64.b64encode(file_content).decode('utf-8')
            texte_extrait = extract_text_from_image(image_base64)
            data_uri = f"data:{file.content_type or 'image/jpeg'};base64,{image_base64}"
        
        if not texte_extrait or len(texte_extrait.strip()) < 10:
            error_msg = "Impossible d'extraire du texte du PDF. Vérifiez que le PDF contient du texte." if file_type == 'pdf' else "Impossible d'extraire du texte de l'image. Vérifiez la qualité de l'image."
            raise HTTPException(status_code=400, detail=error_msg)
        
        print(f"✅ Text extracted successfully: {len(texte_extrait)} characters from {file_type}")
        
        # Parser selon le type de document
        donnees_parsees = {}
        if document_type == "z_report":
            # Utiliser le parser enhanced pour les rapports Z
            z_data = parse_z_report_enhanced(texte_extrait)
            donnees_parsees = z_data.dict()
        elif document_type == "facture_fournisseur":
            facture_data = parse_facture_fournisseur(texte_extrait)
            donnees_parsees = facture_data.dict()
        
        # Créer le document dans la base
        document = DocumentOCR(
            type_document=document_type,
            nom_fichier=file.filename,
            image_base64=data_uri,  # Peut être une image ou un PDF encodé
            texte_extrait=texte_extrait,
            donnees_parsees=donnees_parsees,
            statut="traite",
            date_traitement=datetime.utcnow(),
            file_type=file_type  # Nouveau champ pour identifier le type
        )
        
        await db.documents_ocr.insert_one(document.dict())
        
        return DocumentUploadResponse(
            document_id=document.id,
            type_document=document_type,
            texte_extrait=texte_extrait,
            donnees_parsees=donnees_parsees,
            message=f"Document {document_type} traité avec succès",
            file_type=file_type
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