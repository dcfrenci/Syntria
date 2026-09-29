import datetime
from nicegui import ui
from api_client.import_export import DataClient

class ExportModal:
    """Provides a searchable table allowing users to select specific records for bulk CSV export."""
    def __init__(self, entity_name: str):
        self.entity_name = entity_name

    async def open(self):
        rows = await DataClient.fetch_all(self.entity_name)
        if not rows:
            ui.notify(f"No {self.entity_name} found in the system to export.", type="warning")
            return

        columns = []
        
        # Helper to enforce column width and truncate overflowing text
        def _col(name, label, max_w):
            return {
                "name": name, 
                "label": label, 
                "field": name, 
                "align": "left", 
                "classes": f"truncate max-w-[{max_w}px]",
                "headerClasses": f"truncate max-w-[{max_w}px]"
            }

        # --- Define explicit schemas and data mappings per entity ---
        if self.entity_name == "quotes":
            for r in rows:
                patient = r.get("patient") or {}
                r["patient_name"] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            columns = [
                _col("id", "ID", 60),
                _col("patient_name", "Name Surname", 250),
                _col("status", "Status", 120),
                _col("total_amount", "Total Amount", 120),
            ]
        elif self.entity_name == "items":
            columns = [
                _col("id", "ID", 60),
                _col("name", "Name", 300),
                _col("price", "Price", 100),
                _col("is_specific", "Specific", 100),
                _col("is_active", "Active", 100),
            ]
        elif self.entity_name == "reservations":
            for r in rows:
                # Format date to dd/mm/yyyy HH:MM
                try:
                    dt = datetime.datetime.fromisoformat(r["reservation_date"].replace("Z", "+00:00"))
                    r["formatted_date"] = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    r["formatted_date"] = r.get("reservation_date")
                    
                # Extract Doctor Name (Reservations use 'staff' list)
                staff_list = r.get("staff", [])
                if staff_list:
                    r["doctor_name"] = ", ".join([f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() for s in staff_list])
                else:
                    r["doctor_name"] = "Unassigned"
                    
                patient = r.get("patient") or {}
                r["patient_name"] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
                
            columns = [
                _col("id", "ID", 60),
                _col("formatted_date", "Date & Time", 150),
                _col("patient_name", "Patient", 200),
                _col("doctor_name", "Doctor Name", 200),
            ]
        elif self.entity_name == "presets":
            columns = [
                _col("id", "ID", 60),
                _col("name", "Preset Name", 300),
                _col("is_active", "Active", 100),
            ]
        else:
            # Fallback for unknown entities
            keys = [k for k in rows[0].keys() if not isinstance(rows[0][k], (dict, list))]
            columns = [_col(k, k.replace("_", " ").capitalize(), 150) for k in keys[:5]]

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-6'):
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label(f"Export {self.entity_name.capitalize()}").classes("text-2xl font-bold")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense text-color=gray-500")

            ui.label("Search and select the elements you would like to export to CSV.").classes("text-gray-600 mb-4")

            table = ui.table(columns=columns, rows=rows, row_key="id", selection="multiple").classes('w-full h-[450px]')
            
            with table.add_slot("top"):
                search = ui.input(placeholder="Search elements...").classes("w-full").props("outlined dense clearable")
                search.add_slot("prepend", '<q-icon name="search" />')
                table.bind_filter_from(search, "value")

            async def do_export():
                if not table.selected:
                    ui.notify("Please select at least one item to export.", type="warning")
                    return
                ids = [r["id"] for r in table.selected]
                await DataClient.export_csv(self.entity_name, ids)
                dialog.close()

            with ui.row().classes('w-full justify-end mt-4 gap-2'):
                ui.button("Cancel", color="negative", on_click=dialog.close).props("flat")
                ui.button("Export Selected", color="primary", icon="download", on_click=do_export).classes('px-6')

        dialog.open()