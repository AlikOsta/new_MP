import requests
import sys
import json

def test_api_endpoints():
    """Test API endpoints with and without trailing slashes"""
    base_url = "https://82d3e5fa-4130-416d-8d10-174d6a16170f.preview.emergentagent.com"
    
    # Test health endpoint
    print("\n🔍 Testing health endpoint...")
    response = requests.get(f"{base_url}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test posts endpoint with trailing slash
    print("\n🔍 Testing posts endpoint with trailing slash...")
    response = requests.get(f"{base_url}/api/posts/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json()[:2], indent=2)}")
    
    # Test posts endpoint without trailing slash
    print("\n🔍 Testing posts endpoint without trailing slash...")
    response = requests.get(f"{base_url}/api/posts")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json()[:2], indent=2)}")
    else:
        print(f"Response: {response.text}")
    
    # Test posts endpoint with query parameter and trailing slash
    print("\n🔍 Testing posts endpoint with query parameter and trailing slash...")
    response = requests.get(f"{base_url}/api/posts/?post_type=job")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json()[:2], indent=2)}")
    else:
        print(f"Response: {response.text}")
    
    # Test posts endpoint with query parameter and without trailing slash
    print("\n🔍 Testing posts endpoint with query parameter and without trailing slash...")
    response = requests.get(f"{base_url}/api/posts?post_type=job")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json()[:2], indent=2)}")
    else:
        print(f"Response: {response.text}")
    
    # Test HTTP to HTTPS redirection
    print("\n🔍 Testing HTTP to HTTPS redirection...")
    try:
        response = requests.get(f"http://dd2133eb-15ad-4681-b6b7-b2b6cd0e455f.preview.emergentagent.com/api/health", allow_redirects=False)
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()