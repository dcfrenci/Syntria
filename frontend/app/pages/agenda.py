from nicegui import ui
import datetime
from api_client.agenda import AgendaClient
from api_client.persons import PersonsClient
from components.style import Style
from components.modals import reservation_modal


class Agenda:
    def __init__(self):
        self.doctor_id = None
        self.current_date = datetime.date.today()
        self.week_shift = 0

    def reset(self):
        self.doctor_id = None
        self.week_shift = 0

    def previous_week(self):
        self.week_shift -= 1
        calendar.refresh()

    def next_week(self):
        self.week_shift += 1
        calendar.refresh()

    def set_doctor(self, doctor_id: int):
        self.doctor_id = doctor_id
        self.week_shift = 0
        calendar.refresh()

    def get_week_start(self):
        return (
            self.current_date
            - datetime.timedelta(days=self.current_date.weekday())
            + datetime.timedelta(days=self.week_shift * 7)
        )

    def get_week_end(self):
        return self.get_week_start() + datetime.timedelta(days=6)


agenda = Agenda()
START_HOUR = 7
END_HOUR = 20


def split_by_day(reservations: list[dict]):
    split = {}
    for res in reservations:
        dt = datetime.datetime.fromisoformat(
            res["reservation_date"].replace("Z", "+00:00")
        )
        res_date = dt.date()

        if res_date not in split:
            split[res_date] = []
        split[res_date].append(res)
    return split


async def save_reservation(reservation: dict, id: int | None = None):
    if id is None:
        await AgendaClient.create_reservation(data=reservation)
    else:
        await AgendaClient.update_reservation(reservation_id=id, data=reservation)
    calendar.refresh()


async def delete_reservation(reservation_id: int):
    await AgendaClient.delete_reservation(reservation_id=reservation_id)
    calendar.refresh()


async def new_reservation():
    modal = await reservation_modal(
        title="New Reservation",
        h_start=START_HOUR,
        h_end=END_HOUR,
        doctor_id=agenda.doctor_id,
        on_save_callback=save_reservation,
        on_delete_callback=delete_reservation
    )
    modal.open()


async def edit_reservation(reservation_id: int):
    modal = await reservation_modal(
        title="Edit Reservation",
        h_start=START_HOUR,
        h_end=END_HOUR,
        doctor_id=agenda.doctor_id,
        on_save_callback=save_reservation,
        on_delete_callback=delete_reservation,
        reservation_id=reservation_id,
    )
    modal.open()


