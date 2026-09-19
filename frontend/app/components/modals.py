from nicegui import ui
from datetime import datetime, timezone, timedelta

from components.style import Style

from api_client.services import ServicesClient
from api_client.persons import PersonsClient
from api_client.services import ServicesClient


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
                if name.value == '' or description.value == '' or price.value is None or category.value is None:
                    ui.notify(message="Fill out all the details before saving", type="warning")
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
                if name.value == '' or description.value == '':
                    ui.notify(message="Fill out all the details before saving", type="warning")
                    return
                category = {
                    "name": name.value,
                    "description": description.value,
                    "is_active": active.value,
                }
                await on_save_callback(category, category_id)
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


async def reservation_modal(title: str, h_start: int, h_end: int, doctor_id: int, on_save_callback, reservation_id: int | None = None):
    """Generate a dialog popup for reservation creation/editing."""
    
    raw_persons = await PersonsClient.get_persons()
    raw_services = await ServicesClient.get_items()
    raw_doctor = next((p for p in raw_persons if p["id"] == doctor_id), None)

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-3xl p-6"):
        ui.label(title).classes(Style.h1())
        
        doctor = ui.select(label="Doctor", options={p["id"]: f"{p["first_name"]} {p["last_name"]}" for p in raw_persons})
        patient = ui.select(label="Patient", options={p["id"]: f"{p["first_name"]} {p["last_name"]}" for p in raw_persons})
        date = ui.date()
        # time = ui.select(label="Time", options=[f"{t}:00" if t % 1 == 0 else f"{t - 0.5}:30" for t in range(h_start, h_end + 0.5, 0.5)])
        time = ui.select(label="Time", options=[(datetime.strptime(f"{h_start}:00", "%H:%M") + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(int((h_end - h_start) * 2) + 1)])
        service = ui.select(label="Service", options={s["id"]: s["name"] for s in raw_services})
        duration = ui.number("Duration minutes")
        description = ui.input("Description")
        
        doctor.value = raw_doctor["id"]
        
        if reservation_id:
            pass
        
        async def handle_save(value: bool):
            if value:
                if doctor.value == None or patient.value == None or date.value == None or time.value == None or service.value == None or duration.value == None or description.value == None:
                    ui.notify(message="Fill out all the details before saving", type="warning")
                    return
                
                reservation = {
                    "reservation_date": datetime.strptime(f"{date.value} {time.value}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "duration_minutes": int(duration.value),
                    "description": description.value,
                    "patient_id": patient.value,
                    "staff_ids": [doctor.value]
                }
                
                print(reservation, flush=True)
                await on_save_callback(reservation, reservation_id)
            else:
                ui.notify(message="The reservation was not saved", type="info")
            dialog.close()
        
        with ui.row().classes(Style.row_end()):
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
                        description="Confirm you want to save this reservation to your agenda.",
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
