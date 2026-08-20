from nicegui import ui
from app.api_client.agenda import AgendaClient

async def agenda_page():
    """Renders the Agenda calendar view."""
    reservations = await AgendaClient.get_reservations()

    with ui.column().classes('p-8 w-full'):
        ui.label('Agenda').classes('text-3xl font-bold mb-6 text-gray-800')

        # Header week view matching Figma layout[cite: 5]
        with ui.row().classes('w-full bg-gray-100 p-4 rounded-xl items-center justify-between'):
            ui.label('Week of 1 July - 7 July').classes('text-xl font-semibold text-gray-800')

        # Reservation list
        with ui.column().classes('mt-4 w-full gap-2'):
            if not reservations:
                ui.label('No reservations scheduled for this week.').classes('text-gray-500 italic')
            else:
                for res in reservations:
                    with ui.card().classes('w-full p-4 border border-gray-200 rounded-xl shadow-none'):
                        ui.label(f"Date: {res.get('reservation_date')}").classes('font-bold')
                        ui.label(f"Description: {res.get('description', 'No description provided')}").classes('text-gray-600')