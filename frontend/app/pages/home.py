from datetime import datetime
from PIL import Image


from nicegui import ui
from api_client.quotes import QuotesClient
from api_client.services import ServicesClient
from api_client.persons import PersonsClient
from components.teeth_selection import teeth_selection


def home_page():
    """Renders the Home dashboard view."""
    with ui.column().classes("p-8 w-full"):

        ui.sub_pages({"/home": quotes, "/home/quote_create": quote_create}).classes(
            "w-full"
        )


async def quotes():
    with ui.column().classes("w-full h-screen"):
        ui.label("Quote").classes("text-3xl font-bold mb-5")

        quotes = await QuotesClient.get_quotes()

        async def action(page):
            row = await quotes.get_selected_row()
            if row:
                ui.notify(str(row))
                ui.notify(f"{row['Name']}, {row['Surname']}")
                ui.navigate.to(page)
            else:
                ui.notify("Select a quote before")

        quotes = ui.aggrid(
            {
                "columnDefs": [
                    {"field": "id", "hide": True},
                    {
                        "headerName": "Name",
                        "field": "patient.first_name",
                        "sortable": True,
                    },
                    {
                        "headerName": "Surname",
                        "field": "patient.last_name",
                        "sortable": True,
                        "filter": "agTextColumnFilter",
                        "floatingFilter": True,
                    },
                    {
                        "headerName": "Date",
                        "field": "created_at",
                        "sortable": True,
                        ":valueFormatter": """
                        params => {
                            if (!params.value) return '';
                            const d = new Date(params.value);
                            const day = String(d.getDate()).padStart(2, '0');
                            const month = String(d.getMonth() + 1).padStart(2, '0');
                            const year = d.getFullYear();
                            return `${day}/${month}/${year}`;
                        }
                    """,
                    },
                ],
                "rowData": quotes,
                "rowSelection": {
                    "mode": "singleRow",
                    "checkboxes": False,
                    "enableClickSelection": True,
                },
            }
        )

        with ui.row():
            ui.button(
                "New",
                icon="r_add",
                on_click=lambda: ui.navigate.to("/home/quote_create"),
            )
            ui.button("Edit", icon="r_edit", on_click=lambda: action(""))
            ui.button("Print", icon="r_print", on_click=lambda: action(""))
            ui.button("Download", icon="r_download", on_click=lambda: action(""))
            ui.button("Delete", icon="r_delete", on_click=lambda: action(""))


