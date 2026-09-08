"""
Module Daily Specials : configuration journalière du Plat du Jour et Menu Enfant
par le chef. Mission obligatoire pour permettre le décrément stock automatique
quand "Plat du jour" ou "Menu enfant" sont vendus.

Endpoints :
  GET  /api/daily-specials/today        -> config du jour
  GET  /api/daily-specials/{date}        -> config d'une date donnée (YYYY-MM-DD)
  POST /api/daily-specials/today        -> crée/met à jour la config du jour
  GET  /api/daily-specials/mission-status -> indique si la mission est complétée

Modèle MongoDB (collection daily_specials) :
  {
    id, date (YYYY-MM-DD),
    plat_du_jour: {recette_id, recette_nom} | null,
    menu_enfant: {recette_id, recette_nom} | null,
    set_by_user_id, set_by_user_nom,
    created_at, updated_at
  }
"""
import uuid
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


daily_router = APIRouter(prefix="/daily-specials", tags=["daily-specials"])


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


# ==================== Modèles ====================

class SpecialRecipeRef(BaseModel):
    recette_id: Optional[str] = None
    recette_nom: Optional[str] = None


class DailySpecialUpdate(BaseModel):
    plat_du_jour: Optional[SpecialRecipeRef] = None
    menu_enfant: Optional[SpecialRecipeRef] = None
    set_by_user_id: Optional[str] = None
    set_by_user_nom: Optional[str] = None


def setup_daily_specials_routes(db):

    @daily_router.get("/today")
    async def get_today():
        """Config du jour. Si absente, retourne {plat_du_jour: null, menu_enfant: null}."""
        d = today_iso()
        doc = await db.daily_specials.find_one({"date": d}, {"_id": 0})
        if not doc:
            return {
                "date": d,
                "plat_du_jour": None,
                "menu_enfant": None,
                "is_set": False,
                "is_complete": False,
            }
        return {
            **doc,
            "is_set": True,
            "is_complete": bool(doc.get("plat_du_jour")) and bool(doc.get("menu_enfant")),
        }

    @daily_router.get("/{date_str}")
    async def get_for_date(date_str: str):
        """Config d'une date donnée (format YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Format date invalide (YYYY-MM-DD requis)")
        doc = await db.daily_specials.find_one({"date": date_str}, {"_id": 0})
        if not doc:
            return {"date": date_str, "plat_du_jour": None, "menu_enfant": None, "is_set": False}
        return {**doc, "is_set": True}

    @daily_router.post("/today")
    async def set_today(payload: DailySpecialUpdate):
        """Crée ou met à jour la config du jour. Permet de mettre à jour partiellement."""
        d = today_iso()
        existing = await db.daily_specials.find_one({"date": d}, {"_id": 0})

        # Validation : si recette_id fourni, vérifier qu'elle existe
        for field_name, ref in (("plat_du_jour", payload.plat_du_jour), ("menu_enfant", payload.menu_enfant)):
            if ref and ref.recette_id:
                r = await db.recettes.find_one({"id": ref.recette_id}, {"_id": 0, "nom": 1})
                if not r:
                    raise HTTPException(status_code=404, detail=f"Recette {field_name} introuvable")
                # On rafraîchit le nom
                ref.recette_nom = r["nom"]

        # Construire l'objet mis à jour (preserve l'autre champ si non fourni)
        plat = payload.plat_du_jour.dict() if payload.plat_du_jour else (existing or {}).get("plat_du_jour")
        menu = payload.menu_enfant.dict() if payload.menu_enfant else (existing or {}).get("menu_enfant")

        update = {
            "date": d,
            "plat_du_jour": plat,
            "menu_enfant": menu,
            "set_by_user_id": payload.set_by_user_id,
            "set_by_user_nom": payload.set_by_user_nom,
            "updated_at": datetime.now(timezone.utc),
        }
        await db.daily_specials.update_one(
            {"date": d},
            {"$set": update, "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc),
            }},
            upsert=True
        )

        is_complete = bool(plat) and bool(menu)
        return {"success": True, "date": d, "is_complete": is_complete, "plat_du_jour": plat, "menu_enfant": menu}

    @daily_router.get("/mission-status/today")
    async def mission_status():
        """
        Statut de la mission obligatoire chef du jour :
        - mission_required: True si pas encore défini ce jour
        - missing_fields: ['plat_du_jour', 'menu_enfant'] selon ce qui manque
        """
        d = today_iso()
        doc = await db.daily_specials.find_one({"date": d}, {"_id": 0})
        missing = []
        if not doc:
            missing = ['plat_du_jour', 'menu_enfant']
        else:
            if not doc.get('plat_du_jour'):
                missing.append('plat_du_jour')
            if not doc.get('menu_enfant'):
                missing.append('menu_enfant')
        return {
            "date": d,
            "mission_required": len(missing) > 0,
            "missing_fields": missing,
            "is_complete": len(missing) == 0,
        }

    return daily_router


# ==================== Helper utilisable depuis sales_import ====================

async def resolve_daily_special(db, daily_special_key: str, date_str: str = None):
    """
    Pour un mapping de type 'daily_special' avec daily_special_key='plat_du_jour' ou 'menu_enfant',
    retourne (recette_id, recette_nom) si la mission a été complétée pour cette date.
    Retourne (None, None) sinon.
    """
    d = date_str or today_iso()
    doc = await db.daily_specials.find_one({"date": d}, {"_id": 0})
    if not doc:
        return None, None
    ref = doc.get(daily_special_key)
    if not ref:
        return None, None
    return ref.get("recette_id"), ref.get("recette_nom")
