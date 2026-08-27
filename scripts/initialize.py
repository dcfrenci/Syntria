import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000/api/v1"

def post_data(endpoint: str, data: list, token: str):
    """Helper method to iterate through data and make POST requests using the auth token."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    ids = []
    for item in data:
        response = requests.post(url, json=item, headers=headers)
        if response.status_code in [200, 201]:
            print(f"Successfully created in {endpoint}: {item.get('name', item.get('title', item.get('email', 'Item')))}")
            if "id" in response.json():
                ids.append(response.json().get("id"))
        else:
            print(f"Failed to create in {endpoint}. Status: {response.status_code}, Error: {response.text}")
    return ids

def bootstrap_system():
    """Bootstraps the admin role, admin person, and admin user."""
    print("--- Bootstrapping System ---")
    
    # 1. Bootstrap Role
    role_payload = {
        "name": "Admin", 
        "description": "System Administrator"
    }
    role_response = requests.post(f"{BASE_URL}/users/bootstrap_role", json=role_payload)
    print(f"Bootstrap Role Status: {role_response.status_code}")
    
    role_id = 1
    if role_response.status_code in [200, 201]:
        role_id = role_response.json().get("id", 1)

    # 2. Create Admin Person
    person_payload = {
        "first_name": "Admin",
        "last_name": "System",
        "email": "admin@email.com",
        "phone": "0000000000"
    }
    person_response = requests.post(f"{BASE_URL}/persons", json=person_payload)
    print(f"Create Admin Person Status: {person_response.status_code}")
    
    person_id = 1 
    if person_response.status_code in [200, 201]:
        person_id = person_response.json().get("id", 1)

    # 3. Bootstrap Admin User
    admin_credentials = {
        "email": "admin@email.com",
        "password": "12345678",
        "person_id": person_id,
        "role_id": role_id
    }
    user_response = requests.post(f"{BASE_URL}/users/bootstrap_user", json=admin_credentials)
    print(f"Bootstrap User Status: {user_response.status_code}")
    print("----------------------------\n")

def auth():
    """Logs in with the admin credentials and returns the access token."""
    print("--- Authenticating ---")
    
    # FastAPI typically expects form data (OAuth2PasswordRequestForm) for login, using "username" field for the email
    login_data = {
        "username": "admin@email.com",
        "password": "12345678"
    }
    
    # Adjust this endpoint if your auth router uses /auth/login instead of /auth/token
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("Authentication successful.")
        print("----------------------------\n")
        return token
    else:
        print(f"Authentication failed. Status: {response.status_code}, Error: {response.text}")
        return None

def create_roles(token: str):
    roles = [
        {"name": "Manager"},
        {"name": "User"},
        {"name": "Guest"}
    ]
    return post_data("roles", roles, token)

def create_users(token: str, roles_ids: list, persons_ids: list):
    users = [
        {
            "person_id": persons_ids[0], 
            "role_id": roles_ids[0], 
            "is_active": True, 
            "password": "password123"
        },
        {
            "person_id": persons_ids[1], 
            "role_id": roles_ids[1], 
            "is_active": True, 
            "password": "password123"
        },
        {
            "person_id": persons_ids[2], 
            "role_id": roles_ids[2], 
            "is_active": True, 
            "password": "password123"
        }
    ]
    return post_data("users", users, token)

def create_persons(token: str, reminders_ids: list):
    persons = [
        {"first_name": "Alice", "last_name": "Smith", "phone_number": "3395550101", "email": "alice@client.com", "birth_date": "1969-10-21", "reminder_preference_id": reminders_ids[0]},
        {"first_name": "Bob", "last_name": "Jones", "phone_number": "3395550102", "email": "bob@client.com", "birth_date": "1999-05-11", "reminder_preference_id": reminders_ids[1]},
        {"first_name": "Charlie", "last_name": "Brown", "phone_number": "3395550103", "email": "charlie@client.com", "birth_date": "1999-01-17", "reminder_preference_id": reminders_ids[2]}
    ]
    return post_data("persons", persons, token)

def create_categories(token: str):
    categories = [
        {"name": "Dental Services", "description": "General dental procedures"},
        {"name": "Orthodontics", "description": "Braces and aligners"},
        {"name": "Surgery", "description": "Surgical procedures"}
    ]
    return post_data("categories", categories, token)

def create_items(token: str, categories_ids: list):
    items = [
        {"name": "Teeth Cleaning", "price": 100.0, "category_id": categories_ids[0]},
        {"name": "Metal Braces", "price": 2500.0, "category_id": categories_ids[1]},
        {"name": "Wisdom Tooth Extraction", "price": 400.0, "category_id": categories_ids[2]}
    ]
    return post_data("items", items, token)

def create_quotes(token: str, persons_ids: list, items_ids: list):
    now = datetime.now()
    quotes = [
        {
            "valid_until": (now + timedelta(days=15)).strftime("%Y-%m-%d"),
            "patient_id": persons_ids[0],
            "staff_id": persons_ids[0],
            "items": [
                {
                    "item_id": items_ids[0],
                    "quantity": 1,
                    "discount": 0.0
                },
                {
                    "item_id": items_ids[1],
                    "quantity": 1,
                    "discount": 10.0
                }
            ]
        },
        {
            "valid_until": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
            "patient_id": persons_ids[1],
            "staff_id": persons_ids[1],
            "items": [
                {
                    "item_id": items_ids[1],
                    "quantity": 2,
                    "discount": 5.0
                }
            ]
        },
        {
            "valid_until": (now + timedelta(days=10)).strftime("%Y-%m-%d"),
            "patient_id": persons_ids[2],
            "staff_id": persons_ids[2],
            "items": [
                {
                    "item_id": items_ids[2],
                    "quantity": 1,
                    "discount": 0.0
                }
            ]
        }
    ]
    
    return post_data("quotes", quotes, token)


def create_reservations(token: str, persons_ids: list):
    now = datetime.now(timezone.utc)
    reservations = [
        {
            "reservation_date": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "duration_minutes": 30,
            "description": "Initial consultation and dental checkup",
            "patient_id": persons_ids[0],
            "staff_ids": [persons_ids[0]]
        },
        {
            "reservation_date": (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "duration_minutes": 60,
            "description": "Deep teeth cleaning and whitening procedure",
            "patient_id": persons_ids[1],
            "staff_ids": [persons_ids[1]]
        },
        {
            "reservation_date": (now + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "duration_minutes": 45,
            "description": "Follow-up for cavity filling",
            "patient_id": 3,
            "staff_ids": [1]
        },
        {
            "reservation_date": (now + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "duration_minutes": 90,
            "description": "Braces adjustment and tightening",
            "patient_id": persons_ids[2],
            "staff_ids": [persons_ids[2]]
        }
    ]
    
    return post_data("reservations", reservations, token)

def create_reminders(token: str):
    reminders = [
        {"name": "sms"},
        {"name": "whatapp"},
        {"name": "Telegram"}
    ]
    return post_data("reminder", reminders, token)

if __name__ == "__main__":
    print("Starting database population...\n")
    
    # 1. Bootstrap the core admin dependencies
    bootstrap_system()
    
    # 2. Authenticate to get the token
    token = auth()
    
    # 3. Proceed only if authentication was successful
    if token:
        roles_ids = create_roles(token)
        remainders_ids = create_reminders(token)
        persons_ids = create_persons(token, remainders_ids)
        users_ids = create_users(token, roles_ids, persons_ids)
        categories_ids = create_categories(token)
        items_ids = create_items(token, categories_ids)
        quotes_ids = create_quotes(token, persons_ids, items_ids)
        reservations_ids = create_reservations(token, persons_ids)
        print("Database population complete.")
    else:
        print("Aborting database population due to authentication failure.")