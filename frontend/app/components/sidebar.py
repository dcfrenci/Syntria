from nicegui import ui

def create_sidebar(active_route: str = '/'):
    """Generates the navigation drawer with hover and active states."""
    with ui.left_drawer(value=True, fixed=True).classes('bg-gray-200 p-4 w-64 rounded-tr-3xl rounded-br-3xl'):
        
        with ui.row().classes('items-center mb-8 gap-4 px-2'):
            ui.icon('menu', size='sm')
            ui.label('Menù').classes('text-2xl font-bold')
            
        def menu_item(icon: str, text: str, route: str):
            # Apply darker background if active, otherwise apply hover effects[cite: 7]
            is_active = route == active_route
            
            
            base_classes = 'menu-btn w-full justify-start py-3 px-4 rounded-xl text-lg text-black bg-transparent shadow-none'
            if is_active:
                base_classes += ' menu-btn-active'
            
            # If you are using custom SVGs instead of Material icons, 
            # you would use an Image component rather than an Icon component here.
            with ui.button(on_click=lambda: ui.navigate.to(route)).classes(base_classes).props('flat'):
                with ui.row().classes('items-center gap-4'):
                    # Example using Material icons (change to ui.image('/assets/icons/home.svg') for custom ones)
                    ui.icon(icon, size='sm') 
                    ui.label(text)
            
        with ui.column().classes('w-full gap-2'):
            menu_item('r_home', 'Home', '/home')
            menu_item('r_menu_book', 'Agenda', '/agenda')
            menu_item('r_attach_money', 'Pricing', '/pricing')
            menu_item('r_edit', 'Customize quote', '/quote')
            menu_item('r_settings', 'Setting', '/settings')