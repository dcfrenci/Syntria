# Comprehensive NiceGUI Styling Reference: Tailwind, Quasar & CSS

NiceGUI gives every element **three** styling methods. Understanding the interplay between Tailwind CSS utility classes, Quasar's component props, and raw CSS is critical for building robust NiceGUI applications.

---

## 1. The Three Styling Methods

| Method | Purpose | Delimiter | Example |
| :--- | :--- | :--- | :--- |
| `.classes()` | Tailwind CSS utility classes | space | `.classes('text-xl font-bold')` |
| `.props()` | Quasar component props (framework-native styling/behavior) | space | `.props('outline round color=green')` |
| `.style()` | Raw inline CSS | **semicolon** (`;`) | `.style('color: #6E93D6; font-size: 200%')` |

All three accept `add=`, `remove=`, and `replace=` keyword arguments to modify existing values instead of overwriting:

```python
btn.classes(add='bg-green-600 text-white')
btn.classes(remove='bg-gray-400')
btn.classes(replace='w-full py-3 rounded-xl bg-blue-600 text-white')
```

Class-level defaults can also be set before instantiation:
```python
ui.button.default_classes('rounded-full')
ui.button.default_props('unelevated')
ui.button.default_style('font-weight: 600')
```

### Why `.props()` matters as much as `.classes()`
NiceGUI is built on the **Quasar Framework** (Vue-based). Many things people try to do with Tailwind classes are actually meant to be Quasar props (e.g., button color, density, outlining):
```python
ui.button('Submit').props('outline color=primary dense')
```

---

## 2. The `!important` Problem & CSS Layers

Quasar ships most of its component CSS with `!important`, which **beats Tailwind utility classes by default**. 

```python
# This often silently fails on Quasar components:
ui.button('Button').classes('bg-slate-100 text-slate-950')

# Fix: prepend ! to force specificity (Remove Defaults/Force Priority)
ui.button('Button').classes('!bg-slate-100 !text-slate-950')
```

As of **NiceGUI 3.0.0**, custom CSS added via `ui.add_css()` should go in the `components` or `utilities` layer, and still needs `!important` since Quasar's layer sits above it:

```python
ui.add_css('''
@layer utilities {
    .my-button-override {
        background-color: red !important;
    }
}
''')
```

---

## 3. Quasar Theme Colors vs. Tailwind Colors

NiceGUI/Quasar exposes semantic color classes tied to the app's theme palette, independent of Tailwind's color scale:

| Class | Maps to |
| :--- | :--- |
| `bg-primary`, `text-primary` | Theme primary color |
| `bg-secondary`, `text-secondary` | Theme secondary color |
| `bg-accent`, `text-accent` | Theme accent color |
| `bg-positive`, `bg-negative`, `bg-info`, `bg-warning` | Semantic states |
| `bg-dark` | Dark surface color |

Set/override the palette globally or per-page:
```python
ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E')
```
*Note: Mixing these with Tailwind's `bg-blue-500`-style classes is normal and expected.*

---

## 4. Syntax Modifiers & NiceGUI Specials

| Feature | Syntax / Prefix | Example | Description |
| :--- | :--- | :--- | :--- |
| **Force priority / Remove Defaults** | `!` | `!p-0`, `!bg-red-500` | Needed to beat Quasar's `!important` rules or strip default container paddings/gaps. |
| **Pseudo-classes** | `hover:`, `focus:`, `active:`, `disabled:` | `hover:bg-blue-600` | Applies styles on user interaction. |
| **List Modifiers** | `first:`, `last:`, `odd:`, `even:` | `odd:bg-gray-100` | Target child element positions. |
| **Group States** | `group-hover:`, `group-focus:` | `group-hover:opacity-100` | Style child when parent (`group`) is interacted with. |
| **Peer States** | `peer-checked:`, `peer-focus:` | `peer-checked:block` | Sibling-driven state. |
| **Breakpoints** | `sm:`, `md:`, `lg:`, `xl:`, `2xl:` | `md:flex-row` | Responsive design breakpoints. |
| **Dark Mode** | `dark:` | `dark:bg-zinc-900` | Applies when NiceGUI dark mode is enabled (`ui.dark_mode()`). |
| **Arbitrary Values** | `[...]` | `w-[320px]`, `top-[13px]` | Escape hatch for exact values. |

---

## 5. Layout & Positioning

| Category | Options / Patterns | Description |
| :--- | :--- | :--- |
| **Display** | `block`, `inline-block`, `inline`, `flex`, `inline-flex`, `grid`, `inline-grid`, `hidden` | Controls box rendering behavior. |
| **Position** | `static`, `fixed`, `absolute`, `relative`, `sticky` | Element positioning mode. |
| **Coordinates** | `top-`, `bottom-`, `left-`, `right-`, `inset-`<br>Values: `0`, `0.5`, `1`..`64`, `auto`, `full`, `1/2`.. | Placement along axes. |
| **Z-Index** | `z-0`, `z-10`, `z-20`, `z-30`, `z-40`, `z-50`, `z-auto` | Layer stack order. |
| **Overflow** | `overflow-auto`, `overflow-hidden`, `overflow-visible`, `overflow-scroll`, `overflow-x-auto`, `overflow-y-auto` | Content overflow behavior. |

