"""Tenant-scoped workflows pilot: recipes, internal purchase drafts and Z reports.

All data is stored in new collections; legacy Restop collections are never read.
All routes require a persisted server-side session and restaurant_id. This router
must only be installed under RESTOP_ENABLE_TENANT_V2=1; there is no rollout here.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from tenant_stock_api import _READ_ROLES, _WRITE_ROLES


class TenantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecipeIngredient(TenantInput):
    product_id: str = Field(min_length=1, max_length=64)
    quantity_milliunits: StrictInt = Field(gt=0, le=100000000)


class RecipeInput(TenantInput):
    name: str = Field(min_length=2, max_length=160)
    yield_portions: StrictInt = Field(ge=1, le=1000)
    sale_price_cents: StrictInt = Field(ge=0, le=100000000)
    ingredients: List[RecipeIngredient] = Field(min_length=1, max_length=40)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nom de recette requis")
        return v

    @model_validator(mode="after")
    def reject_duplicate_products(self):
        ids = [line.product_id for line in self.ingredients]
        if len(ids) != len(set(ids)):
            raise ValueError("Un ingrédient ne peut apparaître deux fois dans la recette")
        return self


class OrderLine(TenantInput):
    product_id: str = Field(min_length=1, max_length=64)
    quantity_milliunits: StrictInt = Field(gt=0, le=100000000)
    unit_price_cents: StrictInt = Field(ge=0, le=100000000)


class PurchaseDraftInput(TenantInput):
    supplier_id: str = Field(min_length=1, max_length=64)
    lines: List[OrderLine] = Field(min_length=1, max_length=100)
    note: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def unique_products(self):
        ids = [line.product_id for line in self.lines]
        if len(ids) != len(set(ids)):
            raise ValueError("Une référence ne peut apparaître deux fois dans un brouillon")
        return self


class ZReportInput(TenantInput):
    report_reference: str = Field(min_length=2, max_length=100)
    report_date: date
    total_cents: StrictInt = Field(ge=0, le=1000000000)
    cash_cents: StrictInt = Field(ge=0, le=1000000000)
    card_cents: StrictInt = Field(ge=0, le=1000000000)
    other_cents: StrictInt = Field(ge=0, le=1000000000)
    note: Optional[str] = Field(default=None, max_length=500)

    @field_validator("report_reference")
    @classmethod
    def clean_reference(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Référence Z requise")
        return v

    @model_validator(mode="after")
    def check_payment_total(self):
        if self.total_cents != self.cash_cents + self.card_cents + self.other_cents:
            raise ValueError("La somme des règlements doit correspondre au total du Z")
        return self


def cents_for_quantity(unit_price_cents, quantity_milliunits):
    """Integer cents, decimal half-up for quantities smaller than one unit."""
    return int((Decimal(unit_price_cents) * Decimal(quantity_milliunits) /
                Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


async def ensure_workflow_indexes(db):
    await db.tenant_recipes.create_index([("restaurant_id", ASCENDING), ("id", ASCENDING)], unique=True)
    await db.tenant_purchase_orders.create_index([("restaurant_id", ASCENDING), ("id", ASCENDING)], unique=True)
    await db.tenant_z_reports.create_index([("restaurant_id", ASCENDING), ("id", ASCENDING)], unique=True)
    await db.tenant_z_reports.create_index([("restaurant_id", ASCENDING), ("report_reference", ASCENDING)], unique=True)


def build_tenant_workflow_router(db, session_guard):
    router = APIRouter(prefix="/tenant", tags=["tenant-v2-workflows"])

    async def editor(user=Depends(session_guard)):
        rid = user.get("restaurant_id")
        if not isinstance(rid, str) or not rid.strip():
            raise HTTPException(status_code=403, detail="Compte sans établissement")
        if user.get("role") not in _WRITE_ROLES:
            raise HTTPException(status_code=403, detail="Réservé aux responsables métiers")
        return user

    async def z_reader(user=Depends(session_guard)):
        rid = user.get("restaurant_id")
        if not isinstance(rid, str) or not rid.strip():
            raise HTTPException(status_code=403, detail="Compte sans établissement")
        if user.get("role") not in {"super_admin", "patron", "gerant", "caissier"}:
            raise HTTPException(status_code=403, detail="Rapports Z réservés à la caisse et direction")
        return user

    async def tenant_product(rid, pid):
        product = await db.tenant_products.find_one(
            {"restaurant_id": rid, "id": pid}, {"_id": 0})
        if product is None:
            raise HTTPException(status_code=404, detail="Produit introuvable")
        return product

    @router.get("/recipes")
    async def list_recipes(user=Depends(editor)):
        return await db.tenant_recipes.find(
            {"restaurant_id": user["restaurant_id"]}, {"_id": 0}
        ).limit(200).to_list(length=200)

    @router.get("/recipes/{recipe_id}")
    async def get_recipe(recipe_id: str, user=Depends(editor)):
        row = await db.tenant_recipes.find_one(
            {"restaurant_id": user["restaurant_id"], "id": recipe_id}, {"_id": 0})
        if row is None:
            raise HTTPException(status_code=404, detail="Recette introuvable")
        return row

    @router.post("/recipes", status_code=201)
    async def create_recipe(body: RecipeInput, user=Depends(editor)):
        rid = user["restaurant_id"]
        priced = []
        cost_cents = 0
        for ingredient in body.ingredients:
            product = await tenant_product(rid, ingredient.product_id)
            line_cents = cents_for_quantity(
                product["purchase_price_cents"], ingredient.quantity_milliunits)
            cost_cents += line_cents
            priced.append({**ingredient.model_dump(), "unit": product["unit"],
                           "price_snapshot_cents": product["purchase_price_cents"],
                           "cost_snapshot_cents": line_cents})
        row = {"id": str(uuid.uuid4()), "restaurant_id": rid,
               "name": body.name, "yield_portions": body.yield_portions,
               "sale_price_cents": body.sale_price_cents, "ingredients": priced,
               "cost_snapshot_cents": cost_cents,
               "cost_per_portion_snapshot_cents": cents_for_quantity(cost_cents, 1000) // body.yield_portions,
               "created_by": user["id"], "created_at": datetime.utcnow()}
        # A cost snapshot is not silently refreshed when purchase prices change.
        await db.tenant_recipes.insert_one(dict(row))
        return row

    @router.get("/purchase-orders")
    async def list_orders(user=Depends(editor)):
        return await db.tenant_purchase_orders.find(
            {"restaurant_id": user["restaurant_id"]}, {"_id": 0}
        ).limit(200).to_list(length=200)

    @router.get("/purchase-orders/{order_id}")
    async def get_order(order_id: str, user=Depends(editor)):
        row = await db.tenant_purchase_orders.find_one(
            {"restaurant_id": user["restaurant_id"], "id": order_id}, {"_id": 0})
        if row is None:
            raise HTTPException(status_code=404, detail="Brouillon introuvable")
        return row

    @router.post("/purchase-orders", status_code=201)
    async def create_order_draft(body: PurchaseDraftInput, user=Depends(editor)):
        rid = user["restaurant_id"]
        supplier = await db.tenant_suppliers.find_one(
            {"restaurant_id": rid, "id": body.supplier_id}, {"_id": 0})
        if supplier is None:
            raise HTTPException(status_code=404, detail="Fournisseur introuvable")
        rows, total = [], 0
        for line in body.lines:
            product = await tenant_product(rid, line.product_id)
            if product.get("supplier_id") != body.supplier_id:
                raise HTTPException(status_code=409,
                                    detail="Produit non lié à ce fournisseur")
            amount = cents_for_quantity(line.unit_price_cents, line.quantity_milliunits)
            total += amount
            rows.append({**line.model_dump(), "unit": product["unit"],
                         "line_total_cents": amount})
        row = {"id": str(uuid.uuid4()), "restaurant_id": rid, "supplier_id": body.supplier_id,
               "status": "draft", "note": body.note, "lines": rows,
               "estimated_total_cents": total, "created_by": user["id"],
               "created_at": datetime.utcnow()}
        # IMPORTANT: This is an INTERNAL draft, never an actual supplier order.
        await db.tenant_purchase_orders.insert_one(dict(row))
        return row

    @router.get("/z-reports")
    async def list_z_reports(user=Depends(z_reader)):
        return await db.tenant_z_reports.find(
            {"restaurant_id": user["restaurant_id"]}, {"_id": 0}
        ).sort("report_date", -1).limit(200).to_list(length=200)

    @router.get("/z-reports/{report_id}")
    async def get_z_report(report_id: str, user=Depends(z_reader)):
        row = await db.tenant_z_reports.find_one(
            {"restaurant_id": user["restaurant_id"], "id": report_id}, {"_id": 0})
        if row is None:
            raise HTTPException(status_code=404, detail="Rapport Z introuvable")
        return row

    @router.post("/z-reports", status_code=201)
    async def record_z_report(body: ZReportInput, user=Depends(z_reader)):
        rid = user["restaurant_id"]
        payload = body.model_dump(mode="json")

        async def existing_report():
            row = await db.tenant_z_reports.find_one(
                {"restaurant_id": rid, "report_reference": body.report_reference},
                {"_id": 0})
            if row is None:
                return None
            if any(row.get(key) != value for key, value in payload.items()):
                raise HTTPException(status_code=409,
                                    detail="Référence Z déjà enregistrée avec d'autres données")
            return {"report": row, "replayed": True}

        replay = await existing_report()
        if replay:
            return replay
        row = {"id": str(uuid.uuid4()), "restaurant_id": rid, **payload,
               "created_by": user["id"], "created_at": datetime.utcnow()}
        try:
            await db.tenant_z_reports.insert_one(dict(row))
        except DuplicateKeyError:
            replay = await existing_report()
            if replay:
                return replay
            raise HTTPException(status_code=409, detail="Conflit d'enregistrement du Z")
        return {"report": row, "replayed": False}

    return router
