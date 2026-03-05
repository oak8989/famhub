"""
Family Hub Permission Tests
Comprehensive testing at ALL permission levels: Owner, Parent, Family Member, Child
Tests: Add member permissions, Change family name, Server settings access, Module visibility
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

TEST_PASSWORD = "test123"


class TestPermissionSetup:
    """Setup test family with users at all permission levels"""
    
    @pytest.fixture(scope="class")
    def family_with_all_roles(self):
        """Create a family with owner, parent, member, and child users"""
        # Create owner and family
        owner_email = f"owner_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register owner
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Owner",
            "email": owner_email,
            "password": TEST_PASSWORD,
            "role": "owner"
        })
        assert reg_resp.status_code == 200, f"Owner registration failed: {reg_resp.text}"
        
        # Login owner
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create family
        family_resp = requests.post(f"{BASE_URL}/api/family/create",
            json={"name": "Permission Test Family"},
            headers=owner_headers
        )
        assert family_resp.status_code == 200
        family_data = family_resp.json()
        family_pin = family_data["pin"]
        
        # Re-login owner to get updated token with family_id
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        owner_id = login_resp.json()["user"]["id"]
        
        # Add parent member
        parent_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test Parent", "role": "parent"},
            headers=owner_headers
        )
        assert parent_resp.status_code == 200
        parent_pin = parent_resp.json()["user_pin"]
        parent_id = parent_resp.json()["user_id"]
        
        # Add family member
        member_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test Member", "role": "member"},
            headers=owner_headers
        )
        assert member_resp.status_code == 200
        member_pin = member_resp.json()["user_pin"]
        member_id = member_resp.json()["user_id"]
        
        # Add child member
        child_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test Child", "role": "child"},
            headers=owner_headers
        )
        assert child_resp.status_code == 200
        child_pin = child_resp.json()["user_pin"]
        child_id = child_resp.json()["user_id"]
        
        # Get tokens for each role via PIN login
        parent_login = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={"pin": parent_pin})
        assert parent_login.status_code == 200
        parent_token = parent_login.json()["token"]
        
        member_login = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={"pin": member_pin})
        assert member_login.status_code == 200
        member_token = member_login.json()["token"]
        
        child_login = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={"pin": child_pin})
        assert child_login.status_code == 200
        child_token = child_login.json()["token"]
        
        print(f"✓ Family created with all roles - Family PIN: {family_pin}")
        
        return {
            "family_pin": family_pin,
            "owner": {"id": owner_id, "token": owner_token, "headers": {"Authorization": f"Bearer {owner_token}"}},
            "parent": {"id": parent_id, "token": parent_token, "headers": {"Authorization": f"Bearer {parent_token}"}},
            "member": {"id": member_id, "token": member_token, "headers": {"Authorization": f"Bearer {member_token}"}},
            "child": {"id": child_id, "token": child_token, "headers": {"Authorization": f"Bearer {child_token}"}},
        }


class TestAddMemberPermissions(TestPermissionSetup):
    """Test add member permissions for each role"""
    
    def test_owner_can_add_member(self, family_with_all_roles):
        """Owner should be able to add members"""
        headers = family_with_all_roles["owner"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "New Member by Owner", "role": "member"},
            headers=headers
        )
        assert response.status_code == 200, f"Owner should be able to add member: {response.text}"
        print("✓ Owner CAN add member - PASS")
    
    def test_parent_can_add_member(self, family_with_all_roles):
        """Parent should be able to add members"""
        headers = family_with_all_roles["parent"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "New Member by Parent", "role": "child"},
            headers=headers
        )
        assert response.status_code == 200, f"Parent should be able to add member: {response.text}"
        print("✓ Parent CAN add member - PASS")
    
    def test_member_cannot_add_member(self, family_with_all_roles):
        """Family Member should NOT be able to add members (403)"""
        headers = family_with_all_roles["member"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "New Member by Member", "role": "child"},
            headers=headers
        )
        assert response.status_code == 403, f"Member should NOT be able to add member, got {response.status_code}: {response.text}"
        print("✓ Member CANNOT add member (403) - PASS")
    
    def test_child_cannot_add_member(self, family_with_all_roles):
        """Child should NOT be able to add members (403)"""
        headers = family_with_all_roles["child"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "New Member by Child", "role": "child"},
            headers=headers
        )
        assert response.status_code == 403, f"Child should NOT be able to add member, got {response.status_code}: {response.text}"
        print("✓ Child CANNOT add member (403) - PASS")


class TestChangeFamilyNamePermissions(TestPermissionSetup):
    """Test change family name permissions for each role"""
    
    def test_owner_can_change_family_name(self, family_with_all_roles):
        """Owner should be able to change family name"""
        headers = family_with_all_roles["owner"]["headers"]
        response = requests.put(f"{BASE_URL}/api/family",
            json={"name": "Updated by Owner"},
            headers=headers
        )
        assert response.status_code == 200, f"Owner should be able to change family name: {response.text}"
        print("✓ Owner CAN change family name - PASS")
    
    def test_parent_can_change_family_name(self, family_with_all_roles):
        """Parent should be able to change family name"""
        headers = family_with_all_roles["parent"]["headers"]
        response = requests.put(f"{BASE_URL}/api/family",
            json={"name": "Updated by Parent"},
            headers=headers
        )
        assert response.status_code == 200, f"Parent should be able to change family name: {response.text}"
        print("✓ Parent CAN change family name - PASS")
    
    def test_member_cannot_change_family_name(self, family_with_all_roles):
        """Family Member should NOT be able to change family name"""
        headers = family_with_all_roles["member"]["headers"]
        response = requests.put(f"{BASE_URL}/api/family",
            json={"name": "Updated by Member"},
            headers=headers
        )
        assert response.status_code == 403, f"Member should NOT be able to change family name, got {response.status_code}: {response.text}"
        print("✓ Member CANNOT change family name (403) - PASS")
    
    def test_child_cannot_change_family_name(self, family_with_all_roles):
        """Child should NOT be able to change family name"""
        headers = family_with_all_roles["child"]["headers"]
        response = requests.put(f"{BASE_URL}/api/family",
            json={"name": "Updated by Child"},
            headers=headers
        )
        assert response.status_code == 403, f"Child should NOT be able to change family name, got {response.status_code}: {response.text}"
        print("✓ Child CANNOT change family name (403) - PASS")


class TestServerSettingsPermissions(TestPermissionSetup):
    """Test server settings access permissions"""
    
    def test_owner_can_access_server_settings(self, family_with_all_roles):
        """Owner should be able to access server settings"""
        headers = family_with_all_roles["owner"]["headers"]
        response = requests.get(f"{BASE_URL}/api/settings/server", headers=headers)
        assert response.status_code == 200, f"Owner should access server settings: {response.text}"
        print("✓ Owner CAN access server settings - PASS")
    
    def test_parent_cannot_access_server_settings(self, family_with_all_roles):
        """Parent should NOT be able to access server settings"""
        headers = family_with_all_roles["parent"]["headers"]
        response = requests.get(f"{BASE_URL}/api/settings/server", headers=headers)
        assert response.status_code == 403, f"Parent should NOT access server settings, got {response.status_code}: {response.text}"
        print("✓ Parent CANNOT access server settings (403) - PASS")
    
    def test_member_cannot_access_server_settings(self, family_with_all_roles):
        """Member should NOT be able to access server settings"""
        headers = family_with_all_roles["member"]["headers"]
        response = requests.get(f"{BASE_URL}/api/settings/server", headers=headers)
        assert response.status_code == 403, f"Member should NOT access server settings, got {response.status_code}: {response.text}"
        print("✓ Member CANNOT access server settings (403) - PASS")
    
    def test_child_cannot_access_server_settings(self, family_with_all_roles):
        """Child should NOT be able to access server settings"""
        headers = family_with_all_roles["child"]["headers"]
        response = requests.get(f"{BASE_URL}/api/settings/server", headers=headers)
        assert response.status_code == 403, f"Child should NOT access server settings, got {response.status_code}: {response.text}"
        print("✓ Child CANNOT access server settings (403) - PASS")


class TestUpdateSettingsPermissions(TestPermissionSetup):
    """Test update settings permissions"""
    
    def test_owner_can_update_settings(self, family_with_all_roles):
        """Owner should be able to update settings"""
        headers = family_with_all_roles["owner"]["headers"]
        response = requests.put(f"{BASE_URL}/api/settings",
            json={"modules": {"calendar": {"enabled": True, "visible_to": ["owner", "parent"]}}},
            headers=headers
        )
        assert response.status_code == 200, f"Owner should update settings: {response.text}"
        print("✓ Owner CAN update settings - PASS")
    
    def test_parent_can_update_settings(self, family_with_all_roles):
        """Parent should be able to update settings"""
        headers = family_with_all_roles["parent"]["headers"]
        response = requests.put(f"{BASE_URL}/api/settings",
            json={"modules": {"calendar": {"enabled": True, "visible_to": ["owner", "parent", "member"]}}},
            headers=headers
        )
        assert response.status_code == 200, f"Parent should update settings: {response.text}"
        print("✓ Parent CAN update settings - PASS")
    
    def test_member_cannot_update_settings(self, family_with_all_roles):
        """Member should NOT be able to update settings"""
        headers = family_with_all_roles["member"]["headers"]
        response = requests.put(f"{BASE_URL}/api/settings",
            json={"modules": {"calendar": {"enabled": False}}},
            headers=headers
        )
        assert response.status_code == 403, f"Member should NOT update settings, got {response.status_code}: {response.text}"
        print("✓ Member CANNOT update settings (403) - PASS")
    
    def test_child_cannot_update_settings(self, family_with_all_roles):
        """Child should NOT be able to update settings"""
        headers = family_with_all_roles["child"]["headers"]
        response = requests.put(f"{BASE_URL}/api/settings",
            json={"modules": {"calendar": {"enabled": False}}},
            headers=headers
        )
        assert response.status_code == 403, f"Child should NOT update settings, got {response.status_code}: {response.text}"
        print("✓ Child CANNOT update settings (403) - PASS")


class TestRegeneratePinPermissions(TestPermissionSetup):
    """Test regenerate family PIN permissions"""
    
    def test_owner_can_regenerate_family_pin(self, family_with_all_roles):
        """Owner should be able to regenerate family PIN"""
        headers = family_with_all_roles["owner"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/regenerate-pin", headers=headers)
        assert response.status_code == 200, f"Owner should regenerate PIN: {response.text}"
        print("✓ Owner CAN regenerate family PIN - PASS")
    
    def test_parent_can_regenerate_family_pin(self, family_with_all_roles):
        """Parent should be able to regenerate family PIN"""
        headers = family_with_all_roles["parent"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/regenerate-pin", headers=headers)
        assert response.status_code == 200, f"Parent should regenerate PIN: {response.text}"
        print("✓ Parent CAN regenerate family PIN - PASS")
    
    def test_member_cannot_regenerate_family_pin(self, family_with_all_roles):
        """Member should NOT be able to regenerate family PIN"""
        headers = family_with_all_roles["member"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/regenerate-pin", headers=headers)
        assert response.status_code == 403, f"Member should NOT regenerate PIN, got {response.status_code}: {response.text}"
        print("✓ Member CANNOT regenerate family PIN (403) - PASS")
    
    def test_child_cannot_regenerate_family_pin(self, family_with_all_roles):
        """Child should NOT be able to regenerate family PIN"""
        headers = family_with_all_roles["child"]["headers"]
        response = requests.post(f"{BASE_URL}/api/family/regenerate-pin", headers=headers)
        assert response.status_code == 403, f"Child should NOT regenerate PIN, got {response.status_code}: {response.text}"
        print("✓ Child CANNOT regenerate family PIN (403) - PASS")


class TestCreateRewardPermissions(TestPermissionSetup):
    """Test create reward permissions"""
    
    def test_owner_can_create_reward(self, family_with_all_roles):
        """Owner should be able to create rewards"""
        headers = family_with_all_roles["owner"]["headers"]
        response = requests.post(f"{BASE_URL}/api/rewards",
            json={"name": "Ice Cream", "description": "Get ice cream", "points_required": 50},
            headers=headers
        )
        assert response.status_code == 200, f"Owner should create reward: {response.text}"
        print("✓ Owner CAN create reward - PASS")
    
    def test_parent_can_create_reward(self, family_with_all_roles):
        """Parent should be able to create rewards"""
        headers = family_with_all_roles["parent"]["headers"]
        response = requests.post(f"{BASE_URL}/api/rewards",
            json={"name": "Movie Night", "description": "Watch a movie", "points_required": 100},
            headers=headers
        )
        assert response.status_code == 200, f"Parent should create reward: {response.text}"
        print("✓ Parent CAN create reward - PASS")
    
    def test_member_cannot_create_reward(self, family_with_all_roles):
        """Member should NOT be able to create rewards"""
        headers = family_with_all_roles["member"]["headers"]
        response = requests.post(f"{BASE_URL}/api/rewards",
            json={"name": "Unauthorized Reward", "points_required": 10},
            headers=headers
        )
        assert response.status_code == 403, f"Member should NOT create reward, got {response.status_code}: {response.text}"
        print("✓ Member CANNOT create reward (403) - PASS")
    
    def test_child_cannot_create_reward(self, family_with_all_roles):
        """Child should NOT be able to create rewards"""
        headers = family_with_all_roles["child"]["headers"]
        response = requests.post(f"{BASE_URL}/api/rewards",
            json={"name": "Unauthorized Reward", "points_required": 10},
            headers=headers
        )
        assert response.status_code == 403, f"Child should NOT create reward, got {response.status_code}: {response.text}"
        print("✓ Child CANNOT create reward (403) - PASS")


class TestFamilyPinLogin:
    """Test Family PIN login creates guest user with child role"""
    
    def test_family_pin_login_creates_child_role(self):
        """Family PIN login should create guest user with child role"""
        # First create a family
        owner_email = f"pintest_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register owner
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "PIN Test Owner",
            "email": owner_email,
            "password": TEST_PASSWORD,
            "role": "owner"
        })
        
        # Login owner
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create family
        family_resp = requests.post(f"{BASE_URL}/api/family/create",
            json={"name": "PIN Test Family"},
            headers=owner_headers
        )
        family_pin = family_resp.json()["pin"]
        
        # Login with family PIN (6 digits)
        pin_login_resp = requests.post(f"{BASE_URL}/api/auth/pin-login", json={"pin": family_pin})
        assert pin_login_resp.status_code == 200
        
        data = pin_login_resp.json()
        assert "token" in data
        assert "family" in data
        
        # Verify the token gives child-level access
        guest_headers = {"Authorization": f"Bearer {data['token']}"}
        
        # Guest should NOT be able to add members (child role)
        add_member_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Test", "role": "child"},
            headers=guest_headers
        )
        assert add_member_resp.status_code == 403, f"Family PIN guest should have child role (403), got {add_member_resp.status_code}"
        
        print("✓ Family PIN login creates guest with child role - PASS")


class TestPersonalPinLogin:
    """Test Personal PIN login logs in specific user with their role"""
    
    def test_personal_pin_login_preserves_role(self):
        """Personal PIN login should preserve user's assigned role"""
        # Create a family with a parent user
        owner_email = f"personal_pin_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register owner
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Personal PIN Owner",
            "email": owner_email,
            "password": TEST_PASSWORD,
            "role": "owner"
        })
        
        # Login owner
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create family
        requests.post(f"{BASE_URL}/api/family/create",
            json={"name": "Personal PIN Family"},
            headers=owner_headers
        )
        
        # Re-login to get updated token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Add a parent member
        parent_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Parent User", "role": "parent"},
            headers=owner_headers
        )
        parent_pin = parent_resp.json()["user_pin"]
        
        # Login with personal PIN (4 digits)
        pin_login_resp = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={"pin": parent_pin})
        assert pin_login_resp.status_code == 200
        
        data = pin_login_resp.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "parent", f"Expected parent role, got {data['user']['role']}"
        
        # Verify parent can add members
        parent_headers = {"Authorization": f"Bearer {data['token']}"}
        add_member_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Added by Parent", "role": "child"},
            headers=parent_headers
        )
        assert add_member_resp.status_code == 200, f"Parent should be able to add members: {add_member_resp.text}"
        
        print("✓ Personal PIN login preserves user role - PASS")


