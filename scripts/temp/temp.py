from nicegui import ui
from collections import defaultdict

data = [
    {'category': 'Hardware', 'item': 'Laptop', 'price': 1200},
    {'category': 'Hardware', 'item': 'Mouse', 'price': 25},
    {'category': 'Software', 'item': 'IDE License', 'price': 150},
]

grouped = defaultdict(list)
for row in data:
    grouped[row['category']].append(row)

for category, items in grouped.items():
    with ui.expansion(f'{category} ({len(items)})', icon='folder').classes('w-full'):
        ui.table(
            columns=[
                {'name': 'item', 'label': 'Item', 'field': 'item'},
                {'name': 'price', 'label': 'Price ($)', 'field': 'price'},
            ],
            rows=items,
        ).classes('w-full')

ui.run(host='127.0.0.1', port=8001)