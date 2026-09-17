from nicegui import ui
from api_client.agenda import AgendaClient
from components.style import Style

import datetime
import asyncio
from typing import List, Dict, Any

# Mocking the internal API Client based on the repo structure
# In production, this would use `from app.api_client.reservations import ...`
class MockAgendaClient:
    @staticmethod
    async def get_doctor_info() -> str:
        await asyncio.sleep(0.1) # Simulate network
        return "Doctor: Mario Rossi"

    @staticmethod
    async def get_weekly_reservations(start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.3)
        # Mocking data that matches the visual target
        return [
            {
                "id": 1,
                "start": datetime.datetime.combine(start_date, datetime.time(8, 15)),
                "end": datetime.datetime.combine(start_date, datetime.time(9, 45)),
                "patient": "Rossi Mario",
                "service": "General Checkup",
                "day_offset": 0 # Monday
            },
            {
                "id": 2,
                "start": datetime.datetime.combine(start_date, datetime.time(10, 45)),
                "end": datetime.datetime.combine(start_date, datetime.time(11, 45)),
                "patient": "Bianchi Luca",
                "service": "Follow-up",
                "day_offset": 1 # Tuesday
            },
            {
                "id": 3,
                "start": datetime.datetime.combine(start_date, datetime.time(10, 45)),
                "end": datetime.datetime.combine(start_date, datetime.time(11, 45)),
                "patient": "Verdi Giulia",
                "service": "Consultation",
                "day_offset": 2 # Wednesday
            },
            {
                "id": 4,
                "start": datetime.datetime.combine(start_date, datetime.time(12, 0)),
                "end": datetime.datetime.combine(start_date, datetime.time(13, 0)),
                "patient": "Neri Anna",
                "service": "Therapy",
                "day_offset": 2 # Wednesday
            },
            {
                "id": 5,
                "start": datetime.datetime.combine(start_date, datetime.time(9, 0)),
                "end": datetime.datetime.combine(start_date, datetime.time(10, 30)),
                "patient": "Gialli Marco",
                "service": "Checkup",
                "day_offset": 4 # Friday
            }
        ]

class AgendaState:
    def __init__(self):
        self.current_date = datetime.date.today()
        # Ensure we start on Monday of the current week
        self.week_start = self.current_date - datetime.timedelta(days=self.current_date.weekday())
        self.doctor_name = "Loading..."
        self.reservations = []
        self.loading = False

    def previous_week(self):
        self.week_start -= datetime.timedelta(days=7)
    
    def next_week(self):
        self.week_start += datetime.timedelta(days=7)

state = AgendaState()

