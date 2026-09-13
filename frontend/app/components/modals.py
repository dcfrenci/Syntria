from nicegui import ui
from components.style import Style

def service_modal(on_save_callback):
    """Generates the 'New Service' modal popup."""
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        ui.label('New Service').classes('text-2xl font-bold mb-4 text-gray-800')
        
        # Form Inputs matching the Figma design[cite: 3]
        name_input = ui.input('Name').classes('w-full mb-2')
        price_input = ui.number('Price', format='%.2f').classes('w-full mb-2')
        
        # Action Buttons
        with ui.row().classes('w-full justify-end mt-4 gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('outline')
            ui.button('Apply', on_click=lambda: [
                on_save_callback(name_input.value, price_input.value), 
                dialog.close()
            ])
            
    return dialog


def confirmation_model(title: str, description: str, on_save_callback):
    """Generates a customizable modal popup."""
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        ui.label(title).classes(Style.h1())
        
        ui.label(description).classes(Style.p())
        
        async def handle_cancel():
            await on_save_callback(False)
            dialog.close()
        
        async def handle_confirm():
            await on_save_callback(True)
            dialog.close()
        
        with ui.row().classes(Style.row_end()):
            ui.button('Cancel', on_click=handle_cancel).props('outline')
            ui.button('Confirm', on_click=handle_confirm)
        
    return dialog