@ui.refreshable
async def calendar():

    if not agenda.doctor_id:
        ui.label("Please select a doctor to view their agenda.").classes(
            "text-gray-500 italic mt-10 text-center w-full"
        )
        return

    week_reservation = await AgendaClient.get_reservations_doctor_week(
        agenda.doctor_id, agenda.get_week_start().isoformat()
    )

    reservation = split_by_day(reservations=week_reservation)

    with ui.column().classes("w-full"):

        # Date Navigator
        with ui.row().classes("w-full justify-center"):
            ui.button(
                icon="chevron_left", on_click=lambda: agenda.previous_week()
            ).props("flat round dense")
            with ui.element().classes("w-[320px]"):
                ui.label(
                    f"Week of {agenda.get_week_start().day} {agenda.get_week_start().strftime('%B')} - {agenda.get_week_end().day} {agenda.get_week_end().strftime('%B')}"
                ).classes("text-center text-lg font-semibold")
            ui.button(icon="chevron_right", on_click=lambda: agenda.next_week()).props(
                "flat round dense"
            )

        with ui.row().classes("w-full gap-0 justify-center"):
            start_hour = START_HOUR
            end_hour = END_HOUR

            h_header = 40
            mt_hours = 3
            h_hours = 35

            # Left time axis
            with ui.column().classes("w-15 h-full gap-0"):
                ui.element().classes(f"h-[{h_header}px]")
                ui.separator().classes(f"mb-{mt_hours} border-b bg-gray-500")
                for h in range(start_hour, end_hour + 1):
                    with ui.element().classes(
                        f"h-[{h_hours}px] w-full flex items-center justify-end"
                    ):
                        ui.label(f"{h}:00").classes(
                            "mr-5 text-xs text-black font-medium"
                        )
                    if h != end_hour:
                        with ui.element().classes(
                            f"h-[{h_hours}px] w-full flex items-center justify-end"
                        ):
                            ui.label(f"{h}:30").classes(
                                "mr-5 text-[10px] text-gray-500"
                            )

            # Week
            for i in range(7):
                day = agenda.get_week_start() + datetime.timedelta(days=i)

                with ui.column().classes("gap-0 w-[130px] items-center"):
                    # Day title
                    with ui.element().classes(f"h-[{h_header}px]"):
                        day_label = ui.label(f"{day.day} - {day.strftime('%A')}")
                        if day == datetime.date.today():
                            day_label.classes("bg-gray-400 text-white shadow-md")
                    ui.separator().classes(f"mb-{mt_hours} border-b bg-gray-500")

                    total_slots = 2 * (end_hour - start_hour) + 1
                    with ui.element("div").classes("grid w-full relative").style(
                        f"grid-template-rows: repeat({total_slots}, {h_hours}px);"
                    ):

                        # Time grid
                        for slot in range(total_slots):
                            with ui.element().classes(
                                "col-start-1 flex items-center w-full"
                            ).style(f"grid-row: {slot + 1};"):
                                ui.separator()

                        # Events
                        for event in reservation.get(day, []):
                            dt = datetime.datetime.fromisoformat(
                                event["reservation_date"].replace("Z", "+00:00")
                            )

                            time_offset = (dt.hour - start_hour) + (dt.minute / 60.0)
                            start_row = int(time_offset * 2) + 1
                            duration = event["duration_minutes"]
                            row_span = max(1, int(duration // 30))
                            end_time = dt + datetime.timedelta(minutes=duration)

                            with ui.card().classes(
                                "col-start-1 w-[95%] p-1 shadow-lg cursor-pointer rounded-lg justify-center bg-gray-300"
                            ).style(
                                f"grid-row: {start_row} / span {row_span}; top: {h_hours / 2}px;"
                            ) as card:
                                card.on("click", lambda: edit_reservation(event["id"]))

                                ui.label(
                                    f"{dt.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                                ).classes("text-xs font-semibold text-center w-full")
                                if row_span > 1:
                                    ui.label(event["patient"]["last_name"]).classes(
                                        "text-xs text-center w-full truncate"
                                    )

                                with ui.tooltip().classes(
                                    "w-50 bg-transparent p-0 shadow-none"
                                ):
                                    with ui.card().classes(
                                        "w-[90%] bg-white border border-gray-200 shadow-xl p-3 rounded-xl"
                                    ):
                                        with ui.column().classes("gap-0"):
                                            ui.label("Reservation details").classes(
                                                "mb-1 font-bold text-center text-sm text-gray-800"
                                            )
                                            sty_label = "ml-1 max-w-40 truncate text-sm text-gray-600"
                                            ui.label(
                                                f"- Time: {dt.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                                            ).classes(sty_label)
                                            ui.label(
                                                f"- Name: {event["patient"]["first_name"]} {event["patient"]["last_name"]}"
                                            ).classes(sty_label)
                                            ui.label(
                                                f"- Description: {event["description"]}"
                                            ).classes(sty_label)
                                            ui.label(
                                                f"- Reminder: {event["patient"]["reminder_preference"]["name"]}"
                                            ).classes(sty_label)
                                            ui.label(
                                                f"- Phone: {event["patient"]["phone_number"]}"
                                            ).classes(sty_label)
                                            ui.label("Cliclk to edit").classes(
                                                "text-xs text-gray-500 italic mt-2 text-center w-full"
                                            )

            # Right time axis
            with ui.column().classes("w-15 h-full gap-0"):
                ui.element().classes(f"h-[{h_header}px]")
                ui.separator().classes(f"mb-{mt_hours} border-b bg-gray-500")
                for h in range(start_hour, end_hour + 1):
                    with ui.element().classes(
                        f"h-[{h_hours}px] w-full flex items-center"
                    ):
                        ui.label(f"{h}:00").classes(
                            "ml-5 text-xs text-black font-medium"
                        )
                    if h != end_hour:
                        with ui.element().classes(
                            f"h-[{h_hours}px] w-full flex items-center"
                        ):
                            ui.label(f"{h}:30").classes(
                                "ml-5 text-[10px] text-gray-500"
                            )


async def agenda_page():

    persons = await PersonsClient.get_persons()
    doctors = {p["id"]: f"{p["first_name"]} {p["last_name"]}" for p in persons}
    agenda.reset()

    ui.label("Agenda").classes(Style.title())

    # Doctor selection
    with ui.row().classes(Style.row_center()):

        def update_agenda():
            agenda.set_doctor(doctor_id=doctor.value)

        doctor = ui.select(
            label="Select doctor", options=doctors, on_change=update_agenda
        ).classes(f"max-w-1/3 {Style.p()}")

    await calendar()

    # Floating buttons
    with ui.row().classes("fixed bottom-8 right-8 gap-4 z-50"):

        ui.button(icon="notifications_none")
        ui.button(icon="add", on_click=new_reservation)
