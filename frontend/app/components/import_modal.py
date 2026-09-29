import inspect
from nicegui import ui
from api_client.import_export import DataClient

class ImportModal:
    """Uploads a CSV for backend validation and allows users to resolve conflicts before committing."""
    def __init__(self, entity_name: str):
        self.entity_name = entity_name
        self.validation_results = []

    async def open(self):
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-6xl p-6'):
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label(f"Import {self.entity_name.capitalize()}").classes("text-2xl font-bold")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense text-color=gray-500")

            ui.label("1. Upload your CSV file to validate data and review potential conflicts.").classes("text-gray-600 mb-2")
            
            table_container = ui.column().classes('w-full mt-4')

            async def handle_upload(e):
                # Safely locate the file-like object regardless of NiceGUI version
                file_like = None
                if hasattr(e, 'content') and hasattr(e.content, 'read'):
                    file_like = e.content
                elif hasattr(e, 'file') and hasattr(e.file, 'read'):
                    file_like = e.file
                else:
                    file_like = next((getattr(e, a) for a in dir(e) if hasattr(getattr(e, a), 'read')), None)
                
                if not file_like:
                    ui.notify("Upload failed: Could not read file payload.", type='negative')
                    return
                
                # Safely read bytes (handling both async and sync read methods)
                content_or_coro = file_like.read()
                file_bytes = await content_or_coro if inspect.isawaitable(content_or_coro) else content_or_coro

                self.validation_results = await DataClient.validate_import(self.entity_name, file_bytes)
                render_table()
            
            ui.upload(on_upload=handle_upload, auto_upload=True).classes('w-full').props('accept=".csv" flat bordered')

            def render_table():
                table_container.clear()
                with table_container:
                    ui.label("2. Review Validation Results").classes("text-lg font-bold mt-6 mb-2")
                    
                    with ui.row().classes('w-full font-bold border-b border-gray-300 pb-2 mb-2 text-sm text-gray-700'):
                        ui.label("Import ID").classes('w-20')
                        ui.label("Status").classes('w-24')
                        ui.label("Action").classes('w-56')
                        ui.label("Diagnostic Details").classes('flex-1')

                    with ui.scroll_area().classes('w-full h-[400px] border border-gray-200 rounded-md bg-gray-50'):
                        for r in self.validation_results:
                            with ui.row().classes('w-full items-center border-b border-gray-200 p-3 text-sm bg-white hover:bg-gray-50'):
                                ui.label(str(r.get("row_id", "N/A"))).classes('w-20 text-gray-600 font-mono')
                                
                                status = r["status"]
                                color = "text-red-600" if status == "error" else "text-orange-600" if status == "conflict" else "text-green-600"
                                ui.label(status.upper()).classes(f'w-24 font-bold {color}')

                                # Map the correct action selector based on the conflict status
                                if status == "conflict":
                                    r["selected_action"] = "keep"
                                    ui.select(
                                        {"keep": "Keep Existing", "update": "Update Existing", "new": "Create New Version"}, 
                                        value="keep", 
                                        on_change=lambda e, row=r: row.update({"selected_action": e.value})
                                    ).classes('w-56').props('dense outlined bg-white')
                                elif status == "ok":
                                    r["selected_action"] = "new"
                                    ui.label("Will Append to DB").classes('w-56 text-gray-500 italic')
                                else:
                                    r["selected_action"] = "ignore"
                                    ui.label("Cannot Import").classes('w-56 text-red-500 italic')

                                err_text = ", ".join(r.get("errors", [])) or "Clean. No relational errors found."
                                ui.label(err_text).classes(f"flex-1 {'text-red-500 font-medium' if r.get('errors') else 'text-gray-500'}")

                    async def do_commit():
                        success = await DataClient.commit_import(self.entity_name, self.validation_results)
                        if success: dialog.close()

                    with ui.row().classes('w-full justify-end mt-6'):
                        ui.button("Commit Import", color="primary", icon="check_circle", on_click=do_commit).classes('px-8 py-2')

        dialog.open()