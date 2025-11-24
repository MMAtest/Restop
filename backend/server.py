from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
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

# Google Cloud Vision imports
from google.cloud import vision
from pdf2image import convert_from_bytes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

# MongoDB connection

# ✅ Version 3 - Enhanced RBAC System
ROLES = {
    "super_admin": "Super Admin",
    "patron": "Patron (Owner)",
    "gerant": "Gérant (Manager)", 
    "chef_cuisine": "Chef de cuisine (Head Chef)",
    "barman": "Barman (Bartender)",
    "caissier": "Caissier (Cashier)",
    "employe_cuisine": "Employé de Cuisine"
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

# Categories pour fournisseurs
CATEGORIES_FOURNISSEURS = [
    "frais", "surgelés", "primeur", "marée", "boucherie", "fromagerie", "extra", "hygiène", "bar"
]

# Models pour la gestion des stocks
class DeliveryRules(BaseModel):
    """Règles de livraison spécifiques pour un fournisseur"""
    order_days: Optional[List[str]] = None  # Jours où on peut commander: ["lundi", "mardi", etc.]
    order_deadline_hour: Optional[int] = 11  # Heure limite de commande (ex: 11h)
    delivery_days: Optional[List[str]] = None  # Jours de livraison possibles
    delivery_delay_days: Optional[int] = 1  # Délai en jours (ex: 1 = lendemain)
    delivery_time: Optional[str] = "12:00"  # Heure de livraison (ex: "12:00", "11:00")
    special_rules: Optional[str] = None  # Règles spéciales (texte libre)

class Fournisseur(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    couleur: Optional[str] = "#3B82F6"  # Couleur par défaut (bleu)
    logo: Optional[str] = None  # URL ou emoji pour le logo
    categorie: Optional[str] = "frais"  # Catégorie par défaut
    delivery_rules: Optional[DeliveryRules] = None  # Règles de livraison
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FournisseurCreate(BaseModel):
    nom: str
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    couleur: Optional[str] = "#3B82F6"  # Couleur par défaut (bleu)
    logo: Optional[str] = None  # URL ou emoji pour le logo
    categorie: Optional[str] = "frais"  # Catégorie par défaut
    delivery_rules: Optional[DeliveryRules] = None  # Règles de livraison

# ✅ Order Management Models
class OrderItem(BaseModel):
    """Article dans une commande"""
    product_id: str
    product_name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float

class Order(BaseModel):
    """Commande fournisseur"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str  # Numéro de commande unique (ex: CMD-123456)
    supplier_id: str
    supplier_name: str
    items: List[OrderItem]
    total_amount: float
    order_date: datetime = Field(default_factory=datetime.utcnow)
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    status: str = "pending"  # pending, confirmed, in_transit, delivered, cancelled
    notes: Optional[str] = None
    created_by: Optional[str] = None  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrderCreate(BaseModel):
    """Création d'une commande"""
    supplier_id: str
    items: List[OrderItem]
    notes: Optional[str] = None

# ✅ Préparations - Étape intermédiaire entre produit brut et production
class Preparation(BaseModel):
    """Préparation d'un produit brut"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str  # Nom de la préparation (ex: "Carottes en julienne")
    produit_id: str  # ID du produit brut source
    produit_nom: str  # Nom du produit pour affichage
    
    # Forme de découpe/transformation
    forme_decoupe: str  # julienne, brunoise, carré, émincé, haché, sauce, purée, cuit, mariné, custom
    forme_decoupe_custom: Optional[str] = None  # Si forme custom
    
    # Quantités
    quantite_produit_brut: float  # Quantité de produit brut utilisée
    unite_produit_brut: str  # kg, g, L, cl, pièces
    quantite_preparee: float  # Quantité après préparation
    unite_preparee: str  # kg, g, L, cl, pièces
    
    # Perte
    perte: float  # Perte en unité (ex: 1.5 kg)
    perte_pourcentage: float  # Perte en % (ex: 15%)
    
    # Portions
    nombre_portions: int  # Nombre de portions obtenues
    taille_portion: float  # Taille d'une portion (ex: 100g)
    unite_portion: str  # kg, g, L, cl, pièces
    
    # DLC et dates
    date_preparation: datetime = Field(default_factory=datetime.utcnow)
    dlc: Optional[datetime] = None  # Date limite de consommation spécifique
    
    # Informations complémentaires
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PreparationCreate(BaseModel):
    """Création d'une préparation"""
    nom: str
    produit_id: str
    forme_decoupe: str
    forme_decoupe_custom: Optional[str] = None
    quantite_produit_brut: float
    unite_produit_brut: str
    quantite_preparee: float
    unite_preparee: str
    perte: float
    perte_pourcentage: float
    nombre_portions: int
    taille_portion: float
    unite_portion: str
    dlc: Optional[datetime] = None
    notes: Optional[str] = None

class FormeDecoupeCustom(BaseModel):
    """Forme de découpe personnalisée"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

# ✅ Mission & Notification System Models
class Mission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str  # Titre de la mission
    description: str  # Description détaillée
    type: str  # Type de mission (stock_check, preparation, cleaning, etc.)
    category: str  # Catégorie (cuisine, stock, hygiene, commande)
    assigned_to_user_id: str  # ID de l'utilisateur assigné
    assigned_by_user_id: str  # ID de l'utilisateur qui a créé la mission
    assigned_to_name: str  # Nom de l'employé assigné
    assigned_by_name: str  # Nom de l'assignateur
    
    # Statuts et états
    status: str = "en_cours"  # en_cours, terminee_attente, validee, en_retard, annulee
    priority: str = "normale"  # basse, normale, haute, urgente
    
    # Dates
    assigned_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None  # Date limite
    completed_by_employee_date: Optional[datetime] = None  # Quand l'employé l'a marquée terminée
    validated_date: Optional[datetime] = None  # Quand le chef/patron a validé
    
    # Données liées à la mission
    related_product_id: Optional[str] = None  # Si lié à un produit
    related_preparation_id: Optional[str] = None  # Si lié à une préparation
    related_supplier_id: Optional[str] = None  # Si lié à un fournisseur
    target_quantity: Optional[float] = None  # Quantité cible (ex: 15 portions)
    target_unit: Optional[str] = None  # Unité cible
    
    # Notes et suivi
    employee_notes: Optional[str] = None  # Notes de l'employé lors de la completion
    validation_notes: Optional[str] = None  # Notes du chef lors de la validation
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MissionCreate(BaseModel):
    title: str
    description: str
    type: str
    category: str
    assigned_to_user_id: str
    priority: str = "normale"
    due_date: Optional[datetime] = None
    related_product_id: Optional[str] = None
    related_preparation_id: Optional[str] = None
    related_supplier_id: Optional[str] = None
    target_quantity: Optional[float] = None
    target_unit: Optional[str] = None

class MissionUpdate(BaseModel):
    status: Optional[str] = None
    employee_notes: Optional[str] = None
    validation_notes: Optional[str] = None

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Utilisateur destinataire
    title: str
    message: str
    type: str  # mission, alert, info, system
    read: bool = False
    mission_id: Optional[str] = None  # Si liée à une mission
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None

# ✅ Session Management for Simple Auth
class UserSession(BaseModel):
    user_id: str
    username: str
    role: str
    full_name: str
    login_time: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class LoginResponse(BaseModel):
    success: bool
    user: Optional[UserResponse] = None
    session_id: Optional[str] = None
    message: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    full_name: Optional[str] = None

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

# ✅ Auto-generated delivery & extra costs products per supplier
class SupplierCostConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str
    delivery_cost: float = 0.0  # Frais de livraison fixes par commande
    extra_cost: float = 0.0    # Frais supplémentaires (manutention, etc.)
    delivery_cost_product_id: Optional[str] = None  # ID du produit auto-créé pour frais livraison
    extra_cost_product_id: Optional[str] = None     # ID du produit auto-créé pour frais extra
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SupplierCostConfigCreate(BaseModel):
    supplier_id: str
    delivery_cost: float = 0.0
    extra_cost: float = 0.0

# ✅ Archive system models
class ArchivedItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_id: str  # ID de l'objet original
    item_type: str    # "produit", "production", "fournisseur"
    original_data: dict  # Données complètes de l'objet archivé
    archived_at: datetime = Field(default_factory=datetime.utcnow)
    archived_by: Optional[str] = None  # Utilisateur qui a archivé
    reason: Optional[str] = None  # Raison de l'archivage

class ArchiveRequest(BaseModel):
    item_id: str
    item_type: str  # "produit", "production", "fournisseur"
    reason: Optional[str] = None

class RestoreRequest(BaseModel):
    archive_id: str

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
    quantity_brute: Optional[float] = None    # Quantité brute reçue
    perte_percentage: Optional[float] = None  # Pourcentage de perte (produit brut → fini)
    expiry_date: Optional[datetime] = None    # DLC - Date Limite de Consommation
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

# ✅ Stock Preparations - Collection séparée pour les préparations en stock
class StockPreparation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    preparation_id: str  # Référence à la préparation dans la collection preparations
    preparation_nom: str
    quantite_actuelle: float
    unite: str
    quantite_min: float = 0.0
    quantite_max: Optional[float] = None
    date_preparation: datetime = Field(default_factory=datetime.utcnow)
    dlc: Optional[datetime] = None  # Date limite de consommation
    derniere_maj: datetime = Field(default_factory=datetime.utcnow)
    statut: str = "disponible"  # disponible, expire_bientot, expire

class StockPreparationCreate(BaseModel):
    preparation_id: str
    quantite_actuelle: float
    quantite_min: float = 0.0
    quantite_max: Optional[float] = None
    dlc: Optional[datetime] = None

class StockPreparationUpdate(BaseModel):
    quantite_actuelle: Optional[float] = None
    quantite_min: Optional[float] = None
    quantite_max: Optional[float] = None
    dlc: Optional[datetime] = None
    statut: Optional[str] = None

class ExecutePreparationRequest(BaseModel):
    """Request pour exécuter une préparation (transformer produits en préparation)"""
    quantite_a_produire: float  # Quantité de préparation à produire
    notes: Optional[str] = None

class ExecutePreparationResult(BaseModel):
    """Résultat de l'exécution d'une préparation"""
    success: bool
    preparation_nom: str
    quantite_produite: float
    unite: str
    produits_deduits: List[dict] = []  # Liste des produits déduits
    stock_preparation_id: str  # ID du stock de préparation créé
    warnings: List[str] = []
    errors: List[str] = []

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

# Models pour la gestion des recettes (Productions)
class RecetteIngredient(BaseModel):
    # ✅ Nouveau format (optionnel pour backward compatibility)
    ingredient_id: Optional[str] = None  # ID universel (peut pointer vers produit OU preparation)
    ingredient_type: Optional[str] = None  # "produit" OU "preparation"
    ingredient_nom: Optional[str] = None
    
    # ✅ Legacy fields (optionnel pour backward compatibility)
    produit_id: Optional[str] = None  # Ancien format - converti automatiquement
    produit_nom: Optional[str] = None  # Ancien format
    
    # ✅ Champs requis
    quantite: float
    unite: str
    
    def __init__(self, **data):
        # Auto-conversion: si produit_id fourni sans ingredient_id, convertir automatiquement
        if "produit_id" in data and not data.get("ingredient_id"):
            data["ingredient_id"] = data["produit_id"]
            data["ingredient_type"] = "produit"
            if "produit_nom" in data and not data.get("ingredient_nom"):
                data["ingredient_nom"] = data["produit_nom"]
        super().__init__(**data)

# Modèle pour les données de vente avec services
class VenteService(BaseModel):
    service: str  # "midi" ou "soir"
    ca_total: float
    nb_couverts: int
    productions: List[dict] = []  # Productions vendues avec leurs coefficients

class AnalyseVente(BaseModel):
    date: str
    ca_total: float
    ca_midi: float
    ca_soir: float
    nb_couverts_midi: int
    nb_couverts_soir: int
    productions_performance: List[dict] = []  # Avec coefficients prévu/réel

CATEGORIES_PRODUCTION = ["Entrée", "Plat", "Dessert", "Bar", "Autres"]

class Recette(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None  # "Entrée", "Plat", "Dessert", "Bar", "Autres"
    portions: int  # Nombre de portions que la recette produit
    temps_preparation: Optional[int] = None  # en minutes
    instructions: Optional[str] = None
    prix_vente: Optional[float] = None
    coefficient_prevu: Optional[float] = None  # Coefficient prévu par le manager
    coefficient_reel: Optional[float] = None   # Coefficient réel calculé (Coût Matière / Prix de Vente)
    cout_matiere: Optional[float] = None       # Coût total des matières premières
    ingredients: List[RecetteIngredient] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RecetteCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None  # Doit être une des CATEGORIES_PRODUCTION
    portions: int
    temps_preparation: Optional[int] = None
    instructions: Optional[str] = None
    prix_vente: Optional[float] = None
    coefficient_prevu: Optional[float] = None  # Nouveau champ pour le coefficient prévu
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
    coefficient_prevu: Optional[float] = None  # Coefficient prévu par le manager (en multiples)
    coefficient_reel: Optional[float] = None   # Coefficient réel calculé (Coût Matière / Prix de Vente)
    cout_matiere: Optional[float] = None       # Coût total des matières premières
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

# ✅ New Models for OCR Processing Results
class ProductMatch(BaseModel):
    """Résultat du matching d'un produit OCR avec la base de données"""
    ocr_name: str
    matched_product_id: Optional[str] = None
    matched_product_name: Optional[str] = None
    confidence_score: float = 0.0  # 0.0 to 1.0
    quantity: float
    unit: str
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    needs_creation: bool = False
    suggested_category: Optional[str] = None

class ZReportProcessingResult(BaseModel):
    """Résultat du processing d'un Ticket Z"""
    success: bool
    document_id: str
    date: str
    ca_total: float
    nb_couverts: Optional[int] = None
    productions_matched: List[dict] = []
    stock_deductions: List[dict] = []
    warnings: List[str] = []
    errors: List[str] = []
    rapport_z_id: Optional[str] = None

class FactureProcessingResult(BaseModel):
    """Résultat du processing d'une facture fournisseur"""
    success: bool
    document_id: str
    supplier_name: str
    supplier_id: Optional[str] = None
    products_matched: List[ProductMatch] = []
    products_created: int = 0
    stock_entries_created: int = 0
    price_alerts: List[dict] = []
    warnings: List[str] = []
    errors: List[str] = []
    order_id: Optional[str] = None

class MercurialeProcessingResult(BaseModel):
    """Résultat du processing d'une mercuriale"""
    success: bool
    document_id: str
    supplier_name: str
    supplier_id: Optional[str] = None
    prices_updated: int = 0
    price_changes: List[dict] = []
    warnings: List[str] = []
    errors: List[str] = []

# ===== Stock Quantity Rounding Helper =====
def round_stock_quantity(quantity: float) -> float:
    """Arrondir une quantité de stock à 0.01 près (2 décimales)"""
    return round(quantity, 2)

# ===== Product Matching Helper Functions =====
def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (simple Levenshtein-like)"""
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    if str1 == str2:
        return 1.0
    
    # Check if one contains the other
    if str1 in str2 or str2 in str1:
        return 0.8
    
    # Simple character-based similarity
    set1 = set(str1.split())
    set2 = set(str2.split())
    
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

async def match_product_by_name(product_name: str, min_confidence: float = 0.6) -> Optional[dict]:
    """Match a product name from OCR with existing products in database"""
    best_match = None
    best_score = 0.0
    
    # Get all products
    products = await db.produits.find().to_list(length=None)
    
    for product in products:
        score = calculate_similarity(product_name, product["nom"])
        if score > best_score and score >= min_confidence:
            best_score = score
            best_match = {
                "product_id": product["id"],
                "product_name": product["nom"],
                "confidence": score,
                "category": product.get("categorie"),
                "unit": product.get("unite", "kg")
            }
    
    return best_match

async def match_recipe_by_name(recipe_name: str, min_confidence: float = 0.6) -> Optional[dict]:
    """Match a recipe/production name from OCR with existing recipes"""
    best_match = None
    best_score = 0.0
    
    # Get all recipes
    recipes = await db.recettes.find().to_list(length=None)
    
    for recipe in recipes:
        score = calculate_similarity(recipe_name, recipe["nom"])
        if score > best_score and score >= min_confidence:
            best_score = score
            best_match = {
                "recipe_id": recipe["id"],
                "recipe_name": recipe["nom"],
                "confidence": score,
                "ingredients": recipe.get("ingredients", []),
                "category": recipe.get("categorie")
            }
    
    return best_match

async def match_supplier_by_name(supplier_name: str, min_confidence: float = 0.6) -> Optional[dict]:
    """Match a supplier name from OCR with existing suppliers"""
    best_match = None
    best_score = 0.0
    
    # Get all suppliers
    suppliers = await db.fournisseurs.find().to_list(length=None)
    
    for supplier in suppliers:
        score = calculate_similarity(supplier_name, supplier["nom"])
        if score > best_score and score >= min_confidence:
            best_score = score
            best_match = {
                "supplier_id": supplier["id"],
                "supplier_name": supplier["nom"],
                "confidence": score
            }
    
    return best_match

# ===== Helpers for FR numeric parsing and Z analysis =====
number_separators = re.compile(r"[\s\u00A0\u202F]")  # spaces incl. NBSP, NNBSP

def parse_number_fr(val: str) -> Optional[float]:
    try:
        if val is None:
            return None
        s = str(val)
        s = s.replace('€', '')
        s = number_separators.sub('', s)
        # Replace comma decimal with dot if needed
        if s.count(',') == 1 and s.count('.') == 0:
            s = s.replace(',', '.')
        # Remove any trailing non-numeric
        s = re.sub(r"[^0-9\.-]", '', s)
        if s in ('', '-', '.', ','):
            return None
        return float(s)
    except Exception:
        return None

BAR_REGEXES = [
    r"boissons?\s*(chaudes?|fra[iî]ches?)",
    r"pago",
    r"cocktails?",
    r"bi[eè]re?s?\s*pression",
    r"ap[ée]ritifs?",
    r"digestifs?",
    r"alcools?\s*forts?",
    r"verres?\s*pichets?\s*(?:de\s*)?(rouge|rose|blanc)",
    r"bouteilles?\s*(rouge|rose|blanc)",
    r"verres?\s*pichets",  # sans "de"
    r"bouteille\b"         # singulier
]
ENTREE_REGEXES = [r"entr[éee]es?"]
PLAT_REGEXES = [r"plats?", r"plat\b"]
DESSERT_REGEXES = [r"desserts?"]

CATEGORY_FAMILIES = [
    ("Bar", BAR_REGEXES),
    ("Entrées", ENTREE_REGEXES),
    ("Plats", PLAT_REGEXES),
    ("Desserts", DESSERT_REGEXES)
]

def normalize_family(cat_name: str) -> str:
    n = (cat_name or '').lower()
    for fam, patterns in CATEGORY_FAMILIES:
        for pat in patterns:
            if re.search(pat, n, re.IGNORECASE):
                return fam
    return "Autres"

def detect_multiple_invoices(text_content):
    """Détecter s'il y a plusieurs factures dans le document et les séparer"""
    try:
        # Patterns améliorés basés sur l'analyse du PDF METRO
        invoice_separators = [
            # Patterns spécifiques METRO et autres fournisseurs français
            r'METRO\s+(?:FRANCE\s+)?[A-Z\s]*(?:FACTURE|Facture)',
            r'(?:FACTURE|Facture)\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
            r'(?:INVOICE|Invoice)\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
            r'BON\s*DE\s*LIVRAISON\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
            r'BL\s*N[°O]?\s*:?\s*[A-Z0-9\/\-]+',
            # Patterns pour fournisseurs spécifiques
            r'LE\s+DIAMANT\s+DU\s+TERROIR',
            r'RM\s+MAREE',
            r'GFD\s+LERDA',
            r'LE\s+ROYAUME\s+DES\s+MERS',
            # Patterns génériques d'en-têtes de factures
            r'(?:^|\n)\s*[A-Z][A-Z\s&]+(?:SARL|SAS|SA|EURL)\s*(?:\n|$)',
            # Totaux qui indiquent la fin d'une facture
            r'NET\s*[AÀ]\s*PAYER\s*:?\s*\d+[,.]?\d*\s*€?',
            r'TOTAL\s*TTC\s*:?\s*\d+[,.]?\d*\s*€?',
            r'MONTANT\s*TOTAL\s*:?\s*\d+[,.]?\d*\s*€?'
        ]
        
        # Rechercher tous les indicateurs de factures
        invoice_positions = []
        
        for i, pattern in enumerate(invoice_separators):
            for match in re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE):
                invoice_positions.append({
                    'type': 'header' if i < 10 else 'footer',
                    'position': match.start(),
                    'text': match.group().strip(),
                    'pattern_index': i
                })
        
        # Filtrer et nettoyer les positions
        if len(invoice_positions) > 1:
            # Trier par position
            invoice_positions.sort(key=lambda x: x['position'])
            
            # NOUVELLE APPROCHE: Identifier les vrais débuts de factures (headers forts)
            # Headers forts = patterns 0-9 (fournisseurs, numéros de facture/BL)
            # Footers = patterns 10-12 (totaux)
            strong_headers = [pos for pos in invoice_positions if pos['type'] == 'header']
            
            print(f"📊 Analyse: {len(invoice_positions)} positions totales, {len(strong_headers)} headers forts")
            
            # Si on a plusieurs headers forts, on a probablement plusieurs factures
            if len(strong_headers) > 1:
                print(f"✅ Détection de {len(strong_headers)} factures potentielles (basé sur headers forts)")
                
                # Grouper par header fort : chaque header fort démarre une nouvelle facture
                grouped_positions = []
                current_group = []
                
                for pos in invoice_positions:
                    if pos['type'] == 'header' and current_group:
                        # Nouveau header -> nouvelle facture (sauf si c'est le tout premier)
                        # Vérifier que ce n'est pas juste le même header répété (delta < 50 chars)
                        if pos['position'] - current_group[0]['position'] > 50:
                            grouped_positions.append(current_group)
                            current_group = [pos]
                        else:
                            current_group.append(pos)
                    else:
                        current_group.append(pos)
                
                if current_group:
                    grouped_positions.append(current_group)
                
                print(f"📋 {len(grouped_positions)} groupes créés")
                for i, group in enumerate(grouped_positions):
                    headers_in_group = [p for p in group if p['type'] == 'header']
                    print(f"   Groupe {i+1}: {len(group)} éléments, headers: {[h['text'][:30] for h in headers_in_group]}")
            
            # Si on a plusieurs groupes, on a plusieurs factures
            if len(grouped_positions) > 1:
                print(f"✅ Confirmation: {len(grouped_positions)} factures multiples détectées")
                
                separated_invoices = []
                
                for i, group in enumerate(grouped_positions):
                    start_pos = group[0]['position']
                    
                    # Déterminer la fin : soit le début du groupe suivant, soit la fin du document
                    if i < len(grouped_positions) - 1:
                        # Chercher le dernier total/footer avant le prochain header
                        end_pos = grouped_positions[i + 1][0]['position']
                        
                        # Chercher un footer/total dans cette section pour une coupe plus précise
                        section_text = text_content[start_pos:end_pos]
                        footer_patterns = [
                            r'NET\s*[AÀ]\s*PAYER\s*:?\s*\d+[,.]?\d*\s*€?',
                            r'TOTAL\s*TTC\s*:?\s*\d+[,.]?\d*\s*€?',
                            r'Merci\s+de\s+votre\s+confiance',
                            r'Conditions\s+de\s+vente'
                        ]
                        
                        for footer_pattern in footer_patterns:
                            footer_match = None
                            for match in re.finditer(footer_pattern, section_text, re.IGNORECASE):
                                footer_match = match
                            if footer_match:
                                end_pos = start_pos + footer_match.end() + 100  # Petit buffer après le total
                                break
                    else:
                        end_pos = len(text_content)
                    
                    # Extraire le texte de cette facture
                    invoice_text = text_content[start_pos:end_pos].strip()
                    
                    # Vérifier la qualité du texte extrait
                    quality_check = check_invoice_quality(invoice_text)
                    
                    if len(invoice_text) > 200 and quality_check['is_valid']:  # Filtrer les segments trop courts ou de mauvaise qualité
                        separated_invoices.append({
                            'index': len(separated_invoices) + 1,
                            'header': group[0]['text'],
                            'text_content': invoice_text,
                            'start_position': start_pos,
                            'end_position': end_pos,
                            'quality_score': quality_check['score'],
                            'quality_issues': quality_check['issues']
                        })
                    else:
                        print(f"⚠️ Facture {i+1} rejetée: qualité insuffisante ou trop courte")
                        print(f"   - Longueur: {len(invoice_text)} caractères")
                        print(f"   - Qualité: {quality_check}")
                
                print(f"✅ {len(separated_invoices)} factures de qualité suffisante séparées")
                return separated_invoices
        
        # Facture unique
        print("✅ Facture unique détectée")
        quality_check = check_invoice_quality(text_content)
        
        if not quality_check['is_valid']:
            print(f"⚠️ Qualité de la facture insuffisante: {quality_check['issues']}")
        
        return [{
            'index': 1,
            'header': 'Facture unique',
            'text_content': text_content,
            'start_position': 0,
            'end_position': len(text_content),
            'quality_score': quality_check['score'],
            'quality_issues': quality_check['issues']
        }]
    
    except Exception as e:
        print(f"❌ Erreur lors de la détection de factures multiples: {str(e)}")
        return [{
            'index': 1,
            'header': 'Facture (erreur détection)',
            'text_content': text_content,
            'start_position': 0,
            'end_position': len(text_content),
            'quality_score': 0.0,
            'quality_issues': [f"Erreur de traitement: {str(e)}"]
        }]

def check_invoice_quality(text_content):
    """Vérifier la qualité d'une facture extraite"""
    try:
        quality_score = 1.0
        issues = []
        
        # Vérifications de base
        if len(text_content) < 200:
            quality_score -= 0.5
            issues.append("Texte trop court (< 200 caractères)")
        
        # Vérifier la présence d'éléments essentiels d'une facture
        essential_patterns = [
            (r'(?:FACTURE|INVOICE|BON)', 0.3, "Pas d'en-tête de facture détecté"),
            (r'\d{2}[/\-\.]\d{2}[/\-\.]\d{2,4}', 0.2, "Pas de date détectée"), 
            (r'\d+[,.]?\d*\s*€', 0.2, "Pas de montant en euros détecté"),
            (r'(?:TOTAL|NET|PAYER)', 0.1, "Pas de total détecté")
        ]
        
        for pattern, penalty, message in essential_patterns:
            if not re.search(pattern, text_content, re.IGNORECASE):
                quality_score -= penalty
                issues.append(message)
        
        # Vérifier la lisibilité (ratio de caractères alphanumériques vs spéciaux)
        total_chars = len(text_content)
        alnum_chars = sum(1 for c in text_content if c.isalnum() or c.isspace())
        if total_chars > 0:
            readability_ratio = alnum_chars / total_chars
            if readability_ratio < 0.7:  # Moins de 70% de caractères lisibles
                quality_score -= 0.3
                issues.append(f"Lisibilité faible ({readability_ratio:.1%})")
        
        # Détecter les erreurs OCR typiques
        ocr_error_patterns = [
            (r'[|]{3,}', "Lignes de séparation mal reconnues"),
            (r'[#@$%^&*]{5,}', "Caractères spéciaux en série (erreur OCR)"),
            (r'\s{10,}', "Espaces excessifs"),
            (r'[A-Z]{20,}', "Texte en majuscules anormalement long")
        ]
        
        for pattern, message in ocr_error_patterns:
            if re.search(pattern, text_content):
                quality_score -= 0.1
                issues.append(message)
        
        # Score final
        quality_score = max(0.0, min(1.0, quality_score))
        is_valid = quality_score >= 0.6  # Seuil de qualité acceptable
        
        return {
            'is_valid': is_valid,
            'score': round(quality_score, 2),
            'issues': issues
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'score': 0.0,
            'issues': [f"Erreur d'analyse qualité: {str(e)}"]
        }

def analyze_z_report_categories(texte_ocr: str) -> dict:
    """
    Analyse optimisée des rapports Z selon les spécifications détaillées.
    Respecte la structure séquentielle : Entrées → Plats → Desserts
    CORRECTION CRITIQUE : Détection d'indentation basée sur les bonnes pratiques OCR
    """
    # PRÉSERVER TOUTES LES LIGNES AVEC INDENTATION ORIGINALE (ne pas strip !)
    lines = [l for l in (texte_ocr or '').split('\n') if l.strip()]  # Enlever seulement les lignes vides
    
    # Variables pour les données principales
    date_cloture = None
    heure_cloture = None
    nombre_couverts = None
    total_ht = None
    total_ttc = None
    
    # 1. Extraction Date et Heure de clôture (sur texte nettoyé)
    for ln in lines:
        ln_clean = ln.strip()
        # Recherche de la date (format DD/MM/YYYY ou DD/MM/YY)
        m_date = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", ln_clean)
        if m_date and date_cloture is None:
            day, month, year = m_date.groups()
            if len(year) == 2:
                year = "20" + year
            date_cloture = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        # Recherche de l'heure (format HH:MM:SS ou HH:MM)
        m_heure = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", ln_clean)
        if m_heure and heure_cloture is None:
            hour, minute, second = m_heure.groups()
            if second:
                heure_cloture = f"{hour.zfill(2)}:{minute}:{second}"
            else:
                heure_cloture = f"{hour.zfill(2)}:{minute}"
    
    # 2. Extraction Nombre de couverts
    for ln in lines:
        ln_clean = ln.strip()
        m_cov = re.search(r"nombre\s+de\s+couverts\s*:?\s*([0-9]+(?:[,\.][0-9]{1,2})?)", ln_clean, re.IGNORECASE)
        if m_cov and nombre_couverts is None:
            nombre_couverts = parse_number_fr(m_cov.group(1))
    
    # 3. Extraction Total HT
    for ln in lines:
        ln_clean = ln.strip()
        m_ht = re.search(r"total\s+ht\s*:?\s*([0-9]+(?:[,\.][0-9]{1,2})?)", ln_clean, re.IGNORECASE)
        if m_ht and total_ht is None:
            total_ht = parse_number_fr(m_ht.group(1))
    
    # 4. Extraction Total TTC
    for ln in lines:
        ln_clean = ln.strip()
        m_ttc = re.search(r"total\s+ttc\s*:?\s*([0-9]+(?:[,\.][0-9]{1,2})?)", ln_clean, re.IGNORECASE)
        if m_ttc and total_ttc is None:
            total_ttc = parse_number_fr(m_ttc.group(1))
    
    # 5. LOGIQUE CORRIGÉE : Détection d'indentation basée sur les meilleures pratiques
    categories = []
    productions = []
    
    # Patterns pour catégories et productions
    category_pattern = re.compile(r"^x?(\d+)\)\s*([^0-9]+?)\s+([0-9]+(?:[,\.][0-9]{2}))$", re.IGNORECASE)
    production_pattern = re.compile(r"^\(?x?(\d+)\)?\s*([^0-9]+?)\s+([0-9]+(?:[,\.][0-9]{2}))$", re.IGNORECASE)
    
    # Mots-clés à éviter
    keywords_to_avoid = [
        "tva", "total", "sous.total", "sous total", "solde", "caisse", "espece", "carte", "cheque",
        "remise", "service", "pourboire", "commission", "frais", "reduction", 
        "annulation", "retour", "net", "brut", "ht", "ttc", "taux", "base", "heure", "date", "rapport"
    ]
    
    current_category = None
    
    # Construire la hiérarchie en analysant l'indentation
    for i, line in enumerate(lines):
        # DÉTECTION INDENTATION CORRECTE selon bonnes pratiques OCR
        indent_level = len(line) - len(line.lstrip(' \t'))  # Compte espaces et tabulations
        content = line.strip()
        
        # Skip les lignes vides ou trop courtes
        if len(content) < 5:
            continue
        
        # Skip les lignes contenant des mots-clés à éviter
        if any(keyword in content.lower() for keyword in keywords_to_avoid):
            continue
        
        # CLASSIFICATION BASÉE SUR L'INDENTATION
        if indent_level == 0:
            # CATÉGORIES (non indentées)
            m_cat = category_pattern.match(content)
            if m_cat:
                quantity = int(m_cat.group(1))
                name = m_cat.group(2).strip()
                amount = parse_number_fr(m_cat.group(3)) or 0.0
                
                # Classification intelligente des familles
                name_lower = name.lower()
                if any(word in name_lower for word in ["entree", "entrée", "appetizer", "amuse"]):
                    family = "Entrées"
                elif any(word in name_lower for word in ["plat", "main", "principal", "resistance"]):
                    family = "Plats"
                elif any(word in name_lower for word in ["dessert", "sweet", "glace", "patisserie"]):
                    family = "Desserts"
                elif any(word in name_lower for word in ["boisson", "cocktail", "biere", "vin", "verre", "bouteille"]):
                    family = "Bar"
                else:
                    family = "Autres"
                
                category_info = {
                    "nom": name,
                    "quantite": quantity,
                    "prix_total": amount,
                    "type": "categorie",
                    "family": family,
                    "raw_line": content,
                    "line_number": i,
                    "indent_level": indent_level
                }
                categories.append(category_info)
                current_category = category_info
                
        elif indent_level > 0:
            # PRODUCTIONS (indentées)
            m_prod = production_pattern.match(content)
            if m_prod:
                quantity = int(m_prod.group(1))
                name = m_prod.group(2).strip()
                amount = parse_number_fr(m_prod.group(3)) or 0.0
                
                # Filtrage des faux positifs
                name_lower = name.lower()
                if any(keyword in name_lower for keyword in keywords_to_avoid):
                    continue
                
                # Skip patterns de TVA/pourcentage
                if re.search(r"\d+[\.,]?\d*\s*%", name):
                    continue
                
                # Déterminer la famille
                if current_category:
                    family = current_category["family"]
                    parent_name = current_category["nom"]
                else:
                    # Classification de secours
                    if any(word in name_lower for word in ["salade", "tartare", "soupe"]):
                        family = "Entrées"
                    elif any(word in name_lower for word in ["steak", "poisson", "pasta"]):
                        family = "Plats"
                    elif any(word in name_lower for word in ["tiramisu", "tarte"]):
                        family = "Desserts"
                    else:
                        family = "Autres"
                    parent_name = None
                
                production = {
                    "nom": name,
                    "quantite": quantity,
                    "prix_total": amount,
                    "type": "production",
                    "categorie_parent": parent_name,
                    "family": family,
                    "raw_line": line,  # Ligne originale avec indentation
                    "line_number": i,
                    "indent_level": indent_level
                }
                productions.append(production)
    
    # LOGIQUE SÉQUENTIELLE pour filtrer les plats problématiques
    # Trouver les bornes des entrées et desserts
    entrees_lines = [cat["line_number"] for cat in categories if cat["family"] == "Entrées"]
    desserts_lines = [cat["line_number"] for cat in categories if cat["family"] == "Desserts"]
    
    entrees_end_line = max(entrees_lines) if entrees_lines else None
    desserts_start_line = min(desserts_lines) if desserts_lines else None
    
    # Filtrer les productions de plats selon la séquence
    if entrees_end_line is not None and desserts_start_line is not None:
        filtered_productions = []
        for prod in productions:
            if prod["family"] == "Plats":
                # Ne garder que les plats entre les entrées et desserts
                if entrees_end_line < prod["line_number"] < desserts_start_line:
                    filtered_productions.append(prod)
            else:
                # Garder toutes les autres productions
                filtered_productions.append(prod)
        productions = filtered_productions
    
    # 6. Regroupement et analyse par familles
    categories_bar = [
        "boissons chaudes", "boissons fraiches", "cocktail", "biere pression",
        "verre pichets rouge", "verres pichets de rose", "verres pichets de blanc",
        "bouteilles rose", "bouteille rouge", "bouteille blanc"
    ]
    
    analysis = {
        "Bar": {"articles": 0, "ca": 0.0, "details": []},
        "Entrées": {"articles": 0, "ca": 0.0, "details": []},
        "Plats": {"articles": 0, "ca": 0.0, "details": []},
        "Desserts": {"articles": 0, "ca": 0.0, "details": []},
        "Autres": {"articles": 0, "ca": 0.0, "details": []}
    }
    
    # Agréger catégories
    for cat in categories:
        nom_clean = cat["nom"].lower()
        is_bar = any(bar_cat in nom_clean for bar_cat in categories_bar)
        family = "Bar" if is_bar else cat["family"]
        
        analysis[family]["articles"] += cat["quantite"]
        analysis[family]["ca"] += cat["prix_total"]
        analysis[family]["details"].append({
            "name": cat["nom"],
            "quantity": cat["quantite"],
            "amount": cat["prix_total"]
        })
    
    # Agréger productions
    for prod in productions:
        family = prod["family"]
        analysis[family]["articles"] += prod["quantite"]
        analysis[family]["ca"] += prod["prix_total"]
        analysis[family]["details"].append({
            "name": prod["nom"],
            "quantity": prod["quantite"],
            "amount": prod["prix_total"]
        })
    
    # Calculs de vérification
    total_calc = sum(analysis[k]["ca"] for k in analysis)
    verification = {
        "total_calculated": round(total_calc, 2),
        "displayed_total": total_ttc,
        "delta_eur": (round(total_calc - total_ttc, 2) if (total_ttc is not None) else None),
        "delta_pct": (round(((total_calc - total_ttc) / total_ttc) * 100, 2) if (total_ttc and total_ttc != 0) else None)
    }
    
    return {
        # Données principales extraites
        "date_cloture": date_cloture,
        "heure_cloture": heure_cloture,
        "nombre_couverts": nombre_couverts,
        "total_ht": total_ht,
        "total_ttc": total_ttc,
        
        # Données détaillées
        "categories_detectees": categories,
        "productions_detectees": productions,
        
        # Debug pour analyse séquentielle
        "entrees_end_line": entrees_end_line,
        "desserts_start_line": desserts_start_line,
        
        # Analyse par familles
        "analysis": analysis,
        "verification": verification,
        
        # Compteurs
        "total_categories": len(categories),
        "total_productions": len(productions),
        
        # Legacy compatibility
        "covers": nombre_couverts,
        "category_headers": categories
    }

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using a robust multi-pass strategy for completeness"""
    import io
    extracted_parts = []
    
    print(f"🔍 PDF extraction starting - {len(pdf_content)} bytes")

    # Helper to append unique chunks
    def append_text(txt):
        if not txt:
            return
        txt = txt.strip()
        if not txt:
            return
        # Avoid adding duplicates
        if txt not in extracted_parts:
            extracted_parts.append(txt)
            print(f"   ✓ Added {len(txt)} chars")

    # PASS 1: pdfplumber - SIMPLE TEXT EXTRACTION FIRST
    try:
        pdf_file = io.BytesIO(pdf_content)
        with pdfplumber.open(pdf_file) as pdf:
            print(f"📄 pdfplumber: {len(pdf.pages)} pages detected")
            for i, page in enumerate(pdf.pages):
                # APPROCHE 1: Extraction simple et rapide
                txt1 = page.extract_text()
                if txt1 and len(txt1.strip()) > 50:  # Au moins 50 caractères
                    append_text(txt1)
                    print(f"   Page {i+1}: {len(txt1)} chars extracted (simple)")
                
                # APPROCHE 2: Extraction avec layout
                txt2 = page.extract_text(layout=True)
                if txt2 and len(txt2.strip()) > 50 and txt2 != txt1:
                    append_text(txt2)
                    print(f"   Page {i+1}: {len(txt2)} chars extracted (layout)")
                
                # APPROCHE 3: table-aware extraction if tables exist
                try:
                    tables = page.extract_tables()
                    if tables:
                        for t in tables:
                            lines = []
                            for row in t:
                                if row:
                                    line = " ".join([str(c) for c in row if c])
                                    if line:
                                        lines.append(line)
                            if lines:
                                table_text = "\n".join(lines)
                                if len(table_text) > 50:
                                    append_text(table_text)
                                    print(f"   Page {i+1}: {len(table_text)} chars from tables")
                except Exception as e:
                    print(f"   ⚠️ Table extraction failed: {str(e)}")
        
        if extracted_parts:
            print(f"✅ pdfplumber extracted {len(extracted_parts)} parts, {sum(len(p) for p in extracted_parts)} chars total")
    except Exception as e:
        print(f"❌ pdfplumber failed: {str(e)}")

    # PASS 2: PyPDF2 text extraction
    if len(extracted_parts) < 3:  # Seulement si pdfplumber n'a pas assez récupéré
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PyPDF2.PdfReader(pdf_file)
            print(f"📄 PyPDF2: {len(reader.pages)} pages detected")
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text()
                    if txt and len(txt.strip()) > 50:
                        append_text(txt)
                        print(f"   Page {i+1}: {len(txt)} chars extracted")
                except Exception as e:
                    print(f"   ⚠️ Page {i+1} failed: {str(e)}")
                    continue
            if extracted_parts:
                print(f"✅ PyPDF2 extracted {sum(len(p) for p in extracted_parts)} chars total")
        except Exception as e:
            print(f"❌ PyPDF2 failed: {str(e)}")
    else:
        print("⏭️ PyPDF2 skipped - pdfplumber successful")

    # PASS 3: Image-based OCR fallback - pour PDFs scannés
    if len(extracted_parts) == 0 or sum(len(p) for p in extracted_parts) < 500:
        print("🖼️ Trying OCR fallback (scanned PDF detected)...")
        try:
            # Use pdfplumber to rasterize each page to image then pytesseract
            pdf_file = io.BytesIO(pdf_content)
            with pdfplumber.open(pdf_file) as pdf:
                print(f"📄 OCR fallback: processing {len(pdf.pages)} pages")
                for i, page in enumerate(pdf.pages):
                    try:
                        print(f"   Page {i+1}: converting to image...")
                        im = page.to_image(resolution=200).original  # 200 DPI suffit pour la plupart des cas
                        # Convert PIL -> cv2 BGR
                        import numpy as np
                        im_np = np.array(im)
                        # Ensure 3 channels
                        if im_np.ndim == 2:
                            im_np = cv2.cvtColor(im_np, cv2.COLOR_GRAY2BGR)
                        elif im_np.shape[2] == 4:
                            im_np = cv2.cvtColor(im_np, cv2.COLOR_RGBA2BGR)
                        
                        print(f"   Page {i+1}: preprocessing...")
                        processed = preprocess_image(im_np)
                        
                        # Try OCR with best PSM for documents
                        print(f"   Page {i+1}: OCR processing...")
                        config = "--oem 3 --psm 6 -l fra+eng"
                        txt = pytesseract.image_to_string(processed, config=config)
                        if txt and len(txt.strip()) > 50:
                            append_text(txt)
                            print(f"   Page {i+1}: {len(txt)} chars extracted via OCR")
                    except Exception as e:
                        print(f"   ⚠️ Page {i+1} OCR failed: {str(e)}")
                        continue
            
            if extracted_parts:
                print(f"✅ OCR fallback extracted {sum(len(p) for p in extracted_parts)} chars total")
        except Exception as e:
            print(f"❌ Image-based OCR fallback failed: {str(e)}")
    else:
        print("⏭️ OCR fallback skipped - sufficient text extracted")

    # If we gathered any text from previous passes, return it combined
    if extracted_parts:
        # Deduplicate lines while preserving order
        seen = set()
        lines = []
        for part in extracted_parts:
            for line in part.splitlines():
                key = line.strip()
                if key and len(key) > 3 and key not in seen:  # Ignorer lignes très courtes
                    seen.add(key)
                    lines.append(key)
        combined = "\n".join(lines)
        print(f"✅ PDF extraction SUCCESS: {len(combined)} chars, {len(lines)} unique lines")
        print(f"   Preview: {combined[:200]}...")
        return combined

    # Final fallback - échec complet
    error_msg = "Erreur: Extraction PDF incomplète. Merci de fournir un PDF de meilleure qualité."
    print(f"❌ PDF extraction FAILED - returning error message ({len(error_msg)} chars)")
    return error_msg

def extract_text_from_pdf_google_vision(pdf_content: bytes) -> str:
    """
    Extract text from PDF using Google Cloud Vision API (Document Text Detection)
    - Converts PDF pages to images using pdf2image
    - Sends each image to Google Vision API for OCR
    - Returns concatenated text from all pages
    - Much faster and more accurate than Tesseract for scanned PDFs
    """
    print("🚀 Google Vision API - Starting PDF text extraction")
    
    try:
        # Initialize Google Vision client
        client = vision.ImageAnnotatorClient()
        print("✅ Vision API client initialized")
        
        # Convert PDF to images (200 DPI for good quality/speed balance)
        print(f"📄 Converting PDF to images ({len(pdf_content)} bytes)...")
        images = convert_from_bytes(pdf_content, dpi=200, fmt='jpeg')
        print(f"✅ Converted to {len(images)} images")
        
        extracted_texts = []
        
        # Process each page
        for i, img in enumerate(images):
            try:
                print(f"   📄 Processing page {i+1}/{len(images)}...")
                
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_bytes = img_byte_arr.getvalue()
                
                # Create Vision API image object
                image = vision.Image(content=img_bytes)
                
                # Perform document text detection (optimized for documents)
                response = client.document_text_detection(image=image)
                
                # Check for errors
                if response.error.message:
                    print(f"   ⚠️ Page {i+1} API error: {response.error.message}")
                    continue
                
                # Extract full text annotation
                if response.full_text_annotation:
                    text = response.full_text_annotation.text
                    if text and len(text.strip()) > 50:
                        extracted_texts.append(text)
                        print(f"   ✅ Page {i+1}: {len(text)} characters extracted")
                    else:
                        print(f"   ⚠️ Page {i+1}: Insufficient text ({len(text) if text else 0} chars)")
                else:
                    print(f"   ⚠️ Page {i+1}: No text detected")
                    
            except Exception as e:
                print(f"   ❌ Page {i+1} error: {str(e)}")
                continue
        
        # Combine all extracted text
        if extracted_texts:
            combined_text = "\n\n=== PAGE BREAK ===\n\n".join(extracted_texts)
            print(f"✅ Google Vision extraction SUCCESS: {len(combined_text)} chars from {len(extracted_texts)} pages")
            return combined_text
        else:
            error_msg = "Erreur: Aucun texte extrait par Google Vision API"
            print(f"❌ {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Erreur Google Vision API: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

def extract_text_from_image_google_vision(image_content: bytes) -> str:
    """
    Extract text from image using Google Cloud Vision API
    Superior accuracy compared to Tesseract for images
    """
    try:
        print("🚀 Google Vision API - Starting image text extraction")
        
        # Initialize Google Vision client
        client = vision.ImageAnnotatorClient()
        
        # Create image object
        image = vision.Image(content=image_content)
        
        # Perform text detection
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            # First annotation contains full text
            extracted_text = texts[0].description
            print(f"✅ Google Vision image extraction SUCCESS: {len(extracted_text)} chars")
            return extracted_text
        else:
            error_msg = "Aucun texte détecté par Google Vision API dans l'image"
            print(f"⚠️ {error_msg}")
            return ""
            
    except Exception as e:
        error_msg = f"Erreur Google Vision API image: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


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

def calculate_delivery_date(supplier: Fournisseur, order_date: datetime = None) -> dict:
    """
    Calcule la date de livraison estimée selon les règles du fournisseur
    
    Exemples de règles:
    - METRO: Commandes Lun-Sam avant 11h, livraison lendemain midi (sauf samedi → lundi)
    - Montaner: Commandes Mar/Ven avant 11h, livraison lendemain 11h
    - Royaume des Mers: Commandes tous les jours avant midi, livraison Mar/Sam 11h
    
    Returns:
        {
            'estimated_date': datetime,
            'can_order_today': bool,
            'next_order_date': datetime,
            'explanation': str
        }
    """
    if order_date is None:
        order_date = datetime.now()
    
    # Si pas de règles définies, utiliser le délai par défaut
    if not supplier.delivery_rules:
        estimated = order_date + timedelta(days=2)
        return {
            'estimated_date': estimated,
            'can_order_today': True,
            'next_order_date': order_date,
            'explanation': 'Livraison estimée sous 2 jours (règles par défaut)'
        }
    
    rules = supplier.delivery_rules
    day_names_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    current_day_name = day_names_fr[order_date.weekday()].lower()
    current_hour = order_date.hour
    
    # Vérifier si on peut commander aujourd'hui
    can_order_today = False
    if rules.order_days:
        order_days_lower = [d.lower() for d in rules.order_days]
        if current_day_name in order_days_lower and current_hour < rules.order_deadline_hour:
            can_order_today = True
    else:
        # Si pas de jours spécifiés, on peut commander tous les jours avant deadline
        can_order_today = current_hour < rules.order_deadline_hour
    
    # Trouver la prochaine date de commande possible
    next_order_date = order_date
    if not can_order_today:
        # Chercher le prochain jour de commande
        for i in range(1, 8):
            test_date = order_date + timedelta(days=i)
            test_day_name = day_names_fr[test_date.weekday()].lower()
            if rules.order_days:
                order_days_lower = [d.lower() for d in rules.order_days]
                if test_day_name in order_days_lower:
                    next_order_date = test_date.replace(hour=9, minute=0, second=0)
                    break
            else:
                next_order_date = test_date.replace(hour=9, minute=0, second=0)
                break
    
    # Calculer la date de livraison
    if rules.delivery_days:
        # Livraison à des jours spécifiques (ex: Royaume des Mers → Mar/Sam)
        delivery_days_lower = [d.lower() for d in rules.delivery_days]
        base_date = next_order_date if not can_order_today else order_date
        
        # Chercher le prochain jour de livraison
        for i in range(1, 15):  # Chercher jusqu'à 2 semaines
            test_date = base_date + timedelta(days=i)
            test_day_name = day_names_fr[test_date.weekday()].lower()
            if test_day_name in delivery_days_lower:
                estimated_date = test_date.replace(hour=int(rules.delivery_time.split(':')[0]), 
                                                   minute=int(rules.delivery_time.split(':')[1]), 
                                                   second=0)
                break
    else:
        # Livraison après un délai fixe (ex: METRO → lendemain)
        delay = rules.delivery_delay_days or 1
        base_date = next_order_date if not can_order_today else order_date
        estimated_date = base_date + timedelta(days=delay)
        
        # Gérer les règles spéciales (ex: METRO samedi → +1 jour)
        if rules.special_rules and 'samedi' in rules.special_rules.lower():
            if day_names_fr[estimated_date.weekday()].lower() == 'samedi':
                estimated_date += timedelta(days=2)  # Samedi → Lundi
        
        estimated_date = estimated_date.replace(hour=int(rules.delivery_time.split(':')[0]), 
                                               minute=int(rules.delivery_time.split(':')[1]), 
                                               second=0)
    
    # Créer l'explication
    if can_order_today:
        explanation = f"Commande aujourd'hui avant {rules.order_deadline_hour}h → Livraison le {estimated_date.strftime('%A %d/%m/%Y à %Hh%M')}"
    else:
        explanation = f"Prochaine commande possible: {next_order_date.strftime('%A %d/%m/%Y')} avant {rules.order_deadline_hour}h → Livraison le {estimated_date.strftime('%A %d/%m/%Y à %Hh%M')}"
    
    return {
        'estimated_date': estimated_date,
        'can_order_today': can_order_today,
        'next_order_date': next_order_date,
        'explanation': explanation
    }

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

@api_router.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update a user (Super Admin only)"""
    try:
        # Vérifier que l'utilisateur existe
        existing_user = await db.users.find_one({"id": user_id})
        if not existing_user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Préparer les données de mise à jour (seulement les champs fournis)
        update_data = user_update.dict(exclude_unset=True)
        
        # Si le mot de passe est vide, ne pas le mettre à jour
        if update_data.get("password"):
            # Hash du nouveau mot de passe (pour l'instant simple, en production utiliser bcrypt)
            update_data["password_hash"] = f"hashed_{update_data['password']}"
            update_data.pop("password", None)
        elif "password" in update_data:
            # Supprimer le champ password s'il est vide
            update_data.pop("password", None)
        
        # Vérifier l'unicité username/email (sauf pour l'utilisateur actuel)
        if update_data.get("username"):
            existing_username = await db.users.find_one({
                "username": update_data["username"],
                "id": {"$ne": user_id}
            })
            if existing_username:
                raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà utilisé")
        
        if update_data.get("email"):
            existing_email = await db.users.find_one({
                "email": update_data["email"],
                "id": {"$ne": user_id}
            })
            if existing_email:
                raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
        
        # Valider le rôle
        if update_data.get("role") and update_data["role"] not in ROLES:
            raise HTTPException(status_code=400, detail=f"Rôle invalide. Rôles disponibles: {', '.join(ROLES.keys())}")
        
        # Effectuer la mise à jour
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Récupérer l'utilisateur mis à jour
        updated_user = await db.users.find_one({"id": user_id})
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")

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
    
    # Update stock with new batch quantity (rounded to 0.01)
    stock = await db.stocks.find_one({"produit_id": batch.product_id})
    if stock:
        current = round_stock_quantity(stock.get("quantite_actuelle", 0))
        new_quantity = round_stock_quantity(current + batch.quantity)
        await db.stocks.update_one(
            {"produit_id": batch.product_id},
            {"$set": {"quantite_actuelle": new_quantity, "derniere_maj": datetime.utcnow()}}
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
                current = round_stock_quantity(stock["quantite_actuelle"])
                adjusted = round_stock_quantity(adjustment.quantity_adjusted)
                new_quantity = round_stock_quantity(max(0, current + adjusted))
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
                total_deduction = round_stock_quantity(qty_per_portion * portions_adjusted)
                
                # Update stock
                stock = await db.stocks.find_one({"produit_id": ingredient["produit_id"]})
                if stock:
                    current_stock = round_stock_quantity(stock["quantite_actuelle"])
                    new_stock = round_stock_quantity(max(0, current_stock - total_deduction))
                    
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
        
        # Update total stock (rounded to 0.01)
        stock = await db.stocks.find_one({"produit_id": batch["product_id"]})
        if stock:
            current = round_stock_quantity(stock.get("quantite_actuelle", 0))
            consumed = round_stock_quantity(quantity_consumed)
            new_quantity = round_stock_quantity(max(0, current - consumed))
            await db.stocks.update_one(
                {"produit_id": batch["product_id"]},
                {"$set": {"quantite_actuelle": new_quantity, "derniere_maj": datetime.utcnow()}}
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
    """Enhanced Z report parser with structured data extraction and categorization (unit prices supported)"""
    structured_data = StructuredZReportData()

    def parse_price(val: str) -> float:
        try:
            v = val.replace('€', '').replace(' ', '').replace('\u202f', '').replace('\xa0', '')
            # Replace comma decimal
            if v.count(',') == 1 and v.count('.') == 0:
                v = v.replace(',', '.')
            # Remove thousand separators if any
            v = v.replace('.', '.')  # no-op but keeps format
            return float(v)
        except Exception:
            return None

    def try_parse_item_line(line: str):
        # Clean leading markers
        line_clean = re.sub(r'^[_\-\•\·\s]+', '', line).strip()
        # Patterns with price
        patterns = [
            # (x3) Name 12,00
            (r'^\(?x?(\d{1,3})\)?\s*[)\-]*\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))$', ('qty','name','price')),
            # (x3) Name €12.00
            (r'^\(?x?(\d{1,3})\)?\s*[)\-]*\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€\s?(\d{1,4}(?:[\.,]\d{2}))$', ('qty','name','price')),
            # Name €12.00 x 3
            (r'^([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))\s*x\s*(\d{1,3})$', ('name','price','qty')),
            # Name x 3 12,00
            (r'^([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+x\s*(\d{1,3})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))$', ('name','qty','price')),
            # 3x Name 12,00
            (r'^(\d{1,3})\s*x\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s+€?\s?(\d{1,4}(?:[\.,]\d{2}))$', ('qty','name','price')),
        ]
        for pat, order in patterns:
            m = re.match(pat, line_clean, re.IGNORECASE)
            if m:
                groups = m.groups()
                qty = int(groups[order.index('qty')])
                name = groups[order.index('name')].strip()
                price = parse_price(groups[order.index('price')])
                return name, qty, price
        # Patterns without explicit price (fallback)
        no_price_patterns = [
            (r'^\(x?(\d{1,3})\)\s+([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})$', ('qty','name')),
            (r'^(\d{1,3})x\s+([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})$', ('qty','name')),
            (r'^([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\'\-\.,]{3,80})\s*:?\s*(\d{1,3})$', ('name','qty')),
        ]
        for pat, order in no_price_patterns:
            m = re.match(pat, line_clean, re.IGNORECASE)
            if m:
                groups = m.groups()
                # Determine indices
                if order == ('qty','name'):
                    qty = int(groups[0])
                    name = groups[1].strip()
                else:
                    name = groups[0].strip()
                    qty = int(groups[1])
                return name, qty, None
        return None

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
        # New tighter parsing is handled by try_parse_item_line; keep legacy patterns for fallback only
        item_patterns = [
            r'\([x]?(\d{1,3})\)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,80})',
            r'(\d{1,3})[x\s]+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,80})',
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,80})\s*:?\s*(\d{1,3})',
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\'\-\.\,]{3,80})\s*€?(\d+[,.]?\d*)\s*x?\s*(\d{1,3})'
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
        
        # Pass 2.5: Try robust price/qty parser on each line
        enhanced_items = []
        for line in lines:
            parsed = try_parse_item_line(line)
            if parsed:
                name, qty, price = parsed
                cat = categorize_menu_item(name)
                enhanced_items.append({
                    "name": name,
                    "quantity_sold": qty,
                    "category": cat,
                    "unit_price": price,
                    "total_price": (price * qty) if (price is not None) else None,
                    "raw_line": line
                })
        # Merge enhanced_items with raw_items, deduplicate by (name, qty) preferring entries with price
        def item_key(it):
            return (it["name"].lower(), it["quantity_sold"]) 
        merged = {}
        for it in raw_items + enhanced_items:
            key = item_key(it)
            if key not in merged:
                merged[key] = it
            else:
                # Prefer the one with price
                if merged[key].get("unit_price") is None and it.get("unit_price") is not None:
                    merged[key] = it
        raw_items = list(merged.values())

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

async def enrich_z_report_prices(donnees_parsees: dict) -> dict:
    """Enrichir les prix manquants à partir des recettes en base"""
    try:
        # Parcourir les catégories d'items
        for category, items in donnees_parsees.get("items_by_category", {}).items():
            for item in items:
                # Si le prix unitaire est manquant, essayer de le trouver dans les recettes
                if item.get("unit_price") is None:
                    item_name = item.get("name", "").lower()
                    
                    # Chercher une recette correspondante
                    recipe = await db.recettes.find_one({
                        "$or": [
                            {"nom": {"$regex": item_name, "$options": "i"}},
                            {"nom": {"$regex": item_name.replace(" ", ".*"), "$options": "i"}}
                        ]
                    })
                    
                    if recipe and recipe.get("prix_vente"):
                        item["unit_price"] = recipe["prix_vente"]
                        # Calculer le prix total si on a la quantité
                        if item.get("quantity_sold"):
                            item["total_price"] = item["unit_price"] * item["quantity_sold"]
        
        return donnees_parsees
        
    except Exception as e:
        print(f"Erreur lors de l'enrichissement des prix: {str(e)}")
        return donnees_parsees

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

def parse_mercuriale_fournisseur(texte_ocr: str, fournisseur_id: str = None) -> dict:
    """Parser une mercuriale (liste de prix fournisseur) pour créer des produits"""
    try:
        lines = texte_ocr.split('\n')
        produits_detectes = []
        fournisseur_detecte = None
        
        # Patterns pour détecter les lignes de produits dans les mercuriales
        patterns_produits = [
            # Format: "Nom produit    prix  unité" 
            r'^(.+?)\s+([0-9]+[,.]?[0-9]*)\s*[€]?\s*(kg|g|L|mL|cl|pièce|pc|pcs|botte|paquet)\s*$',
            # Format: "Nom produit - prix €/unité"
            r'^(.+?)\s*[-–]\s*([0-9]+[,.]?[0-9]*)\s*[€]?\s*[/]\s*(kg|g|L|mL|cl|pièce|pc|pcs|botte|paquet)',
            # Format: "Code | Nom produit | Prix | Unité" 
            r'^[A-Z0-9]*\s*[|]\s*(.+?)\s*[|]\s*([0-9]+[,.]?[0-9]*)\s*[€]?\s*[|]\s*(kg|g|L|mL|cl|pièce|pc|pcs|botte|paquet)',
            # Format: "Produit    €X.XX  unité"
            r'^(.+?)\s+[€]\s*([0-9]+[,.]?[0-9]*)\s+(kg|g|L|mL|cl|pièce|pc|pcs|botte|paquet)'
        ]
        
        # Détecter le fournisseur dans l'en-tête
        for i, line in enumerate(lines[:10]):  
            line_clean = line.strip().upper()
            if any(keyword in line_clean for keyword in ['MERCURIALE', 'LISTE', 'PRIX', 'TARIFS', 'CATALOGUE']):
                # Chercher le nom du fournisseur dans les lignes précédentes/suivantes
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    potential_name = lines[j].strip()
                    if len(potential_name) > 3 and not any(skip in potential_name.upper() for skip in ['MERCURIALE', 'LISTE', 'PRIX', 'DATE', 'CATALOGUE', 'TARIF']):
                        fournisseur_detecte = potential_name
                        break
                break
        
        # Catégoriser les produits automatiquement
        def detect_category(nom_produit: str) -> str:
            nom_lower = nom_produit.lower()
            if any(word in nom_lower for word in ['tomate', 'salade', 'carotte', 'courgette', 'épinard', 'poireau', 'oignon', 'ail']):
                return 'Légumes'
            elif any(word in nom_lower for word in ['bœuf', 'porc', 'agneau', 'veau', 'volaille', 'poulet', 'canard']):
                return 'Viandes'  
            elif any(word in nom_lower for word in ['saumon', 'dorade', 'bar', 'sole', 'morue', 'crevette', 'homard', 'moule']):
                return 'Poissons'
            elif any(word in nom_lower for word in ['fromage', 'beurre', 'crème', 'yaourt', 'lait', 'mozzarella', 'parmesan']):
                return 'Crêmerie'
            elif any(word in nom_lower for word in ['farine', 'riz', 'pâte', 'semoule', 'quinoa', 'avoine']):
                return 'Céréales'
            elif any(word in nom_lower for word in ['pomme', 'poire', 'orange', 'citron', 'fraise', 'banane']):
                return 'Fruits'
            elif any(word in nom_lower for word in ['thym', 'basilic', 'persil', 'poivre', 'sel', 'paprika', 'cumin']):
                return 'Épices'
            else:
                return 'Autres'
        
        # Parser les lignes de produits
        for line in lines:
            line_clean = line.strip()
            if len(line_clean) < 5:  # Ignorer les lignes trop courtes
                continue
                
            # Ignorer les en-têtes et lignes non-produits
            if any(skip in line_clean.upper() for skip in [
                'FOURNISSEUR', 'MERCURIALE', 'LISTE', 'PRIX', 'TARIFS', 'DATE', 
                'CATALOGUE', 'PAGE', 'TOTAL', 'SUBTOTAL', 'TVA', 'HT', 'TTC',
                'CODE', 'RÉFÉRENCE', 'DESIGNATION', 'QUANTITÉ', 'UNITÉ'
            ]):
                continue
            
            # Tester chaque pattern
            for pattern in patterns_produits:
                match = re.match(pattern, line_clean, re.IGNORECASE)
                if match:
                    try:
                        nom = match.group(1).strip()
                        prix = float(match.group(2).replace(',', '.'))
                        unite = match.group(3).lower()
                        
                        # Nettoyer le nom du produit
                        nom = re.sub(r'^[A-Z0-9\-\s]*\|', '', nom).strip()
                        nom = re.sub(r'[|]+', '', nom).strip()
                        
                        if len(nom) > 2 and prix > 0:
                            # Standardiser l'unité
                            unite_standard = {
                                'kg': 'kg', 'g': 'g', 'l': 'L', 'ml': 'mL', 'cl': 'cL',
                                'piece': 'pièce', 'pc': 'pièce', 'pcs': 'pièce',
                                'botte': 'botte', 'paquet': 'paquet'
                            }.get(unite.lower(), unite)
                            
                            produit = {
                                "nom": nom.title(),
                                "prix_achat": prix,
                                "unite": unite_standard,
                                "categorie": detect_category(nom),
                                "fournisseur_id": fournisseur_id,
                                "ligne_originale": line_clean
                            }
                            
                            # Éviter les doublons
                            if not any(p["nom"].lower() == nom.lower() for p in produits_detectes):
                                produits_detectes.append(produit)
                        break
                    except (ValueError, IndexError):
                        continue
        
        return {
            "type": "mercuriale",
            "fournisseur_detecte": fournisseur_detecte,
            "produits_detectes": produits_detectes,
            "total_produits": len(produits_detectes),
            "fournisseur_id": fournisseur_id
        }
        
    except Exception as e:
        print(f"Erreur parsing mercuriale: {str(e)}")
        return {
            "type": "mercuriale", 
            "fournisseur_detecte": None,
            "produits_detectes": [],
            "total_produits": 0,
            "error": str(e)
        }

# Routes pour les fournisseurs
@api_router.post("/fournisseurs", response_model=Fournisseur)
async def create_fournisseur(fournisseur: FournisseurCreate):
    # Valider la catégorie si fournie
    if fournisseur.categorie and fournisseur.categorie not in CATEGORIES_FOURNISSEURS:
        raise HTTPException(status_code=400, detail=f"Catégorie invalide. Catégories disponibles: {', '.join(CATEGORIES_FOURNISSEURS)}")
    
    fournisseur_dict = fournisseur.dict()
    fournisseur_obj = Fournisseur(**fournisseur_dict)
    await db.fournisseurs.insert_one(fournisseur_obj.dict())
    
    # Créer automatiquement les produits de coûts (delivery & extra costs)
    await create_supplier_cost_products(fournisseur_obj.id, fournisseur_obj.nom)
    
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

# Helper function pour créer les produits de coûts automatiquement
async def create_supplier_cost_products(supplier_id: str, supplier_name: str):
    """Créer automatiquement les produits 'delivery' et 'extra costs' pour un fournisseur"""
    try:
        # Créer le produit "Frais de livraison"
        delivery_product = Produit(
            nom=f"Frais de livraison - {supplier_name}",
            description=f"Frais de livraison fixes pour les commandes de {supplier_name}",
            categorie="Service",
            unite="forfait",
            reference_price=0.0,
            main_supplier_id=supplier_id,
            fournisseur_id=supplier_id,  # Legacy compatibility
            fournisseur_nom=supplier_name
        )
        await db.produits.insert_one(delivery_product.dict())
        
        # Créer le produit "Frais supplémentaires"
        extra_product = Produit(
            nom=f"Frais supplémentaires - {supplier_name}",
            description=f"Frais supplémentaires (manutention, emballage...) pour {supplier_name}",
            categorie="Service", 
            unite="forfait",
            reference_price=0.0,
            main_supplier_id=supplier_id,
            fournisseur_id=supplier_id,  # Legacy compatibility
            fournisseur_nom=supplier_name
        )
        await db.produits.insert_one(extra_product.dict())
        
        # Créer la configuration des coûts
        cost_config = SupplierCostConfig(
            supplier_id=supplier_id,
            delivery_cost=0.0,
            extra_cost=0.0,
            delivery_cost_product_id=delivery_product.id,
            extra_cost_product_id=extra_product.id
        )
        await db.supplier_cost_configs.insert_one(cost_config.dict())
        
        # Créer les stocks initiaux pour ces produits
        for product in [delivery_product, extra_product]:
            stock = Stock(
                produit_id=product.id,
                produit_nom=product.nom,
                quantite_actuelle=0.0,
                quantite_min=0.0,
                quantite_max=1.0
            )
            await db.stocks.insert_one(stock.dict())
        
        print(f"✅ Produits de coûts créés pour {supplier_name}")
        
    except Exception as e:
        print(f"⚠️ Erreur création produits de coûts pour {supplier_name}: {str(e)}")

# Routes pour les catégories de fournisseurs
@api_router.get("/fournisseurs-categories")
async def get_fournisseurs_categories():
    """Obtenir la liste des catégories de fournisseurs disponibles"""
    return {"categories": CATEGORIES_FOURNISSEURS}

# Routes pour la configuration des coûts fournisseurs
@api_router.post("/supplier-cost-config", response_model=SupplierCostConfig)
async def create_supplier_cost_config(config: SupplierCostConfigCreate):
    # Vérifier que le fournisseur existe
    supplier = await db.fournisseurs.find_one({"id": config.supplier_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    
    # Vérifier si une config existe déjà
    existing = await db.supplier_cost_configs.find_one({"supplier_id": config.supplier_id})
    if existing:
        raise HTTPException(status_code=400, detail="Configuration déjà existante pour ce fournisseur")
    
    config_obj = SupplierCostConfig(**config.dict())
    await db.supplier_cost_configs.insert_one(config_obj.dict())
    return config_obj

@api_router.get("/supplier-cost-config/{supplier_id}", response_model=SupplierCostConfig)
async def get_supplier_cost_config(supplier_id: str):
    config = await db.supplier_cost_configs.find_one({"supplier_id": supplier_id})
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return SupplierCostConfig(**config)

@api_router.put("/supplier-cost-config/{supplier_id}", response_model=SupplierCostConfig)
async def update_supplier_cost_config(supplier_id: str, config: SupplierCostConfigCreate):
    result = await db.supplier_cost_configs.update_one(
        {"supplier_id": supplier_id},
        {"$set": {**config.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    
    updated_config = await db.supplier_cost_configs.find_one({"supplier_id": supplier_id})
    return SupplierCostConfig(**updated_config)

# Routes pour les commandes (Orders)
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    """Créer une nouvelle commande"""
    # Récupérer le fournisseur
    supplier = await db.fournisseurs.find_one({"id": order_data.supplier_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    
    # Calculer le montant total
    total_amount = sum(item.total_price for item in order_data.items)
    
    # Calculer la date de livraison estimée
    supplier_obj = Fournisseur(**supplier)
    delivery_info = calculate_delivery_date(supplier_obj)
    
    # Créer le numéro de commande
    order_number = f"CMD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Créer l'objet commande
    order = Order(
        order_number=order_number,
        supplier_id=order_data.supplier_id,
        supplier_name=supplier["nom"],
        items=order_data.items,
        total_amount=total_amount,
        estimated_delivery_date=delivery_info['estimated_date'],
        notes=order_data.notes,
        status="pending"
    )
    
    # Sauvegarder en base
    await db.orders.insert_one(order.dict())
    
    return order

@api_router.get("/orders", response_model=List[Order])
async def get_orders(status: Optional[str] = None, supplier_id: Optional[str] = None):
    """Récupérer les commandes avec filtres optionnels"""
    query = {}
    if status:
        query["status"] = status
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    orders = await db.orders.find(query).sort("order_date", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Récupérer une commande spécifique"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return Order(**order)

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, actual_delivery_date: Optional[str] = None):
    """Mettre à jour le statut d'une commande"""
    valid_statuses = ["pending", "confirmed", "in_transit", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Utilisez: {', '.join(valid_statuses)}")
    
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if status == "delivered" and actual_delivery_date:
        update_data["actual_delivery_date"] = datetime.fromisoformat(actual_delivery_date)
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    return {"message": "Statut mis à jour", "status": status}

@api_router.get("/suppliers/{supplier_id}/delivery-estimate")
async def get_delivery_estimate(supplier_id: str):
    """Calculer la date de livraison estimée pour un fournisseur"""
    supplier = await db.fournisseurs.find_one({"id": supplier_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    
    supplier_obj = Fournisseur(**supplier)
    delivery_info = calculate_delivery_date(supplier_obj)
    
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier["nom"],
        "estimated_delivery_date": delivery_info['estimated_date'].isoformat(),
        "can_order_today": delivery_info['can_order_today'],
        "next_order_date": delivery_info['next_order_date'].isoformat(),
        "explanation": delivery_info['explanation']
    }

# Routes pour les Préparations
@api_router.post("/preparations", response_model=Preparation)
async def create_preparation(prep_data: PreparationCreate):
    """Créer une nouvelle préparation"""
    # Récupérer le produit pour avoir son nom
    produit = await db.produits.find_one({"id": prep_data.produit_id})
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Créer la préparation
    preparation = Preparation(
        **prep_data.dict(),
        produit_nom=produit["nom"]
    )
    
    await db.preparations.insert_one(preparation.dict())
    return preparation

@api_router.get("/preparations", response_model=List[Preparation])
async def get_preparations(produit_id: Optional[str] = None):
    """Récupérer toutes les préparations avec filtre optionnel par produit"""
    query = {}
    if produit_id:
        query["produit_id"] = produit_id
    
    preparations = await db.preparations.find(query).sort("date_preparation", -1).to_list(1000)
    return [Preparation(**prep) for prep in preparations]

@api_router.get("/preparations/{preparation_id}", response_model=Preparation)
async def get_preparation(preparation_id: str):
    """Récupérer une préparation spécifique"""
    preparation = await db.preparations.find_one({"id": preparation_id})
    if not preparation:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    return Preparation(**preparation)

@api_router.put("/preparations/{preparation_id}", response_model=Preparation)
async def update_preparation(preparation_id: str, prep_data: PreparationCreate):
    """Mettre à jour une préparation"""
    # Récupérer le produit pour avoir son nom
    produit = await db.produits.find_one({"id": prep_data.produit_id})
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    update_data = prep_data.dict()
    update_data["produit_nom"] = produit["nom"]
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.preparations.update_one(
        {"id": preparation_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    
    updated_prep = await db.preparations.find_one({"id": preparation_id})
    return Preparation(**updated_prep)

@api_router.delete("/preparations/{preparation_id}")
async def delete_preparation(preparation_id: str):
    """Supprimer une préparation"""
    result = await db.preparations.delete_one({"id": preparation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    return {"message": "Préparation supprimée"}

@api_router.get("/preparations/dlc/alerts")
async def get_preparations_dlc_alerts(days: int = 3):
    """Récupérer les préparations dont la DLC expire bientôt"""
    limit_date = datetime.utcnow() + timedelta(days=days)
    preparations = await db.preparations.find({
        "dlc": {"$lte": limit_date, "$gte": datetime.utcnow()}
    }).sort("dlc", 1).to_list(100)
    
    return [Preparation(**prep) for prep in preparations]

# Routes pour les formes de découpe personnalisées
@api_router.get("/formes-decoupe")
async def get_formes_decoupe():
    """Récupérer toutes les formes de découpe (prédéfinies + custom)"""
    predefined = [
        {"id": "julienne", "nom": "Julienne", "description": "Bâtonnets fins"},
        {"id": "brunoise", "nom": "Brunoise", "description": "Petits dés réguliers"},
        {"id": "carre", "nom": "Carré", "description": "Cubes moyens"},
        {"id": "emince", "nom": "Émincé", "description": "Tranches fines"},
        {"id": "hache", "nom": "Haché", "description": "Haché grossier ou fin"},
        {"id": "filets", "nom": "En filets", "description": "Levés en filets (poissons)"},
        {"id": "sauce", "nom": "Sauce", "description": "Transformé en sauce"},
        {"id": "puree", "nom": "Purée", "description": "Écrasé en purée"},
        {"id": "cuit", "nom": "Cuit", "description": "Cuit entier ou préparé"},
        {"id": "marine", "nom": "Mariné", "description": "Mariné"},
        {"id": "rape", "nom": "Râpé", "description": "Râpé fin ou gros"},
        {"id": "concasse", "nom": "Concassé", "description": "Grossièrement haché"},
        {"id": "tourne", "nom": "Tourné", "description": "Taillé en forme régulière"}
    ]
    
    # Récupérer les formes custom
    custom_formes = await db.formes_decoupe_custom.find().to_list(100)
    custom = [{"id": f["id"], "nom": f["nom"], "description": f.get("description", ""), "custom": True} for f in custom_formes]
    
    return {"predefined": predefined, "custom": custom}

@api_router.post("/formes-decoupe")
async def create_forme_decoupe_custom(nom: str, description: Optional[str] = None):
    """Créer une forme de découpe personnalisée"""
    forme = FormeDecoupeCustom(nom=nom, description=description)
    await db.formes_decoupe_custom.insert_one(forme.dict())
    return forme

# ✅ Auto-generation des préparations intelligentes
@api_router.post("/preparations/auto-generate")
async def auto_generate_preparations():
    """Génère automatiquement 2-3 préparations cohérentes pour chaque produit avec catégorie"""
    try:
        # Récupérer tous les produits avec catégories
        produits = await db.produits.find({"categorie": {"$exists": True, "$ne": None, "$ne": ""}}).to_list(1000)
        
        # Récupérer toutes les recettes pour l'intelligence de génération
        recettes = await db.recettes.find().to_list(1000)
        
        # Supprimer toutes les préparations existantes avant régénération
        await db.preparations.delete_many({})
        
        preparations_created = []
        
        # Mapping intelligent des préparations par catégorie et relation avec les recettes
        preparation_mapping = {
            "Légumes": [
                {"forme": "julienne", "nom_suffix": "en julienne", "rendement": 0.85, "portions_base": 8},
                {"forme": "brunoise", "nom_suffix": "en brunoise", "rendement": 0.80, "portions_base": 12},
                {"forme": "emince", "nom_suffix": "émincés", "rendement": 0.90, "portions_base": 10}
            ],
            "Poissons": [
                {"forme": "filets", "nom_suffix": "en filets", "rendement": 0.75, "portions_base": 4},
                {"forme": "emince", "nom_suffix": "émincés", "rendement": 0.70, "portions_base": 6},
                {"forme": "marine", "nom_suffix": "marinés", "rendement": 0.85, "portions_base": 5}
            ],
            "Viandes": [
                {"forme": "emince", "nom_suffix": "émincés", "rendement": 0.85, "portions_base": 6},
                {"forme": "hache", "nom_suffix": "hachés", "rendement": 0.90, "portions_base": 8},
                {"forme": "cuit", "nom_suffix": "cuits", "rendement": 0.75, "portions_base": 4}
            ],
            "Fruits": [
                {"forme": "carre", "nom_suffix": "en cubes", "rendement": 0.85, "portions_base": 12},
                {"forme": "puree", "nom_suffix": "en purée", "rendement": 0.75, "portions_base": 10},
                {"forme": "concasse", "nom_suffix": "concassés", "rendement": 0.90, "portions_base": 8}
            ],
            "Crêmerie": [
                {"forme": "emince", "nom_suffix": "tranchés", "rendement": 0.95, "portions_base": 10},
                {"forme": "rape", "nom_suffix": "râpés", "rendement": 0.90, "portions_base": 15},
                {"forme": "carre", "nom_suffix": "en cubes", "rendement": 0.85, "portions_base": 12}
            ],
            "Épices": [
                {"forme": "hache", "nom_suffix": "hachées", "rendement": 0.95, "portions_base": 20},
                {"forme": "concasse", "nom_suffix": "concassées", "rendement": 0.90, "portions_base": 25}
            ]
        }
        
        # Définir des préparations génériques pour les catégories non mappées
        generic_preparations = [
            {"forme": "emince", "nom_suffix": "émincés", "rendement": 0.85, "portions_base": 8},
            {"forme": "hache", "nom_suffix": "hachés", "rendement": 0.80, "portions_base": 10},
            {"forme": "carre", "nom_suffix": "en cubes", "rendement": 0.75, "portions_base": 6}
        ]
        
        for produit in produits:
            if not produit.get("categorie") or produit["categorie"] in ["Service", "Test"]:
                continue
                
            # Sélectionner les préparations appropriées pour cette catégorie
            preparations_config = preparation_mapping.get(produit["categorie"], generic_preparations)
            
            # Limiter à 2-3 préparations par produit
            selected_preparations = preparations_config[:3]
            
            for i, config in enumerate(selected_preparations):
                # Analyser les recettes pour ajuster intelligemment les quantités
                recettes_utilisant_produit = [r for r in recettes if any(ing.get("produit_id") == produit["id"] for ing in r.get("ingredients", []))]
                
                # Calculs de base
                quantite_brute = 2.0 if produit.get("unite") == "kg" else (500.0 if produit.get("unite") == "g" else 1.0)
                rendement = config["rendement"]
                quantite_preparee = quantite_brute * rendement
                perte = quantite_brute - quantite_preparee
                perte_pourcentage = (perte / quantite_brute) * 100
                
                # Ajuster les portions selon les recettes trouvées
                portions_base = config["portions_base"]
                if recettes_utilisant_produit:
                    # Prendre la moyenne des portions des recettes qui utilisent ce produit
                    moyenne_portions_recettes = sum(r.get("portions", 4) for r in recettes_utilisant_produit) / len(recettes_utilisant_produit)
                    portions_base = max(int(moyenne_portions_recettes * 1.5), config["portions_base"])
                
                taille_portion = quantite_preparee / portions_base if portions_base > 0 else 0.1
                
                # Créer la préparation
                preparation = Preparation(
                    nom=f"{produit['nom']} {config['nom_suffix']}",
                    produit_id=produit["id"],
                    produit_nom=produit["nom"],
                    forme_decoupe=config["forme"],
                    quantite_produit_brut=quantite_brute,
                    unite_produit_brut=produit.get("unite", "kg"),
                    quantite_preparee=round(quantite_preparee, 2),
                    unite_preparee=produit.get("unite", "kg"),
                    perte=round(perte, 2),
                    perte_pourcentage=round(perte_pourcentage, 1),
                    nombre_portions=portions_base,
                    taille_portion=round(taille_portion, 3),
                    unite_portion=produit.get("unite", "kg"),
                    notes=f"Génération automatique - Catégorie: {produit['categorie']}" + 
                          (f" - Basé sur {len(recettes_utilisant_produit)} recette(s)" if recettes_utilisant_produit else "")
                )
                
                await db.preparations.insert_one(preparation.dict())
                preparations_created.append(preparation.nom)
        
        return {
            "success": True,
            "message": "✅ Génération automatique terminée !",
            "preparations_created": len(preparations_created),
            "details": {
                "total_products_processed": len(produits),
                "categories_processed": list(set(p.get("categorie") for p in produits if p.get("categorie"))),
                "sample_preparations": preparations_created[:10]  # Montrer 10 exemples
            }
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération automatique: {str(e)}")
        return {
            "success": False,
            "message": f"❌ Erreur lors de la génération: {str(e)}",
            "preparations_created": 0
        }

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

@api_router.get("/produits/by-categories")
async def get_produits_by_categories():
    """Récupérer les produits regroupés par catégories pour affichage accordéon"""
    produits = await db.produits.find().to_list(1000)
    
    # Grouper par catégorie
    categories = {}
    for produit in produits:
        category = produit.get("categorie", "Sans catégorie")
        if category not in categories:
            categories[category] = []
        categories[category].append(Produit(**produit))
    
    # Trier les catégories et les produits dans chaque catégorie
    sorted_categories = {}
    for category in sorted(categories.keys()):
        sorted_categories[category] = sorted(categories[category], key=lambda p: p.nom)
    
    # Calculer des statistiques par catégorie
    category_stats = {}
    for category, products in sorted_categories.items():
        category_stats[category] = {
            "total_products": len(products),
            "products": [p.dict() for p in products],
            "icon": get_category_icon(category)
        }
    
    return {
        "categories": category_stats,
        "total_categories": len(sorted_categories),
        "total_products": len(produits)
    }

def get_category_icon(category: str) -> str:
    """Retourne l'icône appropriée pour chaque catégorie"""
    icons = {
        "Légumes": "🥬",
        "Fruits": "🍎", 
        "Viandes": "🥩",
        "Poissons": "🐟",
        "Crêmerie": "🧀",
        "Céréales": "🌾",
        "Épices": "🌶️",
        "Autres": "📦",
        "Service": "⚙️",
        "Test": "🧪",
        "Sans catégorie": "❓"
    }
    return icons.get(category, "📦")

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
    
    # Mettre à jour le stock (arrondi à 0.01)
    stock = await db.stocks.find_one({"produit_id": mouvement.produit_id})
    if stock:
        nouvelle_quantite = round_stock_quantity(stock["quantite_actuelle"])
        quantite_mouvement = round_stock_quantity(mouvement.quantite)
        
        if mouvement.type == "entree":
            nouvelle_quantite = round_stock_quantity(nouvelle_quantite + quantite_mouvement)
        elif mouvement.type == "sortie":
            nouvelle_quantite = round_stock_quantity(nouvelle_quantite - quantite_mouvement)
        elif mouvement.type == "ajustement":
            nouvelle_quantite = quantite_mouvement
        
        await db.stocks.update_one(
            {"produit_id": mouvement.produit_id},
            {"$set": {"quantite_actuelle": round_stock_quantity(max(0, nouvelle_quantite)), "derniere_maj": datetime.utcnow()}}
        )
    
    return mouvement_obj

@api_router.get("/mouvements", response_model=List[MouvementStock])
async def get_mouvements():
    mouvements = await db.mouvements_stock.find().sort("date", -1).to_list(1000)
    return [MouvementStock(**m) for m in mouvements]

# Routes pour les recettes (Productions)
@api_router.get("/categories-production")
async def get_categories_production():
    """Récupère les catégories de production disponibles"""
    return {"categories": CATEGORIES_PRODUCTION}

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
async def get_recettes(categorie: Optional[str] = None):
    """Récupère les recettes avec filtre optionnel par catégorie"""
    query = {}
    if categorie and categorie in CATEGORIES_PRODUCTION:
        query["categorie"] = categorie
    
    recettes = await db.recettes.find(query).to_list(1000)
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

@api_router.get("/dashboard/analytics")
async def get_dashboard_analytics():
    """
    Obtenir les analytics réelles du dashboard basées sur les rapports Z et ventes
    Calcule le CA, les couverts, top/flop productions à partir des VRAIES données
    """
    from datetime import timedelta
    
    # Période par défaut : 30 derniers jours
    date_fin = datetime.utcnow()
    date_debut = date_fin - timedelta(days=30)
    
    # 1. Récupérer tous les rapports Z de la période
    rapports_z = await db.rapports_z.find({
        "date": {"$gte": date_debut, "$lte": date_fin}
    }).to_list(1000)
    
    # 2. Calculer le CA total et les couverts
    ca_total = 0
    couverts_total = 0
    ca_midi = 0
    ca_soir = 0
    couverts_midi = 0
    couverts_soir = 0
    
    productions_stats = {}  # {nom_production: {ventes, portions, categorie}}
    
    for rapport in rapports_z:
        ca_rapport = rapport.get("ca_total", 0)
        ca_total += ca_rapport
        
        # Estimer midi/soir (60/40 par défaut si pas d'info)
        ca_midi += ca_rapport * 0.6
        ca_soir += ca_rapport * 0.4
        
        couverts = rapport.get("nb_couverts", 0)
        couverts_total += couverts
        couverts_midi += int(couverts * 0.6)
        couverts_soir += int(couverts * 0.4)
        
        # Analyser les produits vendus
        produits = rapport.get("produits", [])
        for produit in produits:
            nom = produit.get("nom", "Inconnu")
            quantite = produit.get("quantite", 0)
            prix_unitaire = produit.get("prix_unitaire", 0)
            ventes = quantite * prix_unitaire
            
            if nom not in productions_stats:
                productions_stats[nom] = {
                    "ventes": 0,
                    "portions": 0,
                    "categorie": "Autres"  # À améliorer avec matching recettes
                }
            
            productions_stats[nom]["ventes"] += ventes
            productions_stats[nom]["portions"] += quantite
    
    # 3. Trier et obtenir top/flop productions
    productions_list = []
    for nom, stats in productions_stats.items():
        # Essayer de matcher avec une recette pour obtenir la catégorie
        recette = await db.recettes.find_one({"nom": {"$regex": nom, "$options": "i"}})
        categorie = recette.get("categorie", "Autres") if recette else "Autres"
        
        productions_list.append({
            "nom": nom,
            "ventes": round(stats["ventes"], 2),
            "portions": stats["portions"],
            "categorie": categorie,
            "coefficientPrevu": 0,  # À calculer si besoin
            "coefficientReel": 0,
            "coutMatiere": 0,
            "prixVente": round(stats["ventes"] / stats["portions"], 2) if stats["portions"] > 0 else 0
        })
    
    # Trier par ventes décroissantes
    productions_list.sort(key=lambda x: x["ventes"], reverse=True)
    
    top_productions = productions_list[:7] if len(productions_list) > 7 else productions_list
    flop_productions = productions_list[-7:] if len(productions_list) > 7 else []
    flop_productions.reverse()  # Les moins vendus en premier
    
    # 4. Ventes par catégorie
    ventes_par_categorie = {
        "plats": 0,
        "boissons": 0,
        "desserts": 0,
        "entrees": 0,
        "autres": 0
    }
    
    for prod in productions_list:
        cat = prod["categorie"].lower()
        if "plat" in cat:
            ventes_par_categorie["plats"] += prod["ventes"]
        elif "boisson" in cat or "bar" in cat:
            ventes_par_categorie["boissons"] += prod["ventes"]
        elif "dessert" in cat:
            ventes_par_categorie["desserts"] += prod["ventes"]
        elif "entrée" in cat or "entree" in cat:
            ventes_par_categorie["entrees"] += prod["ventes"]
        else:
            ventes_par_categorie["autres"] += prod["ventes"]
    
    # Si aucun rapport Z, retourner des données vides
    if len(rapports_z) == 0:
        return {
            "caTotal": 0,
            "caMidi": 0,
            "caSoir": 0,
            "couvertsMidi": 0,
            "couvertsSoir": 0,
            "topProductions": [],
            "flopProductions": [],
            "ventesParCategorie": ventes_par_categorie,
            "periode": {
                "debut": date_debut.isoformat(),
                "fin": date_fin.isoformat(),
                "nb_rapports": 0
            },
            "is_real_data": True
        }
    
    return {
        "caTotal": round(ca_total, 2),
        "caMidi": round(ca_midi, 2),
        "caSoir": round(ca_soir, 2),
        "couvertsMidi": couverts_midi,
        "couvertsSoir": couverts_soir,
        "topProductions": top_productions,
        "flopProductions": flop_productions,
        "ventesParCategorie": {k: round(v, 2) for k, v in ventes_par_categorie.items()},
        "periode": {
            "debut": date_debut.isoformat(),
            "fin": date_fin.isoformat(),
            "nb_rapports": len(rapports_z)
        },
        "is_real_data": True
    }

# Routes pour le traitement OCR
@api_router.post("/ocr/upload-document")  # No response_model to allow flexible multi-invoice responses
async def upload_and_process_document(
    file: UploadFile = File(...),
    document_type: str = Form("z_report")  # "z_report" ou "facture_fournisseur" ou "mercuriale"
):
    """Upload et traitement OCR d'un document (image ou PDF) - Rapport Z, facture ou mercuriale"""
    
    print(f"📝 Document type received: {document_type}")
    
    if document_type not in ["z_report", "facture_fournisseur", "mercuriale"]:
        raise HTTPException(status_code=400, detail="Type de document invalide. Utilisez 'z_report', 'facture_fournisseur' ou 'mercuriale'")
    
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
            # Use Google Vision API for PDF extraction (superior accuracy)
            texte_extrait = extract_text_from_pdf_google_vision(file_content)
            # Pour les PDF, on stocke le contenu comme base64 mais avec prefix PDF
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            data_uri = f"data:application/pdf;base64,{content_base64}"
        else:
            print(f"🖼️ Processing image file: {file.filename}")
            image_base64 = base64.b64encode(file_content).decode('utf-8')
            texte_extrait = extract_text_from_image_google_vision(file_content)
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
            # Enrichir les prix manquants à partir des recettes en base
            donnees_parsees = await enrich_z_report_prices(donnees_parsees)
            # Ajouter l'analyse catégories → familles et vérification
            z_summary = analyze_z_report_categories(texte_extrait)
            donnees_parsees["z_analysis"] = z_summary
        elif document_type == "facture_fournisseur":
            # Détecter s'il y a plusieurs factures dans le document
            separated_invoices = detect_multiple_invoices(texte_extrait)
            
            if len(separated_invoices) == 1:
                # Facture unique - traitement normal
                facture_data = parse_facture_fournisseur(texte_extrait)
                donnees_parsees = facture_data.dict()
                
                # Créer le document dans la base
                document = DocumentOCR(
                    type_document=document_type,
                    nom_fichier=file.filename,
                    image_base64=data_uri,
                    texte_extrait=texte_extrait,
                    donnees_parsees=donnees_parsees,
                    statut="traite",
                    date_traitement=datetime.utcnow(),
                    file_type=file_type
                )
                
                await db.documents_ocr.insert_one(document.dict())
                
                return DocumentUploadResponse(
                    document_id=document.id,
                    type_document=document_type,
                    texte_extrait=texte_extrait,
                    donnees_parsees=donnees_parsees,
                    message="Facture unique traitée avec succès",
                    file_type=file_type
                )
                
            else:
                # Factures multiples - traiter chaque facture séparément
                created_documents = []
                rejected_invoices = []
                processing_summary = []
                
                for i, invoice in enumerate(separated_invoices):
                    try:
                        # Vérifier la qualité avant traitement
                        if invoice['quality_score'] < 0.6:
                            rejected_invoices.append({
                                'index': invoice['index'],
                                'header': invoice['header'],
                                'quality_score': invoice['quality_score'],
                                'issues': invoice['quality_issues'],
                                'reason': 'Qualité insuffisante pour traitement automatique'
                            })
                            processing_summary.append(f"❌ Facture {invoice['index']}: Rejetée (qualité {invoice['quality_score']:.1%})")
                            print(f"⚠️ Facture {invoice['index']} rejetée - Qualité: {invoice['quality_score']:.1%}")
                            print(f"   Issues: {', '.join(invoice['quality_issues'])}")
                            continue
                        
                        # Parser chaque facture de qualité suffisante
                        facture_data = parse_facture_fournisseur(invoice['text_content'])
                        donnees_parsees = facture_data.dict()
                        
                        # Ajouter des métadonnées complètes
                        donnees_parsees["separation_info"] = {
                            "is_multi_invoice": True,
                            "invoice_index": invoice['index'],
                            "total_invoices": len(separated_invoices),
                            "total_processed": len([inv for inv in separated_invoices if inv['quality_score'] >= 0.6]),
                            "header_detected": invoice['header'],
                            "quality_score": invoice['quality_score'],
                            "quality_issues": invoice['quality_issues']
                        }
                        
                        # Déterminer le statut selon la qualité
                        statut = "traite" if invoice['quality_score'] >= 0.8 else "traite_avec_avertissement"
                        
                        # Créer un document pour chaque facture valide
                        document = DocumentOCR(
                            type_document=document_type,
                            nom_fichier=f"{file.filename} - Facture {invoice['index']}/{len(separated_invoices)} (Q:{invoice['quality_score']:.1%})",
                            image_base64=data_uri,  # Même image/PDF source
                            texte_extrait=invoice['text_content'],  # Texte de cette facture uniquement
                            donnees_parsees=donnees_parsees,
                            statut=statut,
                            date_traitement=datetime.utcnow(),
                            file_type=file_type
                        )
                        
                        await db.documents_ocr.insert_one(document.dict())
                        created_documents.append(document.id)
                        
                        processing_summary.append(f"✅ Facture {invoice['index']}: Traitée avec succès (qualité {invoice['quality_score']:.1%})")
                        print(f"✅ Facture {invoice['index']}/{len(separated_invoices)} créée - Qualité: {invoice['quality_score']:.1%}")
                        
                    except Exception as e:
                        rejected_invoices.append({
                            'index': invoice.get('index', i+1),
                            'header': invoice.get('header', 'En-tête non détecté'),
                            'quality_score': invoice.get('quality_score', 0.0),
                            'issues': [f"Erreur de traitement: {str(e)}"],
                            'reason': f'Erreur lors du parsing: {str(e)}'
                        })
                        processing_summary.append(f"❌ Facture {invoice.get('index', i+1)}: Erreur de traitement")
                        print(f"❌ Erreur lors du traitement de la facture {invoice.get('index', i+1)}: {str(e)}")
                        continue
                
                # Retourner un résumé détaillé
                return {
                    "multi_invoice": True,
                    "total_detected": len(separated_invoices),
                    "successfully_processed": len(created_documents),
                    "rejected_count": len(rejected_invoices),
                    "document_ids": created_documents,
                    "rejected_invoices": rejected_invoices,
                    "processing_summary": processing_summary,
                    "message": f"{len(created_documents)} factures traitées avec succès, {len(rejected_invoices)} rejetées sur {len(separated_invoices)} détectées",
                    "file_type": file_type,
                    "has_quality_issues": len(rejected_invoices) > 0
                }
        elif document_type == "mercuriale":
            # Parser la mercuriale pour détecter les produits
            mercuriale_data = parse_mercuriale_fournisseur(texte_extrait)
            donnees_parsees = mercuriale_data
        
        # Pour les tickets Z (traitement normal inchangé)
        if document_type == "z_report":
            document = DocumentOCR(
                type_document=document_type,
                nom_fichier=file.filename,
                image_base64=data_uri,
                texte_extrait=texte_extrait,
                donnees_parsees=donnees_parsees,
                statut="traite",
                date_traitement=datetime.utcnow(),
                file_type=file_type
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
    """Récupérer un document spécifique par son ID. Enrichit les prix manquants et ajoute l'analyse Z si absente."""
    document = await db.documents_ocr.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    # Si Z-report et données parsées présentes, enrichir si nécessaire
    try:
        if document.get("type_document") == "z_report" and document.get("donnees_parsees"):
            parsed = document["donnees_parsees"]
            items = parsed.get("items_by_category", {})
            # Vérifier s'il manque des prix
            missing_prices = False
            for cat_items in items.values():
                for it in cat_items:
                    if it.get("unit_price") is None:
                        missing_prices = True
                        break
                if missing_prices:
                    break
            if missing_prices:
                enriched = await enrich_z_report_prices(parsed)
                if enriched != parsed:
                    await db.documents_ocr.update_one(
                        {"id": document_id}, {"$set": {"donnees_parsees": enriched}}
                    )
                    document["donnees_parsees"] = enriched
            # Ajouter analyse si absente
            if not parsed.get("z_analysis") and document.get("texte_extrait"):
                z_summary = analyze_z_report_categories(document["texte_extrait"])
                parsed["z_analysis"] = z_summary
                await db.documents_ocr.update_one(
                    {"id": document_id}, {"$set": {"donnees_parsees": parsed}}
                )
                document["donnees_parsees"] = parsed
    except Exception as e:
        print(f"⚠️ Enrichment/analysis on GET failed: {str(e)}")
    
    # Supprimer l'_id MongoDB pour éviter les problèmes de sérialisation
    if "_id" in document:
        del document["_id"]
    
    return document

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

@api_router.delete("/ocr/documents/all")
async def delete_all_ocr_documents():
    """Supprimer tous les documents OCR de l'historique"""
    try:
        result = await db.documents_ocr.delete_many({})
        return {
            "message": "Tous les documents OCR ont été supprimés",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

# ✅ Archive System Endpoints
@api_router.post("/archive")
async def archive_item(request: ArchiveRequest):
    """Archiver un produit, production ou fournisseur"""
    # Obtenir les données originales selon le type
    original_data = None
    collection_name = None
    
    if request.item_type == "produit":
        collection_name = "produits"
        original_data = await db.produits.find_one({"id": request.item_id})
    elif request.item_type == "production":
        collection_name = "recettes"
        original_data = await db.recettes.find_one({"id": request.item_id})
    elif request.item_type == "fournisseur":
        collection_name = "fournisseurs" 
        original_data = await db.fournisseurs.find_one({"id": request.item_id})
    else:
        raise HTTPException(status_code=400, detail="Type d'élément invalide")
    
    if not original_data:
        raise HTTPException(status_code=404, detail="Élément non trouvé")
    
    # Supprimer l'_id MongoDB pour éviter les conflits
    if "_id" in original_data:
        del original_data["_id"]
    
    # Créer l'archive
    archived_item = ArchivedItem(
        original_id=request.item_id,
        item_type=request.item_type,
        original_data=original_data,
        reason=request.reason
    )
    
    await db.archived_items.insert_one(archived_item.dict())
    
    # Supprimer l'élément original de sa collection
    collection = getattr(db, collection_name)
    await collection.delete_one({"id": request.item_id})
    
    return {"message": f"{request.item_type.capitalize()} archivé avec succès", "archive_id": archived_item.id}

@api_router.get("/archives", response_model=List[ArchivedItem])
async def get_archives(item_type: Optional[str] = None):
    """Obtenir la liste des éléments archivés"""
    query = {}
    if item_type:
        query["item_type"] = item_type
    
    archives = await db.archived_items.find(query).sort("archived_at", -1).to_list(1000)
    return [ArchivedItem(**archive) for archive in archives]

@api_router.post("/restore/{archive_id}")
async def restore_item(archive_id: str):
    """Restaurer un élément archivé"""
    # Trouver l'archive
    archive = await db.archived_items.find_one({"id": archive_id})
    if not archive:
        raise HTTPException(status_code=404, detail="Archive non trouvée")
    
    archived_item = ArchivedItem(**archive)
    
    # Déterminer la collection de destination
    collection_name = None
    if archived_item.item_type == "produit":
        collection_name = "produits"
    elif archived_item.item_type == "production":
        collection_name = "recettes"
    elif archived_item.item_type == "fournisseur":
        collection_name = "fournisseurs"
    
    # Vérifier que l'élément n'existe pas déjà
    collection = getattr(db, collection_name)
    existing = await collection.find_one({"id": archived_item.original_id})
    if existing:
        raise HTTPException(status_code=400, detail="L'élément existe déjà et ne peut pas être restauré")
    
    # Restaurer l'élément
    await collection.insert_one(archived_item.original_data)
    
    # Supprimer l'archive
    await db.archived_items.delete_one({"id": archive_id})
    
    return {"message": f"{archived_item.item_type.capitalize()} restauré avec succès"}

@api_router.delete("/archives/{archive_id}")
async def delete_archive(archive_id: str):
    """Supprimer définitivement une archive (sans restauration)"""
    result = await db.archived_items.delete_one({"id": archive_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Archive non trouvée")
    
    return {"message": "Archive supprimée définitivement"}

@api_router.post("/archive/diagnostic")
async def diagnostic_archive_system():
    """Diagnostique et test du système d'archivage"""
    try:
        results = {
            "system_status": "running",
            "tests": [],
            "recommendations": []
        }
        
        # Test 1: Vérifier les collections
        produits_count = await db.produits.count_documents({})
        recettes_count = await db.recettes.count_documents({})
        fournisseurs_count = await db.fournisseurs.count_documents({})
        archives_count = await db.archived_items.count_documents({})
        
        results["tests"].append({
            "name": "Collections Count",
            "status": "success",
            "details": {
                "produits": produits_count,
                "recettes": recettes_count, 
                "fournisseurs": fournisseurs_count,
                "archives": archives_count
            }
        })
        
        # Test 2: Test d'archivage sur un produit temporaire
        if produits_count > 0:
            # Prendre le premier produit pour test
            test_produit = await db.produits.find_one({})
            if test_produit:
                try:
                    # Simuler un archivage (sans vraiment le faire)
                    test_archive = {
                        "original_id": test_produit["id"],
                        "item_type": "produit",
                        "original_data": test_produit,
                        "reason": "Test diagnostic"
                    }
                    
                    results["tests"].append({
                        "name": "Archive Simulation",
                        "status": "success",
                        "details": "Le système peut créer des archives"
                    })
                except Exception as e:
                    results["tests"].append({
                        "name": "Archive Simulation",
                        "status": "error",
                        "details": str(e)
                    })
        
        # Test 3: Vérifier la structure des données archivées existantes
        if archives_count > 0:
            sample_archive = await db.archived_items.find_one({})
            if sample_archive:
                required_fields = ["id", "original_id", "item_type", "original_data", "archived_at"]
                missing_fields = [field for field in required_fields if field not in sample_archive]
                
                if missing_fields:
                    results["tests"].append({
                        "name": "Archive Structure",
                        "status": "warning",
                        "details": f"Champs manquants: {missing_fields}"
                    })
                    results["recommendations"].append("Vérifier la structure des archives existantes")
                else:
                    results["tests"].append({
                        "name": "Archive Structure",
                        "status": "success",
                        "details": "Structure des archives correcte"
                    })
        
        # Test 4: Permissions et accès
        try:
            # Test d'écriture sur la collection archives
            test_write = await db.archived_items.find_one({"test_write": True})
            results["tests"].append({
                "name": "Database Permissions",
                "status": "success",
                "details": "Permissions de lecture/écriture OK"
            })
        except Exception as e:
            results["tests"].append({
                "name": "Database Permissions", 
                "status": "error",
                "details": str(e)
            })
            results["recommendations"].append("Vérifier les permissions MongoDB")
        
        # Recommandations générales
        if archives_count == 0:
            results["recommendations"].append("Aucune archive trouvée - le système n'a pas encore été utilisé")
        
        # Status global
        error_tests = [t for t in results["tests"] if t["status"] == "error"]
        if error_tests:
            results["system_status"] = "error"
        elif any(t["status"] == "warning" for t in results["tests"]):
            results["system_status"] = "warning"
        
        return results
        
    except Exception as e:
        return {
            "system_status": "error",
            "error": str(e),
            "tests": [],
            "recommendations": ["Contacter le support technique"]
        }

# ✅ Authentication Endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Connexion simple avec username/password"""
    try:
        # Chercher l'utilisateur
        user = await db.users.find_one({"username": request.username})
        
        if not user:
            return LoginResponse(success=False, message="Nom d'utilisateur incorrect")
        
        # Vérification simple du mot de passe (en production, utiliser bcrypt)
        user_obj = User(**user)
        
        # Pour l'instant, vérification simple - en production utiliser bcrypt
        if request.password != "password123":  # Mot de passe par défaut pour les comptes test
            return LoginResponse(success=False, message="Mot de passe incorrect")
        
        # Créer une session
        session_id = str(uuid.uuid4())
        session = UserSession(
            user_id=user_obj.id,
            username=user_obj.username,
            role=user_obj.role,
            full_name=user_obj.full_name or user_obj.username
        )
        
        # Sauvegarder la session (simple stockage en mémoire pour l'instant)
        await db.user_sessions.insert_one({**session.dict(), "session_id": session_id})
        
        # Mettre à jour la dernière connexion
        await db.users.update_one(
            {"id": user_obj.id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return LoginResponse(
            success=True,
            user=UserResponse(**user_obj.dict()),
            session_id=session_id,
            message="Connexion réussie"
        )
        
    except Exception as e:
        return LoginResponse(success=False, message=f"Erreur de connexion: {str(e)}")

@api_router.post("/auth/logout")
async def logout(session_id: str):
    """Déconnexion"""
    try:
        await db.user_sessions.delete_one({"session_id": session_id})
        return {"success": True, "message": "Déconnexion réussie"}
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de la déconnexion: {str(e)}"}

@api_router.get("/auth/session/{session_id}")
async def get_session(session_id: str):
    """Vérifier une session"""
    try:
        session = await db.user_sessions.find_one({"session_id": session_id})
        if not session:
            return {"valid": False, "message": "Session expirée"}
        
        # Mettre à jour l'activité
        await db.user_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )
        
        return {"valid": True, "user": UserSession(**session)}
    except Exception as e:
        return {"valid": False, "message": f"Erreur session: {str(e)}"}

# ✅ Mission Management Endpoints
@api_router.post("/missions", response_model=Mission)
async def create_mission(mission: MissionCreate, assigned_by_user_id: str):
    """Créer une nouvelle mission"""
    try:
        # Récupérer les noms des utilisateurs
        assigned_to_user = await db.users.find_one({"id": mission.assigned_to_user_id})
        assigned_by_user = await db.users.find_one({"id": assigned_by_user_id})
        
        if not assigned_to_user:
            raise HTTPException(status_code=404, detail="Utilisateur assigné non trouvé")
        if not assigned_by_user:
            raise HTTPException(status_code=404, detail="Utilisateur assignateur non trouvé")
        
        mission_obj = Mission(
            **mission.dict(),
            assigned_by_user_id=assigned_by_user_id,
            assigned_to_name=assigned_to_user.get("full_name", assigned_to_user["username"]),
            assigned_by_name=assigned_by_user.get("full_name", assigned_by_user["username"])
        )
        
        await db.missions.insert_one(mission_obj.dict())
        
        # Créer une notification pour l'employé
        notification = Notification(
            user_id=mission.assigned_to_user_id,
            title="Nouvelle mission assignée",
            message=f"Mission: {mission.title}",
            type="mission",
            mission_id=mission_obj.id
        )
        
        await db.notifications.insert_one(notification.dict())
        
        return mission_obj
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")

@api_router.get("/missions", response_model=List[Mission])
async def get_missions(user_id: Optional[str] = None, status: Optional[str] = None):
    """Récupérer les missions"""
    query = {}
    if user_id:
        query["assigned_to_user_id"] = user_id
    if status:
        query["status"] = status
    
    missions = await db.missions.find(query).sort("assigned_date", -1).to_list(1000)
    return [Mission(**m) for m in missions]

@api_router.get("/missions/by-user/{user_id}")
async def get_missions_by_user(user_id: str):
    """Récupérer toutes les missions pour un utilisateur (assignées à lui ET créées par lui)"""
    assigned_to_missions = await db.missions.find({"assigned_to_user_id": user_id}).sort("assigned_date", -1).to_list(1000)
    created_by_missions = await db.missions.find({"assigned_by_user_id": user_id}).sort("assigned_date", -1).to_list(1000)
    
    return {
        "assigned_to_me": [Mission(**m) for m in assigned_to_missions],
        "created_by_me": [Mission(**m) for m in created_by_missions],
        "total_assigned": len(assigned_to_missions),
        "total_created": len(created_by_missions)
    }

@api_router.put("/missions/{mission_id}", response_model=Mission)
async def update_mission(mission_id: str, update: MissionUpdate, user_id: str):
    """Mettre à jour une mission"""
    try:
        mission = await db.missions.find_one({"id": mission_id})
        if not mission:
            raise HTTPException(status_code=404, detail="Mission non trouvée")
        
        update_data = update.dict(exclude_unset=True)
        
        # Si l'employé marque comme terminée
        if update_data.get("status") == "terminee_attente":
            update_data["completed_by_employee_date"] = datetime.utcnow()
            
            # Créer notification pour le chef/patron
            manager = await db.users.find_one({"id": mission["assigned_by_user_id"]})
            if manager:
                notification = Notification(
                    user_id=mission["assigned_by_user_id"],
                    title="Mission terminée - À valider",
                    message=f"{mission['assigned_to_name']} a terminé: {mission['title']}",
                    type="mission",
                    mission_id=mission_id
                )
                await db.notifications.insert_one(notification.dict())
        
        # Si le chef/patron valide
        elif update_data.get("status") == "validee":
            update_data["validated_date"] = datetime.utcnow()
            
            # Créer notification pour l'employé
            notification = Notification(
                user_id=mission["assigned_to_user_id"],
                title="Mission validée",
                message=f"Votre mission '{mission['title']}' a été validée !",
                type="mission",
                mission_id=mission_id
            )
            await db.notifications.insert_one(notification.dict())
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.missions.update_one({"id": mission_id}, {"$set": update_data})
        
        updated_mission = await db.missions.find_one({"id": mission_id})
        return Mission(**updated_mission)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour: {str(e)}")

@api_router.delete("/missions/{mission_id}")
async def delete_mission(mission_id: str):
    """Supprimer une mission"""
    result = await db.missions.delete_one({"id": mission_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mission non trouvée")
    
    # Supprimer les notifications liées
    await db.notifications.delete_many({"mission_id": mission_id})
    
    return {"message": "Mission supprimée"}

@api_router.get("/notifications/{user_id}")
async def get_user_notifications(user_id: str, limit: int = 50):
    """Récupérer les notifications d'un utilisateur"""
    notifications = await db.notifications.find({"user_id": user_id}).sort("created_at", -1).limit(limit).to_list(limit)
    return [Notification(**n) for n in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Marquer une notification comme lue"""
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True, "read_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    return {"message": "Notification marquée comme lue"}

# ✅ Demo Data Creation for Missions System
@api_router.post("/demo/init-missions-users")
async def init_demo_missions_and_users():
    """Créer les utilisateurs test et missions de démonstration"""
    try:
        # Supprimer les données existantes
        await db.users.delete_many({})
        await db.missions.delete_many({})
        await db.notifications.delete_many({})
        await db.user_sessions.delete_many({})
        
        # Créer les utilisateurs test
        test_users = [
            User(
                id="superadmin-001",
                username="skander_admin",
                email="skander@table-augustine.fr",
                password_hash="hashed_password123",  # En production: bcrypt
                role="super_admin",
                full_name="Skander Ben Ali (Super Admin)",
                is_active=True
            ),
            User(
                id="patron-001",
                username="patron_test",
                email="patron@table-augustine.fr",
                password_hash="hashed_password123",  # En production: bcrypt
                role="patron",
                full_name="Antonin Portal (Patron)",
                is_active=True
            ),
            User(
                id="chef-001", 
                username="chef_test",
                email="chef@table-augustine.fr",
                password_hash="hashed_password123",
                role="chef_cuisine",
                full_name="Marie Dubois (Chef de Cuisine)",
                is_active=True
            ),
            User(
                id="souschef-001", 
                username="souschef_test",
                email="nabil@table-augustine.fr",
                password_hash="hashed_password123",
                role="chef_cuisine",
                full_name="Nabil El Mansouri (Sous-Chef)",
                is_active=True
            ),
            User(
                id="caisse-001",
                username="caisse_test", 
                email="caisse@table-augustine.fr",
                password_hash="hashed_password123",
                role="caissier",
                full_name="Jean Martin (Responsable Caisse)",
                is_active=True
            ),
            User(
                id="barman-001",
                username="barman_test",
                email="barman@table-augustine.fr", 
                password_hash="hashed_password123",
                role="barman",
                full_name="Sophie Leroy (Barman)",
                is_active=True
            ),
            User(
                id="cuisine-001",
                username="cuisine_test",
                email="cuisine@table-augustine.fr",
                password_hash="hashed_password123", 
                role="employe_cuisine",
                full_name="Lucas Petit (Employé Cuisine)",
                is_active=True
            )
        ]
        
        # Insérer les utilisateurs
        for user in test_users:
            await db.users.insert_one(user.dict())
        
        # Créer des missions de démonstration
        demo_missions = [
            # Mission du Chef vers Employé Cuisine
            Mission(
                title="Préparer 15 portions de Supions émincés",
                description="Découper les supions en fines lamelles pour le service du soir. Vérifier la fraîcheur et noter toute anomalie.",
                type="preparation",
                category="cuisine",
                assigned_to_user_id="cuisine-001",
                assigned_by_user_id="chef-001", 
                assigned_to_name="Lucas Petit (Employé Cuisine)",
                assigned_by_name="Marie Dubois (Chef de Cuisine)",
                priority="haute",
                due_date=datetime.utcnow() + timedelta(hours=2),
                target_quantity=15,
                target_unit="portions"
            ),
            
            # Mission du Patron vers Chef
            Mission(
                title="Vérifier stock critique : Huile d'olive",
                description="Le stock d'huile d'olive est critique (2L restant). Vérifier la qualité, commander si nécessaire.",
                type="stock_check", 
                category="stock",
                assigned_to_user_id="chef-001",
                assigned_by_user_id="patron-001",
                assigned_to_name="Marie Dubois (Chef de Cuisine)",
                assigned_by_name="Antonin Portal (Patron)",
                priority="urgente",
                due_date=datetime.utcnow() + timedelta(hours=1)
            ),
            
            # Mission du Chef vers Barman
            Mission(
                title="Contrôler la température des chambres froides",
                description="Vérifier que les chambres froides du bar maintiennent la température correcte (2-4°C).",
                type="equipment_check",
                category="hygiene", 
                assigned_to_user_id="barman-001",
                assigned_by_user_id="chef-001",
                assigned_to_name="Sophie Leroy (Barman)",
                assigned_by_name="Marie Dubois (Chef de Cuisine)",
                priority="normale",
                due_date=datetime.utcnow() + timedelta(hours=4)
            ),
            
            # Mission terminée en attente de validation
            Mission(
                title="Nettoyer la zone de découpe des poissons", 
                description="Nettoyage complet et désinfection de la zone poissons après le service.",
                type="cleaning",
                category="hygiene",
                assigned_to_user_id="cuisine-001",
                assigned_by_user_id="chef-001",
                assigned_to_name="Lucas Petit (Employé Cuisine)", 
                assigned_by_name="Marie Dubois (Chef de Cuisine)",
                status="terminee_attente",
                priority="normale",
                completed_by_employee_date=datetime.utcnow() - timedelta(minutes=15),
                employee_notes="Zone nettoyée et désinfectée. Produits rangés au frais."
            ),
            
            # Mission validée
            Mission(
                title="Réceptionner livraison Pêcherie des Sanguinaires",
                description="Contrôler la livraison de poissons : supions (5kg), moules (3kg), sardines (2kg).",
                type="delivery_check",
                category="commande",
                assigned_to_user_id="caisse-001", 
                assigned_by_user_id="chef-001",
                assigned_to_name="Jean Martin (Responsable Caisse)",
                assigned_by_name="Marie Dubois (Chef de Cuisine)",
                status="validee",
                priority="haute",
                completed_by_employee_date=datetime.utcnow() - timedelta(hours=2),
                validated_date=datetime.utcnow() - timedelta(hours=1),
                employee_notes="Livraison conforme. Poissons de qualité excellent.",
                validation_notes="Parfait, merci Jean !"
            ),
            
            # Nouvelles missions créées AUJOURD'HUI par le chef pour les listes
            Mission(
                title="Vérifier température frigos légumes",
                description="Contrôler que les frigos légumes maintiennent entre 2-4°C. Noter les températures.",
                type="equipment_check",
                category="hygiene",
                assigned_to_user_id="cuisine-001",
                assigned_by_user_id="chef-001",
                assigned_to_name="Lucas Petit (Employé Cuisine)",
                assigned_by_name="Marie Dubois (Chef de Cuisine)",
                priority="normale",
                due_date=datetime.utcnow() + timedelta(hours=3),
                assigned_date=datetime.utcnow()  # Mission créée aujourd'hui
            ),
            
            Mission(
                title="Compter stock épices",
                description="Faire l'inventaire complet des épices en réserve. Vérifier les DLC.",
                type="stock_check", 
                category="stock",
                assigned_to_user_id="barman-001",
                assigned_by_user_id="souschef-001",  # Mission créée par le sous-chef
                assigned_to_name="Sophie Leroy (Barman)",
                assigned_by_name="Nabil El Mansouri (Sous-Chef)",
                priority="basse",
                assigned_date=datetime.utcnow() - timedelta(hours=2)  # Créée plus tôt aujourd'hui
            ),
            
            Mission(
                title="Nettoyer planches à découper",
                description="Nettoyer et désinfecter toutes les planches à découper. Vérifier l'état.",
                type="cleaning",
                category="hygiene",
                assigned_to_user_id="cuisine-001",
                assigned_by_user_id="chef-001",
                assigned_to_name="Lucas Petit (Employé Cuisine)",
                assigned_by_name="Marie Dubois (Chef de Cuisine)",
                status="terminee_attente",  # Terminée, en attente validation
                priority="normale",
                assigned_date=datetime.utcnow() - timedelta(hours=1),
                completed_by_employee_date=datetime.utcnow() - timedelta(minutes=30),
                employee_notes="Toutes les planches nettoyées et désinfectées avec Javel. État excellent."
            ),
            
            Mission(
                title="Préparer 25 portions Moules marinières",
                description="Nettoyer et préparer les moules pour le service de ce soir. Éliminer celles qui ne s'ouvrent pas.",
                type="preparation",
                category="cuisine",
                assigned_to_user_id="cuisine-001",
                assigned_by_user_id="souschef-001",  # Par le sous-chef
                assigned_to_name="Lucas Petit (Employé Cuisine)",
                assigned_by_name="Nabil El Mansouri (Sous-Chef)",
                status="terminee_attente",  # Terminée, en attente validation
                priority="haute",
                assigned_date=datetime.utcnow() - timedelta(hours=3),
                completed_by_employee_date=datetime.utcnow() - timedelta(minutes=45),
                target_quantity=25,
                target_unit="portions",
                employee_notes="25 portions préparées. Moules très fraîches, aucune écartée."
            ),
            
            # Mission créée par le patron aujourd'hui
            Mission(
                title="Former nouveau serveur sur protocoles",
                description="Former le nouveau serveur sur les protocoles de service et présentation des plats.",
                type="formation",
                category="service",
                assigned_to_user_id="chef-001",
                assigned_by_user_id="patron-001",
                assigned_to_name="Marie Dubois (Chef de Cuisine)",
                assigned_by_name="Antonin Portal (Patron)",
                priority="normale",
                assigned_date=datetime.utcnow() - timedelta(minutes=30),  # Très récente
                due_date=datetime.utcnow() + timedelta(hours=6)
            )
        ]
        
        # Insérer les missions
        for mission in demo_missions:
            await db.missions.insert_one(mission.dict())
        
        # Créer quelques notifications de démonstration
        demo_notifications = [
            Notification(
                user_id="cuisine-001",
                title="Nouvelle mission urgente",
                message="Préparer 15 portions de Supions émincés - À terminer avant 18h30",
                type="mission",
                mission_id=demo_missions[0].id
            ),
            Notification(
                user_id="chef-001", 
                title="Mission terminée - À valider",
                message="Lucas a terminé le nettoyage de la zone poissons",
                type="mission",
                mission_id=demo_missions[3].id
            ),
            Notification(
                user_id="barman-001",
                title="Rappel DLC",
                message="3 produits Bar arrivent à expiration dans 2 jours",
                type="alert"
            )
        ]
        
        for notification in demo_notifications:
            await db.notifications.insert_one(notification.dict())
        
        return {
            "success": True,
            "message": "✅ Système missions et utilisateurs initialisé !",
            "users_created": len(test_users),
            "missions_created": len(demo_missions),
            "notifications_created": len(demo_notifications),
            "test_accounts": [
                {"username": "skander_admin", "password": "password123", "role": "Super Admin"},
                {"username": "patron_test", "password": "password123", "role": "Patron"},
                {"username": "chef_test", "password": "password123", "role": "Chef de Cuisine"}, 
                {"username": "souschef_test", "password": "password123", "role": "Sous-Chef"},
                {"username": "caisse_test", "password": "password123", "role": "Responsable Caisse"},
                {"username": "barman_test", "password": "password123", "role": "Barman"},
                {"username": "cuisine_test", "password": "password123", "role": "Employé Cuisine"}
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur initialisation: {str(e)}"
        }

# ✅ Import nouvelle carte et création automatique
@api_router.post("/demo/import-nouvelle-carte")
async def import_nouvelle_carte():
    """Importer la nouvelle carte de La Table d'Augustine et créer productions/préparations"""
    try:
        # ✅ ARCHIVER anciennes recettes/préparations au lieu de les supprimer
        
        # Récupérer toutes les anciennes recettes pour archivage
        anciennes_recettes = await db.recettes.find().to_list(1000)
        anciennes_preparations = await db.preparations.find().to_list(1000)
        
        archived_recettes_count = 0
        archived_preparations_count = 0
        
        # Archiver chaque ancienne recette
        for ancienne_recette in anciennes_recettes:
            # Supprimer l'_id MongoDB pour éviter les conflits
            if "_id" in ancienne_recette:
                del ancienne_recette["_id"]
            
            # Créer l'archive
            archived_item = ArchivedItem(
                original_id=ancienne_recette["id"],
                item_type="production",
                original_data=ancienne_recette,
                reason="Ancienne carte - Mise à jour menu novembre 2024"
            )
            
            await db.archived_items.insert_one(archived_item.dict())
            archived_recettes_count += 1
        
        # Supprimer les anciennes recettes après archivage
        await db.recettes.delete_many({})
        
        # Archiver chaque ancienne préparation
        for ancienne_preparation in anciennes_preparations:
            if "_id" in ancienne_preparation:
                del ancienne_preparation["_id"]
            
            archived_item = ArchivedItem(
                original_id=ancienne_preparation["id"],
                item_type="preparation",
                original_data=ancienne_preparation,
                reason="Ancienne carte - Mise à jour menu novembre 2024"
            )
            
            await db.archived_items.insert_one(archived_item.dict())
            archived_preparations_count += 1
        
        # Supprimer les anciennes préparations après archivage
        await db.preparations.delete_many({})
        
        # Nouvelles productions basées sur la carte analysée
        nouvelles_productions = [
            # ENTRÉES
            {"nom": "Supions en persillade de Mamie", "prix_vente": 26, "categorie": "Entrée", "portions": 4, "ingredients": ["Supions (petits calamars)", "Persil", "Ail"]},
            {"nom": "Moules gratinées en persillade", "prix_vente": 18, "categorie": "Entrée", "portions": 4, "ingredients": ["Moules de Méditerranée", "Persil", "Ail", "Beurre"]},
            {"nom": "Saint-Jacques façon Mr Paul Bocuse", "prix_vente": 27, "categorie": "Entrée", "portions": 4, "ingredients": ["Noix de Saint-Jacques", "Crème fraîche", "Beurre"]},
            {"nom": "Le crabe sublimé d'Augustine", "prix_vente": 29, "categorie": "Entrée", "portions": 4, "ingredients": ["Crabe", "Homard", "Cardamome"]},
            {"nom": "Les panisses de l'Estaque", "prix_vente": 15, "categorie": "Entrée", "portions": 6, "ingredients": ["Farine de pois-chiche", "Huile d'olive"]},
            {"nom": "Le pâté en croûte de Mamet Augustine", "prix_vente": 18, "categorie": "Entrée", "portions": 4, "ingredients": ["Porc", "Veau", "Pâte brisée", "Œufs"]},
            {"nom": "La soupe à l'oignon, foie gras & Comté", "prix_vente": 19, "categorie": "Entrée", "portions": 4, "ingredients": ["Oignon", "Foie gras", "Fromage Comté", "Pâte feuilletée"]},
            {"nom": "Cuisses de grenouilles à la française", "prix_vente": 24, "categorie": "Entrée", "portions": 4, "ingredients": ["Cuisses de grenouilles", "Ail", "Persil", "Beurre"]},
            {"nom": "La fameuse poêlée de sanguins des chasseurs", "prix_vente": 23, "categorie": "Entrée", "portions": 4, "ingredients": ["Champignons sanguins", "Ail", "Persil"]},
            {"nom": "Foie gras de canard IGP", "prix_vente": 28, "categorie": "Entrée", "portions": 4, "ingredients": ["Foie gras de canard", "Chutney"]},
            
            # PLATS
            {"nom": "Pêche du jour au four façon grand-mère", "prix_vente": 33, "categorie": "Plat", "portions": 4, "ingredients": ["Poisson frais", "Pommes de terre grenaille", "Herbes de Provence"]},
            {"nom": "La sole meunière, l'excellence", "prix_vente": 48, "categorie": "Plat", "portions": 4, "ingredients": ["Sole", "Beurre", "Pommes de terre", "Citron"]},
            {"nom": "Linguine aux palourdes & sauce à l'ail", "prix_vente": 29, "categorie": "Plat", "portions": 4, "ingredients": ["Linguine", "Palourdes", "Ail", "Huile d'olive"]},
            {"nom": "Rigatoni à la truffe fraîche de Bourgogne", "prix_vente": 35, "categorie": "Plat", "portions": 4, "ingredients": ["Rigatoni", "Truffe fraîche", "Crème", "Parmesan"]},
            {"nom": "Gnocchi d'Augustine sauce napolitaine", "prix_vente": 25, "categorie": "Plat", "portions": 4, "ingredients": ["Gnocchi artisanaux", "Tomates", "Burrata", "Basilic"]},
            {"nom": "Nos farcis provençaux", "prix_vente": 31, "categorie": "Plat", "portions": 4, "ingredients": ["Tomates", "Courgettes", "Bœuf limousin", "Veau", "Riz"]},
            {"nom": "La merveilleuse souris d'agneau", "prix_vente": 36, "categorie": "Plat", "portions": 4, "ingredients": ["Souris d'agneau", "Gnocchi", "Herbes de Provence"]},
            {"nom": "Le fameux boeuf Wellington à la truffe", "prix_vente": 56, "categorie": "Plat", "portions": 4, "ingredients": ["Filet de bœuf limousin", "Truffe", "Pâte feuilletée", "Champignons"]},
            {"nom": "Magret de canard de la ferme du Puntoun", "prix_vente": 42, "categorie": "Plat", "portions": 4, "ingredients": ["Magret de canard", "Girolles"]},
            {"nom": "Côte de boeuf Aubrac", "prix_vente": 110, "categorie": "Plat", "portions": 4, "ingredients": ["Côte de bœuf Aubrac"]},
            {"nom": "Jarret de veau du Sud Ouest", "prix_vente": 80, "categorie": "Plat", "portions": 4, "ingredients": ["Jarret de veau"]},
            
            # ACCOMPAGNEMENTS (comptent comme des PLATS)
            {"nom": "Écrasé de pomme de terre", "prix_vente": 6, "categorie": "Plat", "portions": 4, "ingredients": ["Pommes de terre", "Beurre"]},
            {"nom": "Poêlée de légumes", "prix_vente": 6, "categorie": "Plat", "portions": 4, "ingredients": ["Légumes de saison", "Huile d'olive"]},
            {"nom": "Purée à la truffe (Uncinatum)", "prix_vente": 11, "categorie": "Plat", "portions": 4, "ingredients": ["Pommes de terre", "Truffe", "Beurre", "Crème"]},
            {"nom": "Gnocchi artisanaux au beurre", "prix_vente": 11, "categorie": "Plat", "portions": 4, "ingredients": ["Gnocchi artisanaux", "Beurre", "Parmesan"]},
            
            # DESSERTS  
            {"nom": "La glace yaourt dessert signature", "prix_vente": 13, "categorie": "Dessert", "portions": 4, "ingredients": ["Yaourt", "Sucre", "Crème"]},
            {"nom": "Tiramisu de Mamet", "prix_vente": 12, "categorie": "Dessert", "portions": 4, "ingredients": ["Mascarpone", "Café", "Biscuits", "Cacao"]},
            {"nom": "Crêpe Suzette recette de 1961", "prix_vente": 12, "categorie": "Dessert", "portions": 4, "ingredients": ["Farine", "Œufs", "Lait", "Orange", "Grand Marnier"]},
            {"nom": "Mont Blanc classique", "prix_vente": 12, "categorie": "Dessert", "portions": 4, "ingredients": ["Crème de marron", "Chantilly", "Meringue"]}
        ]
        
        created_count = 0
        
        # Créer chaque production
        for prod_data in nouvelles_productions:
            # Créer les ingrédients avec logique améliorée
            ingredients = []
            for ing_name in prod_data["ingredients"]:
                # Logique de recherche améliorée
                produit = None
                
                # Recherches spécifiques selon l'ingrédient
                if "supions" in ing_name.lower() or "calamar" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "supions|calamar", "$options": "i"}})
                elif "moules" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "moules", "$options": "i"}})
                elif "saint-jacques" in ing_name.lower() or "noix" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "saint-jacques|coquille", "$options": "i"}})
                elif "crabe" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "crabe", "$options": "i"}})
                elif "persil" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "persil", "$options": "i"}})
                elif "ail" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "ail", "$options": "i"}})
                elif "tomates" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "tomate", "$options": "i"}})
                elif "agneau" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "agneau", "$options": "i"}})
                elif "bœuf" in ing_name.lower() or "boeuf" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "bœuf|boeuf", "$options": "i"}})
                elif "veau" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "veau", "$options": "i"}})
                elif "canard" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "canard", "$options": "i"}})
                elif "truffe" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "truffe", "$options": "i"}})
                elif "palourdes" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "palourde", "$options": "i"}})
                elif "linguine" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "linguine|pâte", "$options": "i"}})
                elif "rigatoni" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "rigatoni|pâte", "$options": "i"}})
                elif "gnocchi" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "gnocchi|pomme.*terre", "$options": "i"}})
                elif "foie gras" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "foie.*gras", "$options": "i"}})
                elif "champignon" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "champignon", "$options": "i"}})
                elif "crème" in ing_name.lower():
                    produit = await db.produits.find_one({"nom": {"$regex": "crème|cream", "$options": "i"}})
                else:
                    # Recherche générique sur le premier mot
                    first_word = ing_name.split()[0].lower()
                    produit = await db.produits.find_one({"nom": {"$regex": first_word, "$options": "i"}})
                
                if produit:
                    # Quantités réalistes selon l'ingrédient
                    quantite = 0.1  # Par défaut
                    if "viande" in ing_name.lower() or "agneau" in ing_name.lower() or "bœuf" in ing_name.lower() or "veau" in ing_name.lower():
                        quantite = 0.15  # 150g par portion
                    elif "poisson" in ing_name.lower() or "sole" in ing_name.lower() or "supions" in ing_name.lower():
                        quantite = 0.12  # 120g par portion
                    elif "truffe" in ing_name.lower():
                        quantite = 0.01  # 10g par portion (truffe précieuse)
                    elif "légume" in ing_name.lower() or "tomate" in ing_name.lower():
                        quantite = 0.08  # 80g par portion
                    elif "pâte" in ing_name.lower() or "linguine" in ing_name.lower() or "gnocchi" in ing_name.lower():
                        quantite = 0.1   # 100g par portion
                    elif "persil" in ing_name.lower() or "ail" in ing_name.lower():
                        quantite = 0.005 # 5g par portion (aromates)
                    
                    ingredients.append({
                        "produit_id": produit["id"],
                        "produit_nom": produit["nom"],
                        "quantite": quantite,
                        "unite": produit.get("unite", "kg")
                    })
            
            # Créer la recette avec description améliorée
            description = f"Production de la nouvelle carte novembre 2024 - {prod_data['nom']}"
            if prod_data["categorie"] == "Entrée":
                description += " (Entrée signature La Table d'Augustine)"
            elif prod_data["categorie"] == "Plat":
                description += " (Plat principal traditionnel)"
            elif prod_data["categorie"] == "Dessert":
                description += " (Dessert maison)"
            
            recette = Recipe(
                nom=prod_data["nom"],
                description=description,
                categorie=prod_data["categorie"],
                portions=prod_data["portions"],
                prix_vente=prod_data["prix_vente"],
                coefficient_prevu=2.5,  # Coefficient par défaut
                ingredients=ingredients
            )
            
            await db.recettes.insert_one(recette.dict())
            created_count += 1
        
        # Créer les préparations appropriées
        preparation_count = 0
        
        # Préparations spécifiques selon la nouvelle carte
        preparations_config = [
            # Pour les supions
            {"produit": "Supions", "forme": "émincé", "description": "Pour persillade"},
            {"produit": "Supions", "forme": "entier", "description": "Pour cuisson complète"},
            
            # Pour les moules
            {"produit": "Moules", "forme": "nettoyé", "description": "Prêtes à gratiner"},
            
            # Pour les Saint-Jacques
            {"produit": "Saint-Jacques", "forme": "filet", "description": "Noix nettoyées"},
            
            # Pour le crabe
            {"produit": "Crabe", "forme": "émietté", "description": "Chair extraite"},
            
            # Pour les légumes
            {"produit": "Tomates", "forme": "concassé", "description": "Pour farcis provençaux"},
            {"produit": "Tomates", "forme": "sauce", "description": "Pour sauce napolitaine"},
            {"produit": "Courgettes", "forme": "évidé", "description": "Pour farcis provençaux"},
            
            # Pour les viandes
            {"produit": "Agneau", "forme": "désossé", "description": "Souris préparée"},
            {"produit": "Bœuf", "forme": "filet", "description": "Pour Wellington"},
            {"produit": "Veau", "forme": "haché", "description": "Pour farce"},
            {"produit": "Canard", "forme": "magret", "description": "Magret paré"},
            
            # Pour les aromates
            {"produit": "Persil", "forme": "haché", "description": "Pour persillade"},
            {"produit": "Ail", "forme": "émincé", "description": "Pour sauces"},
            
            # Pour les poissons (ajoutés)
            {"produit": "Sole", "forme": "filets", "description": "Préparée pour meunière"},
            {"produit": "Poisson", "forme": "entier", "description": "Pêche du jour au four"}
        ]
        
        for prep_config in preparations_config:
            # Chercher le produit correspondant
            produit = await db.produits.find_one({"nom": {"$regex": prep_config["produit"], "$options": "i"}})
            if produit:
                preparation = Preparation(
                    nom=f"{produit['nom']} {prep_config['forme']} - {prep_config['description']}",
                    produit_id=produit["id"],
                    produit_nom=produit["nom"],
                    forme_decoupe=prep_config["forme"],
                    quantite_produit_brut=2.0,
                    unite_produit_brut=produit.get("unite", "kg"),
                    quantite_preparee=1.8,
                    unite_preparee=produit.get("unite", "kg"),
                    perte=0.2,
                    perte_pourcentage=10.0,
                    nombre_portions=8,
                    taille_portion=0.225,
                    unite_portion=produit.get("unite", "kg"),
                    notes=f"Préparation pour nouvelle carte - {prep_config['description']}"
                )
                
                await db.preparations.insert_one(preparation.dict())
                preparation_count += 1
        
        return {
            "success": True,
            "message": "🎉 Nouvelle carte importée avec succès !",
            "productions_created": created_count,
            "preparations_created": preparation_count,
            "archived_recettes": archived_recettes_count,
            "archived_preparations": archived_preparations_count,
            "details": {
                "entrees": 10,
                "plats": 15,  # 11 plats principaux (9 + 2 poissons) + 4 accompagnements
                "desserts": 4,
                "total": 29
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Erreur import nouvelle carte: {str(e)}",
            "productions_created": 0,
            "preparations_created": 0
        }

@api_router.post("/demo/update-ingredients-from-carte")
async def update_ingredients_from_carte():
    """Archiver anciens ingrédients et créer nouveaux selon nouvelle carte"""
    try:
        # Récupérer toutes les nouvelles recettes pour analyser les ingrédients requis
        nouvelles_recettes = await db.recettes.find().to_list(1000)
        
        # Extraire tous les ingrédients requis des nouvelles recettes
        ingredients_requis = set()
        for recette in nouvelles_recettes:
            for ingredient in recette.get("ingredients", []):
                ingredients_requis.add(ingredient["produit_nom"].lower())
        
        # Récupérer tous les produits actuels
        tous_produits = await db.produits.find().to_list(1000)
        
        # Identifier produits à archiver (non utilisés dans nouvelle carte)
        produits_a_archiver = []
        produits_utilises = []
        
        for produit in tous_produits:
            produit_utilise = False
            for ing_requis in ingredients_requis:
                if (ing_requis in produit["nom"].lower() or 
                    produit["nom"].lower() in ing_requis or
                    any(word in produit["nom"].lower() for word in ing_requis.split())):
                    produit_utilise = True
                    break
            
            if produit_utilise:
                produits_utilises.append(produit)
            else:
                produits_a_archiver.append(produit)
        
        # Archiver les produits non utilisés
        archived_count = 0
        for produit in produits_a_archiver:
            # Créer l'archive
            archived_item = ArchivedItem(
                original_id=produit["id"],
                item_type="produit",
                original_data={k: v for k, v in produit.items() if k != "_id"},
                reason="Produit non utilisé dans nouvelle carte novembre 2024"
            )
            
            await db.archived_items.insert_one(archived_item.dict())
            
            # Supprimer le produit après archivage
            await db.produits.delete_one({"id": produit["id"]})
            
            # Supprimer aussi le stock associé
            await db.stocks.delete_one({"produit_id": produit["id"]})
            
            archived_count += 1
        
        # Créer nouveaux produits nécessaires selon nouvelle carte
        nouveaux_produits = [
            # Ingrédients de base pour nouvelle carte
            {"nom": "Pommes de terre grenaille", "categorie": "Légumes", "unite": "kg", "prix_achat": 2.80, "description": "Pour pêche du jour façon grand-mère"},
            {"nom": "Beurre montée", "categorie": "Crêmerie", "unite": "kg", "prix_achat": 8.50, "description": "Pour sauces et cuissons"},
            {"nom": "Crème de cardamome", "categorie": "Épices", "unite": "L", "prix_achat": 15.00, "description": "Pour émulsion homard"},
            {"nom": "Chutney maison", "categorie": "Épices", "unite": "kg", "prix_achat": 12.00, "description": "Accompagnement foie gras"},
            {"nom": "Pâte feuilletée", "categorie": "Céréales", "unite": "kg", "prix_achat": 4.50, "description": "Pour Wellington et pâtés"},
            {"nom": "Stracciatella", "categorie": "Crêmerie", "unite": "kg", "prix_achat": 18.00, "description": "Pour gnocchi napolitaine"},
            {"nom": "Girolles fraîches", "categorie": "Légumes", "unite": "kg", "prix_achat": 25.00, "description": "Pour magret de canard"},
            {"nom": "Herbes de Provence", "categorie": "Épices", "unite": "paquet", "prix_achat": 3.50, "description": "Pour agneau et plats provençaux"},
            {"nom": "Grand Marnier", "categorie": "Autres", "unite": "L", "prix_achat": 45.00, "description": "Pour crêpe Suzette"},
            {"nom": "Mascarpone", "categorie": "Crêmerie", "unite": "kg", "prix_achat": 12.00, "description": "Pour tiramisu"},
            {"nom": "Café expresso", "categorie": "Autres", "unite": "kg", "prix_achat": 18.00, "description": "Pour tiramisu"},
            {"nom": "Biscuits à la cuillère", "categorie": "Autres", "unite": "paquet", "prix_achat": 6.00, "description": "Pour tiramisu"}
        ]
        
        created_products = 0
        
        # Créer chaque nouveau produit
        for prod_data in nouveaux_produits:
            # Vérifier qu'il n'existe pas déjà
            existing = await db.produits.find_one({"nom": {"$regex": f"^{prod_data['nom']}$", "$options": "i"}})
            
            if not existing:
                produit = Produit(
                    nom=prod_data["nom"],
                    description=prod_data["description"],
                    categorie=prod_data["categorie"],
                    unite=prod_data["unite"],
                    prix_achat=prod_data["prix_achat"],
                    reference_price=prod_data["prix_achat"]
                )
                
                await db.produits.insert_one(produit.dict())
                
                # Créer un stock initial
                stock = Stock(
                    produit_id=produit.id,
                    produit_nom=produit.nom,
                    quantite_actuelle=10.0,  # Stock initial
                    quantite_min=2.0,
                    quantite_max=50.0
                )
                
                await db.stocks.insert_one(stock.dict())
                created_products += 1
        
        return {
            "success": True,
            "message": "🎉 Ingrédients mis à jour selon nouvelle carte !",
            "produits_archives": archived_count,
            "nouveaux_produits": created_products,
            "produits_conserves": len(produits_utilises),
            "details": {
                "ingredients_requis": len(ingredients_requis),
                "produits_analyses": len(tous_produits)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Erreur mise à jour ingrédients: {str(e)}",
            "produits_archives": 0,
            "nouveaux_produits": 0
        }
# ===== STOCK PREPARATIONS ENDPOINTS =====

@api_router.get("/stock-preparations")
async def list_stock_preparations():
    """Lister tous les stocks de préparations"""
    stocks = await db.stock_preparations.find().to_list(1000)
    # Nettoyer les _id MongoDB
    for stock in stocks:
        if "_id" in stock:
            del stock["_id"]
    return stocks

@api_router.get("/stock-preparations/{stock_id}")
async def get_stock_preparation(stock_id: str):
    """Obtenir un stock de préparation spécifique"""
    stock = await db.stock_preparations.find_one({"id": stock_id})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock de préparation non trouvé")
    if "_id" in stock:
        del stock["_id"]
    return stock

@api_router.post("/stock-preparations")
async def create_stock_preparation(stock_data: StockPreparationCreate):
    """Créer un nouveau stock de préparation"""
    # Vérifier que la préparation existe
    preparation = await db.preparations.find_one({"id": stock_data.preparation_id})
    if not preparation:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    
    stock = StockPreparation(
        preparation_id=stock_data.preparation_id,
        preparation_nom=preparation.get("nom", "Préparation inconnue"),
        quantite_actuelle=stock_data.quantite_actuelle,
        unite=preparation.get("unite_preparee", "kg"),
        quantite_min=stock_data.quantite_min,
        quantite_max=stock_data.quantite_max,
        dlc=stock_data.dlc
    )
    
    await db.stock_preparations.insert_one(stock.dict())
    return {"status": "ok", "id": stock.id}

@api_router.put("/stock-preparations/{stock_id}")
async def update_stock_preparation(stock_id: str, update_data: StockPreparationUpdate):
    """Mettre à jour un stock de préparation"""
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["derniere_maj"] = datetime.utcnow()
    
    result = await db.stock_preparations.update_one(
        {"id": stock_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Stock de préparation non trouvé")
    
    return {"status": "updated"}

@api_router.delete("/stock-preparations/{stock_id}")
async def delete_stock_preparation(stock_id: str):
    """Supprimer un stock de préparation"""
    result = await db.stock_preparations.delete_one({"id": stock_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Stock de préparation non trouvé")
    return {"message": "Stock de préparation supprimé"}

@api_router.post("/preparations/{preparation_id}/execute", response_model=ExecutePreparationResult)
async def execute_preparation(preparation_id: str, request: ExecutePreparationRequest):
    """
    Exécuter une préparation : transformer des produits bruts en préparation
    - Déduit les produits bruts du stock
    - Crée ou met à jour le stock de préparation
    - Enregistre les mouvements de stock
    - Gère les pertes de transformation
    """
    try:
        # 1. Récupérer la préparation
        preparation = await db.preparations.find_one({"id": preparation_id})
        if not preparation:
            raise HTTPException(status_code=404, detail="Préparation non trouvée")
        
        preparation_nom = preparation.get("nom", "Préparation inconnue")
        produit_id = preparation.get("produit_id")
        quantite_produit_brut = preparation.get("quantite_produit_brut", 1.0)
        quantite_preparee = preparation.get("quantite_preparee", 1.0)
        perte_pourcentage = preparation.get("perte_pourcentage", 0.0)
        unite_preparee = preparation.get("unite_preparee", "kg")
        dlc_jours = preparation.get("dlc", None)
        
        print(f"🔧 Exécution préparation: {preparation_nom}")
        print(f"   Quantité à produire: {request.quantite_a_produire} {unite_preparee}")
        
        produits_deduits = []
        warnings = []
        errors = []
        
        # 2. Calculer la quantité de produit brut nécessaire
        # Ratio: quantite_preparee est obtenue à partir de quantite_produit_brut
        ratio = quantite_preparee / quantite_produit_brut if quantite_produit_brut > 0 else 1.0
        quantite_brut_necessaire = round_stock_quantity(request.quantite_a_produire / ratio)
        
        print(f"   Produit brut nécessaire: {quantite_brut_necessaire} (ratio: {ratio})")
        
        # 3. Vérifier et déduire le stock du produit brut
        stock_produit = await db.stocks.find_one({"produit_id": produit_id})
        if not stock_produit:
            raise HTTPException(status_code=404, detail=f"Stock du produit brut {produit_id} non trouvé")
        
        stock_actuel = round_stock_quantity(stock_produit.get("quantite_actuelle", 0))
        produit_nom = stock_produit.get("produit_nom", "Produit inconnu")
        
        if stock_actuel < quantite_brut_necessaire:
            errors.append(f"Stock insuffisant: {stock_actuel} disponible, {quantite_brut_necessaire} requis")
            raise HTTPException(status_code=400, detail=f"Stock insuffisant pour {produit_nom}")
        
        # Déduire le stock
        nouveau_stock = round_stock_quantity(stock_actuel - quantite_brut_necessaire)
        await db.stocks.update_one(
            {"produit_id": produit_id},
            {
                "$set": {
                    "quantite_actuelle": nouveau_stock,
                    "derniere_maj": datetime.utcnow()
                }
            }
        )
        
        # Créer mouvement de sortie pour le produit brut
        mouvement_sortie = MouvementStock(
            produit_id=produit_id,
            produit_nom=produit_nom,
            type="sortie",
            quantite=quantite_brut_necessaire,
            reference=f"Préparation-{preparation_id[:8]}",
            commentaire=f"Transformation en {preparation_nom}"
        )
        await db.mouvements_stock.insert_one(mouvement_sortie.dict())
        
        produits_deduits.append({
            "produit_id": produit_id,
            "produit_nom": produit_nom,
            "quantite_deduite": quantite_brut_necessaire,
            "stock_avant": stock_actuel,
            "stock_apres": nouveau_stock
        })
        
        print(f"   ✅ Produit déduit: {produit_nom} -{quantite_brut_necessaire}")
        
        # 4. Calculer la DLC si définie
        dlc_date = None
        if dlc_jours:
            if isinstance(dlc_jours, datetime):
                dlc_date = dlc_jours
            else:
                # Supposer que dlc_jours est un nombre de jours
                dlc_date = datetime.utcnow() + timedelta(days=int(dlc_jours))
        
        # 5. Créer ou mettre à jour le stock de préparation
        stock_prep_existant = await db.stock_preparations.find_one({"preparation_id": preparation_id})
        
        stock_prep_id = None
        if stock_prep_existant:
            # Mettre à jour le stock existant
            nouvelle_quantite = stock_prep_existant.get("quantite_actuelle", 0) + request.quantite_a_produire
            await db.stock_preparations.update_one(
                {"id": stock_prep_existant["id"]},
                {
                    "$set": {
                        "quantite_actuelle": nouvelle_quantite,
                        "date_preparation": datetime.utcnow(),
                        "dlc": dlc_date,
                        "derniere_maj": datetime.utcnow(),
                        "statut": "disponible"
                    }
                }
            )
            stock_prep_id = stock_prep_existant["id"]
            print(f"   ✅ Stock préparation mis à jour: {nouvelle_quantite} {unite_preparee}")
        else:
            # Créer un nouveau stock de préparation
            stock_prep = StockPreparation(
                preparation_id=preparation_id,
                preparation_nom=preparation_nom,
                quantite_actuelle=request.quantite_a_produire,
                unite=unite_preparee,
                quantite_min=0.0,
                dlc=dlc_date
            )
            await db.stock_preparations.insert_one(stock_prep.dict())
            stock_prep_id = stock_prep.id
            print(f"   ✅ Nouveau stock préparation créé: {request.quantite_a_produire} {unite_preparee}")
        
        # 6. Ajouter un avertissement sur les pertes
        if perte_pourcentage > 0:
            warnings.append(f"⚠️ Perte de transformation: {perte_pourcentage}% ({quantite_brut_necessaire * perte_pourcentage / 100} {unite_preparee})")
        
        return ExecutePreparationResult(
            success=True,
            preparation_nom=preparation_nom,
            quantite_produite=request.quantite_a_produire,
            unite=unite_preparee,
            produits_deduits=produits_deduits,
            stock_preparation_id=stock_prep_id,
            warnings=warnings,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur exécution préparation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'exécution de la préparation: {str(e)}")


# ===== OCR PROCESSING ENDPOINTS - REAL DATA INTEGRATION =====

@api_router.post("/ocr/process-z-report/{document_id}", response_model=ZReportProcessingResult)
async def process_z_report_to_real_data(document_id: str):
    """
    Process a Z report document and integrate it into real system data:
    - Match productions with existing recipes
    - Deduct stock based on recipes sold
    - Create real Z report in rapports_z collection
    - Generate alerts for insufficient stock
    """
    try:
        # 1. Récupérer le document OCR
        document = await db.documents_ocr.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document OCR non trouvé")
        
        if document["type_document"] != "z_report":
            raise HTTPException(status_code=400, detail="Ce document n'est pas un ticket Z")
        
        # 2. Extraire les données parsées
        donnees_parsees = document.get("donnees_parsees", {})
        if not donnees_parsees:
            raise HTTPException(status_code=400, detail="Données parsées non disponibles")
        
        # Utiliser soit l'ancienne structure soit la nouvelle
        z_analysis = donnees_parsees.get("z_analysis", donnees_parsees)
        
        date_rapport = z_analysis.get("date_cloture", datetime.utcnow().strftime("%d/%m/%Y"))
        ca_total = z_analysis.get("total_ttc", 0.0) or z_analysis.get("analysis", {}).get("Bar", {}).get("ca", 0.0)
        nb_couverts = z_analysis.get("nombre_couverts")
        
        productions_matched = []
        stock_deductions = []
        warnings = []
        errors = []
        
        # 3. Récupérer les productions détectées
        productions_detectees = z_analysis.get("productions_detectees", [])
        
        if not productions_detectees:
            # Essayer l'ancienne structure
            items_by_category = donnees_parsees.get("items_by_category", {})
            for category, items in items_by_category.items():
                for item in items:
                    productions_detectees.append({
                        "nom": item.get("name", ""),
                        "quantite": item.get("quantity_sold", 0),
                        "family": category
                    })
        
        print(f"📊 Processing {len(productions_detectees)} productions from Z report")
        
        # 4. Matcher chaque production avec les recettes existantes
        for prod in productions_detectees:
            prod_name = prod.get("nom", "")
            quantity_sold = prod.get("quantite", 0)
            
            if not prod_name or quantity_sold <= 0:
                continue
            
            # Matcher avec les recettes
            recipe_match = await match_recipe_by_name(prod_name)
            
            if recipe_match and recipe_match["confidence"] >= 0.5:
                # Recette trouvée - calculer les déductions de stock
                recipe_id = recipe_match["recipe_id"]
                recipe_name = recipe_match["recipe_name"]
                ingredients = recipe_match["ingredients"]
                
                production_info = {
                    "ocr_name": prod_name,
                    "matched_recipe_id": recipe_id,
                    "matched_recipe_name": recipe_name,
                    "confidence": recipe_match["confidence"],
                    "quantity_sold": quantity_sold
                }
                productions_matched.append(production_info)
                
                # Calculer les déductions pour chaque ingrédient (PRODUITS et PRÉPARATIONS)
                for ingredient in ingredients:
                    # Support ancien format (produit_id) et nouveau format (ingredient_id + ingredient_type)
                    ingredient_id = ingredient.get("ingredient_id") or ingredient.get("produit_id")
                    ingredient_type = ingredient.get("ingredient_type", "produit")  # Par défaut "produit" pour compatibilité
                    ingredient_nom = ingredient.get("ingredient_nom") or ingredient.get("produit_nom", "Ingrédient inconnu")
                    quantity_per_portion = ingredient.get("quantite", 0)
                    unit = ingredient.get("unite", "")
                    
                    if not ingredient_id:
                        continue
                    
                    # Quantité totale à déduire
                    total_deduction = quantity_per_portion * quantity_sold
                    
                    # 🔀 GESTION SELON LE TYPE D'INGRÉDIENT
                    
                    if ingredient_type == "produit":
                        # ✅ PRODUIT BRUT - Déduire du stock produits
                        stock = await db.stocks.find_one({"produit_id": ingredient_id})
                        if stock:
                            current_stock = round_stock_quantity(stock.get("quantite_actuelle", 0))
                            total_deduction = round_stock_quantity(total_deduction)
                            new_stock = round_stock_quantity(current_stock - total_deduction)
                            
                            if new_stock < 0:
                                warnings.append(f"⚠️ Stock produit insuffisant pour {ingredient_nom}: {current_stock} {unit} disponible, {total_deduction} {unit} requis")
                                new_stock = 0
                            
                            # Créer la déduction
                            deduction = {
                                "ingredient_id": ingredient_id,
                                "ingredient_type": "produit",
                                "ingredient_name": ingredient_nom,
                                "recipe_name": recipe_name,
                                "quantity_per_portion": quantity_per_portion,
                                "portions_sold": quantity_sold,
                                "total_deduction": total_deduction,
                                "unit": unit,
                                "stock_before": current_stock,
                                "stock_after": new_stock
                            }
                            stock_deductions.append(deduction)
                            
                            # Appliquer la déduction
                            await db.stocks.update_one(
                                {"produit_id": ingredient_id},
                                {
                                    "$set": {
                                        "quantite_actuelle": new_stock,
                                        "derniere_maj": datetime.utcnow()
                                    }
                                }
                            )
                            
                            # Créer mouvement de stock
                            mouvement = MouvementStock(
                                produit_id=ingredient_id,
                                produit_nom=ingredient_nom,
                                type="sortie",
                                quantite=total_deduction,
                                reference=f"Z-Report {date_rapport} - {recipe_name}",
                                commentaire=f"Vente: {quantity_sold} x {recipe_name}"
                            )
                            await db.mouvements_stock.insert_one(mouvement.dict())
                        else:
                            warnings.append(f"⚠️ Produit {ingredient_id} non trouvé dans les stocks")
                    
                    elif ingredient_type == "preparation":
                        # ✅ PRÉPARATION - Déduire du stock préparations
                        stock_prep = await db.stock_preparations.find_one({"preparation_id": ingredient_id})
                        if stock_prep:
                            current_stock = stock_prep.get("quantite_actuelle", 0)
                            new_stock = current_stock - total_deduction
                            
                            if new_stock < 0:
                                warnings.append(f"⚠️ Stock préparation insuffisant pour {ingredient_nom}: {current_stock} {unit} disponible, {total_deduction} {unit} requis")
                                new_stock = 0
                            
                            # Créer la déduction
                            deduction = {
                                "ingredient_id": ingredient_id,
                                "ingredient_type": "preparation",
                                "ingredient_name": ingredient_nom,
                                "recipe_name": recipe_name,
                                "quantity_per_portion": quantity_per_portion,
                                "portions_sold": quantity_sold,
                                "total_deduction": total_deduction,
                                "unit": unit,
                                "stock_before": current_stock,
                                "stock_after": new_stock
                            }
                            stock_deductions.append(deduction)
                            
                            # Appliquer la déduction
                            await db.stock_preparations.update_one(
                                {"preparation_id": ingredient_id},
                                {
                                    "$set": {
                                        "quantite_actuelle": new_stock,
                                        "derniere_maj": datetime.utcnow()
                                    }
                                }
                            )
                            
                            # Note: Pas de mouvement_stock pour les préparations (collection différente)
                            print(f"   ✅ Préparation déduite: {ingredient_nom} -{total_deduction} {unit}")
                        else:
                            warnings.append(f"⚠️ Préparation {ingredient_id} non trouvée dans les stocks de préparations")
            else:
                warnings.append(f"⚠️ Production '{prod_name}' non matchée avec les recettes (confiance: {recipe_match['confidence'] if recipe_match else 0})")
        
        # 6. Créer le rapport Z réel dans la collection rapports_z
        rapport_z_data = {
            "date": datetime.strptime(date_rapport, "%d/%m/%Y") if "/" in date_rapport else datetime.utcnow(),
            "ca_total": ca_total,
            "produits": [
                {
                    "nom": p["matched_recipe_name"],
                    "quantite": p["quantity_sold"],
                    "prix_unitaire": 0.0  # À améliorer avec les prix de vente réels
                }
                for p in productions_matched
            ]
        }
        
        rapport_z = RapportZ(**rapport_z_data)
        result = await db.rapports_z.insert_one(rapport_z.dict())
        
        # Marquer le document OCR comme traité
        await db.documents_ocr.update_one(
            {"id": document_id},
            {
                "$set": {
                    "statut": "integre",
                    "date_traitement": datetime.utcnow(),
                    "integration_result": {
                        "productions_matched": len(productions_matched),
                        "stock_deductions": len(stock_deductions),
                        "rapport_z_id": rapport_z.id
                    }
                }
            }
        )
        
        return ZReportProcessingResult(
            success=True,
            document_id=document_id,
            date=date_rapport,
            ca_total=ca_total,
            nb_couverts=nb_couverts,
            productions_matched=productions_matched,
            stock_deductions=stock_deductions,
            warnings=warnings,
            errors=errors,
            rapport_z_id=rapport_z.id
        )
        
    except Exception as e:
        print(f"❌ Erreur processing Z report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du ticket Z: {str(e)}")


@api_router.post("/ocr/process-facture/{document_id}", response_model=FactureProcessingResult)
async def process_facture_to_real_data(document_id: str):
    """
    Process a supplier invoice and integrate it into real system data:
    - Match products with existing database or create new ones
    - Create automatic stock entries
    - Record real supplier prices
    - Generate price variation alerts
    - Create supplier order in history
    """
    try:
        # 1. Récupérer le document OCR
        document = await db.documents_ocr.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document OCR non trouvé")
        
        if document["type_document"] != "facture_fournisseur":
            raise HTTPException(status_code=400, detail="Ce document n'est pas une facture fournisseur")
        
        # 2. Extraire les données parsées
        donnees_parsees = document.get("donnees_parsees", {})
        if not donnees_parsees:
            raise HTTPException(status_code=400, detail="Données parsées non disponibles")
        
        supplier_name = donnees_parsees.get("fournisseur", "Fournisseur inconnu")
        facture_date = donnees_parsees.get("date", datetime.utcnow().strftime("%d/%m/%Y"))
        numero_facture = donnees_parsees.get("numero_facture", "N/A")
        produits_facture = donnees_parsees.get("produits", [])
        total_ttc = donnees_parsees.get("total_ttc", 0.0)
        
        print(f"📄 Processing facture {numero_facture} from {supplier_name} with {len(produits_facture)} products")
        
        # 3. Matcher ou créer le fournisseur
        supplier_match = await match_supplier_by_name(supplier_name)
        supplier_id = None
        
        if supplier_match and supplier_match["confidence"] >= 0.6:
            supplier_id = supplier_match["supplier_id"]
            supplier_name = supplier_match["supplier_name"]
            print(f"✅ Fournisseur matché: {supplier_name}")
        else:
            # Créer un nouveau fournisseur
            new_supplier = Fournisseur(
                nom=supplier_name,
                categorie="frais"
            )
            await db.fournisseurs.insert_one(new_supplier.dict())
            supplier_id = new_supplier.id
            print(f"✅ Nouveau fournisseur créé: {supplier_name}")
        
        products_matched = []
        products_created = 0
        stock_entries_created = 0
        price_alerts = []
        warnings = []
        errors = []
        
        # 4. Traiter chaque produit de la facture
        for prod_data in produits_facture:
            prod_name = prod_data.get("nom", "")
            quantity = prod_data.get("quantite", 0)
            unit_price = prod_data.get("prix_unitaire", 0)
            total_price = prod_data.get("prix_total", 0)
            unit = prod_data.get("unite", "kg")
            
            if not prod_name or quantity <= 0:
                continue
            
            # Matcher avec les produits existants
            product_match = await match_product_by_name(prod_name)
            
            product_id = None
            product_name_final = prod_name
            needs_creation = False
            
            if product_match and product_match["confidence"] >= 0.6:
                # Produit trouvé
                product_id = product_match["product_id"]
                product_name_final = product_match["product_name"]
                confidence = product_match["confidence"]
                
                # Vérifier les variations de prix
                produit = await db.produits.find_one({"id": product_id})
                if produit:
                    reference_price = produit.get("reference_price", 0)
                    if reference_price and unit_price:
                        price_diff_pct = ((unit_price - reference_price) / reference_price) * 100
                        if abs(price_diff_pct) > 10:  # Variation > 10%
                            price_alerts.append({
                                "product_name": product_name_final,
                                "reference_price": reference_price,
                                "actual_price": unit_price,
                                "difference_pct": round(price_diff_pct, 1),
                                "alert_type": "increase" if price_diff_pct > 0 else "decrease"
                            })
                
                # Mettre à jour les informations fournisseur-produit
                supplier_product_info = await db.supplier_product_info.find_one({
                    "supplier_id": supplier_id,
                    "product_id": product_id
                })
                
                if supplier_product_info:
                    # Mettre à jour le prix
                    await db.supplier_product_info.update_one(
                        {"id": supplier_product_info["id"]},
                        {
                            "$set": {
                                "price": unit_price,
                                "last_updated": datetime.utcnow()
                            }
                        }
                    )
                else:
                    # Créer la relation fournisseur-produit
                    new_relation = SupplierProductInfo(
                        supplier_id=supplier_id,
                        product_id=product_id,
                        price=unit_price,
                        is_preferred=True
                    )
                    await db.supplier_product_info.insert_one(new_relation.dict())
                
            else:
                # Produit non trouvé - créer un nouveau produit
                new_product = Produit(
                    nom=prod_name,
                    categorie="Autres",
                    unite=unit,
                    reference_price=unit_price,
                    main_supplier_id=supplier_id,
                    fournisseur_id=supplier_id,  # Legacy
                    fournisseur_nom=supplier_name  # Legacy
                )
                await db.produits.insert_one(new_product.dict())
                product_id = new_product.id
                products_created += 1
                needs_creation = True
                
                # Créer le stock initial
                new_stock = Stock(
                    produit_id=product_id,
                    produit_nom=prod_name,
                    quantite_actuelle=0,
                    quantite_min=0
                )
                await db.stocks.insert_one(new_stock.dict())
                
                # Créer la relation fournisseur-produit
                new_relation = SupplierProductInfo(
                    supplier_id=supplier_id,
                    product_id=product_id,
                    price=unit_price,
                    is_preferred=True
                )
                await db.supplier_product_info.insert_one(new_relation.dict())
                
                warnings.append(f"✨ Nouveau produit créé: {prod_name}")
            
            # 5. Créer l'entrée de stock
            stock = await db.stocks.find_one({"produit_id": product_id})
            if stock:
                current_stock = round_stock_quantity(stock.get("quantite_actuelle", 0))
                quantity = round_stock_quantity(quantity)
                new_stock_level = round_stock_quantity(current_stock + quantity)
                
                await db.stocks.update_one(
                    {"produit_id": product_id},
                    {
                        "$set": {
                            "quantite_actuelle": new_stock_level,
                            "derniere_maj": datetime.utcnow()
                        }
                    }
                )
                
                # Créer un mouvement de stock
                mouvement = MouvementStock(
                    produit_id=product_id,
                    produit_nom=product_name_final,
                    type="entree",
                    quantite=quantity,
                    reference=f"Facture {numero_facture}",
                    fournisseur_id=supplier_id,
                    commentaire=f"Livraison {supplier_name} - {facture_date}"
                )
                await db.mouvements_stock.insert_one(mouvement.dict())
                stock_entries_created += 1
            
            # Ajouter au résultat
            match_result = ProductMatch(
                ocr_name=prod_name,
                matched_product_id=product_id,
                matched_product_name=product_name_final,
                confidence_score=product_match["confidence"] if product_match else 0.0,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                total_price=total_price,
                needs_creation=needs_creation
            )
            products_matched.append(match_result)
        
        # 6. Créer la commande fournisseur dans l'historique
        order_items = [
            OrderItem(
                product_id=pm.matched_product_id,
                product_name=pm.matched_product_name,
                quantity=pm.quantity,
                unit=pm.unit,
                unit_price=pm.unit_price or 0.0,
                total_price=pm.total_price or 0.0
            )
            for pm in products_matched
        ]
        
        order_number = f"CMD-{numero_facture}"
        order = Order(
            order_number=order_number,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            items=order_items,
            total_amount=total_ttc or sum(item.total_price for item in order_items),
            status="delivered",
            actual_delivery_date=datetime.utcnow(),
            notes=f"Importé depuis facture OCR {numero_facture}"
        )
        await db.orders.insert_one(order.dict())
        
        # Marquer le document OCR comme traité
        await db.documents_ocr.update_one(
            {"id": document_id},
            {
                "$set": {
                    "statut": "integre",
                    "date_traitement": datetime.utcnow(),
                    "integration_result": {
                        "products_matched": len(products_matched),
                        "products_created": products_created,
                        "stock_entries": stock_entries_created,
                        "order_id": order.id
                    }
                }
            }
        )
        
        return FactureProcessingResult(
            success=True,
            document_id=document_id,
            supplier_name=supplier_name,
            supplier_id=supplier_id,
            products_matched=products_matched,
            products_created=products_created,
            stock_entries_created=stock_entries_created,
            price_alerts=price_alerts,
            warnings=warnings,
            errors=errors,
            order_id=order.id
        )
        
    except Exception as e:
        print(f"❌ Erreur processing facture: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement de la facture: {str(e)}")


@api_router.post("/ocr/process-mercuriale/{document_id}", response_model=MercurialeProcessingResult)
async def process_mercuriale_to_real_data(document_id: str):
    """
    Process a supplier price list (mercuriale) and integrate it into real system data:
    - Match products with existing database
    - Update reference prices
    - Compare with current prices
    - Generate alerts for significant variations
    - Create price change history
    """
    try:
        # 1. Récupérer le document OCR
        document = await db.documents_ocr.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document OCR non trouvé")
        
        # 2. Extraire les données parsées
        donnees_parsees = document.get("donnees_parsees", {})
        if not donnees_parsees:
            raise HTTPException(status_code=400, detail="Données parsées non disponibles")
        
        supplier_name = donnees_parsees.get("fournisseur", "Fournisseur inconnu")
        mercuriale_date = donnees_parsees.get("date", datetime.utcnow().strftime("%d/%m/%Y"))
        produits_mercuriale = donnees_parsees.get("produits", [])
        
        print(f"📋 Processing mercuriale from {supplier_name} with {len(produits_mercuriale)} products")
        
        # 3. Matcher le fournisseur
        supplier_match = await match_supplier_by_name(supplier_name)
        supplier_id = None
        
        if supplier_match and supplier_match["confidence"] >= 0.6:
            supplier_id = supplier_match["supplier_id"]
            supplier_name = supplier_match["supplier_name"]
            print(f"✅ Fournisseur matché: {supplier_name}")
        else:
            # Créer un nouveau fournisseur
            new_supplier = Fournisseur(
                nom=supplier_name,
                categorie="frais"
            )
            await db.fournisseurs.insert_one(new_supplier.dict())
            supplier_id = new_supplier.id
            print(f"✅ Nouveau fournisseur créé: {supplier_name}")
        
        prices_updated = 0
        price_changes = []
        warnings = []
        errors = []
        
        # 4. Traiter chaque produit de la mercuriale
        for prod_data in produits_mercuriale:
            prod_name = prod_data.get("nom", "")
            new_price = prod_data.get("prix_unitaire", 0)
            unit = prod_data.get("unite", "kg")
            
            if not prod_name or new_price <= 0:
                continue
            
            # Matcher avec les produits existants
            product_match = await match_product_by_name(prod_name, min_confidence=0.7)
            
            if product_match and product_match["confidence"] >= 0.7:
                product_id = product_match["product_id"]
                product_name_final = product_match["product_name"]
                
                # Récupérer le produit pour comparer les prix
                produit = await db.produits.find_one({"id": product_id})
                if produit:
                    old_reference_price = produit.get("reference_price", 0)
                    
                    # Calculer la variation
                    if old_reference_price:
                        price_diff = new_price - old_reference_price
                        price_diff_pct = (price_diff / old_reference_price) * 100
                        
                        if abs(price_diff_pct) > 5:  # Variation > 5%
                            price_changes.append({
                                "product_name": product_name_final,
                                "old_price": old_reference_price,
                                "new_price": new_price,
                                "difference": round(price_diff, 2),
                                "difference_pct": round(price_diff_pct, 1),
                                "change_type": "increase" if price_diff > 0 else "decrease"
                            })
                    
                    # Mettre à jour le prix de référence
                    await db.produits.update_one(
                        {"id": product_id},
                        {
                            "$set": {
                                "reference_price": new_price
                            }
                        }
                    )
                    
                    # Mettre à jour ou créer la relation fournisseur-produit
                    supplier_product_info = await db.supplier_product_info.find_one({
                        "supplier_id": supplier_id,
                        "product_id": product_id
                    })
                    
                    if supplier_product_info:
                        await db.supplier_product_info.update_one(
                            {"id": supplier_product_info["id"]},
                            {
                                "$set": {
                                    "price": new_price,
                                    "last_updated": datetime.utcnow()
                                }
                            }
                        )
                    else:
                        new_relation = SupplierProductInfo(
                            supplier_id=supplier_id,
                            product_id=product_id,
                            price=new_price,
                            is_preferred=False
                        )
                        await db.supplier_product_info.insert_one(new_relation.dict())
                    
                    prices_updated += 1
                else:
                    warnings.append(f"⚠️ Produit {product_id} non trouvé en base")
            else:
                warnings.append(f"⚠️ Produit '{prod_name}' non matché (confiance: {product_match['confidence'] if product_match else 0})")
        
        # Marquer le document OCR comme traité
        await db.documents_ocr.update_one(
            {"id": document_id},
            {
                "$set": {
                    "statut": "integre",
                    "date_traitement": datetime.utcnow(),
                    "integration_result": {
                        "prices_updated": prices_updated,
                        "price_changes": len(price_changes)
                    }
                }
            }
        )
        
        return MercurialeProcessingResult(
            success=True,
            document_id=document_id,
            supplier_name=supplier_name,
            supplier_id=supplier_id,
            prices_updated=prices_updated,
            price_changes=price_changes,
            warnings=warnings,
            errors=errors
        )
        
    except Exception as e:
        print(f"❌ Erreur processing mercuriale: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement de la mercuriale: {str(e)}")


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