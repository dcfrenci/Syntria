from nicegui import ui

def settings_page():
    """Renders the Settings view."""
    with ui.column().classes('p-8 w-full max-w-4xl'):
        ui.label('Settings').classes('text-3xl font-bold mb-6 text-gray-800')