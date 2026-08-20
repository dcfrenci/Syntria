from contextlib import contextmanager
from nicegui import ui, app

# Import your shared components
from app.components.sidebar import create_sidebar

# Import your page content functions
from app.pages.home import home_page
from app.pages.pricing import pricing_page
from app.pages.agenda import agenda_page
from app.pages.quote import quote_page
from app.pages.reminders import reminders_page

@contextmanager
def frame(page_title: str, active_route: str):
    """A reusable layout wrapper that injects the sidebar and standardizes the page container."""
    ui.page_title(page_title)
    # Background color of the whole app
    ui.query('body').classes('bg-white') 
    
    ui.add_head_html('<link href="/assets/style.css" rel="stylesheet">')
    
    # Render the sidebar with the correct active hover state
    create_sidebar(active_route=active_route)
    
    # Create the main content container
    with ui.column().classes('w-full max-w-7xl mx-auto h-screen overflow-y-auto pl-64'): 
        yield

# --- Routes Registration ---

@ui.page('/')
def home_route():
    with frame('Home - Syntria', active_route='/'):
        home_page()

@ui.page('/agenda')
async def agenda_route():
    with frame('Agenda - Syntria', active_route='/agenda'):
        await agenda_page()

@ui.page('/pricing')
async def pricing_route():
    with frame('Pricing - Syntria', active_route='/pricing'):
        await pricing_page()

@ui.page('/quote')
def quote_route():
    with frame('Quotes - Syntria', active_route='/quote'):
        quote_page()

@ui.page('/reminders')
def reminders_route():
    with frame('Reminders - Syntria', active_route='/reminders'):
        reminders_page()

# Initialize the UI server
ui.run(title="Syntria", port=8080, host="0.0.0.0", reload=True)