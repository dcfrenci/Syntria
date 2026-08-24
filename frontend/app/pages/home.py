from nicegui import ui

def home_page():
    """Renders the Home dashboard view."""
    with ui.column().classes('p-8 w-full'):
        
        ui.sub_pages({'/home': quotes, '/home/quote_create': quote_create}).classes('w-full')
    

def quotes():
    with ui.column().classes('w-full h-screen'):
        ui.label('Quote').classes('text-3xl font-bold mb-5')
        
        async def action(page):
            row = await quotes.get_selected_row()
            if row:
                ui.notify(str(row))
                ui.notify(f"{row['Name']}, {row['Surname']}")
                ui.navigate.to(page)
            else:
                ui.notify('Select a quote before')
        
        quotes = ui.aggrid({
            'columnDefs': [
                {'headerName': 'Id', 'field': 'id', 'hide': True},
                {'headerName': 'Name', 'field': 'Name', 'sortable': True},
                {'headerName': 'Surname', 'field': 'Surname', 'sortable': True, 'filter': 'agTextColumnFilter', 'floatingFilter': True},
                {'headerName': 'Date', 'field': 'Date', 'sortable': True},
            ],
            'rowData': [
                # TODO implement
                {'Name': 'Francesco', 'Surname': 'Della Casa', 'Date': '01/01/2002'},
                {'Name': 'Matteo', 'Surname': 'Della Casa', 'Date': '03/10/2005'},
                {'Name': 'Antonella', 'Surname': 'Della Bella', 'Date': '18/02/1966'},
            ],
            'rowSelection': {
                'mode': 'singleRow',
                'checkboxes': False,
                'enableClickSelection': True,
            },
        })
        
        with ui.row():
            ui.button('New', icon='r_add', on_click=lambda: ui.navigate.to('/home/quote_create'))
            ui.button('Print', icon='r_print', on_click=lambda: action(''))
            ui.button('Download', icon='r_download', on_click=lambda: action(''))
            ui.button('Edit', icon='r_edit', on_click=lambda: action(''))
            ui.button('Delete', icon='r_delete', on_click=lambda: action(''))
        
        
    
    
    
    
def quote_create():
    
    ui.label('Dashboard New Quote').classes('w-full')
    ui.link('Go to quote', '/home')
    
    with ui.grid(columns='1fr 1fr').classes('w-full gap-10'):
        
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
        }).on('rowDobleClicked', lambda event: add(event.args["data"]), args='data')
        
        grid_selected = ui.aggrid({
            'columnDefs': [
                {'field': 'Name', 'editable': False, 'sortable': True},
                {'field': 'Price', 'editable': False, 'sortable': False},    
            ],
            'rowData': [],
        })
