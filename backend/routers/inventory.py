from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models.schemas import InventoryItem
from auth import get_current_user
from database import db
import uuid
import requests
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
async def get_items(user: dict = Depends(get_current_user)):
    items = await db.inventory_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return items


@router.post("")
async def create_item(item: InventoryItem, user: dict = Depends(get_current_user)):
    doc = item.model_dump()
    doc["family_id"] = user["family_id"]
    doc["created_by"] = user["user_id"]
    await db.inventory_items.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("family_id", None)
    return doc


@router.put("/{item_id}")
async def update_item(item_id: str, item: InventoryItem, user: dict = Depends(get_current_user)):
    update_data = item.model_dump()
    update_data.pop("id", None)
    result = await db.inventory_items.update_one(
        {"id": item_id, "family_id": user["family_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = await db.inventory_items.find_one({"id": item_id}, {"_id": 0, "family_id": 0})
    return updated


@router.delete("/{item_id}")
async def delete_item(item_id: str, user: dict = Depends(get_current_user)):
    result = await db.inventory_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}


@router.post("/bulk-add")
async def bulk_add_items(items: List[InventoryItem], user: dict = Depends(get_current_user)):
    if not items:
        return {"message": "No items to add", "count": 0}
    docs = []
    for item in items:
        doc = item.model_dump()
        if not doc.get("id"):
            doc["id"] = str(uuid.uuid4())
        doc["family_id"] = user["family_id"]
        doc["created_by"] = user["user_id"]
        docs.append(doc)
    await db.inventory_items.insert_many(docs)
    for d in docs:
        d.pop("_id", None)
        d.pop("family_id", None)
    return {"message": f"{len(docs)} items added", "count": len(docs)}


@router.get("/barcode/{barcode}")
async def lookup_barcode(barcode: str, user: dict = Depends(get_current_user)):
    try:
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                return {
                    "found": True,
                    "barcode": barcode,
                    "name": product.get("product_name", "Unknown"),
                    "brand": product.get("brands", ""),
                    "category": product.get("categories_tags", ["Other"])[0] if product.get("categories_tags") else "Other",
                    "image": product.get("image_url", ""),
                }
    except Exception as e:
        logger.error(f"Barcode lookup error: {e}")
    return {"found": False, "barcode": barcode}
