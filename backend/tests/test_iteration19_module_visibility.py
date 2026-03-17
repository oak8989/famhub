"""
Iteration 19: Module Visibility Features Testing
Tests:
1. Personal hidden modules (hidden_modules on user doc)
2. PUT /api/auth/hidden-modules endpoint
3. GET /api/auth/me returns hidden_modules field
4. Admin Modules tab includes nok_box and inventory in MODULE_NAMES
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_OWNER_EMAIL = "test@bulk.com"
TEST_OWNER_PASSWORD = "test123"

# New test user credentials
TEST_NEW_USER_EMAIL = f"modtest_{uuid.uuid4().hex[:8]}@famhub.com"
TEST_NEW_USER_PASSWORD = "TestPass123"
TEST_NEW_USER_NAME = "Module Tester"
TEST_NEW_FAMILY_NAME = "Test Family Module"


class TestSetup:
    """Verify setup and get auth tokens"""
    
    def test_health_check(self):
        """Verify backend is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print(f"✓ Backend healthy at {BASE_URL}")
    
    def test_login_existing_owner(self):
        """Login with existing owner account"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_OWNER_EMAIL,
            "password": TEST_OWNER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        pytest.owner_token = data["token"]
        pytest.owner_user = data["user"]
        print(f"✓ Logged in as owner: {data['user']['name']} (role: {data['user']['role']})")


class TestHiddenModulesEndpoint:
    """Test PUT /api/auth/hidden-modules endpoint"""
    
    def test_update_hidden_modules_success(self):
        """Test updating hidden modules list"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        # Set some modules as hidden
        hidden_list = ["calendar", "shopping"]
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": hidden_list},
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "hidden_modules" in data
        assert data["hidden_modules"] == hidden_list
        print(f"✓ PUT /api/auth/hidden-modules - Set hidden: {hidden_list}")
    
    def test_update_hidden_modules_empty_list(self):
        """Test clearing all hidden modules"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": []},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hidden_modules"] == []
        print("✓ PUT /api/auth/hidden-modules - Cleared hidden modules")
    
    def test_update_hidden_modules_invalid_type(self):
        """Test validation - hidden_modules must be a list"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": "not-a-list"},
            headers=headers
        )
        assert response.status_code == 400
        print("✓ PUT /api/auth/hidden-modules - Validates list type")
    
    def test_update_hidden_modules_all_module_keys(self):
        """Test hiding all 14 module keys"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        all_modules = [
            "calendar", "shopping", "tasks", "notes", "budget", "meals",
            "recipes", "grocery", "contacts", "pantry", "suggestions",
            "chores", "nok_box", "inventory"
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": all_modules},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["hidden_modules"]) == 14
        assert "nok_box" in data["hidden_modules"]
        assert "inventory" in data["hidden_modules"]
        print(f"✓ PUT /api/auth/hidden-modules - All 14 modules can be hidden including nok_box, inventory")
    
    def test_update_hidden_modules_reset(self):
        """Reset hidden modules to empty for subsequent tests"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": []},
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Reset hidden_modules to empty")


class TestGetMeReturnsHiddenModules:
    """Test GET /api/auth/me returns hidden_modules field"""
    
    def test_get_me_has_hidden_modules_field(self):
        """Verify /api/auth/me returns hidden_modules"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        # First set some hidden modules
        requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": ["tasks", "notes"]},
            headers=headers
        )
        
        # Now get /me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check hidden_modules is in response
        assert "hidden_modules" in data, f"hidden_modules not in response: {data.keys()}"
        assert data["hidden_modules"] == ["tasks", "notes"]
        print(f"✓ GET /api/auth/me returns hidden_modules: {data['hidden_modules']}")
    
    def test_get_me_hidden_modules_persists(self):
        """Verify hidden_modules persists across requests"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        # Set hidden modules
        hidden_list = ["budget", "meals", "nok_box"]
        requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": hidden_list},
            headers=headers
        )
        
        # Get /me multiple times
        for i in range(3):
            response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["hidden_modules"] == hidden_list, f"Iteration {i}: hidden_modules mismatch"
        
        print("✓ GET /api/auth/me - hidden_modules persists across requests")


