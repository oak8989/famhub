from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "member"
    avatar_seed: Optional[str] = None
    family_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserInvite(BaseModel):
    email: str
    name: str
    role: str = "member"

class UserRoleUpdate(BaseModel):
    role: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class ResetMemberPassword(BaseModel):
    user_id: str


class FamilyCreate(BaseModel):
    name: str

class FamilyUpdate(BaseModel):
    name: Optional[str] = None

class FamilyPinLogin(BaseModel):
    pin: str

class QuickAddMember(BaseModel):
    name: str
    email: Optional[str] = None
    role: str = "member"

class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    date: str
    time: Optional[str] = ""
    color: Optional[str] = "#E07A5F"
    created_by: Optional[str] = None
    google_event_id: Optional[str] = None

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
    assigned_to_name: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    completed: bool = False
    created_by: Optional[str] = None

class Chore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[str] = None
    difficulty: str = "medium"
    points: int = 10
    completed: bool = False
    completed_at: Optional[str] = None
    recurring: Optional[str] = None
    created_by: Optional[str] = None

class RewardClaim(BaseModel):
    reward_id: str
    user_id: str

class Reward(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    points_required: int
    available: bool = True
    created_by: Optional[str] = None

class Note(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    color: Optional[str] = "#F2CC8F"
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BudgetEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str
    type: str
    date: str
    created_by: Optional[str] = None

class MealPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    meal_type: str
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

class FamilySettings(BaseModel):
    modules: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None
    theme: Optional[Dict[str, Any]] = None
    chore_rewards: Optional[Dict[str, Any]] = None

class ServerSettings(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]

class AIMealSuggestionRequest(BaseModel):
    use_ai: bool = True



class NOKEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    section: str = "custom"  # emergency_contacts, medical, vehicles, documents, custom
    title: str
    content: str = ""
    data: Optional[Dict[str, Any]] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    barcode: Optional[str] = None
    category: str = "Other"
    location: str = "Storage"
    quantity: int = 1
    condition: str = "Good"
    purchase_date: Optional[str] = None
    notes: Optional[str] = ""
    image: Optional[str] = None
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
