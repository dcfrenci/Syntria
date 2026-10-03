from nicegui import app, ui

def create_sidebar(active_route: str = '/'):
    """Generates the navigation drawer with hover and active states."""
    with ui.left_drawer(value=True, fixed=True).classes('bg-gray-200 p-4 w-64 rounded-tr-3xl rounded-br-3xl'):
        
        with ui.row().classes('items-center py-6 gap-4 px-2'):
            ui.icon('menu', size='md')
            ui.label('Menu').classes('text-3xl font-bold')
            
        def menu_item(icon: str, text: str, route: str):
            # Apply darker background if active, otherwise apply hover effects
            is_active = route == active_route
            
            
            base_classes = 'menu-btn w-full justify-start py-3 px-4 rounded-xl text-lg text-black bg-transparent shadow-none'
            if is_active:
                base_classes += ' menu-btn-active'
            
            with ui.button(on_click=lambda: ui.navigate.to(route)).classes(base_classes).props('flat align=left'):
                with ui.row().classes('items-center gap-4'):
                    ui.icon(icon, size='sm') 
                    ui.label(text)
            
        with ui.column().classes('w-full gap-2'):
            menu_item('r_home', 'Home', '/home')
            menu_item('r_menu_book', 'Agenda', '/agenda')
            menu_item('r_person', 'Persons', '/persons')
            menu_item('r_attach_money', 'Pricing', '/pricing')
            menu_item('r_edit', 'Customize quote', '/preset')
            menu_item('r_settings', 'Setting', '/settings')
            
        ui.space()

        def perform_logout():
            app.storage.user['authenticated'] = False
            app.storage.user['token'] = None
            ui.navigate.to('/login')
            
        # 3. Add the logout button
        ui.button('Logout', icon='logout', color='negative', on_click=perform_logout).classes('mb-4 self-center')