from nicegui import ui
from app.api_client.services import ServicesClient
from app.components.modals import service_modal

async def pricing_page():
    """Renders the Pricing & Services management view."""
    # Fetch data asynchronously from FastAPI via ServicesClient
    items = await ServicesClient.get_items()

    with ui.column().classes('p-8 w-full'):
        ui.label('Pricing & Services').classes('text-3xl font-bold mb-6 text-gray-800')

        # Define save callback for the modal
        async def save_new_service(name: str, price: float):
            await ServicesClient.create_item({"name": name, "price": price})
            ui.navigate.reload()

        # Modal component
        modal = service_modal(on_save_callback=save_new_service)
        ui.button('Add New Service', icon='add', on_click=modal.open).classes(
            'bg-gray-900 text-white rounded-xl px-4 py-2 mb-6'
        )

        # Items Table
        columns = [
            {'name': 'name', 'label': 'Service Name', 'field': 'name', 'required': True, 'align': 'left'},
            {'name': 'price', 'label': 'Price (€)', 'field': 'price', 'align': 'right'},
        ]
        ui.table(columns=columns, rows=items, row_key='id').classes('w-full shadow-sm rounded-xl')