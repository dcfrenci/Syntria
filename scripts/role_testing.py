import os
import time
import sys
import requests
from common import (
    BASE_URL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    DEMO_PASSWORD,
    require_demo_password,
)

# Users extracted directly from seed_data.py
TEST_USERS = [
    # Active Users
    {"role": "Admin", "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "active": True},
    {
        "role": "Manager",
        "email": "matteo.b@gmail.com",
        "password": DEMO_PASSWORD,
        "active": True,
    },
    {
        "role": "Secretary",
        "email": "vale.bruno@email.com",
        "password": DEMO_PASSWORD,
        "active": True,
    },
    {
        "role": "Doctor",
        "email": "mbianchi88@yahoo.it",
        "password": DEMO_PASSWORD,
        "active": True,
    },
    {
        "role": "Assistant",
        "email": "giulia.rossi@email.com",
        "password": DEMO_PASSWORD,
        "active": True,
    },
    {
        "role": "Employee",
        "email": "alex.romano@email.com",
        "password": DEMO_PASSWORD,
        "active": True,
    },
    {
        "role": "Client",
        "email": "marty.colombo@gmail.com",
        "password": DEMO_PASSWORD,
        "active": True,
    },
    # Inactive Users (For testing Authentication blocking)
    {
        "role": "Manager (Inactive)",
        "email": "francesco@gmai.com",
        "password": DEMO_PASSWORD,
        "active": False,
    },
    {
        "role": "Secretary (Inactive)",
        "email": "lorenzo.f@email.com",
        "password": DEMO_PASSWORD,
        "active": False,
    },
    {
        "role": "Doctor (Inactive)",
        "email": "s.ricci@gmail.com",
        "password": DEMO_PASSWORD,
        "active": False,
    },
    {
        "role": "Assistant (Inactive)",
        "email": "antonella@email.com",
        "password": DEMO_PASSWORD,
        "active": False,
    },
    {
        "role": "Employee (Inactive)",
        "email": "ggallo@yahoo.it",
        "password": DEMO_PASSWORD,
        "active": False,
    },
    {
        "role": "Client (Inactive)",
        "email": "elena.costa@gmail.com",
        "password": DEMO_PASSWORD,
        "active": False,
    },
]

EXPECTED_ALLOWED = {
    ("GET", "/health"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
        "Client",
    ],
    ("GET", "/users/"): ["Admin", "Manager", "Secretary"],
    ("POST", "/users/"): ["Admin", "Manager"],
    ("GET", "/users/me"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
    ],
    ("GET", "/users/1"): ["Admin", "Manager", "Secretary"],
    ("PATCH", "/users/1"): ["Admin", "Manager"],
    ("DELETE", "/users/1"): ["Admin"],
    ("GET", "/users/reservations?start_date=2026-01-01"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
        "Client",
    ],
    ("GET", "/roles/"): ["Admin", "Manager"],
    ("POST", "/roles/"): ["Admin"],
    ("GET", "/persons/"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"],
    ("POST", "/persons/"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("GET", "/persons/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"],
    ("PATCH", "/persons/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("DELETE", "/persons/1"): ["Admin", "Manager"],
    ("GET", "/reservations/"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Client",
    ],
    ("POST", "/reservations/"): ["Admin", "Manager", "Secretary"],
    ("GET", "/reservations/1"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
    ],
    ("PATCH", "/reservations/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("DELETE", "/reservations/1"): ["Admin", "Manager", "Secretary"],
    ("GET", "/quotes/"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
        "Client",
    ],
    ("POST", "/quotes/"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("GET", "/quotes/1"): ["Admin", "Manager", "Secretary", "Doctor", "Assistant"],
    ("PATCH", "/quotes/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("DELETE", "/quotes/1"): ["Admin", "Manager"],
    ("GET", "/items/"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
    ],
    ("POST", "/items/"): ["Admin", "Manager"],
    ("GET", "/items/1"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
    ],
    ("PATCH", "/items/1"): ["Admin", "Manager"],
    ("DELETE", "/items/1"): ["Admin", "Manager"],
    ("GET", "/categories/"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
    ],
    ("POST", "/categories/"): ["Admin", "Manager"],
    ("GET", "/categories/1"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Employee",
    ],
    ("PATCH", "/categories/1"): ["Admin", "Manager"],
    ("DELETE", "/categories/1"): ["Admin", "Manager"],
    ("GET", "/presets/"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("POST", "/presets/"): ["Admin", "Manager", "Secretary"],
    ("GET", "/presets/1"): ["Admin", "Manager", "Secretary", "Doctor"],
    ("PATCH", "/presets/1"): ["Admin", "Manager", "Secretary"],
    ("DELETE", "/presets/1"): ["Admin", "Manager"],
    ("GET", "/reminders/"): [
        "Admin",
        "Manager",
        "Secretary",
        "Doctor",
        "Assistant",
        "Client",
    ],
    ("POST", "/reminders/"): ["Admin"],
    ("POST", "/import_export/export/items"): ["Admin", "Manager"],
    ("POST", "/import_export/validate/items"): ["Admin", "Manager"],
    ("POST", "/import_export/commit/items"): ["Admin", "Manager"],
}

# Endpoints that deliberately answer 404 instead of 403 to hide existence
NOT_FOUND_OK = {("GET", "/quotes/1")}
ADMIN_TOKEN = None
PERSON_BY_EMAIL: dict[str, int] = {}


def _get(path, token):
    return requests.get(
        f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {token}"}
    )


def test_all_endpoints(token: str, role_name: str):
    print(f"\n{'='*60}\nTesting Endpoints for Role: {role_name}\n{'='*60}")

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    correct = 0
    wrong = 0

    # Fetch current user's person_id to satisfy self-assigned business logic restrictions
    current_person_id = None
    if token:
        try:
            me_res = requests.get(f"{BASE_URL}/users/me", headers=headers)
            if me_res.status_code == 200:
                current_person_id = me_res.json().get("person", {}).get("id")
        except requests.exceptions.RequestException:
            pass

    # Build the payload dynamically to include the staff_id for the logged-in doctor
    quote_payload = {"patient_id": 1, "items": [{"item_id": 1}]}
    if current_person_id is not None:
        quote_payload["staff_id"] = current_person_id

    endpoints = [
        # 1. Auth & System
        ("GET", "/health", None, None),
        # 2. Users
        ("GET", "/users/", None, None),
        (
            "POST",
            "/users/",
            {"person_id": 999, "role_id": 4, "password": DEMO_PASSWORD},
            None,
        ),
        ("GET", "/users/me", None, None),
        ("GET", "/users/1", None, None),
        ("PATCH", "/users/1", {}, None),
        ("DELETE", "/users/1", None, None),
        ("GET", "/users/reservations?start_date=2026-01-01", None, None),
        # 3. Roles
        ("GET", "/roles/", None, None),
        ("POST", "/roles/", {"name": "TestRole"}, None),
        # 4. Persons
        ("GET", "/persons/", None, None),
        (
            "POST",
            "/persons/",
            {"first_name": "T", "last_name": "T", "email": "t@test.com"},
            None,
        ),
        ("GET", "/persons/1", None, None),
        ("PATCH", "/persons/1", {}, None),
        ("DELETE", "/persons/1", None, None),
        # 5. Reservations
        ("GET", "/reservations/", None, None),
        (
            "POST",
            "/reservations/",
            {
                "patient_id": 1,
                "staff_ids": [1],
                "reservation_date": "2026-10-02T18:00:00Z",
            },
            None,
        ),
        ("GET", "/reservations/1", None, None),
        ("PATCH", "/reservations/1", {}, None),
        ("DELETE", "/reservations/1", None, None),
        # 6. Quotes
        ("GET", "/quotes/", None, None),
        ("POST", "/quotes/", quote_payload, None),
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
        (
            "POST",
            "/import_export/validate/items",
            None,
            {"file": ("test.csv", b"id,name\n1,test", "text/csv")},
        ),
        ("POST", "/import_export/commit/items", {"actions": []}, None),
    ]

    for method, path, payload, files in endpoints:
        time.sleep(0.05)
        real_path = (
            path.replace("/1", "/999999")
            if method in ("PATCH", "DELETE") and path.endswith("/1")
            else path
        )
        is_allowed = role_name in EXPECTED_ALLOWED.get((method, path), [])

        if path == "/health":
            url = f"{BASE_URL}{path}"
            res_callable = lambda: requests.get(url)
        else:
            url = f"{BASE_URL}{real_path}"
            if method == "GET":
                res_callable = lambda: requests.get(url, headers=headers)
            elif method == "POST":
                if files:
                    res_callable = lambda: requests.post(
                        url, headers=headers, files=files
                    )
                else:
                    res_callable = lambda: requests.post(
                        url, headers=headers, json=payload
                    )
            elif method == "PATCH":
                res_callable = lambda: requests.patch(
                    url, headers=headers, json=payload
                )
            elif method == "DELETE":
                res_callable = lambda: requests.delete(url, headers=headers)

        expected_desc = "-"

        try:
            res = res_callable()
            status_code = res.status_code

            # Evaluate correctness
            if is_allowed:
                is_correct = status_code not in (401, 403) and status_code < 500
                expected_desc = "not 401/403/5xx"
            else:
                is_correct = status_code == 403 or (
                    status_code == 404 and (method, path) in NOT_FOUND_OK
                )
                expected_desc = (
                    "403/404" if (method, path) in NOT_FOUND_OK else "== 403"
                )

            judgment = "[CORRECT]" if is_correct else "[WRONG]"
            if is_correct:
                correct += 1
            else:
                wrong += 1

            # Formatted Output
            print(
                f"[{method:^6}] {path:<48} -> Status: {status_code:<3} (Expected: {expected_desc:<7}) {judgment}"
            )

        except requests.exceptions.RequestException:
            print(
                f"[{method:^6}] {path:<48} -> Status: ERR (Expected: {expected_desc:<7}) [WRONG]"
            )
            wrong += 1

    # Print Summary Table
    total = correct + wrong
    percentage = (correct / total) * 100 if total > 0 else 0

    print(f"\nSummary for {role_name}:")
    print(f"| {'Correct Outputs':<15} | {'Wrong Outputs':<13} | {'Accuracy':<8} |")
    print(f"|{'-'*17}|{'-'*15}|{'-'*10}|")
    print(f"| {correct:<15} | {wrong:<13} | {percentage:>7.2f}% |")

    return [correct, wrong, percentage]


def test_scoped_access(token: str, role_name: str, me: int | None):
    role = role_name.lower()
    if role == "admin":
        return [0, 0, 100.0]
    results = []

    def check(desc, ok):
        results.append(bool(ok))
        print(f"[SCOPE ] {desc:<62} {'[CORRECT]' if ok else '[WRONG]'}")

    if role in {"manager", "secretary"}:
        users = _get("/users/?limit=100", token).json().get("users", [])
        check(
            "admin account hidden from /users/",
            all(u["person"]["email"] != ADMIN_EMAIL for u in users),
        )
    if role in {"manager", "secretary", "doctor", "assistant"}:
        persons = _get("/persons/?limit=100", token).json().get("persons", [])
        check(
            "admin person hidden from /persons/",
            all(p["email"] != ADMIN_EMAIL for p in persons),
        )

    if role in {"doctor", "assistant", "employee", "client"} and me is not None:
        key = "staff" if role == "doctor" else "patient"
        admin_quotes = _get("/quotes/?limit=100", ADMIN_TOKEN).json()["quotes"]
        mine = _get("/quotes/?limit=100", token).json()["quotes"]
        check(
            "/quotes/ lists only own",
            all((q.get(key) or {}).get("id") == me for q in mine),
        )
        foreign = next(
            (q for q in admin_quotes if (q.get(key) or {}).get("id") != me), None
        )
        if foreign:
            check(
                f"GET /quotes/{foreign['id']} (foreign) -> 404",
                _get(f"/quotes/{foreign['id']}", token).status_code == 404,
            )

        foreign_pid = next(
            (q["patient"]["id"] for q in admin_quotes if q["patient"]["id"] != me), None
        )
        if foreign_pid:
            r = _get(
                f"/users/reservations?start_date=2026-01-01&user_id={foreign_pid}",
                token,
            )
            check("foreign /users/reservations -> 403", r.status_code == 403)
            if role == "client":
                check(
                    "client GET /persons/{foreign} -> 403",
                    _get(f"/persons/{foreign_pid}", token).status_code == 403,
                )

        if role in {"doctor", "assistant", "client"}:
            own = (
                (lambda r: r["patient"]["id"] == me)
                if role == "client"
                else (lambda r: me in [s["id"] for s in r["staff"]])
            )
            rs = _get("/reservations/?limit=100", token).json()["reservations"]
            check("/reservations/ lists only own", all(own(r) for r in rs))
            admin_rs = _get("/reservations/?limit=100", ADMIN_TOKEN).json()[
                "reservations"
            ]
            f = next((r for r in admin_rs if not own(r)), None)
            if f:
                check(
                    f"GET /reservations/{f['id']} (foreign) -> 403",
                    _get(f"/reservations/{f['id']}", token).status_code == 403,
                )

    wrong = results.count(False)
    return [
        len(results) - wrong,
        wrong,
        100.0 * (len(results) - wrong) / len(results) if results else 100.0,
    ]


def main():
    print("Starting Permissions Test Script...\n")

    global ADMIN_TOKEN

    require_demo_password()

    score = []
    for user in TEST_USERS:
        print(f"\n--- Authenticating as {user['role']} ({user['email']}) ---")
        time.sleep(2)
        login_data = {"username": user["email"], "password": user["password"]}
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data)

        is_active = user.get("active", True)

        if response.status_code == 200:
            if not is_active:
                print(f"❌ [WRONG] Inactive user successfully authenticated!")
                score.append([0, 1, 0.0])
                continue

            token = response.json().get("access_token")
            if user["role"] == "Admin":  # Admin is first in TEST_USERS
                ADMIN_TOKEN = token
                PERSON_BY_EMAIL.update(
                    {
                        u["person"]["email"]: u["person"]["id"]
                        for u in _get("/users/?limit=100", token).json()["users"]
                    }
                )
            out = test_all_endpoints(token, user["role"])
            sc = test_scoped_access(
                token, user["role"], PERSON_BY_EMAIL.get(user["email"])
            )
            c, w = out[0] + sc[0], out[1] + sc[1]
            out = [c, w, 100.0 * c / (c + w) if c + w else 0.0]
            score.append(out)
        else:
            if not is_active and response.status_code == 403:
                print(
                    f"Authentication blocked. Status: {response.status_code}, Response: {response.text}"
                )
                print(
                    f"✅ [CORRECT] Inactive user was correctly prevented from logging in."
                )
                score.append([1, 0, 100.0])
            else:
                print(
                    f"❌ [WRONG] Failed to authenticate active user or unexpected status. Status: {response.status_code}, Response: {response.text}"
                )
                score.append([0, 1, 0.0])

    print(f"\n{'='*60}\nTEST SUMMARY\n{'='*60}")
    print(
        f"| {'Role':<22} | {'Correct Outputs':<15} | {'Wrong Outputs':<13} | {'Accuracy':<8} |"
    )
    print(f"|{'-'*24}|{'-'*17}|{'-'*15}|{'-'*10}|")

    for user, s in zip(TEST_USERS, score):
        print(f"| {user['role']:<22} | {s[0]:<15} | {s[1]:<13} | {s[2]:>7.2f}% |")

    failed = [u["role"] for u, s in zip(TEST_USERS, score) if s[1] > 0]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
