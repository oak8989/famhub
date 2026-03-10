"""
Test iteration 10 features for Family Hub:
1. Push notifications backend (pywebpush) - /api/notifications/vapid-key, subscribe, unsubscribe
2. Data import/restore with merge mode - /api/import/data, /api/export/data
3. Enhanced AI pantry-based meal suggestions - /api/suggestions
Plus regression tests on all existing CRUD endpoints
"""
import pytest
import requests
import os
import uuid
import json
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_headers(api_client):
    """Register a new user and get fresh JWT token"""
    user_email = f"test_iter10_{uuid.uuid4().hex[:8]}@test.com"
    user_password = "Test123456!"
    
    # Register user with family
    reg_resp = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Iteration 10 Test User",
        "email": user_email,
        "password": user_password,
        "family_name": "Iteration10TestFamily"
    })
    assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
    
    data = reg_resp.json()
    token = data["token"]
    family_id = data["user"].get("family_id")
    
    print(f"[PASS] Created test user: {user_email}")
    print(f"[PASS] Family ID: {family_id}")
    
    return {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json",
        "family_id": family_id,
        "user_id": data["user"].get("id")
    }


# ===== HEALTH & BASIC API TESTS =====
class TestHealthAndBasic:
    """Basic API health and status tests"""
    
    def test_health_check(self, api_client):
        """Test /api/health returns healthy status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("[PASS] Health check passed")
    
    def test_root_api(self, api_client):
        """Test /api/ returns API info"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
        print(f"[PASS] API version: {data.get('version')}")


# ===== AUTH TESTS =====
class TestAuth:
    """Authentication tests"""
    
    def test_register_new_user(self, api_client):
        """Test POST /api/auth/register with push_test user"""
        user_email = f"push_test_{uuid.uuid4().hex[:8]}@test.com"
        response = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Push Test User",
            "email": user_email,
            "password": "test123",
            "family_name": "PushFamily"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == user_email
        print(f"[PASS] Registered user: {user_email}")
    
    def test_login_existing_user(self, api_client):
        """Test POST /api/auth/login with test@test.com"""
        # This tests the existing test user if it exists
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        # May succeed or fail based on whether test user exists
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            print("[PASS] Login successful for test@test.com")
        else:
            # Create a new user for login test
            user_email = f"login_test_{uuid.uuid4().hex[:8]}@test.com"
            api_client.post(f"{BASE_URL}/api/auth/register", json={
                "name": "Login Test",
                "email": user_email,
                "password": "test123",
                "family_name": "LoginTestFamily"
            })
            response = api_client.post(f"{BASE_URL}/api/auth/login", json={
                "email": user_email,
                "password": "test123"
            })
            assert response.status_code == 200
            print(f"[PASS] Login successful for new user {user_email}")


