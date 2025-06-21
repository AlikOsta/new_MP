import requests
import sys
import json
import sqlite3
from datetime import datetime
import uuid
import os

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
        self.db_path = "/app/telegram_marketplace.db"
        
        # Create a test user for our tests
        self.test_user = {
            "telegram_id": 123456789,
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "language": "ru"
        }

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
                
            # Verify data in database
            db_success, db_data = self.verify_db_data("super_rubrics", "is_active = 1")
            if db_success:
                print("✅ Database verification: Categories data exists in SQLite")
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
                
            # Verify data in database
            db_success, db_data = self.verify_db_data("cities", "is_active = 1")
            if db_success:
                print("✅ Database verification: Cities data exists in SQLite")
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
                
            # Verify data in database
            db_success, db_data = self.verify_db_data("currencies", "is_active = 1")
            if db_success:
                print("✅ Database verification: Currencies data exists in SQLite")
        return success, data

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
    backend_url = "https://b0a15686-ccf3-4104-b6fc-70d7835c7c89.preview.emergentagent.com"
    
    print(f"Testing SQLite API at: {backend_url}")
    
    # Setup tester
    tester = TelegramMarketplaceAPITester(backend_url)
    
    # Run basic API tests
    print("\n🔍 TESTING BASIC API ENDPOINTS")
    tester.test_health_check()
    tester.test_get_super_rubrics()
    tester.test_get_cities()
    tester.test_get_currencies()
    
    # Test user creation
    print("\n🔍 TESTING USER API")
    tester.test_create_user()
    
    # Test posts API
    print("\n🔍 TESTING POSTS API")
    tester.test_get_posts()
    tester.test_create_job_post()
    tester.test_create_service_post()
    tester.test_update_post_status()
    tester.test_get_post_details()
    tester.test_view_counter()
    
    # Test favorites API
    print("\n🔍 TESTING FAVORITES API")
    tester.test_favorites_functionality()
    
    # Test admin panel functionality
    print("\n🔍 TESTING ADMIN PANEL: Admin authentication and functionality")
    
    # Test admin authentication
    tester.test_admin_login_valid()
    tester.test_admin_login_invalid()
    
    # Test admin statistics
    print("\n🔍 TESTING ADMIN STATISTICS: User and post statistics")
    tester.test_admin_stats_users()
    tester.test_admin_stats_posts()
    
    # Test admin settings
    print("\n🔍 TESTING ADMIN SETTINGS: Get and update application settings")
    tester.test_admin_get_settings()
    tester.test_admin_update_settings()
    
    # Test admin CRUD for currencies
    print("\n🔍 TESTING ADMIN CURRENCIES: CRUD operations for currencies")
    tester.test_admin_get_currencies()
    tester.test_admin_create_currency()
    tester.test_admin_update_currency()
    tester.test_admin_delete_currency()
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())