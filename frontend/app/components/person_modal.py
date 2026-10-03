from nicegui import ui
from api_client.persons import PersonsClient
from api_client.reminders import RemindersClient
from api_client.users import UsersClient
from api_client.roles import RolesClient


class PersonModal:
    def __init__(self, title: str, on_save_callback, person_id: int | None = None):
        self.title = title
        self.on_save_callback = on_save_callback
        self.person_id = person_id
        self.dialog = None
        self.person_data = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "birth_date": None,
            "phone_number": "",
            "reminder_preference_id": None,
        }
        self.original_person_data = {}

    async def build(self):
        # Fetch existing person data if editing
        if self.person_id:
            person = await PersonsClient.get_person(self.person_id)
            if person:
                self.person_data = {k: person.get(k) for k in self.person_data.keys()}
                self.original_person_data = self.person_data.copy() # Snapshot original state

        # Fetch reminder preferences for the dropdown
        try:
            raw_prefs = await RemindersClient.get_preferences()
            pref_options = {p["id"]: p["name"] for p in raw_prefs}
        except Exception as e:
            ui.notify(f"Failed to load reminder preferences: {e}", type="warning")
            pref_options = {}

        with ui.dialog() as self.dialog, ui.card().classes(
            "w-full max-w-lg p-6 rounded-xl"
        ):
            ui.label(self.title).classes("text-2xl font-bold mb-4 text-gray-800")

            with ui.grid(columns=2).classes("w-full gap-4"):
                self.first_name_input = (
                    ui.input("First Name *")
                    .bind_value(self.person_data, "first_name")
                    .classes("w-full")
                    .props("outlined")
                )
                self.last_name_input = (
                    ui.input("Last Name *")
                    .bind_value(self.person_data, "last_name")
                    .classes("w-full")
                    .props("outlined")
                )

                self.email_input = (
                    ui.input("Email *")
                    .bind_value(self.person_data, "email")
                    .classes("w-full")
                    .props("outlined type=email")
                )
                self.phone_number_input = (
                    ui.input("Phone Number")
                    .bind_value(self.person_data, "phone_number")
                    .classes("w-full")
                    .props("outlined")
                )

                self.birth_date_input = (
                    ui.input("Birth Date")
                    .bind_value(self.person_data, "birth_date")
                    .classes("w-full")
                    .props("outlined type=date")
                )

                self.reminder_input = (
                    ui.select(
                        options=pref_options,
                        label="Reminder Preference",
                        clearable=True,
                    )
                    .bind_value(self.person_data, "reminder_preference_id")
                    .classes("w-full")
                    .props("outlined")
                )

            with ui.row().classes("w-full justify-end gap-4 mt-6"):
                ui.button("Cancel", on_click=self.dialog.close).props(
                    "flat text-color=gray-600"
                )
                ui.button("Save", on_click=self.save).props("unelevated color=primary")

    async def save(self):
        # Basic validation
        if (
            not self.person_data["first_name"]
            or not self.person_data["last_name"]
            or not self.person_data["email"]
        ):
            ui.notify("First Name, Last Name, and Email are required.", type="warning")
            return

        # Clean empty values
        if self.person_data["reminder_preference_id"] == "":
            self.person_data["reminder_preference_id"] = None

        # Create a true PATCH payload
        if self.person_id:
            payload = {}
            for key, value in self.person_data.items():
                if value != self.original_person_data.get(key):
                    payload[key] = value
        else:
            payload = self.person_data.copy()

        await self.on_save_callback(payload, self.person_id)
        self.dialog.close()

    async def open(self):
        await self.build()
        self.dialog.open()


async def person_modal(title: str, on_save_callback, person_id: int | None = None):
    modal = PersonModal(title, on_save_callback, person_id)
    return modal


