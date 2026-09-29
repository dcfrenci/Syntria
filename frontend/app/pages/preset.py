import uuid
import base64
import inspect
from datetime import datetime
from nicegui import ui, events
from components.style import Style
from components.modals import confirmation_modal
from components.quote_preview_modal import QuotePreviewModal
from api_client.presets import PresetsClient

# Standard Document Constraints
A4_WIDTH = 794
A4_HEIGHT = 1123

# Mock Quote Data for Preview Generation with corrected total amount
FAKE_QUOTE = {
  "valid_until": "2026-09-25",
  "id": 0,
  "status": "Draft",
  "total_amount": "1970.00",
    "patient": { "first_name": "Mario", "last_name": "Rossi" },
    "quote_items": [
        { "quantity": 1, "item": { "name": "Dental Cleaning", "price": "80", "is_specific": False }, "teeth": [] },
    { "quantity": 2, "item": { "name": "Cavity Filling", "price": "120", "is_specific": True }, "teeth": [11, 12] },
    { "quantity": 1, "item": { "name": "Root Canal", "price": "500", "is_specific": True }, "teeth": [24] },
    { "quantity": 1, "item": { "name": "Crown Installation", "price": "850", "is_specific": True }, "teeth": [31] },
    { "quantity": 4, "item": { "name": "X-Ray", "price": "25", "is_specific": False }, "teeth": [] },
    { "quantity": 1, "item": { "name": "Teeth Whitening", "price": "200", "is_specific": False }, "teeth": [] }
  ],
    "created_at": "2026-09-25T15:23:36.631Z"
}

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
        self.preset_name = ""
        self.scale = 0.75  
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

        async def on_set_active_click():
            if check_selected(table_presets, "preset"):
                await set_active(table_presets.selected[0]['id'])

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
                {"name": "is_active", "label": "Active", "field": "is_active", "align": "left", "sortable": True},
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
            "body-cell-is_active",
            """
            <q-td :props="props">
                <q-badge v-if="props.row.is_active" color="positive" text-color="white" label="Active" />
            </q-td>
            """,
        )

        delete_diag = confirmation_modal(
            title="Delete Preset?",
            description="Are you sure you want to permanently delete this preset?",
            on_save_callback=delete_preset,
        )

        with ui.row().classes(Style.row_end()):
            ui.button("Set Active", icon="check_circle", on_click=on_set_active_click)
            ui.button("New", icon="r_add", on_click=lambda: ui.navigate.to("/preset/create"))
            ui.button("Edit", icon="r_edit", on_click=edit_preset)
            ui.button(
                "Delete", icon="r_delete", on_click=lambda: delete_diag.open() if check_selected(table_presets, "preset") else None
            )


