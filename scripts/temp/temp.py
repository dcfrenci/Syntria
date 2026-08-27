from pathlib import Path
from PIL import Image
from nicegui import ui

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMG_FILE = PROJECT_ROOT / 'frontend/app/assets/images/primary_stylized.jpeg'

BASE_W, BASE_H = 1000, 440

TEETH_DATA = [
    # FDI, X, Y, Width, Height
    ("55", 15, 60, 95, 155),
    ("54", 130, 60, 95, 160),
    ("53", 255, 18, 70, 205),
    ("52", 335, 38, 65, 185),
    ("51", 410, 32, 75, 190),
    ("61", 500, 32, 75, 190),
    ("62", 585, 38, 65, 185),
    ("63", 660, 18, 70, 205),
    ("64", 755, 60, 95, 160),
    ("65", 875, 60, 95, 155),
    ("85", 15, 230, 105, 150),
    ("84", 130, 230, 100, 160),
    ("83", 260, 230, 60, 165),
    ("82", 345, 240, 55, 138),
    ("81", 425, 240, 55, 138),
    ("71", 505, 240, 55, 138),
    ("72", 585, 240, 55, 138),
    ("73", 665, 230, 60, 165),
    ("74", 755, 230, 100, 160),
    ("75", 865, 230, 100, 150),
]

with Image.open(IMG_FILE) as img:
    img_w, img_h = img.size

scale_x = img_w / BASE_W
scale_y = img_h / BASE_H

# State to track clicked teeth
selected_teeth = set()

def build_svg_content() -> str:
    elements = []
    for tooth_id, x, y, w, h in TEETH_DATA:
        scaled_x = x * scale_x
        scaled_y = y * scale_y
        scaled_w = w * scale_x
        scaled_h = h * scale_y
        
        # 1. Main interactive tooth box
        elements.append(
            f'<rect id="{tooth_id}" '
            f'x="{scaled_x:.1f}" y="{scaled_y:.1f}" '
            f'width="{scaled_w:.1f}" height="{scaled_h:.1f}" '
            f'rx="{6 * scale_x:.1f}" fill="transparent" stroke="red" stroke-width="{2 * scale_x:.1f}" '
            f'pointer-events="all" cursor="pointer" />'
        )
        
        # 2. Bottom border line (toggled on selection)
        is_active = tooth_id in selected_teeth
        visibility = "visible" if is_active else "hidden"
        bottom_y = scaled_y + scaled_h
        
        elements.append(
            f'<line x1="{scaled_x:.1f}" y1="{bottom_y:.1f}" '
            f'x2="{(scaled_x + scaled_w):.1f}" y2="{bottom_y:.1f}" '
            f'stroke="black" stroke-width="{4 * scale_x:.1f}" stroke-linecap="round" '
            f'visibility="{visibility}" pointer-events="none" />'
        )
        
    return '\n'.join(elements)

# Interactive Image Component
interactive_img = ui.interactive_image(
    IMG_FILE,
    cross=False,
    content=build_svg_content(),
    sanitize=False,
).classes('w-full')

def handle_click(e):
    tooth_id = e.args.get('element_id')
    if not tooth_id:
        return
    
    # Toggle tooth selection
    if tooth_id in selected_teeth:
        selected_teeth.remove(tooth_id)
    else:
        selected_teeth.add(tooth_id)
        
    # Re-render SVG overlay
    interactive_img.content = build_svg_content()

interactive_img.on('svg:pointerdown', handle_click)

ui.run(host='127.0.0.1', port=8001)