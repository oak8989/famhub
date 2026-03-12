from fastapi import APIRouter, Depends
from typing import List
from models.schemas import PantryItem
from auth import get_current_user
from database import db
import requests
import uuid

router = APIRouter(prefix="/api/pantry", tags=["pantry"])


@router.get("", response_model=List[PantryItem])
async def get_pantry_items(user: dict = Depends(get_current_user)):
    items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for i in items:
        i.pop("family_id", None)
    return items


@router.post("", response_model=PantryItem)
async def create_pantry_item(item: PantryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    await db.pantry_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc


@router.put("/{item_id}")
async def update_pantry_item(item_id: str, item: PantryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.pantry_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc


@router.delete("/{item_id}")
async def delete_pantry_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.pantry_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}


@router.get("/barcode/{barcode}")
async def lookup_barcode(barcode: str):
    # Try Open Food Facts first
    try:
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5)
        data = response.json()
        if data.get("status") == 1:
            product = data.get("product", {})
            name = product.get("product_name", "").strip()
            brand = product.get("brands", "").strip()
            image = product.get("image_front_small_url", "")
            raw_cat = product.get("categories_tags", [])
            category = raw_cat[0].replace("en:", "").replace("-", " ").title() if raw_cat else "Other"
            display_name = f"{brand} {name}".strip() if brand and name else (name or brand or "Unknown Product")
            return {
                "found": True,
                "name": display_name,
                "brand": brand,
                "category": category,
                "image": image,
                "barcode": barcode,
                "source": "Open Food Facts"
            }
    except Exception:
        pass

    # Try UPC Item DB as fallback
    try:
        response = requests.get(f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}", timeout=5)
        data = response.json()
        items = data.get("items", [])
        if items:
            item = items[0]
            return {
                "found": True,
                "name": item.get("title", "Unknown Product"),
                "brand": item.get("brand", ""),
                "category": item.get("category", "Other"),
                "image": (item.get("images", [None]) or [None])[0] or "",
                "barcode": barcode,
                "source": "UPC Item DB"
            }
    except Exception:
        pass

    return {"found": False, "barcode": barcode}


@router.post("/bulk-add")
async def bulk_add_pantry_items(items: List[PantryItem], user: dict = Depends(get_current_user)):
    if not items:
        return {"message": "No items to add", "count": 0}
    docs = []
    for item in items:
        item_doc = item.model_dump()
        if not item_doc.get("id"):
            item_doc["id"] = str(uuid.uuid4())
        item_doc["family_id"] = user["family_id"]
        docs.append(item_doc)
    await db.pantry_items.insert_many(docs)
    # Remove MongoDB _id and family_id from response
    for d in docs:
        d.pop("_id", None)
        d.pop("family_id", None)
    return {"message": f"{len(docs)} items added", "count": len(docs), "items": docs}
