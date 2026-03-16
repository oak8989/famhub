"""
Iteration 16 - Full Application Audit Test Suite
Tests all major backend APIs: Auth, Shopping, Grocery, Pantry, Tasks, Notes, 
Budget, Calendar, Contacts, Recipes, Meals, Chores, Rewards, Settings
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testall@test.com"
TEST_PASSWORD = "test123"
TEST_NAME = "TestAll"
TEST_FAMILY = "TestAll Family"

# Alternative test account - test@bulk.com works (bughunt@test.com was rate limited)
EXISTING_EMAIL = "test@bulk.com"
EXISTING_PASSWORD = "test123"


class TestHealthCheck:
    """Verify backend is running"""
    
    def test_api_root(self):
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        print(f"API is running: v{data.get('version')}")
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Health check passed")


class TestAuthFlow:
    """Test authentication endpoints"""
    
    def test_register_new_user(self):
        """Register a new user with family"""
        unique_email = f"test_audit_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": TEST_NAME,
            "email": unique_email,
            "password": TEST_PASSWORD,
            "family_name": "Audit Test Family"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token returned"
        assert "user" in data, "No user returned"
        assert data["user"]["email"] == unique_email
        assert data["user"]["role"] == "owner"
        assert "family_pin" in data, "No family_pin returned"
        print(f"Registration successful: {unique_email}")
    
    def test_login_with_email(self):
        """Login with existing email/password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_EMAIL,
            "password": EXISTING_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token returned"
        assert "user" in data, "No user returned"
        print(f"Login successful for {EXISTING_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_EMAIL,
            "password": "wrongpassword123"
        })
        assert response.status_code == 401
        print("Invalid credentials correctly rejected")
    
    def test_forgot_password_endpoint(self):
        """Forgot password endpoint returns message"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": EXISTING_EMAIL
        })
        assert response.status_code == 200, f"Forgot password failed: {response.text}"
        data = response.json()
        assert "message" in data
        print("Forgot password endpoint works")
    
    def test_forgot_password_requires_email(self):
        """Forgot password returns 400 without email"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={})
        assert response.status_code == 400
        print("Forgot password correctly requires email")


# Global token cache to avoid re-login on every test
_cached_token = None

