from nicegui import ui

def home_page():
    """Renders the Home dashboard view."""
    with ui.column().classes('p-8 w-full'):
        
        ui.sub_pages({'/home': quotes, '/home/new_quote': new_quote})
    

def quotes():
    ui.label('Dashboard Home').classes('text-3xl font-bold mb-6 text-gray-800')
    with ui.card().classes('w-full p-6 border border-gray-200 rounded-xl shadow-none'):
        ui.label('Welcome to the Syntria Dashboard.').classes('text-lg')
        ui.label('Use the left menu to navigate through your services, agenda, and quotes.').classes('text-gray-500 mt-2')
        
    ui.link('Go to quote', '/home/new_quote')
    
def new_quote():
    
    ui.label('Dashboard New Quote').classes('text-3xl font-bold mb-6 text-gray-800')
    ui.link('Go to quote', '/home')
