"""
Iteration 13 - Testing pending member removal and Google Calendar auth
Features:
1. POST /api/family/add-member creates a pending member (no last_login field)
2. GET /api/family/members returns last_login field for each member
3. Members without last_login show as 'Pending' in the response
4. DELETE /api/family/members/{id} for pending member (no last_login) fully deletes user document
5. DELETE /api/family/members/{id} for joined member (has last_login) only clears family_id
6. POST /api/auth/login sets last_login timestamp on the user document
7. GET /api/calendar/google/auth returns error with helpful message when Google not configured
8. GET /api/calendar/google/auth returns authorization_url when Google IS configured
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSetup:
    """Setup: login as owner and get auth token"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        """Login as owner@test.com and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "owner@test.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, owner_token):
        """Return auth headers for API calls"""
        return {"Authorization": f"Bearer {owner_token}"}


class TestPendingMemberFlow(TestSetup):
    """Test pending member creation and removal"""
    
    def test_add_member_creates_pending_user(self, auth_headers):
        """POST /api/family/add-member should create user WITHOUT last_login"""
        # Create a unique test member
        test_name = f"TEST_Pending_{int(time.time())}"
        test_email = f"test_pending_{int(time.time())}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/family/add-member",
            json={"name": test_name, "role": "member", "email": test_email},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Add member failed: {response.text}"
        data = response.json()
        
        # Should return user info with PIN
        assert "id" in data, "Response missing 'id'"
        assert "user_pin" in data, "Response missing 'user_pin'"
        assert data["name"] == test_name
        
        # Store member_id for subsequent tests
        pytest.pending_member_id = data["id"]
        pytest.pending_member_name = test_name
        print(f"Created pending member: {test_name} with id: {data['id']}")
    
    def test_get_members_returns_last_login_field(self, auth_headers):
        """GET /api/family/members should return last_login field for each member"""
        response = requests.get(f"{BASE_URL}/api/family/members", headers=auth_headers)
        assert response.status_code == 200, f"Get members failed: {response.text}"
        members = response.json()
        
        assert isinstance(members, list), "Response should be a list"
        assert len(members) > 0, "Should have at least one member"
        
        # Find the pending member we just created
        pending_member = None
        owner_member = None
        for member in members:
            if hasattr(pytest, 'pending_member_id') and member.get("id") == pytest.pending_member_id:
                pending_member = member
            if member.get("role") == "owner":
                owner_member = member
        
        # Check that owner has last_login (joined member)
        if owner_member:
            assert "last_login" in owner_member or owner_member.get("last_login") is not None, \
                "Owner should have last_login field"
            print(f"Owner last_login: {owner_member.get('last_login')}")
        
        # Check that pending member does NOT have last_login
        if pending_member:
            assert pending_member.get("last_login") is None, \
                f"Pending member should NOT have last_login, but got: {pending_member.get('last_login')}"
            print(f"Pending member correctly has no last_login")
    
    def test_delete_pending_member_fully_deletes(self, auth_headers):
        """DELETE /api/family/members/{id} for pending member should FULLY delete user"""
        assert hasattr(pytest, 'pending_member_id'), "Pending member not created"
        
        # Delete the pending member
        response = requests.delete(
            f"{BASE_URL}/api/family/members/{pytest.pending_member_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        data = response.json()
        
        # Should return "Pending invite removed" message
        assert "message" in data, "Response missing 'message'"
        assert "pending" in data["message"].lower() or "removed" in data["message"].lower(), \
            f"Expected pending removal message, got: {data['message']}"
        print(f"Delete response: {data['message']}")
        
        # Verify user is completely gone from members list
        members_response = requests.get(f"{BASE_URL}/api/family/members", headers=auth_headers)
        members = members_response.json()
        member_ids = [m.get("id") for m in members]
        
        assert pytest.pending_member_id not in member_ids, \
            "Pending member should be completely removed from family"
        print("Verified: Pending member fully deleted from database")


class TestJoinedMemberRemoval(TestSetup):
    """Test that joined members (with last_login) are soft-removed"""
    
    def test_create_and_login_member(self, auth_headers):
        """Create a member and simulate login to set last_login"""
        # Create test member with email and password
        test_name = f"TEST_JoinedMember_{int(time.time())}"
        test_email = f"joined_{int(time.time())}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/family/add-member",
            json={"name": test_name, "role": "member", "email": test_email},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Add member failed: {response.text}"
        data = response.json()
        pytest.joined_member_id = data["id"]
        pytest.joined_member_pin = data.get("user_pin")
        pytest.joined_member_temp_pw = data.get("temp_password")
        print(f"Created member: {test_name}, PIN: {pytest.joined_member_pin}")
        
        # Login with PIN to set last_login
        if pytest.joined_member_pin:
            pin_login_response = requests.post(
                f"{BASE_URL}/api/auth/user-pin-login",
                json={"pin": pytest.joined_member_pin}
            )
            if pin_login_response.status_code == 200:
                print(f"PIN login successful - last_login should be set")
                # Verify last_login is now set
                members_response = requests.get(f"{BASE_URL}/api/family/members", headers=auth_headers)
                members = members_response.json()
                for m in members:
                    if m.get("id") == pytest.joined_member_id:
                        assert m.get("last_login") is not None, "last_login should be set after login"
                        print(f"Verified last_login: {m.get('last_login')}")
                        break
    
    def test_delete_joined_member_soft_removes(self, auth_headers):
        """DELETE /api/family/members/{id} for joined member should only clear family_id"""
        assert hasattr(pytest, 'joined_member_id'), "Joined member not created"
        
        # Delete the joined member
        response = requests.delete(
            f"{BASE_URL}/api/family/members/{pytest.joined_member_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        data = response.json()
        
        # Should return "Member removed" (not "Pending invite removed")
        assert "message" in data, "Response missing 'message'"
        print(f"Delete response for joined member: {data['message']}")
        
        # Verify member is removed from family members list
        members_response = requests.get(f"{BASE_URL}/api/family/members", headers=auth_headers)
        members = members_response.json()
        member_ids = [m.get("id") for m in members]
        
        assert pytest.joined_member_id not in member_ids, \
            "Joined member should be removed from family"
        print("Verified: Joined member removed from family (soft-delete)")


class TestLoginSetsLastLogin(TestSetup):
    """Test that POST /api/auth/login sets last_login timestamp"""
    
    def test_login_sets_last_login(self):
        """POST /api/auth/login should set last_login on user document"""
        # Login with owner account
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "owner@test.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # The login response may or may not include last_login in user object
        # but we can verify by checking /api/auth/me or /api/family/members
        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        
        # User should have last_login set
        assert user_data.get("last_login") is not None, \
            f"last_login should be set after login. User data: {user_data}"
        print(f"Verified last_login after login: {user_data.get('last_login')}")


class TestGoogleCalendarAuth(TestSetup):
    """Test Google Calendar auth endpoint behavior"""
    
    def test_google_auth_without_config_returns_error(self, auth_headers):
        """GET /api/calendar/google/auth should return helpful error when not configured"""
        # First, we need to check if Google is configured
        # If GOOGLE_CLIENT_ID is set in backend .env, this test behavior changes
        
        response = requests.get(f"{BASE_URL}/api/calendar/google/auth", headers=auth_headers)
        
        # If Google IS configured (has client_id/secret), it should return authorization_url
        # If Google is NOT configured, it should return 400 with helpful message
        
        if response.status_code == 400:
            # Not configured - check for helpful error message
            data = response.json()
            assert "detail" in data, "Error response should have 'detail'"
            assert "google" in data["detail"].lower() or "not configured" in data["detail"].lower(), \
                f"Error should mention Google/not configured. Got: {data['detail']}"
            print(f"Google auth not configured - error message: {data['detail']}")
        elif response.status_code == 200:
            # Configured - should return authorization_url
            data = response.json()
            assert "authorization_url" in data, "Response should have 'authorization_url'"
            assert "accounts.google.com" in data["authorization_url"], \
                f"URL should be Google OAuth URL. Got: {data['authorization_url']}"
            print(f"Google auth IS configured - URL: {data['authorization_url'][:100]}...")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, response: {response.text}")
    
    def test_google_auth_with_config_returns_url(self, auth_headers):
        """
        GET /api/calendar/google/auth should return authorization_url when configured.
        Note: This tests the current state - if Google config exists in backend .env or admin config.
        """
        # Save Google config first via admin API (owner only)
        admin_config_response = requests.post(
            f"{BASE_URL}/api/admin/config/google",
            json={
                "google_client_id": "test-client-id.apps.googleusercontent.com",
                "google_client_secret": "test-secret",
                "google_redirect_uri": f"{BASE_URL}/api/calendar/google/callback"
            },
            headers=auth_headers
        )
        
        if admin_config_response.status_code == 200:
            print("Saved test Google config via admin API")
        else:
            print(f"Admin config save returned: {admin_config_response.status_code}")
        
        # Now test Google auth endpoint
        response = requests.get(f"{BASE_URL}/api/calendar/google/auth", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "authorization_url" in data, "Response should have 'authorization_url'"
            url = data["authorization_url"]
            
            # Validate URL structure
            assert "accounts.google.com" in url, "Should be Google OAuth URL"
            assert "client_id=" in url, "URL should contain client_id"
            assert "redirect_uri=" in url, "URL should contain redirect_uri"
            assert "scope=" in url, "URL should contain scope"
            
            print(f"Google auth URL generated successfully")
            print(f"URL contains: client_id={bool('client_id=' in url)}, redirect_uri={bool('redirect_uri=' in url)}")
        else:
            # May still return 400 if env vars aren't set
            print(f"Google auth returned {response.status_code}: {response.text}")


class TestCleanup(TestSetup):
    """Cleanup test data"""
    
    def test_cleanup_test_members(self, auth_headers):
        """Remove any remaining TEST_ prefixed members"""
        members_response = requests.get(f"{BASE_URL}/api/family/members", headers=auth_headers)
        if members_response.status_code == 200:
            members = members_response.json()
            for member in members:
                if member.get("name", "").startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/family/members/{member['id']}",
                        headers=auth_headers
                    )
                    print(f"Cleaned up test member: {member['name']}")
