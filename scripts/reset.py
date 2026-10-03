import requests

BASE_URL = "http://localhost:8000/api/v1"


def auth():
    """Logs in with the admin credentials and returns the access token."""
    print("--- Authenticating ---")
    login_data = {"username": "admin@email.com", "password": "asTf82#1"}

    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)

    if response.status_code == 200:
        print("Authentication successful.\n")
        return response.json().get("access_token")
    else:
        print(
            f"Authentication failed. Status: {response.status_code}, Error: {response.text}"
        )
        return None


def fetch_all(endpoint: str, token: str, key: str):
    """Fetches all records for a given endpoint, handling pagination up to the 100-item limit."""
    headers = {"Authorization": f"Bearer {token}"}
    all_items = []
    skip = 0
    limit = 100  # Max limit allowed by the backend

    while True:
        response = requests.get(
            f"{BASE_URL}/{endpoint}/?skip={skip}&limit={limit}", headers=headers
        )
        if response.status_code == 200:
            data = response.json().get(key, [])
            all_items.extend(data)

            # If we received fewer items than the limit, we've reached the end of the pages
            if len(data) < limit:
                break
            skip += limit
        else:
            print(f"Failed to fetch {endpoint}: {response.text}")
            break

    return all_items


def delete_item(endpoint: str, item_id: int, token: str):
    """Issues a DELETE request for a specific item."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/{endpoint}/{item_id}", headers=headers)

    if response.status_code in [200, 204]:
        print(f"Successfully deleted {endpoint} ID: {item_id}")
    else:
        print(f"Failed to delete {endpoint} ID: {item_id}. Error: {response.text}")


def reset_database(token: str):
    print("--- Starting Database Reset ---\n")

    # 1. Delete Quotes (Must be deleted before items/persons due to relations)
    print("Cleaning up Quotes...")
    quotes = fetch_all("quotes", token, "quotes")
    for q in quotes:
        delete_item("quotes", q["id"], token)

    # 2. Delete Reservations
    print("\nCleaning up Reservations...")
    reservations = fetch_all("reservations", token, "reservations")
    for r in reservations:
        delete_item("reservations", r["id"], token)

    # 3. Delete Items
    print("\nCleaning up Items...")
    items = fetch_all("items", token, "items")
    for i in items:
        delete_item("items", i["id"], token)

    # 4. Delete Categories
    print("\nCleaning up Categories...")
    categories = fetch_all("categories", token, "categories")
    for c in categories:
        delete_item("categories", c["id"], token)

    # 5. Delete Presets
    print("\nCleaning up Presets...")
    presets = fetch_all("presets", token, "presets")
    for p in presets:
        delete_item("presets", p["id"], token)

    # 6. Delete Users (Keep Admin)
    print("\nCleaning up Users...")
    users = fetch_all("users", token, "users")
    for u in users:
        if u["person"]["email"] != "admin@email.com":
            delete_item("users", u["id"], token)

    # 7. Delete Persons (Keep Admin)
    print("\nCleaning up Persons...")
    persons = fetch_all("persons", token, "persons")
    for p in persons:
        if p["email"] != "admin@email.com":
            delete_item("persons", p["id"], token)


if __name__ == "__main__":
    token = auth()
    if token:
        reset_database(token)
        print("\n--- Reset Complete ---")
        print(
            "All data cleared. Only the Admin User, Admin Person, Roles, and Reminders remain."
        )
