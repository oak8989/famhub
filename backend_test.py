import requests
import sys
import json
from datetime import datetime, timedelta

class FamilyHubTester:
    def __init__(self, base_url="https://hub-staging-3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.family_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_api_status(self):
        """Test API root endpoint"""
        success, response = self.run_test("API Status", "GET", "", 200)
        return success

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "TestPass123!",
            "role": "member"
        }
        
        success, response = self.run_test("User Registration", "POST", "auth/register", 200, user_data)
        if success:
            self.test_email = user_data["email"]
            self.test_password = user_data["password"]
        return success

    def test_user_login(self):
        """Test user login"""
        if not hasattr(self, 'test_email'):
            self.log_test("User Login", False, "No registered user to login")
            return False
            
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
        return success

    def test_create_family(self):
        """Test family creation"""
        if not self.token:
            self.log_test("Create Family", False, "No auth token")
            return False
            
        family_data = {
            "name": f"Test Family {datetime.now().strftime('%H%M%S')}",
            "pin": "1234"
        }
        
        success, response = self.run_test("Create Family", "POST", "family/create", 200, family_data)
        if success:
            self.family_id = response.get('id')
            self.family_pin = family_data["pin"]
        return success

    def test_pin_login(self):
        """Test family PIN login"""
        if not hasattr(self, 'family_pin'):
            self.log_test("PIN Login", False, "No family PIN available")
            return False
            
        pin_data = {"pin": self.family_pin}
        success, response = self.run_test("PIN Login", "POST", "auth/pin-login", 200, pin_data)
        return success

    def test_calendar_operations(self):
        """Test calendar CRUD operations"""
        if not self.token:
            return False
            
        # Create event
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "10:00",
            "color": "#E07A5F"
        }
        
        success, response = self.run_test("Create Calendar Event", "POST", "calendar", 200, event_data)
        if not success:
            return False
            
        event_id = response.get('id')
        
        # Get events
        success, _ = self.run_test("Get Calendar Events", "GET", "calendar", 200)
        if not success:
            return False
            
        # Delete event
        if event_id:
            success, _ = self.run_test("Delete Calendar Event", "DELETE", f"calendar/{event_id}", 200)
        
        return success

    def test_shopping_operations(self):
        """Test shopping list CRUD operations"""
        if not self.token:
            return False
            
        # Create item
        item_data = {
            "name": "Test Item",
            "quantity": "2",
            "category": "Groceries"
        }
        
        success, response = self.run_test("Create Shopping Item", "POST", "shopping", 200, item_data)
        if not success:
            return False
            
        item_id = response.get('id')
        
        # Get items
        success, _ = self.run_test("Get Shopping Items", "GET", "shopping", 200)
        if not success:
            return False
            
        # Update item (check it)
        if item_id:
            update_data = {**item_data, "checked": True}
            success, _ = self.run_test("Update Shopping Item", "PUT", f"shopping/{item_id}", 200, update_data)
            
        return success

    def test_tasks_operations(self):
        """Test tasks CRUD operations"""
        if not self.token:
            return False
            
        # Create task
        task_data = {
            "title": "Test Task",
            "description": "Test task description",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        success, response = self.run_test("Create Task", "POST", "tasks", 200, task_data)
        if not success:
            return False
            
        task_id = response.get('id')
        
        # Get tasks
        success, _ = self.run_test("Get Tasks", "GET", "tasks", 200)
        if not success:
            return False
            
        # Complete task
        if task_id:
            update_data = {**task_data, "completed": True}
            success, _ = self.run_test("Complete Task", "PUT", f"tasks/{task_id}", 200, update_data)
            
        return success

    def test_notes_operations(self):
        """Test notes CRUD operations"""
        if not self.token:
            return False
            
        # Create note
        note_data = {
            "title": "Test Note",
            "content": "This is a test note content",
            "color": "#F2CC8F"
        }
        
        success, response = self.run_test("Create Note", "POST", "notes", 200, note_data)
        if not success:
            return False
            
        note_id = response.get('id')
        
        # Get notes
        success, _ = self.run_test("Get Notes", "GET", "notes", 200)
        if not success:
            return False
            
        # Update note
        if note_id:
            update_data = {**note_data, "content": "Updated content"}
            success, _ = self.run_test("Update Note", "PUT", f"notes/{note_id}", 200, update_data)
            
        return success

    def test_messages_operations(self):
        """Test messages operations"""
        if not self.token:
            return False
            
        # Send message
        message_data = {
            "content": "Test message",
            "sender_id": self.user_id or "test-user",
            "sender_name": "Test User"
        }
        
        success, response = self.run_test("Send Message", "POST", "messages", 200, message_data)
        if not success:
            return False
            
        # Get messages
        success, _ = self.run_test("Get Messages", "GET", "messages", 200)
        return success

    def test_budget_operations(self):
        """Test budget CRUD operations"""
        if not self.token:
            return False
            
        # Create budget entry
        entry_data = {
            "description": "Test Income",
            "amount": 1000.0,
            "category": "Salary",
            "type": "income",
            "date": datetime.now().strftime('%Y-%m-%d')
        }
        
        success, response = self.run_test("Create Budget Entry", "POST", "budget", 200, entry_data)
        if not success:
            return False
            
        # Get budget entries
        success, _ = self.run_test("Get Budget Entries", "GET", "budget", 200)
        if not success:
            return False
            
        # Get budget summary
        success, _ = self.run_test("Get Budget Summary", "GET", "budget/summary", 200)
        return success

    def test_recipes_operations(self):
        """Test recipes CRUD operations"""
        if not self.token:
            return False
            
        # Create recipe
        recipe_data = {
            "name": "Test Recipe",
            "description": "A test recipe",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "prep_time": "15 mins",
            "cook_time": "30 mins",
            "servings": 4,
            "category": "Main Course"
        }
        
        success, response = self.run_test("Create Recipe", "POST", "recipes", 200, recipe_data)
        if not success:
            return False
            
        recipe_id = response.get('id')
        
        # Get recipes
        success, _ = self.run_test("Get Recipes", "GET", "recipes", 200)
        if not success:
            return False
            
        # Get single recipe
        if recipe_id:
            success, _ = self.run_test("Get Single Recipe", "GET", f"recipes/{recipe_id}", 200)
            
        return success

    def test_pantry_operations(self):
        """Test pantry CRUD operations"""
        if not self.token:
            return False
            
        # Create pantry item
        item_data = {
            "name": "Test Pantry Item",
            "barcode": "1234567890",
            "quantity": 5,
            "unit": "pcs",
            "category": "Canned Goods",
            "expiry_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        }
        
        success, response = self.run_test("Create Pantry Item", "POST", "pantry", 200, item_data)
        if not success:
            return False
            
        # Get pantry items
        success, _ = self.run_test("Get Pantry Items", "GET", "pantry", 200)
        if not success:
            return False
            
        # Test barcode lookup
        success, _ = self.run_test("Barcode Lookup", "GET", "pantry/barcode/1234567890", 200)
        return success

    def test_meal_suggestions(self):
        """Test meal suggestions"""
        if not self.token:
            return False
            
        success, _ = self.run_test("Get Meal Suggestions", "GET", "meal-suggestions", 200)
        return success

    def test_other_modules(self):
        """Test other module endpoints"""
        if not self.token:
            return False
            
        # Test meal plans
        success, _ = self.run_test("Get Meal Plans", "GET", "meal-plans", 200)
        if not success:
            return False
            
        # Test grocery list
        success, _ = self.run_test("Get Grocery Items", "GET", "grocery", 200)
        if not success:
            return False
            
        # Test contacts
        success, _ = self.run_test("Get Contacts", "GET", "contacts", 200)
        if not success:
            return False
            
        # Test photos
        success, _ = self.run_test("Get Photos", "GET", "photos", 200)
        return success

def main():
    print("🏠 Starting Family Hub API Tests...")
    print("=" * 50)
    
    tester = FamilyHubTester()
    
    # Run all tests
    tests = [
        tester.test_api_status,
        tester.test_user_registration,
        tester.test_user_login,
        tester.test_create_family,
        tester.test_pin_login,
        tester.test_calendar_operations,
        tester.test_shopping_operations,
        tester.test_tasks_operations,
        tester.test_notes_operations,
        tester.test_messages_operations,
        tester.test_budget_operations,
        tester.test_recipes_operations,
        tester.test_pantry_operations,
        tester.test_meal_suggestions,
        tester.test_other_modules
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__} - Exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Tests Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())