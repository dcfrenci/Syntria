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

BASE_URL = "http://localhost:8000/api/v1"


def post_data(endpoint: str, data: list, token: str):
    """Helper method to iterate through data and make POST requests using the auth token."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ids = []
    for item in data:
        response = requests.post(url, json=item, headers=headers)
        if response.status_code in [200, 201]:
            print(
                f"Successfully created in {endpoint}: {item.get('name', item.get('title', item.get('email', 'Item')))}"
            )
            if "id" in response.json():
                ids.append(response.json().get("id"))
        else:
            print(
                f"Failed to create in {endpoint}. Status: {response.status_code}, Error: {response.text}"
            )
    return ids


def bootstrap_system():
    """Bootstraps the admin role, admin person, and admin user."""
    print("--- Bootstrapping System ---")

    # 1. Bootstrap Role
    role_payload = {"name": "Admin"}
    role_response = requests.post(f"{BASE_URL}/users/bootstrap_role", json=role_payload)
    print(f"Bootstrap Role Status: {role_response.status_code}")

    role_id = 1
    if role_response.status_code in [200, 201]:
        role_id = role_response.json().get("id", 1)

    # 2. Create Admin Person (Trailing slash added to avoid 307 redirect)
    person_payload = {
        "first_name": "Admin",
        "last_name": "System",
        "email": "admin@email.com",
        "phone_number": "0000000000",
        "birth_date": "0001-01-01",
    }
    person_response = requests.post(f"{BASE_URL}/persons/", json=person_payload)
    print(f"Create Admin Person Status: {person_response.status_code}")

    person_id = 1
    if person_response.status_code in [200, 201]:
        person_id = person_response.json().get("id", 1)

    # 3. Bootstrap Admin User
    admin_credentials = {
        "email": "admin@email.com",
        "password": "asTf82#1",
        "person_id": person_id,
        "role_id": role_id,
        "is_active": True,
    }
    user_response = requests.post(
        f"{BASE_URL}/users/bootstrap_user", json=admin_credentials
    )
    print(f"Bootstrap User Status: {user_response.status_code}")
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
        print(
            f"Authentication failed. Status: {response.status_code}, Error: {response.text}"
        )
        return None


def create_reminders(token: str):
    reminders = get_reminders()
    ids = post_data("reminders/", reminders, token)
    return dict(zip([r["name"] for r in reminders], ids))


def create_roles(token: str):
    roles = get_roles()
    ids = post_data("roles/", roles, token)

    role_map = dict(zip([r["name"] for r in roles], ids))
    role_map["Admin"] = 1
    return role_map


def create_persons(token: str, rem_map: dict):
    persons = get_persons(rem_map)
    ids = post_data("persons/", persons, token)

    p_map = dict(zip([f"{p['first_name']} {p['last_name']}" for p in persons], ids))
    p_map["Elisa Copolla"] = p_map["Elisa Coppola"]
    return p_map


def create_users(token: str, roles_map: dict, p_map: dict):
    users = get_users(roles_map, p_map)
    return post_data("users/", users, token)


def create_categories(token: str):
    categories = get_categories()
    ids = post_data("categories/", categories, token)
    return dict(zip([c["name"] for c in categories], ids))


def create_items(token: str, c_map: dict):
    items = get_items(c_map)
    ids = post_data("items/", items, token)
    return dict(zip([i["name"] for i in items], ids))


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
        "--admin-only",
        action="store_true",
        help="Only bootstrap the admin role, person, and user. Skips the rest of the database prefill.",
    )
    args = parser.parse_args()

    print("Starting database population...\n")

    # 1. Bootstrap the core admin dependencies
    bootstrap_system()

    if args.admin_only:
        print("Admin-only flag provided. Skipping prefill data.")
    else:
        # 2. Authenticate to get the token
        token = auth()

        if token:
            rem_map = create_reminders(token)
            roles_map = create_roles(token)
            p_map = create_persons(token, rem_map)

            users_ids = create_users(token, roles_map, p_map)

            c_map = create_categories(token)
            i_map = create_items(token, c_map)

            presets_ids = create_presets(token)

            quotes_ids = create_quotes(token, p_map, i_map)
            reservations_ids = create_reservations(token, p_map)

            print("Database population complete.")
        else:
            print("Aborting database population due to authentication failure.")