class TestChoreCompletionPoints:
    """Test chore completion awards points to correct user"""
    
    def test_chore_completion_awards_points_to_assigned_user(self):
        """Completing a chore should award points to the assigned user"""
        # Setup
        owner_email = f"chore_points_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register owner
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Chore Points Owner",
            "email": owner_email,
            "password": TEST_PASSWORD,
            "role": "owner"
        })
        
        # Login owner
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create family
        requests.post(f"{BASE_URL}/api/family/create",
            json={"name": "Chore Points Family"},
            headers=owner_headers
        )
        
        # Re-login to get updated token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Add a child member
        child_resp = requests.post(f"{BASE_URL}/api/family/add-member",
            json={"name": "Points Child", "role": "child"},
            headers=owner_headers
        )
        child_id = child_resp.json()["user_id"]
        child_pin = child_resp.json()["user_pin"]
        
        # Get child's initial points
        child_login = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={"pin": child_pin})
        initial_points = child_login.json()["user"]["points"]
        
        # Create a chore assigned to child (medium = 10 points)
        chore_resp = requests.post(f"{BASE_URL}/api/chores",
            json={"title": "Test Chore", "difficulty": "medium", "assigned_to": child_id},
            headers=owner_headers
        )
        chore_id = chore_resp.json()["id"]
        chore_points = chore_resp.json()["points"]
        
        # Complete the chore
        complete_resp = requests.post(f"{BASE_URL}/api/chores/{chore_id}/complete", headers=owner_headers)
        assert complete_resp.status_code == 200
        assert complete_resp.json()["points_earned"] == chore_points
        
        # Verify child's points increased
        child_login = requests.post(f"{BASE_URL}/api/auth/user-pin-login", json={"pin": child_pin})
        final_points = child_login.json()["user"]["points"]
        
        assert final_points == initial_points + chore_points, f"Expected {initial_points + chore_points} points, got {final_points}"
        print(f"✓ Chore completion awarded {chore_points} points to assigned user - PASS")


