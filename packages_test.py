import requests
import json
import time
import sqlite3
from datetime import datetime, timedelta
import uuid
import sys

class PackagesTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}
        self.test_user_id = None
        self.created_package_id = None
        self.db_path = "/app/telegram_marketplace.db"
        
        # Create a test user for our tests
        self.test_user = {
            "telegram_id": int(time.time()),
            "first_name": "Package",
            "last_name": "Tester",
            "username": f"package_tester_{int(time.time())}",
            "language": "ru"
        }
        
        # Admin credentials
        self.admin_credentials = {
            "username": "Admin",
            "password": "Admin"
        }
        self.admin_token = None

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

    def setup(self):
        """Setup test environment - create test user and get admin token"""
        # Create test user
        success, data = self.run_test(
            "Create Test User",
            "POST",
            "api/users/",
            200,
            data=self.test_user
        )
        
        if success and data and "id" in data:
            self.test_user_id = data["id"]
            print(f"✅ Created test user with ID: {self.test_user_id}")
        else:
            print("❌ Failed to create test user")
            return False
            
        # Get admin token
        success, data = self.run_test(
            "Admin Login",
            "POST",
            "api/admin/login",
            200,
            data=self.admin_credentials
        )
        
        if success and data and data.get("success") and "token" in data:
            self.admin_token = data["token"]
            print(f"✅ Got admin token: {self.admin_token}")
        else:
            print("❌ Failed to get admin token")
            return False
            
        return True

    def test_get_active_packages(self):
        """Test getting active packages"""
        success, data = self.run_test(
            "Get Active Packages",
            "GET",
            "api/packages/"
        )
        
        if success and isinstance(data, list):
            print(f"✅ Retrieved {len(data)} active packages")
            
            # Verify we have the 5 default packages
            if len(data) >= 5:
                print(f"✅ Found at least 5 packages")
                
                # Check for expected package types
                package_types = [pkg.get("package_type") for pkg in data]
                expected_types = ["free", "standard", "photo", "highlight", "boost"]
                found_types = [t for t in expected_types if t in package_types]
                
                if len(found_types) == len(expected_types):
                    print(f"✅ Found all expected package types: {', '.join(found_types)}")
                else:
                    print(f"❌ Not all expected package types found. Found: {', '.join(found_types)}")
                
                # Check features parsing
                for pkg in data:
                    if "features_ru" in pkg and isinstance(pkg["features_ru"], list):
                        print(f"✅ Features correctly parsed as array for package {pkg.get('name_ru')}")
                    elif "features_ru" in pkg:
                        print(f"❌ Features not parsed as array for package {pkg.get('name_ru')}")
            else:
                print(f"❌ Expected at least 5 packages, got {len(data)}")
        
        return success, data

    def test_check_free_post_availability(self):
        """Test checking free post availability"""
        if not self.test_user_id:
            print("❌ Cannot test free post availability: No test user created")
            return False, None
            
        success, data = self.run_test(
            "Check Free Post Availability (Initial)",
            "GET",
            f"api/packages/check-free-post/{self.test_user_id}"
        )
        
        if success and data:
            # First check should allow free post
            if data.get("can_create_free") == True:
                print("✅ User can create free post initially")
            else:
                print("❌ User cannot create free post initially")
                return success, data
                
            # Create a free post
            job_data = {
                "title": f"Free Test Job {int(time.time())}",
                "description": "This is a test job post with free package",
                "price": 1000,
                "currency_id": "rub-id",
                "super_rubric_id": "job-id",
                "city_id": "moscow-id",
                "package_id": "free-package"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Author-ID': self.test_user_id
            }
            
            post_success, post_data = self.run_test(
                "Create Free Post",
                "POST",
                "api/posts/jobs",
                200,
                data=job_data,
                headers=headers
            )
            
            if post_success and post_data and "id" in post_data:
                print(f"✅ Created free post with ID: {post_data['id']}")
                
                # Verify post has correct package attributes
                if post_data.get("has_photo") == False and post_data.get("has_highlight") == False and post_data.get("has_boost") == False:
                    print("✅ Free post has correct package attributes")
                else:
                    print("❌ Free post has incorrect package attributes")
                
                # Verify post lifetime
                if post_data.get("post_lifetime_days") == 30:
                    print("✅ Free post has correct lifetime (30 days)")
                else:
                    print(f"❌ Free post has incorrect lifetime: {post_data.get('post_lifetime_days')} days")
                
                # Verify user_free_posts record in database
                db_success, db_data = self.verify_db_data(
                    "user_free_posts", 
                    f"user_id = '{self.test_user_id}'",
                    {"user_id": self.test_user_id}
                )
                
                if db_success:
                    print("✅ user_free_posts record created in database")
                    
                    # Check next free post date (should be 7 days later)
                    next_free_at = datetime.fromisoformat(db_data["next_free_post_at"])
                    created_at = datetime.fromisoformat(db_data["created_at"])
                    days_diff = (next_free_at - created_at).days
                    
                    if days_diff == 7:
                        print("✅ Next free post date correctly set to 7 days later")
                    else:
                        print(f"❌ Next free post date incorrectly set to {days_diff} days later")
                
                # Check free post availability again - should be unavailable
                second_check_success, second_check_data = self.run_test(
                    "Check Free Post Availability (After Creation)",
                    "GET",
                    f"api/packages/check-free-post/{self.test_user_id}"
                )
                
                if second_check_success and second_check_data:
                    if second_check_data.get("can_create_free") == False:
                        print("✅ User cannot create another free post immediately")
                        
                        # Verify next_free_at date is returned
                        if second_check_data.get("next_free_at"):
                            print(f"✅ Next free post date returned: {second_check_data.get('next_free_at')}")
                        else:
                            print("❌ Next free post date not returned")
                    else:
                        print("❌ User can still create free post immediately after creating one")
            else:
                print("❌ Failed to create free post")
        
        return success, data

    def test_create_post_with_photo_package(self):
        """Test creating a post with photo package"""
        if not self.test_user_id:
            print("❌ Cannot test photo package: No test user created")
            return False, None
            
        # Create a post with photo package
        job_data = {
            "title": f"Photo Package Test Job {int(time.time())}",
            "description": "This is a test job post with photo package",
            "price": 2000,
            "currency_id": "rub-id",
            "super_rubric_id": "job-id",
            "city_id": "moscow-id",
            "package_id": "photo-package"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': self.test_user_id
        }
        
        success, data = self.run_test(
            "Create Post with Photo Package",
            "POST",
            "api/posts/jobs",
            200,
            data=job_data,
            headers=headers
        )
        
        if success and data and "id" in data:
            print(f"✅ Created post with photo package, ID: {data['id']}")
            
            # Verify post has correct package attributes
            if data.get("has_photo") == True and data.get("has_highlight") == False and data.get("has_boost") == False:
                print("✅ Post has correct photo package attributes")
            else:
                print("❌ Post has incorrect photo package attributes")
            
            # Verify post lifetime
            if data.get("post_lifetime_days") == 30:
                print("✅ Post has correct lifetime (30 days)")
            else:
                print(f"❌ Post has incorrect lifetime: {data.get('post_lifetime_days')} days")
            
            # Verify post is marked as premium
            if data.get("is_premium") == True:
                print("✅ Post is correctly marked as premium")
            else:
                print("❌ Post is not marked as premium")
        
        return success, data

    def test_create_post_with_boost_package(self):
        """Test creating a post with boost package"""
        if not self.test_user_id:
            print("❌ Cannot test boost package: No test user created")
            return False, None
            
        # Create a post with boost package
        job_data = {
            "title": f"Boost Package Test Job {int(time.time())}",
            "description": "This is a test job post with boost package",
            "price": 3000,
            "currency_id": "rub-id",
            "super_rubric_id": "job-id",
            "city_id": "moscow-id",
            "package_id": "boost-package"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Author-ID': self.test_user_id
        }
        
        success, data = self.run_test(
            "Create Post with Boost Package",
            "POST",
            "api/posts/jobs",
            200,
            data=job_data,
            headers=headers
        )
        
        if success and data and "id" in data:
            post_id = data["id"]
            print(f"✅ Created post with boost package, ID: {post_id}")
            
            # Verify post has correct package attributes
            if data.get("has_photo") == False and data.get("has_highlight") == False and data.get("has_boost") == True:
                print("✅ Post has correct boost package attributes")
            else:
                print("❌ Post has incorrect boost package attributes")
            
            # Verify post_boost_schedule record in database
            db_success, db_data = self.verify_db_data(
                "post_boost_schedule", 
                f"post_id = '{post_id}'",
                {"post_id": post_id, "is_active": 1, "boost_count": 0}
            )
            
            if db_success:
                print("✅ post_boost_schedule record created in database")
                
                # Check next boost date (should be set based on boost_interval_days)
                next_boost_at = datetime.fromisoformat(db_data["next_boost_at"])
                created_at = datetime.fromisoformat(db_data["created_at"])
                days_diff = (next_boost_at - created_at).days
                
                # Get boost_interval_days from package
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT boost_interval_days FROM packages WHERE id = 'boost-package'")
                package = cursor.fetchone()
                conn.close()
                
                boost_interval_days = package["boost_interval_days"] if package else None
                
                if boost_interval_days and days_diff == boost_interval_days:
                    print(f"✅ Next boost date correctly set to {boost_interval_days} days later")
                else:
                    print(f"❌ Next boost date incorrectly set: expected {boost_interval_days} days, got {days_diff} days")
        
        return success, data

    def test_purchase_package(self):
        """Test package purchase initiation"""
        if not self.test_user_id:
            print("❌ Cannot test package purchase: No test user created")
            return False, None
            
        # Initiate package purchase
        purchase_data = {
            "user_id": self.test_user_id,
            "package_id": "photo-package"
        }
        
        success, data = self.run_test(
            "Purchase Package",
            "POST",
            "api/packages/purchase",
            200,
            data=purchase_data
        )
        
        if success and data:
            if "purchase_id" in data:
                print(f"✅ Package purchase initiated with ID: {data['purchase_id']}")
                
                # Verify user_packages record in database
                db_success, db_data = self.verify_db_data(
                    "user_packages", 
                    f"id = '{data['purchase_id']}'",
                    {
                        "user_id": self.test_user_id,
                        "package_id": "photo-package",
                        "payment_status": "pending"
                    }
                )
                
                if db_success:
                    print("✅ user_packages record created in database")
                    
                # Try to purchase a free package (should fail)
                free_purchase_data = {
                    "user_id": self.test_user_id,
                    "package_id": "free-package"
                }
                
                free_success, free_data = self.run_test(
                    "Purchase Free Package (Should Fail)",
                    "POST",
                    "api/packages/purchase",
                    200,
                    data=free_purchase_data
                )
                
                if free_success and free_data and "error" in free_data:
                    print("✅ Free package purchase correctly rejected")
                else:
                    print("❌ Free package purchase not rejected")
            else:
                print("❌ Package purchase response missing purchase_id")
        
        return success, data

    def test_admin_packages_crud(self):
        """Test admin CRUD operations for packages"""
        if not self.admin_token:
            print("❌ Cannot test admin packages CRUD: No admin token available")
            return False, None
            
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # 1. Get all packages as admin
        success, data = self.run_test(
            "Admin Get All Packages",
            "GET",
            "api/admin/packages",
            200,
            headers=headers
        )
        
        if not (success and isinstance(data, list)):
            print("❌ Failed to get packages as admin")
            return False, None
            
        print(f"✅ Retrieved {len(data)} packages as admin")
        
        # 2. Create a new package
        new_package = {
            "name_ru": "Тестовый тариф",
            "name_ua": "Тестовий тариф",
            "package_type": "test",
            "price": 250,
            "currency_id": "rub-id",
            "duration_days": 15,
            "post_lifetime_days": 45,
            "features_ru": ["Тестовая функция 1", "Тестовая функция 2"],
            "features_ua": ["Тестова функція 1", "Тестова функція 2"],
            "has_photo": True,
            "has_highlight": True,
            "has_boost": False,
            "is_active": True,
            "sort_order": 10
        }
        
        create_success, create_data = self.run_test(
            "Admin Create Package",
            "POST",
            "api/admin/packages",
            200,
            data=new_package,
            headers=headers
        )
        
        if not (create_success and create_data and "id" in create_data):
            print("❌ Failed to create package as admin")
            return False, None
            
        self.created_package_id = create_data["id"]
        print(f"✅ Created package with ID: {self.created_package_id}")
        
        # Verify features were stored as pipe-separated string
        db_success, db_data = self.verify_db_data(
            "packages", 
            f"id = '{self.created_package_id}'"
        )
        
        if db_success:
            if "|" in db_data["features_ru"]:
                print("✅ Features correctly stored as pipe-separated string")
            else:
                print("❌ Features not stored as pipe-separated string")
        
        # 3. Update the package
        update_data = {
            "name_ru": "Обновленный тестовый тариф",
            "price": 300,
            "features_ru": ["Обновленная функция 1", "Обновленная функция 2", "Новая функция 3"],
            "has_boost": True,
            "boost_interval_days": 5
        }
        
        update_success, update_result = self.run_test(
            "Admin Update Package",
            "PUT",
            f"api/admin/packages/{self.created_package_id}",
            200,
            data=update_data,
            headers=headers
        )
        
        if not (update_success and update_result and update_result.get("success")):
            print("❌ Failed to update package as admin")
            return False, None
            
        print("✅ Updated package successfully")
        
        # Verify the update
        get_updated_success, get_updated_data = self.run_test(
            "Get Updated Package",
            "GET",
            "api/admin/packages",
            200,
            headers=headers
        )
        
        if get_updated_success and isinstance(get_updated_data, list):
            updated_package = next((p for p in get_updated_data if p.get("id") == self.created_package_id), None)
            
            if updated_package:
                if (updated_package.get("name_ru") == update_data["name_ru"] and 
                    updated_package.get("price") == update_data["price"] and
                    updated_package.get("has_boost") == update_data["has_boost"] and
                    updated_package.get("boost_interval_days") == update_data["boost_interval_days"]):
                    print("✅ Package updated correctly")
                else:
                    print("❌ Package not updated correctly")
                    
                # Check features array
                if (isinstance(updated_package.get("features_ru"), list) and 
                    len(updated_package.get("features_ru")) == len(update_data["features_ru"])):
                    print("✅ Features array updated and parsed correctly")
                else:
                    print("❌ Features array not updated or parsed correctly")
            else:
                print("❌ Updated package not found")
        
        # 4. Delete the package
        delete_success, delete_result = self.run_test(
            "Admin Delete Package",
            "DELETE",
            f"api/admin/packages/{self.created_package_id}",
            200,
            headers=headers
        )
        
        if not (delete_success and delete_result and delete_result.get("success")):
            print("❌ Failed to delete package as admin")
            return False, None
            
        print("✅ Deleted package successfully")
        
        # Verify the deletion
        verify_delete_success, verify_delete_data = self.run_test(
            "Verify Package Deletion",
            "GET",
            "api/admin/packages",
            200,
            headers=headers
        )
        
        if verify_delete_success and isinstance(verify_delete_data, list):
            deleted_package = next((p for p in verify_delete_data if p.get("id") == self.created_package_id), None)
            
            if not deleted_package:
                print("✅ Package successfully deleted")
            else:
                print("❌ Package still exists after deletion")
        
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
    backend_url = "https://51d971f9-1e69-4e09-9727-e45dadcdbabe.preview.emergentagent.com"
    
    print(f"Testing Telegram Marketplace Packages API at: {backend_url}")
    
    # Setup tester
    tester = PackagesTester(backend_url)
    
    # Setup test environment
    if not tester.setup():
        print("❌ Failed to setup test environment")
        return 1
    
    # Run tests
    print("\n🔍 TESTING PACKAGES API")
    tester.test_get_active_packages()
    tester.test_check_free_post_availability()
    tester.test_create_post_with_photo_package()
    tester.test_create_post_with_boost_package()
    tester.test_purchase_package()
    
    print("\n🔍 TESTING ADMIN PACKAGES API")
    tester.test_admin_packages_crud()
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())