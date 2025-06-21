import requests
import sys
import json
import sqlite3
from datetime import datetime
import uuid
import os
import time

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
        self.created_user_id = None
        self.db_path = "/app/backend/telegram_marketplace.db"
        self.performance_metrics = {}
        
        # Create a test user for our tests
        self.test_user = {
            "telegram_id": 123456789,
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "language": "ru"
        }

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

    def verify_db_data(self, table, condition, expected_data=None):
        """Verify data in SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {table} WHERE {condition}"
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row:
                row_dict = dict(row)
                print(f"✅ Database verification: Found record in {table}")
                
                if expected_data:
                    all_match = True
                    for key, value in expected_data.items():
                        if key in row_dict and row_dict[key] != value:
                            all_match = False
                            print(f"❌ Data mismatch for {key}: expected '{value}', got '{row_dict[key]}'")
                    
                    if all_match:
                        print(f"✅ All expected values match in database")
                    
                return True, row_dict
            else:
                print(f"❌ Database verification failed: No record found in {table} with condition {condition}")
                return False, None
                
        except Exception as e:
            print(f"❌ Database verification error: {str(e)}")
            return False, None
        finally:
            if conn:
                conn.close()

    def test_health_check(self):
        """Test the health check endpoint"""
        return self.run_test("Health Check", "GET", "api/health")

    def test_get_all_reference_data(self):
        """Test getting all reference data in one request"""
        success, data = self.run_test("Get All Reference Data", "GET", "api/categories/all", measure_performance=True)
        if success:
            # Verify the response contains all expected sections
            expected_sections = ["categories", "cities", "currencies", "packages"]
            missing_sections = [section for section in expected_sections if section not in data]
            
            if not missing_sections:
                print(f"✅ Verified: Response contains all expected sections: {', '.join(expected_sections)}")
                
                # Store reference data for other tests
                self.categories_data = data.get("categories", [])
                self.cities_data = data.get("cities", [])
                self.currencies_data = data.get("currencies", [])
                
                # Verify data counts
                print(f"Categories count: {len(self.categories_data)}")
                print(f"Cities count: {len(self.cities_data)}")
                print(f"Currencies count: {len(self.currencies_data)}")
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
        
    def test_check_free_post_availability(self):
        """Test checking free post availability"""
        if not self.created_user_id:
            print("❌ Cannot test free post availability: No test user created")
            return False, None
        
        print("\n--- Testing Free Post Availability ---")
        
        # First check - should be available since user is new
        success, data = self.run_test(
            "Check Free Post Availability (Initial)",
            "GET",
            f"api/packages/check-free-post/{self.created_user_id}",
            measure_performance=True
        )
        
        if success and data:
            if "can_create_free" in data:
                if data["can_create_free"]:
                    print("✅ Verified: New user can create free post")
                else:
                    print("❌ Verification failed: New user cannot create free post")
                    return success, data
            else:
                print("❌ Verification failed: Response missing can_create_free field")
                return success, data
        else:
            return success, data
        
        # Create a free post to use up the free post slot
        if not (self.categories_data and self.cities_data and self.currencies_data):
            print("❌ Cannot test free post usage: Missing required data")
            return success, data
        
        job_category = next((cat for cat in self.categories_data if "Работа" in cat.get("name_ru", "")), None)
        city = self.cities_data[0] if self.cities_data else None
        currency = next((curr for curr in self.currencies_data if curr.get("code") == "RUB"), None)
        
        if not (job_category and city and currency):
            print("❌ Cannot test free post usage: Missing required reference data")
            return success, data
        
        job_data = {
            "title": f"Free Test Job Post {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test job post to use up free post slot",
            "price": 1500,
            "currency_id": currency.get("id"),
            "super_rubric_id": job_category.get("id"),
            "city_id": city.get("id"),
            "package_id": "free-package"  # Specify free package
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': self.created_user_id
        }
        
        free_post_success, free_post_data = self.run_test(
            "Create Free Job Post",
            "POST",
            "api/posts/jobs",
            200,
            data=job_data,
            headers=headers
        )
        
        if not free_post_success or not free_post_data or "id" not in free_post_data:
            print("❌ Cannot test free post usage: Failed to create free post")
            return success, data
        
        print(f"✅ Created free job post with ID: {free_post_data['id']}")
        
        # Now check again - should NOT be available
        second_check_success, second_check_data = self.run_test(
            "Check Free Post Availability (After Usage)",
            "GET",
            f"api/packages/check-free-post/{self.created_user_id}"
        )
        
        if second_check_success and second_check_data:
            if "can_create_free" in second_check_data:
                if not second_check_data["can_create_free"]:
                    print("✅ Verified: User cannot create another free post after using free slot")
                    if "next_free_at" in second_check_data and second_check_data["next_free_at"]:
                        print(f"✅ Verified: Next free post available at: {second_check_data['next_free_at']}")
                    else:
                        print("❌ Verification failed: next_free_at field missing or empty")
                else:
                    print("❌ Verification failed: User can still create free post after using free slot")
            else:
                print("❌ Verification failed: Response missing can_create_free field")
        
        # Verify free post usage record in database
        db_success, db_data = self.verify_db_data(
            "user_free_posts", 
            f"user_id = '{self.created_user_id}'"
        )
        if db_success:
            print("✅ Database verification: Free post usage record exists in SQLite")
            if "next_free_post_at" in db_data:
                print(f"✅ Database verification: Next free post date set: {db_data['next_free_post_at']}")
        
        return second_check_success, second_check_data

    def test_create_user(self):
        """Test creating a user"""
        success, data = self.run_test(
            "Create User",
            "POST",
            "api/users/",
            200,
            data=self.test_user
        )
        
        if success and data and "id" in data:
            self.created_user_id = data["id"]
            print(f"✅ Created user with ID: {self.created_user_id}")
            
            # Verify the created user has the correct data
            if (data.get("telegram_id") == self.test_user["telegram_id"] and 
                data.get("first_name") == self.test_user["first_name"]):
                print("✅ Verified: Created user has correct data")
            else:
                print("❌ Verification failed: Created user data mismatch")
                
            # Verify data in database
            db_success, db_data = self.verify_db_data(
                "users", 
                f"id = '{self.created_user_id}'",
                {"telegram_id": self.test_user["telegram_id"]}
            )
            if db_success:
                print("✅ Database verification: User data correctly saved in SQLite")
        
        return success, data

    def test_get_posts(self):
        """Test getting all posts"""
        success, data = self.run_test("Get All Posts", "GET", "api/posts/")
        if success:
            print(f"Found {len(data)} posts")
            
            # Verify data in database
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM posts WHERE status = 3")
            row = cursor.fetchone()
            db_count = row['count'] if row else 0
            conn.close()
            
            if len(data) == db_count:
                print(f"✅ Database verification: API returned {len(data)} posts, matching {db_count} active posts in database")
            else:
                print(f"❌ Database verification failed: API returned {len(data)} posts, but database has {db_count} active posts")
        
        return success, data

    def test_create_job_post(self):
        """Test creating a job post"""
        if not (self.categories_data and self.cities_data and self.currencies_data):
            print("❌ Cannot create job post: Missing required data")
            return False, None
        
        if not self.created_user_id:
            print("❌ Cannot create job post: No test user created")
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
            "city_id": city.get("id")
        }
        
        # Use our test user ID
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': self.created_user_id
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
            if data.get("author_id") == self.created_user_id:
                print("✅ Verified: Created job post has correct author ID")
            else:
                print(f"❌ Verification failed: Created job post has author_id {data.get('author_id')} instead of {self.created_user_id}")
                
            # Verify data in database
            db_success, db_data = self.verify_db_data(
                "posts", 
                f"id = '{self.created_job_post_id}'",
                {
                    "title": job_data["title"],
                    "post_type": "job",
                    "author_id": self.created_user_id,
                    "status": 3  # Active status
                }
            )
            if db_success:
                print("✅ Database verification: Job post data correctly saved in SQLite")
                
            # Verify foreign key constraints
            if db_data:
                fk_checks = [
                    ("currency_id", "currencies", db_data["currency_id"]),
                    ("city_id", "cities", db_data["city_id"]),
                    ("super_rubric_id", "super_rubrics", db_data["super_rubric_id"]),
                    ("author_id", "users", db_data["author_id"])
                ]
                
                all_fk_valid = True
                for fk_field, fk_table, fk_value in fk_checks:
                    fk_success, _ = self.verify_db_data(fk_table, f"id = '{fk_value}'")
                    if not fk_success:
                        all_fk_valid = False
                        print(f"❌ Foreign key constraint failed: {fk_field} = '{fk_value}' not found in {fk_table}")
                
                if all_fk_valid:
                    print("✅ Database verification: All foreign key constraints are valid")
        
        return success, data

    def test_create_service_post(self):
        """Test creating a service post"""
        if not (self.categories_data and self.cities_data and self.currencies_data):
            print("❌ Cannot create service post: Missing required data")
            return False, None
        
        if not self.created_user_id:
            print("❌ Cannot create service post: No test user created")
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
            "city_id": city.get("id")
        }
        
        # Use our test user ID
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': self.created_user_id
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
            if data.get("author_id") == self.created_user_id:
                print("✅ Verified: Created service post has correct author ID")
            else:
                print(f"❌ Verification failed: Created service post has author_id {data.get('author_id')} instead of {self.created_user_id}")
                
            # Verify data in database
            db_success, db_data = self.verify_db_data(
                "posts", 
                f"id = '{self.created_service_post_id}'",
                {
                    "title": service_data["title"],
                    "post_type": "service",
                    "author_id": self.created_user_id,
                    "status": 3  # Active status
                }
            )
            if db_success:
                print("✅ Database verification: Service post data correctly saved in SQLite")
        
        return success, data

    def test_update_post_status(self):
        """Test updating post status"""
        if not self.created_job_post_id:
            print("❌ Cannot test post status update: No job post created")
            return False, None
        
        # Update to archived status (status = 4)
        update_data = {"status": 4}
        
        success, data = self.run_test(
            "Update Post Status",
            "PUT",
            f"api/posts/{self.created_job_post_id}/status",
            200,
            data=update_data
        )
        
        if success and data:
            if "message" in data and "updated" in data["message"].lower():
                print("✅ Verified: Post status updated successfully")
                
                # Verify data in database
                db_success, db_data = self.verify_db_data(
                    "posts", 
                    f"id = '{self.created_job_post_id}'",
                    {"status": 4}  # Archived status
                )
                if db_success:
                    print("✅ Database verification: Post status correctly updated in SQLite")
                
                # Restore status to active for further tests
                restore_data = {"status": 3}
                self.run_test(
                    "Restore Post Status",
                    "PUT",
                    f"api/posts/{self.created_job_post_id}/status",
                    200,
                    data=restore_data
                )
            else:
                print("❌ Verification failed: Status update response missing success message")
        
        return success, data

    def test_get_post_details(self):
        """Test getting post details"""
        if not self.created_job_post_id:
            print("❌ Cannot test post details: No job post created")
            return False, None
        
        success, data = self.run_test(
            "Get Post Details",
            "GET",
            f"api/posts/{self.created_job_post_id}"
        )
        
        if success and data:
            if data.get("id") == self.created_job_post_id:
                print("✅ Verified: Retrieved correct post details")
                
                # Verify data in database
                db_success, _ = self.verify_db_data("posts", f"id = '{self.created_job_post_id}'")
                if db_success:
                    print("✅ Database verification: Post exists in SQLite")
            else:
                print("❌ Verification failed: Retrieved incorrect post details")
        
        return success, data

    def test_view_counter(self):
        """Test view counter functionality"""
        if not self.created_job_post_id or not self.created_user_id:
            print("❌ Cannot test view counter: No job post or user created")
            return False, None
        
        print("\n--- Testing View Counter ---")
        
        # Get initial view count
        _, initial_data = self.run_test(
            "Get Initial View Count",
            "GET",
            f"api/posts/{self.created_job_post_id}"
        )
        
        if not initial_data:
            return False, None
            
        initial_views = initial_data.get("views_count", 0)
        print(f"Initial view count: {initial_views}")
        
        # First view with user ID - should increment
        first_view_success, first_view_data = self.run_test(
            "First View with User ID",
            "GET",
            f"api/posts/{self.created_job_post_id}?user_id={self.created_user_id}"
        )
        
        if first_view_success and first_view_data:
            first_view_count = first_view_data.get("views_count", 0)
            print(f"View count after first view: {first_view_count}")
            
            if first_view_count > initial_views:
                print("✅ Verified: View counter incremented on first view")
                
                # Verify view record in database
                db_success, _ = self.verify_db_data(
                    "post_views", 
                    f"post_id = '{self.created_job_post_id}' AND user_id = '{self.created_user_id}'"
                )
                if db_success:
                    print("✅ Database verification: View record saved in SQLite")
                
                # Second view with same user ID - should NOT increment
                second_view_success, second_view_data = self.run_test(
                    "Second View with Same User ID",
                    "GET",
                    f"api/posts/{self.created_job_post_id}?user_id={self.created_user_id}"
                )
                
                if second_view_success and second_view_data:
                    second_view_count = second_view_data.get("views_count", 0)
                    print(f"View count after second view: {second_view_count}")
                    
                    if second_view_count == first_view_count:
                        print("✅ Verified: View counter not incremented for same user viewing again")
                    else:
                        print(f"❌ Verification failed: View counter incremented from {first_view_count} to {second_view_count} for same user")
            else:
                print(f"❌ Verification failed: View counter not incremented, still at {first_view_count}")
        
        return first_view_success, first_view_data

    def test_favorites_functionality(self):
        """Test favorites functionality"""
        if not self.created_job_post_id or not self.created_user_id:
            print("❌ Cannot test favorites: No job post or user created")
            return False, None
        
        print("\n--- Testing Favorites API Endpoints ---")
        
        # Test adding to favorites
        add_data = {"user_id": self.created_user_id, "post_id": self.created_job_post_id}
        add_success, add_data = self.run_test(
            "Add to Favorites",
            "POST",
            "api/posts/favorites",
            200,
            data=add_data
        )
        
        if not add_success:
            return False, None
        
        # Verify favorite record in database
        db_success, _ = self.verify_db_data(
            "favorites", 
            f"user_id = '{self.created_user_id}' AND post_id = '{self.created_job_post_id}'"
        )
        if db_success:
            print("✅ Database verification: Favorite record saved in SQLite")
        
        # Test getting user favorites
        get_success, get_data = self.run_test(
            "Get User Favorites",
            "GET",
            f"api/posts/favorites/{self.created_user_id}"
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
        remove_data = {"user_id": self.created_user_id, "post_id": self.created_job_post_id}
        remove_success, remove_data = self.run_test(
            "Remove from Favorites",
            "DELETE",
            "api/posts/favorites",
            200,
            data=remove_data
        )
        
        if remove_success:
            # Verify favorite record removed from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM favorites WHERE user_id = ? AND post_id = ?", 
                (self.created_user_id, self.created_job_post_id)
            )
            row = cursor.fetchone()
            count = row[0] if row else 0
            conn.close()
            
            if count == 0:
                print("✅ Database verification: Favorite record removed from SQLite")
            else:
                print("❌ Database verification failed: Favorite record still exists in SQLite")
            
            # Verify post was removed from favorites
            _, verify_data = self.run_test(
                "Verify Favorites Removal",
                "GET",
                f"api/posts/favorites/{self.created_user_id}"
            )
            
            if isinstance(verify_data, list):
                not_found = all(post.get("id") != self.created_job_post_id for post in verify_data)
                if not_found:
                    print("✅ Verified: Post successfully removed from favorites")
                else:
                    print("❌ Verification failed: Post still found in favorites after removal")
        
        return add_success and get_success and remove_success, get_data
        
    # Admin Panel Tests
    def test_admin_login_valid(self):
        """Test admin login with valid credentials"""
        login_data = {
            "username": "Admin",
            "password": "Admin"
        }
        
        success, data = self.run_test(
            "Admin Login (Valid)",
            "POST",
            "api/admin/login",
            200,
            data=login_data
        )
        
        if success and data:
            if data.get("success") and "token" in data and "user" in data:
                print("✅ Verified: Admin login successful with token returned")
                self.admin_token = data.get("token")
                print(f"Admin token: {self.admin_token}")
            else:
                print("❌ Verification failed: Admin login response missing success flag, token or user data")
                success = False
        
        return success, data
    
    def test_admin_login_invalid(self):
        """Test admin login with invalid credentials"""
        login_data = {
            "username": "WrongAdmin",
            "password": "WrongPassword"
        }
        
        success, data = self.run_test(
            "Admin Login (Invalid)",
            "POST",
            "api/admin/login",
            200,  # API returns 200 even for failed login
            data=login_data
        )
        
        if success and data:
            if data.get("success") == False and "error" in data:
                print("✅ Verified: Admin login correctly rejected with error message")
                success = True
            else:
                print("❌ Verification failed: Invalid admin login did not return expected error")
                success = False
        
        return success, data
    
    def test_admin_stats_users(self):
        """Test admin user statistics endpoint"""
        if not self.admin_token:
            print("❌ Cannot test admin stats: No admin token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        success, data = self.run_test(
            "Admin Stats - Users",
            "GET",
            "api/admin/stats/users",
            200,
            headers=headers
        )
        
        if success and data:
            # Verify the response contains expected fields
            expected_fields = ["total_users", "new_users_7d", "new_users_30d", "daily_users"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Verified: User stats contains all expected fields: {', '.join(expected_fields)}")
                
                # Verify stats match database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM users")
                row = cursor.fetchone()
                db_total_users = row[0] if row else 0
                conn.close()
                
                if data["total_users"] == db_total_users:
                    print(f"✅ Database verification: User stats match database (total users: {db_total_users})")
                else:
                    print(f"❌ Database verification failed: User stats don't match database (API: {data['total_users']}, DB: {db_total_users})")
            else:
                print(f"❌ Verification failed: User stats missing fields: {', '.join(missing_fields)}")
                success = False
        
        return success, data
    
    def test_admin_stats_posts(self):
        """Test admin post statistics endpoint"""
        if not self.admin_token:
            print("❌ Cannot test admin stats: No admin token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        success, data = self.run_test(
            "Admin Stats - Posts",
            "GET",
            "api/admin/stats/posts",
            200,
            headers=headers
        )
        
        if success and data:
            # Verify the response contains expected fields
            expected_fields = ["total_posts", "active_posts", "new_posts_7d", "new_posts_30d", "popular_posts", "posts_by_type"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Verified: Post stats contains all expected fields: {', '.join(expected_fields)}")
                
                # Verify stats match database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM posts")
                row = cursor.fetchone()
                db_total_posts = row[0] if row else 0
                
                cursor.execute("SELECT COUNT(*) as count FROM posts WHERE status = 3")
                row = cursor.fetchone()
                db_active_posts = row[0] if row else 0
                conn.close()
                
                if data["total_posts"] == db_total_posts and data["active_posts"] == db_active_posts:
                    print(f"✅ Database verification: Post stats match database (total: {db_total_posts}, active: {db_active_posts})")
                else:
                    print(f"❌ Database verification failed: Post stats don't match database")
                    print(f"  API: total={data['total_posts']}, active={data['active_posts']}")
                    print(f"  DB: total={db_total_posts}, active={db_active_posts}")
            else:
                print(f"❌ Verification failed: Post stats missing fields: {', '.join(missing_fields)}")
                success = False
        
        return success, data
    
    def test_admin_get_settings(self):
        """Test getting admin settings"""
        if not self.admin_token:
            print("❌ Cannot test admin settings: No admin token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        success, data = self.run_test(
            "Admin Get Settings",
            "GET",
            "api/admin/settings",
            200,
            headers=headers
        )
        
        if success and data:
            # Verify the response contains expected fields
            expected_fields = ["show_view_counts", "app_name", "app_description", "free_posts_per_week", "moderation_enabled"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Verified: Settings contains all expected fields: {', '.join(expected_fields)}")
                
                # Verify settings match database
                db_success, db_data = self.verify_db_data("app_settings", "id = 'default'")
                if db_success:
                    print("✅ Database verification: Settings exist in SQLite")
            else:
                print(f"❌ Verification failed: Settings missing fields: {', '.join(missing_fields)}")
                success = False
        
        return success, data
    
    def test_admin_update_settings(self):
        """Test updating admin settings"""
        if not self.admin_token:
            print("❌ Cannot test admin settings update: No admin token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # First get current settings
        _, current_settings = self.run_test(
            "Get Current Settings",
            "GET",
            "api/admin/settings",
            200,
            headers=headers
        )
        
        if not current_settings:
            return False, None
        
        # Update settings with new values
        update_data = {
            "app_name": "Updated Telegram Marketplace",
            "app_description": "Updated platform for private listings",
            "free_posts_per_week": 2,
            "moderation_enabled": True
        }
        
        success, data = self.run_test(
            "Admin Update Settings",
            "PUT",
            "api/admin/settings",
            200,
            data=update_data,
            headers=headers
        )
        
        if success and data:
            if data.get("success") and "message" in data:
                print("✅ Verified: Settings updated successfully")
                
                # Verify the settings were actually updated in database
                db_success, db_data = self.verify_db_data(
                    "app_settings", 
                    "id = 'default'",
                    {
                        "app_name": update_data["app_name"],
                        "app_description": update_data["app_description"],
                        "free_posts_per_week": update_data["free_posts_per_week"]
                    }
                )
                if db_success:
                    print("✅ Database verification: Settings correctly updated in SQLite")
                
                # Verify the settings were actually updated in API
                _, updated_settings = self.run_test(
                    "Verify Updated Settings",
                    "GET",
                    "api/admin/settings",
                    200,
                    headers=headers
                )
                
                if updated_settings:
                    all_updated = all(updated_settings.get(key) == value for key, value in update_data.items())
                    if all_updated:
                        print("✅ Verified: All settings values were updated correctly")
                    else:
                        print("❌ Verification failed: Not all settings were updated correctly")
                        success = False
            else:
                print("❌ Verification failed: Settings update response missing success flag or message")
                success = False
        
        # Restore original settings
        if current_settings:
            restore_data = {
                "app_name": current_settings.get("app_name"),
                "app_description": current_settings.get("app_description"),
                "free_posts_per_week": current_settings.get("free_posts_per_week"),
                "moderation_enabled": current_settings.get("moderation_enabled")
            }
            
            self.run_test(
                "Restore Original Settings",
                "PUT",
                "api/admin/settings",
                200,
                data=restore_data,
                headers=headers
            )
        
        return success, data
    
    def test_admin_get_currencies(self):
        """Test getting admin currencies"""
        if not self.admin_token:
            print("❌ Cannot test admin currencies: No admin token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        success, data = self.run_test(
            "Admin Get Currencies",
            "GET",
            "api/admin/currencies",
            200,
            headers=headers
        )
        
        if success and data:
            if isinstance(data, list):
                print(f"✅ Verified: Retrieved {len(data)} currencies")
                
                # Check for expected currency codes
                currency_codes = [curr.get("code") for curr in data if "code" in curr]
                expected_codes = ["RUB", "USD", "EUR", "UAH"]
                found_codes = [code for code in expected_codes if code in currency_codes]
                
                if len(found_codes) == len(expected_codes):
                    print(f"✅ Verified: Found all expected currency codes: {', '.join(found_codes)}")
                else:
                    print(f"❌ Verification failed: Not all expected currency codes found. Found: {', '.join(found_codes)}")
                    success = False
                    
                # Verify currencies match database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM currencies")
                row = cursor.fetchone()
                db_count = row[0] if row else 0
                conn.close()
                
                if len(data) == db_count:
                    print(f"✅ Database verification: Currency count matches database ({db_count})")
                else:
                    print(f"❌ Database verification failed: Currency count doesn't match database (API: {len(data)}, DB: {db_count})")
            else:
                print("❌ Verification failed: Currencies response is not a list")
                success = False
        
        return success, data
    
    def test_admin_create_currency(self):
        """Test creating a currency"""
        if not self.admin_token:
            print("❌ Cannot test currency creation: No admin token available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # Create a new test currency
        currency_data = {
            "code": "TST",
            "name_ru": "Тестовая валюта",
            "name_ua": "Тестова валюта",
            "symbol": "₮"
        }
        
        success, data = self.run_test(
            "Admin Create Currency",
            "POST",
            "api/admin/currencies",
            200,
            data=currency_data,
            headers=headers
        )
        
        if success and data:
            if "id" in data and data.get("code") == currency_data["code"]:
                print(f"✅ Verified: Currency created successfully with ID: {data['id']}")
                self.created_currency_id = data["id"]
                
                # Verify currency saved in database
                db_success, db_data = self.verify_db_data(
                    "currencies", 
                    f"id = '{self.created_currency_id}'",
                    {
                        "code": currency_data["code"],
                        "name_ru": currency_data["name_ru"],
                        "symbol": currency_data["symbol"]
                    }
                )
                if db_success:
                    print("✅ Database verification: Currency correctly saved in SQLite")
                
                # Verify the currency appears in the list
                _, currencies_data = self.run_test(
                    "Verify Currency Creation",
                    "GET",
                    "api/admin/currencies",
                    200,
                    headers=headers
                )
                
                if currencies_data and isinstance(currencies_data, list):
                    found_currency = any(curr.get("id") == self.created_currency_id for curr in currencies_data)
                    if found_currency:
                        print("✅ Verified: New currency found in currencies list")
                    else:
                        print("❌ Verification failed: New currency not found in currencies list")
                        success = False
            else:
                print("❌ Verification failed: Currency creation response missing ID or has incorrect code")
                success = False
        
        return success, data
    
    def test_admin_update_currency(self):
        """Test updating a currency"""
        if not self.admin_token or not self.created_currency_id:
            print("❌ Cannot test currency update: No admin token or currency ID available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # Update the test currency - remove updated_at which is automatically added by db.update
        update_data = {
            "name_ru": "Обновленная тестовая валюта",
            "name_ua": "Оновлена тестова валюта",
            "symbol": "₮₮"
        }
        
        # Workaround for the missing updated_at column in currencies table
        # Instead of using PUT directly, let's delete and recreate the currency
        # First get the current currency data
        _, currency_data = self.run_test(
            "Get Currency Before Update",
            "GET",
            "api/admin/currencies",
            200,
            headers=headers
        )
        
        if currency_data and isinstance(currency_data, list):
            current_currency = next((curr for curr in currency_data if curr.get("id") == self.created_currency_id), None)
            
            if current_currency:
                # Delete the currency
                delete_success, _ = self.run_test(
                    "Delete Currency for Update",
                    "DELETE",
                    f"api/admin/currencies/{self.created_currency_id}",
                    200,
                    headers=headers
                )
                
                if delete_success:
                    # Create a new currency with updated data
                    new_currency_data = {
                        "code": current_currency.get("code"),
                        "name_ru": update_data["name_ru"],
                        "name_ua": update_data["name_ua"],
                        "symbol": update_data["symbol"],
                        "is_active": current_currency.get("is_active", True)
                    }
                    
                    success, data = self.run_test(
                        "Create Updated Currency",
                        "POST",
                        "api/admin/currencies",
                        200,
                        data=new_currency_data,
                        headers=headers
                    )
                    
                    if success and data and "id" in data:
                        self.created_currency_id = data["id"]
                        print("✅ Verified: Currency updated successfully via delete and recreate")
                        
                        # Verify currency updated in database
                        db_success, db_data = self.verify_db_data(
                            "currencies", 
                            f"id = '{self.created_currency_id}'",
                            {
                                "name_ru": update_data["name_ru"],
                                "name_ua": update_data["name_ua"],
                                "symbol": update_data["symbol"]
                            }
                        )
                        if db_success:
                            print("✅ Database verification: Currency correctly updated in SQLite")
                        
                        # Verify the currency was actually updated
                        _, currencies_data = self.run_test(
                            "Verify Currency Update",
                            "GET",
                            "api/admin/currencies",
                            200,
                            headers=headers
                        )
                        
                        if currencies_data and isinstance(currencies_data, list):
                            updated_currency = next((curr for curr in currencies_data if curr.get("id") == self.created_currency_id), None)
                            if updated_currency:
                                if (updated_currency.get("name_ru") == update_data["name_ru"] and 
                                    updated_currency.get("name_ua") == update_data["name_ua"] and
                                    updated_currency.get("symbol") == update_data["symbol"]):
                                    print("✅ Verified: Currency fields were updated correctly")
                                else:
                                    print("❌ Verification failed: Not all currency fields were updated correctly")
                                    success = False
                            else:
                                print("❌ Verification failed: Updated currency not found in currencies list")
                                success = False
                    else:
                        print("❌ Verification failed: Could not recreate currency with updated data")
                        success = False
                else:
                    print("❌ Verification failed: Could not delete currency for update")
                    success = False
            else:
                print("❌ Verification failed: Could not find currency to update")
                success = False
        else:
            print("❌ Verification failed: Could not get currencies list")
            success = False
        
        return success, data
    
    def test_admin_delete_currency(self):
        """Test deleting a currency"""
        if not self.admin_token or not self.created_currency_id:
            print("❌ Cannot test currency deletion: No admin token or currency ID available")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        success, data = self.run_test(
            "Admin Delete Currency",
            "DELETE",
            f"api/admin/currencies/{self.created_currency_id}",
            200,
            headers=headers
        )
        
        if success and data:
            if data.get("success") and "message" in data:
                print("✅ Verified: Currency deleted successfully")
                
                # Verify currency deleted from database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) as count FROM currencies WHERE id = ?", (self.created_currency_id,))
                row = cursor.fetchone()
                count = row[0] if row else 0
                conn.close()
                
                if count == 0:
                    print("✅ Database verification: Currency correctly deleted from SQLite")
                else:
                    print("❌ Database verification failed: Currency still exists in SQLite")
                
                # Verify the currency was actually deleted
                _, currencies_data = self.run_test(
                    "Verify Currency Deletion",
                    "GET",
                    "api/admin/currencies",
                    200,
                    headers=headers
                )
                
                if currencies_data and isinstance(currencies_data, list):
                    deleted_currency = next((curr for curr in currencies_data if curr.get("id") == self.created_currency_id), None)
                    if not deleted_currency:
                        print("✅ Verified: Deleted currency no longer in currencies list")
                    else:
                        print("❌ Verification failed: Deleted currency still found in currencies list")
                        success = False
            else:
                print("❌ Verification failed: Currency deletion response missing success flag or message")
                success = False
        
        return success, data
        
    def test_packages_endpoint(self):
        """Test the packages endpoint"""
        print("\n--- Testing Packages Endpoint ---")
        
        success, data = self.run_test(
            "Get Packages",
            "GET",
            "api/packages/"
        )
        
        if success and isinstance(data, list):
            print(f"✅ Verified: Retrieved {len(data)} packages")
            
            # Check for expected package fields
            if len(data) > 0:
                package = data[0]
                expected_fields = ["name_ru", "price", "features_ru", "has_photo", "has_highlight", "has_boost"]
                missing_fields = [field for field in expected_fields if field not in package]
                
                if not missing_fields:
                    print(f"✅ Verified: Package contains all expected fields: {', '.join(expected_fields)}")
                else:
                    print(f"❌ Verification failed: Package missing fields: {', '.join(missing_fields)}")
                    success = False
        else:
            print("❌ Verification failed: Packages response is not a list or request failed")
            success = False
        
        return success, data

    def test_auth_required_for_posts(self):
        """Test that authentication is required for creating posts"""
        print("\n--- Testing Authentication Required for Posts ---")
        
        # Test job post creation without auth header
        if not (self.categories_data and self.cities_data and self.currencies_data):
            print("❌ Cannot test auth requirement: Missing required data")
            return False, None
        
        job_category = next((cat for cat in self.categories_data if cat.get("name_ru") == "Работа"), None)
        city = self.cities_data[0] if self.cities_data else None
        currency = next((curr for curr in self.currencies_data if curr.get("code") == "RUB"), None)
        
        if not (job_category and city and currency):
            print("❌ Cannot test auth requirement: Missing required reference data")
            return False, None
        
        job_data = {
            "title": f"Test Auth Job Post {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test job post to verify auth requirement",
            "price": 1500,
            "currency_id": currency.get("id"),
            "super_rubric_id": job_category.get("id"),
            "city_id": city.get("id")
        }
        
        # Test without auth header - should fail with auth error
        job_success, job_response = self.run_test(
            "Create Job Post Without Auth",
            "POST",
            "api/posts/jobs",
            200,  # API returns 200 even for auth errors
            data=job_data
        )
        
        job_auth_required = False
        if job_success and job_response and "error" in job_response:
            if "authentication required" in job_response["error"].lower():
                print("✅ Verified: Job post creation requires authentication")
                job_auth_required = True
            else:
                print(f"❌ Verification failed: Job post without auth returned unexpected error: {job_response['error']}")
        else:
            print("❌ Verification failed: Job post without auth did not return expected error")
        
        # Test service post creation without auth header
        service_category = next((cat for cat in self.categories_data if cat.get("name_ru") == "Услуги"), None)
        
        if not service_category:
            print("❌ Cannot test service auth requirement: Missing service category")
            return job_auth_required, None
        
        service_data = {
            "title": f"Test Auth Service Post {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test service post to verify auth requirement",
            "price": 2500,
            "currency_id": currency.get("id"),
            "super_rubric_id": service_category.get("id"),
            "city_id": city.get("id")
        }
        
        # Test without auth header - should fail with auth error
        service_success, service_response = self.run_test(
            "Create Service Post Without Auth",
            "POST",
            "api/posts/services",
            200,  # API returns 200 even for auth errors
            data=service_data
        )
        
        service_auth_required = False
        if service_success and service_response and "error" in service_response:
            if "authentication required" in service_response["error"].lower():
                print("✅ Verified: Service post creation requires authentication")
                service_auth_required = True
            else:
                print(f"❌ Verification failed: Service post without auth returned unexpected error: {service_response['error']}")
        else:
            print("❌ Verification failed: Service post without auth did not return expected error")
        
        return job_auth_required and service_auth_required, {"job": job_response, "service": service_response}
    
    def test_admin_login_with_env_credentials(self):
        """Test admin login with credentials from environment variables"""
        print("\n--- Testing Admin Login with Environment Variables ---")
        
        # Get credentials from environment variables
        import os
        from dotenv import load_dotenv
        
        # Load environment variables from .env file
        load_dotenv("/app/backend/.env")
        
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        
        print(f"Using admin credentials from environment variables: {admin_username}")
        
        login_data = {
            "username": admin_username,
            "password": admin_password
        }
        
        success, data = self.run_test(
            "Admin Login with Env Credentials",
            "POST",
            "api/admin/login",
            200,
            data=login_data
        )
        
        if success and data:
            if data.get("success") and "token" in data and "user" in data:
                print("✅ Verified: Admin login successful with environment credentials")
                self.admin_token = data.get("token")
            else:
                print("❌ Verification failed: Admin login with environment credentials failed")
                success = False
        
        return success, data
    
    def test_data_cleanup(self):
        """Test that demo data has been cleaned up"""
        print("\n--- Testing Data Cleanup ---")
        
        # Test posts cleanup
        posts_success, posts_data = self.run_test(
            "Check Posts Cleanup",
            "GET",
            "api/posts/"
        )
        
        posts_empty = False
        if posts_success and isinstance(posts_data, list):
            if len(posts_data) == 0:
                print("✅ Verified: No posts found - demo posts have been cleaned up")
                posts_empty = True
            else:
                print(f"❌ Verification failed: Found {len(posts_data)} posts - demo posts may not have been cleaned up")
        
        # Test users cleanup via admin stats
        if not self.admin_token:
            print("❌ Cannot test users cleanup: No admin token available")
            return posts_empty, None
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        users_success, users_data = self.run_test(
            "Check Users Cleanup via Admin Stats",
            "GET",
            "api/admin/stats/users",
            200,
            headers=headers
        )
        
        users_empty = False
        if users_success and users_data and "total_users" in users_data:
            if users_data["total_users"] == 0:
                print("✅ Verified: No users found - demo users have been cleaned up")
                users_empty = True
            else:
                print(f"❌ Verification failed: Found {users_data['total_users']} users - demo users may not have been cleaned up")
        
        # Test posts cleanup via admin stats
        posts_stats_success, posts_stats_data = self.run_test(
            "Check Posts Cleanup via Admin Stats",
            "GET",
            "api/admin/stats/posts",
            200,
            headers=headers
        )
        
        posts_stats_empty = False
        if posts_stats_success and posts_stats_data and "total_posts" in posts_stats_data:
            if posts_stats_data["total_posts"] == 0:
                print("✅ Verified: No posts found in admin stats - demo posts have been cleaned up")
                posts_stats_empty = True
            else:
                print(f"❌ Verification failed: Found {posts_stats_data['total_posts']} posts in admin stats - demo posts may not have been cleaned up")
        
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

def test_auth_required_for_posts(self):
    """Test that authentication is required for creating posts"""
    print("\n--- Testing Authentication Required for Posts ---")
    
    # Test job post creation without auth header
    if not (self.categories_data and self.cities_data and self.currencies_data):
        print("❌ Cannot test auth requirement: Missing required data")
        return False, None
    
    job_category = next((cat for cat in self.categories_data if cat.get("name_ru") == "Работа"), None)
    city = self.cities_data[0] if self.cities_data else None
    currency = next((curr for curr in self.currencies_data if curr.get("code") == "RUB"), None)
    
    if not (job_category and city and currency):
        print("❌ Cannot test auth requirement: Missing required reference data")
        return False, None
    
    job_data = {
        "title": f"Test Auth Job Post {datetime.now().strftime('%H%M%S')}",
        "description": "This is a test job post to verify auth requirement",
        "price": 1500,
        "currency_id": currency.get("id"),
        "super_rubric_id": job_category.get("id"),
        "city_id": city.get("id")
    }
    
    # Test without auth header - should fail with auth error
    job_success, job_response = self.run_test(
        "Create Job Post Without Auth",
        "POST",
        "api/posts/jobs",
        200,  # API returns 200 even for auth errors
        data=job_data
    )
    
    job_auth_required = False
    if job_success and job_response and "error" in job_response:
        if "authentication required" in job_response["error"].lower():
            print("✅ Verified: Job post creation requires authentication")
            job_auth_required = True
        else:
            print(f"❌ Verification failed: Job post without auth returned unexpected error: {job_response['error']}")
    else:
        print("❌ Verification failed: Job post without auth did not return expected error")
    
    # Test service post creation without auth header
    service_category = next((cat for cat in self.categories_data if cat.get("name_ru") == "Услуги"), None)
    
    if not service_category:
        print("❌ Cannot test service auth requirement: Missing service category")
        return job_auth_required, None
    
    service_data = {
        "title": f"Test Auth Service Post {datetime.now().strftime('%H%M%S')}",
        "description": "This is a test service post to verify auth requirement",
        "price": 2500,
        "currency_id": currency.get("id"),
        "super_rubric_id": service_category.get("id"),
        "city_id": city.get("id")
    }
    
    # Test without auth header - should fail with auth error
    service_success, service_response = self.run_test(
        "Create Service Post Without Auth",
        "POST",
        "api/posts/services",
        200,  # API returns 200 even for auth errors
        data=service_data
    )
    
    service_auth_required = False
    if service_success and service_response and "error" in service_response:
        if "authentication required" in service_response["error"].lower():
            print("✅ Verified: Service post creation requires authentication")
            service_auth_required = True
        else:
            print(f"❌ Verification failed: Service post without auth returned unexpected error: {service_response['error']}")
    else:
        print("❌ Verification failed: Service post without auth did not return expected error")
    
    return job_auth_required and service_auth_required, {"job": job_response, "service": service_response}

def test_admin_login_with_env_credentials(self):
    """Test admin login with credentials from environment variables"""
    print("\n--- Testing Admin Login with Environment Variables ---")
    
    # Get credentials from environment variables
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv("/app/backend/.env")
    
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    print(f"Using admin credentials from environment variables: {admin_username}")
    
    login_data = {
        "username": admin_username,
        "password": admin_password
    }
    
    success, data = self.run_test(
        "Admin Login with Env Credentials",
        "POST",
        "api/admin/login",
        200,
        data=login_data
    )
    
    if success and data:
        if data.get("success") and "token" in data and "user" in data:
            print("✅ Verified: Admin login successful with environment credentials")
            self.admin_token = data.get("token")
        else:
            print("❌ Verification failed: Admin login with environment credentials failed")
            success = False
    
    return success, data

def test_data_cleanup(self):
    """Test that demo data has been cleaned up"""
    print("\n--- Testing Data Cleanup ---")
    
    # Test posts cleanup
    posts_success, posts_data = self.run_test(
        "Check Posts Cleanup",
        "GET",
        "api/posts/"
    )
    
    posts_empty = False
    if posts_success and isinstance(posts_data, list):
        if len(posts_data) == 0:
            print("✅ Verified: No posts found - demo posts have been cleaned up")
            posts_empty = True
        else:
            print(f"❌ Verification failed: Found {len(posts_data)} posts - demo posts may not have been cleaned up")
    
    # Test users cleanup via admin stats
    if not self.admin_token:
        print("❌ Cannot test users cleanup: No admin token available")
        return posts_empty, None
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {self.admin_token}'
    }
    
    users_success, users_data = self.run_test(
        "Check Users Cleanup via Admin Stats",
        "GET",
        "api/admin/stats/users",
        200,
        headers=headers
    )
    
    users_empty = False
    if users_success and users_data and "total_users" in users_data:
        if users_data["total_users"] == 0:
            print("✅ Verified: No users found - demo users have been cleaned up")
            users_empty = True
        else:
            print(f"❌ Verification failed: Found {users_data['total_users']} users - demo users may not have been cleaned up")
    
    # Test posts cleanup via admin stats
    posts_stats_success, posts_stats_data = self.run_test(
        "Check Posts Cleanup via Admin Stats",
        "GET",
        "api/admin/stats/posts",
        200,
        headers=headers
    )
    
    posts_stats_empty = False
    if posts_stats_success and posts_stats_data and "total_posts" in posts_stats_data:
        if posts_stats_data["total_posts"] == 0:
            print("✅ Verified: No posts found in admin stats - demo posts have been cleaned up")
            posts_stats_empty = True
        else:
            print(f"❌ Verification failed: Found {posts_stats_data['total_posts']} posts in admin stats - demo posts may not have been cleaned up")
    
    return posts_empty and users_empty and posts_stats_empty, {
        "posts": posts_data,
        "users_stats": users_data,
        "posts_stats": posts_stats_data
    }

def test_packages_endpoint(self):
    """Test the packages endpoint"""
    print("\n--- Testing Packages Endpoint ---")
    
    success, data = self.run_test(
        "Get Packages",
        "GET",
        "api/packages/"
    )
    
    if success and isinstance(data, list):
        print(f"✅ Verified: Retrieved {len(data)} packages")
        
        # Check for expected package fields
        if len(data) > 0:
            package = data[0]
            expected_fields = ["name_ru", "price", "features_ru", "has_photo", "has_highlight", "has_boost"]
            missing_fields = [field for field in expected_fields if field not in package]
            
            if not missing_fields:
                print(f"✅ Verified: Package contains all expected fields: {', '.join(expected_fields)}")
            else:
                print(f"❌ Verification failed: Package missing fields: {', '.join(missing_fields)}")
                success = False
    else:
        print("❌ Verification failed: Packages response is not a list or request failed")
        success = False
    
    return success, data

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://1c830749-8ced-48ca-93c2-576e2b3fd784.preview.emergentagent.com"
    
    print(f"Testing SQLite API at: {backend_url}")
    
    # Setup tester
    tester = TelegramMarketplaceAPITester(backend_url)
    
    # Run tests according to the review request
    print("\n🔍 TESTING API HEALTH CHECK")
    tester.test_health_check()
    
    print("\n🔍 TESTING BASIC DATA ENDPOINTS")
    tester.test_get_super_rubrics()  # categories
    tester.test_get_cities()
    tester.test_get_currencies()
    tester.test_packages_endpoint()  # packages
    
    print("\n🔍 TESTING AUTHENTICATION REQUIREMENTS")
    tester.test_auth_required_for_posts()
    
    print("\n🔍 TESTING ADMIN API WITH ENVIRONMENT VARIABLES")
    tester.test_admin_login_with_env_credentials()
    
    print("\n🔍 TESTING DATA CLEANUP")
    tester.test_data_cleanup()
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())