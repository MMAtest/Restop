"""Isolated, opt-in RESTOP tenant-v2 stock pilot.

Legacy collections are never read here. All tenant IDs come from an authenticated
user record, not from any URL or request body. Do NOT enable legacy tenant routes.
"""
import hashlib
import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure, PyMongoError

_ALLOWED_UNITS = {"kg", "g", "l", "ml", "unite"}
_READ_ROLES = {"super_admin", "patron", "gerant", "chef_cuisine", "employe_cuisine", "caissier", "barman"}
_WRITE_ROLES = {"super_admin", "patron", "gerant", "chef_cuisine"}


class TenantPayload(BaseModel):
    # Never accept restaurant_id, actor_id or any client-controlled ownership.
    model_config = ConfigDict(extra="forbid")


class SupplierInput(TenantPayload):
    name: str = Field(min_length=2, max_length=160)

    @field_validator("name")
    @classmethod
    def safe_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("nom fournisseur requis")
        return value


class ProductInput(TenantPayload):
    name: str = Field(min_length=2, max_length=160)
    unit: str
    supplier_id: Optional[str] = Field(default=None, max_length=64)
    purchase_price_cents: StrictInt = Field(ge=0, le=100000000)

    @field_validator("name")
    @classmethod
    def safe_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("nom produit requis")
        return value

    @field_validator("unit")
    @classmethod
    def safe_unit(cls, value):
        if value not in _ALLOWED_UNITS:
            raise ValueError("unité invalide")
        return value


class StockAdjustmentInput(TenantPayload):
    product_id: str = Field(min_length=1, max_length=64)
    delta_milliunits: StrictInt = Field(ge=-100000000, le=100000000)
    reason: str = Field(min_length=4, max_length=500)
    idempotency_key: str = Field(min_length=12, max_length=128)

    @field_validator("reason")
    @classmethod
    def safe_reason(cls, value):
        value = value.strip()
        if len(value) < 4:
            raise ValueError("motif insuffisant")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def safe_idempotency_key(cls, value):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{12,128}", value):
            raise ValueError("clé d'idempotence invalide")
        return value

    @field_validator("delta_milliunits")
    @classmethod
    def delta_nonzero(cls, value):
        if value == 0:
            raise ValueError("quantité nulle")
        return value


def scoped_stock_id(restaurant_id, product_id):
    return hashlib.sha256((restaurant_id + "\0" + product_id).encode("utf-8")).hexdigest()


def scoped_movement_id(restaurant_id, key):
    return hashlib.sha256((restaurant_id + "\0" + key).encode("utf-8")).hexdigest()


async def ensure_tenant_indexes(db):
    """Run only when RESTOP_ENABLE_TENANT_V2=1 after migration review."""
    await db.tenant_suppliers.create_index([("restaurant_id", ASCENDING), ("id", ASCENDING)], unique=True)
    await db.tenant_products.create_index([("restaurant_id", ASCENDING), ("id", ASCENDING)], unique=True)
    await db.tenant_stocks.create_index([("restaurant_id", ASCENDING), ("product_id", ASCENDING)], unique=True)
    await db.tenant_stock_movements.create_index([("restaurant_id", ASCENDING), ("product_id", ASCENDING), ("created_at", ASCENDING)])