class TestRewardClaiming:
    """Test reward claiming deducts points correctly"""
    
    def test_reward_claiming_deducts_points(self):
        """Claiming a reward should deduct points from user"""
        # Setup
        owner_email = f"reward_claim_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register owner
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Reward Claim Owner",
            "email": owner_email,
            "password": TEST_PASSWORD,
            "role": "owner"
        })
        
        # Login owner
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_id = login_resp.json()["user"]["id"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create family
        requests.post(f"{BASE_URL}/api/family/create",
            json={"name": "Reward Claim Family"},
            headers=owner_headers
        )
        
        # Re-login to get updated token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": owner_email,
            "password": TEST_PASSWORD
        })
        owner_token = login_resp.json()["token"]
        owner_id = login_resp.json()["user"]["id"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Complete some chores to earn points
        for i in range(3):
            chore_resp = requests.post(f"{BASE_URL}/api/chores",
                json={"title": f"Earn Points Chore {i}", "difficulty": "hard", "assigned_to": owner_id},
                headers=owner_headers
            )
            chore_id = chore_resp.json()["id"]
            requests.post(f"{BASE_URL}/api/chores/{chore_id}/complete", headers=owner_headers)
        
        # Get current points
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=owner_headers)
        initial_points = me_resp.json()["points"]
        
        # Create a reward
        reward_resp = requests.post(f"{BASE_URL}/api/rewards",
            json={"name": "Test Reward", "description": "Test", "points_required": 30},
            headers=owner_headers
        )
        reward_id = reward_resp.json()["id"]
        
        # Claim the reward
        claim_resp = requests.post(f"{BASE_URL}/api/rewards/claim",
            json={"reward_id": reward_id, "user_id": owner_id},
            headers=owner_headers
        )
        assert claim_resp.status_code == 200
        assert claim_resp.json()["points_spent"] == 30
        
        # Verify points deducted
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=owner_headers)
        final_points = me_resp.json()["points"]
        
        assert final_points == initial_points - 30, f"Expected {initial_points - 30} points, got {final_points}"
        print(f"✓ Reward claiming deducted 30 points correctly - PASS")