# ===== NEW FEATURE: PUSH NOTIFICATIONS =====
class TestPushNotifications:
    """Push notification endpoint tests - NEW FEATURE"""
    
    def test_get_vapid_key(self, api_client):
        """Test GET /api/notifications/vapid-key returns public_key"""
        response = api_client.get(f"{BASE_URL}/api/notifications/vapid-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 50  # VAPID keys are typically 87 chars
        print(f"[PASS] VAPID key received: {data['public_key'][:20]}...")
    
    def test_push_subscribe(self, api_client, auth_headers):
        """Test POST /api/notifications/subscribe"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        response = api_client.post(f"{BASE_URL}/api/notifications/subscribe", json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {
                "p256dh": "test_p256dh_key_value_for_testing",
                "auth": "test_auth_key"
            }
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"[PASS] Push subscribe: {data.get('message')}")
    
    def test_push_unsubscribe(self, api_client, auth_headers):
        """Test DELETE /api/notifications/unsubscribe"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        response = api_client.delete(f"{BASE_URL}/api/notifications/unsubscribe", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"[PASS] Push unsubscribe: {data.get('message')}")


# ===== NEW FEATURE: DATA EXPORT/IMPORT =====
class TestDataExportImport:
    """Data export and import tests - NEW FEATURE"""
    
    def test_export_data(self, api_client, auth_headers):
        """Test GET /api/export/data returns JSON with version field"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        response = api_client.get(f"{BASE_URL}/api/export/data", headers=headers)
        assert response.status_code == 200
        
        # Response is a streaming JSON file
        data = response.json()
        assert "version" in data
        assert "exported_at" in data
        assert "exported_by" in data
        assert "family" in data
        assert "members" in data
        print(f"[PASS] Export data: version={data.get('version')}, exported_at={data.get('exported_at')[:10]}")
    
    def test_import_data_new_items(self, api_client, auth_headers):
        """Test POST /api/import/data imports new items"""
        token = auth_headers["Authorization"]
        
        # Create a test import file with unique ID
        unique_id = f"import-test-{uuid.uuid4().hex[:8]}"
        import_data = {
            "version": "2.2.0",
            "calendar_events": [
                {
                    "id": unique_id,
                    "title": "Test Import Event",
                    "date": "2026-05-01",
                    "time": "14:00",
                    "color": "blue"
                }
            ]
        }
        
        # Use requests directly for file upload (session has content-type issues with multipart)
        files = {"file": ("backup.json", json.dumps(import_data), "application/json")}
        
        response = requests.post(
            f"{BASE_URL}/api/import/data",
            files=files,
            headers={"Authorization": token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_imported" in data
        assert data["total_imported"] >= 1
        print(f"[PASS] Import data: imported={data.get('total_imported')}, skipped={data.get('total_skipped')}")
    
    def test_import_data_merge_skips_duplicates(self, api_client, auth_headers):
        """Test POST /api/import/data with duplicate items skips them (merge behavior)"""
        token = auth_headers["Authorization"]
        
        # Use a fixed ID for this test
        fixed_id = f"import-merge-test-{uuid.uuid4().hex[:6]}"
        
        import_data = {
            "version": "2.2.0",
            "calendar_events": [
                {
                    "id": fixed_id,
                    "title": "Merge Test Event",
                    "date": "2026-05-15",
                    "time": "10:00",
                    "color": "green"
                }
            ]
        }
        
        # First import - should import 1 item
        files1 = {"file": ("backup.json", json.dumps(import_data), "application/json")}
        response1 = requests.post(
            f"{BASE_URL}/api/import/data",
            files=files1,
            headers={"Authorization": token}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        first_imported = data1.get("total_imported", 0)
        first_skipped = data1.get("total_skipped", 0)
        print(f"[INFO] First import: imported={first_imported}, skipped={first_skipped}")
        
        # Second import with same ID - should skip (merge behavior)
        files2 = {"file": ("backup.json", json.dumps(import_data), "application/json")}
        response2 = requests.post(
            f"{BASE_URL}/api/import/data",
            files=files2,
            headers={"Authorization": token}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        second_imported = data2.get("total_imported", 0)
        second_skipped = data2.get("total_skipped", 0)
        
        # Second import should have more skipped items
        assert second_skipped >= 1, f"Expected at least 1 skipped item, got {second_skipped}"
        print(f"[PASS] Merge behavior: 2nd import - imported={second_imported}, skipped={second_skipped}")
    
    def test_export_csv_module(self, api_client, auth_headers):
        """Test GET /api/export/csv/{module} returns CSV"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # Test calendar export
        response = api_client.get(f"{BASE_URL}/api/export/csv/calendar", headers=headers)
        assert response.status_code == 200
        # Response should contain CSV header
        content = response.text
        assert "id" in content or "title" in content
        print(f"[PASS] CSV export for calendar module successful")


# ===== SUGGESTIONS (Enhanced AI) =====
class TestSuggestions:
    """Meal suggestions tests - Enhanced with expiring items + recent meals"""
    
    def test_get_suggestions(self, api_client, auth_headers):
        """Test GET /api/suggestions returns pantry-based suggestions"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # First add some pantry items
        api_client.post(f"{BASE_URL}/api/pantry", json={
            "name": "Flour",
            "quantity": 2,
            "unit": "kg",
            "category": "Dry Goods"
        }, headers=headers)
        
        api_client.post(f"{BASE_URL}/api/pantry", json={
            "name": "Sugar",
            "quantity": 1,
            "unit": "kg",
            "category": "Dry Goods"
        }, headers=headers)
        
        # Get suggestions
        response = api_client.get(f"{BASE_URL}/api/suggestions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"[PASS] Got {len(data)} pantry-based suggestions")


# ===== RECIPE IMPORT URL =====
class TestRecipeImport:
    """Recipe URL import tests"""
    
    def test_recipe_import_from_url(self, api_client, auth_headers):
        """Test POST /api/recipes/import-url"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        response = api_client.post(f"{BASE_URL}/api/recipes/import-url", json={
            "url": "https://www.food.com/recipe/banana-bread-180529"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "ingredients" in data
        assert "instructions" in data
        print(f"[PASS] Recipe import: name={data.get('name', 'N/A')}")


# ===== SHOPPING LIST CRUD (triggers push notifications) =====
class TestShoppingCRUD:
    """Shopping list full CRUD cycle - push notifications fire on create"""
    
    def test_shopping_crud_cycle(self, api_client, auth_headers):
        """Test full CRUD on /api/shopping"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # CREATE (triggers push notification)
        create_resp = api_client.post(f"{BASE_URL}/api/shopping", json={
            "name": "TEST_Milk_Push",
            "quantity": "2 gallons",
            "category": "Dairy"
        }, headers=headers)
        assert create_resp.status_code == 200
        item = create_resp.json()
        item_id = item["id"]
        assert item["name"] == "TEST_Milk_Push"
        print(f"[PASS] Created shopping item (push triggered): {item_id}")
        
        # READ (list)
        list_resp = api_client.get(f"{BASE_URL}/api/shopping", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert isinstance(items, list)
        assert any(i["id"] == item_id for i in items)
        print(f"[PASS] Listed shopping items: {len(items)}")
        
        # UPDATE
        update_resp = api_client.put(f"{BASE_URL}/api/shopping/{item_id}", json={
            "id": item_id,
            "name": "TEST_Milk_Push_Updated",
            "quantity": "3 gallons",
            "category": "Dairy",
            "checked": True
        }, headers=headers)
        assert update_resp.status_code == 200
        print(f"[PASS] Updated shopping item")
        
        # DELETE
        delete_resp = api_client.delete(f"{BASE_URL}/api/shopping/{item_id}", headers=headers)
        assert delete_resp.status_code == 200
        print(f"[PASS] Deleted shopping item")


# ===== TASKS CRUD =====
class TestTasksCRUD:
    """Tasks full CRUD cycle"""
    
    def test_tasks_crud_cycle(self, api_client, auth_headers):
        """Test full CRUD on /api/tasks"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # CREATE
        create_resp = api_client.post(f"{BASE_URL}/api/tasks", json={
            "title": "TEST_Task_Iter10",
            "description": "Test task description",
            "priority": "high",
            "due_date": "2026-02-15"
        }, headers=headers)
        assert create_resp.status_code == 200
        task = create_resp.json()
        task_id = task["id"]
        print(f"[PASS] Created task: {task_id}")
        
        # READ
        list_resp = api_client.get(f"{BASE_URL}/api/tasks", headers=headers)
        assert list_resp.status_code == 200
        tasks = list_resp.json()
        assert any(t["id"] == task_id for t in tasks)
        print(f"[PASS] Listed tasks: {len(tasks)}")
        
        # UPDATE
        update_resp = api_client.put(f"{BASE_URL}/api/tasks/{task_id}", json={
            "id": task_id,
            "title": "TEST_Task_Iter10_Updated",
            "description": "Updated",
            "priority": "medium",
            "due_date": "2026-02-20",
            "completed": True
        }, headers=headers)
        assert update_resp.status_code == 200
        print(f"[PASS] Updated task")
        
        # DELETE
        delete_resp = api_client.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
        assert delete_resp.status_code == 200
        print(f"[PASS] Deleted task")


# ===== CALENDAR CRUD =====
class TestCalendarCRUD:
    """Calendar full CRUD cycle"""
    
    def test_calendar_crud_cycle(self, api_client, auth_headers):
        """Test full CRUD on /api/calendar"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # CREATE
        create_resp = api_client.post(f"{BASE_URL}/api/calendar", json={
            "title": "TEST_Event_Iter10",
            "description": "Test event",
            "date": "2026-02-15",
            "time": "14:00",
            "color": "blue"
        }, headers=headers)
        assert create_resp.status_code == 200
        event = create_resp.json()
        event_id = event["id"]
        print(f"[PASS] Created calendar event: {event_id}")
        
        # READ
        list_resp = api_client.get(f"{BASE_URL}/api/calendar", headers=headers)
        assert list_resp.status_code == 200
        events = list_resp.json()
        assert any(e["id"] == event_id for e in events)
        print(f"[PASS] Listed events: {len(events)}")
        
        # UPDATE
        update_resp = api_client.put(f"{BASE_URL}/api/calendar/{event_id}", json={
            "id": event_id,
            "title": "TEST_Event_Iter10_Updated",
            "description": "Updated event",
            "date": "2026-02-20",
            "time": "15:00",
            "color": "red"
        }, headers=headers)
        assert update_resp.status_code == 200
        print(f"[PASS] Updated event")
        
        # DELETE
        delete_resp = api_client.delete(f"{BASE_URL}/api/calendar/{event_id}", headers=headers)
        assert delete_resp.status_code == 200
        print(f"[PASS] Deleted event")


# ===== CHORES CRUD + COMPLETE =====
class TestChoresCRUD:
    """Chores full CRUD cycle + completion"""
    
    def test_chores_crud_cycle(self, api_client, auth_headers):
        """Test full CRUD on /api/chores + POST /api/chores/{id}/complete"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # CREATE
        create_resp = api_client.post(f"{BASE_URL}/api/chores", json={
            "title": "TEST_Chore_Iter10",
            "description": "Test chore description",
            "difficulty": "medium"
        }, headers=headers)
        assert create_resp.status_code == 200
        chore = create_resp.json()
        chore_id = chore["id"]
        assert chore["points"] == 10  # medium = 10 points
        print(f"[PASS] Created chore: {chore_id} with {chore['points']} points")
        
        # READ
        list_resp = api_client.get(f"{BASE_URL}/api/chores", headers=headers)
        assert list_resp.status_code == 200
        chores = list_resp.json()
        assert any(c["id"] == chore_id for c in chores)
        print(f"[PASS] Listed chores: {len(chores)}")
        
        # COMPLETE
        complete_resp = api_client.post(f"{BASE_URL}/api/chores/{chore_id}/complete", headers=headers)
        assert complete_resp.status_code == 200
        complete_data = complete_resp.json()
        assert "points_earned" in complete_data
        print(f"[PASS] Completed chore, earned {complete_data['points_earned']} points")
        
        # DELETE
        delete_resp = api_client.delete(f"{BASE_URL}/api/chores/{chore_id}", headers=headers)
        assert delete_resp.status_code == 200
        print(f"[PASS] Deleted chore")


# ===== NOTES CRUD =====
class TestNotesCRUD:
    """Notes full CRUD cycle"""
    
    def test_notes_crud_cycle(self, api_client, auth_headers):
        """Test full CRUD on /api/notes"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # CREATE
        create_resp = api_client.post(f"{BASE_URL}/api/notes", json={
            "title": "TEST_Note_Iter10",
            "content": "Test note content",
            "color": "yellow"
        }, headers=headers)
        assert create_resp.status_code == 200
        note = create_resp.json()
        note_id = note["id"]
        print(f"[PASS] Created note: {note_id}")
        
        # READ
        list_resp = api_client.get(f"{BASE_URL}/api/notes", headers=headers)
        assert list_resp.status_code == 200
        notes = list_resp.json()
        assert any(n["id"] == note_id for n in notes)
        print(f"[PASS] Listed notes: {len(notes)}")
        
        # UPDATE
        update_resp = api_client.put(f"{BASE_URL}/api/notes/{note_id}", json={
            "id": note_id,
            "title": "TEST_Note_Iter10_Updated",
            "content": "Updated content",
            "color": "blue"
        }, headers=headers)
        assert update_resp.status_code == 200
        print(f"[PASS] Updated note")
        
        # DELETE
        delete_resp = api_client.delete(f"{BASE_URL}/api/notes/{note_id}", headers=headers)
        assert delete_resp.status_code == 200
        print(f"[PASS] Deleted note")


# ===== PANTRY CRUD + BARCODE =====
class TestPantryCRUD:
    """Pantry full CRUD cycle + barcode lookup"""
    
    def test_pantry_crud_cycle(self, api_client, auth_headers):
        """Test full CRUD on /api/pantry"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        
        # CREATE
        create_resp = api_client.post(f"{BASE_URL}/api/pantry", json={
            "name": "TEST_Cereal_Iter10",
            "quantity": 2,
            "unit": "boxes",
            "category": "Dry Goods",
            "expiry_date": "2026-06-01"
        }, headers=headers)
        assert create_resp.status_code == 200
        item = create_resp.json()
        item_id = item["id"]
        print(f"[PASS] Created pantry item: {item_id}")
        
        # READ
        list_resp = api_client.get(f"{BASE_URL}/api/pantry", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert any(i["id"] == item_id for i in items)
        print(f"[PASS] Listed pantry items: {len(items)}")
        
        # UPDATE
        update_resp = api_client.put(f"{BASE_URL}/api/pantry/{item_id}", json={
            "id": item_id,
            "name": "TEST_Cereal_Iter10_Updated",
            "quantity": 3,
            "unit": "boxes",
            "category": "Dry Goods",
            "expiry_date": "2026-07-01"
        }, headers=headers)
        assert update_resp.status_code == 200
        print(f"[PASS] Updated pantry item")
        
        # DELETE
        delete_resp = api_client.delete(f"{BASE_URL}/api/pantry/{item_id}", headers=headers)
        assert delete_resp.status_code == 200
        print(f"[PASS] Deleted pantry item")
    
    def test_barcode_lookup(self, api_client):
        """Test GET /api/pantry/barcode/{barcode}"""
        # Coca-Cola Zero Sugar barcode
        response = api_client.get(f"{BASE_URL}/api/pantry/barcode/049000042559")
        assert response.status_code == 200
        data = response.json()
        assert "found" in data
        print(f"[PASS] Barcode lookup: found={data['found']}, name={data.get('name', 'N/A')}")


# ===== SETTINGS =====
class TestSettings:
    """Settings endpoint tests"""
    
    def test_get_settings(self, api_client, auth_headers):
        """Test GET /api/settings"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        response = api_client.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data or "family_id" in data
        print(f"[PASS] Settings retrieved")


# ===== BUDGET =====
class TestBudget:
    """Budget endpoint tests"""
    
    def test_budget_summary(self, api_client, auth_headers):
        """Test GET /api/budget/summary"""
        headers = {k: v for k, v in auth_headers.items() if k not in ["family_id", "user_id"]}
        response = api_client.get(f"{BASE_URL}/api/budget/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "balance" in data
        print(f"[PASS] Budget summary: balance={data.get('balance')}")


# ===== QR CODE =====
class TestQRCode:
    """QR Code generation tests"""
    
    def test_qr_code_base64(self, api_client):
        """Test GET /api/qr-code/base64?url=..."""
        response = api_client.get(f"{BASE_URL}/api/qr-code/base64?url=https://test.com")
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert data["qr_code"].startswith("data:image/png;base64,")
        print(f"[PASS] QR code generated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
