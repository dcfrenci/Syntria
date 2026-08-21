from nicegui import ui

def reminders_page():
    """Renders the Reminders view."""
    with ui.column().classes('p-8 w-full max-w-4xl'):
        ui.label('Reminders').classes('text-3xl font-bold mb-6 text-gray-800')

        ui.label('Automatic').classes('text-xl font-bold mb-2 text-gray-700')
        with ui.card().classes('w-full bg-green-100 p-4 mb-6 flex flex-row justify-between items-center shadow-none rounded-xl'):
            ui.label('Today reminder').classes('text-green-900 font-medium')
            with ui.row().classes('gap-4 text-green-900'):
                ui.icon('notifications_off', size='sm').classes('cursor-pointer')
                ui.icon('edit', size='sm').classes('cursor-pointer')
                ui.icon('delete', size='sm').classes('cursor-pointer')

        ui.label('Manual').classes('text-xl font-bold mb-2 text-gray-700')
        with ui.card().classes('w-full bg-gray-100 p-4 flex flex-row justify-between items-center shadow-none rounded-xl'):
            ui.label('Today reminder').classes('text-gray-800 font-medium')
            with ui.row().classes('gap-4 text-gray-800'):
                ui.icon('send', size='sm').classes('cursor-pointer')
                ui.icon('edit', size='sm').classes('cursor-pointer')
                ui.icon('delete', size='sm').classes('cursor-pointer')