@pytest.fixture(scope="session")
def auth_token():
    """Get authentication token for protected routes - cached for session"""
    global _cached_token
    if _cached_token:
        return _cached_token
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": EXISTING_EMAIL,
        "password": EXISTING_PASSWORD
    })
    if response.status_code != 200:
        pytest.fail(f"Login failed: {response.text}")
    _cached_token = response.json()["token"]
    return _cached_token


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDashboard:
    """Test dashboard-related endpoints"""
    
    def test_get_me(self, auth_headers):
        """Get current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "user_id" in data
        print(f"Got user info: {data.get('name', data.get('email', 'Unknown'))}")


class TestShoppingList:
    """Test shopping list CRUD"""
    
    def test_get_shopping_items(self, auth_headers):
        """Get shopping list"""
        response = requests.get(f"{BASE_URL}/api/shopping", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Shopping list has {len(response.json())} items")
    
    def test_add_shopping_item(self, auth_headers):
        """Add item to shopping list"""
        response = requests.post(f"{BASE_URL}/api/shopping", headers=auth_headers, json={
            "name": "TEST_Audit_Milk",
            "quantity": "2",
            "category": "Dairy"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Audit_Milk"
        print(f"Added shopping item: {data['id']}")
        return data["id"]
    
    def test_update_shopping_item(self, auth_headers):
        """Update shopping item (check/uncheck)"""
        # First add an item
        add_resp = requests.post(f"{BASE_URL}/api/shopping", headers=auth_headers, json={
            "name": "TEST_Update_Item",
            "quantity": "1"
        })
        item_id = add_resp.json()["id"]
        
        # Update it
        response = requests.put(f"{BASE_URL}/api/shopping/{item_id}", headers=auth_headers, json={
            "name": "TEST_Update_Item",
            "quantity": "3",
            "checked": True
        })
        assert response.status_code == 200
        print("Shopping item updated")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/shopping/{item_id}", headers=auth_headers)
    
    def test_delete_shopping_item(self, auth_headers):
        """Delete shopping item"""
        # First add an item
        add_resp = requests.post(f"{BASE_URL}/api/shopping", headers=auth_headers, json={
            "name": "TEST_Delete_Item"
        })
        item_id = add_resp.json()["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/shopping/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Shopping item deleted")


class TestGroceryList:
    """Test grocery list CRUD"""
    
    def test_get_grocery_items(self, auth_headers):
        """Get grocery list"""
        response = requests.get(f"{BASE_URL}/api/grocery", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Grocery list has {len(response.json())} items")
    
    def test_add_grocery_item(self, auth_headers):
        """Add item to grocery list"""
        response = requests.post(f"{BASE_URL}/api/grocery", headers=auth_headers, json={
            "name": "TEST_Audit_Bread",
            "quantity": "1"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Audit_Bread"
        print(f"Added grocery item: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/grocery/{data['id']}", headers=auth_headers)
    
    def test_delete_grocery_item(self, auth_headers):
        """Delete grocery item"""
        add_resp = requests.post(f"{BASE_URL}/api/grocery", headers=auth_headers, json={
            "name": "TEST_Delete_Grocery"
        })
        item_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/grocery/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Grocery item deleted")


class TestPantry:
    """Test pantry CRUD including bulk scan"""
    
    def test_get_pantry_items(self, auth_headers):
        """Get pantry items"""
        response = requests.get(f"{BASE_URL}/api/pantry", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Pantry has {len(response.json())} items")
    
    def test_add_pantry_item(self, auth_headers):
        """Add item to pantry"""
        response = requests.post(f"{BASE_URL}/api/pantry", headers=auth_headers, json={
            "name": "TEST_Audit_Rice",
            "quantity": 5,
            "unit": "kg",
            "category": "Grains"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Audit_Rice"
        print(f"Added pantry item: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/pantry/{data['id']}", headers=auth_headers)
    
    def test_bulk_add_pantry_items(self, auth_headers):
        """Test bulk add endpoint"""
        response = requests.post(f"{BASE_URL}/api/pantry/bulk-add", headers=auth_headers, json=[
            {"name": "TEST_Bulk_Item1", "quantity": 1},
            {"name": "TEST_Bulk_Item2", "quantity": 2}
        ])
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["count"] == 2
        print(f"Bulk added {data['count']} items")
        
        # Cleanup
        for item in data.get("items", []):
            requests.delete(f"{BASE_URL}/api/pantry/{item['id']}", headers=auth_headers)
    
    def test_delete_pantry_item(self, auth_headers):
        """Delete pantry item"""
        add_resp = requests.post(f"{BASE_URL}/api/pantry", headers=auth_headers, json={
            "name": "TEST_Delete_Pantry",
            "quantity": 1
        })
        item_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/pantry/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Pantry item deleted")


class TestTasks:
    """Test tasks CRUD"""
    
    def test_get_tasks(self, auth_headers):
        """Get all tasks"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Tasks list has {len(response.json())} items")
    
    def test_create_task(self, auth_headers):
        """Create a task"""
        response = requests.post(f"{BASE_URL}/api/tasks", headers=auth_headers, json={
            "title": "TEST_Audit_Task",
            "description": "Test task description",
            "priority": "high"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["title"] == "TEST_Audit_Task"
        print(f"Created task: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tasks/{data['id']}", headers=auth_headers)
    
    def test_complete_task(self, auth_headers):
        """Update task to completed"""
        add_resp = requests.post(f"{BASE_URL}/api/tasks", headers=auth_headers, json={
            "title": "TEST_Complete_Task"
        })
        task = add_resp.json()
        
        response = requests.put(f"{BASE_URL}/api/tasks/{task['id']}", headers=auth_headers, json={
            "title": "TEST_Complete_Task",
            "completed": True
        })
        assert response.status_code == 200
        print("Task completed")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tasks/{task['id']}", headers=auth_headers)
    
    def test_delete_task(self, auth_headers):
        """Delete task"""
        add_resp = requests.post(f"{BASE_URL}/api/tasks", headers=auth_headers, json={
            "title": "TEST_Delete_Task"
        })
        task_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Task deleted")


class TestNotes:
    """Test notes CRUD"""
    
    def test_get_notes(self, auth_headers):
        """Get all notes"""
        response = requests.get(f"{BASE_URL}/api/notes", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Notes list has {len(response.json())} items")
    
    def test_create_note(self, auth_headers):
        """Create a note"""
        response = requests.post(f"{BASE_URL}/api/notes", headers=auth_headers, json={
            "title": "TEST_Audit_Note",
            "content": "Test note content"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["title"] == "TEST_Audit_Note"
        print(f"Created note: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/notes/{data['id']}", headers=auth_headers)
    
    def test_update_note(self, auth_headers):
        """Update note"""
        add_resp = requests.post(f"{BASE_URL}/api/notes", headers=auth_headers, json={
            "title": "TEST_Update_Note",
            "content": "Original content"
        })
        note = add_resp.json()
        
        response = requests.put(f"{BASE_URL}/api/notes/{note['id']}", headers=auth_headers, json={
            "title": "TEST_Update_Note",
            "content": "Updated content"
        })
        assert response.status_code == 200
        assert response.json()["content"] == "Updated content"
        print("Note updated")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/notes/{note['id']}", headers=auth_headers)
    
    def test_delete_note(self, auth_headers):
        """Delete note"""
        add_resp = requests.post(f"{BASE_URL}/api/notes", headers=auth_headers, json={
            "title": "TEST_Delete_Note",
            "content": "To delete"
        })
        note_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/notes/{note_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Note deleted")


class TestBudget:
    """Test budget CRUD - uses /api/budget not /api/budget/entries"""
    
    def test_get_budget_entries(self, auth_headers):
        """Get all budget entries"""
        response = requests.get(f"{BASE_URL}/api/budget", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Budget has {len(response.json())} entries")
    
    def test_create_budget_entry(self, auth_headers):
        """Create a budget entry (expense)"""
        response = requests.post(f"{BASE_URL}/api/budget", headers=auth_headers, json={
            "description": "TEST_Audit_Expense",
            "amount": 50.00,
            "category": "Food",
            "type": "expense",
            "date": "2026-01-15"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["description"] == "TEST_Audit_Expense"
        print(f"Created budget entry: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/budget/{data['id']}", headers=auth_headers)
    
    def test_budget_summary(self, auth_headers):
        """Get budget summary"""
        response = requests.get(f"{BASE_URL}/api/budget/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "balance" in data
        print(f"Budget balance: {data['balance']}")
    
    def test_delete_budget_entry(self, auth_headers):
        """Delete budget entry"""
        add_resp = requests.post(f"{BASE_URL}/api/budget", headers=auth_headers, json={
            "description": "TEST_Delete_Budget",
            "amount": 10.00,
            "category": "Other",
            "type": "expense",
            "date": "2026-01-15"
        })
        entry_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/budget/{entry_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Budget entry deleted")


class TestCalendar:
    """Test calendar CRUD - uses /api/calendar not /api/calendar/events"""
    
    def test_get_calendar_events(self, auth_headers):
        """Get all calendar events"""
        response = requests.get(f"{BASE_URL}/api/calendar", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Calendar has {len(response.json())} events")
    
    def test_create_calendar_event(self, auth_headers):
        """Create a calendar event"""
        response = requests.post(f"{BASE_URL}/api/calendar", headers=auth_headers, json={
            "title": "TEST_Audit_Event",
            "description": "Test event description",
            "date": "2026-02-01",
            "time": "10:00"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["title"] == "TEST_Audit_Event"
        print(f"Created calendar event: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/calendar/{data['id']}", headers=auth_headers)
    
    def test_delete_calendar_event(self, auth_headers):
        """Delete calendar event"""
        add_resp = requests.post(f"{BASE_URL}/api/calendar", headers=auth_headers, json={
            "title": "TEST_Delete_Event",
            "date": "2026-02-02"
        })
        event_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/calendar/{event_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Calendar event deleted")


class TestContacts:
    """Test contacts CRUD"""
    
    def test_get_contacts(self, auth_headers):
        """Get all contacts"""
        response = requests.get(f"{BASE_URL}/api/contacts", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Contacts list has {len(response.json())} items")
    
    def test_create_contact(self, auth_headers):
        """Create a contact"""
        response = requests.post(f"{BASE_URL}/api/contacts", headers=auth_headers, json={
            "name": "TEST_Audit_Contact",
            "relationship": "Friend",
            "phone": "555-1234",
            "email": "test@example.com"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Audit_Contact"
        print(f"Created contact: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/contacts/{data['id']}", headers=auth_headers)
    
    def test_update_contact(self, auth_headers):
        """Update contact"""
        add_resp = requests.post(f"{BASE_URL}/api/contacts", headers=auth_headers, json={
            "name": "TEST_Update_Contact"
        })
        contact = add_resp.json()
        
        response = requests.put(f"{BASE_URL}/api/contacts/{contact['id']}", headers=auth_headers, json={
            "name": "TEST_Update_Contact",
            "phone": "555-9999"
        })
        assert response.status_code == 200
        print("Contact updated")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/contacts/{contact['id']}", headers=auth_headers)
    
    def test_delete_contact(self, auth_headers):
        """Delete contact"""
        add_resp = requests.post(f"{BASE_URL}/api/contacts", headers=auth_headers, json={
            "name": "TEST_Delete_Contact"
        })
        contact_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/contacts/{contact_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Contact deleted")


class TestRecipes:
    """Test recipes CRUD - uses 'name' field not 'title'"""
    
    def test_get_recipes(self, auth_headers):
        """Get all recipes"""
        response = requests.get(f"{BASE_URL}/api/recipes", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Recipes list has {len(response.json())} items")
    
    def test_create_recipe(self, auth_headers):
        """Create a recipe"""
        response = requests.post(f"{BASE_URL}/api/recipes", headers=auth_headers, json={
            "name": "TEST_Audit_Recipe",
            "description": "A test recipe",
            "ingredients": ["2 cups flour", "1 cup sugar", "1 egg"],
            "instructions": ["Mix dry ingredients", "Add wet ingredients", "Bake at 350F"],
            "prep_time": "15m",
            "cook_time": "30m",
            "servings": 4,
            "category": "Desserts"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Audit_Recipe"
        print(f"Created recipe: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{data['id']}", headers=auth_headers)
    
    def test_get_single_recipe(self, auth_headers):
        """Get a single recipe by ID"""
        # First create a recipe
        add_resp = requests.post(f"{BASE_URL}/api/recipes", headers=auth_headers, json={
            "name": "TEST_Get_Recipe",
            "ingredients": ["item1"],
            "instructions": ["step1"]
        })
        recipe_id = add_resp.json()["id"]
        
        # Get it
        response = requests.get(f"{BASE_URL}/api/recipes/{recipe_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "TEST_Get_Recipe"
        print("Got single recipe")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{recipe_id}", headers=auth_headers)
    
    def test_delete_recipe(self, auth_headers):
        """Delete recipe"""
        add_resp = requests.post(f"{BASE_URL}/api/recipes", headers=auth_headers, json={
            "name": "TEST_Delete_Recipe",
            "ingredients": ["item"],
            "instructions": ["step"]
        })
        recipe_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/recipes/{recipe_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Recipe deleted")


class TestMealPlanner:
    """Test meal planner CRUD - uses /api/meals not /api/meal-plans"""
    
    def test_get_meals(self, auth_headers):
        """Get all meal plans"""
        response = requests.get(f"{BASE_URL}/api/meals", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Meal plans has {len(response.json())} items")
    
    def test_create_meal_plan(self, auth_headers):
        """Create a meal plan"""
        response = requests.post(f"{BASE_URL}/api/meals", headers=auth_headers, json={
            "date": "2026-01-20",
            "meal_type": "dinner",
            "recipe_name": "TEST_Audit_Meal"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["recipe_name"] == "TEST_Audit_Meal"
        print(f"Created meal plan: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/meals/{data['id']}", headers=auth_headers)
    
    def test_delete_meal_plan(self, auth_headers):
        """Delete meal plan"""
        add_resp = requests.post(f"{BASE_URL}/api/meals", headers=auth_headers, json={
            "date": "2026-01-21",
            "meal_type": "lunch",
            "recipe_name": "TEST_Delete_Meal"
        })
        plan_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/meals/{plan_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Meal plan deleted")


class TestChores:
    """Test chores CRUD"""
    
    def test_get_chores(self, auth_headers):
        """Get all chores"""
        response = requests.get(f"{BASE_URL}/api/chores", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Chores list has {len(response.json())} items")
    
    def test_create_chore(self, auth_headers):
        """Create a chore"""
        response = requests.post(f"{BASE_URL}/api/chores", headers=auth_headers, json={
            "title": "TEST_Audit_Chore",
            "description": "A test chore",
            "difficulty": "easy"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["title"] == "TEST_Audit_Chore"
        assert data["points"] == 5  # easy = 5 points
        print(f"Created chore: {data['id']} with {data['points']} points")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/chores/{data['id']}", headers=auth_headers)
    
    def test_complete_chore(self, auth_headers):
        """Complete a chore and earn points"""
        add_resp = requests.post(f"{BASE_URL}/api/chores", headers=auth_headers, json={
            "title": "TEST_Complete_Chore",
            "difficulty": "medium"
        })
        chore = add_resp.json()
        
        response = requests.post(f"{BASE_URL}/api/chores/{chore['id']}/complete", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "points_earned" in data
        print(f"Completed chore, earned {data['points_earned']} points")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/chores/{chore['id']}", headers=auth_headers)
    
    def test_delete_chore(self, auth_headers):
        """Delete chore"""
        add_resp = requests.post(f"{BASE_URL}/api/chores", headers=auth_headers, json={
            "title": "TEST_Delete_Chore"
        })
        chore_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/chores/{chore_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Chore deleted")


class TestRewards:
    """Test rewards CRUD - uses 'name' and 'points_required' fields"""
    
    def test_get_rewards(self, auth_headers):
        """Get all rewards"""
        response = requests.get(f"{BASE_URL}/api/rewards", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Rewards list has {len(response.json())} items")
    
    def test_create_reward(self, auth_headers):
        """Create a reward"""
        response = requests.post(f"{BASE_URL}/api/rewards", headers=auth_headers, json={
            "name": "TEST_Audit_Reward",
            "description": "A test reward",
            "points_required": 50
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Audit_Reward"
        assert data["points_required"] == 50
        print(f"Created reward: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rewards/{data['id']}", headers=auth_headers)
    
    def test_get_leaderboard(self, auth_headers):
        """Get leaderboard"""
        response = requests.get(f"{BASE_URL}/api/leaderboard", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Leaderboard has {len(response.json())} members")
    
    def test_get_reward_claims(self, auth_headers):
        """Get reward claim history"""
        response = requests.get(f"{BASE_URL}/api/reward-claims", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Reward claims: {len(response.json())} records")
    
    def test_delete_reward(self, auth_headers):
        """Delete reward"""
        add_resp = requests.post(f"{BASE_URL}/api/rewards", headers=auth_headers, json={
            "name": "TEST_Delete_Reward",
            "points_required": 10
        })
        reward_id = add_resp.json()["id"]
        
        response = requests.delete(f"{BASE_URL}/api/rewards/{reward_id}", headers=auth_headers)
        assert response.status_code == 200
        print("Reward deleted")


class TestSettings:
    """Test settings endpoints"""
    
    def test_get_family(self, auth_headers):
        """Get family info"""
        response = requests.get(f"{BASE_URL}/api/family", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "id" in data
        print(f"Got family info")
    
    def test_get_family_members(self, auth_headers):
        """Get family members"""
        response = requests.get(f"{BASE_URL}/api/family/members", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Family has {len(response.json())} members")
    
    def test_get_settings(self, auth_headers):
        """Get settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        assert response.status_code == 200
        print("Settings retrieved")
    
    def test_get_server_settings(self, auth_headers):
        """Get server settings (for owner)"""
        response = requests.get(f"{BASE_URL}/api/settings/server", headers=auth_headers)
        # May return 403 if not owner, or 200 if owner
        assert response.status_code in [200, 403]
        print(f"Server settings response: {response.status_code}")


class TestSuggestions:
    """Test meal suggestions"""
    
    def test_get_suggestions(self, auth_headers):
        """Get meal suggestions"""
        response = requests.get(f"{BASE_URL}/api/suggestions", headers=auth_headers)
        assert response.status_code == 200
        print(f"Suggestions retrieved")


class TestCleanup:
    """Clean up any leftover test data"""
    
    def test_cleanup_test_items(self, auth_headers):
        """Delete any remaining TEST_ prefixed items"""
        cleanup_count = 0
        
        # Clean shopping
        resp = requests.get(f"{BASE_URL}/api/shopping", headers=auth_headers)
        for item in resp.json():
            if item.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/shopping/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean grocery
        resp = requests.get(f"{BASE_URL}/api/grocery", headers=auth_headers)
        for item in resp.json():
            if item.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/grocery/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean pantry
        resp = requests.get(f"{BASE_URL}/api/pantry", headers=auth_headers)
        for item in resp.json():
            if item.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/pantry/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean tasks
        resp = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers)
        for item in resp.json():
            if item.get("title", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/tasks/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean notes
        resp = requests.get(f"{BASE_URL}/api/notes", headers=auth_headers)
        for item in resp.json():
            if item.get("title", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/notes/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean budget
        resp = requests.get(f"{BASE_URL}/api/budget", headers=auth_headers)
        for item in resp.json():
            if item.get("description", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/budget/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean calendar
        resp = requests.get(f"{BASE_URL}/api/calendar", headers=auth_headers)
        for item in resp.json():
            if item.get("title", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/calendar/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean contacts
        resp = requests.get(f"{BASE_URL}/api/contacts", headers=auth_headers)
        for item in resp.json():
            if item.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/contacts/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean recipes
        resp = requests.get(f"{BASE_URL}/api/recipes", headers=auth_headers)
        for item in resp.json():
            if item.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/recipes/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean meals
        resp = requests.get(f"{BASE_URL}/api/meals", headers=auth_headers)
        for item in resp.json():
            if item.get("recipe_name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/meals/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean chores
        resp = requests.get(f"{BASE_URL}/api/chores", headers=auth_headers)
        for item in resp.json():
            if item.get("title", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/chores/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        # Clean rewards
        resp = requests.get(f"{BASE_URL}/api/rewards", headers=auth_headers)
        for item in resp.json():
            if item.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/rewards/{item['id']}", headers=auth_headers)
                cleanup_count += 1
        
        print(f"Cleaned up {cleanup_count} test items")
