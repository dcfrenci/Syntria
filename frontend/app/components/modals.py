from nicegui import ui
from datetime import datetime, timezone, timedelta, date

from components.style import Style

from api_client.services import ServicesClient
from api_client.persons import PersonsClient
from api_client.services import ServicesClient
from api_client.agenda import AgendaClient

from components.calendar import time_column, day_column


async def service_modal(title: str, on_save_callback, item_id: int | None = None):
    """Generate a dialog popup for service creation/editing."""

    categories = await ServicesClient.get_categories()

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-3xl p-6"):
        ui.label(title).classes(Style.h1())

        category = ui.select(
            options={category["id"]: category["name"] for category in categories}
        ).classes(Style.p())
        name = ui.input("Name").classes(Style.p())
        description = ui.input("Description").classes(Style.p())
        price = ui.number("Price", format="%.2f").classes(Style.p())
        specific = ui.checkbox("Specific").classes(Style.p())
        active = ui.checkbox("Active").classes(Style.p())

        if item_id:
            item = await ServicesClient.get_item_with_id(item_id=item_id)
            category.value = item["category"]["id"]
            name.value = item["name"]
            description.value = item["description"]
            price.value = item["price"]
            specific.value = item["is_specific"]
            active.value = item["is_active"]

        async def handle_save(value: bool):
            if value:
                if (
                    name.value == ""
                    or description.value == ""
                    or price.value is None
                    or category.value is None
                ):
                    ui.notify(
                        message="Fill out all the details before saving", type="warning"
                    )
                    return
                item = {
                    "name": name.value,
                    "description": description.value,
                    "price": price.value,
                    "category_id": category.value,
                    "is_active": active.value,
                    "is_specific": specific.value,
                }
                await on_save_callback(item, item_id)
                ui.notify(message="The service was saved successfully", type="positive")
            else:
                ui.notify(message="The service was not saved", type="info")
            dialog.close()

        with ui.row().classes(Style.row_end()):
            ui.button(
                "Cancel",
                on_click=lambda: [
                    dialog.close(),
                    ui.notify(message="The service was not saved", type="info"),
                ],
            ).props("outline")
            ui.button(
                "Save",
                on_click=lambda: [
                    confirmation_modal(
                        title="Save Service?",
                        description="Confirm you want to save this service to your catalog.",
                        on_save_callback=handle_save,
                    ).open()
                ],
            )

    return dialog


async def category_modal(title: str, on_save_callback, category_id: int | None = None):
    """Generate a dialog popup for category creation/editing."""

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-3xl p-6"):
        ui.label(title).classes(Style.h1())

        name = ui.input("Name").classes(Style.p())
        description = ui.input("Description").classes(Style.p())
        active = ui.checkbox("Active").classes(Style.p())

        if category_id:
            category = await ServicesClient.get_category_with_id(
                category_id=category_id
            )
            name.value = category["name"]
            description.value = category["description"]
            active.value = category["is_active"]

        async def handle_save(value: bool):
            if value:
                if name.value == "" or description.value == "":
                    ui.notify(
                        message="Fill out all the details before saving", type="warning"
                    )
                    return
                category = {
                    "name": name.value,
                    "description": description.value,
                    "is_active": active.value,
                }
                await on_save_callback(category, category_id)
                ui.notify(
                    message="The category was saved successfully", type="positive"
                )
            else:
                ui.notify(message="The category was not saved", type="info")
            dialog.close()

        with ui.row().classes(Style.row_end()):
            ui.button(
                "Cancel",
                on_click=lambda: [
                    dialog.close(),
                    ui.notify(message="The category was not saved", type="info"),
                ],
            ).props("outline")
            ui.button(
                "Save",
                on_click=lambda: [
                    confirmation_modal(
                        title="Save Category?",
                        description="Confirm you want to save this category to your catalog.",
                        on_save_callback=handle_save,
                    ).open()
                ],
            )

    return dialog


