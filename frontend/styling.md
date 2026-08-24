# NiceGUI Styling Reference: Tailwind, Quasar & CSS

NiceGUI gives every element **three** styling methods, not just one. The original schema only documented `.classes()` (Tailwind). This is incomplete on its own — Quasar's component CSS uses `!important` internally and frequently **overrules Tailwind utility classes silently**, which is the #1 confusion point for NiceGUI users. This reference fixes that gap and fills in missing Tailwind categories.

---

## 0. The Three Styling Methods (critical, was missing entirely)

| Method | Purpose | Delimiter | Example |
| :--- | :--- | :--- | :--- |
| `.classes()` | Tailwind CSS utility classes | space | `.classes('text-xl font-bold')` |
| `.props()` | Quasar component props (framework-native styling/behavior) | space | `.props('outline round color=green')` |
| `.style()` | Raw inline CSS | **semicolon** (`;`), not space | `.style('color: #6E93D6; font-size: 200%')` |

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
NiceGUI is built on the **Quasar Framework** (Vue-based), not raw HTML+Tailwind. Many things people try to do with Tailwind classes are actually meant to be Quasar props — e.g. button color, density, outlining:
```python
ui.button('Submit').props('outline color=primary dense')
```
Quasar's full prop reference lives at quasar.dev, not in Tailwind docs — see link at the bottom.

---

## 1. The `!important` Problem (critical, was missing)

Quasar ships most of its component CSS with `!important`, which **beats Tailwind utility classes by default**. This is the most common "why isn't my Tailwind class working" issue.

```python
# This often silently fails on Quasar components:
ui.button('Button').classes('bg-slate-100 text-slate-950')

# Fix: prepend ! to force specificity
ui.button('Button').classes('!bg-slate-100 !text-slate-950')
```

As of **NiceGUI 3.0.0**, CSS layers were introduced to make overriding more predictable. Custom CSS added via `ui.add_css()` should go in the `components` or `utilities` layer, and still needs `!important` since Quasar's layer sits above it:

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

## 2. Quasar Theme Colors (missing from original)

NiceGUI/Quasar expose semantic color classes tied to the app's theme palette, independent of Tailwind's color scale:

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

These are **not** the same as Tailwind's `bg-blue-500`-style classes — mixing the two systems is normal and expected in NiceGUI apps.

---

## 3. Syntax Modifiers & NiceGUI Specials (from original, verified)

| Feature | Syntax / Prefix | Example | Description |
| :--- | :--- | :--- | :--- |
| Force priority | `!` | `!p-0`, `!bg-red-500` | Needed to beat Quasar's `!important` rules |
| Pseudo-classes | `hover:`, `focus:`, `active:`, `disabled:` | `hover:bg-blue-600` | Interaction states |
| List modifiers | `first:`, `last:`, `odd:`, `even:` | `odd:bg-gray-100` | Child position targeting |
| Group states | `group-hover:`, `group-focus:` | `group-hover:opacity-100` | Requires `group` class on parent |
| Peer states | `peer-checked:`, `peer-focus:` | `peer-checked:block` | Sibling-driven state (missing from original) |
| Breakpoints | `sm: md: lg: xl: 2xl:` | `md:flex-row` | Responsive design |
| Dark mode | `dark:` | `dark:bg-zinc-900` | Requires NiceGUI dark mode enabled (`ui.dark_mode()`) |
| Arbitrary values | `[...]` | `w-[320px]`, `bg-[#1da1f2]`, `top-[13px]` | Escape hatch for exact values |

---

## 4. Layout & Positioning (from original, verified — unchanged)

Display, position, coordinates, z-index, overflow — all correct as originally listed.

---

## 5. Flexbox & Grid (expanded — several categories were missing)

Everything from the original (direction, wrap, grow/shrink, justify, align, gap, grid-cols, col-span) plus:

| Category | Options / Patterns | Description |
| :--- | :--- | :--- |
| **Grid Rows** | `grid-rows-1` .. `grid-rows-6`, `grid-rows-none` | Number of explicit rows |
| **Row Span** | `row-span-1` .. `row-span-6`, `row-span-full` | Row span of a grid item |
| **Grid Auto Flow** | `grid-flow-row`, `grid-flow-col`, `grid-flow-dense` | Auto-placement algorithm |
| **Auto Columns/Rows** | `auto-cols-auto`, `auto-cols-min`, `auto-cols-max`, `auto-cols-fr`, `auto-rows-*` | Sizing of implicitly-created tracks |
| **Place Content** | `place-content-center`, `place-content-between`, ... | Shorthand for align+justify content (grid) |
| **Place Items** | `place-items-start`, `place-items-center`, ... | Shorthand for align+justify items |
| **Place Self** | `place-self-auto`, `place-self-center`, ... | Per-item override |
| **Order** | `order-1` .. `order-12`, `order-first`, `order-last`, `order-none` | Visual reordering without changing DOM |