class TestNewUserRegistration:
    """Test new user registration includes hidden_modules handling"""
    
    def test_register_new_user(self):
        """Register a new user and verify hidden_modules is empty by default"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_NEW_USER_EMAIL,
            "password": TEST_NEW_USER_PASSWORD,
            "name": TEST_NEW_USER_NAME,
            "family_name": TEST_NEW_FAMILY_NAME
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        pytest.new_user_token = data["token"]
        pytest.new_user_id = data["user"]["id"]
        print(f"✓ Registered new user: {TEST_NEW_USER_EMAIL}")
    
    def test_new_user_get_me(self):
        """Verify new user's /me endpoint works"""
        headers = {"Authorization": f"Bearer {pytest.new_user_token}"}
        
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # New users should have either no hidden_modules or empty list
        hidden = data.get("hidden_modules", [])
        assert hidden == [] or hidden is None, f"New user should have no hidden modules, got: {hidden}"
        print(f"✓ New user has no hidden modules by default")
    
    def test_new_user_can_hide_modules(self):
        """Verify new user can hide modules"""
        headers = {"Authorization": f"Bearer {pytest.new_user_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": ["calendar", "inventory"]},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "calendar" in data["hidden_modules"]
        assert "inventory" in data["hidden_modules"]
        print("✓ New user can hide modules")


class TestSettingsEndpoint:
    """Test /api/settings includes nok_box and inventory modules"""
    
    def test_settings_has_all_14_modules(self):
        """Verify settings endpoint returns module config for all 14 modules"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "modules" in data, "Settings should have 'modules' key"
        
        expected_modules = [
            "calendar", "shopping", "tasks", "notes", "budget", "meals",
            "recipes", "grocery", "contacts", "pantry", "suggestions",
            "chores", "nok_box", "inventory"
        ]
        
        modules = data["modules"]
        missing = [m for m in expected_modules if m not in modules]
        assert not missing, f"Missing modules in settings: {missing}"
        
        print(f"✓ GET /api/settings - All 14 modules present: {list(modules.keys())}")
    
    def test_settings_nok_box_module_config(self):
        """Verify nok_box module has proper config"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        nok_box = data["modules"].get("nok_box")
        assert nok_box is not None, "nok_box module should exist in settings"
        assert "enabled" in nok_box
        assert "visible_to" in nok_box
        print(f"✓ nok_box module config: enabled={nok_box['enabled']}, visible_to={nok_box['visible_to']}")
    
    def test_settings_inventory_module_config(self):
        """Verify inventory module has proper config"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        inventory = data["modules"].get("inventory")
        assert inventory is not None, "inventory module should exist in settings"
        assert "enabled" in inventory
        assert "visible_to" in inventory
        print(f"✓ inventory module config: enabled={inventory['enabled']}, visible_to={inventory['visible_to']}")


class TestModuleToggleAdmin:
    """Test admin can toggle module visibility for family"""
    
    def test_toggle_module_enabled(self):
        """Test admin can enable/disable modules via PUT /api/settings"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        # Get current settings
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert get_response.status_code == 200
        settings = get_response.json()
        
        # Toggle calendar off
        settings["modules"]["calendar"]["enabled"] = False
        
        response = requests.put(
            f"{BASE_URL}/api/settings",
            json={"modules": settings["modules"]},
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Admin can toggle module enabled state")
        
        # Reset to enabled
        settings["modules"]["calendar"]["enabled"] = True
        requests.put(
            f"{BASE_URL}/api/settings",
            json={"modules": settings["modules"]},
            headers=headers
        )
    
    def test_toggle_nok_box_visibility(self):
        """Test admin can change nok_box visible_to roles"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        settings = get_response.json()
        
        # Set nok_box visible only to owner and parent
        settings["modules"]["nok_box"]["visible_to"] = ["owner", "parent"]
        
        response = requests.put(
            f"{BASE_URL}/api/settings",
            json={"modules": settings["modules"]},
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify change
        get_response2 = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        updated = get_response2.json()
        assert updated["modules"]["nok_box"]["visible_to"] == ["owner", "parent"]
        print("✓ Admin can change nok_box visible_to roles")
        
        # Reset to all roles
        settings["modules"]["nok_box"]["visible_to"] = ["owner", "parent", "member", "child"]
        requests.put(
            f"{BASE_URL}/api/settings",
            json={"modules": settings["modules"]},
            headers=headers
        )


class TestCleanup:
    """Cleanup: Reset owner hidden_modules"""
    
    def test_reset_owner_hidden_modules(self):
        """Reset owner's hidden_modules to empty"""
        headers = {"Authorization": f"Bearer {pytest.owner_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/auth/hidden-modules",
            json={"hidden_modules": []},
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Cleanup: Reset owner hidden_modules to empty")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
