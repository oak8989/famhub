"""
Test new features for Family Hub iteration 6:
- QR Code generation
- Data Export (JSON/CSV)
- AI Meal Suggestions
- Push Notifications
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_headers():
    """Register a new user and get fresh JWT token"""
    user_email = f"test_newfeatures_{uuid.uuid4().hex[:8]}@test.com"
    user_password = "Test123456!"
    
    # Register user with family
    reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Test New Features User",
        "email": user_email,
        "password": user_password,
        "family_name": "Test Features Family"
    })
    assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
    
    # Get token from registration response
    token = reg_resp.json()["token"]
    print(f"✅ Created test user: {user_email}")
    
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class TestHealthAndRoot:
    """Basic API health tests"""
    
    def test_health_check(self, api_client):
        """Test health endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✅ Health check passed")
    
    def test_root_api(self, api_client):
        """Test root API endpoint"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
        print(f"✅ API root returned version: {data.get('version')}")


class TestQRCodeGeneration:
    """Test QR Code generation endpoints"""
    
    def test_qr_code_base64_endpoint(self, api_client):
        """Test QR code base64 generation"""
        test_url = "https://example.com/famhub"
        response = api_client.get(f"{BASE_URL}/api/qr-code/base64?url={test_url}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "qr_code" in data
        assert "url" in data
        assert data["url"] == test_url
        
        # Verify base64 PNG format
        assert data["qr_code"].startswith("data:image/png;base64,")
        print("✅ QR code base64 generation works")
    
    def test_qr_code_streaming_endpoint(self, api_client):
        """Test QR code streaming PNG generation"""
        test_url = "https://hub.example.com"
        response = api_client.get(f"{BASE_URL}/api/qr-code?url={test_url}")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/png"
        assert len(response.content) > 0  # Should have binary data
        print("✅ QR code streaming PNG endpoint works")
    
    def test_qr_code_empty_url(self, api_client):
        """Test QR code with empty URL - should fail validation"""
        response = api_client.get(f"{BASE_URL}/api/qr-code/base64")
        # FastAPI should return 422 for missing required query param
        assert response.status_code == 422
        print("✅ QR code properly validates required URL param")


class TestDataExport:
    """Test data export endpoints"""
    
    def test_export_full_data_json(self, api_client, auth_headers):
        """Test full data export as JSON"""
        response = api_client.get(f"{BASE_URL}/api/export/data", headers=auth_headers)
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        
        # Verify it's valid JSON
        data = response.json()
        
        # Check expected fields
        assert "exported_at" in data
        assert "exported_by" in data
        assert "family" in data
        assert "members" in data
        assert "calendar_events" in data
        assert "shopping_items" in data
        assert "tasks" in data
        assert "pantry_items" in data
        print("✅ Full data export JSON works")
    
    def test_export_calendar_csv(self, api_client, auth_headers):
        """Test calendar CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/calendar", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        
        # Verify it's CSV with headers
        content = response.text
        assert "id,title,description,date,time,color" in content
        print("✅ Calendar CSV export works")
    
    def test_export_shopping_csv(self, api_client, auth_headers):
        """Test shopping list CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/shopping", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        
        content = response.text
        assert "id,name,quantity,category,checked" in content
        print("✅ Shopping CSV export works")
    
    def test_export_pantry_csv(self, api_client, auth_headers):
        """Test pantry CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/pantry", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        
        content = response.text
        assert "id,name,quantity,unit,category,expiry_date" in content
        print("✅ Pantry CSV export works")
    
    def test_export_tasks_csv(self, api_client, auth_headers):
        """Test tasks CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/tasks", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✅ Tasks CSV export works")
    
    def test_export_budget_csv(self, api_client, auth_headers):
        """Test budget CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/budget", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✅ Budget CSV export works")
    
    def test_export_contacts_csv(self, api_client, auth_headers):
        """Test contacts CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/contacts", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✅ Contacts CSV export works")
    
    def test_export_chores_csv(self, api_client, auth_headers):
        """Test chores CSV export"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/chores", headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✅ Chores CSV export works")
    
    def test_export_invalid_module(self, api_client, auth_headers):
        """Test exporting invalid module returns error"""
        response = api_client.get(f"{BASE_URL}/api/export/csv/invalid_module", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid module" in response.json().get("detail", "")
        print("✅ Invalid module export properly rejected")
    
    def test_export_without_auth(self, api_client):
        """Test export requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/export/data")
        
        assert response.status_code == 401
        print("✅ Export endpoints require authentication")


class TestPushNotifications:
    """Test push notification endpoints"""
    
    def test_get_vapid_key(self, api_client):
        """Test VAPID public key retrieval"""
        response = api_client.get(f"{BASE_URL}/api/notifications/vapid-key")
        
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 0
        print(f"✅ VAPID key endpoint works: {data['public_key'][:30]}...")
    
    def test_subscribe_push_notifications(self, api_client, auth_headers):
        """Test push notification subscription"""
        subscription_data = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-12345",
            "keys": {
                "p256dh": "test-p256dh-key",
                "auth": "test-auth-key"
            }
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Subscribed to notifications"
        print("✅ Push notification subscription works")
    
    def test_unsubscribe_push_notifications(self, api_client, auth_headers):
        """Test push notification unsubscription"""
        response = api_client.delete(
            f"{BASE_URL}/api/notifications/unsubscribe",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unsubscribed from notifications"
        print("✅ Push notification unsubscription works")


class TestAIMealSuggestions:
    """Test AI meal suggestions endpoint"""
    
    def test_ai_suggestions_endpoint(self, api_client, auth_headers):
        """Test AI meal suggestions - requires pantry items"""
        response = api_client.post(
            f"{BASE_URL}/api/suggestions/ai",
            json={"use_ai": True},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have either suggestions or a message
        assert "suggestions" in data or "message" in data
        
        if data.get("suggestions"):
            print(f"✅ AI suggestions returned {len(data['suggestions'])} meal ideas")
            # Check structure of suggestions if any
            for meal in data.get("suggestions", []):
                assert "name" in meal
                print(f"   - {meal.get('name')}")
        else:
            print(f"✅ AI suggestions endpoint responds: {data.get('message')}")
    
    def test_regular_suggestions_endpoint(self, api_client, auth_headers):
        """Test regular (non-AI) meal suggestions"""
        response = api_client.get(f"{BASE_URL}/api/suggestions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list)
        print(f"✅ Regular suggestions returned {len(data)} recipes")


class TestPantryWithBarcode:
    """Test pantry functionality including barcode lookup"""
    
    def test_get_pantry_items(self, api_client, auth_headers):
        """Test getting pantry items"""
        response = api_client.get(f"{BASE_URL}/api/pantry", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Pantry has {len(data)} items")
        for item in data:
            print(f"   - {item.get('name')}: {item.get('quantity')} {item.get('unit')}")
    
    def test_barcode_lookup(self, api_client):
        """Test barcode lookup endpoint"""
        # Use a known barcode from OpenFoodFacts
        test_barcode = "3017620422003"  # Nutella
        response = api_client.get(f"{BASE_URL}/api/pantry/barcode/{test_barcode}")
        
        assert response.status_code == 200
        data = response.json()
        assert "found" in data
        print(f"✅ Barcode lookup works: found={data['found']}, name={data.get('name', 'N/A')}")
    
    def test_barcode_lookup_unknown(self, api_client):
        """Test barcode lookup with unknown barcode"""
        # Use a truly random barcode that shouldn't exist
        response = api_client.get(f"{BASE_URL}/api/pantry/barcode/9999999999999")
        
        assert response.status_code == 200
        data = response.json()
        # Either found=False or if UPC DB finds something, just ensure it returns valid response
        assert "found" in data
        print(f"✅ Unknown barcode lookup returns found={data['found']}")
    
    def test_create_pantry_item_with_barcode(self, api_client, auth_headers):
        """Test creating pantry item with manual barcode"""
        item_data = {
            "name": "TEST_Barcode_Item",
            "barcode": "1234567890123",
            "quantity": 2,
            "unit": "boxes",
            "category": "Dry Goods"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/pantry",
            json=item_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Barcode_Item"
        assert data["barcode"] == "1234567890123"
        print(f"✅ Created pantry item with barcode: {data['id']}")
        
        # Clean up
        api_client.delete(f"{BASE_URL}/api/pantry/{data['id']}", headers=auth_headers)


class TestMobileNavigation:
    """Test endpoints used by mobile navigation"""
    
    def test_dashboard_endpoints(self, api_client, auth_headers):
        """Test all dashboard data endpoints are accessible"""
        endpoints = [
            "/api/calendar",
            "/api/tasks",
            "/api/chores",
            "/api/settings"
        ]
        
        for endpoint in endpoints:
            response = api_client.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            assert response.status_code == 200, f"Failed: {endpoint}"
            print(f"✅ {endpoint} accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