---

## 6. Spacing (from original, verified — unchanged)

Padding, margin, negative margin, and `space-x/y` all correct.

---

## 7. Sizing (from original, verified, plus one addition)

Width/height/max-width/max-height as listed, plus:

| Dimension | Class Patterns | Notes |
| :--- | :--- | :--- |
| **Min Width/Height** | `min-w-0`, `min-w-full`, `min-w-min/max/fit`, `min-h-*` | Was missing entirely from original |
| **Aspect Ratio** | `aspect-auto`, `aspect-square`, `aspect-video`, `aspect-[4/3]` | Was missing entirely |

---

## 8. Typography (expanded)

Everything from the original, plus:

| Category | Options / Patterns |
| :--- | :--- |
| **Font Family** | `font-sans`, `font-serif`, `font-mono` (missing originally) |
| **Line Height** | `leading-none`, `leading-tight`, `leading-snug`, `leading-normal`, `leading-relaxed`, `leading-loose`, `leading-{3..10}` |
| **Letter Spacing** | `tracking-tighter`, `tracking-tight`, `tracking-normal`, `tracking-wide`, `tracking-wider`, `tracking-widest` |
| **Whitespace** | `whitespace-normal`, `whitespace-nowrap`, `whitespace-pre`, `whitespace-pre-wrap` |
| **Word Break** | `break-normal`, `break-words`, `break-all`, `truncate` |
| **List Style** | `list-none`, `list-disc`, `list-decimal`, `list-inside`, `list-outside` |
| **Vertical Align** | `align-baseline`, `align-top`, `align-middle`, `align-bottom` |

---

## 9. Backgrounds & Borders (expanded)

Everything from original, plus:

| Category | Class Pattern | Notes |
| :--- | :--- | :--- |
| **Ring** (focus outlines) | `ring`, `ring-{1,2,4,8}`, `ring-{color}`, `ring-offset-{0..8}` | Entirely missing originally — common for focus states |
| **Divide** (borders between siblings) | `divide-x`, `divide-y`, `divide-{color}` | Missing originally |
| **Background Gradient** | `bg-gradient-to-{t,tr,r,br,b,bl,l,tl}`, `from-{color}`, `via-{color}`, `to-{color}` | Missing originally |
| **Background Position/Size** | `bg-center`, `bg-cover`, `bg-contain`, `bg-no-repeat` | Missing originally |

**Full color name list** (used across `bg-`, `text-`, `border-`, `ring-`, `divide-`, `from-/via-/to-`):
`slate, gray, zinc, neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose` — each with shades `50–950`.

---

## 10. Effects & Interactivity (expanded)

Everything from original (shadow, opacity, cursor, select, transition, duration), plus:

| Category | Options | Notes |
| :--- | :--- | :--- |
| **Transform** | `scale-{0..150}`, `rotate-{0,45,90,180}`, `translate-x/y-*`, `skew-x/y-*` — requires `transform` class to activate in older Tailwind | Missing originally |
| **Filters** | `blur-{sm,md,lg,xl}`, `brightness-{50..150}`, `contrast-*`, `grayscale`, `sepia`, `saturate-*`, `drop-shadow-*` | Missing originally |
| **Backdrop Filters** | `backdrop-blur-*`, `backdrop-brightness-*` | Missing originally |
| **Animation** | `animate-none`, `animate-spin`, `animate-ping`, `animate-pulse`, `animate-bounce` | Missing originally |
| **Timing Function** | `ease-linear`, `ease-in`, `ease-out`, `ease-in-out` | Missing originally |
| **Pointer Events** | `pointer-events-none`, `pointer-events-auto` | Missing originally |
| **Accessibility** | `sr-only`, `not-sr-only` | Missing originally |

---

## 11. NiceGUI-Specific Patterns Cheatsheet (expanded from original)

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

## 12. Best Places to Look This Up

1. **NiceGUI official "Styling & Appearance" docs** — the authoritative source for `.classes()`/`.props()`/`.style()` behavior, CSS layers, and `ui.colors()`:
   https://nicegui.io/documentation/section_styling_appearance

2. **Quasar Framework docs** — required whenever you use `.props()`, since NiceGUI just passes those strings straight through to Quasar components:
   https://quasar.dev/style/color-palette (and the wider quasar.dev/style section)

3. **Tailwind CSS official docs** — the canonical utility-class reference (NiceGUI bundles Tailwind but doesn't fork its class names):
   https://tailwindcss.com/docs

For day-to-day NiceGUI work, keep the first link open — it's the only one that explains the parts that are unique to NiceGUI (the `!important` conflict, layers, `add=/remove=/replace=`, and theme colors) that neither the Quasar nor Tailwind docs will tell you.