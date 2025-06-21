#!/usr/bin/env python3
"""
Backend API Test Script for Telegram Marketplace
Tests the backend API after fixes and improvements
"""
import requests
import sys
import json
import os
from datetime import datetime

class BackendAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}
        self.performance_metrics = {}
    
    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None, headers=None, measure_performance=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            import time
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, headers=headers)
            elif method == 'OPTIONS':
                response = requests.options(url, headers=headers)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if measure_performance:
                self.performance_metrics[name] = {
                    "response_time_ms": response_time,
                    "endpoint": endpoint,
                    "method": method
                }
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
    
    def test_health_check(self):
        """Test the health check endpoint"""
        return self.run_test("Health Check", "GET", "api/health", measure_performance=True)
    
    def test_get_all_reference_data(self):
        """Test getting all reference data in one request"""
        success, data = self.run_test("Get All Reference Data", "GET", "api/categories/all", measure_performance=True)
        if success:
            # Verify the response contains all expected sections
            expected_sections = ["categories", "cities", "currencies", "packages"]
            missing_sections = [section for section in expected_sections if section not in data]
            
            if not missing_sections:
                print(f"✅ Verified: Response contains all expected sections: {', '.join(expected_sections)}")
                
                # Verify data counts
                print(f"Categories count: {len(data.get('categories', []))}")
                print(f"Cities count: {len(data.get('cities', []))}")
                print(f"Currencies count: {len(data.get('currencies', []))}")
                print(f"Packages count: {len(data.get('packages', []))}")
                
                # Verify packages have parsed features
                if data.get("packages") and len(data["packages"]) > 0:
                    first_package = data["packages"][0]
                    if "features_ru" in first_package and isinstance(first_package["features_ru"], list):
                        print("✅ Verified: Package features are correctly parsed as lists")
                    else:
                        print("❌ Verification failed: Package features are not parsed as lists")
            else:
                print(f"❌ Verification failed: Response missing sections: {', '.join(missing_sections)}")
        
        return success, data
    
    def test_get_posts(self):
        """Test getting all posts"""
        return self.run_test("Get All Posts", "GET", "api/posts/", measure_performance=True)
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n🔍 Testing CORS configuration...")
        
        # Test with OPTIONS request
        headers = {
            "Origin": self.base_url,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        # FastAPI returns 200 for OPTIONS requests, not 204
        success, _ = self.run_test("CORS Preflight", "OPTIONS", "api/health", 200, headers=headers)
        
        if success:
            # Make a regular request and check CORS headers
            response = requests.get(f"{self.base_url}/api/health", headers={"Origin": self.base_url})
            
            if 'Access-Control-Allow-Origin' in response.headers:
                allowed_origin = response.headers['Access-Control-Allow-Origin']
                print(f"✅ CORS is configured correctly. Allowed origin: {allowed_origin}")
                
                # Check if our domain is allowed
                if self.base_url in allowed_origin or allowed_origin == '*':
                    print(f"✅ Frontend domain {self.base_url} is allowed by CORS")
                    return True, {"allowed_origin": allowed_origin}
                else:
                    print(f"❌ Frontend domain {self.base_url} is NOT allowed by CORS")
            else:
                print("❌ CORS headers not found in response")
        
        return False, None
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🔍 Testing error handling...")
        
        # Test with invalid endpoint
        success, _ = self.run_test("404 Error Handling", "GET", "api/nonexistent", 404)
        
        # For this test, we expect a 404 response which is considered a "success" in our test framework
        # because we specified 404 as the expected status code
        if success:
            print("✅ 404 error handled correctly for non-existent endpoint")
            
            # Make another request to check error response format
            response = requests.get(f"{self.base_url}/api/nonexistent")
            try:
                error_data = response.json()
                if "detail" in error_data:
                    print(f"✅ Error response format is correct: {error_data}")
                    return True, error_data
                else:
                    print(f"❌ Error response format is incorrect: {error_data}")
            except:
                print(f"❌ Error response is not valid JSON: {response.text}")
        
        return False, None

def main():
    # Get the backend URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        env_content = f.read()
        backend_url = None
        for line in env_content.splitlines():
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip()
                break
    
    if not backend_url:
        print("❌ Error: Could not find REACT_APP_BACKEND_URL in frontend/.env")
        sys.exit(1)
    
    print(f"🔍 Using backend URL: {backend_url}")
    
    # Create API tester
    tester = BackendAPITester(backend_url)
    
    print("\n==== TESTING BACKEND API AFTER FIXES ====\n")
    
    # 1. Test health check endpoint
    health_success, health_data = tester.test_health_check()
    
    # 2. Test reference data endpoint
    ref_data_success, ref_data = tester.test_get_all_reference_data()
    
    # 3. Test posts endpoint
    posts_success, posts_data = tester.test_get_posts()
    
    # 4. Test CORS configuration
    cors_success, cors_data = tester.test_cors_configuration()
    
    # 5. Test error handling
    error_success, error_data = tester.test_error_handling()
    
    # Print summary
    print("\n==== TEST SUMMARY ====")
    print(f"Total tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0:.2f}%")
    
    # Print performance metrics
    if tester.performance_metrics:
        print("\n==== PERFORMANCE METRICS ====")
        for name, metrics in tester.performance_metrics.items():
            print(f"{name}: {metrics['response_time_ms']:.2f} ms")
    
    # Overall result
    all_passed = health_success and ref_data_success and posts_success and cors_success
    
    if all_passed:
        print("\n✅ All backend API tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some backend API tests FAILED!")
        failed_tests = []
        if not health_success: failed_tests.append("Health Check")
        if not ref_data_success: failed_tests.append("Reference Data")
        if not posts_success: failed_tests.append("Posts")
        if not cors_success: failed_tests.append("CORS Configuration")
        if not error_success: failed_tests.append("Error Handling")
        
        print(f"Failed tests: {', '.join(failed_tests)}")
        sys.exit(1)

if __name__ == "__main__":
    main()