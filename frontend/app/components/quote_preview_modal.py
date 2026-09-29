import asyncio
from nicegui import ui
from datetime import datetime

A4_WIDTH = 794
A4_HEIGHT = 1123

class QuotePreviewModal:
    """
    A reusable modal for rendering an A4 document preview from preset elements and real quote data.
    Now supports instant headless export (direct to browser print dialog).
    """
    def __init__(self):
        self.dialog = ui.dialog()

    def _prepare_data(self, preset: dict, quote: dict):
        elements = preset.get("elements", [])
        margins = preset.get("margins", {"top": 96.0, "right": 96.0, "bottom": 96.0, "left": 96.0})
        
        patient = quote.get("patient", {})
        patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        if not patient_name:
            patient_name = "Unknown Client"
            
        raw_date = quote.get("created_at", "")
        if raw_date:
            try:
                dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                date_str = dt_obj.strftime("%d/%m/%Y")
            except ValueError:
                date_parts = raw_date.split("T")[0].split("-")
                if len(date_parts) == 3:
                    date_str = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                else:
                    date_str = raw_date
        else:
            date_str = "N/A"

        items = quote.get("quote_items", [])
        total_amount = quote.get("total_amount", "0.00")
        
        safe_name = patient_name.replace(" ", "_")
        filename = f"Quote_{safe_name}_{date_str.replace('/', '-')}.pdf"
        
        HEADER_HEIGHT = 40
        ROW_HEIGHT = 45 
        FOOTER_HEIGHT = 50
        
        quote_el = next((e for e in elements if e["type"] == "quote"), None)
        pages_data = []
        
        if quote_el and items:
            items_remaining = list(items)
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
            
        return pages_data, elements, patient_name, date_str, total_amount, quote_el, filename

    def _render_pages(self, pages_data, elements, patient_name, date_str, total_amount, quote_el, scale):
        scaled_w = A4_WIDTH * scale
        scaled_h = A4_HEIGHT * scale
        HEADER_HEIGHT = 40
        ROW_HEIGHT = 45
        FOOTER_HEIGHT = 50

        # Remove the box-shadow for the unscaled 1.0 version to prevent a border artifact in the PDF
        shadow_style = 'box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);' if scale < 1.0 else ''

        for i, p_data in enumerate(pages_data):
            is_last_page = p_data.get('is_last', True)
            
            with ui.element('div').classes("shrink-0").style(f'width: {scaled_w}px; height: {scaled_h}px; position: relative;'):
                with ui.element('div').style(
                    f'width: {A4_WIDTH}px; height: {A4_HEIGHT}px; '
                    f'transform: scale({scale}); transform-origin: top left; '
                    f'position: absolute; top: 0; left: 0; '
                    f'background-color: white; border-radius: 4px; {shadow_style}'
                ):
                    for el in elements:
                        if el["type"] == "quote": continue
                        if el["type"] == "sign" and not is_last_page: continue
                        if el["type"] not in ["sign", "quote"] and i > 0: continue
                        
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
                                    ui.element('img').props(f'src="{el["content"]}" draggable="false"').classes(
                                        f"w-full h-full pointer-events-none object-{fit_style}"
                                    ).style(f"object-position: {pos_x}% {pos_y}%;")
                                    
                            elif el["type"] == "sign":
                                with ui.column().classes("w-full h-full justify-end gap-0"):
                                    ui.label("Signature:").classes("text-xs text-gray-500 mb-1")
                                    ui.label().classes("border-b border-black w-full")
                    
                    if quote_el:
                        current_items = p_data['items']
                        calc_h = HEADER_HEIGHT + (len(current_items) * ROW_HEIGHT) + (FOOTER_HEIGHT if is_last_page else 0)
                        
                        with ui.element('div').style(
                            f"position: absolute; left: {quote_el['x']}px; top: {p_data['start_y']}px; "
                            f"width: {quote_el['w']}px; height: {calc_h}px;"
                        ):
                            with ui.column().classes("w-full h-full gap-0"):
                                with ui.row().classes("w-full border-b-2 border-gray-800 pb-2 mb-2 font-bold text-gray-900 text-sm flex flex-row"):
                                    ui.label("Service").classes("flex-1")
                                    ui.label("Teeth").classes("w-20 text-center")
                                    ui.label("Qty").classes("w-16 text-center")
                                    ui.label("Unit Price").classes("w-32 text-right")
                                
                                for item in current_items:
                                    i_data = item.get("item", {})
                                    name = i_data.get("name", "Unknown Service")
                                    qty = item.get("quantity", 1)
                                    price = i_data.get("price", "0.00")
                                    if len(str(price)) > 15: price = str(price)[:12] + "..."
                                    
                                    is_spec = i_data.get("is_specific", False)
                                    teeth_arr = item.get("teeth", [])
                                    teeth_str = ", ".join(map(str, teeth_arr)) if is_spec and teeth_arr else ""
                                    
                                    with ui.row().classes("w-full text-gray-800 mb-1 text-sm items-center flex flex-row"):
                                        ui.label(name).classes("flex-1 whitespace-normal line-clamp-2 leading-tight")
                                        ui.label(teeth_str).classes("w-20 text-center text-xs truncate")
                                        ui.label(str(qty)).classes("w-16 text-center")
                                        ui.label(f"${price}").classes("w-32 text-right truncate")
                                
                                if is_last_page:
                                    with ui.row().classes("w-full border-t border-gray-400 pt-2 mt-2 font-bold text-gray-900 text-sm flex flex-row"):
                                        ui.label("Total Amount").classes("flex-1 text-right pr-4")
                                        disp_total = str(total_amount)[:12] + "..." if len(str(total_amount)) > 15 else str(total_amount)
                                        ui.label(f"${disp_total}").classes("w-32 text-right truncate")

    async def process_direct(self, preset: dict, quote: dict, action: str):
        """Generates the DOM dynamically in the background and prints instantly"""
        pages_data, elements, patient_name, date_str, total_amount, quote_el, filename = self._prepare_data(preset, quote)
        
        container_id = f"quote_headless_{quote.get('id', 'new')}_{int(datetime.now().timestamp())}"
        container = ui.element('div').props(f'id="{container_id}"').classes('fixed top-[-20000px] left-[-20000px] bg-white z-0')
        
        with container:
            self._render_pages(pages_data, elements, patient_name, date_str, total_amount, quote_el, scale=1.0)
            
        await asyncio.sleep(0.2) # Allow NiceGUI to push DOM elements to the browser
        
        ui.notify("Preparing document...", type="info")
        if action == "download":
            ui.notify("Please select 'Save as PDF' as the destination in the print window.", type="warning", timeout=5000)

        js = f"""
            const el = document.getElementById('{container_id}');
            if (!el) return;
            
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            document.body.appendChild(iframe);
            
            const html = `
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.tailwindcss.com"></script>
                <link href="https://cdn.jsdelivr.net/npm/quasar@2/dist/quasar.prod.css" rel="stylesheet" type="text/css">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                    @page {{ size: auto; margin: 0mm; }}
                    body {{ 
                        margin: 0; 
                        font-family: 'Inter', sans-serif; 
                        -webkit-print-color-adjust: exact; 
                        print-color-adjust: exact; 
                        background-color: white;
                    }}
                    .shrink-0 {{ 
                        width: 794px !important; 
                        height: 1123px !important; 
                        page-break-after: always; 
                        overflow: hidden; 
                    }}
                    .shrink-0:last-child {{ page-break-after: auto; }}
                    .row {{ display: flex; flex-direction: row; }}
                    .column {{ display: flex; flex-direction: column; }}
                </style>
            </head>
            <body>
                ${{el.innerHTML}}
                <script>
                    setTimeout(() => {{ 
                        window.print(); 
                    }}, 800);
                </script>
            </body>
            </html>`;
            
            const doc = iframe.contentWindow.document;
            doc.open();
            doc.write(html);
            doc.close();
            
            setTimeout(() => {{ document.body.removeChild(iframe); }}, 10000);
        """
        
        await ui.run_javascript(js)
        container.delete() # Cleanup the invisible container after firing the script

    async def open(self, preset: dict, quote: dict):
        """Opens the visual modal for previewing"""
        self.dialog.clear()
        pages_data, elements, patient_name, date_str, total_amount, quote_el, filename = self._prepare_data(preset, quote)

        with self.dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden bg-gray-200 flex flex-col items-center'):
            with ui.row().classes('w-full justify-between items-center p-4 bg-white shadow-sm z-10'):
                ui.label('Document Preview').classes('text-xl font-bold text-gray-800')
                with ui.row().classes('gap-2 items-center'):
                    ui.button('Print', icon='print', on_click=lambda: self.process_direct(preset, quote, 'print')).props('outline color=primary')
                    ui.button('Download', icon='download', on_click=lambda: self.process_direct(preset, quote, 'download')).props('unelevated color=primary')
                    ui.button(icon='close', on_click=self.dialog.close).props('flat round dense text-color=gray-700')
            
            with ui.column().classes('w-full items-center p-8 overflow-auto h-[80vh] gap-8 bg-gray-200'):
                self._render_pages(pages_data, elements, patient_name, date_str, total_amount, quote_el, scale=0.85)

        self.dialog.open()