---

## 6. Flexbox & Grid

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
| **Grid Rows** | `grid-rows-1` .. `grid-rows-6`, `grid-rows-none` | Number of explicit rows. |
| **Row Span** | `row-span-1` .. `row-span-6`, `row-span-full` | Row span of a grid item. |
| **Grid Auto Flow** | `grid-flow-row`, `grid-flow-col`, `grid-flow-dense` | Auto-placement algorithm. |
| **Auto Cols/Rows** | `auto-cols-auto`, `auto-cols-min`, `auto-cols-max`, `auto-cols-fr`, `auto-rows-*` | Sizing of implicitly-created tracks. |
| **Place Content** | `place-content-center`, `place-content-between`, ... | Shorthand for align+justify content (grid). |
| **Place Items** | `place-items-start`, `place-items-center`, ... | Shorthand for align+justify items. |
| **Place Self** | `place-self-auto`, `place-self-center`, ... | Per-item override. |
| **Order** | `order-1` .. `order-12`, `order-first`, `order-last`, `order-none` | Visual reordering without changing DOM. |

---

## 7. Spacing (Padding & Margin)

Spacing values: `0`, `0.5`, `1`, `1.5`, `2`, `2.5`, `3`, `4`, `5`, `6`, `8`, `10`, `12`, `16`, `20`, `24`, `32`, `40`, `48`, `56`, `64`, `px`, or arbitrary `[15px]`.

| Prefix | Target | Example |
| :--- | :--- | :--- |
| `p-` / `m-` | All sides | `p-4`, `m-2` |
| `pt-` / `mt-` | Top | `pt-6`, `mt-4` |
| `pb-` / `mb-` | Bottom | `pb-3`, `mb-8` |
| `pl-` / `ml-` | Left | `pl-2`, `ml-auto` |
| `pr-` / `mr-` | Right | `pr-4`, `mr-0` |
| `px-` / `mx-` | Horizontal (left & right) | `px-6`, `mx-auto` |
| `py-` / `my-` | Vertical (top & bottom) | `py-2`, `my-4` |
| `-m*` | Negative margins | `-mt-4`, `-mx-2` |
| `space-x-*`, `space-y-*` | Sibling separation | `space-y-4` |

---

## 8. Sizing (Width & Height)

| Dimension | Class Patterns | Options / Scale |
| :--- | :--- | :--- |
| **Width** | `w-*` | `0`..`96`, `auto`, `px`, `1/2`, `1/3`.. `full`, `screen`, `min`, `max`, `fit`, `[320px]` |
| **Height** | `h-*` | `0`..`96`, `auto`, `px`, `1/2`, `1/3`.. `full`, `screen`, `min`, `max`, `fit`, `[250px]` |
| **Max Width** | `max-w-*` | `none`, `xs`, `sm`, `md`, `lg`, `xl`, `2xl`..`7xl`, `full`, `screen-sm`..`screen-xl` |
| **Max Height**| `max-h-*` | `full`, `screen`, `min`, `max`, `fit`, `[400px]` |
| **Min W/H** | `min-w-*`, `min-h-*` | `0`, `full`, `min`, `max`, `fit` |
| **Aspect Ratio**| `aspect-*` | `auto`, `square`, `video`, `[4/3]` |

---

## 9. Typography

| Category | Options / Patterns |
| :--- | :--- |
| **Font Family** | `font-sans`, `font-serif`, `font-mono` |
| **Font Size** | `text-xs`, `text-sm`, `text-base`, `text-lg`.. `text-6xl` |
| **Font Weight** | `font-thin`, `font-light`, `font-normal`, `font-medium`, `font-semibold`, `font-bold`, `font-black` |
| **Line Height** | `leading-none`, `leading-tight`, `leading-snug`, `leading-normal`, `leading-relaxed`, `leading-loose`, `leading-{3..10}` |
| **Letter Spacing** | `tracking-tighter`, `tracking-tight`, `tracking-normal`, `tracking-wide`, `tracking-wider`, `tracking-widest` |
| **Alignment** | `text-left`, `text-center`, `text-right`, `text-justify` |
| **Colors** | `text-{color}-{50..950}` *(e.g. `text-slate-800`, `text-white`)* |
| **Decoration** | `underline`, `overline`, `line-through`, `no-underline` |
| **Transform** | `uppercase`, `lowercase`, `capitalize`, `normal-case` |
| **Overflow / Break** | `truncate`, `text-ellipsis`, `text-clip`, `break-normal`, `break-words`, `break-all` |
| **Whitespace** | `whitespace-normal`, `whitespace-nowrap`, `whitespace-pre`, `whitespace-pre-wrap` |
| **List Style** | `list-none`, `list-disc`, `list-decimal`, `list-inside`, `list-outside` |
| **Vertical Align** | `align-baseline`, `align-top`, `align-middle`, `align-bottom` |

