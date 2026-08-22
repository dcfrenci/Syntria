from nicegui import ui

def home_page():
    """Renders the Home dashboard view."""
    with ui.column().classes('p-8 w-full'):
        
        ui.sub_pages({'/home': quotes, '/home/quote_create': quote_create}).classes('w-full')
    

def quotes():
    ui.label('Dashboard Home').classes('text-3xl font-bold mb-6 text-gray-800')
    with ui.card().classes('w-full p-6 border border-gray-200 rounded-xl shadow-none'):
        ui.label('Welcome to the Syntria Dashboard.').classes('text-lg')
        ui.label('Use the left menu to navigate through your services, agenda, and quotes.').classes('text-gray-500 mt-2')
        
    ui.link('Go to quote', '/home/quote_create')
    
    with ui.column().classes('w-full'):
        ui.label('Quote')
        
        def action(row, action):
            if row != None:
                ui.notify(str(row))
                pass
            else:
                ui.notify('Select a quote before')
        
        quotes = ui.aggrid({
            'columnDefs': [
                {'headerName': 'Name', 'field': 'Name'},
                {'headerName': 'Surname', 'field': 'Surname'},
                {'headerName': 'Date', 'field': 'Date'},
            ],
            'rowData': [
                
            ],
        })
        
        with ui.row():
            ui.button('New', icon='r_add', on_click=lambda: action(quotes.get_selected_row(), '/home/quote_create'))
        
        # .on('rowDoubleClicked', lambda event: quotes.run_grid_method())
        
        pass
    
    
    
    
def quote_create():
    
    ui.label('Dashboard New Quote').classes('w-full')
    ui.link('Go to quote', '/home')
    
    with ui.grid(columns='1fr 1fr').classes('w-full gap-20'):
        
        def add(row):
            print(row)
            grid_selected.options['rowData'].append(row)
            grid_selected.update()
            grid_selected.run_grid_method('ensureIndexVisible', len(grid_selected.options['rowData']) - 1)
        
        grid_services = ui.aggrid({
            'columnDefs': [
                {'field': 'Name', 'editable': False, 'sortable': True},
                {'field': 'Price', 'editable': False, 'sortable': False},
            ],
            'rowData': [
                # TODO Implement loading services
                {'Name': 'Service 1', 'Price': '100.5'},
                {'Name': 'Service 2', 'Price': '150.75'},
                {'Name': 'Service 3', 'Price': '300'},    
            ],
        }).on('rowClicked', lambda event: add(event.args["data"]), args='data')
        
        grid_selected = ui.aggrid({
            'columnDefs': [
                {'field': 'Name', 'editable': False, 'sortable': True},
                {'field': 'Price', 'editable': False, 'sortable': False},    
            ],
            'rowData': [],
        })
