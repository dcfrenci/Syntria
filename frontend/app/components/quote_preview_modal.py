import asyncio
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from nicegui import ui

from api_client.base import BASE_URL
from components.images import image_src

# Layout Constants (96 DPI A4 Standard)
A4_WIDTH_PX = 794
A4_HEIGHT_PX = 1123

HEADER_HEIGHT_PX = 40
ROW_HEIGHT_PX = 45
FOOTER_HEIGHT_PX = 50
DEFAULT_MARGIN_PX = 96.0


# --- Utility Helpers ---

def format_currency(amount: Any) -> str:
    """Format numerical values into EUR currency format safely."""
    try:
        val = Decimal(str(amount or 0))
        return f"€{val:,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return f"€{amount}"


def format_date(raw_date: Optional[str]) -> str:
    """Parse ISO date strings into DD/MM/YYYY string format."""
    if not raw_date:
        return "N/A"
    try:
        dt_obj = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
        return dt_obj.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        date_parts = str(raw_date).split("T")[0].split("-")
        if len(date_parts) == 3:
            return f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
        return str(raw_date)


def get_page_margins_css(margins: Dict[str, Any]) -> str:
    """Helper for generating inline CSS page padding from margin definitions."""
    top = margins.get("top", 20)
    right = margins.get("right", 20)
    bottom = margins.get("bottom", 20)
    left = margins.get("left", 20)
    return f"padding: {top}mm {right}mm {bottom}mm {left}mm;"


# --- Primary Modal Class ---

