import requests

BASE_URL = "http://localhost:8000/api/v1"

# Users extracted directly from seed_data.py
TEST_USERS = [
    # Active Users
    {"role": "Admin", "email": "admin@email.com", "password": "asTf82#1", "active": True},
    {"role": "Manager", "email": "matteo.b@gmail.com", "password": "kL9$zQ2w", "active": True},
    {"role": "Doctor", "email": "mbianchi88@yahoo.it", "password": "rT2#yN9b", "active": True},
    {"role": "Assistant", "email": "giulia.rossi@email.com", "password": "pM4@vX7c", "active": True},
    {"role": "Employee", "email": "alex.romano@email.com", "password": "bV5&cH1k", "active": True},
    {"role": "Client", "email": "marty.colombo@gmail.com", "password": "xN7*jP4d", "active": True},
    
    # Inactive Users (For testing Authentication blocking)
    {"role": "Manager (Inactive)", "email": "francesco@gmai.com", "password": "testPass1!", "active": False},
    {"role": "Secretary (Inactive)", "email": "lorenzo.f@email.com", "password": "gZ3%tR8s", "active": False},
    {"role": "Doctor (Inactive)", "email": "s.ricci@gmail.com", "password": "wE8!qF3m", "active": False},
    {"role": "Assistant (Inactive)", "email": "antonella@email.com", "password": "testPass1!", "active": False},
    {"role": "Employee (Inactive)", "email": "ggallo@yahoo.it", "password": "testPass1!", "active": False},
    {"role": "Client (Inactive)", "email": "elena.costa@gmail.com", "password": "testPass1!", "active": False},
]

