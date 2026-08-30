from nicegui import ui

from PIL import Image

def teeth_selection(on_save_callback):

    with ui.dialog() as dialog, ui.card().classes(
        "max-w-1000 w-2/3 flex flex-col items-center select-none"
    ):

        selected_teeth = set()

        def generate_teeth_svg(
            teeth_data: list, img_path: str, base_w: int, base_h: int
        ) -> str:

            with Image.open(img_path) as img:
                img_w, img_h = img.size

            scale_x = img_w / base_w
            scale_y = img_h / base_h

            elements = []
            for tooth_id, x, y, w, h in teeth_data:
                sx = x * scale_x
                sy = y * scale_y
                sw = w * scale_x
                sh = h * scale_y

                is_upper = tooth_id[0] in {"1", "2", "5", "6"}

                # Center horizontally
                text_x = sx + (sw / 2)

                # Upper Arch: line at box top (sy), number above the line (sy - offset)
                # Lower Arch: line at box bottom (sy + sh), number below the line (sy + sh + offset)
                if is_upper:
                    line_y = sy
                    text_y = sy - (10 * scale_y)
                else:
                    line_y = sy + sh
                    text_y = (sy + sh) + (14 * scale_y)

                # 1. Main interactive bounding box (red border removed/transparent)
                elements.append(
                    f'<rect id="{tooth_id}" '
                    f'x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                    f'rx="{6 * scale_x:.1f}" fill="rgba(0,0,0,0.001)" stroke="none" '
                    f'pointer-events="all" cursor="pointer" />'
                )

                # 2. Non-clickable number outside the arch
                elements.append(
                    f'<text x="{text_x:.1f}" y="{text_y:.1f}" '
                    f'font-size="{12 * scale_y:.1f}" font-weight="bold" fill="#333333" '
                    f'text-anchor="middle" dominant-baseline="central" pointer-events="none">{tooth_id}</text>'
                )

                # 3. Black line on the border
                is_active = tooth_id in selected_teeth
                visibility = "visible" if is_active else "hidden"
                elements.append(
                    f'<line x1="{sx:.1f}" y1="{line_y:.1f}" x2="{(sx + sw):.1f}" y2="{line_y:.1f}" '
                    f'stroke="black" stroke-width="{3 * scale_x:.1f}" stroke-linecap="round" '
                    f'visibility="{visibility}" pointer-events="none" />'
                )

                elements.append("<style>svg { overflow: visible !important; }</style>")

            return "\n".join(elements)

        # Toggle switch
        primary_switch = ui.switch("Show Primary Dentition", value=False)

        # Permanent Dentition
        PERMANENT_IMG = "app/assets/images/permanent_stylized.jpeg"
        PERMANENT_BASE_W, PERMANENT_BASE_H = 1000, 475
        PERMANENT_TEETH = [
            # Upper arch (FDI: 17 to 27)
            ("17", 15, 25, 107, 215),
            ("16", 122, 25, 109, 215),
            ("15", 231, 25, 52, 215),
            ("14", 283, 25, 51, 215),
            ("13", 334, 25, 55, 215),
            ("12", 389, 25, 50, 215),
            ("11", 439, 25, 64, 215),
            ("21", 503, 25, 67, 215),
            ("22", 570, 25, 50, 215),
            ("23", 620, 25, 54, 215),
            ("24", 674, 25, 52, 215),
            ("25", 726, 25, 52, 215),
            ("26", 778, 25, 94, 215),
            ("27", 872, 25, 105, 215),
            # Lower arch (FDI: 47 to 37)
            ("47", 15, 245, 110, 220),
            ("46", 125, 245, 106, 220),
            ("45", 231, 245, 56, 220),
            ("44", 287, 245, 56, 220),
            ("43", 343, 245, 62, 220),
            ("42", 405, 245, 48, 220),
            ("41", 453, 245, 51, 220),
            ("31", 504, 245, 51, 220),
            ("32", 555, 245, 49, 220),
            ("33", 604, 245, 61, 220),
            ("34", 665, 245, 58, 220),
            ("35", 723, 245, 55, 220),
            ("36", 778, 245, 92, 220),
            ("37", 870, 245, 107, 220),
        ]

        img_permanent = ui.interactive_image(
            PERMANENT_IMG,
            cross=False,
            content=generate_teeth_svg(
                PERMANENT_TEETH, PERMANENT_IMG, PERMANENT_BASE_W, PERMANENT_BASE_H
            ),
            sanitize=False,
        ).classes("w-full max-w-[1000px] mx-auto block select-none mb-[3.5%]")

        # Primary Dentition
        PRIMARY_IMG = "app/assets/images/primary_stylized.jpeg"
        PRIMARY_BASE_W, PRIMARY_BASE_H = 1000, 440
        PRIMARY_TEETH = [
            # Upper Arch (FDI: 55 to 65)
            ("55", 15, 15, 108, 210),
            ("54", 123, 15, 122, 210),
            ("53", 245, 15, 90, 210),
            ("52", 335, 15, 75, 210),
            ("51", 410, 15, 85, 210),
            ("61", 495, 15, 84, 210),
            ("62", 579, 15, 75, 210),
            ("63", 654, 15, 87, 210),
            ("64", 741, 15, 125, 210),
            ("65", 866, 15, 111, 210),
            # Lower Arch (FDI: 85 to 75)
            ("85", 15, 230, 108, 170),
            ("84", 123, 230, 122, 170),
            ("83", 245, 230, 90, 170),
            ("82", 335, 230, 75, 170),
            ("81", 410, 230, 85, 170),
            ("71", 495, 230, 84, 170),
            ("72", 579, 230, 75, 170),
            ("73", 654, 230, 87, 170),
            ("74", 741, 230, 125, 170),
            ("75", 866, 230, 111, 170),
        ]

        img_primary = ui.interactive_image(
            PRIMARY_IMG,
            cross=False,
            content=generate_teeth_svg(
                PRIMARY_TEETH, PRIMARY_IMG, PRIMARY_BASE_W, PRIMARY_BASE_H
            ),
            sanitize=False,
        ).classes("w-full max-w-[1000px] mx-auto block select-none")
        img_primary.set_visibility(False)

        # Switch callback for changing visibility
        def toggle_dentition(e):
            is_primary = e.value
            img_permanent.set_visibility(not is_primary)
            img_primary.set_visibility(is_primary)
            selected_teeth.clear()

        primary_switch.on_value_change(toggle_dentition)

        # Click handler
        def handle_tooth_click(e):
            tooth_id = e.args.get("element_id")
            if not tooth_id:
                return

            if tooth_id in selected_teeth:
                selected_teeth.remove(tooth_id)
            else:
                selected_teeth.add(tooth_id)

            # Update SVG content using set_content
            img_permanent.set_content(
                generate_teeth_svg(
                    PERMANENT_TEETH, PERMANENT_IMG, PERMANENT_BASE_W, PERMANENT_BASE_H
                )
            )
            img_primary.set_content(
                generate_teeth_svg(
                    PRIMARY_TEETH, PRIMARY_IMG, PRIMARY_BASE_W, PRIMARY_BASE_H
                )
            )

        img_permanent.on("svg:pointerdown", handle_tooth_click)
        img_primary.on("svg:pointerdown", handle_tooth_click)

        with ui.row().classes("w-full justify-end mt-4 gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("outline")
            ui.button(
                "",
                on_click=lambda: [
                    on_save_callback(selected_teeth),
                    dialog.close(),
                ],
            )

    return dialog