class QuotePreviewModal:
    """
    A reusable modal and print service for rendering A4 document previews 
    from customizable preset templates and dynamic quote data.
    """

    def __init__(self) -> None:
        self.dialog = ui.dialog()

    def _prepare_data(
        self, preset: Dict[str, Any], quote: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, str, str, Optional[Dict[str, Any]]]:
        """Calculates item pagination splits across A4 pages and prepares metadata."""
        elements = preset.get("elements", [])
        margins = preset.get(
            "margins",
            {
                "top": DEFAULT_MARGIN_PX,
                "right": DEFAULT_MARGIN_PX,
                "bottom": DEFAULT_MARGIN_PX,
                "left": DEFAULT_MARGIN_PX,
            },
        )

        patient = quote.get("patient") or {}
        patient_name = (
            f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            or "Unknown Client"
        )

        date_str = format_date(quote.get("created_at"))
        total_amount = format_currency(quote.get("total_amount", "0.00"))

        quote_el = next((e for e in elements if e.get("type") == "quote"), None)
        pages_data: List[Dict[str, Any]] = []
        items = quote.get("quote_items", [])

        if quote_el and items:
            items_remaining = list(items)
            avail_first = A4_HEIGHT_PX - float(margins.get("bottom", DEFAULT_MARGIN_PX)) - float(quote_el.get("y", 0))
            max_items_first = max(0, int((avail_first - HEADER_HEIGHT_PX - FOOTER_HEIGHT_PX) // ROW_HEIGHT_PX))

            if max_items_first >= len(items_remaining):
                pages_data.append({
                    "items": items_remaining,
                    "is_last": True,
                    "start_y": quote_el.get("y", 0),
                })
                items_remaining = []
            else:
                if max_items_first > 0:
                    pages_data.append({
                        "items": items_remaining[:max_items_first],
                        "is_last": False,
                        "start_y": quote_el.get("y", 0),
                    })
                    items_remaining = items_remaining[max_items_first:]
                else:
                    pages_data.append({
                        "items": [],
                        "is_last": False,
                        "start_y": quote_el.get("y", 0),
                    })

            top_margin = float(margins.get("top", DEFAULT_MARGIN_PX))
            avail_subsequent = A4_HEIGHT_PX - float(margins.get("bottom", DEFAULT_MARGIN_PX)) - top_margin
            max_items_subsequent = max(1, int((avail_subsequent - HEADER_HEIGHT_PX - FOOTER_HEIGHT_PX) // ROW_HEIGHT_PX))

            while items_remaining:
                if max_items_subsequent >= len(items_remaining):
                    pages_data.append({
                        "items": items_remaining,
                        "is_last": True,
                        "start_y": top_margin,
                    })
                    items_remaining = []
                else:
                    pages_data.append({
                        "items": items_remaining[:max_items_subsequent],
                        "is_last": False,
                        "start_y": top_margin,
                    })
                    items_remaining = items_remaining[max_items_subsequent:]
        else:
            pages_data.append({"items": [], "is_last": True, "start_y": 0})

        return pages_data, elements, patient_name, date_str, total_amount, quote_el

    def _render_pages(
        self,
        pages_data: List[Dict[str, Any]],
        elements: List[Dict[str, Any]],
        patient_name: str,
        date_str: str,
        total_amount: str,
        quote_el: Optional[Dict[str, Any]],
        scale: float = 1.0,
    ) -> None:
        """Renders page elements dynamically with CSS absolute positioning."""
        scaled_w = A4_WIDTH_PX * scale
        scaled_h = A4_HEIGHT_PX * scale
        shadow_style = "box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);" if scale < 1.0 else ""

        for page_idx, p_data in enumerate(pages_data):
            is_last_page = p_data.get("is_last", True)

            with ui.element("div").classes("shrink-0").style(
                f"width: {scaled_w}px; height: {scaled_h}px; position: relative;"
            ):
                with ui.element("div").style(
                    f"width: {A4_WIDTH_PX}px; height: {A4_HEIGHT_PX}px; "
                    f"transform: scale({scale}); transform-origin: top left; "
                    f"position: absolute; top: 0; left: 0; "
                    f"background-color: white; border-radius: 4px; {shadow_style}"
                ):
                    for el in elements:
                        el_type = el.get("type")
                        if el_type == "quote":
                            continue
                        if el_type == "sign" and not is_last_page:
                            continue
                        if el_type not in ["sign", "quote"] and page_idx > 0:
                            continue

                        x, y = el.get("x", 0), el.get("y", 0)
                        w, h = el.get("w", 100), el.get("h", 50)

                        with ui.element("div").style(
                            f"position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px;"
                        ):
                            if el_type in ["text", "client", "date"]:
                                f_size = el.get("font_size", 14)
                                f_weight = "bold" if el.get("font_bold") else "normal"
                                f_style = "italic" if el.get("font_italic") else "normal"
                                style_str = f"font-size: {f_size}px; font-weight: {f_weight}; font-style: {f_style};"

                                if el_type == "text":
                                    ui.label(el.get("content", "")).classes(
                                        "w-full h-full whitespace-pre-wrap text-gray-800"
                                    ).style(style_str)
                                elif el_type == "client":
                                    ui.label(patient_name).classes(
                                        "w-full h-full text-gray-900"
                                    ).style(style_str)
                                elif el_type == "date":
                                    ui.label(f"Date: {date_str}").classes(
                                        "w-full h-full text-gray-800"
                                    ).style(style_str)

                            elif el_type == "image":
                                img_content = el.get("content", "")
                                if img_content:
                                    fit_style = el.get("image_fit", "contain")
                                    pos_x = el.get("image_pos_x", 50)
                                    pos_y = el.get("image_pos_y", 50)
                                    src = image_src(img_content) if callable(image_src) else img_content
                                    ui.element("img").props(
                                        f'src="{src}" draggable="false"'
                                    ).classes(
                                        f"w-full h-full pointer-events-none object-{fit_style}"
                                    ).style(
                                        f"object-position: {pos_x}% {pos_y}%;"
                                    )

                            elif el_type == "sign":
                                with ui.column().classes("w-full h-full justify-end gap-0"):
                                    ui.label("Signature:").classes("text-xs text-gray-500 mb-1")
                                    ui.label().classes("border-b border-black w-full")

                    if quote_el:
                        current_items = p_data.get("items", [])
                        calc_h = (
                            HEADER_HEIGHT_PX
                            + (len(current_items) * ROW_HEIGHT_PX)
                            + (FOOTER_HEIGHT_PX if is_last_page else 0)
                        )

                        with ui.element("div").style(
                            f"position: absolute; left: {quote_el.get('x', 0)}px; top: {p_data.get('start_y', 0)}px; "
                            f"width: {quote_el.get('w', 700)}px; height: {calc_h}px;"
                        ):
                            with ui.column().classes("w-full h-full gap-0"):
                                with ui.row().classes(
                                    "w-full border-b-2 border-gray-800 pb-2 mb-2 font-bold text-gray-900 text-sm flex flex-row"
                                ):
                                    ui.label("Service").classes("flex-1")
                                    ui.label("Teeth").classes("w-20 text-center")
                                    ui.label("Qty").classes("w-16 text-center")
                                    ui.label("Unit Price").classes("w-32 text-right")

                                for item in current_items:
                                    i_data = item.get("item") or {}
                                    name = i_data.get("name", "Unknown Service")
                                    qty = item.get("quantity", 1)

                                    is_spec = i_data.get("is_specific", False)
                                    teeth_arr = item.get("teeth", [])
                                    teeth_str = (
                                        ", ".join(map(str, teeth_arr))
                                        if is_spec and teeth_arr
                                        else "-"
                                    )

                                    raw_price = item.get("unit_price")
                                    if raw_price is None:
                                        raw_price = i_data.get("price", "0.00")
                                    price_formatted = format_currency(raw_price)

                                    with ui.row().classes(
                                        "w-full text-gray-800 mb-1 text-sm items-center flex flex-row"
                                    ):
                                        ui.label(name).classes(
                                            "flex-1 whitespace-normal line-clamp-2 leading-tight"
                                        )
                                        ui.label(teeth_str).classes(
                                            "w-20 text-center text-xs truncate"
                                        )
                                        ui.label(str(qty)).classes("w-16 text-center")
                                        ui.label(price_formatted).classes(
                                            "w-32 text-right truncate"
                                        )

                                if is_last_page:
                                    with ui.row().classes(
                                        "w-full border-t border-gray-400 pt-2 mt-2 font-bold text-gray-900 text-sm flex flex-row"
                                    ):
                                        ui.label("Total Amount").classes("flex-1 text-right pr-4")
                                        ui.label(total_amount).classes("w-32 text-right truncate")

    async def process_direct(
        self, preset: Dict[str, Any], quote: Dict[str, Any], action: str = "print"
    ) -> None:
        """Renders headless DOM in background and triggers native print/download dialog."""
        pages_data, elements, patient_name, date_str, total_amount, quote_el = self._prepare_data(
            preset, quote
        )

        quote_id = quote.get("id", "new")
        container_id = f"quote_headless_{quote_id}_{int(datetime.now().timestamp())}"
        container = (
            ui.element("div")
            .props(f'id="{container_id}"')
            .classes("fixed top-[-20000px] left-[-20000px] bg-white z-0")
        )

        with container:
            self._render_pages(
                pages_data,
                elements,
                patient_name,
                date_str,
                total_amount,
                quote_el,
                scale=1.0,
            )

        await asyncio.sleep(0.2)

        ui.notify("Preparing document...", type="info")
        if action == "download":
            ui.notify(
                "Please select 'Save as PDF' as the destination in the print window.",
                type="warning",
                timeout=5000,
            )

        js = f"""
            const el = document.getElementById('{container_id}');
            if (!el) return;
            
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            document.body.appendChild(iframe);
            
            const appStyles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
                .map(n => n.tagName === 'LINK' ? `<link rel="stylesheet" href="${{n.href}}">` : n.outerHTML)
                .join('\\n');
            
            const html = `
            <!DOCTYPE html>
            <html>
            <head>
                ${{appStyles}}
                <style>
                    @page {{ size: auto; margin: 0mm; }}
                    body {{ 
                        margin: 0; 
                        font-family: 'Inter', sans-serif; 
                        -webkit-print-color-adjust: exact; 
                        print-color-adjust: exact; 
                        background-color: white;
                    }}
                    .shrink-0 {{ 
                        width: {A4_WIDTH_PX}px !important; 
                        height: {A4_HEIGHT_PX}px !important; 
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
                    window.addEventListener('load', () => {{ setTimeout(() => window.print(), 300); }});
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
        container.delete()

    async def open(self, preset: Dict[str, Any], quote: Dict[str, Any]) -> None:
        """Opens the visual modal dialog for interactive document preview."""
        self.dialog.clear()
        pages_data, elements, patient_name, date_str, total_amount, quote_el = self._prepare_data(
            preset, quote
        )

        with self.dialog, ui.card().classes(
            "w-full max-w-5xl p-0 overflow-hidden bg-gray-200 flex flex-col items-center"
        ):
            with ui.row().classes(
                "w-full justify-between items-center p-4 bg-white shadow-sm z-10"
            ):
                ui.label("Document Preview").classes("text-xl font-bold text-gray-800")
                with ui.row().classes("gap-2 items-center"):
                    ui.button(
                        "Print",
                        icon="print",
                        on_click=lambda: self.process_direct(preset, quote, "print"),
                    ).props("outline color=primary")
                    ui.button(
                        "Download",
                        icon="download",
                        on_click=lambda: self.process_direct(preset, quote, "download"),
                    ).props("unelevated color=primary")
                    ui.button(icon="close", on_click=self.dialog.close).props(
                        "flat round dense text-color=gray-700"
                    )

            with ui.column().classes(
                "w-full items-center p-8 overflow-auto h-[80vh] gap-8 bg-gray-200"
            ):
                self._render_pages(
                    pages_data,
                    elements,
                    patient_name,
                    date_str,
                    total_amount,
                    quote_el,
                    scale=0.85,
                )

        self.dialog.open()


# --- Backward Compatibility Functional Wrapper ---

def show_quote_preview_modal(
    quote: Dict[str, Any], preset: Dict[str, Any], title: str = "Print Preview"
) -> None:
    """Procedural wrapper for directly opening the quote preview modal."""
    modal = QuotePreviewModal()
    asyncio.create_task(modal.open(preset, quote))