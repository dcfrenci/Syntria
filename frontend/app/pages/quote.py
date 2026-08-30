from nicegui import ui

def quote_page():
    """Renders the Customize Quote view"""
    with ui.column().classes('p-8 w-full'):
        ui.label('New Quote / Edit Quote').classes('text-3xl font-bold mb-6 text-gray-800')

        with ui.row().classes('w-full gap-8'):
            # Left Column: Patient & Quote details
            with ui.column().classes('w-1/3 gap-4'):
                ui.input('Name').classes('w-full')
                ui.input('Surname').classes('w-full')
                ui.input('Date', type='date').classes('w-full')
                ui.select(label='Services', options=['Dental Cleaning', 'Consultation']).classes('w-full')
                ui.button('Create Quote', on_click=lambda: ui.notify('Quote Draft Created')).classes(
                    'bg-gray-900 text-white rounded-xl py-2 mt-4'
                )
