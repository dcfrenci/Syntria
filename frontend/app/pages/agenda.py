from nicegui import ui
import datetime
from api_client.agenda import AgendaClient
from api_client.persons import PersonsClient
from components.style import Style
from components.calendar import Calendar
from components.modals import reservation_modal


class Agenda:
    def __init__(self, calendar_instance):
        self.calendar = calendar_instance
        self.doctor_id = None
        self.current_date = datetime.date.today()
        self.week_shift = 0

    # async def reset(self):
    #     self.doctor_id = None
    #     self.week_shift = 0
    #     await self._update_ui()

    def get_week_start(self):
        return (
            self.current_date
            - datetime.timedelta(days=self.current_date.weekday())
            + datetime.timedelta(days=self.week_shift * 7)
        )

    def get_week_end(self):
        return self.get_week_start() + datetime.timedelta(days=6)

    def get_current_week_dates(self):
        start = self.get_week_start()
        return [start + datetime.timedelta(days=i) for i in range(7)]

    async def _update_ui(self):
        # 1. Fetch new data using the async API call
        if self.doctor_id:
            new_reservations = await AgendaClient.get_reservations_doctor_week(
                self.doctor_id, self.get_week_start().isoformat()
            )
        else:
            new_reservations = []

        # 2. Update the Calendar component (refreshes headers and events, ignores static grid)
        self.calendar.update_calendar(
            new_dates=self.get_current_week_dates(), new_reservations=new_reservations
        )

        # 3. Refresh the Date Navigator component below
        self.date_navigator.refresh()

    async def previous_week(self):
        self.week_shift -= 1
        await self._update_ui()

    async def next_week(self):
        self.week_shift += 1
        await self._update_ui()

    async def set_doctor(self, doctor_id: int):
        self.doctor_id = doctor_id
        self.week_shift = 0
        await self._update_ui()

    @ui.refreshable
    def date_navigator(self):
        with ui.row().classes("w-full justify-center items-center mb-4"):
            ui.button(icon="chevron_left", on_click=self.previous_week).props(
                "flat round dense"
            )

            with ui.element().classes("w-[320px]"):
                start = self.get_week_start()
                end = self.get_week_end()
                ui.label(
                    f"Week of {start.day} {start.strftime('%B')} - {end.day} {end.strftime('%B')}"
                ).classes("text-center text-lg font-semibold w-full block")

            ui.button(icon="chevron_right", on_click=self.next_week).props(
                "flat round dense"
            )


START_HOUR = 7
END_HOUR = 20
my_calendar = Calendar(
        start_hour=START_HOUR, end_hour=END_HOUR, h_header=40, h_row=35, mt_row=5
    )
my_agenda = Agenda(calendar_instance=my_calendar)


async def save_reservation(reservation: dict, id: int | None = None):
    if id is None:
        await AgendaClient.create_reservation(data=reservation)
    else:
        await AgendaClient.update_reservation(reservation_id=id, data=reservation)
    await my_agenda._update_ui()


async def delete_reservation(reservation_id: int):
    await AgendaClient.delete_reservation(reservation_id=reservation_id)
    await my_agenda._update_ui()


async def new_reservation():
    modal = await reservation_modal(
        title="New Reservation",
        h_start=START_HOUR,
        h_end=END_HOUR,
        doctor_id=my_agenda.doctor_id,
        on_save_callback=save_reservation,
        on_delete_callback=delete_reservation,
    )
    modal.open()


async def edit_reservation(reservation_id: int):
    modal = await reservation_modal(
        title="Edit Reservation",
        h_start=START_HOUR,
        h_end=END_HOUR,
        doctor_id=my_agenda.doctor_id,
        on_save_callback=save_reservation,
        on_delete_callback=delete_reservation,
        reservation_id=reservation_id,
    )
    modal.open()


async def agenda_page():

    persons = await PersonsClient.get_persons()
    doctors = {p["id"]: f"{p["first_name"]} {p["last_name"]}" for p in persons}

    ui.label("Agenda").classes(Style.title())

    # Doctor selection
    with ui.row().classes(Style.row_center()):

        async def update_agenda():
            await my_agenda.set_doctor(doctor_id=doctor.value)

        doctor = ui.select(
            label="Select doctor", options=doctors, on_change=update_agenda
        ).classes(f"max-w-1/3 {Style.p()}")

    with ui.column().classes("w-full"):
        my_agenda.date_navigator()
        
        my_calendar.build(
            dates=my_agenda.get_current_week_dates(),
            on_callback=edit_reservation,
            time_width=50,
            day_width=130,
            reservations=[]
        )

    # Floating buttons
    with ui.row().classes("fixed bottom-8 right-8 gap-4 z-50"):

        ui.button(icon="notifications_none")
        ui.button(icon="add", on_click=new_reservation)
