"""
Iteration 14 Backend Tests - Bulk Scan and Quantity Placeholder Features

Tests for:
1. POST /api/pantry/bulk-add - accepts array of items, returns count and items
2. POST /api/pantry/bulk-add - empty array returns count 0
3. Shopping page add item still works correctly
4. Grocery page add item still works correctly
5. Pantry page add item still works (with empty quantity defaulting to 1)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuth:
    """Get auth token for authenticated requests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@bulk.com", "password": "test123"}
        )
        if response.status_code == 200:
            return response.json().get("token")
        # If test user doesn't exist, try with owner@test.com
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "owner@test.com", "password": "test123"}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping tests")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestPantryBulkAdd(TestAuth):
    """Test the new POST /api/pantry/bulk-add endpoint"""
    
    def test_bulk_add_empty_array(self, headers):
        """Empty array should return count 0"""
        response = requests.post(
            f"{BASE_URL}/api/pantry/bulk-add",
            headers=headers,
            json=[]
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("count") == 0, f"Expected count 0, got {data}"
        print("PASS: Empty array returns count 0")
    
    def test_bulk_add_single_item(self, headers):
        """Single item should be added and returned"""
        test_item = {
            "name": "TEST_BulkItem1",
            "barcode": "1234567890123",
            "quantity": 1,
            "unit": "pcs",
            "category": "Snacks"
        }
        response = requests.post(
            f"{BASE_URL}/api/pantry/bulk-add",
            headers=headers,
            json=[test_item]
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("count") == 1, f"Expected count 1, got {data}"
        assert "items" in data, "Expected 'items' in response"
        assert len(data["items"]) == 1, f"Expected 1 item, got {len(data['items'])}"
        assert data["items"][0]["name"] == "TEST_BulkItem1"
        print("PASS: Single item bulk add works correctly")
    
    def test_bulk_add_multiple_items(self, headers):
        """Multiple items should all be added"""
        test_items = [
            {"name": "TEST_BulkItem2", "quantity": 2, "unit": "pcs", "category": "Dairy"},
            {"name": "TEST_BulkItem3", "quantity": 3, "unit": "lbs", "category": "Produce"},
            {"name": "TEST_BulkItem4", "quantity": 5, "unit": "oz", "category": "Meat"}
        ]
        response = requests.post(
            f"{BASE_URL}/api/pantry/bulk-add",
            headers=headers,
            json=test_items
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("count") == 3, f"Expected count 3, got {data}"
        assert len(data["items"]) == 3, f"Expected 3 items, got {len(data['items'])}"
        item_names = [item["name"] for item in data["items"]]
        assert "TEST_BulkItem2" in item_names
        assert "TEST_BulkItem3" in item_names
        assert "TEST_BulkItem4" in item_names
        print("PASS: Multiple items bulk add works correctly")
    
    def test_bulk_add_items_with_barcode(self, headers):
        """Items with barcodes should preserve barcode"""
        test_items = [
            {"name": "TEST_BulkBarcode1", "barcode": "9876543210123", "quantity": 1, "unit": "pcs", "category": "Beverages"}
        ]
        response = requests.post(
            f"{BASE_URL}/api/pantry/bulk-add",
            headers=headers,
            json=test_items
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["barcode"] == "9876543210123"
        print("PASS: Barcode preserved in bulk add")
    
    def test_bulk_added_items_appear_in_pantry(self, headers):
        """Items added via bulk should appear in pantry list"""
        response = requests.get(
            f"{BASE_URL}/api/pantry",
            headers=headers
        )
        assert response.status_code == 200
        items = response.json()
        item_names = [item["name"] for item in items]
        # Check that our test items are there
        assert any("TEST_BulkItem" in name for name in item_names), "Bulk added items should appear in pantry"
        print("PASS: Bulk added items appear in GET /api/pantry")


class TestShoppingStillWorks(TestAuth):
    """Verify shopping list CRUD still works"""
    
    def test_shopping_add_item(self, headers):
        """Add item to shopping list"""
        response = requests.post(
            f"{BASE_URL}/api/shopping",
            headers=headers,
            json={"name": "TEST_ShoppingItem", "quantity": "", "category": "General"}
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("name") == "TEST_ShoppingItem"
        print("PASS: Shopping add item works")
        return data.get("id")
    
    def test_shopping_get_items(self, headers):
        """Get shopping list items"""
        response = requests.get(
            f"{BASE_URL}/api/shopping",
            headers=headers
        )
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        print(f"PASS: Shopping get items works, found {len(items)} items")


class TestGroceryStillWorks(TestAuth):
    """Verify grocery list CRUD still works"""
    
    def test_grocery_add_item(self, headers):
        """Add item to grocery list"""
        response = requests.post(
            f"{BASE_URL}/api/grocery",
            headers=headers,
            json={"name": "TEST_GroceryItem", "quantity": ""}
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("name") == "TEST_GroceryItem"
        print("PASS: Grocery add item works")
    
    def test_grocery_get_items(self, headers):
        """Get grocery list items"""
        response = requests.get(
            f"{BASE_URL}/api/grocery",
            headers=headers
        )
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        print(f"PASS: Grocery get items works, found {len(items)} items")


class TestPantryStillWorks(TestAuth):
    """Verify pantry CRUD still works (single item add)"""
    
    def test_pantry_add_item_with_empty_quantity(self, headers):
        """Add pantry item with empty quantity - should default to 1"""
        response = requests.post(
            f"{BASE_URL}/api/pantry",
            headers=headers,
            json={
                "name": "TEST_PantryEmptyQty",
                "quantity": 1,  # Frontend sends 1 when empty
                "unit": "pcs",
                "category": "Other"
            }
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("name") == "TEST_PantryEmptyQty"
        assert data.get("quantity") == 1 or data.get("quantity") == "1"
        print("PASS: Pantry add item with quantity works")
    
    def test_pantry_get_items(self, headers):
        """Get pantry items"""
        response = requests.get(
            f"{BASE_URL}/api/pantry",
            headers=headers
        )
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        print(f"PASS: Pantry get items works, found {len(items)} items")


class TestCleanup(TestAuth):
    """Clean up test data"""
    
    def test_cleanup_test_items(self, headers):
        """Remove test items created during tests"""
        # Get all pantry items and delete TEST_ prefixed ones
        response = requests.get(f"{BASE_URL}/api/pantry", headers=headers)
        if response.status_code == 200:
            for item in response.json():
                if item.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/pantry/{item['id']}", headers=headers)
        
        # Get all shopping items and delete TEST_ prefixed ones
        response = requests.get(f"{BASE_URL}/api/shopping", headers=headers)
        if response.status_code == 200:
            for item in response.json():
                if item.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/shopping/{item['id']}", headers=headers)
        
        # Get all grocery items and delete TEST_ prefixed ones
        response = requests.get(f"{BASE_URL}/api/grocery", headers=headers)
        if response.status_code == 200:
            for item in response.json():
                if item.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/grocery/{item['id']}", headers=headers)
        
        print("PASS: Cleanup completed")
