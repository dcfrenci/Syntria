import base64
import json
import time
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
from pages.persons import persons_page
from pages.preset import preset_page
from pages.reminders import reminders_page
from pages.settings import settings_page


def is_token_expired(token: str | None) -> bool:
    """Decodes the JWT payload natively to check the expiration timestamp."""
    if not token:
        return True
    try:
        # The JWT payload is the second part of the string
        payload_part = token.split('.')[1]
        # Pad the base64 string to be a multiple of 4
        padded = payload_part + '=' * (-len(payload_part) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        payload = json.loads(decoded)
        
        # Check if current time has surpassed the token's expiration
        return payload.get('exp', 0) < time.time()
    except Exception:
        # If parsing fails or the token is malformed, assume it is expired
        return True

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = app.storage.user.get('token')
        
        # If marked as authenticated but the token is expired, clear the session
        if app.storage.user.get('authenticated', False) and is_token_expired(token):
            app.storage.user['authenticated'] = False
            app.storage.user['token'] = None

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
    ui.query('.nicegui-content').classes('pb-32')
        
    # Render the sidebar with the correct active hover state
    create_sidebar(active_route=active_route)
    
    def check_session():
        token = app.storage.user.get('token')
        if is_token_expired(token):
            app.storage.user['authenticated'] = False
            app.storage.user['token'] = None
            ui.notify('Your session has expired. Please log in again.', type='warning')
            ui.navigate.to('/login')
            
    ui.timer(10.0, check_session)
        
    # Create the main content container
    with ui.column().classes('w-full max-w-7xl mx-auto overflow-y-auto'):
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
        
@ui.page('/persons')
async def persons_route():
    with frame(page_title='Persons', active_route='/persons'):
        await persons_page()

@ui.page('/pricing')
async def pricing_route():
    with frame(page_title='Pricing', active_route='/pricing'):
        await pricing_page()

@ui.page('/preset')
@ui.page('/preset/create')
@ui.page('/preset/edit/{id}')
def quote_route():
    with frame(page_title='Quotes', active_route='/preset'):
        preset_page()

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