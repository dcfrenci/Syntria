from nicegui import app, ui
from api_client.auth import authenticate

def login_page():
    if app.storage.user.get('authenticated', False):
        ui.navigate.to('/home')
        return

    with ui.card().classes('absolute-center w-80'):
        ui.label('Login').classes('text-xl font-bold mb-4')
        username_input = ui.input('Username').classes('w-full')
        password_input = ui.input('Password', password=True, password_toggle_button=True).classes('w-full')

        async def try_login():
            result = await authenticate(username_input.value, password_input.value)
            if result:
                app.storage.user['authenticated'] = True
                app.storage.user['token'] = result.get('access_token')
                ui.navigate.to('/home')
            else:
                ui.notify('Invalid username or password', color='negative')

        ui.button('Sign In', on_click=try_login).classes('w-full mt-4')