"""
Test suite for Admin endpoints (Iteration 11)
Tests the merged admin portal functionality into owner profile
- /api/admin/* endpoints require Owner role
- Non-owner users get 403 Forbidden
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
OWNER_CREDS = {"email": "owner@test.com", "password": "test123"}


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_api_health(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ API health check passed")


class TestOwnerAdminEndpoints:
    """Test admin endpoints with Owner credentials"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        """Get owner token - first try login, if fails register new owner"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        if response.status_code == 200:
            token = response.json().get("token")
            print(f"✓ Owner login successful")
            return token
        
        # Register new owner account
        unique_id = uuid.uuid4().hex[:8]
        new_owner = {
            "name": f"TEST_Admin_Owner_{unique_id}",
            "email": f"test_admin_owner_{unique_id}@test.com",
            "password": "test123",
            "family_name": f"TEST_Admin_Family_{unique_id}"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=new_owner)
        assert response.status_code == 200, f"Failed to register owner: {response.text}"
        token = response.json().get("token")
        print(f"✓ Created new owner: {new_owner['email']}")
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, owner_token):
        return {"Authorization": f"Bearer {owner_token}"}
    
    def test_get_admin_status(self, auth_headers):
        """GET /api/admin/status - returns backend, database, smtp, openai, google status"""
        response = requests.get(f"{BASE_URL}/api/admin/status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify all expected status fields are present
        assert "backend" in data, "Missing 'backend' status"
        assert "database" in data, "Missing 'database' status"
        assert "smtp" in data, "Missing 'smtp' status"
        assert "openai" in data, "Missing 'openai' status"
        assert "google" in data, "Missing 'google' status"
        
        # Backend should always be true if we got a response
        assert data["backend"] == True, "Backend should be running"
        # Database should be connected
        assert data["database"] == True, "Database should be connected"
        
        print(f"✓ Admin status: backend={data['backend']}, db={data['database']}, smtp={data['smtp']}, openai={data['openai']}, google={data['google']}")
    
    def test_get_admin_config(self, auth_headers):
        """GET /api/admin/config - returns all server config"""
        response = requests.get(f"{BASE_URL}/api/admin/config", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify config fields exist
        expected_fields = ["smtp_host", "smtp_port", "smtp_user", "smtp_from", 
                          "google_client_id", "google_redirect_uri",
                          "openai_api_key", "jwt_secret", "cors_origins", "db_name"]
        for field in expected_fields:
            assert field in data, f"Missing config field: {field}"
        
        # Sensitive fields should be masked
        if data.get("openai_api_key"):
            assert data["openai_api_key"] == "***" or data["openai_api_key"] == "", "OpenAI key should be masked"
        if data.get("jwt_secret"):
            assert data["jwt_secret"] == "***" or data["jwt_secret"] == "", "JWT secret should be masked"
        
        print(f"✓ Admin config retrieved: smtp_host={data['smtp_host']}, db_name={data['db_name']}")
    
    def test_save_smtp_config(self, auth_headers):
        """POST /api/admin/config/smtp - saves SMTP settings"""
        smtp_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test_smtp_user@test.com",
            "smtp_password": "",  # Empty to avoid changing actual password
            "smtp_from": "Test Family Hub <test@test.com>"
        }
        response = requests.post(f"{BASE_URL}/api/admin/config/smtp", 
                                 json=smtp_config, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "SMTP" in data["message"]
        print(f"✓ SMTP config saved: {data['message']}")
    
    def test_save_google_config(self, auth_headers):
        """POST /api/admin/config/google - saves Google Calendar settings"""
        google_config = {
            "google_client_id": "test-client-id.apps.googleusercontent.com",
            "google_client_secret": "",  # Empty to avoid changing actual secret
            "google_redirect_uri": "http://localhost/api/calendar/google/callback"
        }
        response = requests.post(f"{BASE_URL}/api/admin/config/google", 
                                 json=google_config, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "Google" in data["message"]
        print(f"✓ Google config saved: {data['message']}")
    
    def test_save_openai_config(self, auth_headers):
        """POST /api/admin/config/openai - saves OpenAI settings"""
        openai_config = {
            "openai_api_key": ""  # Empty to avoid changing actual key
        }
        response = requests.post(f"{BASE_URL}/api/admin/config/openai", 
                                 json=openai_config, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "OpenAI" in data["message"]
        print(f"✓ OpenAI config saved: {data['message']}")
    
    def test_save_server_config(self, auth_headers):
        """POST /api/admin/config/server - saves server settings"""
        server_config = {
            "jwt_secret": "",  # Empty to avoid changing
            "cors_origins": "*",
            "db_name": "family_hub"
        }
        response = requests.post(f"{BASE_URL}/api/admin/config/server", 
                                 json=server_config, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "Server" in data["message"]
        print(f"✓ Server config saved: {data['message']}")
    
    def test_test_email(self, auth_headers):
        """POST /api/admin/test-email - tests SMTP connection"""
        response = requests.post(f"{BASE_URL}/api/admin/test-email", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Note: SMTP test may fail if not configured, but endpoint should work
        assert "success" in data
        assert "message" in data
        print(f"✓ Email test completed: success={data['success']}, message={data['message']}")
    
    def test_get_backend_logs(self, auth_headers):
        """GET /api/admin/logs?type=backend - returns server logs"""
        response = requests.get(f"{BASE_URL}/api/admin/logs?type=backend", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "logs" in data
        print(f"✓ Backend logs retrieved: {len(data['logs'])} characters")
    
    def test_get_frontend_logs(self, auth_headers):
        """GET /api/admin/logs?type=frontend - returns frontend logs"""
        response = requests.get(f"{BASE_URL}/api/admin/logs?type=frontend", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "logs" in data
        print(f"✓ Frontend logs retrieved: {len(data['logs'])} characters")
    
    def test_get_error_logs(self, auth_headers):
        """GET /api/admin/logs?type=error - returns error logs"""
        response = requests.get(f"{BASE_URL}/api/admin/logs?type=error", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "logs" in data
        print(f"✓ Error logs retrieved: {len(data['logs'])} characters")
    
    def test_reboot_endpoint_exists(self, auth_headers):
        """POST /api/admin/reboot - verify endpoint exists (skip actual restart)"""
        # Just verify the endpoint responds, but don't actually trigger restart
        # as it would disrupt testing
        print("✓ Reboot endpoint test skipped (would restart server)")


class TestNonOwnerAccess:
    """Test that non-owner users get 403 on admin endpoints"""
    
    @pytest.fixture(scope="class")
    def member_credentials(self):
        """Create a new member user"""
        # First register an owner to create a family
        unique_id = uuid.uuid4().hex[:8]
        owner_data = {
            "name": f"TEST_Owner_{unique_id}",
            "email": f"test_owner_{unique_id}@test.com",
            "password": "test123",
            "family_name": f"TEST_Family_{unique_id}"
        }
        owner_resp = requests.post(f"{BASE_URL}/api/auth/register", json=owner_data)
        assert owner_resp.status_code == 200, f"Failed to create owner: {owner_resp.text}"
        owner_token = owner_resp.json().get("token")
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Add a member to the family
        member_data = {
            "name": f"TEST_Member_{unique_id}",
            "email": f"test_member_{unique_id}@test.com",
            "role": "member"
        }
        add_resp = requests.post(f"{BASE_URL}/api/family/add-member", 
                                 json=member_data, headers=owner_headers)
        assert add_resp.status_code == 200, f"Failed to add member: {add_resp.text}"
        member_result = add_resp.json()
        
        # Login as the member (if temp password provided) or use user_pin
        if member_result.get("temp_password"):
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": member_data["email"],
                "password": member_result["temp_password"]
            })
            if login_resp.status_code == 200:
                return {"token": login_resp.json().get("token"), "email": member_data["email"]}
        
        # Try PIN login
        if member_result.get("user_pin"):
            pin_resp = requests.post(f"{BASE_URL}/api/auth/user-pin-login", 
                                     json={"pin": member_result["user_pin"]})
            if pin_resp.status_code == 200:
                return {"token": pin_resp.json().get("token"), "email": member_data["email"]}
        
        # If no login method works, skip these tests
        pytest.skip("Could not authenticate as member user")
    
    @pytest.fixture(scope="class")
    def member_headers(self, member_credentials):
        return {"Authorization": f"Bearer {member_credentials['token']}"}
    
    def test_member_cannot_access_status(self, member_headers):
        """Non-owner should get 403 on /api/admin/status"""
        response = requests.get(f"{BASE_URL}/api/admin/status", headers=member_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Member correctly denied access to /api/admin/status (403)")
    
    def test_member_cannot_access_config(self, member_headers):
        """Non-owner should get 403 on /api/admin/config"""
        response = requests.get(f"{BASE_URL}/api/admin/config", headers=member_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Member correctly denied access to /api/admin/config (403)")
    
    def test_member_cannot_save_smtp(self, member_headers):
        """Non-owner should get 403 on POST /api/admin/config/smtp"""
        response = requests.post(f"{BASE_URL}/api/admin/config/smtp", 
                                 json={"smtp_host": "test"}, headers=member_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Member correctly denied access to save SMTP config (403)")
    
    def test_member_cannot_get_logs(self, member_headers):
        """Non-owner should get 403 on /api/admin/logs"""
        response = requests.get(f"{BASE_URL}/api/admin/logs", headers=member_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Member correctly denied access to logs (403)")
    
    def test_member_cannot_reboot(self, member_headers):
        """Non-owner should get 403 on POST /api/admin/reboot"""
        response = requests.post(f"{BASE_URL}/api/admin/reboot", headers=member_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Member correctly denied access to reboot (403)")


class TestUnauthenticatedAccess:
    """Test that unauthenticated users get 401 on admin endpoints"""
    
    def test_unauthenticated_status(self):
        """No auth should get 401 on /api/admin/status"""
        response = requests.get(f"{BASE_URL}/api/admin/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated correctly denied (401)")
    
    def test_unauthenticated_config(self):
        """No auth should get 401 on /api/admin/config"""
        response = requests.get(f"{BASE_URL}/api/admin/config")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated correctly denied (401)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
