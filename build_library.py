#!/usr/bin/env python3
"""Builds scribble-ux.excalidrawlib (import via Excalidraw > Library > Open)
and scribble-ux-showcase.excalidraw (all items on one board).
Change STYLE / ACCENT below and rerun: python3 build_library.py"""
import contextlib, copy, datetime, json, math, os, random

STYLE = dict(roughness=1, fillStyle="hachure", strokeWidth=1)  # roughness 0|1|2, fill hachure|cross-hatch|solid, stroke 1|2|4
ACCENT, ACCENT_BG = "#1971c2", "#a5d8ff"
INK, MUTED, FAINT, PAPER, SHADE = "#1e1e1e", "#868e96", "#ced4da", "#ffffff", "#e9ecef"
GREEN, GREEN_BG = "#2f9e44", "#b2f2bb"
RED, RED_BG = "#e03131", "#ffc9c9"
AMBER, AMBER_BG = "#f08c00", "#ffec99"
FONT, LH = 5, 1.25  # 5 = Excalifont

HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, "excalifont-widths.json")))  # advance widths per em, from Excalifont
rnd = random.Random(7)


def nid():
    return "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(20))


def tw(t, size):
    return max(sum(W.get(c, 0.6) for c in ln) for ln in t.split("\n")) * size


def th(t, size):
    return (t.count("\n") + 1) * size * LH