---

## 10. Backgrounds & Borders

**Full color name list** used across `bg-`, `text-`, `border-`, `ring-`, `divide-`, `from-/via-/to-`:
`slate, gray, zinc, neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose` — each with shades `50–950`.

| Category | Class Pattern |
| :--- | :--- |
| **Background Color** | `bg-{color}-{50..950}` |
| **Background Opacity**| `bg-opacity-{0..100}` |
| **Background Gradient**| `bg-gradient-to-{t,tr,r,br,b,bl,l,tl}`, `from-{color}`, `via-{color}`, `to-{color}` |
| **Bg Position/Size** | `bg-center`, `bg-cover`, `bg-contain`, `bg-no-repeat` |
| **Border Width** | `border`, `border-{t|b|l|r|x|y}`, `border-{0|2|4|8}` |
| **Border Color** | `border-{color}-{50..950}` |
| **Border Radius** | `rounded`, `rounded-{sm|md|lg|xl|2xl|3xl|full|none}`, `rounded-{t|b|l|r|tl|tr|bl|br}-*` |
| **Ring (Focus)** | `ring`, `ring-{1,2,4,8}`, `ring-{color}`, `ring-offset-{0..8}` |
| **Divide (Siblings)**| `divide-x`, `divide-y`, `divide-{color}` |

---

## 11. Effects & Interactivity

| Category | Options / Values |
| :--- | :--- |
| **Shadow** | `shadow-none`, `shadow-sm`, `shadow`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-2xl`, `shadow-inner` |
| **Opacity** | `opacity-0`, `opacity-10`, `opacity-20`, `opacity-50`, `opacity-75`, `opacity-100` |
| **Transform** | `scale-{0..150}`, `rotate-{0..180}`, `translate-x/y-*`, `skew-x/y-*` |
| **Filters** | `blur-*`, `brightness-*`, `contrast-*`, `grayscale`, `sepia`, `saturate-*`, `drop-shadow-*` |
| **Backdrop Filters** | `backdrop-blur-*`, `backdrop-brightness-*` |
| **Cursor** | `cursor-auto`, `cursor-default`, `cursor-pointer`, `cursor-wait`, `cursor-text`, `cursor-not-allowed` |
| **User Select**| `select-none`, `select-text`, `select-all`, `select-auto` |
| **Pointer Events** | `pointer-events-none`, `pointer-events-auto` |
| **Transitions** | `transition`, `transition-all`, `transition-colors`, `transition-opacity`, `transition-transform` |
| **Duration & Timing**| `duration-{75..1000}`, `ease-linear`, `ease-in`, `ease-out`, `ease-in-out` |
| **Animation** | `animate-none`, `animate-spin`, `animate-ping`, `animate-pulse`, `animate-bounce` |
| **Accessibility** | `sr-only`, `not-sr-only` |

---

## 12. NiceGUI-Specific Patterns Cheatsheet

```python
from nicegui import ui

# 1. Basic Tailwind styling
ui.label('Dashboard').classes('text-2xl font-bold text-gray-800')

# 2. Reset NiceGUI/Quasar default padding & gaps
with ui.row().classes('!gap-0 !p-0 w-full items-center justify-between'):
    ui.label('Logo')
    ui.button('Logout')

# 3. Combine Tailwind classes with Quasar props (the normal pattern)
ui.button('Submit').props('outline round color=primary').classes('shadow-lg')

# 4. Use .style() for anything Tailwind/Quasar doesn't expose
ui.label('Custom').style('color: #6E93D6; font-size: 200%; font-weight: 300')

# 5. Fight Quasar's !important when Tailwind silently fails
ui.button('Button').classes('!bg-slate-100 !text-slate-950')

# 6. Theme-aware color instead of a fixed Tailwind color
ui.icon('star').classes('text-primary')

# 7. Conditional styling
btn = ui.button('Submit')
btn.classes(add='bg-green-600 text-white' if is_valid else 'bg-gray-400')
btn.classes(replace='w-full py-3 rounded-xl bg-blue-600 text-white')

# 8. Responsive + hover + shadow combo
ui.card().classes('w-full md:w-1/2 p-6 shadow-md hover:shadow-xl transition-shadow')

# 9. Global CSS override respecting NiceGUI 3.0+ layers
ui.add_css('''
@layer utilities {
    .brand-btn { background-color: #ff4081 !important; }
}
''')
ui.button('Buy').classes('brand-btn')
```

---

## 13. Reference Links

1. **NiceGUI Styling & Appearance** — [nicegui.io/documentation/section_styling_appearance](https://nicegui.io/documentation/section_styling_appearance)
2. **Quasar Framework Palette & Style** — [quasar.dev/style/color-palette](https://quasar.dev/style/color-palette)
3. **Tailwind CSS Docs** — [tailwindcss.com/docs](https://tailwindcss.com/docs)
