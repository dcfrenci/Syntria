import httpx
from datetime import datetime
from nicegui import ui
from api_client.persons import PersonsClient
from api_client.users import UsersClient
from api_client.roles import RolesClient
from api_client.reminders import RemindersClient
from components.modals import confirmation_modal
from components.person_modal import person_modal, user_modal, simple_name_modal
from components.style import Style


def handle_api_error(e: Exception, action: str):
    """Helper to consistently handle and display API errors."""
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 403:
            ui.notify(
                "Access Denied: Admin privileges required for this action.",
                type="negative",
                icon="gpp_bad",
                position="top",
            )
        else:
            try:
                detail = e.response.json().get("detail", "Unknown error")
            except Exception:
                detail = e.response.text or f"HTTP {e.response.status_code}"
            
            ui.notify(f"Failed to {action}: {detail}", type="warning")
    else:
        ui.notify(f"System error while trying to {action}: {e}", type="negative")


async def persons_page():
    """Renders the comprehensive Directory, Users, Roles, and Reminders view."""

    with ui.column().classes("w-full gap-10"):
        ui.label("System Manager & Access").classes(Style.title())

        def add_search(table, placeholder: str):
            with table.add_slot("top"):
                search_input = (
                    ui.input(placeholder=placeholder)
                    .classes("w-full text-base")
                    .props("clearable outlined rounded")
                )
                search_input.add_slot("prepend", '<q-icon name="search" />')
                table.bind_filter_from(search_input, "value")

        def check_selected(table, item_name: str) -> bool:
            if not table.selected:
                ui.notify(f"Select a {item_name} before proceeding", type="warning")
                return False
            return True

        # Persons
        with ui.column().classes("w-full"):
            ui.label("Persons").classes(Style.h2())

            # 1. Add a formatting function for the birth dates
            async def format_persons():
                raw = await PersonsClient.get_persons()
                for p in raw:
                    if p.get("birth_date"):
                        try:
                            p["birth_date"] = datetime.strptime(
                                str(p["birth_date"]).split("T")[0], "%Y-%m-%d"
                            ).strftime("%d/%m/%Y")
                        except ValueError:
                            pass
                return raw

            # 2. Update the refresh function to use formatted data
            async def refresh_persons():
                table_persons.rows = await format_persons()
                table_persons.selected.clear()
                table_persons.update()

            async def save_person(data: dict, pid: int | None = None):
                try:
                    if pid is None:
                        await PersonsClient.create_person(data=data)
                    else:
                        await PersonsClient.update_person(person_id=pid, data=data)
                    await refresh_persons()
                    ui.notify("Person saved successfully", type="positive")
                except Exception as e:
                    handle_api_error(e, "save person")

            async def delete_person(value: bool):
                if value:
                    try:
                        await PersonsClient.delete_person(
                            person_id=table_persons.selected[0]["id"]
                        )
                        await refresh_persons()
                        ui.notify("Person deleted", type="positive")
                    except Exception as e:
                        handle_api_error(e, "delete person")

            async def open_new_person():
                m = await person_modal("New Person", save_person)
                await m.open()

            async def open_edit_person():
                if check_selected(table_persons, "person"):
                    m = await person_modal(
                        "Edit Person", save_person, table_persons.selected[0]["id"]
                    )
                    await m.open()

            table_persons = ui.table(
                columns=[
                    {
                        "name": "first_name",
                        "label": "First Name",
                        "field": "first_name",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "last_name",
                        "label": "Last Name",
                        "field": "last_name",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "email",
                        "label": "Email",
                        "field": "email",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "phone_number",
                        "label": "Phone",
                        "field": "phone_number",
                        "align": "left",
                    },
                    {
                        "name": "birth_date",
                        "label": "Birth Date",
                        "field": "birth_date",
                        "align": "left",
                    },
                ],
                # 3. Supply the formatted data on initial load
                rows=await format_persons(),
                row_key="id",
                selection="single",
            ).classes(Style.table())
            add_search(table_persons, "Search persons...")

            delete_person_diag = confirmation_modal(
                title="Delete Person?",
                description="Permanently delete this person and all associated data?",
                on_save_callback=delete_person,
            )

            with ui.row().classes(Style.row_end()):
                ui.button("New", icon="r_add", on_click=open_new_person)
                ui.button("Edit", icon="r_edit", on_click=open_edit_person)
                ui.button(
                    "Delete",
                    icon="r_delete",
                    on_click=lambda: (
                        delete_person_diag.open()
                        if check_selected(table_persons, "person")
                        else None
                    ),
                )

        # User table
        with ui.column().classes("w-full"):
            ui.label("Account").classes(Style.h2())

            async def format_users():
                try:
                    raw = await UsersClient.get_users()
                    return [
                        {
                            "id": u["id"],
                            "name": f"{u['person']['first_name']} {u['person']['last_name']}",
                            "email": u["person"]["email"],
                            "role": u["role"]["name"],
                            "active": "Yes" if u["is_active"] else "No",
                        }
                        for u in raw
                    ]
                except Exception:
                    return []

            async def refresh_users():
                table_users.rows = await format_users()
                table_users.selected.clear()
                table_users.update()

            async def save_user(data: dict, uid: int | None = None):
                try:
                    if uid is None:
                        await UsersClient.create_user(data=data)
                    else:
                        await UsersClient.update_user(user_id=uid, data=data)
                    await refresh_users()
                    ui.notify("User saved successfully", type="positive")
                except Exception as e:
                    handle_api_error(e, "save user")

            async def delete_user(value: bool):
                if value:
                    try:
                        await UsersClient.delete_user(
                            user_id=table_users.selected[0]["id"]
                        )
                        await refresh_users()
                        ui.notify("User deleted", type="positive")
                    except Exception as e:
                        handle_api_error(e, "delete user")

            # Async click handlers for User Modals
            async def open_new_user():
                m = await user_modal("New User", save_user)
                await m.open()

            async def open_edit_user():
                if check_selected(table_users, "user"):
                    m = await user_modal(
                        "Edit User", save_user, table_users.selected[0]["id"]
                    )
                    await m.open()

            table_users = ui.table(
                columns=[
                    {
                        "name": "name",
                        "label": "Name",
                        "field": "name",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "email",
                        "label": "Email",
                        "field": "email",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "role",
                        "label": "Role",
                        "field": "role",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "active",
                        "label": "Active",
                        "field": "active",
                        "align": "left",
                        "sortable": True,
                    },
                ],
                rows=await format_users(),
                row_key="id",
                selection="single",
            ).classes(Style.table())
            add_search(table_users, "Search users...")

            delete_user_diag = confirmation_modal(
                title="Delete User?",
                description="Remove login access for this user?",
                on_save_callback=delete_user,
            )

            with ui.row().classes(Style.row_end()):
                ui.button("New", icon="r_add", on_click=open_new_user)
                ui.button("Edit", icon="r_edit", on_click=open_edit_user)
                ui.button(
                    "Delete",
                    icon="r_delete",
                    on_click=lambda: (
                        delete_user_diag.open()
                        if check_selected(table_users, "user")
                        else None
                    ),
                )

        # Role
        with ui.column().classes("w-full"):
            ui.label("Roles").classes(Style.h2())

            async def refresh_roles():
                table_roles.rows = await RolesClient.get_roles()
                table_roles.update()

            async def save_role(data: dict):
                try:
                    await RolesClient.create_role(data=data)
                    await refresh_roles()
                    ui.notify("Role created successfully", type="positive")
                except Exception as e:
                    handle_api_error(e, "create role")

            table_roles = ui.table(
                columns=[
                    {
                        "name": "name",
                        "label": "Role Name",
                        "field": "name",
                        "align": "left",
                        "sortable": True,
                    }
                ],
                rows=await RolesClient.get_roles(),
                row_key="id",
            ).classes(Style.table())

            with ui.row().classes(Style.row_end()):
                ui.button(
                    "New Role",
                    icon="r_add",
                    on_click=lambda: simple_name_modal(
                        "New Role", "Role Name", save_role
                    ).open(),
                )

        # Reminders
        with ui.column().classes("w-full pb-10"):
            ui.label("Reminder Preferences").classes(Style.h2())

            async def refresh_reminders():
                table_reminders.rows = await RemindersClient.get_preferences()
                table_reminders.update()

            async def save_reminder(data: dict):
                try:
                    await RemindersClient.create_preference(data=data)
                    await refresh_reminders()
                    ui.notify("Preference added", type="positive")
                except Exception as e:
                    handle_api_error(e, "save reminder preference")

            table_reminders = ui.table(
                columns=[
                    {
                        "name": "name",
                        "label": "Preference Name",
                        "field": "name",
                        "align": "left",
                        "sortable": True,
                    }
                ],
                rows=await RemindersClient.get_preferences(),
                row_key="id",
            ).classes(Style.table())

            with ui.row().classes(Style.row_end()):
                ui.button(
                    "New Preference",
                    icon="r_add",
                    on_click=lambda: simple_name_modal(
                        "New Reminder Preference", "Preference Name", save_reminder
                    ).open(),
                )
