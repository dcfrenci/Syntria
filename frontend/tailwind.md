# NiceGUI Tailwind CSS `.classes()` Reference Guide

NiceGUI uses Tailwind CSS under the hood to style elements via `.classes()`. Below is the complete structured reference organized by category.

---

## 1. Syntax Modifiers & NiceGUI Specials

| Feature | Syntax / Prefix | Example / Usage | Description |
| :--- | :--- | :--- | :--- |
| **Remove Defaults** | `!` | `!p-0`, `!gap-0` | NiceGUI/Quasar adds default padding and gaps to containers. Prepend `!` to strip them. |
| **Pseudo-classes** | `hover:`, `focus:`, `active:`, `disabled:` | `hover:bg-blue-600` | Applies styles on user interaction. |
| **List Modifiers** | `first:`, `last:`, `odd:`, `even:` | `odd:bg-gray-100` | Target child element positions. |
| **Group States** | `group-hover:`, `group-focus:` | `group-hover:opacity-100` | Style child when parent (`group`) is hovered. |
| **Breakpoints** | `sm:`, `md:`, `lg:`, `xl:`, `2xl:` | `md:flex-row` | Responsive design breakpoints. |
| **Dark Mode** | `dark:` | `dark:bg-zinc-900` | Applies when dark mode is enabled. |

---

## 2. Layout & Positioning

| Category | Options / Patterns | Description |
| :--- | :--- | :--- |
| **Display** | `block`, `inline-block`, `inline`, `flex`, `inline-flex`, `grid`, `inline-grid`, `hidden` | Controls box rendering behavior. |
| **Position** | `static`, `fixed`, `absolute`, `relative`, `sticky` | Element positioning mode. |
| **Coordinates** | `top-`, `bottom-`, `left-`, `right-`, `inset-`<br>Values: `0`, `0.5`, `1`..`64`, `auto`, `full`, `1/2`, `1/3`, `1/4` | Placement along axes (e.g. `top-4`, `inset-x-0`). |
| **Z-Index** | `z-0`, `z-10`, `z-20`, `z-30`, `z-40`, `z-50`, `z-auto` | Layer stack order. |
| **Overflow** | `overflow-auto`, `overflow-hidden`, `overflow-visible`, `overflow-scroll`, `overflow-x-auto`, `overflow-y-auto` | Content overflow behavior. |

---

## 3. Flexbox & Grid

| Category | Options / Patterns | Description |
| :--- | :--- | :--- |
| **Direction** | `flex-row`, `flex-row-reverse`, `flex-col`, `flex-col-reverse` | Flex axis direction. |
| **Wrapping** | `flex-wrap`, `flex-wrap-reverse`, `flex-nowrap` | Multi-line flex behavior. |
| **Grow & Shrink**| `flex-1`, `flex-auto`, `flex-initial`, `flex-none`, `grow`, `grow-0`, `shrink`, `shrink-0` | Item expansion & shrinking. |
| **Justify Content** | `justify-start`, `justify-end`, `justify-center`, `justify-between`, `justify-around`, `justify-evenly` | Alignment along main axis. |
| **Align Items** | `items-start`, `items-end`, `items-center`, `items-baseline`, `items-stretch` | Alignment along cross axis. |
| **Align Self** | `self-auto`, `self-start`, `self-end`, `self-center`, `self-stretch`, `self-baseline` | Individual item cross-axis alignment. |
| **Gap** | `gap-0` to `gap-32`, `gap-x-*`, `gap-y-*` | Spacing between children. |
| **Grid Columns** | `grid-cols-1` through `grid-cols-12`, `grid-cols-none` | Number of columns in grid layout. |
| **Grid Span** | `col-span-1` through `col-span-12`, `col-span-full` | Column span of a grid item. |

---

## 4. Spacing (Padding & Margin)

Spacing values: `0`, `0.5`, `1`, `1.5`, `2`, `2.5`, `3`, `4`, `5`, `6`, `8`, `10`, `12`, `16`, `20`, `24`, `32`, `40`, `48`, `56`, `64`, `px`, or arbitrary `[15px]`.

| Prefix | Target | Example |
| :--- | :--- | :--- |
| `p-` / `m-` | All sides | `p-4`, `m-2` |
| `pt-` / `mt-` | Top | `pt-6`, `mt-4` |
| `pb-` / `mb-` | Bottom | `pb-3`, `mb-8` |
| `pl-` / `ml-` | Left | `pl-2`, `ml-auto` |
| `pr-` / `mr-` | Right | `pr-4`, `mr-0` |
| `px-` / `mx-` | Horizontal (left & right) | `px-6`, `mx-auto` (centering) |
| `py-` / `my-` | Vertical (top & bottom) | `py-2`, `my-4` |
| `-m*` | Negative margins | `-mt-4`, `-mx-2` |
| `space-x-*`, `space-y-*` | Sibling separation | `space-y-4` |

