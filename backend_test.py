import requests
import sys
import json
from datetime import datetime

class TelegramMarketplaceAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}
        self.created_job_post_id = None
        self.created_service_post_id = None
        self.categories_data = None
        self.cities_data = None
        self.currencies_data = None
        self.admin_token = None
        self.created_currency_id = None

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, headers=headers)

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
                        "data": response_data
                    }
                    return success, response_data
                except:
                    print("Response is not JSON")
                    self.test_results[name] = {
                        "status": "passed",
                        "response_code": response.status_code,
                        "data": response.text[:100]
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
                        "error": error_data
                    }
                except:
                    print(f"Error response: {response.text}")
                    self.test_results[name] = {
                        "status": "failed",
                        "response_code": response.status_code,
                        "error": response.text
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
        return self.run_test("Health Check", "GET", "api/health")

    def test_get_super_rubrics(self):
        """Test getting super rubrics (categories)"""
        success, data = self.run_test("Get Super Rubrics", "GET", "api/categories/super-rubrics")
        if success:
            self.categories_data = data
            # Verify we have exactly 2 categories as specified
            if len(data) == 2:
                print("✅ Verified: Exactly 2 categories returned")
                # Check for expected category names
                category_names = [cat.get("name_ru") for cat in data]
                if "Работа" in category_names and "Услуги" in category_names:
                    print("✅ Verified: Found expected categories 'Работа' and 'Услуги'")
                else:
                    print("❌ Verification failed: Expected categories not found")
            else:
                print(f"❌ Verification failed: Expected 2 categories, got {len(data)}")
        return success, data

    def test_get_cities(self):
        """Test getting cities"""
        success, data = self.run_test("Get Cities", "GET", "api/categories/cities")
        if success:
            self.cities_data = data
            # Verify we have exactly 6 cities as specified
            if len(data) == 6:
                print("✅ Verified: Exactly 6 cities returned")
                # Check for some expected city names
                city_names = [city.get("name_ru") for city in data]
                expected_cities = ["Москва", "Санкт-Петербург", "Киев"]
                found_cities = [city for city in expected_cities if city in city_names]
                if len(found_cities) >= 3:
                    print(f"✅ Verified: Found expected cities: {', '.join(found_cities)}")
                else:
                    print("❌ Verification failed: Expected cities not found")
            else:
                print(f"❌ Verification failed: Expected 6 cities, got {len(data)}")
        return success, data

    def test_get_currencies(self):
        """Test getting currencies"""
        success, data = self.run_test("Get Currencies", "GET", "api/categories/currencies")
        if success:
            self.currencies_data = data
            # Verify we have exactly 4 currencies as specified
            if len(data) == 4:
                print("✅ Verified: Exactly 4 currencies returned")
                # Check for expected currency codes
                currency_codes = [curr.get("code") for curr in data]
                expected_codes = ["RUB", "USD", "EUR", "UAH"]
                found_codes = [code for code in expected_codes if code in currency_codes]
                if len(found_codes) == 4:
                    print(f"✅ Verified: Found all expected currency codes: {', '.join(found_codes)}")
                else:
                    print("❌ Verification failed: Not all expected currency codes found")
            else:
                print(f"❌ Verification failed: Expected 4 currencies, got {len(data)}")
        return success, data

    def test_get_packages(self):
        """Test getting packages"""
        success, data = self.run_test("Get Packages", "GET", "api/packages/")
        if success:
            # Verify we have exactly 3 packages as specified
            if len(data) == 3:
                print("✅ Verified: Exactly 3 packages returned")
                # Check for expected package types
                package_types = [pkg.get("package_type") for pkg in data]
                expected_types = ["basic", "standard", "premium"]
                found_types = [pkg_type for pkg_type in expected_types if pkg_type in package_types]
                if len(found_types) == 3:
                    print(f"✅ Verified: Found all expected package types: {', '.join(found_types)}")
                else:
                    print("❌ Verification failed: Not all expected package types found")
            else:
                print(f"❌ Verification failed: Expected 3 packages, got {len(data)}")
        return success, data

    def test_get_posts(self):
        """Test getting all posts"""
        success, data = self.run_test("Get All Posts", "GET", "api/posts/")
        if success:
            print(f"Found {len(data)} posts")
        return success, data

    def test_get_job_posts(self):
        """Test getting job posts"""
        params = {"post_type": "job"}
        success, data = self.run_test("Get Job Posts", "GET", "api/posts/", params=params)
        if success:
            print(f"Found {len(data)} job posts")
            # Verify all returned posts are of type "job"
            all_jobs = all(post.get("post_type") == "job" for post in data)
            if all_jobs:
                print("✅ Verified: All returned posts are of type 'job'")
            else:
                print("❌ Verification failed: Not all returned posts are of type 'job'")
        return success, data

    def test_get_service_posts(self):
        """Test getting service posts"""
        params = {"post_type": "service"}
        success, data = self.run_test("Get Service Posts", "GET", "api/posts/", params=params)
        if success:
            print(f"Found {len(data)} service posts")
            # Verify all returned posts are of type "service"
            all_services = all(post.get("post_type") == "service" for post in data)
            if all_services:
                print("✅ Verified: All returned posts are of type 'service'")
            else:
                print("❌ Verification failed: Not all returned posts are of type 'service'")
        return success, data

    def test_create_job_post(self):
        """Test creating a job post"""
        if not (self.categories_data and self.cities_data and self.currencies_data):
            print("❌ Cannot create job post: Missing required data")
            return False, None
        
        job_category = next((cat for cat in self.categories_data if cat.get("name_ru") == "Работа"), None)
        city = self.cities_data[0] if self.cities_data else None
        currency = next((curr for curr in self.currencies_data if curr.get("code") == "RUB"), None)
        
        if not (job_category and city and currency):
            print("❌ Cannot create job post: Missing required reference data")
            return False, None
        
        job_data = {
            "title": f"Test Job Post {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test job post created by the API tester",
            "price": 1500,
            "currency_id": currency.get("id"),
            "super_rubric_id": job_category.get("id"),
            "city_id": city.get("id"),
            "experience": "from_1_to_3_years",
            "schedule": "full_time",
            "work_format": "hybrid"
        }
        
        # Use the real user ID from the review request
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': '6855dc265afe51e45102bc68'
        }
        
        success, data = self.run_test(
            "Create Job Post",
            "POST",
            "api/posts/jobs",
            200,
            data=job_data,
            headers=headers
        )
        
        if success and data and "id" in data:
            self.created_job_post_id = data["id"]
            print(f"✅ Created job post with ID: {self.created_job_post_id}")
            
            # Verify the created post has the correct data
            if data.get("title") == job_data["title"] and data.get("post_type") == "job":
                print("✅ Verified: Created job post has correct title and type")
            else:
                print("❌ Verification failed: Created job post data mismatch")
                
            # Verify the post has the correct author ID
            if data.get("author_id") == '6855dc265afe51e45102bc68':
                print("✅ Verified: Created job post has correct author ID")
            else:
                print(f"❌ Verification failed: Created job post has author_id {data.get('author_id')} instead of '6855dc265afe51e45102bc68'")
                
            # Verify the post appears in the active posts list
            _, posts_data = self.run_test("Get Active Posts", "GET", "api/posts/")
            
            if posts_data:
                found_post = any(post.get("id") == self.created_job_post_id for post in posts_data)
                if found_post:
                    print("✅ Verified: New job post found in active posts list")
                else:
                    print("❌ Verification failed: New job post not found in active posts list")
        
        return success, data

    def test_create_service_post(self):
        """Test creating a service post"""
        if not (self.categories_data and self.cities_data and self.currencies_data):
            print("❌ Cannot create service post: Missing required data")
            return False, None
        
        service_category = next((cat for cat in self.categories_data if cat.get("name_ru") == "Услуги"), None)
        city = self.cities_data[0] if self.cities_data else None
        currency = next((curr for curr in self.currencies_data if curr.get("code") == "RUB"), None)
        
        if not (service_category and city and currency):
            print("❌ Cannot create service post: Missing required reference data")
            return False, None
        
        service_data = {
            "title": f"Test Service Post {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test service post created by the API tester",
            "price": 2500,
            "currency_id": currency.get("id"),
            "super_rubric_id": service_category.get("id"),
            "city_id": city.get("id"),
            "phone": "+7 (999) 123-45-67"
        }
        
        # Use the real user ID from the review request
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': '6855dc265afe51e45102bc68'
        }
        
        success, data = self.run_test(
            "Create Service Post",
            "POST",
            "api/posts/services",
            200,
            data=service_data,
            headers=headers
        )
        
        if success and data and "id" in data:
            self.created_service_post_id = data["id"]
            print(f"✅ Created service post with ID: {self.created_service_post_id}")
            
            # Verify the created post has the correct data
            if data.get("title") == service_data["title"] and data.get("post_type") == "service":
                print("✅ Verified: Created service post has correct title and type")
            else:
                print("❌ Verification failed: Created service post data mismatch")
                
            # Verify the post has the correct author ID
            if data.get("author_id") == '6855dc265afe51e45102bc68':
                print("✅ Verified: Created service post has correct author ID")
            else:
                print(f"❌ Verification failed: Created service post has author_id {data.get('author_id')} instead of '6855dc265afe51e45102bc68'")
                
            # Verify the post appears in the active posts list
            _, posts_data = self.run_test("Get Active Posts", "GET", "api/posts/")
            
            if posts_data:
                found_post = any(post.get("id") == self.created_service_post_id for post in posts_data)
                if found_post:
                    print("✅ Verified: New service post found in active posts list")
                else:
                    print("❌ Verification failed: New service post not found in active posts list")
        
        return success, data

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        # Using the real user ID from the review request
        user_id = "6855dc265afe51e45102bc68"
        success, data = self.run_test("Get User by ID", "GET", f"api/users/{user_id}")
        
        if success and data:
            if "error" not in data:
                print(f"✅ Successfully retrieved user with ID: {user_id}")
                print(f"User info: {data.get('first_name')} {data.get('last_name')} (@{data.get('username')})")
            else:
                print(f"❌ Failed to retrieve user with ID: {user_id}")
        
        return success, data

    def test_view_counter_with_user_id(self):
        """Test view counter functionality with user ID to prevent duplicate views"""
        if not self.created_job_post_id:
            print("❌ Cannot test view counter: No job post created")
            return False, None
        
        print("\n--- Testing View Counter with User ID ---")
        
        # Get post details with user ID to increment views
        user_id = "6855dc265afe51e45102bc68"  # Using the real user ID from the review request
        
        # First view - should increment
        first_view_success, first_view_data = self.run_test(
            "First View with User ID",
            "GET",
            f"api/posts/{self.created_job_post_id}?user_id={user_id}"
        )
        
        if first_view_success and first_view_data:
            first_view_count = first_view_data.get("views_count", 0)
            print(f"View count after first view: {first_view_count}")
            
            # Second view with same user ID - should NOT increment
            second_view_success, second_view_data = self.run_test(
                "Second View with Same User ID",
                "GET",
                f"api/posts/{self.created_job_post_id}?user_id={user_id}"
            )
            
            if second_view_success and second_view_data:
                second_view_count = second_view_data.get("views_count", 0)
                print(f"View count after second view: {second_view_count}")
                
                if second_view_count == first_view_count:
                    print("✅ FIXED: View counter not incremented for same user viewing again")
                else:
                    print(f"❌ FIX FAILED: View counter incremented from {first_view_count} to {second_view_count} for same user")
                
                # Third view with different user ID - should increment
                different_user_id = "different-user"
                third_view_success, third_view_data = self.run_test(
                    "View with Different User ID",
                    "GET",
                    f"api/posts/{self.created_job_post_id}?user_id={different_user_id}"
                )
                
                if third_view_success and third_view_data:
                    third_view_count = third_view_data.get("views_count", 0)
                    print(f"View count after view from different user: {third_view_count}")
                    
                    if third_view_count > second_view_count:
                        print("✅ FIXED: View counter incremented for different user")
                    else:
                        print(f"❌ FIX FAILED: View counter not incremented for different user, still at {third_view_count}")
        
        return first_view_success, first_view_data

    def test_favorites_functionality(self):
        """Test favorites functionality"""
        if not self.created_job_post_id:
            print("❌ Cannot test favorites: No job post created")
            return False, None
        
        print("\n--- Testing Favorites API Endpoints ---")
        
        # Test adding to favorites
        add_data = {"user_id": "6855dc265afe51e45102bc68", "post_id": self.created_job_post_id}
        add_success, add_data = self.run_test(
            "Add to Favorites",
            "POST",
            "api/posts/favorites",
            200,
            data=add_data
        )
        
        if not add_success:
            return False, None
        
        # Test getting user favorites
        get_success, get_data = self.run_test(
            "Get User Favorites",
            "GET",
            "api/posts/favorites/6855dc265afe51e45102bc68"
        )
        
        if get_success:
            # Verify our post is in favorites
            if isinstance(get_data, list):
                found_post = any(post.get("id") == self.created_job_post_id for post in get_data)
                if found_post:
                    print("✅ Verified: Post found in user favorites")
                else:
                    print("❌ Verification failed: Post not found in user favorites")
            
        # Test removing from favorites
        remove_data = {"user_id": "6855dc265afe51e45102bc68", "post_id": self.created_job_post_id}
        remove_success, remove_data = self.run_test(
            "Remove from Favorites",
            "DELETE",
            "api/posts/favorites",
            200,
            data=remove_data
        )
        
        if remove_success:
            # Verify post was removed from favorites
            _, verify_data = self.run_test(
                "Verify Favorites Removal",
                "GET",
                "api/posts/favorites/6855dc265afe51e45102bc68"
            )
            
            if isinstance(verify_data, list):
                not_found = all(post.get("id") != self.created_job_post_id for post in verify_data)
                if not_found:
                    print("✅ Verified: Post successfully removed from favorites")
                else:
                    print("❌ Verification failed: Post still found in favorites after removal")
        
        return add_success and get_success and remove_success, get_data

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*50)
        
        if self.tests_passed == self.tests_run:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed.")
            
            # Print failed tests
            failed_tests = {name: result for name, result in self.test_results.items() 
                           if result["status"] != "passed"}
            
            if failed_tests:
                print("\nFailed tests:")
                for name, result in failed_tests.items():
                    print(f"- {name}: {result.get('error', 'Unknown error')}")
        
        return self.tests_passed == self.tests_run

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://82d3e5fa-4130-416d-8d10-174d6a16170f.preview.emergentagent.com"
    
    print(f"Testing API at: {backend_url}")
    
    # Setup tester
    tester = TelegramMarketplaceAPITester(backend_url)
    
    # Run basic API tests
    tester.test_health_check()
    tester.test_get_super_rubrics()
    tester.test_get_cities()
    tester.test_get_currencies()
    tester.test_get_packages()
    
    # Test user endpoints - FOCUS ON TESTING USER INFO
    print("\n🔍 TESTING USER INFO: Get user information for post details")
    tester.test_get_user_by_id()
    
    # Test posts endpoints
    tester.test_get_posts()
    tester.test_get_job_posts()
    tester.test_get_service_posts()
    
    # Test creating posts
    print("\n🔍 TESTING POST CREATION: Creating posts with author information")
    tester.test_create_job_post()
    tester.test_create_service_post()
    
    # Test view counter functionality with user ID
    print("\n🔍 TESTING VIEW COUNTER: View counter should not increment for same user")
    tester.test_view_counter_with_user_id()
    
    # Test favorites functionality
    print("\n🔍 TESTING FAVORITES: Adding/removing posts from favorites")
    tester.test_favorites_functionality()
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())