from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt
import bcrypt
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Frontend build directory (for Docker deployment)
FRONTEND_BUILD_DIR = ROOT_DIR.parent / 'frontend' / 'build'

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'family-hub-secret-key-2024')
JWT_ALGORITHM = "HS256"

# Photo storage directory
PHOTOS_DIR = ROOT_DIR / "photos"
PHOTOS_DIR.mkdir(exist_ok=True)

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# ============== MODELS ==============

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "member"
    avatar_seed: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    role: str
    avatar_seed: str
    created_at: str

class FamilyCreate(BaseModel):
    name: str
    pin: str

class FamilyPinLogin(BaseModel):
    pin: str

class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    date: str
    time: Optional[str] = ""
    color: Optional[str] = "#E07A5F"
    created_by: Optional[str] = None

class ShoppingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: Optional[str] = "1"
    category: Optional[str] = "General"
    checked: bool = False
    added_by: Optional[str] = None

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    completed: bool = False
    created_by: Optional[str] = None

class Note(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    color: Optional[str] = "#F2CC8F"
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    sender_id: str
    sender_name: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BudgetEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str
    type: str  # income or expense
    date: str
    created_by: Optional[str] = None

class MealPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    meal_type: str  # breakfast, lunch, dinner, snack
    recipe_id: Optional[str] = None
    recipe_name: str
    notes: Optional[str] = ""

class Recipe(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    ingredients: List[str]
    instructions: List[str]
    prep_time: Optional[str] = ""
    cook_time: Optional[str] = ""
    servings: Optional[int] = 4
    category: Optional[str] = "Main Course"
    image_url: Optional[str] = ""
    created_by: Optional[str] = None

class GroceryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: Optional[str] = "1"
    checked: bool = False

class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    relationship: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""
    avatar_seed: str = Field(default_factory=lambda: str(uuid.uuid4()))

class PhotoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    filename: str
    uploaded_by: Optional[str] = None
    uploaded_at: str
    description: Optional[str] = ""

class PantryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    barcode: Optional[str] = ""
    quantity: int = 1
    unit: Optional[str] = "pcs"
    category: Optional[str] = "Other"
    expiry_date: Optional[str] = None
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== AUTH HELPERS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, family_id: str) -> str:
    return jwt.encode({"user_id": user_id, "family_id": family_id}, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "id": str(uuid.uuid4()),
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role,
        "avatar_seed": user.avatar_seed or str(uuid.uuid4()),
        "family_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    del user_doc["password"]
    del user_doc["_id"]
    return {"user": user_doc, "message": "Registration successful"}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user.get("family_id", ""))
    del user["password"]
    return {"token": token, "user": user}

@api_router.post("/auth/pin-login")
async def pin_login(data: FamilyPinLogin):
    family = await db.families.find_one({"pin": data.pin}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    
    token = create_token("guest", family["id"])
    return {"token": token, "family": family}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0, "password": 0})
    if not user_data:
        return {"user_id": user["user_id"], "family_id": user["family_id"]}
    return user_data

# ============== FAMILY ROUTES ==============