---

## 5. Sizing (Width & Height)

| Dimension | Class Patterns | Options / Scale |
| :--- | :--- | :--- |
| **Width** | `w-*` | `0`..`96`, `auto`, `px`, `1/2`, `1/3`, `2/3`, `1/4`, `3/4`, `full`, `screen`, `min`, `max`, `fit`, `[320px]` |
| **Height** | `h-*` | `0`..`96`, `auto`, `px`, `1/2`, `1/3`, `2/3`, `1/4`, `3/4`, `full`, `screen`, `min`, `max`, `fit`, `[250px]` |
| **Max Width** | `max-w-*` | `none`, `xs`, `sm`, `md`, `lg`, `xl`, `2xl`, `3xl`, `4xl`, `5xl`, `6xl`, `7xl`, `full`, `screen-sm`..`screen-xl` |
| **Max Height**| `max-h-*` | `full`, `screen`, `min`, `max`, `fit`, `[400px]` |

---

## 6. Typography

| Category | Options / Patterns |
| :--- | :--- |
| **Font Size** | `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, `text-3xl`, `text-4xl`, `text-5xl`, `text-6xl` |
| **Font Weight** | `font-thin`, `font-extralight`, `font-light`, `font-normal`, `font-medium`, `font-semibold`, `font-bold`, `font-extrabold`, `font-black` |
| **Alignment** | `text-left`, `text-center`, `text-right`, `text-justify` |
| **Colors** | `text-{color}-{50..950}` *(e.g. `text-slate-800`, `text-blue-500`, `text-red-600`, `text-white`)* |
| **Decoration** | `underline`, `overline`, `line-through`, `no-underline` |
| **Transform** | `uppercase`, `lowercase`, `capitalize`, `normal-case` |
| **Overflow** | `truncate` (ellipsis + single line), `text-ellipsis`, `text-clip` |

---

## 7. Backgrounds & Borders

| Category | Class Pattern | Examples |
| :--- | :--- | :--- |
| **Background Color** | `bg-{color}-{50..950}` | `bg-white`, `bg-gray-50`, `bg-indigo-600`, `bg-emerald-100` |
| **Background Opacity**| `bg-opacity-{0..100}` | `bg-opacity-50`, `bg-opacity-75` |
| **Border Width** | `border`, `border-{t|b|l|r|x|y}`, `border-{0|2|4|8}` | `border`, `border-b-2`, `border-t-0` |
| **Border Color** | `border-{color}-{50..950}` | `border-gray-300`, `border-red-500`, `border-transparent` |
| **Border Radius** | `rounded`, `rounded-{sm|md|lg|xl|2xl|3xl|full|none}`<br>`rounded-{t|b|l|r|tl|tr|bl|br}-*` | `rounded-lg`, `rounded-full`, `rounded-t-md` |

---

## 8. Effects & Interactivity

| Category | Options / Values |
| :--- | :--- |
| **Shadow** | `shadow-none`, `shadow-sm`, `shadow`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-2xl`, `shadow-inner` |
| **Opacity** | `opacity-0`, `opacity-10`, `opacity-20`, `opacity-50`, `opacity-75`, `opacity-100` |
| **Cursor** | `cursor-auto`, `cursor-default`, `cursor-pointer`, `cursor-wait`, `cursor-text`, `cursor-move`, `cursor-not-allowed` |
| **User Select**| `select-none`, `select-text`, `select-all`, `select-auto` |
| **Transitions** | `transition`, `transition-all`, `transition-colors`, `transition-opacity`, `transition-transform` |
| **Duration** | `duration-75`, `duration-100`, `duration-150`, `duration-200`, `duration-300`, `duration-500`, `duration-700`, `duration-1000` |

---

## 9. NiceGUI `.classes()` Method Cheatsheet

```python
from nicegui import ui

# 1. Basic styling
ui.label('Dashboard').classes('text-2xl font-bold text-gray-800')

# 2. Reset NiceGUI defaults with "!"
with ui.row().classes('!gap-0 !p-0 w-full items-center justify-between'):
    ui.label('Logo')
    ui.button('Logout')

# 3. Interactive hover & responsive layout
ui.card().classes('w-full md:w-1/2 p-6 shadow-md hover:shadow-xl transition-shadow')

# 4. Conditional styling (add / remove / replace)
btn = ui.button('Submit')
btn.classes(add='bg-green-600 text-white' if is_valid else 'bg-gray-400')
btn.classes(replace='w-full py-3 rounded-xl bg-blue-600 text-white')