async def quote_create():
    date_selected = {"date": None}
    person_selected = {"patient_id": None}
    staff_selected = {"staff_id": None}
    services_selected = {}

    with ui.column().classes("w-full"):

        ui.label("Dashboard New Quote").classes("text-3xl font-bold mb-5")

        # Staff selection and detail
        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            persons = {p["id"]: p for p in await PersonsClient.get_persons()}

            with ui.column():

                ui.label("Select Doctor").classes("text-lg font-bold mb-2")

                with ui.card().classes("w-full"):
                    names = {
                        k: f"{v['first_name']} {v['last_name']}"
                        for k, v in persons.items()
                    }
                    ui.select(options=names, with_input=True).bind_value(
                        staff_selected, "staff_id"
                    ).classes("w-full")


            with ui.column():
                ui.label("Doctor Details").classes("text-lg font-bold mb-2")
                with ui.card().classes("w-full h-full flex flex-center"):
                    with ui.row().classes("pl-4"):
                        ui.label("Name: ")
                        ui.label().bind_text_from(
                            staff_selected,
                            "staff_id",
                            backward=lambda id: (
                                f"{persons[id]['first_name']} {persons[id]['last_name']}"
                                if id in persons
                                else ""
                            ),
                        )
                    with ui.row().classes("pl-4"):
                        ui.label("Email: ")
                        ui.label().bind_text_from(
                            staff_selected,
                            "staff_id",
                            backward=lambda id: (
                                str(persons[id].get("email", ""))
                                if id in persons
                                else ""
                            ),
                        )

        # Patient selection and details
        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            persons = {p["id"]: p for p in await PersonsClient.get_persons()}

            with ui.column():

                ui.label("Select Patient").classes("text-lg font-bold mb-2")

                with ui.card().classes("w-full"):
                    names = {
                        k: f"{v['first_name']} {v['last_name']}"
                        for k, v in persons.items()
                    }
                    ui.select(options=names, with_input=True).bind_value(
                        person_selected, "patient_id"
                    ).classes("w-full")

                with ui.card().classes("w-full"):
                    ui.date_input(placeholder="Valid period").classes(
                        "w-full"
                    ).bind_value(date_selected, "date")

            with ui.column():
                ui.label("Patient Details").classes("text-lg font-bold mb-2")
                with ui.card().classes("w-full h-full flex flex-center"):
                    with ui.row().classes("pl-4"):
                        ui.label("Name: ")
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                f"{persons[id]['first_name']} {persons[id]['last_name']}"
                                if id in persons
                                else ""
                            ),
                        )
                    with ui.row().classes("pl-4"):
                        ui.label("Birth date: ")
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                str(persons[id].get("birth_date", ""))
                                if id in persons
                                else ""
                            ),
                        )
                    with ui.row().classes("pl-4"):
                        ui.label("Email: ")
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                str(persons[id].get("email", ""))
                                if id in persons
                                else ""
                            ),
                        )
                    with ui.row().classes("pl-4"):
                        ui.label("Phone: ")
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                str(persons[id].get("phone_number", ""))
                                if id in persons
                                else ""
                            ),
                        )

        # Service selection and teeth selection
        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            raw_services = await ServicesClient.get_items()

            services = [
                {
                    **s,
                    "category_name": (
                        s.get("category", {}).get("name", "")
                        if isinstance(s.get("category"), dict)
                        else getattr(s.get("category"), "name", "")
                    ),
                    "is_specific": s.get("is_specific", False),
                    "teeth": [],
                }
                for s in raw_services
            ]

            def refresh_selected_table():
                table_selected.rows = format_selected_rows()
                table_selected.selected = []

            def add_row(row: dict):
                row_id = row["id"]
                if row_id in services_selected:
                    services_selected[row_id]["quantity"] += 1
                else:
                    services_selected[row_id] = {
                        "id": row_id,
                        "name": row.get("name", ""),
                        "quantity": 1,
                        "discount": 0,
                        "teeth": [],
                        "is_specific": row.get("is_specific", False),
                    }
                refresh_selected_table()

            def remove_row(row: dict):
                row_id = row["id"]
                if row_id not in services_selected:
                    return
                if services_selected[row_id]["quantity"] > 1:
                    services_selected[row_id]["quantity"] -= 1
                else:
                    del services_selected[row_id]
                refresh_selected_table()

            # Button handlers
            def add_selected_button():
                if not table_services.selected:
                    ui.notify("Select a service first", type="warning")
                    return
                add_row(table_services.selected[0])

            def remove_selected_button():
                if not table_selected.selected:
                    ui.notify("Select a service first", type="warning")
                    return
                remove_row(table_selected.selected[0])

            def on_service_dblclick(e):
                # In NiceGUI, e.args contains [evt, row, index] from Quasar
                row = (
                    e.args[1]
                    if isinstance(e.args, list) and len(e.args) > 1
                    else e.args
                )
                if isinstance(row, dict):
                    add_row(row)
                    ui.notify(f"Added {row.get('name')}", type="positive", timeout=1000)

            def on_selected_dblclick(e):
                row = (
                    e.args[1]
                    if isinstance(e.args, list) and len(e.args) > 1
                    else e.args
                )
                if isinstance(row, dict):
                    open_teeth_modal(row)

            def save_teeth_selection(selected_teeth: set):
                global active_selected_id
                row_id = active_selected_id
                services_selected[row_id]["teeth"] = sorted(list(selected_teeth))
                refresh_selected_table()
                ui.notify(
                    f"Updated teeth for service {services_selected[row_id]["name"]}",
                    type="positive",
                )

            def open_teeth_modal(selected_item: dict | None):
                global active_selected_id
                if selected_item is None and not table_selected.selected:
                    ui.notify(
                        "Select a service in the right table to assign teeth",
                        type="warning",
                    )
                    return

                if not selected_item.get("is_specific", False):
                    ui.notify(
                        "The selected service is not tooth specific", type="warning"
                    )
                    return

                if selected_item is None:
                    selected_item = table_selected.selected[0]

                row_id = active_selected_id = selected_item["id"]
                current_teeth = services_selected[row_id].get("teeth", [])
                teeth_dialog_instance.open_with_teeth(current_teeth)

            def format_selected_rows():
                formatted = []
                for row in services_selected.values():
                    formatted.append(
                        {
                            **row,
                            "teeth_display": (
                                ", ".join(row["teeth"]) if row["teeth"] else "-"
                            ),
                        }
                    )
                return formatted

            table_css = "w-full h-[420px] rounded-xl"

            # --- Left Column: Available Services ---
            with ui.column().classes("w-full"):
                ui.label("Select Services").classes("text-lg font-bold")

                table_services = (
                    ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "category",
                                "label": "Category",
                                "field": "category_name",
                                "align": "left",
                                "sortable": True,
                            },
                        ],
                        rows=services,
                        row_key="id",
                        selection="single",
                    )
                    .classes(table_css)
                    .props("flat bordered")
                )

                with table_services.add_slot("top"):
                    search_input = (
                        ui.input(placeholder="Search service or category...")
                        .classes("w-full mb-2")
                        .props("clearable dense outlined rounded")
                    )
                    search_input.add_slot("prepend", '<q-icon name="search" />')

                table_services.bind_filter_from(search_input, "value")

                # Native Quasar row double click listener
                table_services.on("row-dblclick", on_service_dblclick)

                with ui.row().classes("mt-3 gap-2"):
                    ui.button("Add", icon="add", on_click=add_selected_button)

            # --- Right Column: Selected Services ---
            with ui.column().classes("w-full"):
                ui.label("Selected Services").classes("text-lg font-bold")

                table_selected = (
                    ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "align": "left",
                            },
                            {
                                "name": "quantity",
                                "label": "Amount",
                                "field": "quantity",
                                "align": "center",
                            },
                            {
                                "name": "teeth",
                                "label": "Teeth",
                                "field": "teeth_display",
                                "align": "left",
                            },
                        ],
                        rows=format_selected_rows(),
                        row_key="id",
                        selection="single",
                    )
                    .classes(table_css)
                    .props("flat bordered")
                )

                table_selected.on("row-dblclick", on_selected_dblclick)

                teeth_dialog_instance = teeth_selection(
                    on_save_callback=save_teeth_selection
                )

                with ui.row().classes("mt-3 gap-2"):
                    ui.button(
                        "Delete",
                        icon="delete",
                        color="negative",
                        on_click=remove_selected_button,
                    )
                    ui.button(
                        "Assign Teeth",
                        icon="medication",
                        on_click=open_teeth_modal,
                    )

        with ui.row():

            async def save_quote():

                if date_selected["date"] is None:
                    ui.notify("Incorrect date selected", type="warning")
                    return

                if person_selected["patient_id"] is None:
                    ui.notify("Incorrect patient selected", type="warning")
                    return

                if staff_selected["staff_id"] is None:
                    ui.notify("Incorrect staff selected", type="warning")
                    return

                if services_selected == {}:
                    ui.notify("Errors in service selection", type="warning")
                    return
                
                quote = {
                    "valid_until": date_selected["date"],
                    "patient_id": person_selected["patient_id"],
                    "staff_id": staff_selected["staff_id"],
                    "items": [{"item_id": 0, "quantity": 1, "discount": 0}],
                }
                await QuotesClient.create_quote(quote)

            ui.button("Save", icor="r_save", on_click=save_quote)
