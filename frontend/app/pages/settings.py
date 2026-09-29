from nicegui import ui
from components.style import Style
from components.export_modal import ExportModal
from components.import_modal import ImportModal

def settings_page():
    """Renders the centralized Settings view for data portability and configuration."""
    with ui.column().classes('w-full'):
        ui.label('Settings & Data Hub').classes(Style.title())
        
        with ui.row().classes('w-full gap-8'):
            
            # --- Left Column: Export Controls ---
            with ui.column().classes('flex-1'):
                ui.label('Export Data').classes(Style.h2())
                with ui.card().classes('w-full p-6 gap-4 shadow-sm border border-gray-100 rounded-xl').style('background: #f8fafc;'):
                    ui.label('Select an entity below to filter elements and download a centralized CSV copy. Nested details (like items within quotes) are perfectly serialized.').classes('text-gray-600 text-sm mb-2')
                    
                    ui.button('Export Quotes', icon="ios_share", on_click=ExportModal("quotes").open).classes('w-full').props('outline color=primary')
                    ui.button('Export Pricing (Items)', icon="ios_share", on_click=ExportModal("items").open).classes('w-full').props('outline color=primary')
                    ui.button('Export Agenda', icon="ios_share", on_click=ExportModal("reservations").open).classes('w-full').props('outline color=primary')
                    ui.button('Export Presets', icon="ios_share", on_click=ExportModal("presets").open).classes('w-full').props('outline color=primary')
                    
            # --- Right Column: Import Controls ---
            with ui.column().classes('flex-1'):
                ui.label('Import Data').classes(Style.h2())
                with ui.card().classes('w-full p-6 gap-4 shadow-sm border border-gray-100 rounded-xl').style('background: #f8fafc;'):
                    ui.label('Upload a previously exported CSV. Syntria will map dependencies and detect any ID conflicts to help you gracefully update, duplicate, or ignore data.').classes('text-gray-600 text-sm mb-2')
                    
                    ui.button('Import Quotes', icon="file_download", on_click=ImportModal("quotes").open).classes('w-full').props('unelevated color=primary')
                    ui.button('Import Pricing (Items)', icon="file_download", on_click=ImportModal("items").open).classes('w-full').props('unelevated color=primary')
                    ui.button('Import Agenda', icon="file_download", on_click=ImportModal("reservations").open).classes('w-full').props('unelevated color=primary')
                    ui.button('Import Presets', icon="file_download", on_click=ImportModal("presets").open).classes('w-full').props('unelevated color=primary')