@api_router.post("/family/create")
async def create_family(family: FamilyCreate, user: dict = Depends(get_current_user)):
    family_doc = {
        "id": str(uuid.uuid4()),
        "name": family.name,
        "pin": family.pin,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.families.insert_one(family_doc)
    await db.users.update_one({"id": user["user_id"]}, {"$set": {"family_id": family_doc["id"]}})
    del family_doc["_id"]
    return family_doc

@api_router.get("/family")
async def get_family(user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        return None
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    return family

@api_router.get("/family/members")
async def get_family_members(user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        return []
    members = await db.users.find({"family_id": user["family_id"]}, {"_id": 0, "password": 0}).to_list(100)
    return members

@api_router.post("/family/join/{family_id}")
async def join_family(family_id: str, user: dict = Depends(get_current_user)):
    family = await db.families.find_one({"id": family_id}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    await db.users.update_one({"id": user["user_id"]}, {"$set": {"family_id": family_id}})
    return {"message": "Joined family successfully"}

# ============== CALENDAR ROUTES ==============

@api_router.get("/calendar", response_model=List[CalendarEvent])
async def get_events(user: dict = Depends(get_current_user)):
    events = await db.calendar_events.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return events

@api_router.post("/calendar", response_model=CalendarEvent)
async def create_event(event: CalendarEvent, user: dict = Depends(get_current_user)):
    event_doc = event.model_dump()
    event_doc["family_id"] = user["family_id"]
    event_doc["created_by"] = user["user_id"]
    await db.calendar_events.insert_one(event_doc)
    del event_doc["_id"]
    del event_doc["family_id"]
    return event_doc

@api_router.put("/calendar/{event_id}")
async def update_event(event_id: str, event: CalendarEvent, user: dict = Depends(get_current_user)):
    event_doc = event.model_dump()
    await db.calendar_events.update_one({"id": event_id, "family_id": user["family_id"]}, {"$set": event_doc})
    return event_doc

@api_router.delete("/calendar/{event_id}")
async def delete_event(event_id: str, user: dict = Depends(get_current_user)):
    await db.calendar_events.delete_one({"id": event_id, "family_id": user["family_id"]})
    return {"message": "Event deleted"}

# ============== SHOPPING LIST ROUTES ==============

@api_router.get("/shopping", response_model=List[ShoppingItem])
async def get_shopping_items(user: dict = Depends(get_current_user)):
    items = await db.shopping_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/shopping", response_model=ShoppingItem)
async def create_shopping_item(item: ShoppingItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    item_doc["added_by"] = user["user_id"]
    await db.shopping_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc

@api_router.put("/shopping/{item_id}")
async def update_shopping_item(item_id: str, item: ShoppingItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.shopping_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc

@api_router.delete("/shopping/{item_id}")
async def delete_shopping_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.shopping_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}

@api_router.delete("/shopping")
async def clear_checked_items(user: dict = Depends(get_current_user)):
    await db.shopping_items.delete_many({"family_id": user["family_id"], "checked": True})
    return {"message": "Checked items cleared"}

# ============== TASKS ROUTES ==============

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(user: dict = Depends(get_current_user)):
    tasks = await db.tasks.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return tasks

@api_router.post("/tasks", response_model=Task)
async def create_task(task: Task, user: dict = Depends(get_current_user)):
    task_doc = task.model_dump()
    task_doc["family_id"] = user["family_id"]
    task_doc["created_by"] = user["user_id"]
    await db.tasks.insert_one(task_doc)
    del task_doc["_id"]
    del task_doc["family_id"]
    return task_doc

@api_router.put("/tasks/{task_id}")
async def update_task(task_id: str, task: Task, user: dict = Depends(get_current_user)):
    task_doc = task.model_dump()
    await db.tasks.update_one({"id": task_id, "family_id": user["family_id"]}, {"$set": task_doc})
    return task_doc

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    await db.tasks.delete_one({"id": task_id, "family_id": user["family_id"]})
    return {"message": "Task deleted"}

# ============== NOTES ROUTES ==============

@api_router.get("/notes", response_model=List[Note])
async def get_notes(user: dict = Depends(get_current_user)):
    notes = await db.notes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return notes

@api_router.post("/notes", response_model=Note)
async def create_note(note: Note, user: dict = Depends(get_current_user)):
    note_doc = note.model_dump()
    note_doc["family_id"] = user["family_id"]
    note_doc["created_by"] = user["user_id"]
    await db.notes.insert_one(note_doc)
    del note_doc["_id"]
    del note_doc["family_id"]
    return note_doc

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, note: Note, user: dict = Depends(get_current_user)):
    note_doc = note.model_dump()
    note_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.notes.update_one({"id": note_id, "family_id": user["family_id"]}, {"$set": note_doc})
    return note_doc

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user: dict = Depends(get_current_user)):
    await db.notes.delete_one({"id": note_id, "family_id": user["family_id"]})
    return {"message": "Note deleted"}

# ============== MESSAGES ROUTES ==============

@api_router.get("/messages", response_model=List[Message])
async def get_messages(user: dict = Depends(get_current_user)):
    messages = await db.messages.find({"family_id": user["family_id"]}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    return messages

@api_router.post("/messages", response_model=Message)
async def create_message(message: Message, user: dict = Depends(get_current_user)):
    msg_doc = message.model_dump()
    msg_doc["family_id"] = user["family_id"]
    await db.messages.insert_one(msg_doc)
    del msg_doc["_id"]
    del msg_doc["family_id"]
    return msg_doc

# ============== BUDGET ROUTES ==============

@api_router.get("/budget", response_model=List[BudgetEntry])
async def get_budget_entries(user: dict = Depends(get_current_user)):
    entries = await db.budget_entries.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return entries

@api_router.post("/budget", response_model=BudgetEntry)
async def create_budget_entry(entry: BudgetEntry, user: dict = Depends(get_current_user)):
    entry_doc = entry.model_dump()
    entry_doc["family_id"] = user["family_id"]
    entry_doc["created_by"] = user["user_id"]
    await db.budget_entries.insert_one(entry_doc)
    del entry_doc["_id"]
    del entry_doc["family_id"]
    return entry_doc

@api_router.put("/budget/{entry_id}")
async def update_budget_entry(entry_id: str, entry: BudgetEntry, user: dict = Depends(get_current_user)):
    entry_doc = entry.model_dump()
    await db.budget_entries.update_one({"id": entry_id, "family_id": user["family_id"]}, {"$set": entry_doc})
    return entry_doc

@api_router.delete("/budget/{entry_id}")
async def delete_budget_entry(entry_id: str, user: dict = Depends(get_current_user)):
    await db.budget_entries.delete_one({"id": entry_id, "family_id": user["family_id"]})
    return {"message": "Entry deleted"}

@api_router.get("/budget/summary")
async def get_budget_summary(user: dict = Depends(get_current_user)):
    entries = await db.budget_entries.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    income = sum(e["amount"] for e in entries if e["type"] == "income")
    expenses = sum(e["amount"] for e in entries if e["type"] == "expense")
    return {"income": income, "expenses": expenses, "balance": income - expenses}

# ============== MEAL PLANNER ROUTES ==============

@api_router.get("/meal-plans", response_model=List[MealPlan])
async def get_meal_plans(user: dict = Depends(get_current_user)):
    plans = await db.meal_plans.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return plans

@api_router.post("/meal-plans", response_model=MealPlan)
async def create_meal_plan(plan: MealPlan, user: dict = Depends(get_current_user)):
    plan_doc = plan.model_dump()
    plan_doc["family_id"] = user["family_id"]
    await db.meal_plans.insert_one(plan_doc)
    del plan_doc["_id"]
    del plan_doc["family_id"]
    return plan_doc

@api_router.put("/meal-plans/{plan_id}")
async def update_meal_plan(plan_id: str, plan: MealPlan, user: dict = Depends(get_current_user)):
    plan_doc = plan.model_dump()
    await db.meal_plans.update_one({"id": plan_id, "family_id": user["family_id"]}, {"$set": plan_doc})
    return plan_doc

@api_router.delete("/meal-plans/{plan_id}")
async def delete_meal_plan(plan_id: str, user: dict = Depends(get_current_user)):
    await db.meal_plans.delete_one({"id": plan_id, "family_id": user["family_id"]})
    return {"message": "Meal plan deleted"}

# ============== RECIPE BOX ROUTES ==============

@api_router.get("/recipes", response_model=List[Recipe])
async def get_recipes(user: dict = Depends(get_current_user)):
    recipes = await db.recipes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return recipes

@api_router.post("/recipes", response_model=Recipe)
async def create_recipe(recipe: Recipe, user: dict = Depends(get_current_user)):
    recipe_doc = recipe.model_dump()
    recipe_doc["family_id"] = user["family_id"]
    recipe_doc["created_by"] = user["user_id"]
    await db.recipes.insert_one(recipe_doc)
    del recipe_doc["_id"]
    del recipe_doc["family_id"]
    return recipe_doc

@api_router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    recipe = await db.recipes.find_one({"id": recipe_id, "family_id": user["family_id"]}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@api_router.put("/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, recipe: Recipe, user: dict = Depends(get_current_user)):
    recipe_doc = recipe.model_dump()
    await db.recipes.update_one({"id": recipe_id, "family_id": user["family_id"]}, {"$set": recipe_doc})
    return recipe_doc

@api_router.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    await db.recipes.delete_one({"id": recipe_id, "family_id": user["family_id"]})
    return {"message": "Recipe deleted"}

# ============== GROCERY LIST ROUTES ==============

@api_router.get("/grocery", response_model=List[GroceryItem])
async def get_grocery_items(user: dict = Depends(get_current_user)):
    items = await db.grocery_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/grocery", response_model=GroceryItem)
async def create_grocery_item(item: GroceryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    await db.grocery_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc

@api_router.put("/grocery/{item_id}")
async def update_grocery_item(item_id: str, item: GroceryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.grocery_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc

@api_router.delete("/grocery/{item_id}")
async def delete_grocery_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.grocery_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}

@api_router.delete("/grocery")
async def clear_grocery_list(user: dict = Depends(get_current_user)):
    await db.grocery_items.delete_many({"family_id": user["family_id"], "checked": True})
    return {"message": "Checked items cleared"}

# ============== CONTACTS ROUTES ==============

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(user: dict = Depends(get_current_user)):
    contacts = await db.contacts.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return contacts

@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact: Contact, user: dict = Depends(get_current_user)):
    contact_doc = contact.model_dump()
    contact_doc["family_id"] = user["family_id"]
    await db.contacts.insert_one(contact_doc)
    del contact_doc["_id"]
    del contact_doc["family_id"]
    return contact_doc

@api_router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact: Contact, user: dict = Depends(get_current_user)):
    contact_doc = contact.model_dump()
    await db.contacts.update_one({"id": contact_id, "family_id": user["family_id"]}, {"$set": contact_doc})
    return contact_doc

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, user: dict = Depends(get_current_user)):
    await db.contacts.delete_one({"id": contact_id, "family_id": user["family_id"]})
    return {"message": "Contact deleted"}

# ============== PHOTO GALLERY ROUTES ==============

@api_router.get("/photos")
async def get_photos(user: dict = Depends(get_current_user)):
    photos = await db.photos.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return photos

@api_router.post("/photos")
async def upload_photo(
    file: UploadFile = File(...),
    description: str = Form(""),
    user: dict = Depends(get_current_user)
):
    photo_id = str(uuid.uuid4())
    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{photo_id}.{extension}"
    filepath = PHOTOS_DIR / filename
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    photo_doc = {
        "id": photo_id,
        "filename": filename,
        "original_name": file.filename,
        "family_id": user["family_id"],
        "uploaded_by": user["user_id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "description": description
    }
    await db.photos.insert_one(photo_doc)
    del photo_doc["_id"]
    del photo_doc["family_id"]
    return photo_doc

@api_router.get("/photos/{photo_id}/file")
async def get_photo_file(photo_id: str):
    photo = await db.photos.find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    filepath = PHOTOS_DIR / photo["filename"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")
    
    ext = photo["filename"].split(".")[-1].lower()
    media_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")
    
    return StreamingResponse(open(filepath, "rb"), media_type=media_type)

@api_router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: str, user: dict = Depends(get_current_user)):
    photo = await db.photos.find_one({"id": photo_id, "family_id": user["family_id"]}, {"_id": 0})
    if photo:
        filepath = PHOTOS_DIR / photo["filename"]
        if filepath.exists():
            filepath.unlink()
    await db.photos.delete_one({"id": photo_id, "family_id": user["family_id"]})
    return {"message": "Photo deleted"}

# ============== PANTRY TRACKER ROUTES ==============

@api_router.get("/pantry", response_model=List[PantryItem])
async def get_pantry_items(user: dict = Depends(get_current_user)):
    items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/pantry", response_model=PantryItem)
async def create_pantry_item(item: PantryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    await db.pantry_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc

@api_router.put("/pantry/{item_id}")
async def update_pantry_item(item_id: str, item: PantryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.pantry_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc

@api_router.delete("/pantry/{item_id}")
async def delete_pantry_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.pantry_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}

@api_router.get("/pantry/barcode/{barcode}")
async def lookup_barcode(barcode: str):
    # Simple barcode lookup - returns generic product info
    # In production, this would connect to an external API like Open Food Facts
    return {
        "barcode": barcode,
        "name": f"Product {barcode[-4:]}",
        "category": "General"
    }

# ============== MEAL SUGGESTIONS ROUTES ==============

@api_router.get("/meal-suggestions")
async def get_meal_suggestions(user: dict = Depends(get_current_user)):
    # Get pantry items
    pantry_items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    pantry_names = set(item["name"].lower() for item in pantry_items)
    
    # Get all recipes
    recipes = await db.recipes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    
    suggestions = []
    for recipe in recipes:
        recipe_ingredients = [ing.lower() for ing in recipe.get("ingredients", [])]
        # Count matching ingredients
        matches = sum(1 for ing in recipe_ingredients if any(p in ing for p in pantry_names))
        total = len(recipe_ingredients) if recipe_ingredients else 1
        match_percent = (matches / total) * 100
        
        if matches > 0:
            suggestions.append({
                "recipe": recipe,
                "matches": matches,
                "total_ingredients": total,
                "match_percent": round(match_percent, 1),
                "missing": [ing for ing in recipe_ingredients if not any(p in ing for p in pantry_names)]
            })
    
    # Sort by match percentage
    suggestions.sort(key=lambda x: x["match_percent"], reverse=True)
    return suggestions[:10]

# ============== STATUS ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "Family Hub API", "status": "running", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include router and configure app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Serve static frontend files in production (Docker)
if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't serve frontend for API routes
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Try to serve the requested file
        file_path = FRONTEND_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Fall back to index.html for SPA routing
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
