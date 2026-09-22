from nicegui import ui
from typing import Literal, Any
from datetime import datetime, date, timedelta


class Calendar:
    def __init__(
        self,
        start_hour: int,
        end_hour: int,
        h_header: int,
        h_row: int,
        mt_row: int,
    ):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.h_header = h_header
        self.h_row = h_row
        self.mt_row = mt_row

        # Internal state
        self.is_single_day = False
        self.current_dates = []
        self.events_by_day = {}
        self.on_callback = None
        self.new_event = None

    def _split_by_day(self, reservations: list[dict] | None) -> dict:
        split = {}
        if not reservations:
            return split

        for res in reservations:
            dt = datetime.fromisoformat(res["reservation_date"].replace("Z", "+00:00"))
            res_date = dt.date()
            if res_date not in split:
                split[res_date] = []
            split[res_date].append((dt, res))
        return split

    def update_calendar(self, new_dates: list[date], new_reservations: list[dict]):
        """Updates state and only refreshes the headers and events, leaving the grid untouched."""
        self.current_dates = new_dates
        self.events_by_day = self._split_by_day(new_reservations)

        # Trigger targeted updates
        self.render_header.refresh()
        self.render_events.refresh()

    def update_new_event(self, time: str, duration: int):
        t = datetime.strptime(time, "%H:%M").time()
        self.new_event = {"hour": t.hour, "minute": t.minute, "duration": duration}
        self.render_new_event.refresh()

    @ui.refreshable
    def render_header(self, index: int):
        # Dynamically grab the date for this specific column index
        if index >= len(self.current_dates):
            return
        day = self.current_dates[index]

        with ui.element().classes("w-full items-center"):
            with ui.element().classes(
                f"h-[{self.h_header}px] flex items-center w-full justify-center"
            ):
                month_str = f"{day.strftime('%B')} " if self.is_single_day else ""
                day_label = ui.label(f"{month_str}{day.day} - {day.strftime('%A')}")

                if day == date.today() and not self.is_single_day:
                    day_label.classes(
                        "bg-gray-400 text-white shadow-md rounded px-2 py-1"
                    )

            ui.separator().classes(f"mb-{self.mt_row} border-b w-full bg-gray-500")

    @ui.refreshable
    def render_events(self, index: int):
        if index >= len(self.current_dates):
            return
        day = self.current_dates[index]

        day_reservations = self.events_by_day.get(day, [])

        for dt, res in day_reservations:
            time_offset = (dt.hour - self.start_hour) + (dt.minute / 60.0)
            start_row = int(time_offset * 2) + 1
            duration = res["duration_minutes"]
            row_span = max(1, int(duration // 30))
            end_time = dt + timedelta(minutes=duration)

            with ui.card().classes(
                "col-start-1 w-[95%] p-1 shadow-lg cursor-pointer rounded-lg justify-self-center bg-gray-300"
            ).style(
                f"grid-row: {start_row} / span {row_span}; top: {self.h_row / 2}px;"
            ) as card:
                if not self.is_single_day and self.on_callback:
                    card.on("click", lambda r=res: self.on_callback(r["id"]))

                ui.label(
                    f"{dt.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                ).classes("text-xs font-semibold text-center w-full")

                if row_span > 1:
                    ui.label(res["patient"]["last_name"]).classes(
                        "text-xs text-center w-full truncate"
                    )

                with ui.tooltip().classes("w-50 bg-transparent p-0 shadow-none"):
                    with ui.card().classes(
                        "w-[90%] bg-white border border-gray-200 shadow-xl p-3 rounded-xl justify-self-center"
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
                                f"- Name: {res['patient']['first_name']} {res['patient']['last_name']}"
                            ).classes(sty_label)
                            ui.label(f"- Description: {res['description']}").classes(
                                sty_label
                            )
                            ui.label(
                                f"- Reminder: {res['patient']['reminder_preference']['name']}"
                            ).classes(sty_label)
                            ui.label(
                                f"- Phone: {res['patient']['phone_number']}"
                            ).classes(sty_label)
                            if self.on_callback:
                                ui.label("Click to edit").classes(
                                    "text-xs text-gray-500 italic mt-2 text-center w-full"
                                )

    @ui.refreshable
    def render_new_event(self):
        if not self.new_event:
            return
        
        start_row = int((self.new_event["hour"] - self.start_hour) * 2) + 1
        row_span = max(1, int(self.new_event["duration"] // 30))

        ui.card().classes(
            "col-start-1 w-[95%] p-1 shadow-lg border rounded-lg justify-self-center bg-gray-300/50"
        ).style(f"grid-row: {start_row} / span {row_span}; top: {self.h_row / 2}px;")

    def time_column(self, width: int, align: Literal["left", "right"] = "left"):
        with ui.column().classes(f"w-[{width}px] h-full gap-0"):
            ui.element().classes(f"h-[{self.h_header}px]")
            ui.separator().classes(f"mb-{self.mt_row} border-b bg-gray-500")
            for h in range(self.start_hour, self.end_hour + 1):
                with ui.element().classes(
                    f"h-[{self.h_row}px] w-full flex items-center {'justify-end' if align == 'right' else ''}"
                ):
                    ui.label(f"{h}:00").classes(
                        f"{'mr-5' if align == 'right' else 'ml-5'} text-xs text-black font-medium"
                    )
                if h != self.end_hour:
                    with ui.element().classes(
                        f"h-[{self.h_row}px] w-full flex items-center {'justify-end' if align == 'right' else ''}"
                    ):
                        ui.label(f"{h}:30").classes(
                            f"{'mr-5' if align == 'right' else 'ml-5'} text-[10px] text-gray-500"
                        )

    def day_column(self, index: int, width: int):
        with ui.column().classes(f"gap-0 w-[{width}px] items-center"):
            # Target 1: The refreshable header
            self.render_header(index)

            total_slots = 2 * (self.end_hour - self.start_hour) + 1
            with ui.element("div").classes("grid w-full relative").style(
                f"grid-template-rows: repeat({total_slots}, {self.h_row}px);"
            ):
                # Static Time Grid - This never redraws
                for slot in range(total_slots):
                    with ui.element().classes(
                        "col-start-1 flex items-center w-full"
                    ).style(f"grid-row: {slot + 1};"):
                        ui.separator()

                # Target 2: The refreshable events
                self.render_events(index)
                self.render_new_event()

    def build(
        self,
        dates: list[date],
        time_width: int,
        day_width: int,
        on_callback: Any | None = None,
        reservations: list[dict] | None = None,
    ):
        self.current_dates = dates
        self.events_by_day = self._split_by_day(reservations)
        self.on_callback = on_callback
        self.is_single_day = len(dates) == 1

        with ui.row().classes(
            "w-full justify-center flex-nowrap gap-0 rounded-lg overflow-x-auto"
        ):
            self.time_column(width=time_width, align="right")

            # Build columns using index, not the raw date
            for i in range(len(dates)):
                self.day_column(index=i, width=day_width)

            self.time_column(width=time_width, align="left")
