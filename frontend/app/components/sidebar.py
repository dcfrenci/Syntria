from nicegui import app, ui


def create_sidebar(active_route: str = "/"):
    """Generates the navigation drawer with hover and active states."""
    with ui.left_drawer(value=True, fixed=True).classes(
        "bg-gray-200 p-4 w-64 rounded-tr-3xl rounded-br-3xl"
    ):

        with ui.row().classes("w-full items-center flex-nowrap py-6 gap-3 px-4"):
            # Note: I wrapped the icon in a button so it can actually be clicked to close/open the sidebar,
            # which is standard UI behavior, but you can change it back to just ui.icon if you prefer!
            ui.button(icon="r_menu").props("flat round dense").classes("text-black")
            ui.image("app/assets/images/syntria_name.svg").classes("h-8 w-32")

        ui.separator().classes("gap-0")

        def menu_item(icon: str, text: str, route: str):
            is_active = route == active_route
            base_classes = "menu-btn w-full justify-start py-3 px-4 rounded-xl text-lg text-black bg-transparent shadow-none"

            if is_active:
                base_classes += " menu-btn-active"

            with ui.button(on_click=lambda: ui.navigate.to(route)).classes(
                base_classes
            ).props("flat align=left"):
                # The gap-4 here matches the gap-4 in the header row above!
                with ui.row().classes("items-center gap-4"):
                    ui.icon(icon, size="sm")
                    ui.label(text)

        # 2. MENU ITEMS CONTAINER
        # Added px-2 to the column just so the hover backgrounds of the buttons don't touch the absolute edge of the screen
        with ui.column().classes("w-full gap-2 px-2"):
            user_role = app.storage.user.get("role", "").lower()

            menu_item("r_home", "Home", "/home")
            menu_item("r_menu_book", "Agenda", "/agenda")
            if user_role in ["admin", "manager", "secretary"]:
                menu_item("r_person", "Persons", "/persons")
            if user_role in [
                "admin",
                "manager",
                "secretary",
                "doctor",
                "assistant",
                "employee",
            ]:
                menu_item("r_attach_money", "Pricing", "/pricing")
            if user_role in ["admin", "manager", "secretary", "doctor"]:
                menu_item("r_edit", "Customize quote", "/preset")
            if user_role in ["admin", "manager"]:
                menu_item("r_settings", "Setting", "/settings")

        ui.space()

        user_name = app.storage.user.get("name", "Unknown User")
        user_role = app.storage.user.get("role", "Unknown Role")

        # Display the name and role
        with ui.column().classes("w-full gap-0 mb-3 pl-2"):
            ui.label(user_name).classes(
                "w-full text-center text-sm font-bold text-gray-900"
            )
            ui.label(f"Role: {user_role}").classes(
                "w-full text-center text-xs font-medium text-primary"
            )

        def perform_logout():
            app.storage.user["authenticated"] = False
            app.storage.user["token"] = None
            ui.navigate.to("/login")

        # 3. Add the logout button
        ui.button(
            "Logout", icon="logout", color="negative", on_click=perform_logout
        ).classes("mb-4 self-center")