async def reservation_modal(
    title: str,
    h_start: int,
    h_end: int,
    on_save_callback,
    on_delete_callback,
    doctor_id: int | None = None,
    reservation_id: int | None = None,
):
    """Generate a dialog popup for reservation creation/editing."""

    @ui.refreshable
    async def calendar():
        if doctor.value is None or date_sel.value == "":
            ui.label("Please select a doctor and a date to view their agenda.").classes(
                "text-gray-500 italic mt-10 text-center w-full"
            )
            return

        week_reservation = await AgendaClient.get_reservations_doctor_week(
            doctor_id=doctor.value, start_date=date_sel.value
        )
        target_date = datetime.strptime(date_sel.value, "%Y-%m-%d").date()
        day_reservations = [
            r
            for r in week_reservation
            if datetime.fromisoformat(r["reservation_date"]).date() == target_date
        ]
        h_header = 40
        h_row = 20
        mt_row = 1
        time_column(
            width=40,
            start_hour=h_start,
            end_hour=h_end,
            h_header=h_header,
            h_row=h_row,
            mt_row=mt_row,
            align="right",
        )
        day_column(
            day=target_date,
            reservations=day_reservations,
            width=200,
            start_hour=h_start,
            end_hour=h_end,
            h_header=h_header,
            h_row=h_row,
            mt_row=mt_row,
            single=True,
        )
        time_column(
            width=40,
            start_hour=h_start,
            end_hour=h_end,
            h_header=h_header,
            h_row=h_row,
            mt_row=mt_row,
            align="left",
        )

    raw_persons = await PersonsClient.get_persons()
    raw_services = await ServicesClient.get_items()

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-5xl p-6"):
        ui.label(title).classes(Style.h1())

        with ui.row().classes("w-full gap-5 justify-center items-stretch"):
            # Reservation detail
            with ui.column().classes("w-[30%]"):
                doctor = ui.select(
                    label="Doctor",
                    options={
                        p["id"]: f"{p["first_name"]} {p["last_name"]}"
                        for p in raw_persons
                    },
                    on_change=calendar.refresh,
                ).classes(Style.p())
                patient = ui.select(
                    label="Patient",
                    options={
                        p["id"]: f"{p["first_name"]} {p["last_name"]}"
                        for p in raw_persons
                    },
                ).classes(Style.p())
                date_sel = ui.date_input("Date", on_change=calendar.refresh).classes(
                    Style.p()
                )
                time = ui.select(
                    label="Time",
                    options=[
                        (
                            datetime.strptime(f"{h_start}:00", "%H:%M")
                            + timedelta(minutes=30 * i)
                        ).strftime("%H:%M")
                        for i in range(int((h_end - h_start) * 2) + 1)
                    ],
                ).classes(Style.p())
                service = ui.select(
                    label="Service", options={s["id"]: s["name"] for s in raw_services}
                ).classes(Style.p())
                duration = ui.number("Duration minutes").classes(Style.p())
                description = ui.input("Description").classes(Style.p())

            # Calendar view
            with ui.row().classes("w-[60%] gap-0 justify-center"):
                await calendar()

        if doctor_id:
            raw_doctor = next((p for p in raw_persons if p["id"] == doctor_id), None)
            doctor.value = raw_doctor["id"]

        if reservation_id:
            reservation = await AgendaClient.get_reservation_with_id(reservation_id)
            patient.value = reservation["patient"]["id"]
            date_sel.value = datetime.fromisoformat(
                reservation["reservation_date"]
            ).strftime("%Y-%m-%d")
            time.value = datetime.fromisoformat(
                reservation["reservation_date"]
            ).strftime("%H:%M")
            # service.value = reservation["item"]["id"]
            duration.value = reservation["duration_minutes"]
            description.value = reservation["description"]

        async def handle_delete(value: bool):
            if value:
                await on_delete_callback(reservation_id)
                ui.notify(
                    message="The reservation was deleted successfully", type="positive"
                )
            else:
                ui.notify(message="The reservation was not changed", type="info")
            dialog.close()

        async def handle_save(value: bool):
            if value:
                if (
                    doctor.value == None
                    or patient.value == None
                    or date_sel.value == ""
                    or time.value == None
                    or service.value == None
                    or duration.value == None
                    or description.value == None
                ):
                    ui.notify(
                        message="Fill out all the details before saving", type="warning"
                    )
                    return

                reservation = {
                    "reservation_date": datetime.strptime(
                        f"{date_sel.value} {time.value}", "%Y-%m-%d %H:%M"
                    )
                    .replace(tzinfo=timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "duration_minutes": int(duration.value),
                    "description": description.value,
                    "patient_id": patient.value,
                    "staff_ids": [doctor.value],
                }

                await on_save_callback(reservation, reservation_id)
                ui.notify(
                    message="The reservation was saved successfully", type="positive"
                )
            else:
                ui.notify(message="The reservation was not saved", type="info")
            dialog.close()

        with ui.row().classes(Style.row_end()):
            ui.button(
                "Delete",
                on_click=lambda: [
                    confirmation_modal(
                        title="Delete Reservation?",
                        description="Confirm you want to delete this reservation from the agenda.",
                        on_save_callback=handle_delete,
                    ).open()
                ],
            )
            ui.button(
                "Cancel",
                on_click=lambda: [
                    dialog.close(),
                    ui.notify(message="The reservation was not saved", type="info"),
                ],
            ).props("outline")
            ui.button(
                "Save",
                on_click=lambda: [
                    confirmation_modal(
                        title="Save Reservation?",
                        description="Confirm you want to save this reservation to the agenda.",
                        on_save_callback=handle_save,
                    ).open()
                ],
            )

    return dialog


def confirmation_modal(title: str, description: str, on_save_callback):
    """Generates a customizable confirmation modal popup."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md p-6"):
        ui.label(title).classes(Style.h1())

        ui.label(description).classes(Style.p())

        async def handle_cancel():
            await on_save_callback(False)
            dialog.close()

        async def handle_confirm():
            await on_save_callback(True)
            dialog.close()

        with ui.row().classes(Style.row_end()):
            ui.button("Cancel", on_click=handle_cancel).props("outline")
            ui.button("Confirm", on_click=handle_confirm)

    return dialog
