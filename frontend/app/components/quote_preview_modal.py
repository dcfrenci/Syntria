from nicegui import ui
from datetime import datetime

A4_WIDTH = 794
A4_HEIGHT = 1123

class QuotePreviewModal:
    """
    A reusable modal for rendering an A4 document preview from preset elements and real quote data.
    """
    def __init__(self):
        self.dialog = ui.dialog()

    def open(self, preset: dict, quote: dict):
        self.dialog.clear()
        
        elements = preset.get("elements", [])
        margins = preset.get("margins", {"top": 96.0, "right": 96.0, "bottom": 96.0, "left": 96.0})
        
        # Safely extract data from quote payload
        patient = quote.get("patient", {})
        patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        if not patient_name:
            patient_name = "Unknown Client"
            
        # Parse date to dd/mm/yyyy
        raw_date = quote.get("created_at", "")
        if raw_date:
            try:
                dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                date_str = dt_obj.strftime("%d/%m/%Y")
            except ValueError:
                # Fallback manual parsing if ISO format fails
                date_parts = raw_date.split("T")[0].split("-")
                if len(date_parts) == 3:
                    date_str = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                else:
                    date_str = raw_date
        else:
            date_str = "N/A"

        items = quote.get("quote_items", [])
        total_amount = quote.get("total_amount", "0.00")
        
        # Truncate extremely large test values to prevent layout blowing out
        if len(str(total_amount)) > 15:
            total_amount = str(total_amount)[:12] + "..."

        # Calculate Pagination Logic
        HEADER_HEIGHT = 40
        ROW_HEIGHT = 45 # Supports 2 lines of wrapped text
        FOOTER_HEIGHT = 50
        
        quote_el = next((e for e in elements if e["type"] == "quote"), None)
        pages_data = []
        
        if quote_el and items:
            items_remaining = list(items)
            
            # Page 1 capacity calculation
            avail_1 = A4_HEIGHT - margins["bottom"] - quote_el["y"]
            max_items_1 = max(0, int((avail_1 - HEADER_HEIGHT - FOOTER_HEIGHT) // ROW_HEIGHT))
            
            if max_items_1 >= len(items_remaining):
                pages_data.append({'items': items_remaining, 'is_last': True, 'start_y': quote_el["y"]})
                items_remaining = []
            else:
                if max_items_1 > 0:
                    pages_data.append({'items': items_remaining[:max_items_1], 'is_last': False, 'start_y': quote_el["y"]})
                    items_remaining = items_remaining[max_items_1:]
                else:
                    pages_data.append({'items': [], 'is_last': False, 'start_y': quote_el["y"]})
            
            # Subsequent Pages logic
            while items_remaining:
                avail_n = A4_HEIGHT - margins["bottom"] - margins["top"]
                max_items_n = max(1, int((avail_n - HEADER_HEIGHT - FOOTER_HEIGHT) // ROW_HEIGHT))
                
                if max_items_n >= len(items_remaining):
                    pages_data.append({'items': items_remaining, 'is_last': True, 'start_y': margins["top"]})
                    items_remaining = []
                else:
                    pages_data.append({'items': items_remaining[:max_items_n], 'is_last': False, 'start_y': margins["top"]})
                    items_remaining = items_remaining[max_items_n:]
        else:
            pages_data.append({'items': [], 'is_last': True, 'start_y': 0})

        with self.dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden bg-gray-200 flex flex-col items-center'):
            # Modal Header
            with ui.row().classes('w-full justify-between items-center p-4 bg-white shadow-sm z-10'):
                ui.label('Document Preview').classes('text-xl font-bold text-gray-800')
                ui.button(icon='close', on_click=self.dialog.close).props('flat round dense text-color=gray-700')
            
            # Canvas Container (Scrollable)
            with ui.column().classes('w-full items-center p-8 overflow-auto h-[80vh] gap-8 bg-gray-200'):
                scale = 0.85
                scaled_w = A4_WIDTH * scale
                scaled_h = A4_HEIGHT * scale
                
                # Render multi-page iteration
                for i, p_data in enumerate(pages_data):
                    is_last_page = p_data.get('is_last', True)
                    
                    with ui.element('div').classes("shrink-0").style(f'width: {scaled_w}px; height: {scaled_h}px; position: relative;'):
                        with ui.element('div').style(
                            f'width: {A4_WIDTH}px; height: {A4_HEIGHT}px; '
                            f'transform: scale({scale}); transform-origin: top left; '
                            f'position: absolute; top: 0; left: 0; '
                            f'background-color: white; border-radius: 4px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);'
                        ):
                            # Render static template elements
                            for el in elements:
                                if el["type"] == "quote": continue
                                if el["type"] == "sign" and not is_last_page: continue # Signature only goes on final page
                                if el["type"] not in ["sign", "quote"] and i > 0: continue # Static components ONLY on page 1
                                
                                with ui.element('div').style(
                                    f"position: absolute; left: {el['x']}px; top: {el['y']}px; "
                                    f"width: {el['w']}px; height: {el['h']}px;"
                                ):
                                    if el["type"] in ["text", "client", "date"]:
                                        f_size = el.get("font_size", 14)
                                        f_weight = "bold" if el.get("font_bold") else "normal"
                                        f_style = "italic" if el.get("font_italic") else "normal"
                                        style_str = f"font-size: {f_size}px; font-weight: {f_weight}; font-style: {f_style};"
                                        
                                        if el["type"] == "text":
                                            ui.label(el["content"]).classes("w-full h-full whitespace-pre-wrap text-gray-800").style(style_str)
                                        elif el["type"] == "client":
                                            ui.label(f"Mr. / Ms. {patient_name}").classes("w-full h-full text-gray-900").style(style_str)
                                        elif el["type"] == "date":
                                            ui.label(f"Date: {date_str}").classes("w-full h-full text-gray-800").style(style_str)
                                            
                                    elif el["type"] == "image":
                                        if el.get("content"):
                                            fit_style = el.get("image_fit", "contain")
                                            pos_x = el.get("image_pos_x", 50)
                                            pos_y = el.get("image_pos_y", 50)
                                            # Use native HTML img to avoid Vue style parsing limits and resize blockages
                                            ui.element('img').props(f'src="{el["content"]}" draggable="false"').classes(
                                                f"w-full h-full pointer-events-none object-{fit_style}"
                                            ).style(f"object-position: {pos_x}% {pos_y}%;")
                                            
                                    elif el["type"] == "sign":
                                        with ui.column().classes("w-full h-full justify-end gap-0"):
                                            ui.label("Signature:").classes("text-xs text-gray-500 mb-1")
                                            ui.label().classes("border-b border-black w-full")
                            
                            # Render Quote Table dynamically sized based on rows
                            if quote_el:
                                current_items = p_data['items']
                                calc_h = HEADER_HEIGHT + (len(current_items) * ROW_HEIGHT) + (FOOTER_HEIGHT if is_last_page else 0)
                                
                                with ui.element('div').style(
                                    f"position: absolute; left: {quote_el['x']}px; top: {p_data['start_y']}px; "
                                    f"width: {quote_el['w']}px; height: {calc_h}px;"
                                ):
                                    with ui.column().classes("w-full h-full gap-0"):
                                        # Table Header
                                        with ui.row().classes("w-full border-b-2 border-gray-800 pb-2 mb-2 font-bold text-gray-900 text-sm"):
                                            ui.label("Service").classes("flex-1")
                                            ui.label("Teeth").classes("w-20 text-center")
                                            ui.label("Qty").classes("w-16 text-center")
                                            ui.label("Unit Price").classes("w-32 text-right")
                                        
                                        # Table Rows
                                        for item in current_items:
                                            i_data = item.get("item", {})
                                            name = i_data.get("name", "Unknown Service")
                                            qty = item.get("quantity", 1)
                                            price = i_data.get("price", "0.00")
                                            if len(str(price)) > 15: price = str(price)[:12] + "..."
                                            
                                            is_spec = i_data.get("is_specific", False)
                                            teeth_arr = item.get("teeth", [])
                                            teeth_str = ", ".join(map(str, teeth_arr)) if is_spec and teeth_arr else ""
                                            
                                            with ui.row().classes("w-full text-gray-800 mb-1 text-sm items-center"):
                                                ui.label(name).classes("flex-1 whitespace-normal line-clamp-2 leading-tight")
                                                ui.label(teeth_str).classes("w-20 text-center text-xs truncate")
                                                ui.label(str(qty)).classes("w-16 text-center")
                                                ui.label(f"${price}").classes("w-32 text-right truncate")
                                        
                                        # Table Footer
                                        if is_last_page:
                                            with ui.row().classes("w-full border-t border-gray-400 pt-2 mt-2 font-bold text-gray-900 text-sm"):
                                                ui.label("Total Amount").classes("flex-1 text-right pr-4")
                                                disp_total = str(total_amount)[:12] + "..." if len(str(total_amount)) > 15 else str(total_amount)
                                                ui.label(f"${disp_total}").classes("w-32 text-right truncate")

        self.dialog.open()