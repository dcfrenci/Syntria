from datetime import datetime

from nicegui import ui
from api_client.quotes import QuotesClient
from api_client.services import ServicesClient

def home_page():
    """Renders the Home dashboard view."""
    with ui.column().classes('p-8 w-full'):
        
        ui.sub_pages({'/home': quotes, '/home/quote_create': quote_create}).classes('w-full')
    

async def quotes():
    with ui.column().classes('w-full h-screen'):
        ui.label('Quote').classes('text-3xl font-bold mb-5')
        
        quotes = await QuotesClient.get_quotes()
        
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
                {'field': 'id', 'hide': True},
                {'headerName': 'Name', 'field': 'patient.first_name', 'sortable': True},
                {'headerName': 'Surname', 'field': 'patient.last_name', 'sortable': True, 'filter': 'agTextColumnFilter', 'floatingFilter': True},
                {'headerName': 'Date', 'field': 'created_at', 'sortable': True, 
                    ':valueFormatter': """
                        params => {
                            if (!params.value) return '';
                            const d = new Date(params.value);
                            const day = String(d.getDate()).padStart(2, '0');
                            const month = String(d.getMonth() + 1).padStart(2, '0');
                            const year = d.getFullYear();
                            return `${day}/${month}/${year}`;
                        }
                    """
                },
            ],
            'rowData': quotes,
            'rowSelection': {
                'mode': 'singleRow',
                'checkboxes': False,
                'enableClickSelection': True,
            },
        })
        
        
        with ui.row():
            ui.button('New', icon='r_add', on_click=lambda: ui.navigate.to('/home/quote_create'))
            ui.button('Edit', icon='r_edit', on_click=lambda: action(''))
            ui.button('Print', icon='r_print', on_click=lambda: action(''))
            ui.button('Download', icon='r_download', on_click=lambda: action(''))
            ui.button('Delete', icon='r_delete', on_click=lambda: action(''))
        

    
async def quote_create():
    
    with ui.column().classes('w-full'):
        
        ui.label('Dashboard New Quote').classes('text-lg font-bold mb-5')
    
        with ui.grid(columns='1fr 1fr').classes('w-full gap-10'):
        
            services = await ServicesClient.get_items()
            services_selected = {}
            
            def refresh_selected_grid():
                grid_selected.options['rowData'] = list(services_selected.values())
                grid_selected.update()
            
            async def add():
                row = await grid_services.get_selected_row()   
                if row:
                    if row['id'] in services_selected.keys():
                        services_selected[row['id']]['quantity'] += 1
                    else:
                        services_selected[row['id']] = {'id': row['id'], 'name': row['name'], 'quantity': 1, 'discount': 0, 'teeth': []}
                    refresh_selected_grid()
                else:
                    ui.notify('Select a service before')
            
            
            with ui.row().classes('w-full'):
                ui.label('Select services').classes('text-lg font-bold mb-2')
                
                grid_services = ui.aggrid({
                    'columnDefs': [
                        {'field': 'id', 'hide': True},
                        {'headerName': 'Name', 'field': 'name'},
                        {'headerName': 'Category', 'field': 'category.name'},
                    ],
                    'rowData': services,
                    'rowSelection': {
                        'mode': 'singleRow',
                        'checkboxes': False,
                        'enableClickSelection': True,
                    },
                })
                
                ui.button('Add', icon='r_add', on_click=lambda: add())
                
            async def remove():
                row = await grid_selected.get_selected_row()
                print(row, flush=True)
                if row:
                    if services_selected[row['id']]['quantity'] > 1:
                        services_selected[row['id']]['quantity'] -= 1
                    else:
                        del services_selected[row['id']]  
                    refresh_selected_grid()
                else:
                    ui.notify('Select a service before')
                
            with ui.row().classes('w-full'):
                ui.label('Selected services').classes('text-lg font-bold mb-2')
                
                grid_selected = ui.aggrid({
                    'columnDefs': [
                        {'field': 'id', 'hide': True},
                        {'headerName': 'Name', 'field': 'name'},
                        {'headerName': 'Amount', 'field': 'quantity'},
                        {'headerName': 'Teeth', 'field': 'teeth'},
                    ],
                    'rowData': list(services_selected.values()),
                    'rowSelection': {
                        'mode': 'singleRow',
                        'checkboxes': False,
                        'enableClickSelection': True,
                    },
                })
                
                ui.button('Delete', icon='r_delete', on_click=lambda: remove())
                
    with ui.card().classes('w-full p-4 border border-gray-300 rounded-lg shadow-inner'):
            ui.label('Tooth Selection').classes('text-lg font-bold mb-4')
            
            # Placeholder for the ISO 3950 / Palmer grid[cite: 6]
            with ui.row().classes('w-full justify-center items-center bg-gray-50 h-64 rounded'):
                ui.label('Interactive Dental Grid UI will render here').classes('text-gray-400')