@ui.refreshable
async def calendar_grid():
    # 1. Fetch Data
    week_end = state.week_start + datetime.timedelta(days=6)
    state.loading = True  # <-- Toggle loading ON
    
    try:
        # Show loading spinner in the grid area while fetching
        with ui.row().classes('w-full justify-center items-center h-64 absolute z-50').bind_visibility_from(state, 'loading'):
            ui.spinner('dots', size='lg', color='indigo-3')
            
        state.reservations = await MockAgendaClient.get_weekly_reservations(state.week_start, week_end)
    except Exception as e:
        ui.notify(f"Failed to load agenda: {str(e)}", type='negative')
    finally:
        state.loading = False  # <-- Toggle loading OFF when done

    # Calendar Config
    start_hour = 8
    end_hour = 14
    hour_height = 60 # px per hour
    total_height = (end_hour - start_hour) * hour_height

    with ui.column().classes('w-full max-w-7xl mx-auto mt-6 px-4 gap-0'):
        
        # Date Navigator
        with ui.row().classes('w-full justify-center items-center gap-4 mb-8 relative'):
            ui.button(icon='chevron_left', on_click=lambda: change_week(-1)).props('flat round dense')
            ui.label(f"Week of {state.week_start.day} {state.week_start.strftime('%B')} - {week_end.day} {week_end.strftime('%B')}").classes('text-lg font-semibold')
            ui.button(icon='chevron_right', on_click=lambda: change_week(1)).props('flat round dense')

        # --- Grid Header: Days of the week ---
        with ui.row().classes('w-full flex-nowrap mb-2 pl-12 pr-12'):
            for i in range(7):
                day = state.week_start + datetime.timedelta(days=i)
                is_today = day == datetime.date.today()
                
                with ui.column().classes('flex-1 items-center justify-center'):
                    day_label = ui.label(f"{day.day} - {day.strftime('%A')}").classes('text-sm font-medium px-3 py-1 rounded-md cursor-pointer transition-colors')
                    
                    # Style active/today states based on the mockup
                    if is_today:
                        day_label.classes('bg-gray-400 text-white shadow-md')
                    # Using underline as a secondary highlight (e.g. hovered/selected) as seen on "Thursday" in the mockup
                    elif i == 3: 
                        day_label.classes('underline decoration-gray-400 underline-offset-4')
        
        # --- Calendar Body ---
        with ui.row().classes('w-full flex-nowrap relative').style(f'height: {total_height}px'):
            
            # Left Time Axis
            with ui.column().classes('w-12 shrink-0 relative h-full'):
                for h in range(start_hour, end_hour + 1):
                    ui.label(f"{h}:00").classes('absolute right-2 text-xs text-black font-medium transform -translate-y-1/2').style(f"top: {(h-start_hour)*hour_height}px")
                    if h != end_hour:
                        ui.label(f"{h}:30").classes('absolute right-2 text-[10px] text-gray-500 transform -translate-y-1/2').style(f"top: {(h-start_hour)*hour_height + 30}px")

            # Grid Columns Wrapper
            with ui.row().classes('flex-1 relative h-full flex-nowrap gap-0 border-t border-gray-400'):
                
                # Draw Current Time Indicator (Blue Line)
                now = datetime.datetime.now()
                if start_hour <= now.hour < end_hour:
                    now_top = (now.hour - start_hour) * hour_height + (now.minute / 60) * hour_height
                    ui.element('div').classes('absolute w-full border-b-2 border-blue-500 z-20 pointer-events-none').style(f"top: {now_top}px")

                # Day Columns & Horizontal Grid Lines
                for day_idx in range(7):
                    with ui.column().classes('flex-1 relative h-full border-r border-gray-100 last:border-r-0'):
                        
                        # Draw horizontal lines for hours and half-hours
                        for h in range(start_hour, end_hour):
                            ui.element('div').classes('absolute w-full border-b border-gray-400').style(f"top: {(h-start_hour)*hour_height}px")
                            ui.element('div').classes('absolute w-full border-b border-gray-200').style(f"top: {(h-start_hour)*hour_height + 30}px")

                        # Plot Events
                        day_events = [e for e in state.reservations if e['day_offset'] == day_idx]
                        for event in day_events:
                            duration_mins = (event['end'] - event['start']).total_seconds() / 60
                            top_px = (event['start'].hour - start_hour) * hour_height + (event['start'].minute / 60) * hour_height
                            height_px = (duration_mins / 60) * hour_height
                            
                            with ui.card().classes(
                                'absolute w-[90%] left-[5%] bg-gray-300 rounded-lg shadow-sm border border-gray-400 p-2 flex flex-col gap-0 '
                                'cursor-pointer hover:bg-gray-400 transition-colors group'
                            ).style(f"top: {top_px}px; height: {height_px}px").on('click', lambda e=event: open_edit_modal(e)):
                                
                                ui.label(f"{event['start'].strftime('%H:%M')} - {event['end'].strftime('%H:%M')}").classes('text-[10px] font-semibold text-center w-full')
                                ui.label(event['patient']).classes('text-[10px] text-center w-full mt-1')
                                ui.label(event['service']).classes('text-[10px] text-center w-full leading-tight')
                                
                                # Pencil icon (visible on hover or always in bottom right as per mockup)
                                ui.icon('edit').classes('absolute bottom-1 right-1 text-gray-600 text-sm opacity-0 group-hover:opacity-100 transition-opacity')

            # Right Time Axis (Mirroring mockup)
            with ui.column().classes('w-12 shrink-0 relative h-full'):
                for h in range(start_hour, end_hour + 1):
                    ui.label(f"{h}:00").classes('absolute left-2 text-xs text-black font-medium transform -translate-y-1/2').style(f"top: {(h-start_hour)*hour_height}px")
                    if h != end_hour:
                        ui.label(f"{h}:30").classes('absolute left-2 text-[10px] text-gray-500 transform -translate-y-1/2').style(f"top: {(h-start_hour)*hour_height + 30}px")

def change_week(direction: int):
    if direction == 1:
        state.next_week()
    else:
        state.previous_week()
    calendar_grid.refresh()

def open_edit_modal(event_data):
    ui.notify(f"Opening edit modal for {event_data['patient']}", type='info')
    # Implement modal logic triggering `PUT /api/v1/reservations/{id}`

def open_add_modal():
    ui.notify("Opening new reservation modal", type='info')
    # Implement modal logic triggering `POST /api/v1/reservations`
    
    
class Agenda:
    def __init__(self):
        self.doctor_id = None
        self.current_date = datetime.date.today()
        self.week_shift = 0
        
    def reset(self):
        self.doctor_id = None
        self.week_shift = 0
        
    def previous_week(self):
        self.week_shift += 1
        calendar.refresh()
    
    def next_week(self):
        self.week_shift -= 1
        calendar.refresh()
        
    def set_doctor(self, doctor_id: int):
        self.doctor_id = doctor_id
        calendar.refresh()
        
    def get_week_start(self):
        return self.current_date - datetime.timedelta(days=self.current_date.weekday()) - datetime.timedelta(days=self.week_shift * 7)

    def get_week_end(self):
        return self.get_week_start() + datetime.timedelta(days=6)
    
        