async def preset_create():
    state = QuoteBuilderState()
    
    # Auto-populate mandatory components for new presets
    state.elements = [
        {
            "id": str(uuid.uuid4()),
            "type": "client",
            "x": int(state.margins["left"]),
            "y": int(state.margins["top"]),
            "w": 250,
            "h": 50,
            "content": "Mr. /Ms Name Surname",
            "font_size": 14,
            "font_bold": True,
            "font_italic": False
        },
        {
            "id": str(uuid.uuid4()),
            "type": "date",
            "x": int(A4_WIDTH - state.margins["right"] - 150),
            "y": int(state.margins["top"]),
            "w": 150,
            "h": 50,
            "content": "Date 01/01/2002",
            "font_size": 14,
            "font_bold": False,
            "font_italic": False
        },
        {
            "id": str(uuid.uuid4()),
            "type": "quote",
            "x": int(state.margins["left"]),
            "y": int(state.margins["top"] + 100),
            "w": int(A4_WIDTH - state.margins["left"] - state.margins["right"]),
            "h": 200,
            "content": "Sample Quote"
        }
    ]
    
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
    preview_modal = QuotePreviewModal()

    # --- HELPER FUNCTIONS ---
    def enforce_margins(el):
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
        if state.selected_id != eid:
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
        render_components_list.refresh()

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

        types = [e["type"] for e in state.elements]
        for req in ["client", "date", "quote"]:
            if types.count(req) == 0:
                ui.notify(f"Preset must contain a {req.capitalize()} component.", type="warning")
                return
            elif types.count(req) > 1:
                ui.notify(f"Only one {req.capitalize()} component is allowed.", type="warning")
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

    # Real-time background sync loop to capture native CSS resizes smoothly
    async def auto_sync_size():
        if not state.selected_id: return
        try:
            res = await ui.run_javascript(f'''
                var el = document.getElementById("el_{state.selected_id}_base");
                return el ? {{w: el.offsetWidth, h: el.offsetHeight}} : null;
            ''', timeout=1.0)
            if res:
                target_el = next((x for x in state.elements if x["id"] == state.selected_id), None)
                if target_el:
                    new_w = int(round(res['w']))
                    new_h = int(round(res['h']))
                    if target_el["w"] != new_w or target_el["h"] != new_h:
                        target_el["w"] = new_w
                        target_el["h"] = new_h
                        render_properties_panel.refresh()
        except Exception:
            pass
            
    ui.timer(0.2, auto_sync_size)

    # --- REFRESHABLE UI COMPONENTS ---
    @ui.refreshable
    def render_components_list():
        def on_sidebar_dragstart(e, t):
            state.dragged_type = t
            state.dragged_element_id = None

        def component_block(icon_name, label, ctype):
            is_disabled = ctype in ["client", "date", "quote"] and any(el["type"] == ctype for el in state.elements)
            base_classes = "w-full bg-gray-50 border border-gray-200 p-2 rounded-md flex-nowrap items-center gap-2"
            
            if is_disabled:
                card = ui.row().classes(base_classes + " opacity-50 cursor-not-allowed")
                with card:
                    ui.icon(icon_name, size="sm").classes("text-gray-400 shrink-0")
                    ui.label(label).classes("text-gray-400 font-medium text-sm truncate")
                    ui.space()
                    ui.icon("check", size="sm").classes("text-green-500 shrink-0")
            else:
                card = ui.row().classes(base_classes + " cursor-grab hover:bg-gray-100 transition-colors").props('draggable="true"')
                
                card.on("dragstart", lambda e, t=ctype: on_sidebar_dragstart(e, t))
                card.on("dragend", lambda e: setattr(state, "dragged_type", None))
                
                with card:
                    ui.icon(icon_name, size="sm").classes("text-gray-700 shrink-0")
                    ui.label(label).classes("text-gray-900 font-medium text-sm truncate")

        with ui.grid(columns=2).classes("w-full gap-2 mt-2"):
            component_block("text_fields", "Text", "text")
            component_block("person", "Client", "client")
            component_block("calendar_today", "Date", "date")
            component_block("image", "Image", "image")
            component_block("shopping_cart", "Quote", "quote")
            component_block("draw", "Sign", "sign")


    @ui.refreshable
    def render_canvas_area():
        scaled_w = A4_WIDTH * state.scale
        scaled_h = A4_HEIGHT * state.scale
        
        with ui.element("div").classes("relative").style(f"width: {scaled_w}px; height: {scaled_h}px;"):
            
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

                    elif getattr(state, "dragged_type", None):
                        if state.dragged_type in ["client", "date", "quote"] and any(el["type"] == state.dragged_type for el in state.elements):
                            ui.notify(f"Only one {state.dragged_type.capitalize()} component is allowed.", type="warning")
                            state.dragged_type = None
                            return

                        target_id = e.args.get("target.id", "")
                        target_id_clean = target_id.replace("el_", "").replace("_base", "")
                        
                        if target_id == "canvas_bg":
                            x = e.args.get("offsetX", 0)
                            y = e.args.get("offsetY", 0)
                        elif target_id_clean:
                            target_el = next((x for x in state.elements if x["id"] == target_id_clean), None)
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
                        
                        if state.dragged_type in ["text", "client", "date"]:
                            new_element.update({
                                "font_size": 14, 
                                "font_bold": state.dragged_type == "client", 
                                "font_italic": False
                            })
                        elif state.dragged_type == "image":
                            new_element.update({
                                "image_fit": "contain",
                                "image_pos_x": 50,
                                "image_pos_y": 50
                            })

                        enforce_margins(new_element)
                        state.elements.append(new_element)
                        state.selected_id = new_element["id"]
                        state.dragged_type = None

                        render_canvas_area.refresh()
                        render_properties_panel.refresh()
                        render_components_list.refresh()

                canvas.on("drop", handle_drop, ["offsetX", "offsetY", "clientX", "clientY", "target.id"])
                canvas.on("click", lambda: select_element(None))

                with canvas:
                    ui.element("div").classes("absolute border-2 border-gray-200 border-dashed pointer-events-none").style(
                        f"top: {state.margins['top']}px; left: {state.margins['left']}px; "
                        f"right: {state.margins['right']}px; bottom: {state.margins['bottom']}px;"
                    )

                    for el in state.elements:
                        is_selected = el["id"] == state.selected_id
                        bg = "bg-blue-50/50" if is_selected else "bg-transparent"
                        border = (
                            "border-2 border-blue-500 border-dashed" if is_selected 
                            else "border-2 border-transparent hover:border-gray-300 hover:border-dashed"
                        )
                        
                        resize_style = "overflow: hidden;"
                        if is_selected:
                            resize_style = "resize: vertical; overflow: hidden;" if el["type"] == "quote" else "resize: both; overflow: hidden;"

                        max_el_w = A4_WIDTH - state.margins["right"] - el["x"]
                        max_el_h = A4_HEIGHT - state.margins["bottom"] - el["y"]

                        with ui.card().classes(
                            f"absolute {bg} {border} p-2 shadow-none"
                        ).style(
                            f"left: {el['x']}px; top: {el['y']}px; width: {el['w']}px; height: {el['h']}px; "
                            f"max-width: {max_el_w}px; max-height: {max_el_h}px; "
                            f"pointer-events: auto; {resize_style}"
                        ).props(f'id="el_{el["id"]}_base"') as item:
                            
                            item.on("mousedown", lambda e, eid=el["id"]: select_element(eid))
                            
                            if is_selected:
                                def trigger_delete(eid):
                                    state.element_to_delete = eid
                                    delete_element_diag.open()
                                
                                ui.icon("cancel", size="xs").classes(
                                    "absolute top-1 right-1 text-blue-500 bg-white rounded-full shadow-sm cursor-pointer hover:text-blue-700 z-50"
                                ).on("mousedown.stop.prevent", lambda e, eid=el["id"]: trigger_delete(eid))
                            
                            def on_dragstart(e, eid=el["id"]):
                                state.dragged_element_id = eid
                                state.drag_start_x = e.args.get("clientX", 0)
                                state.drag_start_y = e.args.get("clientY", 0)
                                
                                target_el = next((x for x in state.elements if x["id"] == eid), None)
                                if target_el:
                                    state.drag_start_el_x = target_el["x"]
                                    state.drag_start_el_y = target_el["y"]

                            drag_overlay = ui.element('div').classes('absolute top-0 left-0 cursor-grab').style(
                                'width: calc(100% - 16px); height: calc(100% - 16px); z-index: 10;'
                            ).props(f'id="el_{el["id"]}" draggable="true"')
                            
                            drag_overlay.on("mousedown", lambda e, eid=el["id"]: select_element(eid))
                            drag_overlay.on("dragstart", on_dragstart, ["clientX", "clientY"])
                            drag_overlay.on("dragend", lambda e: setattr(state, "dragged_element_id", None))

                            # Content Rendering
                            if el["type"] in ["text", "client", "date"]:
                                f_size = el.get("font_size", 14)
                                f_weight = "bold" if el.get("font_bold") else "normal"
                                f_style = "italic" if el.get("font_italic") else "normal"
                                style_str = f"font-size: {f_size}px; font-weight: {f_weight}; font-style: {f_style};"
                                
                                ui.label(el["content"]).classes("w-full h-full whitespace-pre-wrap text-gray-800 pointer-events-none").style(style_str)
                                
                            elif el["type"] == "image":
                                if el.get("content"):
                                    fit_style = el.get("image_fit", "contain")
                                    pos_x = el.get("image_pos_x", 50)
                                    pos_y = el.get("image_pos_y", 50)
                                    ui.element('img').props(f'src="{el["content"]}" draggable="false"').classes(
                                        f"w-full h-full pointer-events-none object-{fit_style}"
                                    ).style(f"object-position: {pos_x}% {pos_y}%;")
                                else:
                                    ui.icon("image", size="xl").classes("absolute-center text-gray-400 pointer-events-none")
                                
                            elif el["type"] == "quote":
                                with ui.column().classes("w-full h-full gap-0 pointer-events-none"):
                                    with ui.row().classes("w-full border-b-2 border-gray-800 pb-2 mb-2 font-bold text-gray-900 text-sm"):
                                        ui.label("Service").classes("flex-1")
                                        ui.label("Teeth").classes("w-20 text-center")
                                        ui.label("Qty").classes("w-16 text-center")
                                        ui.label("Unit Price").classes("w-32 text-right")
                                        
                                    with ui.row().classes("w-full text-gray-800 mb-1 text-sm items-center"):
                                        ui.label("Sample Dental Service with a very long name that wraps beautifully").classes("flex-1 whitespace-normal line-clamp-2 leading-tight")
                                        ui.label("11, 12").classes("w-20 text-center text-xs truncate")
                                        ui.label("1").classes("w-16 text-center")
                                        ui.label("$150.00").classes("w-32 text-right truncate")
                                        
                                    ui.space()
                                    with ui.row().classes("w-full border-t border-gray-400 pt-2 mt-2 font-bold text-gray-900 text-sm"):
                                        ui.label("Total Amount").classes("flex-1 text-right pr-4")
                                        ui.label("$150.00").classes("w-32 text-right truncate")
                                        
                            elif el["type"] == "sign":
                                with ui.column().classes("w-full h-full justify-end gap-0 pointer-events-none"):
                                    ui.label("Signature:").classes("text-xs text-gray-500 mb-1")
                                    ui.label().classes("border-b border-black w-full")


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
                x_input = ui.number("X", value=el["x"], format="%.0f", step=1, on_change=lambda e, elem=el: update_element(elem, "x", e.value)).classes("flex-1")
                if el["type"] == "quote": x_input.props('disable')
                ui.number("Y", value=el["y"], format="%.0f", step=1, on_change=lambda e, elem=el: update_element(elem, "y", e.value)).classes("flex-1")
            
            with ui.row().classes("w-full gap-2 mb-6"):
                w_input = ui.number("W", value=el["w"], format="%.0f", step=1, min=1, on_change=lambda e, elem=el: update_element(elem, "w", e.value)).classes("flex-1")
                if el["type"] == "quote": w_input.props('disable')
                ui.number("H", value=el["h"], format="%.0f", step=1, min=1, on_change=lambda e, elem=el: update_element(elem, "h", e.value)).classes("flex-1")

            # --- Content ---
            if el["type"] in ["text", "client", "date"]:
                ui.label("Content & Style").classes(Style.h2()).classes("mt-4")
                
                if el["type"] == "client":
                    ui.label("Will be replaced with actual Client Details during quote generation.").classes("text-xs text-gray-500 mb-4")
                elif el["type"] == "date":
                    ui.label("Will be replaced with actual Date during quote generation.").classes("text-xs text-gray-500 mb-4")
                
                with ui.row().classes("w-full justify-between items-center mb-4"):
                    with ui.row().classes("items-center gap-1"):
                        ui.number("Size", value=el.get("font_size", 14), format="%d", step=1, min=8, max=100,
                                  on_change=lambda e, elem=el: update_element(elem, "font_size", int(e.value)) if e.value else None).props('dense').classes("w-16")
                        ui.button(icon="refresh", on_click=lambda e, elem=el: update_element(elem, "font_size", 14)).props("dense flat size=sm").tooltip("Reset to 14px")
                    
                    with ui.row().classes("items-center gap-4"):
                        ui.checkbox("Bold", value=el.get("font_bold", False),
                                    on_change=lambda e, elem=el: update_element(elem, "font_bold", e.value)).props('dense')
                        ui.checkbox("Italic", value=el.get("font_italic", False),
                                    on_change=lambda e, elem=el: update_element(elem, "font_italic", e.value)).props('dense')
                
                if el["type"] == "text":
                    ui.textarea("Text Value", value=el["content"], on_change=lambda e, elem=el: update_element(elem, "content", e.value)).classes("w-full mb-6")
                else:
                    ui.element('div').classes('mb-6') 
            
            elif el["type"] == "image":
                ui.label("Display Mode").classes(Style.h2()).classes("mt-4")
                
                with ui.row().classes("w-full mb-4"):
                    ui.radio({"contain": "Fit Entire Image", "cover": "Crop to Fill"}, value=el.get("image_fit", "contain"),
                              on_change=lambda e, elem=el: update_element(elem, "image_fit", e.value)).props('inline')
                
                if el.get("image_fit") == "cover":
                    ui.label("Adjust Image Focus (Pan X/Y)").classes("text-sm font-bold text-gray-700")
                    with ui.row().classes("w-full gap-2 items-center mb-6 mt-2"):
                        ui.label("X").classes("text-xs font-bold text-gray-500")
                        ui.slider(min=0, max=100, value=el.get("image_pos_x", 50), on_change=lambda e, elem=el: update_element(elem, "image_pos_x", e.value)).classes("flex-1")
                        ui.label("Y").classes("text-xs font-bold text-gray-500")
                        ui.slider(min=0, max=100, value=el.get("image_pos_y", 50), on_change=lambda e, elem=el: update_element(elem, "image_pos_y", e.value)).classes("flex-1")
                
                ui.label("Content (Upload Image - Max 2MB)").classes(Style.h2()).classes("mt-4")
                
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

                ui.upload(
                    on_upload=handle_image_upload, 
                    auto_upload=True, 
                    max_files=1,
                    on_rejected=lambda: ui.notify('Image is too large. Please upload an image under 2MB.', type='negative')
                ).classes('w-full mb-4').props('accept="image/*" flat bordered max-file-size=2097152')
                
                if el.get("content"):
                    ui.button("Remove Image", on_click=lambda e, elem=el: update_element(elem, "content", None), icon="delete").classes("w-full mb-6 bg-red-100 text-red-600 hover:bg-red-200").props("unelevated")

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
        
        with ui.row().classes("fixed bottom-8 right-8 gap-4 z-50"):
            ui.button("Preview", color="info", icon="visibility", on_click=lambda: preview_modal.open({"elements": state.elements, "margins": state.margins}, FAKE_QUOTE)).classes("shadow-lg px-6")
            ui.button("Cancel", color="negative", icon="r_close", on_click=lambda: ui.navigate.to("/preset")).classes("shadow-lg px-6")
            ui.button("Save", color="primary", icon="r_save", on_click=save_preset).classes("shadow-lg px-6")
        
        page_title = "Edit Preset" if state.editing_preset_id else "New Preset"
        with ui.row().classes("w-full items-center gap-4 mb-4"):
            ui.label(page_title).classes(Style.title()).classes("mb-0")

        with ui.row().classes("w-full justify-between items-start"):
            
            with ui.column().classes("w-[35%] justify-center gap-4 min-w-[300px]"):
                with ui.card().classes("w-full shadow-sm p-4 shrink-0"):
                    ui.label("Preset Details").classes(Style.h2())
                    ui.input("Preset Name").bind_value(state, "preset_name").classes("w-full text-lg")

                with ui.card().classes("w-full shadow-sm p-4 shrink-0"):
                    ui.label("Components").classes(Style.h2())
                    render_components_list()
                
                with ui.card().classes("w-full shadow-sm p-4 min-h-[250px] shrink-0"):
                    render_properties_panel()

                with ui.card().classes("w-full shadow-sm p-4 shrink-0"):
                    render_margin_panel()

            with ui.element("div").classes("w-[60%] sticky top-6 bg-gray-100 rounded-xl border border-gray-200 shadow-inner h-[calc(100vh-8rem)] z-10 relative overflow-hidden flex flex-col"):
                with ui.row().classes("absolute bottom-4 left-1/2 -translate-x-1/2 z-50 bg-white border border-gray-200 shadow-sm rounded-lg p-1 gap-1 items-center"):
                    ui.button(icon="remove", on_click=lambda: change_zoom(-0.05)).props("dense flat round size=sm text-color=gray-700")
                    ui.button("Reset", on_click=reset_zoom).props("dense flat size=sm text-color=gray-700").classes("px-2 font-bold")
                    ui.button(icon="add", on_click=lambda: change_zoom(0.05)).props("dense flat round size=sm text-color=gray-700")

                with ui.column().classes("w-full h-full overflow-auto items-center justify-start p-6"):
                    render_canvas_area()