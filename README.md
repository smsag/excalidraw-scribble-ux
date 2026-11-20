# Excalidraw scribble UX

A hand-drawn ("scribble") UX/UI wireframe library for Excalidraw: 157 items for web and mobile, in Excalifont, with
editable labels.

## Files

| File | What it is |
|---|---|
| `scribble-ux.excalidrawlib` | The library to import |
| `scribble-ux-showcase.excalidraw` | Every item on one board, by section, named |
| `build_library.py` | The generator – both files above are built by it |
| `excalifont-widths.json` | Excalifont character widths, so labels are measured and centred correctly |

## Import

- **excalidraw.com / desktop app / VS Code:** Library panel → ⋮ → Open → `scribble-ux.excalidrawlib`.
- **Obsidian (Excalidraw plugin):** the same Library panel.
- **Nimbus (Pläne):** copy the file to `Pläne/Bibliothek.excalidrawlib` in the vault, or use „Aus Datei importieren …“
  in the library panel.

## Rebuild

Edit `STYLE` / `ACCENT` at the top of `build_library.py` (roughness 0/1/2, fill hachure/cross-hatch/solid, stroke
1/2/4), then:

```bash
python3 build_library.py
```

No dependencies beyond Python 3.

## Contents

- **Frames and layout:** browser, desktop app, phone, tablet, section, divider, 12-column grid
- **Navigation:** top bar, sidebar, tabs, breadcrumb, pagination, progress steps, footer, mobile app bar and tab bar,
  dropdown menu, hamburger
- **Inputs and controls:** buttons (primary, secondary, danger, disabled, link, with icon, icon only, floating), text
  fields (normal, focus, error), password, textarea, search, select, date, checkbox, radio, toggle, slider, stepper,
  segmented control, file upload, chips, rating
- **Content and data:** card, list item, table, avatars, badges, placeholders, text blocks, charts, KPI tile,
  accordion, map
- **Feedback and overlays:** modal, backdrop, bottom sheet, toast, tooltip, alerts, progress, spinner, skeleton, empty
  state, cookie banner
- **Patterns:** login, sign-up, contact, pricing, hero, feature grid, testimonial, search results, product detail,
  order summary, settings, profile, dashboard, data table, calendar, kanban, chat, notifications, comments, file list,
  filters, onboarding, mobile list, navigation drawer, 404
- **Icons:** 35 line icons
- **Annotations and post-its:** post-its in six colours, marker, callout, comment, highlight, tap, dimension line
- **Niehaus wireframe:** the weight ladder (below), legend, example page, fold line

Buttons and fields inside patterns are nested groups: double-click into a pattern to pick one out.

## Niehaus weight ladder

After Sandra Niehaus (2010): each element gets an attention level. Unlike Niehaus' grey blocks, an element keeps its
colour and only gains weight, using the five shades (0–4) of its Excalidraw palette hue.

| Level | Role | Area share | Stroke | Width | Background | Text |
|---|---|---|---|---|---|---|
| Light | must-have | ~60 % | shade 2 | 1 | none | shade 3 |
| Medium | tertiary | ~30 % | shade 4 | 1 | shade 1, hachure | shade 4 |
| Dark | secondary | ~8 % | shade 4 | 2 | shade 2, solid | #1e1e1e |
| Black | primary | ~2 % | shade 4 | 4 | shade 4, solid | #ffffff |

At most two primary (Black) elements per page. In Nimbus the level is set in the style panel and stored at
`customData.nimbus.niehaus`; elsewhere apply the ladder by hand.

## Nimbus-specific data

Post-its carry `customData.nimbus.sticky: true`, so Nimbus renders their text as Markdown and fits the note to it.
Other Excalidraw apps ignore it and show the raw text.

## License

MIT, see [LICENSE](LICENSE). Excalifont itself is not included; `excalifont-widths.json` holds only its character widths.