# --- USER MODAL ---
class UserModal:
    def __init__(self, title: str, on_save_callback, user_id: int | None = None):
        self.title = title
        self.on_save_callback = on_save_callback
        self.user_id = user_id
        self.dialog = None
        self.user_data = {
            "person_id": None,
            "role_id": None,
            "password": "",
            "is_active": True,
        }
        self.original_user_data = {}

    async def build(self):
        # Fetch data for dropdowns
        raw_persons = await PersonsClient.get_persons()
        persons_options = {
            p["id"]: f"{p['first_name']} {p['last_name']} ({p['email']})"
            for p in raw_persons
        }

        raw_roles = await RolesClient.get_roles()
        roles_options = {r["id"]: r["name"] for r in raw_roles}

        if self.user_id:
            user = await UsersClient.get_user(self.user_id)
            if user:
                self.user_data["person_id"] = user.get("person", {}).get("id")
                self.user_data["role_id"] = user.get("role", {}).get("id")
                self.user_data["is_active"] = user.get("is_active", True)
                self.original_user_data = self.user_data.copy() # Snapshot original state

        with ui.dialog() as self.dialog, ui.card().classes(
            "w-full max-w-lg p-6 rounded-xl"
        ):
            ui.label(self.title).classes("text-2xl font-bold mb-4 text-gray-800")

            with ui.column().classes("w-full gap-4"):
                self.person_input = (
                    ui.select(
                        options=persons_options,
                        label="Person (Staff) *",
                        with_input=True,
                    )
                    .bind_value(self.user_data, "person_id")
                    .classes("w-full")
                    .props("outlined")
                )
                if self.user_id:
                    self.person_input.props(
                        "disable"
                    )  # Prevent changing the linked person on update

                self.role_input = (
                    ui.select(options=roles_options, label="Role *")
                    .bind_value(self.user_data, "role_id")
                    .classes("w-full")
                    .props("outlined")
                )

                pwd_label = (
                    "Password *"
                    if not self.user_id
                    else "New Password (leave blank to keep current)"
                )
                self.password_input = (
                    ui.input(pwd_label, password=True, password_toggle_button=True)
                    .bind_value(self.user_data, "password")
                    .classes("w-full")
                    .props("outlined")
                )

                self.active_input = (
                    ui.checkbox("Account is Active")
                    .bind_value(self.user_data, "is_active")
                    .classes("mt-2")
                )

            with ui.row().classes("w-full justify-end gap-4 mt-6"):
                ui.button("Cancel", on_click=self.dialog.close).props(
                    "flat text-color=gray-600"
                )
                ui.button("Save", on_click=self.save).props("unelevated color=primary")

    async def save(self):
        if not self.user_data["person_id"] or not self.user_data["role_id"]:
            ui.notify("Person and Role are required.", type="warning")
            return
        if not self.user_id and not self.user_data["password"]:
            ui.notify("Password is required for new users.", type="warning")
            return

        # Create a true PATCH payload
        if self.user_id:
            payload = {}
            for key, value in self.user_data.items():
                if value != self.original_user_data.get(key):
                    payload[key] = value
            
            # Handle password separately since it starts empty
            if self.user_data["password"]:
                payload["password"] = self.user_data["password"]
        else:
            payload = self.user_data.copy()
            if not payload.get("password"):
                payload.pop("password", None)

        await self.on_save_callback(payload, self.user_id)
        self.dialog.close()

    async def open(self):
        await self.build()
        self.dialog.open()


async def user_modal(title: str, on_save_callback, user_id: int | None = None):
    modal = UserModal(title, on_save_callback, user_id)
    return modal


# --- SIMPLE CREATION MODALS (Roles & Reminders) ---
class SimpleNameModal:
    def __init__(self, title: str, label: str, on_save_callback):
        self.title = title
        self.label = label
        self.on_save_callback = on_save_callback
        self.dialog = None
        self.data = {"name": ""}

    def build(self):
        with ui.dialog() as self.dialog, ui.card().classes(
            "w-full max-w-sm p-6 rounded-xl"
        ):
            ui.label(self.title).classes("text-2xl font-bold mb-4 text-gray-800")
            self.name_input = (
                ui.input(f"{self.label} *")
                .bind_value(self.data, "name")
                .classes("w-full")
                .props("outlined")
            )

            with ui.row().classes("w-full justify-end gap-4 mt-6"):
                ui.button("Cancel", on_click=self.dialog.close).props(
                    "flat text-color=gray-600"
                )
                ui.button("Save", on_click=self.save).props("unelevated color=primary")

    async def save(self):
        if not self.data["name"]:
            ui.notify(f"{self.label} is required.", type="warning")
            return
        await self.on_save_callback(self.data)
        self.dialog.close()

    def open(self):
        self.build()
        self.dialog.open()


def simple_name_modal(title: str, label: str, on_save_callback):
    return SimpleNameModal(title, label, on_save_callback)