EXPECTED_ALLOWED = {
    ("GET", "/health"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee", "Client"],
    ("POST", "/users/admin"): [],
    
    ("GET", "/users/"): ["Admin", "Manager", "Secretary"],
    ("POST", "/users/"): ["Admin", "Manager"],
    ("GET", "/users/me"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee"],
    ("GET", "/users/1"): ["Admin", "Manager", "Secretary"], 
    ("PATCH", "/users/1"): ["Admin", "Manager"],
    ("DELETE", "/users/1"): ["Admin"],
    ("GET", "/users/1/reservations?start_date=2026-01-01"): ["Admin", "Manager", "Secretary"],
    
    ("GET", "/roles/"): ["Admin", "Manager"],
    ("POST", "/roles/"): ["Admin"],
    
    ("GET", "/persons/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"],
    ("POST", "/persons/"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("GET", "/persons/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"],
    ("PATCH", "/persons/1"): ["Admin", "Manager", "Secretary", "Doctor"], 
    ("DELETE", "/persons/1"): ["Admin", "Manager"],
    
    ("GET", "/reservations/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Client"],
    ("POST", "/reservations/"): ["Admin", "Manager", "Secretary"], 
    ("GET", "/reservations/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"],
    ("PATCH", "/reservations/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("DELETE", "/reservations/1"): ["Admin", "Manager", "Secretary"],
    
    ("GET", "/quotes/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Client"],
    ("POST", "/quotes/"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("GET", "/quotes/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"], 
    ("PATCH", "/quotes/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("DELETE", "/quotes/1"): ["Admin", "Manager"],
    
    ("GET", "/items/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee"],
    ("POST", "/items/"): ["Admin", "Manager"],
    ("GET", "/items/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee"],
    ("PATCH", "/items/1"): ["Admin", "Manager"],
    ("DELETE", "/items/1"): ["Admin", "Manager"],
    
    ("GET", "/categories/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee"],
    ("POST", "/categories/"): ["Admin", "Manager"],
    ("GET", "/categories/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee"],
    ("PATCH", "/categories/1"): ["Admin", "Manager"],
    ("DELETE", "/categories/1"): ["Admin", "Manager"],
    
    ("GET", "/presets/"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("POST", "/presets/"): ["Admin", "Manager"],
    ("GET", "/presets/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("PATCH", "/presets/1"): ["Admin", "Manager"],
    ("DELETE", "/presets/1"): ["Admin", "Manager"],
    
    ("GET", "/reminders/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Client"],
    ("POST", "/reminders/"): ["Admin"],
    
    ("POST", "/import_export/export/items"): ["Admin", "Manager"],
    ("POST", "/import_export/validate/items"): ["Admin", "Manager"],
    ("POST", "/import_export/commit/items"): ["Admin", "Manager"],
}


def test_all_endpoints(token: str, role_name: str):
    print(f"\n{'='*60}\nTesting Endpoints for Role: {role_name}\n{'='*60}")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    correct = 0
    wrong = 0
    
    endpoints = [
        # 1. Auth & System
        ("GET", "/health", None, None), 
        ("POST", "/users/admin", {
            "role_name": "Admin",
            "first_name": "Admin",
            "last_name": "System",
            "email": "admin@email.com",
            "password": "asTf82#1"
        }, None),
        
        # 2. Users
        ("GET", "/users/", None, None),
        ("POST", "/users/", {"person_id": 999, "role_id": 1, "password": "TestPassword1!"}, None),
        ("GET", "/users/me", None, None),
        ("GET", "/users/1", None, None),
        ("PATCH", "/users/1", {}, None),
        ("DELETE", "/users/1", None, None),
        ("GET", "/users/1/reservations?start_date=2026-01-01", None, None),
        
        # 3. Roles
        ("GET", "/roles/", None, None),
        ("POST", "/roles/", {"name": "TestRole"}, None),
        
        # 4. Persons
        ("GET", "/persons/", None, None),
        ("POST", "/persons/", {"first_name": "T", "last_name": "T", "email": "t@test.com"}, None),
        ("GET", "/persons/1", None, None),
        ("PATCH", "/persons/1", {}, None),
        ("DELETE", "/persons/1", None, None),
        
        # 5. Reservations
        ("GET", "/reservations/", None, None),
        ("POST", "/reservations/", {"patient_id": 1, "staff_ids": [1], "reservation_date": "2026-10-02T18:00:00Z"}, None),
        ("GET", "/reservations/1", None, None),
        ("PATCH", "/reservations/1", {}, None),
        ("DELETE", "/reservations/1", None, None),
        
        # 6. Quotes
        ("GET", "/quotes/", None, None),
        ("POST", "/quotes/", {"patient_id": 1, "items": [{"item_id": 1}]}, None),
        ("GET", "/quotes/1", None, None),
        ("PATCH", "/quotes/1", {}, None),
        ("DELETE", "/quotes/1", None, None),
        
        # 7. Items
        ("GET", "/items/", None, None),
        ("POST", "/items/", {"name": "Test Item", "price": 10}, None),
        ("GET", "/items/1", None, None),
        ("PATCH", "/items/1", {}, None),
        ("DELETE", "/items/1", None, None),
        
        # 8. Categories
        ("GET", "/categories/", None, None),
        ("POST", "/categories/", {"name": "Test Category"}, None),
        ("GET", "/categories/1", None, None),
        ("PATCH", "/categories/1", {}, None),
        ("DELETE", "/categories/1", None, None),
        
        # 9. Presets
        ("GET", "/presets/", None, None),
        ("POST", "/presets/", {"name": "Test Preset"}, None),
        ("GET", "/presets/1", None, None),
        ("PATCH", "/presets/1", {}, None),
        ("DELETE", "/presets/1", None, None),
        
        # 10. Reminders
        ("GET", "/reminders/", None, None),
        ("POST", "/reminders/", {"name": "Test Reminder"}, None),
        
        # 11. Import / Export
        ("POST", "/import_export/export/items", {"ids": [1]}, None),
        ("POST", "/import_export/validate/items", None, {'file': ('test.csv', b'id,name\n1,test', 'text/csv')}),
        ("POST", "/import_export/commit/items", {"actions": []}, None),
    ]
    
    for method, path, payload, files in endpoints:
        is_allowed = role_name in EXPECTED_ALLOWED.get((method, path), [])
        
        if path == "/health":
            url = f"http://localhost:8000{path}"
            res_callable = lambda: requests.get(url)
        else:
            url = f"{BASE_URL}{path}"
            if method == "GET":
                res_callable = lambda: requests.get(url, headers=headers)
            elif method == "POST":
                if files:
                    res_callable = lambda: requests.post(url, headers=headers, files=files)
                else:
                    res_callable = lambda: requests.post(url, headers=headers, json=payload)
            elif method == "PATCH":
                res_callable = lambda: requests.patch(url, headers=headers, json=payload)
            elif method == "DELETE":
                res_callable = lambda: requests.delete(url, headers=headers)

        try:
            res = res_callable()
            status_code = res.status_code
            
            # Evaluate correctness
            is_correct = False
            
            if "/users/admin" in path:
                expected_desc = "403/422"
                if status_code in [403, 422]:
                    is_correct = True
            else:
                is_item_endpoint = path.endswith("/1")
                expected_desc = "!= 403" if is_allowed else ("403/404" if is_item_endpoint else "== 403")
                
                if is_allowed and status_code != 403:
                    is_correct = True
                elif not is_allowed:
                    if status_code == 403:
                        is_correct = True
                    # Accept 404 for item endpoints because earlier tests (Admin) legally deleted the item
                    elif is_item_endpoint and status_code == 404:
                        is_correct = True
            
            judgment = "[CORRECT]" if is_correct else "[WRONG]"
            if is_correct:
                correct += 1
            else:
                wrong += 1
                
            # Formatted Output
            print(f"[{method:^6}] {path:<48} -> Status: {status_code:<3} (Expected: {expected_desc:<7}) {judgment}")
            
        except requests.exceptions.RequestException:
            print(f"[{method:^6}] {path:<48} -> Status: ERR (Expected: {expected_desc:<7}) [WRONG]")
            wrong += 1

    # Print Summary Table
    total = correct + wrong
    percentage = (correct / total) * 100 if total > 0 else 0
    
    print(f"\nSummary for {role_name}:")
    print(f"| {'Correct Outputs':<15} | {'Wrong Outputs':<13} | {'Accuracy':<8} |")
    print(f"|{'-'*17}|{'-'*15}|{'-'*10}|")
    print(f"| {correct:<15} | {wrong:<13} | {percentage:>7.2f}% |")
    
    return [correct, wrong, percentage]


def main():
    print("Starting Permissions Test Script...\n")
    
    score = []
    for user in TEST_USERS:
        print(f"\n--- Authenticating as {user['role']} ({user['email']}) ---")
        login_data = {"username": user["email"], "password": user["password"]}
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
        
        is_active = user.get("active", True)
        
        if response.status_code == 200:
            if not is_active:
                print(f"❌ [WRONG] Inactive user successfully authenticated!")
                score.append([0, 1, 0.0])
                continue
                
            token = response.json().get("access_token")
            out = test_all_endpoints(token, user["role"])
            score.append(out)
        else:
            if not is_active and response.status_code == 403:
                print(f"Authentication blocked. Status: {response.status_code}, Response: {response.text}")
                print(f"✅ [CORRECT] Inactive user was correctly prevented from logging in.")
                score.append([1, 0, 100.0]) 
            else:
                print(f"❌ [WRONG] Failed to authenticate active user or unexpected status. Status: {response.status_code}, Response: {response.text}")
                score.append([0, 1, 0.0])
    
    print(f"\n{'='*60}\nTEST SUMMARY\n{'='*60}")
    print(f"| {'Role':<22} | {'Correct Outputs':<15} | {'Wrong Outputs':<13} | {'Accuracy':<8} |")
    print(f"|{'-'*24}|{'-'*17}|{'-'*15}|{'-'*10}|")
    
    for user, s in zip(TEST_USERS, score):
        print(f"| {user['role']:<22} | {s[0]:<15} | {s[1]:<13} | {s[2]:>7.2f}% |")
    
if __name__ == "__main__":
    main()