class TestCreateFamilyFlow:
    """Test create new family from registration flow"""
    
    def test_register_then_create_family_flow(self):
        """Test: Register -> Login -> Create Family -> Become Owner"""
        # Step 1: Register new user
        user_email = f"new_family_{uuid.uuid4().hex[:8]}@test.com"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "New Family Creator",
            "email": user_email,
            "password": TEST_PASSWORD,
            "role": "member"  # Start as member
        })
        assert reg_resp.status_code == 200
        user_pin = reg_resp.json()["user_pin"]
        print(f"✓ Step 1: User registered with PIN {user_pin}")
        
        # Step 2: Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✓ Step 2: User logged in")
        
        # Step 3: Create family
        family_resp = requests.post(f"{BASE_URL}/api/family/create",
            json={"name": "My New Family"},
            headers=headers
        )
        assert family_resp.status_code == 200
        family_data = family_resp.json()
        assert "pin" in family_data
        assert len(family_data["pin"]) == 6
        print(f"✓ Step 3: Family created with PIN {family_data['pin']}")
        
        # Step 4: Re-login to get updated token with family_id
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": user_email,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        user_data = login_resp.json()["user"]
        
        # Verify user is now owner
        assert user_data["role"] == "owner", f"Expected owner role, got {user_data['role']}"
        assert user_data["family_id"] == family_data["id"]
        print("✓ Step 4: User is now owner of the family")
        
        # Step 5: Verify owner permissions
        token = login_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Owner should be able to access server settings
        server_resp = requests.get(f"{BASE_URL}/api/settings/server", headers=headers)
        assert server_resp.status_code == 200
        print("✓ Step 5: Owner has full permissions")
        
        print("✓ Create Family Flow COMPLETE - PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
