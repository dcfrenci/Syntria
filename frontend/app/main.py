from contextlib import contextmanager
from nicegui import app, ui

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Import your shared components
from components.sidebar import create_sidebar

# Import your page content functions
from pages.login import login_page
from pages.home import home_page
from pages.pricing import pricing_page
from pages.agenda import agenda_page
from pages.quote import quote_page
from pages.reminders import reminders_page
from pages.settings import settings_page


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if request.url.path not in ['/login'] and not request.url.path.startswith('/_nicegui'):
                return RedirectResponse('/login')
        return await call_next(request)


app.add_static_files('/assets', 'app/assets')

app.add_middleware(AuthMiddleware)


@contextmanager
def frame(page_title: str, active_route: str):
    """A reusable layout wrapper that injects the sidebar and standardizes the page container."""
    ui.page_title(page_title)
    # Background color of the whole app
    ui.query('body').classes('bg-white') 
    
    
    # Render the sidebar with the correct active hover state
    create_sidebar(active_route=active_route)
    
    # Create the main content container
    with ui.column().classes('w-full max-w-7xl mx-auto h-screen overflow-y-auto'): 
        yield

# --- Routes Registration ---
@ui.page('/login')
def auth_route():
    login_page()

@ui.page('/home')
@ui.page('/home/quote_create')
@ui.page('/home/quote_edit/{id}')
def home_route():
    with frame(page_title='Home', active_route='/home'):
        home_page()

@ui.page('/agenda')
async def agenda_route():
    with frame(page_title='Agenda', active_route='/agenda'):
        await agenda_page()

@ui.page('/pricing')
async def pricing_route():
    with frame(page_title='Pricing', active_route='/pricing'):
        await pricing_page()

@ui.page('/quote')
def quote_route():
    with frame(page_title='Quotes', active_route='/quote'):
        quote_page()

@ui.page('/reminders')
def reminders_route():
    with frame(page_title='Reminders', active_route='/reminders'):
        reminders_page()
        
@ui.page('/settings')
def settings_route():
    with frame(page_title='Settings', active_route='/settings'):
        settings_page()

# Initialize the UI server
ui.run(title="Syntria", storage_secret='your_secure_random_secrets', port=8080, host="0.0.0.0", reload=True)