import requests

BASE_URL = "http://localhost:8000/api/v1"  # Adjust to match your API's base URL

def auth():
    """Logs in with the admin credentials and returns the access token."""
    print("--- Authenticating for Deletion ---")
    login_data = {
        "username": "admin@email.com",
        "password": "12345678"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("Authentication successful.\n")
        return token
    else:
        print(f"Authentication failed. Status: {response.status_code}")
        return None

def delete_all_in_endpoint(endpoint: str, token: str):
    """Fetches all items from an endpoint and deletes them one by one."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Fetch all existing records
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch {endpoint}. Status: {response.status_code}, Error: {response.text}")
        return

    # Extract list of items (handles plain lists or paginated dicts)
    data = response.json()
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif isinstance(data, dict) and "data" in data:
        items = data["data"]
    else:
        print(f"Could not parse list of items for {endpoint}.")
        return

    if not items:
        print(f"No items found in {endpoint} to delete.")
        return

    print(f"Found {len(items)} items in {endpoint}. Deleting...")

    # 2. Delete each record by ID
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
            
        delete_url = f"{url}/{item_id}"
        del_response = requests.delete(delete_url, headers=headers)
        
        if del_response.status_code in [200, 204]:
            print(f"  [-] Deleted {endpoint} ID: {item_id}")
        else:
            print(f"  [x] Failed to delete {endpoint} ID: {item_id}. Status: {del_response.status_code}")

if __name__ == "__main__":
    print("Starting database cleanup...\n")
    
    token = auth()
    
    if token:
        # Order is critical: delete dependent child tables before parent tables
        endpoints_to_clear = [
            "reminders",
            "reservations",
            "quotes",
            "items",
            "categories",
            "users",    # Note: Deleting the admin user here may invalidate the token for subsequent calls
            "persons",  
            "roles"
        ]
        
        for endpoint in endpoints_to_clear:
            delete_all_in_endpoint(endpoint, token)
            
        print("\nDatabase cleanup complete.")
    else:
        print("Aborting cleanup due to authentication failure.")