agenda = Agenda()

def split_by_day(reservations: list[dict]):
    split = {}
    for reservation in reservations:
        if reservation["reservation_date"] in split.keys():
            split[reservation["reservation_date"]].add(reservation)
        else: 
            split[reservation["reservation_date"]] = [reservation]
    return split

@ui.refreshable
async def calendar():
    
    week_reservation = await AgendaClient.get_reservations_doctor_week(agenda.doctor_id, agenda.week_shift)
    
    reservation = split_by_day(reservations=week_reservation)
    # {
    #     "reservation_date": "2026-09-16T20:34:33.502Z",
    #     "duration_minutes": 30,
    #     "description": "string",
    #     "id": 0,
    #     "patient": {},
    #     "staff": {}
    # }
    
    with ui.column().classes("w-full"):
        
        # Date Navigator
        with ui.row().classes("w-full justify-center"):
            ui.button(icon='chevron_left', on_click=lambda: agenda.previous_week()).props('flat round dense')
            ui.label(f"Week of {agenda.get_week_start().day} {agenda.get_week_start().strftime('%B')} - {agenda.get_week_end().day} {agenda.get_week_end().strftime('%B')}").classes('text-lg font-semibold')
            ui.button(icon='chevron_right', on_click=lambda: agenda.next_week()).props('flat round dense')

        with ui.row().classes("w-full gap-0 justify-center"):
            start_hour = 7
            end_hour = 20
            
            # Left time axis
            with ui.column().classes('mt-12 mr-5 w-12 shrink-0 relative h-full'):
                for h in range(start_hour, end_hour + 1):
                    ui.label(f"{h}:00").classes('text-xs text-black font-medium self-end')
                    if h != end_hour:
                        ui.label(f"{h}:30").classes('text-[10px] text-gray-500 self-end')

            # Week
            for i in range(7):
                day = agenda.get_week_start() + datetime.timedelta(days=i)
                
                with ui.column().classes("w-[130px]"):
                    day_label = ui.label(f"{day.day} - {day.strftime('%A')}").classes("self-center")
                    if day == datetime.date.today():
                        day_label.classes('bg-gray-400 text-white shadow-md')
                        
                    ui.separator()
                    
                    with ui.element('div').classes('grid'):
                        
                        ui.element('div').classes('col-start-1 row-start-1 w-full h-full bg-blue-500 rounded-xl shadow-lg')
                        ui.icon('rocket', size='6rem').classes('col-start-1 row-start-1 text-white opacity-50')
    
                        # Layer 3: Text (Top)
                        ui.label('Top Layer').classes('col-start-1 row-start-1 text-3xl font-bold text-white z-10')
                    
            
            # Right time axis
            with ui.column().classes('mt-12 ml-5 w-12 shrink-0 relative h-full'):
                for h in range(start_hour, end_hour + 1):
                    ui.label(f"{h}:00").classes('text-xs text-black font-medium')
                    if h != end_hour:
                        ui.label(f"{h}:30").classes('text-[10px] text-gray-500')

    


async def agenda_page():
    # Fetch doctor info on load
    try:
        state.doctor_name = await MockAgendaClient.get_doctor_info()
    except Exception:
        state.doctor_name = "Doctor: Unknown"

    # --- Top Navigation Bar ---
    with ui.row().classes('w-full items-center justify-between p-6 max-w-7xl mx-auto'):
        ui.label('Agenda').classes('text-2xl font-bold text-black')
        ui.label(state.doctor_name).classes('bg-gray-300 px-4 py-2 rounded-lg text-black font-medium text-sm')

    # --- Main Calendar Area ---
    await calendar_grid()

    # --- Floating Action Buttons (FABs) ---
    with ui.row().classes('fixed bottom-8 right-8 gap-4 z-50'):
        ui.button(icon='notifications_none').props('fab color="indigo-3" text-color="black"').classes('shadow-lg w-14 h-14')
        ui.button(icon='add', on_click=open_add_modal).props('fab color="indigo-3" text-color="black"').classes('shadow-lg w-14 h-14 text-2xl')


    # 
    # 
    # 
    # 
    # 
    
    
    doctors = []
    agenda.reset()
    
    ui.label("Agenda").classes(Style.title())
    
    def update_agenda():
        agenda.set_doctor(doctor_id=doctor.value)
        
    
    with ui.row().classes(Style.row_end()):
        ui.label("Doctor: ").classes(Style.p_fit())
        doctor = ui.select(label="Select one...", options=doctors, on_change=update_agenda).classes(Style.p_fit())
    
           
    await calendar()