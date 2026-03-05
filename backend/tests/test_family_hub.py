"""
Family Hub Backend API Tests
Tests for: Auth, Family, Tasks, Chores, Budget, Settings, and PIN functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_USER_EMAIL = f"test_{uuid.uuid4().hex[:8]}@family.com"
TEST_USER_PASSWORD = "test123"
TEST_USER_NAME = "Test User"
TEST_FAMILY_NAME = "Test Family"


class TestHealthAndStatus:
    """Health check and API status tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
    def test_root_api_endpoint(self):
        """Test /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"
        print("✓ Root API endpoint working")


class TestAuthFlow:
    """Authentication flow tests"""
    
    @pytest.fixture(scope="class")
    def registered_user(self):
        """Register a test user and return credentials"""
        user_email = f"test_{uuid.uuid4().hex[:8]}@family.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": TEST_USER_NAME,
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "user_pin" in data
        print(f"✓ User registered: {user_email}")
        return {
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "user_pin": data["user_pin"],
            "user_id": data["user"]["id"]
        }
    
    def test_register_user(self, registered_user):
        """Test user registration creates user with PIN"""
        assert registered_user["email"] is not None
        assert registered_user["user_pin"] is not None
        assert len(registered_user["user_pin"]) == 4  # User PIN is 4 digits
        print(f"✓ User PIN generated: {registered_user['user_pin']}")
    
    def test_login_with_email_password(self, registered_user):
        """Test login with email and password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == registered_user["email"]
        print("✓ Email/password login working")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials properly rejected")
    
    def test_user_pin_login(self, registered_user):
        """Test login with personal PIN"""
        response = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={
            "pin": registered_user["user_pin"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print("✓ Personal PIN login working")


class TestFamilyManagement:
    """Family creation and management tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create user and get auth token"""
        user_email = f"owner_{uuid.uuid4().hex[:8]}@family.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Family Owner",
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def family_data(self, auth_token):
        """Create a family and return data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/family/create", 
            json={"name": TEST_FAMILY_NAME},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        return data
    
    def test_create_family_generates_6_digit_pin(self, family_data):
        """Test family creation auto-generates 6-digit PIN"""
        assert "pin" in family_data
        assert len(family_data["pin"]) == 6
        assert family_data["pin"].isdigit()
        print(f"✓ Family PIN generated: {family_data['pin']} (6 digits)")
    
    def test_get_family(self, auth_token, family_data):
        """Test getting family info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/family", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_FAMILY_NAME
        print("✓ Get family working")
    
    def test_update_family_name(self, auth_token, family_data):
        """Test updating family name"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        new_name = "Updated Family Name"
        response = requests.put(f"{BASE_URL}/api/family", 
            json={"name": new_name},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
        print("✓ Family name update working")
    
    def test_family_pin_login(self, family_data):
        """Test login with family PIN"""
        response = requests.post(f"{BASE_URL}/api/auth/pin-login", json={
            "pin": family_data["pin"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "family" in data
        print("✓ Family PIN login working")
    
    def test_add_family_member_generates_4_digit_pin(self, auth_token):
        """Test adding family member generates 4-digit PIN"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Child Member", "role": "child"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_pin" in data
        assert len(data["user_pin"]) == 4
        assert data["user_pin"].isdigit()
        assert data["role"] == "child"
        print(f"✓ Member added with PIN: {data['user_pin']} (4 digits)")
    
    def test_get_family_members(self, auth_token):
        """Test getting family members list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/family/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the owner
        print(f"✓ Family members retrieved: {len(data)} members")
    
    def test_regenerate_family_pin(self, auth_token, family_data):
        """Test regenerating family PIN"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        old_pin = family_data["pin"]
        response = requests.post(f"{BASE_URL}/api/family/regenerate-pin", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "pin" in data
        assert len(data["pin"]) == 6
        # New PIN should be different (very high probability)
        print(f"✓ Family PIN regenerated: {data['pin']}")


class TestTasksWithAssignment:
    """Tasks module tests with assignment functionality"""
    
    @pytest.fixture(scope="class")
    def auth_setup(self):
        """Setup user with family for tasks testing"""
        user_email = f"tasks_{uuid.uuid4().hex[:8]}@family.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Tasks Tester",
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        user_id = login_resp.json()["user"]["id"]
        
        # Create family
        headers = {"Authorization": f"Bearer {token}"}
        requests.post(f"{BASE_URL}/api/family/create", 
            json={"name": "Tasks Test Family"},
            headers=headers
        )
        
        return {"token": token, "user_id": user_id, "headers": headers}
    
    def test_create_task_with_assignment(self, auth_setup):
        """Test creating task with assigned_to field"""
        headers = auth_setup["headers"]
        task_data = {
            "title": "Test Task",
            "description": "Test task description",
            "priority": "high",
            "due_date": "2025-02-15",
            "assigned_to": auth_setup["user_id"]
        }
        response = requests.post(f"{BASE_URL}/api/tasks", json=task_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["assigned_to"] == auth_setup["user_id"]
        print("✓ Task created with assignment")
        return data
    
    def test_get_tasks(self, auth_setup):
        """Test getting tasks list"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Tasks retrieved: {len(data)} tasks")


class TestChoresWithPoints:
    """Chores module tests with gamification"""
    
    @pytest.fixture(scope="class")
    def auth_setup(self):
        """Setup user with family for chores testing"""
        user_email = f"chores_{uuid.uuid4().hex[:8]}@family.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Chores Tester",
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        user_id = login_resp.json()["user"]["id"]
        
        # Create family
        headers = {"Authorization": f"Bearer {token}"}
        requests.post(f"{BASE_URL}/api/family/create", 
            json={"name": "Chores Test Family"},
            headers=headers
        )
        
        # Re-login to get updated token with family_id
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        return {"token": token, "user_id": user_id, "headers": headers}
    
    def test_create_chore_with_points(self, auth_setup):
        """Test creating chore with difficulty-based points"""
        headers = auth_setup["headers"]
        chore_data = {
            "title": "Clean Room",
            "description": "Clean and organize bedroom",
            "difficulty": "medium",
            "assigned_to": auth_setup["user_id"]
        }
        response = requests.post(f"{BASE_URL}/api/chores", json=chore_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Clean Room"
        assert "points" in data
        assert data["points"] == 10  # Medium difficulty = 10 points
        print(f"✓ Chore created with {data['points']} points")
        return data["id"]
    
    def test_get_chores(self, auth_setup):
        """Test getting chores list"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/chores", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Chores retrieved: {len(data)} chores")
    
    def test_complete_chore_awards_points(self, auth_setup):
        """Test completing chore awards points to user"""
        headers = auth_setup["headers"]
        
        # Create a chore first
        chore_data = {
            "title": "Test Chore for Completion",
            "difficulty": "easy",
            "assigned_to": auth_setup["user_id"]
        }
        create_resp = requests.post(f"{BASE_URL}/api/chores", json=chore_data, headers=headers)
        chore_id = create_resp.json()["id"]
        
        # Complete the chore
        response = requests.post(f"{BASE_URL}/api/chores/{chore_id}/complete", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "points_earned" in data
        print(f"✓ Chore completed, earned {data['points_earned']} points")
    
    def test_get_rewards(self, auth_setup):
        """Test getting rewards list"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/rewards", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("✓ Rewards endpoint working")
    
    def test_get_leaderboard(self, auth_setup):
        """Test getting family leaderboard"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/leaderboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Leaderboard retrieved: {len(data)} members")


class TestBudgetModule:
    """Budget module tests"""
    
    @pytest.fixture(scope="class")
    def auth_setup(self):
        """Setup user with family for budget testing"""
        user_email = f"budget_{uuid.uuid4().hex[:8]}@family.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Budget Tester",
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Create family
        headers = {"Authorization": f"Bearer {token}"}
        requests.post(f"{BASE_URL}/api/family/create", 
            json={"name": "Budget Test Family"},
            headers=headers
        )
        
        return {"token": token, "headers": headers}
    
    def test_create_budget_entry(self, auth_setup):
        """Test creating budget entry"""
        headers = auth_setup["headers"]
        entry_data = {
            "description": "Salary",
            "amount": 5000,
            "category": "Income",
            "type": "income",
            "date": "2025-02-01"
        }
        response = requests.post(f"{BASE_URL}/api/budget", json=entry_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Salary"
        assert data["amount"] == 5000
        print("✓ Budget entry created")
    
    def test_get_budget_entries(self, auth_setup):
        """Test getting budget entries"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/budget", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Budget entries retrieved: {len(data)} entries")
    
    def test_get_budget_summary(self, auth_setup):
        """Test getting budget summary with charts data"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/budget/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "balance" in data
        assert "by_category" in data
        assert "by_month" in data
        print(f"✓ Budget summary: balance=${data['balance']}")


class TestSettingsModule:
    """Settings module tests"""
    
    @pytest.fixture(scope="class")
    def auth_setup(self):
        """Setup user with family for settings testing"""
        user_email = f"settings_{uuid.uuid4().hex[:8]}@family.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Settings Tester",
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Create family
        headers = {"Authorization": f"Bearer {token}"}
        requests.post(f"{BASE_URL}/api/family/create", 
            json={"name": "Settings Test Family"},
            headers=headers
        )
        
        # Re-login to get updated token with family_id
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        return {"token": token, "headers": headers}
    
    def test_get_settings(self, auth_setup):
        """Test getting family settings"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        print("✓ Settings retrieved")
    
    def test_update_settings(self, auth_setup):
        """Test updating family settings"""
        headers = auth_setup["headers"]
        settings_data = {
            "modules": {
                "calendar": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
                "chores": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]}
            }
        }
        response = requests.put(f"{BASE_URL}/api/settings", json=settings_data, headers=headers)
        assert response.status_code == 200
        print("✓ Settings updated")
    
    def test_get_server_settings_owner_only(self, auth_setup):
        """Test server settings accessible only to owner"""
        headers = auth_setup["headers"]
        response = requests.get(f"{BASE_URL}/api/settings/server", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "smtp_configured" in data
        assert "google_configured" in data
        print("✓ Server settings accessible to owner")


class TestUserRoles:
    """User role tests"""
    
    @pytest.fixture(scope="class")
    def auth_setup(self):
        """Setup owner with family"""
        user_email = f"roles_{uuid.uuid4().hex[:8]}@family.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Roles Tester",
            "email": user_email,
            "password": TEST_USER_PASSWORD,
            "role": "owner"
        })
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Create family
        headers = {"Authorization": f"Bearer {token}"}
        requests.post(f"{BASE_URL}/api/family/create", 
            json={"name": "Roles Test Family"},
            headers=headers
        )
        
        return {"token": token, "headers": headers}
    
    def test_add_member_with_child_role(self, auth_setup):
        """Test adding member with child role"""
        headers = auth_setup["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test Child", "role": "child"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "child"
        print("✓ Child role member added")
    
    def test_add_member_with_parent_role(self, auth_setup):
        """Test adding member with parent role"""
        headers = auth_setup["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test Parent", "role": "parent"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "parent"
        print("✓ Parent role member added")
    
    def test_add_member_with_member_role(self, auth_setup):
        """Test adding member with family member role"""
        headers = auth_setup["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test Member", "role": "member"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "member"
        print("✓ Family member role added")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
