from datetime import datetime
import traceback


from nicegui import ui
from api_client.quotes import QuotesClient
from api_client.services import ServicesClient
from api_client.persons import PersonsClient
from api_client.presets import PresetsClient
from components.quote_preview_modal import QuotePreviewModal
from components.teeth_selection import teeth_selection
from components.modals import confirmation_modal
from components.style import Style


def home_page():
    """Renders the Home dashboard view."""
    with ui.column().classes("w-full"):

        ui.sub_pages(
            {
                "/home": quotes,
                "/home/quote_create": quote_create,
                "/home/quote_edit/{id}": quote_edit,
            }
        ).classes("w-full")


async def quotes():
    quote_preview_modal = QuotePreviewModal()

    with ui.column().classes("w-full"):
        ui.label("Quote").classes(Style.title())

        async def load_quotes():
            row_quotes = await QuotesClient.get_quotes()
            quotes = [
                {
                    "id": quote["id"],
                    "name": f"{quote['patient']['first_name']} {quote['patient']['last_name']}",
                    "created_at": datetime.fromisoformat(quote["created_at"])
                    .date()
                    .strftime("%d/%m/%Y"),
                    "staff": f"{quote['staff']['first_name']} {quote['staff']['last_name']}",
                }
                for quote in row_quotes
            ]
            return quotes

        def check_selected() -> bool:
            if not table_quotes.selected:
                ui.notify("Select a quote before", type="warning")
                return False
            return True

        def edit():
            if check_selected():
                ui.navigate.to(f"/home/quote_edit/{table_quotes.selected[0]['id']}")

        def delete():
            async def on_save_callback(result: bool):
                if result:
                    await QuotesClient.delete_quote(
                        quote_id=table_quotes.selected[0]["id"]
                    )
                    table_quotes.rows = await load_quotes()
                    table_quotes.selected.clear()
                    table_quotes.update()
                    ui.notify("The quote has been deleted", type="positive")

            if check_selected():
                confirmation_modal(
                    title="Delete Quote?",
                    description="Are you sure you want to permanently delete this quote and all its details?",
                    on_save_callback=on_save_callback,
                ).open()

        async def handle_quote_action(action: str):
            if not check_selected():
                return
                
            quote_id = table_quotes.selected[0]["id"]
            
            try:
                quote_data = await QuotesClient.get_quote_with_id(quote_id)
                presets = await PresetsClient.get_presets()
                active_preset = next((p for p in presets if p.get("is_active")), None)
                
                if not active_preset:
                    ui.notify("No active preset found. Please activate one in Presets.", type="warning")
                    return
                
                # Split traffic based on the user's intent
                if action in ['print', 'download']:
                    await quote_preview_modal.process_direct(active_preset, quote_data, action)
                else:
                    await quote_preview_modal.open(active_preset, quote_data)
                    
            except Exception as e:
                ui.notify(f"Failed to process quote document: {str(e)}", type="negative")

        table_quotes = ui.table(
            columns=[
                {
                    "name": "name",
                    "label": "Name",
                    "field": "name",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "date": "date",
                    "label": "Date",
                    "field": "created_at",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "staff": "staff",
                    "label": "Doctor",
                    "field": "staff",
                    "align": "left",
                    "sortable": True,
                },
            ],
            rows=await load_quotes(),
            row_key="id",
            selection="single",
        ).classes(Style.table())

        with table_quotes.add_slot("top"):
            search_input = (
                ui.input(placeholder="Search patient or doctor...")
                .classes("w-full text-base")
                .props("clearable outlined rounded")
            )
            search_input.add_slot("prepend", '<q-icon name="search" />')

        table_quotes.bind_filter_from(search_input, "value")

        with ui.row().classes(Style.row_end()):
            ui.button("New", icon="r_add", on_click=lambda: ui.navigate.to("/home/quote_create"))
            ui.button("Edit", icon="r_edit", on_click=edit)
            ui.button("Preview", icon="visibility", on_click=lambda: handle_quote_action("preview"))
            ui.button("Print", icon="r_print", on_click=lambda: handle_quote_action("print"))
            ui.button("Download", icon="r_download", on_click=lambda: handle_quote_action("download"))
            ui.button("Delete", icon="r_delete", on_click=delete)


