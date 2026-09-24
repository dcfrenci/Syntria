import uuid
import base64
import inspect
from datetime import datetime

from nicegui import ui, events
from components.style import Style
from components.modals import confirmation_modal
from api_client.presets import PresetsClient

# Standard Document Constraints
A4_WIDTH = 794
A4_HEIGHT = 1123


class QuoteBuilderState:
    def __init__(self):
        self.dragged_type = None
        self.dragged_element_id = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_el_x = 0
        self.drag_start_el_y = 0
        self.elements = []
        self.selected_id = None
        self.editing_preset_id = None
        self.element_to_delete = None
        self.preset_name = "New Preset"
        self.scale = 0.75  # Manage zoom state
        self.margins = {"top": 96.0, "right": 96.0, "bottom": 96.0, "left": 96.0}


def preset_page():
    """Renders the Customize Quote view & Drag-and-Drop Builder using Subpages"""
    with ui.column().classes("w-full"):
        ui.sub_pages(
            {
                "/preset": preset_list,
                "/preset/create": preset_create,
                "/preset/edit/{id}": preset_edit,
            }
        ).classes("w-full")


async def preset_list():
    with ui.column().classes("w-full"):
        ui.label("Quote Presets").classes(Style.title())

        async def load_presets():
            try:
                presets = await PresetsClient.get_presets()
                for p in presets:
                    if "created_at" in p and p["created_at"]:
                        p["created_at"] = datetime.fromisoformat(p["created_at"]).strftime("%d/%m/%Y")
                return presets
            except Exception as e:
                ui.notify(f"Failed to load presets: {e}", type="negative")
                return []

        def check_selected(table, type_name: str) -> bool:
            if not table.selected:
                ui.notify(f"Select a {type_name} before", type="warning")
                return False
            return True

        async def set_active(preset_id):
            try:
                await PresetsClient.update_preset(preset_id, {"is_active": True})
                ui.notify("Active preset updated", type="positive")
                table_presets.rows = await load_presets()
                table_presets.update()
            except Exception as e:
                ui.notify(f"Error updating preset: {e}", type="negative")

        def edit_preset():
            if check_selected(table_presets, "preset"):
                ui.navigate.to(f"/preset/edit/{table_presets.selected[0]['id']}")

        async def delete_preset(value: bool):
            if value and table_presets.selected:
                try:
                    await PresetsClient.delete_preset(table_presets.selected[0]["id"])
                    table_presets.rows = await load_presets()
                    table_presets.selected.clear()
                    table_presets.update()
                    ui.notify("The preset has been deleted", type="positive")
                except Exception as e:
                    ui.notify(f"Error deleting preset: {e}", type="negative")

        table_presets = ui.table(
            columns=[
                {"name": "name", "label": "Preset Name", "field": "name", "align": "left", "sortable": True},
                {"name": "created_at", "label": "Date Created", "field": "created_at", "align": "left", "sortable": True},
                {"name": "active", "label": "Active", "field": "active", "align": "left", "sortable": True},
            ],
            rows=await load_presets(),
            row_key="id",
            selection="single",
        ).classes(Style.table())

        with table_presets.add_slot("top"):
            search_input = (
                ui.input(placeholder="Search preset ...")
                .classes("w-full text-base")
                .props("clearable outlined rounded")
            )
            search_input.add_slot("prepend", '<q-icon name="search" />')
            table_presets.bind_filter_from(search_input, "value")

        table_presets.add_slot(
            "body-cell-active",
            """
            <q-td :props="props">
                <q-badge v-if="props.row.active" color="positive" text-color="white" label="Yes" />
                <q-btn v-else flat size="sm" color="primary" label="Set Active" @click="$parent.$emit('set_active', props.row)" />
            </q-td>
        """,
        )
        table_presets.on("set_active", lambda e: set_active(e.args["id"]))

        delete_diag = confirmation_modal(
            title="Delete Preset?",
            description="Are you sure you want to permanently delete this preset?",
            on_save_callback=delete_preset,
        )

        with ui.row().classes(Style.row_end()):
            ui.button("New", icon="r_add", on_click=lambda: ui.navigate.to("/preset/create"))
            ui.button("Edit", icon="r_edit", on_click=edit_preset)
            ui.button(
                "Delete", icon="r_delete", on_click=lambda: delete_diag.open() if check_selected(table_presets, "preset") else None
            )


