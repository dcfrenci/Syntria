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

        

        ui.button(
            "Add New Service",
            icon="add",
            on_click=teeth_selection(on_save_callback=save_teeth_selection).open,
        )


        with ui.grid(columns="1fr 1fr").classes("w-full gap-8 mb-8 items-start"):

            raw_services = await ServicesClient.get_items()

            services = [
                {
                    **s,
                    "category_name": s.get("category", {}).get("name", "")
                    if isinstance(s.get("category"), dict)
                    else getattr(s.get("category"), "name", ""),
                    "is_specific": s.get("is_specific", False),
                    "teeth": [],
                }
                for s in raw_services
            ]

            services_selected = {}

            def refresh_selected_table():
                table_selected.rows = list(services_selected.values())
                table_selected.selected = []

            def add_row(row: dict):
                row_id = row["id"]
                if row_id in services_selected:
                    services_selected[row_id]["quantity"] += 1
                else:
                    services_selected[row_id] = {
                        "id": row_id,
                        "name": row["name"],
                        "quantity": 1,
                        "discount": 0,
                        "teeth": row.get("teeth", []),
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

            # Native Quasar row-dblclick event handlers (args: [event, row, index])
            def on_service_dblclick(e):
                # In NiceGUI, e.args contains [evt, row, index] from Quasar
                row = e.args[1] if isinstance(e.args, list) and len(e.args) > 1 else e.args
                if isinstance(row, dict):
                    add_row(row)
                    ui.notify(f"Added {row.get('name')}", type="positive", timeout=1000)

            def on_selected_dblclick(e):
                row = e.args[1] if isinstance(e.args, list) and len(e.args) > 1 else e.args
                if isinstance(row, dict):
                    remove_row(row)
                    ui.notify(f"Decreased {row.get('name')}", type="info", timeout=1000)

            def save_teeth_selection(selected_teeth: set):
                if not table_selected.selected:
                    ui.notify("Select a service in the right table to assign teeth", type="warning")
                    return
                row_id = table_selected.selected[0]["id"]
                services_selected[row_id]["teeth"] = sorted(list(selected_teeth))
                refresh_selected_table()
                ui.notify(f"Updated teeth for service {row_id}", type="positive")
                
                
            def save_teeth_selection(selected_services: set, primary: bool):
                ui.notify(selected_services)
                ui.notify(primary)

            table_css = "w-full h-[420px] rounded-xl"

            # --- Left Column: Available Services ---
            with ui.column().classes("w-full"):
                ui.label("Select Services").classes("text-lg font-bold")

                table_services = ui.table(
                    columns=[
                        {"name": "name", "label": "Name", "field": "name", "align": "left", "sortable": True},
                        {"name": "category", "label": "Category", "field": "category_name", "align": "left", "sortable": True},
                    ],
                    rows=services,
                    row_key="id",
                    selection="single",
                ).classes(table_css).props('flat bordered')
                
                with table_services.add_slot('top'):
                    search_input = ui.input(placeholder="Search service or category...").classes("w-full mb-2").props("clearable dense outlined rounded")
                    search_input.add_slot("prepend", '<q-icon name="search" />')

                table_services.bind_filter_from(search_input, "value")

                # Native Quasar row double click listener
                table_services.on("row-dblclick", on_service_dblclick)

                with ui.row().classes("mt-3 gap-2"):
                    ui.button("Add", icon="add", on_click=add_selected_button)

            # --- Right Column: Selected Services ---
            with ui.column().classes("w-full"):
                ui.label("Selected Services (Double-click to decrease)").classes("text-lg font-bold mb-[52px]")

                table_selected = ui.table(
                    columns=[
                        {"name": "name", "label": "Name", "field": "name", "align": "left"},
                        {"name": "quantity", "label": "Amount", "field": "quantity", "align": "center"},
                        {"name": "teeth", "label": "Teeth", "field": "teeth", "align": "left"},
                    ],
                    rows=list(services_selected.values()),
                    row_key="id",
                    selection="single",
                ).classes(table_css).props('flat bordered')
                
                with table_selected.add_slot('body-cell-teeth'):
                    with table_selected.cell('teeth'):
                        ui.label().bind_text_from(services_selected, "teeth", ':props="props"')

                table_selected.on("row-dblclick", on_selected_dblclick)

                with ui.row().classes("mt-3 gap-2"):
                    ui.button("Delete", icon="delete", color="negative", on_click=remove_selected_button)
                    ui.button(
                        "Assign Teeth",
                        icon="medication",
                        on_click=teeth_selection(on_save_callback=save_teeth_selection).open,
                    )


async def quote_create():

    with ui.column().classes("w-full"):

        ui.label("Dashboard New Quote").classes("text-3xl font-bold mb-5")

        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            persons = {p["id"]: p for p in await PersonsClient.get_persons()}
            person_selected = {"patient_id": None}

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
                    ui.date_input(placeholder="Valid period", range_input=True).classes(
                        "w-full"
                    )

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

        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            services = await ServicesClient.get_items()
            services_selected = {}

            def refresh_selected_grid():
                grid_selected.options["rowData"] = list(services_selected.values())
                grid_selected.update()

            async def add():
                row = await grid_services.get_selected_row()
                if row:
                    if row["id"] in services_selected.keys():
                        services_selected[row["id"]]["quantity"] += 1
                    else:
                        services_selected[row["id"]] = {
                            "id": row["id"],
                            "name": row["name"],
                            "quantity": 1,
                            "discount": 0,
                            "teeth": [],
                        }
                    refresh_selected_grid()
                else:
                    ui.notify("Select a service before")

            with ui.row().classes("w-full"):
                ui.label("Select services").classes("text-lg font-bold mb-2")

                grid_services = ui.aggrid(
                    {
                        "columnDefs": [
                            {"field": "id", "hide": True},
                            {"headerName": "Name", "field": "name"},
                            {"headerName": "Category", "field": "category.name"},
                        ],
                        "rowData": services,
                        "rowSelection": {
                            "mode": "singleRow",
                            "checkboxes": False,
                            "enableClickSelection": True,
                        },
                    }
                )

                ui.button("Add", icon="r_add", on_click=lambda: add())

            async def remove():
                row = await grid_selected.get_selected_row()
                if row:
                    if services_selected[row["id"]]["quantity"] > 1:
                        services_selected[row["id"]]["quantity"] -= 1
                    else:
                        del services_selected[row["id"]]
                    refresh_selected_grid()
                else:
                    ui.notify("Select a service before")

            with ui.row().classes("w-full"):
                ui.label("Selected services").classes("text-lg font-bold mb-2")

                grid_selected = ui.aggrid(
                    {
                        "columnDefs": [
                            {"field": "id", "hide": True},
                            {"headerName": "Name", "field": "name"},
                            {"headerName": "Amount", "field": "quantity"},
                            {"headerName": "Teeth", "field": "teeth"},
                        ],
                        "rowData": list(services_selected.values()),
                        "rowSelection": {
                            "mode": "singleRow",
                            "checkboxes": False,
                            "enableClickSelection": True,
                        },
                    }
                )

                ui.button("Delete", icon="r_delete", on_click=lambda: remove())
