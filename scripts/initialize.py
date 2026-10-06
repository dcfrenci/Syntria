import os
import argparse
import requests
from seed_data import (
    get_reminders,
    get_roles,
    get_categories,
    get_persons,
    get_users,
    get_items,
    get_reservations,
    get_quotes,
    get_presets,
)

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def post_data(endpoint: str, data: list, token: str):
    """Helper method to iterate through data and make POST requests using the auth token."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ids = []
    
    for item in data:
        response = requests.post(url, json=item, headers=headers)
        
        # Cleanly extract a label for printing
        name_label = item.get('name', item.get('first_name', item.get('email', 'Item')))
        
        if response.status_code in [200, 201]:
            print(f"Successfully created in {endpoint}: {name_label}")
            if "id" in response.json():
                ids.append(response.json().get("id"))
        elif response.status_code == 409:
            print(f"Already exists in {endpoint}: {name_label}")
        else:
            print(f"Failed to create in {endpoint}. Status: {response.status_code}, Error: {response.text}")
            
    return ids


def bootstrap_system():
    """Bootstraps the admin role, admin person, and admin user in a single request."""
    print("--- Bootstrapping System ---")

    payload = {
        "role_name": "Admin",
        "first_name": "Admin",
        "last_name": "System",
        "email": "admin@email.com",
        "phone_number": "0000000000",
        "birth_date": "0001-01-01",
        "password": "asTf82#1"
    }

    response = requests.post(f"{BASE_URL}/users/admin", json=payload)
    print(f"Bootstrap System Status: {response.status_code}")
    
    if response.status_code not in [200, 201, 403]:
        print(f"Error: {response.text}")
    elif response.status_code == 403:
        print("System already bootstrapped. Proceeding...")
    
    print("----------------------------\n")


def auth():
    """Logs in with the admin credentials and returns the access token."""
    print("--- Authenticating ---")
    login_data = {"username": "admin@email.com", "password": "asTf82#1"}
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)

    if response.status_code == 200:
        token = response.json().get("access_token")
        print("Authentication successful.")
        print("----------------------------\n")
        return token
    else:
        print(f"Authentication failed. Status: {response.status_code}, Error: {response.text}")
        return None


def create_reminders(token: str):
    reminders = get_reminders()
    post_data("reminders/", reminders, token)
    
    # Fetch from DB to guarantee we map IDs even if they already existed
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/reminders/", headers=headers).json()
    return {r["name"]: r["id"] for r in res}


def create_roles(token: str):
    roles = get_roles()
    post_data("roles/", roles, token)

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/roles/", headers=headers).json()
    role_map = {r["name"]: r["id"] for r in res}
    role_map["Admin"] = 1
    return role_map


def create_persons(token: str, rem_map: dict):
    persons = get_persons(rem_map)
    post_data("persons/", persons, token)

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/persons/?limit=100", headers=headers).json()
    p_map = {f"{p['first_name']} {p['last_name']}": p["id"] for p in res.get("persons", [])}
    p_map["Elisa Copolla"] = p_map.get("Elisa Coppola")
    return p_map


def create_categories(token: str):
    categories = get_categories()
    post_data("categories/", categories, token)
    
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/categories/?limit=100", headers=headers).json()
    return {c["name"]: c["id"] for c in res.get("categories", [])}


def create_items(token: str, c_map: dict):
    items = get_items(c_map)
    post_data("items/", items, token)
    
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/items/?limit=100", headers=headers).json()
    return {i["name"]: i["id"] for i in res.get("items", [])}


def create_users(token: str, roles_map: dict, p_map: dict):
    users = get_users(roles_map, p_map)
    return post_data("users/", users, token)


def create_reservations(token: str, p_map: dict):
    reservations = get_reservations(p_map)
    return post_data("reservations/", reservations, token)


def create_quotes(token: str, p_map: dict, i_map: dict):
    quotes = get_quotes(p_map, i_map)
    return post_data("quotes/", quotes, token)


def create_presets(token: str):
    presets = get_presets()
    return post_data("presets/", presets, token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database initialization script.")
    parser.add_argument(
        "--pre-filled",
        action="store_true",
        help="Pre-fill the database with person, users, services and categories.",
    )
    args = parser.parse_args()

    print("Starting database population...\n")

    # 1. Bootstrap the core admin dependencies
    bootstrap_system()

    # 2. Authenticate to get the token
    token = auth()

    if token:
        rem_map = create_reminders(token)
        roles_map = create_roles(token)
            
        if args.pre_filled:
            p_map = create_persons(token, rem_map)
                
            # The mapping above ensures the following functions won't throw KeyErrors
            users_ids = create_users(token, roles_map, p_map)
                
            c_map = create_categories(token)
            i_map = create_items(token, c_map)

            presets_ids = create_presets(token)
            quotes_ids = create_quotes(token, p_map, i_map)
            reservations_ids = create_reservations(token, p_map)

            print("Prefill database population complete.")
        else:
            print("Database population complete.")
    else:
        print("Aborting database population due to authentication failure.")