import requests
import json
import time
import jwt
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/app/frontend/.env")
backend_url = os.environ.get("REACT_APP_BACKEND_URL")

if not backend_url:
    print("❌ Backend URL not found in environment variables")
    sys.exit(1)

print(f"🔗 Using backend URL: {backend_url}")

class TelegramAuthTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}
        self.access_token = None
        self.user_data = None
        
    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None, headers=None, measure_performance=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, headers=headers)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if measure_performance:
                print(f"⏱️ Response time: {response_time:.2f} ms")

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response data: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}...")
                    self.test_results[name] = {
                        "status": "passed",
                        "response_code": response.status_code,
                        "data": response_data,
                        "response_time_ms": response_time if measure_performance else None
                    }
                    return success, response_data
                except:
                    print("Response is not JSON")
                    self.test_results[name] = {
                        "status": "passed",
                        "response_code": response.status_code,
                        "data": response.text[:100],
                        "response_time_ms": response_time if measure_performance else None
                    }
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error data: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    self.test_results[name] = {
                        "status": "failed",
                        "response_code": response.status_code,
                        "error": error_data,
                        "response_time_ms": response_time if measure_performance else None
                    }
                except:
                    print(f"Error response: {response.text}")
                    self.test_results[name] = {
                        "status": "failed",
                        "response_code": response.status_code,
                        "error": response.text,
                        "response_time_ms": response_time if measure_performance else None
                    }
                return success, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results[name] = {
                "status": "error",
                "error": str(e)
            }
            return False, None
    
    def create_mock_telegram_init_data(self):
        """
        Create a mock Telegram initData for testing purposes
        Note: This won't pass the actual hash validation, but it's useful for testing error handling
        """
        user_data = {
            "id": 12345678,
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "language_code": "en"
        }
        
        init_data = {
            "user": json.dumps(user_data),
            "auth_date": int(datetime.now().timestamp()),
            "hash": "invalid_hash_for_testing"
        }
        
        # Convert to URL query string format
        return "&".join([f"{k}={v}" for k, v in init_data.items()])
    
    def create_test_jwt_token(self, user_id="test_user_id", telegram_id=12345678, expires_in_minutes=30):
        """Create a test JWT token for testing"""
        # Load the secret key from environment
        load_dotenv("/app/backend/.env")
        secret_key = os.environ.get("SECRET_KEY", "your-secret-key-for-jwt")
        
        payload = {
            "sub": user_id,
            "telegram_id": telegram_id,
            "username": "testuser",
            "first_name": "Test",
            "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        }
        
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def test_health_check(self):
        """Test the health check endpoint"""
        return self.run_test("Health Check", "GET", "api/health", measure_performance=True)
    
    def test_telegram_auth_with_invalid_data(self):
        """Test Telegram authentication with invalid data"""
        mock_init_data = self.create_mock_telegram_init_data()
        
        return self.run_test(
            "Telegram Auth with Invalid Data",
            "POST",
            "api/auth/telegram",
            400,  # Expect 400 Bad Request
            data={"init_data": mock_init_data}
        )
    
    def test_auth_verify_without_token(self):
        """Test auth verification without token"""
        return self.run_test(
            "Auth Verify without Token",
            "GET",
            "api/auth/verify",
            401  # Expect 401 Unauthorized
        )
    
    def test_auth_verify_with_invalid_token(self):
        """Test auth verification with invalid token"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer invalid_token_for_testing'
        }
        
        return self.run_test(
            "Auth Verify with Invalid Token",
            "GET",
            "api/auth/verify",
            401,  # Expect 401 Unauthorized
            headers=headers
        )
    
    def test_auth_verify_with_valid_token(self):
        """Test auth verification with valid token"""
        if not self.access_token:
            print("❌ Cannot test auth verification: No valid token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        return self.run_test(
            "Auth Verify with Valid Token",
            "GET",
            "api/auth/verify",
            200,
            headers=headers
        )
    
    def test_get_current_user_without_token(self):
        """Test getting current user without token"""
        return self.run_test(
            "Get Current User without Token",
            "GET",
            "api/auth/me",
            401  # Expect 401 Unauthorized
        )
    
    def test_get_current_user_with_invalid_token(self):
        """Test getting current user with invalid token"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer invalid_token_for_testing'
        }
        
        return self.run_test(
            "Get Current User with Invalid Token",
            "GET",
            "api/auth/me",
            401,  # Expect 401 Unauthorized
            headers=headers
        )
    
    def test_get_current_user_with_valid_token(self):
        """Test getting current user with valid token"""
        if not self.access_token:
            print("❌ Cannot test getting current user: No valid token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        return self.run_test(
            "Get Current User with Valid Token",
            "GET",
            "api/auth/me",
            200,
            headers=headers
        )
    
    def test_logout(self):
        """Test logout endpoint"""
        return self.run_test(
            "Logout",
            "POST",
            "api/auth/logout",
            200
        )
    
    def test_protected_endpoint_without_token(self):
        """Test accessing a protected endpoint without token"""
        return self.run_test(
            "Access Protected Endpoint without Token",
            "POST",
            "api/posts/jobs",
            401,  # Expect 401 Unauthorized
            data={
                "title": "Test Job Post",
                "description": "This is a test job post",
                "price": 1500,
                "currency_id": "some-currency-id",
                "super_rubric_id": "some-category-id",
                "city_id": "some-city-id"
            }
        )
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing a protected endpoint with invalid token"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer invalid_token_for_testing'
        }
        
        return self.run_test(
            "Access Protected Endpoint with Invalid Token",
            "POST",
            "api/posts/jobs",
            401,  # Expect 401 Unauthorized
            data={
                "title": "Test Job Post",
                "description": "This is a test job post",
                "price": 1500,
                "currency_id": "some-currency-id",
                "super_rubric_id": "some-category-id",
                "city_id": "some-city-id"
            },
            headers=headers
        )
    
    def run_all_tests(self):
        """Run all auth-related tests"""
        print("\n=== Running Telegram Auth API Tests ===\n")
        
        # Test health check first
        self.test_health_check()
        
        # Test authentication with invalid data
        self.test_telegram_auth_with_invalid_data()
        
        # Create a test token for further tests
        self.access_token = self.create_test_jwt_token()
        print(f"\n🔑 Created test JWT token for testing: {self.access_token[:20]}...")
        
        # Test auth verification
        self.test_auth_verify_without_token()
        self.test_auth_verify_with_invalid_token()
        self.test_auth_verify_with_valid_token()
        
        # Test getting current user
        self.test_get_current_user_without_token()
        self.test_get_current_user_with_invalid_token()
        self.test_get_current_user_with_valid_token()
        
        # Test logout
        self.test_logout()
        
        # Test protected endpoints
        self.test_protected_endpoint_without_token()
        self.test_protected_endpoint_with_invalid_token()
        
        # Print summary
        print(f"\n=== Test Summary ===")
        print(f"Total tests: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run) * 100:.2f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    # Run tests
    tester = TelegramAuthTester(backend_url)
    tester.run_all_tests()