async def quote_detail(
    title: str,
    id: int | None = None,
    date_selected: dict | None = None,
    person_selected: dict | None = None,
    staff_selected: dict | None = None,
    services_selected: dict | None = None,
):
    date_selected = date_selected or {"date": None}
    person_selected = person_selected or {"patient_id": None}
    staff_selected = staff_selected or {"staff_id": None}
    services_selected = services_selected or {}

    with ui.column().classes("w-full"):

        ui.label(title).classes(Style.title())

        # Staff selection and detail
        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            persons = {p["id"]: p for p in await PersonsClient.get_persons()}

            with ui.column():

                ui.label("Select Doctor").classes(Style.h2())

                with ui.card().classes("w-full"):
                    names = {
                        k: f"{v['first_name']} {v['last_name']}"
                        for k, v in persons.items()
                    }
                    ui.select(options=names, with_input=True).bind_value(
                        staff_selected, "staff_id"
                    ).classes(Style.p())

            with ui.column():
                ui.label("Doctor Details").classes(Style.h2())
                with ui.card().classes("w-full h-full flex flex-center"):
                    with ui.row().classes("pl-4"):
                        ui.label("Name: ").classes(Style.p_fit())
                        ui.label().bind_text_from(
                            staff_selected,
                            "staff_id",
                            backward=lambda id: (
                                f"{persons[id]['first_name']} {persons[id]['last_name']}"
                                if id in persons
                                else ""
                            ),
                        ).classes(Style.p_fit())
                    with ui.row().classes("pl-4"):
                        ui.label("Email: ").classes(Style.p_fit())
                        ui.label().bind_text_from(
                            staff_selected,
                            "staff_id",
                            backward=lambda id: (
                                str(persons[id].get("email", ""))
                                if id in persons
                                else ""
                            ),
                        ).classes(Style.p_fit())

        # Patient selection and details
        with ui.grid(columns="1fr 1fr").classes("w-full gap-10 mb-8"):

            persons = {p["id"]: p for p in await PersonsClient.get_persons()}

            with ui.column():

                ui.label("Select Patient").classes(Style.h2())

                with ui.card().classes("w-full"):
                    names = {
                        k: f"{v['first_name']} {v['last_name']}"
                        for k, v in persons.items()
                    }
                    ui.select(options=names, with_input=True).bind_value(
                        person_selected, "patient_id"
                    ).classes(Style.p())

                with ui.card().classes("w-full"):
                    ui.date_input(placeholder="Valid period").classes(
                        Style.p()
                    ).bind_value(date_selected, "date")

            with ui.column():
                ui.label("Patient Details").classes(Style.h2())
                with ui.card().classes("w-full h-full flex flex-center"):
                    with ui.row().classes("pl-4"):
                        ui.label("Name: ").classes(Style.p_fit())
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                f"{persons[id]['first_name']} {persons[id]['last_name']}"
                                if id in persons
                                else ""
                            ),
                        ).classes(Style.p_fit())
                    with ui.row().classes("pl-4"):
                        ui.label("Birth date: ").classes(Style.p_fit())
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                datetime.strptime(
                                    persons[id].get("birth_date"), "%Y-%m-%d"
                                ).strftime("%d/%m/%Y")
                                if id in persons and persons[id].get("birth_date")
                                else ""
                            ),
                        ).classes(Style.p_fit())
                    with ui.row().classes("pl-4"):
                        ui.label("Email: ").classes(Style.p_fit())
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                str(persons[id].get("email", ""))
                                if id in persons
                                else ""
                            ),
                        ).classes(Style.p_fit())
                    with ui.row().classes("pl-4"):
                        ui.label("Phone: ").classes(Style.p_fit())
                        ui.label().bind_text_from(
                            person_selected,
                            "patient_id",
                            backward=lambda id: (
                                str(persons[id].get("phone_number", ""))
                                if id in persons
                                else ""
                            ),
                        ).classes(Style.p_fit())

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
                                ", ".join(str(t) for t in row["teeth"]) if row["teeth"] else "-"
                            ),
                        }
                    )
                return formatted

            table_css = "w-[calc(100%-2rem)] h-[420px] m-2 rounded-xl shadow-lg"

            # --- Left Column: Available Services ---
            with ui.column().classes("w-full"):
                ui.label("Select Services").classes(Style.h2())

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
                        .classes("w-full text-base")
                        .props("clearable outlined rounded")
                    )
                    search_input.add_slot("prepend", '<q-icon name="search" />')

                table_services.bind_filter_from(search_input, "value")

                # Native Quasar row double click listener
                table_services.on("row-dblclick", on_service_dblclick)

                with ui.row().classes("mt-3 gap-2"):
                    ui.button("Add", icon="add", on_click=add_selected_button)

            # --- Right Column: Selected Services ---
            with ui.column().classes("w-full"):
                ui.label("Selected Services").classes(Style.h2())

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

        # Save quote
        with ui.page_sticky(x_offset=30, y_offset=30):

            async def close_quote():
                async def on_save_callback(result: bool):
                    if result:
                        ui.notify("The quote has not been saved", type="info")
                        ui.navigate.to("/home")
                        return

                confirmation_modal(
                    title="Exit Quote?",
                    description="Are you sure you want to exit without saving? All recent changes will be lost.",
                    on_save_callback=on_save_callback,
                ).open()

            async def save_quote():

                if staff_selected["staff_id"] is None:
                    ui.notify("Incorrect staff selected", type="warning")
                    return
                if person_selected["patient_id"] is None:
                    ui.notify("Incorrect patient selected", type="warning")
                    return

                if date_selected["date"] is None:
                    ui.notify("Incorrect date selected", type="warning")
                    return

                if services_selected == {}:
                    ui.notify("Errors in service selection", type="warning")
                    return

                async def on_save_callback(result: bool):
                    if not result:
                        ui.notify("The quote has not been saved", type="info")
                        return

                    items = [
                        {
                            "item_id": service["id"],
                            "quantity": service["quantity"],
                            "discount": service["discount"],
                            "teeth": service["teeth"],
                        }
                        for service in services_selected.values()
                    ]

                    quote = {
                        "valid_until": date_selected["date"],
                        "patient_id": person_selected["patient_id"],
                        "staff_id": staff_selected["staff_id"],
                        "items": items,
                    }

                    if id:
                        res = await QuotesClient.update_quote(id, quote)
                    else:
                        res = await QuotesClient.create_quote(quote)
                        ui.navigate.to(f"/home/quote_edit/{res["id"]}")

                    if res:
                        ui.notify("Quote saved successfully", type="positive")
                    else:
                        ui.notify("Error while saving the quote", type="negative")

                confirmation_modal(
                    title="Save Quote?",
                    description="Are you sure you want to save this quote and its selected services?",
                    on_save_callback=on_save_callback,
                ).open()

            with ui.row():
                ui.button("Close", icon="r_close", on_click=close_quote)
                ui.button("Save", icon="r_save", on_click=save_quote)


async def quote_create():
    try:
        await quote_detail(title="New Quote")
    except Exception as e:
        ui.label(f"Crash detected: {str(e)}").classes("text-red text-xl font-bold")
        print(traceback.format_exc(), flush=True)


async def quote_edit(id: int):
    try:
        quote = await QuotesClient.get_quote_with_id(id)

        services_selected = {
            item["item_id"]: {
                "id": item["item_id"],
                "name": item["item"]["name"],
                "quantity": item["quantity"],
                "discount": item["discount"],
                "teeth": item["teeth"],
                "is_specific": item["item"]["is_specific"],
            }
            for item in quote["quote_items"]
        }

        await quote_detail(
            title="Edit Quote",
            id=id,
            date_selected={"date": quote["valid_until"]},
            person_selected={"patient_id": quote["patient"]["id"]},
            staff_selected={"staff_id": quote["staff"]["id"]},
            services_selected=services_selected,
        )
    except Exception as e:
        ui.label(f"Crash detected: {str(e)}").classes("text-red text-xl font-bold")
        print(traceback.format_exc(), flush=True)
