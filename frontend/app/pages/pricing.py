from nicegui import ui
from api_client.services import ServicesClient
from components.modals import service_modal, category_modal, confirmation_modal
from components.style import Style


async def pricing_page():
    """Renders the Pricing & Services management view."""

    with ui.column().classes("w-full"):

        def check_selected(table, type: str) -> bool:
            if not table.selected:
                ui.notify(f"Select a {type} before", type="warning")
                return False
            return True

        def add_search(table, type: str):
            with table.add_slot("top"):
                search_input = (
                    ui.input(placeholder=f"Search {type} ...")
                    .classes("w-full text-base")
                    .props("clearable outlined rounded")
                )
                search_input.add_slot("prepend", '<q-icon name="search" />')
                table.bind_filter_from(search_input, "value")

        async def load_items():
            raw_items = await ServicesClient.get_items()
            items = [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "description": item["description"],
                    "category": item["category"]["name"],
                    "category_id": item["category"]["id"],
                    "price": item["price"],
                    "active": "Yes" if item["is_active"] else "No",
                    "specific": "Yes" if item["is_specific"] else "No",
                }
                for item in raw_items
            ]
            return items

        async def refresh_items():
            table_items.rows = await load_items()
            table_items.selected.clear()
            table_items.update()

        async def save_service(item: dict, id: int | None = None):
            if id is None:
                await ServicesClient.create_item(data=item)
            else:
                await ServicesClient.update_item(item_id=id, data=item)
            await refresh_items()
            
        async def new_service():
            modal = await service_modal(
                title="New Service", on_save_callback=save_service
            )
            modal.open()

        async def edit_service():
            if check_selected(table_items, type="service"):
                modal = await service_modal(
                    title="Edit Service",
                    on_save_callback=save_service,
                    item_id=table_items.selected[0]["id"],
                )
                modal.open()

        async def delete_service(value: bool):
            if value:
                await ServicesClient.delete_item(item_id=table_items.selected[0]["id"])
                await refresh_items()
                ui.notify("The service has been deleted", type="positive")

        async def load_categories():
            raw_categories = await ServicesClient.get_categories()
            categories = [
                {
                    "id": cat["id"],
                    "name": cat["name"],
                    "description": cat["description"],
                    "active": "Yes" if cat["is_active"] else "No",
                }
                for cat in raw_categories
            ]
            return categories

        async def refresh_categories():
            table_categories.rows = await load_categories()
            table_categories.selected.clear()
            table_categories.update()

        async def save_category(category: dict, id: int | None = None):
            if id is None:
                await ServicesClient.create_category(data=category)
            else:
                await ServicesClient.update_category(category_id=id, data=category)
            await refresh_categories()
            
        async def new_category():
            modal = await category_modal(
                title="New Category", on_save_callback=save_category
            )
            modal.open()

        async def edit_category():
            if check_selected(table_categories, type="category"):
                modal = await category_modal(
                    title="Edit Category",
                    on_save_callback=save_category,
                    category_id=table_categories.selected[0]["id"],
                )
                modal.open()

        async def delete_category(value: bool):
            if value:
                await ServicesClient.delete_category(
                    item_id=table_categories.selected[0]["id"]
                )
                await refresh_items()
                ui.notify("The category has been deleted", type="positive")

        ui.label("Pricing").classes(Style.h1())

        ui.label("Services").classes(Style.h2())

        table_items = ui.table(
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
                    "field": "category",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "price",
                    "label": "Price (€)",
                    "field": "price",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "specific",
                    "label": "Specific",
                    "field": "specific",
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
            rows=await load_items(),
            row_key="id",
            selection="single",
        ).classes(Style.table())

        add_search(table=table_items, type="service")

        delete_service_diag = confirmation_modal(
            title="Delete Service?",
            description="Are you sure you want to permanently delete this service and all its details?",
            on_save_callback=delete_service,
        )

        with ui.row().classes(Style.row_end()):
            ui.button("New", icon="r_add", on_click=new_service)
            ui.button("Edit", icon="r_edit", on_click=edit_service)
            ui.button("Delete", icon="r_delete", on_click=delete_service_diag.open)

        ui.label("Categories").classes(Style.h2())

        table_categories = ui.table(
            columns=[
                {
                    "name": "name",
                    "label": "Category Name",
                    "field": "name",
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
            rows=await load_categories(),
            row_key="id",
            selection="single",
        ).classes(Style.table())

        add_search(table=table_categories, type="category")

        delete_category_diag = confirmation_modal(
            title="Delete Category?",
            description="Are you sure you want to permanently delete this category and all its details?",
            on_save_callback=delete_category,
        )

        with ui.row().classes(Style.row_end()):
            ui.button("New", icon="r_add", on_click=new_category)
            ui.button("Edit", icon="r_edit", on_click=edit_category)
            ui.button("Delete", icon="r_delete", on_click=delete_category_diag.open)