async def preset_create():
    state = QuoteBuilderState()
    builder_ui(state)


async def preset_edit(id: int):
    state = QuoteBuilderState()
    try:
        preset = await PresetsClient.get_preset(int(id))
        if preset:
            state.editing_preset_id = preset["id"]
            state.preset_name = preset.get("name", "Untitled Preset")
            state.elements = [e.copy() for e in preset.get("elements", [])]
            state.margins = preset.get(
                "margins", {"top": 96.0, "right": 96.0, "bottom": 96.0, "left": 96.0}
            ).copy()
    except Exception as e:
        ui.notify(f"Could not load preset {id}: {e}", type="negative")
        ui.navigate.to("/preset")
        return

    builder_ui(state)


def builder_ui(state: QuoteBuilderState):

    # --- HELPER FUNCTIONS ---
    def enforce_margins(el):
        """Clamp element coordinates within the defined document margins and strictly enforce 1px precision."""
        max_x = A4_WIDTH - state.margins["right"] - el["w"]
        max_y = A4_HEIGHT - state.margins["bottom"] - el["h"]
        el["x"] = int(round(max(state.margins["left"], min(el["x"], max_x))))
        el["y"] = int(round(max(state.margins["top"], min(el["y"], max_y))))
        el["w"] = int(round(el["w"]))
        el["h"] = int(round(el["h"]))

    def reapply_margins_to_all():
        for el in state.elements:
            enforce_margins(el)
        render_canvas_area.refresh()
        render_properties_panel.refresh()

    def update_margin(key, value):
        val = int(round(float(value))) if value is not None else 0
        state.margins[key] = max(0, val)
        reapply_margins_to_all()

    def select_element(eid):
        state.selected_id = eid
        render_canvas_area.refresh()
        render_properties_panel.refresh()

    def update_element(el, key, value):
        if key in ["x", "y", "w", "h"]:
            el[key] = int(round(float(value))) if value is not None else 0
            enforce_margins(el)
        else:
            el[key] = value
        render_canvas_area.refresh()

    def remove_element(eid):
        state.elements = [e for e in state.elements if e["id"] != eid]
        state.selected_id = None
        render_canvas_area.refresh()
        render_properties_panel.refresh()

    def change_zoom(delta):
        state.scale = max(0.2, min(state.scale + delta, 2.0))
        render_canvas_area.refresh()

    def reset_zoom():
        state.scale = 0.75
        render_canvas_area.refresh()

    async def confirm_delete_element(result: bool):
        if result and state.element_to_delete:
            remove_element(state.element_to_delete)
        state.element_to_delete = None

    delete_element_diag = confirmation_modal(
        title="Delete Component?",
        description="Are you sure you want to remove this component from the page?",
        on_save_callback=confirm_delete_element,
    )

    async def save_preset():
        if not state.preset_name.strip():
            ui.notify("Preset name cannot be empty", type="warning")
            return

        payload = {
            "name": state.preset_name,
            "elements": state.elements,
            "margins": state.margins,
        }

        try:
            if state.editing_preset_id:
                await PresetsClient.update_preset(state.editing_preset_id, payload)
                ui.notify("Preset updated successfully", type="positive")
            else:
                payload["is_active"] = False
                await PresetsClient.create_preset(payload)
                ui.notify("New preset created successfully", type="positive")

            ui.navigate.to("/preset")
        except Exception as e:
            ui.notify(f"Failed to save preset: {e}", type="negative")

    def handle_keyboard(e: events.KeyEventArguments):
        if not e.action.keydown: return
        if not state.selected_id: return
        if e.key.name not in ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]: return

        el = next((e for e in state.elements if e["id"] == state.selected_id), None)
        if not el: return

        step = 10 if e.modifiers.shift else 1

        if e.key.name == "ArrowUp": el["y"] -= step
        elif e.key.name == "ArrowDown": el["y"] += step
        elif e.key.name == "ArrowLeft": el["x"] -= step
        elif e.key.name == "ArrowRight": el["x"] += step

        enforce_margins(el)
        render_canvas_area.refresh()
        render_properties_panel.refresh()

    ui.keyboard(on_key=handle_keyboard)

    # --- REFRESHABLE UI COMPONENTS ---
    @ui.refreshable
    def render_canvas_area():
        scaled_w = A4_WIDTH * state.scale
        scaled_h = A4_HEIGHT * state.scale
        
        with ui.element("div").style(f"width: {scaled_w}px; height: {scaled_h}px; position: relative;"):
            
            with ui.element("div").style(
                f"width: {A4_WIDTH}px; height: {A4_HEIGHT}px; "
                f"transform: scale({state.scale}); transform-origin: top left; "
                f"position: absolute; top: 0; left: 0;"
            ):
                canvas = (
                    ui.card()
                    .classes("bg-white shadow-xl relative overflow-hidden w-full h-full shrink-0")
                    .style("padding: 0; border-radius: 4px;")
                    .props('id="canvas_bg"')
                )
        
                canvas.on("dragover.prevent", lambda: None)

                def handle_drop(e):
                    
                    # Handle Moving an EXISTING Element
                    if getattr(state, "dragged_element_id", None):
                        el = next((x for x in state.elements if x["id"] == state.dragged_element_id), None)
                        if el:
                            delta_x = (e.args.get("clientX", 0) - state.drag_start_x) / state.scale
                            delta_y = (e.args.get("clientY", 0) - state.drag_start_y) / state.scale
                            
                            el["x"] = int(round(state.drag_start_el_x + delta_x))
                            el["y"] = int(round(state.drag_start_el_y + delta_y))
                            
                            enforce_margins(el)
                            state.selected_id = el["id"]
                        
                        state.dragged_element_id = None
                        render_canvas_area.refresh()
                        render_properties_panel.refresh()

                    # Handle Dropping a NEW Element from the Sidebar
                    elif getattr(state, "dragged_type", None):
                        target_id = e.args.get("target.id", "")
                        
                        if target_id == "canvas_bg":
                            x = e.args.get("offsetX", 0)
                            y = e.args.get("offsetY", 0)
                        elif target_id.startswith("el_"):
                            el_id = target_id[3:]
                            target_el = next((x for x in state.elements if x["id"] == el_id), None)
                            if target_el:
                                x = target_el["x"] + e.args.get("offsetX", 0)
                                y = target_el["y"] + e.args.get("offsetY", 0)
                            else:
                                x, y = state.margins["left"], state.margins["top"]
                        else:
                            x, y = state.margins["left"], state.margins["top"]

                        w, h = 200, 50
                        content = f"Sample {state.dragged_type.capitalize()}"

                        if state.dragged_type == "image": 
                            w, h = 150, 150
                            content = None
                        elif state.dragged_type == "quote": 
                            w, h = A4_WIDTH - state.margins["left"] - state.margins["right"], 200
                        elif state.dragged_type == "client": 
                            w, h = 250, 50
                            content = "Mr. /Ms Name Surname"
                        elif state.dragged_type == "date":
                            w, h = 150, 50
                            content = "Date 01/01/2002"

                        new_element = {
                            "id": str(uuid.uuid4()),
                            "type": state.dragged_type,
                            "x": int(round(x)),
                            "y": int(round(y)),
                            "w": int(round(w)),
                            "h": int(round(h)),
                            "content": content,
                        }

                        enforce_margins(new_element)
                        state.elements.append(new_element)
                        state.selected_id = new_element["id"]
                        state.dragged_type = None

                        render_canvas_area.refresh()
                        render_properties_panel.refresh()

                canvas.on("drop", handle_drop, ["offsetX", "offsetY", "clientX", "clientY", "target.id"])
                canvas.on("click", lambda: select_element(None))

                with canvas:
                    # Draw margins guide
                    ui.element("div").classes(
                        "absolute border-2 border-gray-200 border-dashed pointer-events-none"
                    ).style(
                        f"top: {state.margins['top']}px; left: {state.margins['left']}px; "
                        f"right: {state.margins['right']}px; bottom: {state.margins['bottom']}px;"
                    )

                    # Draw elements
                    for el in state.elements:
                        is_selected = el["id"] == state.selected_id
                        bg = "bg-blue-50/50" if is_selected else "bg-transparent"
                        border = (
                            "border-2 border-blue-500 border-dashed"
                            if is_selected
                            else "border-2 border-transparent hover:border-gray-300 hover:border-dashed"
                        )
                        
                        resize_style = "resize: both; overflow: hidden;" if is_selected else "overflow: hidden;"

                        with ui.card().classes(
                            f"absolute {bg} {border} cursor-grab p-2 shadow-none"
                        ).style(
                            f"left: {el['x']}px; top: {el['y']}px; width: {el['w']}px; height: {el['h']}px; "
                            f"pointer-events: auto; {resize_style}"
                        ).props(f'id="el_{el["id"]}" draggable="true"') as item:

                            item.on("mousedown", lambda e, eid=el["id"]: select_element(eid))

                            def on_dragstart(e, eid=el["id"]):
                                state.dragged_element_id = eid
                                state.drag_start_x = e.args.get("clientX", 0)
                                state.drag_start_y = e.args.get("clientY", 0)
                                target_el = next((x for x in state.elements if x["id"] == eid), None)
                                if target_el:
                                    state.drag_start_el_x = target_el["x"]
                                    state.drag_start_el_y = target_el["y"]

                            item.on("dragstart", on_dragstart, ["clientX", "clientY"])
                            item.on("dragend", lambda e: setattr(state, "dragged_element_id", None))

                            def on_mouseup(e, eid=el["id"]):
                                if eid == state.selected_id:
                                    w = e.args.get("offsetWidth")
                                    h = e.args.get("offsetHeight")
                                    if w and h:
                                        target_el = next((x for x in state.elements if x["id"] == eid), None)
                                        if target_el and (target_el["w"] != int(round(w)) or target_el["h"] != int(round(h))):
                                            target_el["w"] = int(round(w))
                                            target_el["h"] = int(round(h))
                                            enforce_margins(target_el)
                                            render_properties_panel.refresh()

                            item.on("mouseup", on_mouseup, ["offsetWidth", "offsetHeight"])

                            if is_selected:
                                def trigger_delete(eid):
                                    state.element_to_delete = eid
                                    delete_element_diag.open()

                                ui.icon("cancel", size="xs").classes(
                                    "absolute top-1 right-1 text-blue-500 bg-white rounded-full shadow-sm cursor-pointer hover:text-blue-700 z-50"
                                ).on("mousedown.stop.prevent", lambda e, eid=el["id"]: trigger_delete(eid))

                            # Content Rendering
                            if el["type"] in ["text", "client", "date"]:
                                ui.label(el["content"]).classes("w-full h-full whitespace-pre-wrap text-gray-800 pointer-events-none")
                            elif el["type"] == "image":
                                if el.get("content"):
                                    ui.image(el["content"]).classes("w-full h-full object-contain pointer-events-none")
                                else:
                                    ui.icon("image", size="xl").classes("absolute-center text-gray-400 pointer-events-none")
                            elif el["type"] == "quote":
                                with ui.column().classes("w-full h-full border border-gray-300 bg-gray-50 p-2 pointer-events-none"):
                                    ui.label("Quote Table Placeholder").classes("text-gray-500 italic font-bold")
                                    ui.label("Item 1 ......... $100").classes("text-gray-500 text-sm")
                            elif el["type"] == "sign":
                                ui.label("Signature:").classes("text-xs text-gray-500 absolute top-0 pointer-events-none")
                                ui.label().classes("border-b border-black w-full absolute-bottom mb-2 pointer-events-none")

    @ui.refreshable
    def render_properties_panel():
        if not state.selected_id:
            ui.label("Component Detail").classes(Style.h2())
            ui.label("Select an element on the canvas to view or edit its properties. Use Arrow Keys to nudge selected items.").classes("text-gray-500 text-sm mt-4")
            return

        el = next((e for e in state.elements if e["id"] == state.selected_id), None)
        if el:
            # --- Position & Size ---
            ui.label("Position & Size").classes(Style.h2())

            with ui.row().classes("w-full gap-2 mb-2"):
                ui.number("X", value=el["x"], format="%.0f", step=1, on_change=lambda e, elem=el: update_element(elem, "x", e.value)).classes("flex-1")
                ui.number("Y", value=el["y"], format="%.0f", step=1, on_change=lambda e, elem=el: update_element(elem, "y", e.value)).classes("flex-1")

            with ui.row().classes("w-full gap-2 mb-6"):
                ui.number("W", value=el["w"], format="%.0f", step=1, min=1, on_change=lambda e, elem=el: update_element(elem, "w", e.value)).classes("flex-1")
                ui.number("H", value=el["h"], format="%.0f", step=1, min=1, on_change=lambda e, elem=el: update_element(elem, "h", e.value)).classes("flex-1")

            # --- Content ---
            if el["type"] in ["text", "client", "date"]:
                ui.label("Content").classes(Style.h2()).classes("mt-4")
                if el["type"] == "client":
                    ui.label("Will be replaced with actual Client Details during quote generation.").classes("text-xs text-gray-500 mb-2")
                elif el["type"] == "date":
                    ui.label("Will be replaced with actual Date during quote generation.").classes("text-xs text-gray-500 mb-2")
                    
                ui.textarea("Text Value", value=el["content"], on_change=lambda e, elem=el: update_element(elem, "content", e.value)).classes("w-full mb-6")
            
            elif el["type"] == "image":
                ui.label("Content (Image Source)").classes(Style.h2()).classes("mt-4")
                
                async def handle_image_upload(e: events.UploadEventArguments):
                    try:
                        file_like = None
                        if hasattr(e, 'content') and hasattr(e.content, 'read'):
                            file_like = e.content
                        elif hasattr(e, 'file') and hasattr(e.file, 'read'):
                            file_like = e.file
                        else:
                            file_like = next((getattr(e, a) for a in dir(e) if hasattr(getattr(e, a), 'read')), None)
                            
                        if not file_like:
                            ui.notify("Upload failed: No readable file payload found.", type="negative")
                            return
                        
                        content_or_coro = file_like.read()
                        if inspect.isawaitable(content_or_coro):
                            content = await content_or_coro
                        else:
                            content = content_or_coro
                            
                        encoded = base64.b64encode(content).decode('utf-8')
                        
                        ext = getattr(e, 'name', 'image.png').split('.')[-1].lower()
                        mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp', 'svg': 'image/svg+xml'}
                        mime_type = mime_types.get(ext, 'image/png')
                        
                        data_uri = f"data:{mime_type};base64,{encoded}"
                        update_element(el, "content", data_uri)
                    except Exception as ex:
                        ui.notify(f"Error processing image: {ex}", type="negative")

                ui.upload(on_upload=handle_image_upload, auto_upload=True, max_files=1).classes('w-full mb-4').props('accept="image/*" flat bordered')
                
                if el.get("content"):
                    ui.button("Remove Image", on_click=lambda e, elem=el: update_element(elem, "content", None), icon="delete").classes("w-full mb-6 bg-red-100 text-red-600 hover:bg-red-200").props("unelevated")

            # --- Delete ---
            ui.button("Remove Component", color="negative", icon="delete", on_click=lambda elem_id=el["id"]: remove_element(elem_id)).classes("w-full mt-auto")

    @ui.refreshable
    def render_margin_panel():
        ui.label("Document Margins").classes(Style.h2())
        ui.label("Standard A4 Size (794x1123 px)").classes("text-xs text-gray-400 mb-4")

        with ui.grid(columns=2).classes("w-full gap-2 mb-4"):
            ui.number("Top", value=state.margins["top"], format="%.0f", step=1, min=0, on_change=lambda e: update_margin("top", e.value))
            ui.number("Bottom", value=state.margins["bottom"], format="%.0f", step=1, min=0, on_change=lambda e: update_margin("bottom", e.value))
            ui.number("Left", value=state.margins["left"], format="%.0f", step=1, min=0, on_change=lambda e: update_margin("left", e.value))
            ui.number("Right", value=state.margins["right"], format="%.0f", step=1, min=0, on_change=lambda e: update_margin("right", e.value))

        def restore_defaults():
            state.margins = {"top": 96.0, "right": 96.0, "bottom": 96.0, "left": 96.0}
            reapply_margins_to_all()
            render_margin_panel.refresh()

        ui.button("Restore Default", icon="restore", on_click=restore_defaults).classes("w-full bg-gray-200 text-gray-700 hover:bg-gray-300").props("unelevated")


    # --- MAIN UI LAYOUT ---
    with ui.column().classes("w-full min-h-[900px] pb-20"):
        
        # Floating Buttons
        with ui.row().classes("fixed bottom-8 right-8 gap-4 z-50"):
            ui.button("Cancel", color="negative", icon="r_close", on_click=lambda: ui.navigate.to("/preset")).classes("shadow-lg px-6")
            ui.button("Save", color="primary", icon="r_save", on_click=save_preset).classes("shadow-lg px-6")
        
        # Header (No back button)
        page_title = "Edit Preset" if state.editing_preset_id else "New Preset"
        with ui.row().classes("w-full items-center gap-4 mb-4"):
            ui.label(page_title).classes(Style.title()).classes("mb-0")

        # 35% / 60% Layout wrapper
        with ui.row().classes("w-full justify-between items-start"):
            
            # --- LEFT COLUMN (35%) ---
            # Standard vertical flow for Left Column
            with ui.column().classes("w-[35%] justify-center gap-4 min-w-[300px]"):
                
                # 1. Preset Details (Name)
                with ui.card().classes("w-full shadow-sm p-4 shrink-0"):
                    ui.label("Preset Details").classes(Style.h2())
                    ui.input("Preset Name").bind_value(state, "preset_name").classes("w-full text-lg")

                # 2. Components List
                with ui.card().classes("w-full shadow-sm p-4 shrink-0"):
                    ui.label("Components").classes(Style.h2())

                    def on_sidebar_dragstart(e, t):
                        state.dragged_type = t
                        state.dragged_element_id = None

                    def component_block(icon_name, label, ctype):
                        card = ui.row().classes(
                            "w-full bg-gray-50 border border-gray-200 p-3 rounded-md cursor-grab items-center gap-4 hover:bg-gray-100 transition-colors"
                        ).props('draggable="true"')
                        
                        card.on("dragstart", lambda e, t=ctype: on_sidebar_dragstart(e, t))
                        card.on("dragend", lambda e: setattr(state, "dragged_type", None))

                        with card:
                            ui.icon(icon_name, size="sm").classes("text-gray-700")
                            ui.label(label).classes("text-gray-900 font-medium")

                    component_block("text_fields", "Text", "text")
                    component_block("person", "Client", "client")
                    component_block("calendar_today", "Date", "date")
                    component_block("image", "Image", "image")
                    component_block("shopping_cart", "Quote", "quote")
                    component_block("draw", "Sign", "sign")
                
                # 3 & 4. Component Detail (Position, Size, Content)
                with ui.card().classes("w-full shadow-sm p-4 min-h-[250px] shrink-0"):
                    render_properties_panel()

                # 5. Page Margin
                with ui.card().classes("w-full shadow-sm p-4 shrink-0"):
                    render_margin_panel()

            # --- RIGHT COLUMN (60%) ---
            # Outer container is relative and overflow-hidden to anchor the zoom controls
            with ui.element("div").classes("w-[60%] sticky top-6 bg-gray-100 rounded-xl border border-gray-200 shadow-inner h-[calc(100vh-8rem)] z-10 relative overflow-hidden flex flex-col"):
                
                # Zoom controls locked to the bottom-center of the OUTER container
                with ui.row().classes("absolute bottom-4 left-1/2 -translate-x-1/2 z-50 bg-white border border-gray-200 shadow-sm rounded-lg p-1 gap-1 items-center"):
                    ui.button(icon="remove", on_click=lambda: change_zoom(-0.05)).props("dense flat round size=sm text-color=gray-700")
                    ui.button("Reset", on_click=reset_zoom).props("dense flat size=sm text-color=gray-700").classes("px-2 font-bold")
                    ui.button(icon="add", on_click=lambda: change_zoom(0.05)).props("dense flat round size=sm text-color=gray-700")

                # Inner scrollable wrapper for the actual canvas
                with ui.column().classes("w-full h-full overflow-auto items-center justify-start p-6"):
                    render_canvas_area()