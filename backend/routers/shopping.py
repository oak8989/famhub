from fastapi import APIRouter, Depends
from typing import List
from models.schemas import ShoppingItem
from auth import get_current_user
from database import db
from routers.websocket import notify_family
from routers.utilities import send_push_to_family

router = APIRouter(prefix="/api/shopping", tags=["shopping"])


@router.get("", response_model=List[ShoppingItem])
async def get_shopping_items(user: dict = Depends(get_current_user)):
    items = await db.shopping_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for i in items:
        i.pop("family_id", None)
    return items


@router.post("", response_model=ShoppingItem)
async def create_shopping_item(item: ShoppingItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    item_doc["added_by"] = user["user_id"]
    await db.shopping_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    await notify_family(user["family_id"], "update", "shopping")
    await send_push_to_family(user["family_id"], "Shopping List", f"'{item_doc['name']}' was added", "/shopping")
    return item_doc


@router.put("/{item_id}")
async def update_shopping_item(item_id: str, item: ShoppingItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.shopping_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    await notify_family(user["family_id"], "update", "shopping")
    return item_doc


@router.delete("/{item_id}")
async def delete_shopping_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.shopping_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    await notify_family(user["family_id"], "update", "shopping")
    return {"message": "Item deleted"}


@router.delete("")
async def clear_shopping_list(user: dict = Depends(get_current_user)):
    await db.shopping_items.delete_many({"family_id": user["family_id"], "checked": True})
    await notify_family(user["family_id"], "update", "shopping")
    return {"message": "Checked items cleared"}