def build_tenant_router(db, session_guard):
    router = APIRouter(prefix="/tenant", tags=["tenant-v2-pilot"])

    async def tenant_reader(user=Depends(session_guard)):
        restaurant = user.get("restaurant_id")
        if not isinstance(restaurant, str) or not restaurant.strip():
            raise HTTPException(status_code=403, detail="Compte sans établissement")
        if user.get("role") not in _READ_ROLES:
            raise HTTPException(status_code=403, detail="Rôle non autorisé")
        return user

    async def tenant_editor(user=Depends(tenant_reader)):
        if user.get("role") not in _WRITE_ROLES:
            raise HTTPException(status_code=403, detail="Modification réservée au responsable")
        return user

    async def read_product(rid, pid, session=None):
        product = await db.tenant_products.find_one({"restaurant_id": rid, "id": pid}, session=session)
        if product is None:
            # A foreign-tenant ID and a nonexistent ID have identical responses.
            raise HTTPException(status_code=404, detail="Produit introuvable")
        product.pop("_id", None)
        return product

    @router.get("/suppliers")
    async def list_suppliers(user=Depends(tenant_reader)):
        return await db.tenant_suppliers.find({"restaurant_id": user["restaurant_id"]}, {"_id": 0}).limit(200).to_list(length=200)

    @router.post("/suppliers", status_code=201)
    async def create_supplier(body: SupplierInput, user=Depends(tenant_editor)):
        row = {"id": str(uuid.uuid4()), "restaurant_id": user["restaurant_id"], "name": body.name, "created_by": user["id"], "created_at": datetime.utcnow()}
        await db.tenant_suppliers.insert_one(dict(row))
        return row

    @router.get("/products")
    async def list_products(user=Depends(tenant_reader)):
        return await db.tenant_products.find({"restaurant_id": user["restaurant_id"]}, {"_id": 0}).limit(500).to_list(length=500)

    @router.get("/products/{product_id}")
    async def get_product(product_id: str, user=Depends(tenant_reader)):
        return await read_product(user["restaurant_id"], product_id)

    @router.post("/products", status_code=201)
    async def create_product(body: ProductInput, user=Depends(tenant_editor)):
        rid = user["restaurant_id"]
        if body.supplier_id:
            linked = await db.tenant_suppliers.find_one({"restaurant_id": rid, "id": body.supplier_id})
            if linked is None:
                raise HTTPException(status_code=404, detail="Fournisseur introuvable")
        row = {"id": str(uuid.uuid4()), "restaurant_id": rid, "name": body.name,
               "unit": body.unit, "supplier_id": body.supplier_id,
               "purchase_price_cents": body.purchase_price_cents,
               "created_by": user["id"], "created_at": datetime.utcnow()}
        await db.tenant_products.insert_one(dict(row))
        return row

    @router.get("/stock")
    async def list_stock(user=Depends(tenant_reader)):
        rid = user["restaurant_id"]
        return await db.tenant_stocks.find({"restaurant_id": rid}, {"_id": 0}).limit(500).to_list(length=500)

    @router.get("/stock/movements")
    async def list_movements(user=Depends(tenant_reader)):
        rid = user["restaurant_id"]
        return await db.tenant_stock_movements.find({"restaurant_id": rid}, {"_id": 0}).sort("created_at", -1).limit(200).to_list(length=200)

    @router.post("/stock/adjustments", status_code=201)
    async def adjust_stock(body: StockAdjustmentInput, user=Depends(tenant_editor)):
        rid = user["restaurant_id"]
        adjustment_id = scoped_movement_id(rid, body.idempotency_key)
        snapshot = {"product_id": body.product_id, "delta_milliunits": body.delta_milliunits, "reason": body.reason}

        async def replay_or_conflict():
            existing = await db.tenant_stock_movements.find_one({"_id": adjustment_id, "restaurant_id": rid})
            if existing is None:
                return None
            if any(existing.get(field) != value for field, value in snapshot.items()):
                raise HTTPException(status_code=409, detail="Clé d'idempotence déjà utilisée avec d'autres paramètres")
            return {"movement_id": adjustment_id, "product_id": body.product_id,
                    "quantity_milliunits": existing["quantity_after_milliunits"], "replayed": True}

        previous = await replay_or_conflict()
        if previous:
            return previous
        # Stock + movement must either both commit or both roll back.
        # Standalone MongoDB cannot provide this guarantee: reject and do not write.
        try:
            hello = await db.client.admin.command("hello")
            if not hello.get("setName") and hello.get("msg") != "isdbgrid":
                raise HTTPException(status_code=503, detail="Transactions MongoDB indisponibles (replica set requis)")
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    await read_product(rid, body.product_id, session=session)
                    sid = scoped_stock_id(rid, body.product_id)
                    current = await db.tenant_stocks.find_one({"_id": sid, "restaurant_id": rid}, session=session)
                    before = current["quantity_milliunits"] if current else 0
                    after = before + body.delta_milliunits
                    if after < 0:
                        raise HTTPException(status_code=409, detail="Stock insuffisant")
                    if after > 1000000000000:
                        raise HTTPException(status_code=409, detail="Quantité maximale dépassée")
                    if current:
                        await db.tenant_stocks.update_one({"_id": sid, "restaurant_id": rid, "quantity_milliunits": before},
                            {"$set": {"quantity_milliunits": after, "updated_at": datetime.utcnow()}}, session=session)
                    else:
                        await db.tenant_stocks.insert_one({"_id": sid, "restaurant_id": rid, "product_id": body.product_id,
                            "quantity_milliunits": after, "updated_at": datetime.utcnow()}, session=session)
                    await db.tenant_stock_movements.insert_one({"_id": adjustment_id, "restaurant_id": rid, **snapshot,
                        "quantity_after_milliunits": after, "actor_id": user["id"], "created_at": datetime.utcnow()}, session=session)
            return {"movement_id": adjustment_id, "product_id": body.product_id,
                    "quantity_milliunits": after, "replayed": False}
        except HTTPException:
            raise
        except (DuplicateKeyError, OperationFailure) as exc:
            previous = await replay_or_conflict()
            if previous:
                return previous
            raise HTTPException(status_code=409, detail="Conflit de stock : actualiser puis réessayer") from exc
        except PyMongoError as exc:
            raise HTTPException(status_code=503, detail="Stock indisponible, modification non confirmée") from exc

    return router