class Item:
    def __init__(s, name, section):
        s.name, s.section, s.els = name, section, []
        s._part = None

    @contextlib.contextmanager
    def part(s):
        """Sub-component (button, field): own nested group, so a pass can pick it out of a pattern."""
        s._part = nid()
        try:
            yield
        finally:
            s._part = None

    def _el(s, type, x, y, w, h, **kw):
        e = {"id": nid(), "type": type, "x": x, "y": y, "width": w, "height": h, "angle": 0,
             "strokeColor": INK, "backgroundColor": "transparent", "fillStyle": STYLE["fillStyle"],
             "strokeWidth": STYLE["strokeWidth"], "strokeStyle": "solid", "roughness": STYLE["roughness"],
             "opacity": 100, "groupIds": [], "frameId": None, "roundness": None,
             "seed": rnd.randint(1, 2**31 - 1), "version": 1, "versionNonce": rnd.randint(1, 2**31 - 1),
             "isDeleted": False, "boundElements": None, "updated": 1, "link": None, "locked": False}
        e.update(kw)
        if s._part:
            e["groupIds"] = [s._part]
        s.els.append(e)
        return e

    def rect(s, x, y, w, h, bg=None, stroke=INK, round=True, **kw):
        return s._el("rectangle", x, y, w, h, strokeColor=stroke, backgroundColor=bg or "transparent",
                     roundness={"type": 3} if round else None, **kw)

    def ell(s, x, y, w, h, bg=None, stroke=INK, **kw):
        return s._el("ellipse", x, y, w, h, strokeColor=stroke, backgroundColor=bg or "transparent", **kw)

    def line(s, pts, stroke=INK, curve=False, bg=None, arrow=None, **kw):
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs, ys = [p[0] for p in rel], [p[1] for p in rel]
        closed = arrow is None and len(pts) > 2 and pts[0] == pts[-1]
        e = s._el("arrow" if arrow else "line", x0, y0, max(xs) - min(xs), max(ys) - min(ys),
                  strokeColor=stroke, backgroundColor=bg or "transparent",
                  roundness={"type": 2} if curve else None, points=rel, lastCommittedPoint=None,
                  startBinding=None, endBinding=None,
                  startArrowhead="arrow" if arrow == "both" else None,
                  endArrowhead="arrow" if arrow else None, **kw)
        if not arrow:
            e["polygon"] = closed
        return e

    def text(s, x, y, t, size=16, color=INK, align="left", **kw):
        w = tw(t, size)
        x = x - w / 2 if align == "center" else x - w if align == "right" else x
        return s._el("text", x, y, w, th(t, size), strokeColor=color, text=t, originalText=t,
                     fontSize=size, fontFamily=FONT, textAlign=align, verticalAlign="top",
                     containerId=None, autoResize=True, lineHeight=LH, **kw)

    def label(s, c, t, size=16, color=INK):
        """Centered text bound to its container (moves and resizes with it)."""
        w, h = tw(t, size), th(t, size)
        x, y = c["x"] + (c["width"] - w) / 2, c["y"] + (c["height"] - h) / 2
        e = s._el("text", x, y, w, h, strokeColor=color, text=t, originalText=t, fontSize=size,
                  fontFamily=FONT, textAlign="center", verticalAlign="middle", containerId=c["id"],
                  autoResize=True, lineHeight=LH, angle=c["angle"])
        c["boundElements"] = (c["boundElements"] or []) + [{"type": "text", "id": e["id"]}]
        return e

    def icon(s, name, x, y, size=24, color=INK, fill=None):
        k = size / 24
        P = lambda pts: [(x + px * k, y + py * k) for px, py in pts]
        for p in ICONS[name]:
            kind = p[0]
            rough = min(STYLE["roughness"], 1)  # full roughness turns tiny icons into noise
            if kind in "eE":
                s.ell(x + p[1] * k, y + p[2] * k, p[3] * k, p[4] * k, stroke=color, roughness=rough,
                      bg=color if kind == "E" else None, fillStyle="solid")
            elif kind == "r":
                s.rect(x + p[1] * k, y + p[2] * k, p[3] * k, p[4] * k, stroke=color, round=False, roughness=rough)
            else:  # l = polyline, c = curve, p = closed polygon (fillable)
                s.line(P(p[1]), stroke=color, curve=kind == "c" or (len(p) > 2 and p[2]), roughness=rough,
                       bg=fill if kind == "p" else None, fillStyle="solid")

    def squig(s, x, y, w, color=FAINT):
        n = max(2, int(w // 16))
        s.line([(x + w * i / n, y + (2 if i % 2 else -2)) for i in range(n + 1)], stroke=color, curve=True)

    def placeholder(s, x, y, w, h):
        s.rect(x, y, w, h, bg=SHADE, stroke=MUTED, round=False)
        s.line([(x, y), (x + w, y + h)], stroke=MUTED)
        s.line([(x + w, y), (x, y + h)], stroke=MUTED)

    def button(s, x, y, w, h, t, kind="primary", size=16):
        stroke, bg, col = {"primary": (ACCENT, ACCENT_BG, ACCENT), "secondary": (INK, None, INK),
                           "danger": (RED, RED_BG, RED), "disabled": (FAINT, SHADE, MUTED),
                           "black": (INK, INK, PAPER)}[kind]
        with s.part():
            b = s.rect(x, y, w, h, bg=bg, stroke=stroke, **({"fillStyle": "solid"} if kind == "black" else {}))
            s.label(b, t, size, col)
        return b

    def field(s, x, y, w, lab, value, state="default", h=44):
        with s.part():
            if lab:
                s.text(x, y, lab, 16)
                y += 24
            stroke = {"default": INK, "focus": ACCENT, "error": RED}[state]
            f = s.rect(x, y, w, h, stroke=stroke, strokeWidth=STYLE["strokeWidth"] + (state != "default"))
            # free text, not bound: Excalidraw pins left-aligned bound text 5px from the border
            s.text(x + 12, y + (h - th(value, 16)) / 2, value, 16, MUTED if state == "default" else INK)
        return f

    def toggle(s, x, y, on=True):
        s.rect(x, y, 52, 28, bg=ACCENT_BG if on else SHADE, stroke=ACCENT if on else INK)
        s.ell(x + (27 if on else 3), y + 3, 22, 22, bg=PAPER, stroke=ACCENT if on else INK, fillStyle="solid")

    def table(s, x, y):
        s.rect(x, y, 480, 176, round=False)
        s.rect(x, y, 480, 44, bg=SHADE, round=False)
        for j, t in enumerate(["Name", "Status", "Date"]):
            s.text(x + 16 + j * 160, y + 12, t, 16)
        for i, row in enumerate([("Item one", "Active", "12 Nov"), ("Item two", "Pending", "14 Nov"), ("Item three", "Active", "18 Nov")]):
            ry = y + 44 + i * 44
            if i:
                s.line([(x, ry), (x + 480, ry)], stroke=FAINT)
            for j, t in enumerate(row):
                s.text(x + 16 + j * 160, ry + 12, t, 16, (GREEN if t == "Active" else AMBER) if j == 1 else INK)

    def bbox(s):
        xs, ys = [], []
        for e in s.els:
            if "points" in e:
                xs += [e["x"] + p[0] for p in e["points"]]
                ys += [e["y"] + p[1] for p in e["points"]]
            else:
                xs += [e["x"], e["x"] + e["width"]]
                ys += [e["y"], e["y"] + e["height"]]
        return min(xs), min(ys), max(xs), max(ys)

    def done(s):
        x0, y0, _, _ = s.bbox()
        # outer group around the whole item, unless one sub-component already is the whole item
        whole = len({tuple(e["groupIds"]) for e in s.els}) == 1 and s.els[0]["groupIds"]
        gid = nid()
        for e in s.els:
            e["x"] -= x0
            e["y"] -= y0
            if len(s.els) > 1 and not whole:
                e["groupIds"] = e["groupIds"] + [gid]  # innermost first, like Excalidraw


def star(cx, cy, ro, ri):
    pts = [(cx + (ro if i % 2 == 0 else ri) * math.sin(i * math.pi / 5),
            cy - (ro if i % 2 == 0 else ri) * math.cos(i * math.pi / 5)) for i in range(10)]
    return pts + [pts[0]]


ICONS = {
    "search": [("e", 3, 3, 13, 13), ("l", [(14.5, 14.5), (21, 21)])],
    "home": [("l", [(3, 11), (12, 3), (21, 11)]), ("l", [(5, 9), (5, 21), (19, 21), (19, 9)])],
    "user": [("e", 8, 3, 8, 8), ("c", [(4, 21), (6, 15), (12, 13), (18, 15), (20, 21)])],
    "settings": [("e", 5, 5, 14, 14), ("e", 9.5, 9.5, 5, 5)] + [
        ("l", [(12 + 7 * math.cos(a * math.pi / 4), 12 + 7 * math.sin(a * math.pi / 4)),
               (12 + 10 * math.cos(a * math.pi / 4), 12 + 10 * math.sin(a * math.pi / 4))]) for a in range(8)],
    "heart": [("p", [(12, 20), (4, 12), (3, 8), (5, 5), (9, 4), (12, 7), (15, 4), (19, 5), (21, 8), (20, 12), (12, 20)], True)],
    "star": [("p", star(12, 12.5, 10, 4.5))],
    "bell": [("c", [(6, 17), (6, 10), (8, 6), (12, 4), (16, 6), (18, 10), (18, 17)]), ("l", [(4, 17), (20, 17)]), ("e", 10, 18, 4, 4)],
    "mail": [("r", 3, 6, 18, 13), ("l", [(3, 6), (12, 13), (21, 6)])],
    "plus": [("l", [(12, 4), (12, 20)]), ("l", [(4, 12), (20, 12)])],
    "close": [("l", [(5, 5), (19, 19)]), ("l", [(19, 5), (5, 19)])],
    "check": [("l", [(4, 12), (10, 18), (20, 6)])],
    "chevron-right": [("l", [(9, 5), (16, 12), (9, 19)])],
    "chevron-left": [("l", [(15, 5), (8, 12), (15, 19)])],
    "chevron-down": [("l", [(5, 9), (12, 16), (19, 9)])],
    "arrow-left": [("l", [(20, 12), (4, 12)]), ("l", [(10, 6), (4, 12), (10, 18)])],
    "menu": [("l", [(4, 6), (20, 6)]), ("l", [(4, 12), (20, 12)]), ("l", [(4, 18), (20, 18)])],
    "trash": [("l", [(4, 7), (20, 7)]), ("l", [(9, 7), (9, 4), (15, 4), (15, 7)]), ("l", [(6, 7), (7, 21), (17, 21), (18, 7)])],
    "edit": [("p", [(4, 20), (5, 15), (16, 4), (20, 8), (9, 19), (4, 20)]), ("l", [(14, 6), (18, 10)])],
    "share": [("e", 16, 3, 5, 5), ("e", 3, 10, 5, 5), ("e", 16, 17, 5, 5), ("l", [(8, 11.5), (16, 6.5)]), ("l", [(8, 13.5), (16, 18.5)])],
    "calendar": [("r", 3, 5, 18, 16), ("l", [(3, 10), (21, 10)]), ("l", [(8, 3), (8, 7)]), ("l", [(16, 3), (16, 7)])],
    "upload": [("l", [(12, 16), (12, 4)]), ("l", [(7, 9), (12, 4), (17, 9)]), ("l", [(4, 15), (4, 20), (20, 20), (20, 15)])],
    "more": [("E", 4, 10.5, 3, 3), ("E", 10.5, 10.5, 3, 3), ("E", 17, 10.5, 3, 3)],
    "info": [("e", 3, 3, 18, 18), ("l", [(12, 11), (12, 17)]), ("E", 11, 6.5, 2, 2)],
    "alert": [("p", [(12, 3), (22, 20), (2, 20), (12, 3)]), ("l", [(12, 9), (12, 14)]), ("E", 11, 16, 2, 2)],
    "play": [("p", [(8, 5), (19, 12), (8, 19), (8, 5)])],
    "image": [("r", 3, 4, 18, 16), ("l", [(3, 17), (9, 11), (13, 15), (16, 12), (21, 17)]), ("e", 14, 7, 4, 4)],
    "lock": [("r", 5, 11, 14, 10), ("c", [(8, 11), (8, 7), (12, 4), (16, 7), (16, 11)])],
    "folder": [("p", [(3, 6), (10, 6), (12, 8), (21, 8), (21, 19), (3, 19), (3, 6)])],
    "pin": [("p", [(12, 21), (6, 13), (5, 9), (7, 5), (12, 3), (17, 5), (19, 9), (18, 13), (12, 21)], True), ("e", 10, 7, 4, 4)],
    "eye": [("c", [(2, 12), (7, 7), (12, 6), (17, 7), (22, 12), (17, 17), (12, 18), (7, 17), (2, 12)]), ("e", 9, 9, 6, 6)],
    "cart": [("l", [(2, 4), (5, 4), (8, 16), (19, 16), (21, 8), (6, 8)]), ("e", 8, 18, 3, 3), ("e", 16, 18, 3, 3)],
    "filter": [("p", [(3, 5), (21, 5), (14, 13), (14, 20), (10, 18), (10, 13), (3, 5)])],
    "download": [("l", [(12, 4), (12, 16)]), ("l", [(7, 11), (12, 16), (17, 11)]), ("l", [(4, 15), (4, 20), (20, 20), (20, 15)])],
    "file": [("p", [(6, 3), (14, 3), (19, 8), (19, 21), (6, 21), (6, 3)]), ("l", [(14, 3), (14, 8), (19, 8)])],
    "external": [("l", [(13, 4), (20, 4), (20, 11)]), ("l", [(20, 4), (11, 13)]), ("l", [(17, 14), (17, 20), (4, 20), (4, 7), (10, 7)])],
}

LIB = []


def item(name, section):
    it = Item(name, section)
    LIB.append(it)
    return it


# ---------------------------------------------------------------- layout & frames
S = "Frames and layout"
it = item("Browser window", S)
it.rect(0, 0, 800, 520)
it.line([(0, 40), (800, 40)])
for i in range(3):
    it.ell(14 + i * 20, 14, 12, 12)
it.rect(90, 8, 560, 24)
it.text(102, 10, "https://example.com", 16, MUTED)

it = item("Desktop app window", S)
it.rect(0, 0, 800, 520)
it.line([(0, 36), (800, 36)])
for i in range(3):
    it.ell(14 + i * 20, 12, 12, 12)
it.text(400, 8, "App name", 16, MUTED, "center")

it = item("Phone", S)
it.rect(0, 0, 300, 620)
it.rect(110, 12, 80, 22, bg=INK, fillStyle="solid")
it.text(24, 12, "9:41", 16)
it.line([(110, 600), (190, 600)], strokeWidth=3)

it = item("Tablet", S)
it.rect(0, 0, 540, 720)
it.ell(266, 10, 8, 8)
it.line([(230, 700), (310, 700)], strokeWidth=3)

it = item("Section container", S)
it.rect(0, 0, 400, 240, stroke=MUTED, strokeStyle="dashed")
it.text(12, 8, "Section", 16, MUTED)

it = item("Divider", S)
it.line([(0, 0), (400, 0)], stroke=FAINT)

it = item("12-column grid", S)
for i in range(12):
    it.rect(i * 66, 0, 54, 300, bg="#ffc9c9", stroke="#ffc9c9", round=False, opacity=40, fillStyle="solid")

# ---------------------------------------------------------------- navigation
S = "Navigation"
it = item("Top navigation (web)", S)
it.rect(0, 0, 800, 64, round=False)
it.ell(16, 16, 32, 32, bg=SHADE)
it.text(58, 20, "Logo", 20)
for i, t in enumerate(["Products", "Pricing", "About"]):
    it.text(360 + i * 100, 22, t, 16)
it.button(660, 12, 124, 40, "Sign up")

it = item("Sidebar navigation", S)
it.rect(0, 0, 220, 480)
it.text(16, 16, "Workspace", 20)
for i, (ic, t) in enumerate([("home", "Dashboard"), ("folder", "Projects"), ("mail", "Messages"), ("settings", "Settings")]):
    y = 60 + i * 44
    if i == 0:
        it.rect(8, y, 204, 36, bg=ACCENT_BG, stroke=ACCENT)
    it.icon(ic, 20, y + 6, 24, ACCENT if i == 0 else INK)
    it.text(54, y + 8, t, 16, ACCENT if i == 0 else INK)

it = item("Tabs", S)
for i, t in enumerate(["Overview", "Details", "Reviews"]):
    it.text(60 + i * 120, 8, t, 16, ACCENT if i == 0 else MUTED, "center")
it.line([(0, 40), (360, 40)], stroke=FAINT)
it.line([(10, 40), (110, 40)], stroke=ACCENT, strokeWidth=STYLE["strokeWidth"] + 2)

it = item("Breadcrumb", S)
x = 0
for t, c in [("Home", ACCENT), ("/", MUTED), ("Products", ACCENT), ("/", MUTED), ("Detail", INK)]:
    it.text(x, 0, t, 16, c)
    x += tw(t, 16) + 10

it = item("Pagination", S)
for i, t in enumerate(["‹", "1", "2", "3", "…", "9", "›"]):
    b = it.rect(i * 44, 0, 36, 36, bg=ACCENT_BG if t == "2" else None, stroke=ACCENT if t == "2" else INK)
    it.label(b, t, 16, ACCENT if t == "2" else INK)

it = item("Progress steps", S)
for i, t in enumerate(["Cart", "Address", "Payment"]):
    cx = 30 + i * 140
    if i < 2:
        it.line([(cx + 20, 20), (cx + 120, 20)], stroke=ACCENT if i == 0 else FAINT)
    c = it.ell(cx - 18, 2, 36, 36, bg=ACCENT_BG if i == 0 else None,
               stroke=ACCENT if i < 2 else FAINT)
    if i == 0:
        it.icon("check", cx - 10, 10, 20, ACCENT)
    else:
        it.label(c, str(i + 1), 16, ACCENT if i == 1 else MUTED)
    it.text(cx, 46, t, 16, INK if i < 2 else MUTED, "center")

it = item("Footer", S)
it.rect(0, 0, 800, 140, bg=SHADE, round=False)
for i, t in enumerate(["Company", "Help", "Legal"]):
    it.text(24 + i * 180, 20, t, 16)
    it.squig(24 + i * 180, 58, 110, MUTED)
    it.squig(24 + i * 180, 80, 90, MUTED)
it.text(24, 108, "© 2026 Company", 16, MUTED)

it = item("Mobile app bar", S)
it.rect(0, 0, 300, 56, round=False)
it.icon("arrow-left", 14, 16)
it.text(150, 16, "Title", 20, align="center")
it.icon("more", 262, 16)

it = item("Mobile tab bar", S)
it.rect(0, 0, 300, 64, round=False)
for i, (ic, t) in enumerate([("home", "Home"), ("search", "Search"), ("heart", "Saved"), ("user", "Profile")]):
    cx = 37.5 + i * 75
    col = ACCENT if i == 0 else MUTED
    it.icon(ic, cx - 12, 8, 24, col)
    it.text(cx, 36, t, 16, col, "center")

it = item("Dropdown menu (open)", S)
it.rect(0, 0, 200, 168)
it.rect(6, 6, 188, 36, bg=SHADE, stroke=SHADE, fillStyle="solid")
for i, t in enumerate(["Edit", "Duplicate", "Share", "Delete"]):
    it.text(18, 14 + i * 38, t, 16, RED if t == "Delete" else INK)

it = item("Hamburger menu", S)
it.icon("menu", 0, 0, 32)

# ---------------------------------------------------------------- inputs & controls
S = "Inputs and controls"
for name, kind, t in [("Button / primary", "primary", "Sign up"), ("Button / secondary", "secondary", "Cancel"),
                      ("Button / danger", "danger", "Delete"), ("Button / disabled", "disabled", "Disabled")]:
    item(name, S).button(0, 0, 140, 44, t, kind, 20)

it = item("Button / ghost link", S)
it.text(0, 10, "Learn more", 16, ACCENT)
it.icon("chevron-right", tw("Learn more", 16) + 4, 8, 24, ACCENT)

it = item("Button / with icon", S)
it.rect(0, 0, 160, 44, bg=ACCENT_BG, stroke=ACCENT)
it.icon("plus", 14, 10, 24, ACCENT)
it.text(46, 12, "Add item", 16, ACCENT)

it = item("Icon button", S)
it.rect(0, 0, 44, 44)
it.icon("settings", 10, 10)

it = item("Floating action button", S)
it.ell(0, 0, 56, 56, bg=ACCENT_BG, stroke=ACCENT)
it.icon("plus", 14, 14, 28, ACCENT)

item("Text field", S).field(0, 0, 260, "Email", "name@mail.com")
item("Text field / focus", S).field(0, 0, 260, "Email", "anna@mail|", "focus")
it = item("Text field / error", S)
it.field(0, 0, 260, "Email", "anna@", "error")
it.text(0, 74, "Enter a valid email", 16, RED)

it = item("Password field", S)
it.field(0, 0, 260, "Password", "••••••••", "default")
it.icon("eye", 226, 34, 24, MUTED)

it = item("Textarea", S)
it.text(0, 0, "Message", 16)
it.rect(0, 24, 260, 120)
it.text(12, 36, "Write something…", 16, MUTED)
it.line([(244, 140), (256, 128)], stroke=MUTED)
it.line([(250, 140), (256, 134)], stroke=MUTED)

it = item("Search field", S)
it.rect(0, 0, 260, 44)
it.icon("search", 12, 10, 24, MUTED)
it.text(44, 12, "Search…", 16, MUTED)

it = item("Select / dropdown", S)
it.field(0, 0, 260, "Country", "Germany")
it.icon("chevron-down", 226, 34)

it = item("Date picker field", S)
it.field(0, 0, 260, "Date", "20 Nov 2026")
it.icon("calendar", 226, 34, 24, MUTED)

it = item("Checkbox / checked", S)
it.rect(0, 0, 22, 22, bg=ACCENT_BG, stroke=ACCENT)
it.icon("check", 1, 1, 20, ACCENT)
it.text(32, 1, "Remember me", 16)

it = item("Checkbox / unchecked", S)
it.rect(0, 0, 22, 22)
it.text(32, 1, "Subscribe", 16)

it = item("Radio group", S)
for i, t in enumerate(["Standard", "Express", "Pickup"]):
    it.ell(0, i * 34, 22, 22, stroke=ACCENT if i == 0 else INK)
    if i == 0:
        it.ell(6, 6, 10, 10, bg=ACCENT, stroke=ACCENT, fillStyle="solid")
    it.text(32, i * 34 + 1, t, 16)

it = item("Toggle / on", S)
it.toggle(0, 0, True)
it.text(64, 4, "Notifications", 16)

it = item("Toggle / off", S)
it.toggle(0, 0, False)
it.text(64, 4, "Dark mode", 16)

it = item("Slider", S)
it.line([(0, 12), (220, 12)], stroke=FAINT, strokeWidth=STYLE["strokeWidth"] + 2)
it.line([(0, 12), (132, 12)], stroke=ACCENT, strokeWidth=STYLE["strokeWidth"] + 2)
it.ell(122, 2, 20, 20, bg=PAPER, stroke=ACCENT, fillStyle="solid")
it.text(234, 2, "60%", 16)

it = item("Number stepper", S)
it.rect(0, 0, 132, 40)
it.line([(44, 0), (44, 40)])
it.line([(88, 0), (88, 40)])
it.line([(14, 20), (30, 20)])
it.text(66, 10, "1", 16, align="center")
it.icon("plus", 98, 8)

it = item("Segmented control", S)
it.rect(0, 0, 300, 40)
it.label(it.rect(100, 4, 100, 32, bg=ACCENT_BG, stroke=ACCENT), "Week", 16, ACCENT)
it.text(50, 10, "Day", 16, align="center")
it.text(250, 10, "Month", 16, align="center")

it = item("File upload", S)
it.rect(0, 0, 300, 160, stroke=MUTED, strokeStyle="dashed")
it.icon("upload", 134, 30, 32, MUTED)
it.text(150, 76, "Drop files here", 20, align="center")
it.text(150, 108, "or browse", 16, ACCENT, "center")

it = item("Chips / tags", S)
x = 0
for t in ["Design", "UX", "Research"]:
    w = tw(t, 16) + 44
    it.rect(x, 0, w, 32, bg=SHADE)
    it.text(x + 12, 6, t, 16)
    it.icon("close", x + w - 26, 8, 16, MUTED)
    x += w + 10

it = item("Rating stars", S)
for i in range(5):
    it.icon("star", i * 30, 0, 26, AMBER, fill=AMBER_BG if i < 3 else None)

# ---------------------------------------------------------------- content
S = "Content and data"
it = item("Card", S)
it.rect(0, 0, 260, 300)
it.placeholder(16, 16, 228, 120)
it.text(16, 150, "Card title", 20)
it.squig(16, 192, 200)
it.squig(16, 212, 150)
it.button(16, 242, 100, 40, "Open")

it = item("List item", S)
it.ell(12, 12, 40, 40, bg=SHADE)
it.text(64, 12, "Name Surname", 16)
it.text(64, 34, "Last message preview", 16, MUTED)
it.icon("chevron-right", 304, 20, 24, MUTED)
it.line([(0, 64), (340, 64)], stroke=FAINT)

item("Table", S).table(0, 0)

it = item("Avatar", S)
it.ell(0, 0, 48, 48, bg=SHADE)
it.icon("user", 10, 10, 28, MUTED)

it = item("Avatar / initials", S)
it.label(it.ell(0, 0, 48, 48, bg=ACCENT_BG, stroke=ACCENT), "AS", 16, ACCENT)

it = item("Avatar group", S)
for i in range(3):
    it.ell(i * 28, 0, 40, 40, bg=SHADE, fillStyle="solid")
it.label(it.ell(84, 0, 40, 40, bg=PAPER, fillStyle="solid"), "+4", 16, MUTED)

it = item("Badge / new", S)
it.label(it.rect(0, 0, 64, 28, bg=ACCENT_BG, stroke=ACCENT), "New", 16, ACCENT)

it = item("Status badges", S)
x = 0
for t, c, bg in [("Active", GREEN, GREEN_BG), ("Pending", AMBER, AMBER_BG), ("Failed", RED, RED_BG)]:
    w = tw(t, 16) + 24
    it.label(it.rect(x, 0, w, 28, bg=bg, stroke=c), t, 16, c)
    x += w + 10

it = item("Notification count", S)
it.icon("bell", 0, 6, 32)
it.label(it.ell(20, 0, 22, 22, bg=RED, stroke=RED, fillStyle="solid"), "3", 16, PAPER)

it = item("Image placeholder", S)
it.placeholder(0, 0, 240, 160)

it = item("Video placeholder", S)
it.rect(0, 0, 320, 180, bg=SHADE, round=False)
it.ell(130, 60, 60, 60, bg=PAPER, fillStyle="solid")
it.icon("play", 144, 74, 32)
it.line([(16, 164), (304, 164)], stroke=FAINT, strokeWidth=3)
it.line([(16, 164), (120, 164)], stroke=RED, strokeWidth=3)

it = item("Heading and paragraph", S)
it.text(0, 0, "Section heading", 28)
it.text(0, 48, "A short paragraph that explains\nwhat this section is about.", 16, MUTED)

it = item("Text lines (lo-fi)", S)
for i, w in enumerate([300, 280, 300, 180]):
    it.squig(0, i * 20, w, MUTED)

it = item("Bar chart", S)
it.line([(0, 0), (0, 160), (260, 160)])
for i, h in enumerate([60, 100, 80, 140, 110]):
    it.rect(20 + i * 48, 160 - h, 30, h, bg=ACCENT_BG, stroke=ACCENT, round=False)

it = item("Line chart", S)
it.line([(0, 0), (0, 160), (260, 160)])
it.line([(10, 130), (60, 100), (110, 115), (160, 60), (210, 75), (250, 30)], stroke=ACCENT, curve=True,
        strokeWidth=STYLE["strokeWidth"] + 1)

it = item("Donut chart", S)
it.ell(0, 0, 140, 140, bg=ACCENT_BG, stroke=ACCENT)
it.ell(35, 35, 70, 70, bg=PAPER, fillStyle="solid")
it.text(70, 58, "64%", 20, align="center")

it = item("KPI tile", S)
it.rect(0, 0, 200, 104)
it.text(16, 14, "Revenue", 16, MUTED)
it.text(16, 40, "€ 12.4k", 28)
it.text(16, 78, "+8% vs last month", 16, GREEN)

it = item("Accordion", S)
it.rect(0, 0, 340, 224)
it.text(16, 14, "Question one", 16)
it.icon("chevron-down", 304, 12)
it.squig(16, 64, 290, MUTED)
it.squig(16, 86, 220, MUTED)
for i, t in enumerate(["Question two", "Question three"]):
    y = 128 + i * 48
    it.line([(0, y), (340, y)], stroke=FAINT)
    it.text(16, y + 14, t, 16)
    it.icon("chevron-right", 304, y + 12)

it = item("Map placeholder", S)
it.rect(0, 0, 300, 200, bg=SHADE, round=False)
it.line([(0, 140), (80, 120), (160, 150), (300, 90)], stroke=PAPER, curve=True, strokeWidth=6)
it.line([(120, 0), (140, 90), (110, 200)], stroke=PAPER, curve=True, strokeWidth=6)
it.icon("pin", 136, 60, 36, RED, fill=RED_BG)

# ---------------------------------------------------------------- feedback & overlays
S = "Feedback and overlays"
it = item("Modal dialog", S)
it.rect(0, 0, 400, 200)
it.text(24, 24, "Delete project?", 20)
it.icon("close", 360, 20, 20, MUTED)
it.text(24, 64, "This can't be undone.", 16, MUTED)
it.button(152, 136, 100, 40, "Cancel", "secondary")
it.button(268, 136, 108, 40, "Delete", "danger")

it = item("Modal backdrop", S)
it.rect(0, 0, 800, 520, bg=INK, stroke=INK, round=False, opacity=30, fillStyle="solid")

it = item("Bottom sheet (mobile)", S)
it.rect(0, 0, 300, 240)
it.line([(130, 12), (170, 12)], stroke=FAINT, strokeWidth=4)
it.text(20, 28, "Share", 20)
for i, (ic, t) in enumerate([("mail", "Email"), ("share", "Copy link"), ("download", "Save file")]):
    it.icon(ic, 20, 74 + i * 48)
    it.text(56, 76 + i * 48, t, 16)

it = item("Toast", S)
b = it.rect(0, 0, 300, 52, bg="#343a40", stroke="#343a40", fillStyle="solid")
it.text(18, 16, "Changes saved", 16, PAPER)
it.text(282, 16, "Undo", 16, ACCENT_BG, "right")

it = item("Tooltip", S)
it.label(it.rect(0, 0, 160, 40, bg="#343a40", stroke="#343a40", fillStyle="solid"), "Helpful hint", 16, PAPER)
it.line([(70, 40), (80, 50), (90, 40), (70, 40)], stroke="#343a40", bg="#343a40", fillStyle="solid")

for name, ic, c, bg, t in [("Alert / info", "info", ACCENT, ACCENT_BG, "New version available."),
                           ("Alert / success", "check", GREEN, GREEN_BG, "Your changes were saved."),
                           ("Alert / warning", "alert", AMBER, AMBER_BG, "Your trial ends in 3 days."),
                           ("Alert / error", "close", RED, RED_BG, "Payment failed. Try again.")]:
    it = item(name, S)
    it.rect(0, 0, 380, 56, bg=bg, stroke=c)
    it.icon(ic, 16, 16, 24, c)
    it.text(52, 18, t, 16, c)

it = item("Progress bar", S)
it.rect(0, 0, 260, 14, bg=SHADE)
it.rect(0, 0, 160, 14, bg=ACCENT_BG, stroke=ACCENT)
it.text(272, -2, "60%", 16)

it = item("Spinner", S)
it.ell(0, 0, 40, 40, stroke=FAINT, strokeWidth=3)
it.line([(20, 0), (34, 6), (40, 20), (34, 34), (20, 40)], stroke=ACCENT, curve=True, strokeWidth=3)

it = item("Skeleton loader", S)
it.ell(0, 0, 48, 48, bg=SHADE, stroke=SHADE, fillStyle="solid")
it.rect(64, 4, 220, 14, bg=SHADE, stroke=SHADE, fillStyle="solid")
it.rect(64, 30, 160, 14, bg=SHADE, stroke=SHADE, fillStyle="solid")

it = item("Empty state", S)
it.rect(0, 0, 320, 240, stroke=FAINT, strokeStyle="dashed")
it.icon("folder", 136, 24, 48, MUTED)
it.text(160, 88, "Start your first project", 20, align="center")
it.text(160, 120, "Projects you create show up here.", 16, MUTED, "center")
it.button(95, 168, 130, 40, "Create project")

it = item("Cookie banner", S)
it.rect(0, 0, 640, 64)
it.text(20, 22, "We use cookies to improve your experience.", 16)
it.button(400, 12, 104, 40, "Decline", "secondary")
it.button(516, 12, 104, 40, "Accept")

# ---------------------------------------------------------------- patterns
S = "Patterns"
it = item("Login form", S)
it.rect(0, 0, 320, 380)
it.text(24, 24, "Log in", 28)
it.field(24, 80, 272, "Email", "name@mail.com")
it.field(24, 160, 272, "Password", "••••••••")
it.button(24, 252, 272, 44, "Log in", size=20)
it.text(160, 320, "Forgot password?", 16, ACCENT, "center")

it = item("Pricing card", S)
it.rect(0, 0, 260, 340)
it.text(24, 24, "Pro", 20)
it.text(24, 56, "€ 12 / month", 28)
for i, t in enumerate(["Unlimited projects", "Shared libraries", "Priority support"]):
    it.icon("check", 24, 116 + i * 36, 20, GREEN)
    it.text(54, 116 + i * 36, t, 16)
it.button(24, 268, 212, 44, "Choose plan", size=20)

it = item("Sign-up form", S)
it.rect(0, 0, 320, 470)
it.text(24, 24, "Create account", 28)
it.field(24, 80, 272, "Name", "Your name")
it.field(24, 160, 272, "Email", "name@mail.com")
it.field(24, 240, 272, "Password", "••••••••")
it.rect(24, 330, 22, 22)
it.text(56, 331, "I accept the terms", 16)
it.button(24, 372, 272, 44, "Sign up", size=20)
it.text(160, 432, "Already have an account? Log in", 16, ACCENT, "center")

it = item("Contact form", S)
it.rect(0, 0, 340, 440)
it.text(24, 24, "Contact us", 28)
it.field(24, 80, 292, "Name", "Your name")
it.field(24, 160, 292, "Email", "name@mail.com")
it.text(24, 240, "Message", 16)
it.rect(24, 264, 292, 100)
it.text(36, 276, "How can we help?", 16, MUTED)
it.button(24, 380, 292, 44, "Send message", size=20)

it = item("Hero section", S)
it.rect(0, 0, 800, 360, round=False)
it.text(40, 64, "Big headline that\nsays what you do", 36)
it.text(40, 182, "One sentence that explains the value.", 16, MUTED)
it.button(40, 232, 150, 48, "Get started", size=20)
it.button(206, 232, 150, 48, "Learn more", "secondary", 20)
it.placeholder(440, 40, 320, 280)

it = item("Feature grid", S)
for i, (ic, t) in enumerate([("star", "Fast"), ("lock", "Secure"), ("heart", "Loved")]):
    x = i * 260
    it.rect(x, 0, 240, 180)
    it.ell(x + 20, 20, 48, 48, bg=ACCENT_BG, stroke=ACCENT)
    it.icon(ic, x + 32, 32, 24, ACCENT)
    it.text(x + 20, 84, t, 20)
    it.squig(x + 20, 128, 200, MUTED)
    it.squig(x + 20, 148, 150, MUTED)

it = item("Testimonial", S)
it.rect(0, 0, 360, 180)
it.text(20, 20, "“This saved our team\nhours every week.”", 20)
it.ell(20, 116, 44, 44, bg=SHADE)
it.text(76, 116, "Name Surname", 16)
it.text(76, 138, "Role, Company", 16, MUTED)

it = item("Search results", S)
it.rect(0, 0, 560, 44)
it.icon("search", 12, 10, 24, MUTED)
it.text(44, 12, "wireframe kit", 16)
x = 0
for i, t in enumerate(["All", "Images", "Docs", "Recent"]):
    w = tw(t, 16) + 28
    it.label(it.rect(x, 60, w, 30, bg=ACCENT_BG if i == 0 else None, stroke=ACCENT if i == 0 else INK), t, 16,
             ACCENT if i == 0 else INK)
    x += w + 8
for i in range(3):
    y = 112 + i * 84
    it.text(0, y, "Result title", 20, ACCENT)
    it.text(0, y + 28, "example.com/page", 16, GREEN)
    it.squig(0, y + 60, 480, MUTED)

it = item("Product detail", S)
it.placeholder(0, 0, 320, 320)
for i in range(4):
    it.placeholder(i * 83, 336, 71, 71)
it.text(352, 0, "Product name", 28)
for i in range(5):
    it.icon("star", 352 + i * 24, 48, 20, AMBER, fill=AMBER_BG if i < 4 else None)
it.text(478, 48, "(128)", 16, MUTED)
it.text(352, 86, "€ 49.00", 28)
for i, w in enumerate([300, 280, 200]):
    it.squig(352, 144 + i * 20, w, MUTED)
it.text(352, 212, "Size", 16)
for i, t in enumerate(["S", "M", "L"]):
    it.label(it.rect(352 + i * 48, 238, 40, 36, bg=ACCENT_BG if t == "M" else None, stroke=ACCENT if t == "M" else INK),
             t, 16, ACCENT if t == "M" else INK)
it.button(352, 300, 220, 48, "Add to cart", size=20)

it = item("Order summary", S)
it.rect(0, 0, 340, 372)
it.text(24, 20, "Order summary", 20)
for i, (a, b) in enumerate([("Product one", "€ 49.00"), ("Product two", "€ 19.00"), ("Shipping", "€ 4.90")]):
    it.text(24, 64 + i * 36, a, 16)
    it.text(316, 64 + i * 36, b, 16, align="right")
it.line([(24, 176), (316, 176)], stroke=FAINT)
it.text(24, 190, "Total", 20)
it.text(316, 190, "€ 72.90", 20, align="right")
it.rect(24, 240, 180, 40)
it.text(36, 250, "Discount code", 16, MUTED)
it.button(212, 240, 104, 40, "Apply", "secondary")
it.button(24, 300, 292, 48, "Pay now", size=20)

it = item("Settings list (mobile)", S)
it.rect(0, 0, 300, 372)
it.text(20, 20, "Settings", 28)
rows = [("bell", "Notifications", True), ("eye", "Dark mode", False), ("lock", "Privacy", None),
        ("user", "Account", None), ("info", "About", None)]
for i, (ic, t, on) in enumerate(rows):
    y = 76 + i * 56
    it.icon(ic, 20, y + 14)
    it.text(56, y + 16, t, 16)
    if on is None:
        it.icon("chevron-right", 256, y + 14, 24, MUTED)
    else:
        it.toggle(228, y + 12, on)
    if i < len(rows) - 1:
        it.line([(20, y + 56), (280, y + 56)], stroke=FAINT)

it = item("Profile header", S)
it.rect(0, 0, 560, 200)
it.rect(0, 0, 560, 80, bg=SHADE, round=False)
it.ell(24, 36, 88, 88, bg=PAPER, fillStyle="solid")
it.icon("user", 44, 56, 48, MUTED)
it.text(128, 92, "Name Surname", 20)
it.text(128, 120, "Designer · Berlin", 16, MUTED)
for i, t in enumerate(["128 posts", "2.4k followers", "180 following"]):
    it.text(24 + i * 150, 160, t, 16)
it.button(436, 92, 100, 40, "Edit", "secondary")

it = item("Dashboard layout", S)
it.rect(0, 0, 800, 520)
it.rect(0, 0, 180, 520, bg=SHADE, round=False)
it.text(20, 20, "Logo", 20)
for i, (ic, t) in enumerate([("home", "Dashboard"), ("file", "Reports"), ("user", "Users"), ("settings", "Settings")]):
    col = ACCENT if i == 0 else INK
    it.icon(ic, 20, 80 + i * 40, 24, col)
    it.text(52, 82 + i * 40, t, 16, col)
it.text(204, 20, "Dashboard", 28)
it.rect(560, 20, 220, 36)
it.icon("search", 570, 26, 24, MUTED)
for i, (a, b) in enumerate([("Revenue", "€ 12.4k"), ("Users", "1,204"), ("Churn", "2.1%")]):
    it.rect(204 + i * 196, 80, 180, 96)
    it.text(220 + i * 196, 94, a, 16, MUTED)
    it.text(220 + i * 196, 120, b, 28)
it.rect(204, 196, 380, 300)
it.text(220, 210, "Activity", 16)
for i, h in enumerate([80, 140, 110, 200, 160, 120]):
    it.rect(228 + i * 58, 476 - h, 36, h, bg=ACCENT_BG, stroke=ACCENT, round=False)
it.rect(600, 196, 180, 300)
it.text(616, 210, "Recent", 16)
for i in range(5):
    it.squig(616, 256 + i * 44, 140, MUTED)

it = item("Data table with toolbar", S)
it.rect(0, 0, 200, 40)
it.icon("search", 10, 8, 24, MUTED)
it.text(42, 10, "Search…", 16, MUTED)
it.rect(212, 0, 100, 40)
it.icon("filter", 224, 8)
it.text(256, 10, "Filter", 16)
it.button(340, 0, 140, 40, "Add new")
it.table(0, 56)
it.text(0, 248, "1–3 of 24", 16, MUTED)
it.icon("chevron-left", 424, 246, 24, MUTED)
it.icon("chevron-right", 456, 246)

it = item("Calendar month", S)
it.rect(0, 0, 364, 336)
it.icon("chevron-left", 16, 14)
it.text(182, 16, "November 2026", 20, align="center")
it.icon("chevron-right", 324, 14)
for i, d in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
    it.text(40 + i * 48, 60, d, 16, MUTED, "center")
first = datetime.date(2026, 11, 1).weekday()
for day in range(1, 31):
    k = first + day - 1
    cx, cy = 40 + (k % 7) * 48, 92 + (k // 7) * 38
    if day == 20:
        it.ell(cx - 16, cy - 6, 32, 32, bg=ACCENT_BG, stroke=ACCENT)
    it.text(cx, cy, str(day), 16, ACCENT if day == 20 else INK, "center")

it = item("Kanban board", S)
for c, (t, n) in enumerate([("To do", 3), ("Doing", 2), ("Done", 1)]):
    x = c * 240
    it.rect(x, 0, 224, 360, bg=SHADE)
    it.text(x + 16, 14, t, 20)
    it.text(x + 208, 16, str(n), 16, MUTED, "right")
    for i in range(n):
        y = 56 + i * 96
        it.rect(x + 12, y, 200, 84, bg=PAPER, fillStyle="solid")
        it.text(x + 24, y + 12, "Task title", 16)
        it.squig(x + 24, y + 50, 150, MUTED)

it = item("Chat (mobile)", S)
it.rect(0, 0, 300, 520)
it.line([(0, 56), (300, 56)])
it.icon("arrow-left", 12, 16)
it.ell(48, 12, 32, 32, bg=SHADE)
it.text(90, 18, "Name", 16)
it.label(it.rect(16, 76, 200, 56, bg=SHADE), "Hi! Are we still on\nfor tomorrow?", 16)
it.label(it.rect(110, 148, 174, 40, bg=ACCENT_BG, stroke=ACCENT), "Yes, 10 am works.", 16, ACCENT)
it.label(it.rect(16, 204, 150, 40, bg=SHADE), "Great, see you!", 16)
it.text(150, 260, "10:42", 16, MUTED, "center")
it.line([(0, 460), (300, 460)])
it.rect(12, 472, 230, 36)
it.text(24, 480, "Message…", 16, MUTED)
it.ell(252, 472, 36, 36, bg=ACCENT_BG, stroke=ACCENT)
it.icon("chevron-right", 258, 478, 24, ACCENT)

it = item("Notifications list", S)
it.rect(0, 0, 360, 264)
it.text(20, 16, "Notifications", 20)
it.text(340, 20, "Mark all read", 16, ACCENT, "right")
for i, (ic, t, tm) in enumerate([("mail", "New message from Anna", "2 min ago"), ("heart", "Your post got 12 likes", "1 h ago"),
                                 ("calendar", "Meeting starts in 15 min", "Yesterday")]):
    y = 60 + i * 64
    it.ell(20, y + 8, 36, 36, bg=ACCENT_BG if i < 2 else SHADE, stroke=ACCENT if i < 2 else INK)
    it.icon(ic, 26, y + 14, 24, ACCENT if i < 2 else INK)
    it.text(68, y + 8, t, 16)
    it.text(68, y + 30, tm, 16, MUTED)
    if i < 2:
        it.ell(330, y + 20, 10, 10, bg=ACCENT, stroke=ACCENT, fillStyle="solid")

it = item("Comment thread", S)
for i, (name, x) in enumerate([("Name Surname", 0), ("Other person", 48), ("Name Surname", 48)]):
    y = i * 96
    it.ell(x, y, 36, 36, bg=SHADE)
    it.text(x + 48, y, name, 16)
    it.text(x + 58 + tw(name, 16), y, "2 h", 16, MUTED)
    it.squig(x + 48, y + 34, 300 - x, MUTED)
    it.squig(x + 48, y + 54, 200 - x, MUTED)
    it.text(x + 48, y + 66, "Reply", 16, ACCENT)
it.rect(0, 300, 360, 44)
it.text(12, 312, "Write a comment…", 16, MUTED)

it = item("File list", S)
it.rect(0, 0, 480, 236)
for j, t in enumerate(["Name", "Modified", "Size"]):
    it.text([52, 260, 400][j], 12, t, 16, MUTED)
for i, (ic, t, m, sz) in enumerate([("folder", "Projects", "Today", "-"), ("image", "Photo.jpg", "Yesterday", "2.4 MB"),
                                    ("file", "Notes.md", "12 Nov", "8 KB"), ("file", "Budget.xlsx", "3 Nov", "64 KB")]):
    y = 46 + i * 46
    it.line([(0, y), (480, y)], stroke=FAINT)
    it.icon(ic, 16, y + 10)
    it.text(52, y + 12, t, 16)
    it.text(260, y + 12, m, 16, MUTED)
    it.text(400, y + 12, sz, 16, MUTED)

it = item("Filter panel", S)
it.rect(0, 0, 260, 400)
it.text(20, 16, "Filters", 20)
it.text(240, 20, "Reset", 16, ACCENT, "right")
it.text(20, 64, "Category", 16, MUTED)
for i, t in enumerate(["Shoes", "Jackets", "Bags"]):
    y = 92 + i * 32
    it.rect(20, y, 20, 20, bg=ACCENT_BG if i == 0 else None, stroke=ACCENT if i == 0 else INK)
    if i == 0:
        it.icon("check", 21, y + 1, 18, ACCENT)
    it.text(50, y, t, 16)
it.text(20, 200, "Price", 16, MUTED)
it.line([(20, 240), (240, 240)], stroke=FAINT, strokeWidth=STYLE["strokeWidth"] + 2)
it.line([(70, 240), (180, 240)], stroke=ACCENT, strokeWidth=STYLE["strokeWidth"] + 2)
for cx in (70, 180):
    it.ell(cx - 9, 231, 18, 18, bg=PAPER, stroke=ACCENT, fillStyle="solid")
it.text(20, 256, "€ 10", 16, MUTED)
it.text(240, 256, "€ 90", 16, MUTED, "right")
it.text(20, 300, "In stock only", 16)
it.toggle(188, 296, True)
it.button(20, 340, 220, 44, "Show 24 results")

it = item("Onboarding (mobile)", S)
it.rect(0, 0, 300, 560)
it.text(276, 20, "Skip", 16, MUTED, "right")
it.placeholder(40, 72, 220, 200)
it.text(150, 300, "Plan your week", 28, align="center")
it.text(150, 346, "Short text that explains\nthe benefit in one breath.", 16, MUTED, "center")
for i in range(3):
    it.ell(130 + i * 16, 420, 8, 8, bg=ACCENT if i == 0 else FAINT, stroke=ACCENT if i == 0 else FAINT, fillStyle="solid")
it.button(24, 480, 252, 48, "Next", size=20)

it = item("Mobile list screen", S)
it.rect(0, 0, 300, 620)
it.text(24, 12, "9:41", 16)
it.text(20, 48, "Inbox", 28)
it.icon("search", 256, 54)
for i in range(5):
    y = 104 + i * 72
    it.ell(16, y + 12, 44, 44, bg=SHADE)
    it.text(72, y + 12, "Name Surname", 16)
    it.text(72, y + 34, "Message preview…", 16, MUTED)
    it.text(284, y + 12, "10:42", 16, MUTED, "right")
it.line([(0, 556), (300, 556)])
for i, ic in enumerate(["home", "search", "heart", "user"]):
    it.icon(ic, 25.5 + i * 75, 574, 24, ACCENT if i == 0 else MUTED)

it = item("Navigation drawer (mobile)", S)
it.rect(0, 0, 300, 560)
it.rect(220, 0, 80, 560, bg=INK, stroke=INK, opacity=30, fillStyle="solid", round=False)
it.rect(0, 0, 220, 560, bg=PAPER, fillStyle="solid")
it.ell(20, 24, 48, 48, bg=SHADE)
it.text(20, 84, "Name Surname", 16)
it.text(20, 106, "name@mail.com", 16, MUTED)
it.line([(0, 140), (220, 140)], stroke=FAINT)
for i, (ic, t) in enumerate([("home", "Home"), ("search", "Search"), ("heart", "Saved"), ("settings", "Settings")]):
    col = ACCENT if i == 0 else INK
    it.icon(ic, 20, 160 + i * 48, 24, col)
    it.text(56, 162 + i * 48, t, 16, col)
it.line([(0, 480), (220, 480)], stroke=FAINT)
it.text(20, 500, "Log out", 16, RED)

it = item("Error page (404)", S)
it.rect(0, 0, 560, 360)
it.text(280, 40, "404", 72, MUTED, "center")
it.text(280, 150, "Page not found", 28, align="center")
it.text(280, 196, "The page you're looking for doesn't exist.", 16, MUTED, "center")
it.button(205, 248, 150, 44, "Go home", size=20)

# ---------------------------------------------------------------- icons
S = "Icons"
for name in ICONS:
    item("Icon / " + name, S).icon(name, 0, 0, 32)

# ---------------------------------------------------------------- annotations
S = "Annotations and post-its"
for (bg, t), a in zip([("#ffec99", "Idea"), ("#fcc2d7", "Question"), ("#a5d8ff", "To do"),
                       ("#b2f2bb", "Done"), ("#ffd8a8", "Bug"), ("#d0bfff", "Note")], [-3, 2, -1.5, 3, -2, 1.5]):
    it = item("Post-it / " + t.lower(), S)
    # Nimbus: draw the label as Markdown, fit the note to it, never below its own height (stickyHeight)
    it.label(it.rect(0, 0, 160, 160, bg=bg, round=False, angle=math.radians(a),
                     customData={"nimbus": {"sticky": True, "stickyHeight": 160}}), t, 20)

it = item("Numbered marker", S)
it.label(it.ell(0, 0, 32, 32, bg=RED_BG, stroke=RED), "1", 16, RED)

it = item("Callout arrow", S)
it.line([(0, 0), (60, 30), (140, 40)], stroke=RED, curve=True, arrow="end")
it.text(0, -28, "Note here", 16, RED)

it = item("Comment bubble", S)
it.label(it.rect(0, 0, 200, 64), "Comment", 16)
it.line([(24, 64), (20, 84), (48, 64)], stroke=INK)

it = item("Highlight circle", S)
it.ell(0, 0, 180, 80, stroke=RED, strokeWidth=STYLE["strokeWidth"] + 1)

it = item("Tap indicator", S)
it.ell(0, 0, 48, 48, bg=ACCENT_BG, stroke=ACCENT, opacity=50, fillStyle="solid")
it.ell(14, 14, 20, 20, bg=ACCENT, stroke=ACCENT, fillStyle="solid")

it = item("Dimension line", S)
it.line([(0, 30), (320, 30)], stroke=RED, arrow="both")
it.text(160, 0, "320 px", 16, RED, "center")

# ---------------------------------------------------------------- Niehaus wireframe method
S = "Niehaus wireframe"
# Niehaus weight ladder: a level raises an element's visual weight inside its own colour
# (Excalidraw palette shades 0..4); the colour never changes. Shares are the area thresholds per page.
SHADES = {"gray": ["#f8f9fa", "#e9ecef", "#ced4da", "#868e96", "#343a40"],
          "red": ["#fff5f5", "#ffc9c9", "#ff8787", "#fa5252", "#e03131"],
          "blue": ["#e7f5ff", "#a5d8ff", "#4dabf7", "#228be6", "#1971c2"]}
LEVELS = [("Light", "must-have", "~60%"), ("Medium", "tertiary", "~30%"),
          ("Dark", "secondary", "~8%"), ("Black", "primary", "~2%")]


def weigh(it, x, y, w, h, hue, level, t=None, size=16):
    s = SHADES[hue]
    style, col = [(dict(stroke=s[2], strokeWidth=1), s[3]),
                  (dict(stroke=s[4], strokeWidth=1, bg=s[1]), s[4]),
                  (dict(stroke=s[4], strokeWidth=2, bg=s[2], fillStyle="solid"), INK),
                  (dict(stroke=s[4], strokeWidth=4, bg=s[4], fillStyle="solid"), PAPER)][level]
    r = it.rect(x, y, w, h, **style)
    if t:
        it.label(r, t, size, col)


for i, (n, role, share) in enumerate(LEVELS):
    weigh(item(f"Niehaus / {n.lower()} ({role}, {share})", S), 0, 0, 200, 56, "gray", i, n)

it = item("Niehaus / fold line", S)
it.line([(0, 24), (800, 24)], stroke=RED, strokeStyle="dashed", strokeWidth=2)
it.text(800, 0, "Fold", 16, RED, "right")

it = item("Niehaus / legend", S)
it.rect(0, 0, 460, 268)
it.text(16, 14, "Niehaus levels: same color, more weight", 16)
for i, (n, role, share) in enumerate(LEVELS):
    y = 52 + i * 44
    weigh(it, 16, y, 96, 32, "gray", i)
    weigh(it, 124, y, 96, 32, "red", i, "Buy")
    it.text(236, y + 6, f"{n} · {role} · {share}", 16)
it.text(16, 232, "Shares = area per page. Max. 2 primary CTAs.", 16, MUTED)

it = item("Niehaus / example page", S)
it.rect(0, 0, 800, 600)
for x, y, w, h, lvl, t in [(16, 16, 120, 40, 0, "Logo"), (500, 20, 284, 28, 0, "Meta nav"),
                           (16, 72, 768, 44, 1, "Main navigation"), (16, 132, 460, 240, 0, "Key content"),
                           (492, 132, 292, 120, 2, "Secondary focus"), (492, 268, 292, 48, 1, "Trust signals"),
                           (16, 420, 372, 160, 0, "Content"), (412, 420, 372, 160, 0, "Content")]:
    weigh(it, x, y, w, h, "gray", lvl, t)
weigh(it, 570, 328, 140, 44, "blue", 3, "Primary CTA")  # coloured element keeps its hue at full weight
it.line([(0, 400), (800, 400)], stroke=RED, strokeStyle="dashed", strokeWidth=2)
it.text(784, 376, "Fold", 16, RED, "right")


# ---------------------------------------------------------------- output
def clone(it, dx, dy):
    ids = {e["id"]: nid() for e in it.els}
    gids = {}
    out = []
    for e in it.els:
        c = copy.deepcopy(e)
        c["id"], c["x"], c["y"] = ids[e["id"]], e["x"] + dx, e["y"] + dy
        c["seed"] = e["seed"]
        c["groupIds"] = [gids.setdefault(g, nid()) for g in e["groupIds"]]
        if c.get("containerId"):
            c["containerId"] = ids[c["containerId"]]
        if c["boundElements"]:
            c["boundElements"] = [{**b, "id": ids[b["id"]]} for b in c["boundElements"]]
        out.append(c)
    return out


for it in LIB:
    it.done()

lib = {"type": "excalidrawlib", "version": 2, "source": "https://excalidraw.com",
       "libraryItems": [{"id": nid(), "status": "unpublished", "created": 1795000000000 - i, "name": it.name,
                         "elements": it.els} for i, it in enumerate(LIB)]}
json.dump(lib, open(os.path.join(HERE, "scribble-ux.excalidrawlib"), "w"))

# showcase board: one row-wrapped block per section, item name under each item
board, y, MAXW, GAP = [], 0, 2200, 60
sections = list(dict.fromkeys(it.section for it in LIB))
for sec in sections:
    head = Item("", "")
    head.text(0, y, sec, 36)
    board += head.els
    y += 80
    x = rowh = 0
    for it in [i for i in LIB if i.section == sec]:
        _, _, w, h = it.bbox()
        if x and x + w > MAXW:
            x, y, rowh = 0, y + rowh + 50 + GAP, 0
        board += clone(it, x, y)
        cap = Item("", "")
        cap.text(x, y + h + 12, it.name, 16, MUTED)
        board += cap.els
        x += max(w, tw(it.name, 16)) + GAP
        rowh = max(rowh, h)
    y += rowh + 50 + 140

json.dump({"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": board,
           "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}},
          open(os.path.join(HERE, "scribble-ux-showcase.excalidraw"), "w"))

# self-check: every bound text points at a container that lists it back
for it in LIB:
    byid = {e["id"]: e for e in it.els}
    for e in it.els:
        if e.get("containerId"):
            assert any(b["id"] == e["id"] for b in byid[e["containerId"]]["boundElements"]), it.name
print(f"{len(LIB)} library items, {len(board)} showcase elements")
