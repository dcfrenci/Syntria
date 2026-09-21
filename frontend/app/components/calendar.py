from nicegui import ui

from typing import Literal, Any
from datetime import datetime, date, timedelta


def time_column(
    width: int,
    start_hour: int,
    end_hour: int,
    h_header: int,
    h_row: int,
    mt_row: int,
    align: Literal["left", "right"] = "left",
):
    if align not in ("left", "right"):
        raise ValueError(
            f"Invalid align option: '{align}'. Expected 'left' or 'right'."
        )

    with ui.column().classes(f"w-[{width}px] h-full gap-0"):
        ui.element().classes(f"h-[{h_header}px]")
        ui.separator().classes(f"mb-{mt_row} border-b bg-gray-500")
        for h in range(start_hour, end_hour + 1):
            with ui.element().classes(
                f"h-[{h_row}px] w-full flex items-center {"justify-end" if align == "right" else ""}"
            ):
                ui.label(f"{h}:00").classes(
                    f"{"mr-5" if align == "right" else "ml-5"} text-xs text-black font-medium"
                )
            if h != end_hour:
                with ui.element().classes(
                    f"h-[{h_row}px] w-full flex items-center {"justify-end" if align == "right" else ""}"
                ):
                    ui.label(f"{h}:30").classes(
                        f"{"mr-5" if align == "right" else "ml-5"} text-[10px] text-gray-500"
                    )


def day_column(
    day: date,
    reservations: list,
    width: int,
    start_hour: int,
    end_hour: int,
    h_header: int,
    h_row: int,
    mt_row: int,
    single: bool,
    on_callback: Any | None = None,
):
    with ui.column().classes(f"gap-0 w-[{width}px] items-center"):
        # Day title
        with ui.element().classes(f"h-[{h_header}px]"):
            day_label = ui.label(
                f"{day.strftime('%B') if single else ''} {day.day} - {day.strftime('%A')}"
            )
            if day == date.today() and not single:
                day_label.classes("bg-gray-400 text-white shadow-md")
        ui.separator().classes(f"mb-{mt_row} border-b bg-gray-500")

        total_slots = 2 * (end_hour - start_hour) + 1
        with ui.element("div").classes("grid w-full relative").style(
            f"grid-template-rows: repeat({total_slots}, {h_row}px);"
        ):

            # Time grid
            for slot in range(total_slots):
                with ui.element().classes("col-start-1 flex items-center w-full").style(
                    f"grid-row: {slot + 1};"
                ):
                    ui.separator()

            # Events
            for event in reservations:
                dt = datetime.fromisoformat(
                    event["reservation_date"].replace("Z", "+00:00")
                )

                time_offset = (dt.hour - start_hour) + (dt.minute / 60.0)
                start_row = int(time_offset * 2) + 1
                duration = event["duration_minutes"]
                row_span = max(1, int(duration // 30))
                end_time = dt + timedelta(minutes=duration)

                with ui.card().classes(
                    "col-start-1 w-[95%] p-1 shadow-lg cursor-pointer rounded-lg justify-center bg-gray-300"
                ).style(
                    f"grid-row: {start_row} / span {row_span}; top: {h_row / 2}px;"
                ) as card:
                    if not single:
                        card.on("click", lambda: on_callback(event["id"]))

                    ui.label(
                        f"{dt.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                    ).classes("text-xs font-semibold text-center w-full")
                    if row_span > 1:
                        ui.label(event["patient"]["last_name"]).classes(
                            "text-xs text-center w-full truncate"
                        )

                    with ui.tooltip().classes("w-50 bg-transparent p-0 shadow-none"):
                        with ui.card().classes(
                            "w-[90%] bg-white border border-gray-200 shadow-xl p-3 rounded-xl"
                        ):
                            with ui.column().classes("gap-0"):
                                ui.label("Reservation details").classes(
                                    "mb-1 font-bold text-center text-sm text-gray-800"
                                )
                                sty_label = (
                                    "ml-1 max-w-40 truncate text-sm text-gray-600"
                                )
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
