#!/usr/bin/env python3
"""Build an app UI theme in the graphite style (after Linear), using the same accent colour as the app icon.

    python3 scripts/build.py --name Tide -o out/                 # default accent: 蓝 (blue)
    python3 scripts/build.py --name Tide --accent 紫 -o out/     # or --accent violet
    python3 scripts/build.py --name Ask --category AI -o out/   # no icon yet: the category picks the accent

Writes tokens.json, theme.css, Theme.swift, Theme.kt and tailwind.preset.js to the output folder.
Accent names come from assets/palette.json (Chinese or English names both work). The UI primary
follows the icon accent: 蓝→蓝, 绿→绿, 紫→紫. 珊瑚 coral, 黄 yellow and 灰 gray stay in the app icon
and the UI primary falls back to 蓝 (the script prints a note). Without an icon, --category picks the accent the
icon skill gives that category (AI 紫, 工具 tools 蓝, 图片 黄, 视频 珊瑚, 健康 and 财务 绿); with both, the icon wins.

Every colour comes from three inputs in CIE LCh (D65): the graphite base (one hue, near-zero chroma,
an L ladder per mode), the accent (its hue and chroma; only L moves), and the contrast level. Text
tiers, control borders, primary-text and the status colours start from palette.json and only move L
toward more contrast until they pass on every background they can sit on: canvas, bg, surface,
surface-2, surface-3, elevated, menu-active, selected, and the frost over the page and over mid-grey
content. The set is built twice, standard and high contrast, so tokens.json has four schemes:
light, dark, light-hc and dark-hc. Each scheme also carries the media tokens the editor and viewer use (they are
dark pages in every scheme): four chroma-0 canvas steps, the transparency checkerboard, the viewer scrim, white
handles and guides, the video scrubber's track and the media selection outline; white controls are checked on the scrim
over a white photo, and the scrubber's white played part on its track there.

The script prints the contrast matrix of every scheme. If any pair falls short, or a high-contrast
row is lower than its standard row, it exits with status 1 and writes nothing.
"""
import argparse, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = json.load(open(os.path.join(HERE, "..", "assets", "palette.json"), encoding="utf-8"))
DEFAULT_ACCENT = "蓝"
W = "#FFFFFF"
MID_GREY = "#808080"    # stands in for blurred content scrolling under a bar
TEXT, NON_TEXT = 4.5, 3.0  # WCAG: text on a fill; control borders, focus rings and the primary fill itself
CONTAINER = {"light": 0.90, "dark": 0.85}  # how far a -container is mixed toward the surface
LEVELS = ("standard", "high")
MODES = ("light", "dark")
TIERS = ("text", "text-2", "text-3", "text-placeholder")
SURFACES = ("canvas", "bg", "surface", "surface-2", "surface-3", "elevated")
STATUS = list(PALETTE["status"])
# C10, per contrast level: (assert, target). Text aims for 15:1 and asserts less; high-contrast text
# takes the end of the range (dark L 100, light L 6) and reports what that reaches.
NEED = {
    "standard": {"text": (7, 15), "text-2": (7, 7), "text-3": (4.5, 4.5), "text-placeholder": (3, 3),
                 "accent": (PALETTE["primary"]["text_target"],) * 2},
    "high": {"text": (12, 15), "text-2": (10, 10), "text-3": (7, 7), "text-placeholder": (4.5, 4.5),
             "accent": (7, 7)},
}

ORDER = ["canvas", "bg", "surface", "surface-2", "surface-3", "elevated", "menu-active",
         "border", "border-strong", "text", "text-2", "text-3", "text-placeholder",
         "primary", "on-primary", "primary-hover", "primary-pressed", "primary-text",
         "primary-container", "on-primary-container", "selected", "focus", "selection",
         "success", "success-container", "on-success", "warning", "warning-container", "on-warning",
         "danger", "danger-container", "on-danger", "info", "info-container", "on-info",
         "in-progress", "hover", "pressed", "disabled-fg", "disabled-bg", "scrim", "scrim-menu",
         "frost", "frost-border", "frost-highlight", "inverse-surface", "on-inverse", "inverse-primary",
         "media-black", "media-dark", "media-mid", "media-white", "checker-a", "checker-b",
         "on-media", "viewer-scrim", "media-edge", "media-guide", "media-track", "media-selected"]


# ---------- colour maths ----------
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    """t = 0 gives a, t = 1 gives b"""
    a, b = rgb(a), rgb(b)
    return hexc(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def _linear(v):
    v /= 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def lum(h):
    r, g, b = (_linear(v) for v in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rgba(h, a):
    r, g, b = rgb(h)
    return f"rgba({r}, {g}, {b}, {a:g})"


def split(c):
    """'#RRGGBB' or 'rgba(r, g, b, a)' -> ('RRGGBB', alpha)"""
    if c.startswith("#"):
        return c.lstrip("#").upper(), 1.0
    r, g, b, a = (float(v) for v in re.findall(r"[\d.]+", c))
    return "%02X%02X%02X" % (int(r), int(g), int(b)), a


def over(fg, bg):
    """composite a colour (hex or rgba) over an opaque hex background"""
    h, a = split(fg)
    return mix(bg, "#" + h, a)


# ---------- CIE LCh (D65) ----------
XN, YN, ZN = 0.95047, 1.0, 1.08883


def _lch_linear(L, C, H):
    """LCh -> linear sRGB, not clipped"""
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda t: t ** 3 if t > 6 / 29 else 3 * (6 / 29) ** 2 * (t - 4 / 29)
    X, Y, Z = XN * inv(fx), YN * inv(fy), ZN * inv(fz)
    return (3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z,
            -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z,
            0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z)


def lch_to_hex(L, C, H):
    """LCh -> hex; out of gamut, chroma drops (same L and H) until the colour fits"""
    fits = lambda c: all(-1e-6 <= v <= 1 + 1e-6 for v in _lch_linear(L, c, H))
    if not fits(C):
        lo, hi = 0.0, C
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if fits(mid) else (lo, mid)
        C = lo
    gamma = lambda v: 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return hexc(tuple(255 * gamma(max(0.0, min(1.0, v))) for v in _lch_linear(L, C, H)))


def hex_to_lch(h):
    r, g, b = (_linear(v) for v in rgb(h))
    X = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    Y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    Z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    f = lambda t: t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29
    fx, fy, fz = f(X / XN), f(Y / YN), f(Z / ZN)
    L, a, bb = 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def reach(L, C, H, step, backs, need, lo=0.0, hi=100.0):
    """move only L (step 0.5 lighter or -0.5 darker; H and C stay, C drops when out of gamut) until the
    colour reaches `need` on every background in `backs`. Returns (hex, L, ok); when L runs out of
    range it returns the end of the range with ok False, and the audit reports the shortfall."""
    while lo <= L <= hi:
        c = lch_to_hex(L, C, H)
        if min(contrast(c, b) for b in backs) >= need:
            return c, L, True
        L += step
    L = max(lo, min(hi, L - step))
    return lch_to_hex(L, C, H), L, False


def neutral(L, mode):
    """a graphite neutral at lightness L; L 100 is plain white"""
    if L >= 100:
        return W
    return lch_to_hex(L, PALETTE["base"]["chroma"][mode], PALETTE["base"]["hue"])


def ink_on(c, C):
    """text on a filled colour: white when it passes, else the page colour"""
    return W if contrast(W, c) >= TEXT else C["bg"]


def backgrounds(C):
    """every opaque background a foreground can sit on; frost is composited over the page and over
    mid-grey content (saturate() leaves greys unchanged, and blur only evens content out)"""
    B = {k: C[k] for k in SURFACES + ("menu-active",)}
    B["frost/bg"] = over(C["frost"], C["bg"])
    B["frost/mid"] = over(C["frost"], MID_GREY)
    B["selected"] = C["selected"]
    return B


def find_category(name):
    """an app category by its Chinese or English name (the icon skill's data-category): 工具 tools, 图片 image, 视频 video,
    AI, 健康 health, 财务 finance"""
    for k, v in PALETTE["category"].items():
        if name.strip() == k or name.strip().lower() in [v["en"]] + v.get("aliases", []):
            return k, v
    sys.exit(f"unknown category {name!r}: " + ", ".join(f"{k} ({v['en']})" for k, v in PALETTE["category"].items()))


def find(name):
    """an accent by its Chinese or English name (or an alias: purple, grey), or by one of its two tones from the table
    (#3B7BEA -> 蓝)"""
    tone = "#" + name.strip().lstrip("#").upper()
    for k, v in PALETTE["accent"].items():
        if name.strip() == k or name.strip().lower() in [v["en"]] + v.get("aliases", []) or tone in v["tones"]:
            return k, v
    sys.exit(f"unknown accent {name!r}; pass the colour name, not a colour value: " +
             ", ".join(f"{k} ({v['en']})" for k, v in PALETTE["accent"].items()) +
             " (a tone from that table, such as #3B7BEA, works too)")


def key(mode, level):
    return mode if level == "standard" else mode + "-hc"


# ---------- derive ----------
def primary_fill(tone):
    """the filled primary, one value for both modes and both levels: the accent's hue and chroma at the
    highest L whose white text still reaches fill_target. Returns (hex, L, C, H)."""
    _, C, H = hex_to_lch(tone)
    L = 100.0
    while contrast(W, lch_to_hex(L, C, H)) < PALETTE["primary"]["fill_target"]:
        L -= 0.5
    return lch_to_hex(L, C, H), L, C, H


def scheme(mode, level, ui_accent, prim, start):
    """one colour scheme (mode x contrast level). `start` holds the standard scheme's L values: the
    high-contrast walks continue from there, so they can only end at more contrast, never less (the
    high-contrast frost is more opaque, so a walk from the palette value would stop sooner and darker)."""
    P = PALETTE
    hc, dark = level == "high", mode == "dark"
    up = 0.5 if dark else -0.5  # the L direction that raises contrast against the surfaces
    chroma, hue = P["base"]["chroma"][mode], P["base"]["hue"]
    ladder, text_L, need = P["ladder"][mode], P["text"][level][mode], NEED[level]
    C = {k: neutral(ladder[k], mode) for k in SURFACES}
    L = {k: ladder[k] for k in SURFACES}
    for k, (base, a) in P["alpha"][mode].items():
        if k == "frost" and hc:
            a = P["alpha"]["frost_high"]
        C[k] = rgba(C["elevated"] if base == "elevated" else base, a)
    # current item in menus: in dark mode surface-3 on elevated is only 4 L apart, so white 8 % over elevated
    ma = P["alpha"]["menu_active"].get(mode)
    C["menu-active"] = over(rgba(W, ma), C["elevated"]) if ma else C["surface-3"]

    p, pL, pC, pH = prim
    pr = P["primary"]
    C["primary"], C["on-primary"] = p, W
    # hover and pressed darken in both modes: the fill is already the lightest L white text passes on
    C["primary-hover"] = lch_to_hex(pL - 4, pC, pH)
    C["primary-pressed"] = lch_to_hex(pL - 8, pC, pH)
    C["primary-container"] = mix(p, C["surface"], CONTAINER[mode])
    C["selected"] = over(rgba(p, pr["selected"][mode]), C["bg"])
    C["selection"] = over(rgba(p, pr["selection"][mode]), C["bg"])
    B = list(backgrounds(C).values())

    for tier in TIERS:
        floor, target = need[tier]
        backs = B + [C["selection"]] if tier in ("text", "text-2") else B
        if tier == "text" and hc:
            C[tier], L[tier] = neutral(text_L[tier], mode), text_L[tier]
            continue
        c, l, _ = reach(text_L[tier], chroma, hue, up, backs, floor)
        if target > floor:  # body text: try for the target, but never past L 98 / 6
            c2, l2, ok = reach(l, chroma, hue, up, backs, target, lo=6, hi=98)
            if ok:
                c, l = c2, l2
        C[tier], L[tier] = c, l

    # control borders (inputs, checkboxes, switches that are off) sit on the page, cards, rows and menus
    controls = [C[k] for k in ("bg", "surface", "surface-2", "elevated")]
    C["border-strong"], L["border-strong"], _ = reach(ladder["border-strong"], chroma, hue, up, controls, NON_TEXT)
    if hc:
        C["border"] = C["border-strong"]

    # primary-text: links, the selected tab, focus; standard starts at the fill's L, high at the standard result
    acc = need["accent"][0]
    c, l, _ = reach(start["primary-text"] if hc else pL, pC, pH, up, B + [C["primary-container"]], acc)
    C["primary-text"], L["primary-text"] = c, l
    C["on-primary-container"] = C["focus"] = c

    # status colours are text on every surface and on their own container; the one from the
    # primary's own accent reuses primary-text (its badge then carries an icon)
    for s, src in P["status"].items():
        if src == ui_accent:
            C[s], C[s + "-container"], L[s] = c, C["primary-container"], l
        else:
            tone = P["accent"][src]["tones"][1]
            sL, sC, sH = hex_to_lch(tone)
            box = mix(tone, C["surface"], CONTAINER[mode])
            C[s], L[s], _ = reach(start[s] if hc else sL, sC, sH, up, B + [box], acc)
            C[s + "-container"] = box
        C["on-" + s] = ink_on(C[s], C)
    C["in-progress"] = C["info"]  # a running task reads as information, never as a warning

    C["disabled-fg"], C["disabled-bg"] = C["text-placeholder"], C["surface-3"]

    # media pages (editor, viewer) are dark in every scheme. The canvas steps and the checkerboard have chroma 0, so
    # they never tint a photo; white controls sit on the viewer scrim, white handles and guides carry a dark edge.
    # A selected picture gets an outline in primary-text and a check, never a tint over it.
    M = P["media"]
    for k, l in M["canvas"].items():
        C["media-" + k] = lch_to_hex(l, 0, 0)
    for k, l in M["checker"].items():
        C["checker-" + k] = lch_to_hex(l, 0, 0)
    C["on-media"] = W
    for k, (base, a) in M["alpha"].items():
        C[k] = rgba(base, a)
    C["media-selected"] = C["primary-text"]
    return C, L


def derive(name, accent=None, category=None):
    """accent is the app icon's accent; without an icon the category gives the accent its icon would have"""
    cat = find_category(category) if category else None
    if cat and accent and PALETTE["accent"][find(accent)[0]].get("ui_primary") != PALETTE["accent"][cat[1]["icon"]]["ui_primary"]:
        print(f"note: the icon accent {find(accent)[0]} and the category {cat[0]} ({cat[1]['en']}) give different UI primaries; "
              f"following the icon (the app icon and its UI stay one family)")
    ak, a = find(accent or (cat[1]["icon"] if cat else DEFAULT_ACCENT))
    source = {"accent": ak, "en": a["en"], **({"category": cat[0]} if cat else {})}
    ui = a.get("ui_primary", ak)
    if ui != ak:
        why = ("a warm accent" if a.get("warm") else
               "too close to the grey text (selected and unselected would look the same)")
        print(f"note: {ak} ({a['en']}) is {why} and never the UI primary; "
              f"using {ui} instead (keep {ak} in the app icon)")
        source["icon-accent"] = ak
        ak, a = find(ui)
        source.update(accent=ak, en=a["en"])

    prim = primary_fill(a["tones"][1])
    colors, levels, std = {}, {"primary": prim[1]}, {}
    for level in LEVELS:
        for mode in MODES:
            C, L = scheme(mode, level, ak, prim, std.get(mode))
            colors[key(mode, level)], levels[key(mode, level)] = C, {k: round(v, 2) for k, v in L.items()}
            if level == "standard":
                std[mode] = L
        # inverse roles (Material's snackbar): the other mode's surface-3, text and primary-text
        for mode, other in (("light", "dark"), ("dark", "light")):
            C, O = colors[key(mode, level)], colors[key(other, level)]
            C["inverse-surface"], C["on-inverse"], C["inverse-primary"] = O["surface-3"], O["text"], O["primary-text"]
    colors = {k: {t: colors[k][t] for t in ORDER} for k in (key(m, lv) for lv in LEVELS for m in MODES)}

    return {
        "name": name,
        "style": "graphite",
        "source": source,
        "base": PALETTE["base"],
        "levels": levels,
        "color": colors,
        "radius": {"xs": 4, "sm": 6, "md": 8, "lg": 12, "xl": 16, "full": 9999},
        "space": {"0.5": 2, "1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48},
        "size": {
            "hit-min": {"ios": 44, "android": 48},
            "control-h": {"desktop": {"xs": 20, "sm": 24, "md": 28, "lg": 32}, "mobile": {"md": 44, "lg": 50}},
            "row": {"desktop": 36, "compact": 32, "mobile": 60, "mobile-single": 44, "android": 72},
            "sidebar": {"width": 240, "item": 28},
            "view-header": 44, "filter-bar": 36, "kbd": 18,
            "media": MEDIA_SIZE,
            "prompt": {"min": 48, "max-lines": 6},
        },
        "font": FONT,
        "elevation": ELEVATION,
        "motion": MOTION,
        "haptic": HAPTIC,
        "gradient": {"viewer-scrim": {"color": PALETTE["media"]["alpha"]["viewer-scrim"][0],
                                      "stops": PALETTE["media"]["scrim_stops"]}},
        "blur": {"frost": 24, "saturate": 1.5,
                 "opacity": {"standard": PALETTE["alpha"]["light"]["frost"][1], "high": PALETTE["alpha"]["frost_high"]}},
        "icon": {"size": {"sm": 16, "md": 20, "lg": 24}, "stroke": 1.5, "non-scaling": True,
                 "web": "Lucide, stroke-width 1.5 with vector-effect: non-scaling-stroke",
                 "ios": "SF Symbols, weight .regular",
                 "android": "Material Symbols Rounded, weight 300, fill 0, grade 0, optical size 24"},
    }


# ---------- type, elevation, motion (fixed by the style, not by the accent) ----------
def inter_tracking(px):
    """Inter's dynamic metrics, in em"""
    return round(-0.0223 + 0.185 * math.exp(-0.1745 * px), 4)


# web and desktop (C3): size, line height, weight, tracking in em; opsz 32 is Inter Display
WEB_TYPE = {
    "display": (32, 38, 590, -0.022), "title-1": (24, 32, 590, -0.0195), "title-2": (18, 24, 590, -0.0143),
    "title-3": (15, 20, 590, -0.0088), "body": (14, 20, 400, -0.0062), "body-medium": (14, 20, 510, -0.0062),
    "small": (13, 18, 400, -0.0032), "caption": (12, 16, 510, 0.0005), "micro": (11, 14, 510, 0.0048),
}
# phones (C3): semantic name -> SwiftUI text style, weight, and its size and line height at the default
# Dynamic Type size (the mobile web --t-* variables use the same numbers in Inter)
PHONE_TYPE = {
    "page-title": ("largeTitle", "bold", 34, 41),
    "card-title": ("headline", "semibold", 17, 22),
    "long-text": ("body", "regular", 17, 22),
    "row-title": ("subheadline", "medium", 15, 20),
    "row-meta": ("footnote", "regular", 13, 18),
    "section-header": ("footnote", "medium", 13, 18),
    "tag-label": ("caption", "medium", 12, 16),
    "amount": ("subheadline", "medium", 15, 20),
    "timecode": ("footnote", "medium", 13, 18),
}
TABULAR = {"amount", "timecode"}  # digits keep one width, so a running time or a changing amount never jitters
WEB_WEIGHT = {"regular": 400, "medium": 510, "semibold": 590, "bold": 590}  # the web never uses 700
# long Chinese paragraphs need more air than the system body's 17/22: the web sets 17/28, iOS adds the difference
# as line spacing (.longText())
LONG_TEXT_LINE = 28
# the phone text variables before the graphite style (named after the iOS text styles), kept for one version with
# their old size and line height, in Inter at the web weights (700 and 600 become 590): size, line height, weight
LEGACY_PHONE_TYPE = {
    "large-title": (34, 41, 590), "title-1": (28, 34, 590), "title-2": (22, 28, 590), "title-3": (20, 25, 590),
    "headline": (17, 22, 590), "body": (17, 22, 400), "body-long": (17, 28, 400), "callout": (16, 21, 400),
    "subhead": (15, 20, 400), "footnote": (13, 18, 400), "caption": (12, 16, 510),
}
# Material 3 type scale (sp): size, line height, weight, tracking
ANDROID_TYPE = {
    "displayLarge": (57, 64, 400, -0.25), "displayMedium": (45, 52, 400, 0), "displaySmall": (36, 44, 400, 0),
    "headlineLarge": (32, 40, 400, 0), "headlineMedium": (28, 36, 400, 0), "headlineSmall": (24, 32, 400, 0),
    "titleLarge": (22, 28, 400, 0), "titleMedium": (16, 24, 500, 0.15), "titleSmall": (14, 20, 500, 0.1),
    "bodyLarge": (16, 24, 400, 0.5), "bodyMedium": (14, 20, 400, 0.25), "bodySmall": (12, 16, 400, 0.4),
    "labelLarge": (14, 20, 500, 0.1), "labelMedium": (12, 16, 500, 0.5), "labelSmall": (11, 16, 500, 0.5),
}
ANDROID_TIMECODE = "labelLarge"  # 14 sp, 500; tabular in Theme.kt (Typography.timecode)
FONT = {
    "web": {
        "family": "InterVariable, Inter, 'PingFang SC', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "mono": "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, monospace",
        "load": "https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&display=swap",
        "features": ["cv01", "ss03"],
        "scale": {k: {"size": s, "line": lh, "weight": w, "tracking": tr, "opsz": min(max(s, 14), 32)}
                  for k, (s, lh, w, tr) in WEB_TYPE.items()},
        "phone": {k: {"size": s, "line": LONG_TEXT_LINE if k == "long-text" else lh, "weight": WEB_WEIGHT[w],
                      "tracking": inter_tracking(s)}
                  for k, (_, w, s, lh) in PHONE_TYPE.items()},
    },
    "ios": {
        "family": "SF Pro (system font), PingFang SC; no extra tracking",
        "styles": {k: {"style": st, "weight": w, "size": s, "line": lh, **({"tabular": True} if k in TABULAR else {}),
                       **({"line-spacing": LONG_TEXT_LINE - lh} if k == "long-text" else {})}
                   for k, (st, w, s, lh) in PHONE_TYPE.items()},
    },
    "android": {
        "family": "Roboto Flex",
        "scale": {k: {"size": s, "line": lh, "weight": w, "tracking": tr} for k, (s, lh, w, tr) in ANDROID_TYPE.items()},
        "timecode": {"style": ANDROID_TIMECODE, "tabular": True},
    },
}
# box-shadow layers per mode: [x, y, blur, spread, opacity of black]. elev-0 is none (cards and lists
# only have the hairline); 2 = menus, tooltips, toasts, floating bars; 3 = dialogs and the command menu
ELEVATION = {
    "light": {"0": [], "2": [[0, 4, 12, 0, 0.06], [0, 8, 24, 0, 0.10]], "3": [[0, 8, 16, 0, 0.06], [0, 24, 64, 0, 0.12]]},
    "dark": {"0": [], "2": [[0, 8, 24, 0, 0.50]], "3": [[0, 16, 48, 0, 0.60]]},
}
# zoom: the grid-to-viewer shared-element transition and a double-tap zoom
DURATION = {"hover-in": 0, "hover-out": 150, "fast": 100, "standard": 180, "slow": 250, "zoom": 300}
MOTION = {
    "duration": DURATION,
    "exit": {k: round(DURATION[k] * 2 / 3) for k in ("fast", "standard", "slow", "zoom")},  # exits take 2/3 of the entry
    "ease": {"enter": [0.2, 0, 0, 1], "exit": [0.3, 0, 1, 1]},
    "ios": {"spring": {"response": 0.3, "dampingFraction": 0.9}},
    "android": {"scheme": "MotionScheme.standard()",
                "spatial": {"dampingRatio": 0.9, "stiffness": 700}, "effects": {"dampingRatio": 1.0, "stiffness": 1600}},
    "reduced": "durations go to 0 ms: no movement or scaling, at most a fade",
    # photos and video: pinch from fit (1) to zoom-max, a double tap toggles fit and zoom-double-tap; pans keep their
    # momentum (deceleration per ms, iOS UIScrollView .normal; Android uses its own fling decay) and rubber-band at the
    # edges; a swipe down closes the viewer past dismiss-distance of the height or dismiss-velocity pt/s; sliders and
    # dials snap to their detent within detent of the range
    "gesture": {"zoom-double-tap": 2.5, "zoom-max": 8, "deceleration": 0.998, "rubber-band": 0.55,
                "dismiss-distance": 0.25, "dismiss-velocity": 800, "detent": 0.02},
}
# media and AI component sizes (pt / dp / px): the editor's tool tray, sliders, crop handles, the video timeline and
# the audio waveform under it, the thumbnail grid and its selection, the transparency checkerboard and the viewer scrim's height
MEDIA_SIZE = {"tool-tray": 64, "tool-item": 64, "slider-track": 4, "slider-thumb": 24, "slider-tick": 8,
              "crop-handle": 20, "crop-stroke": 3, "playhead": 2, "playhead-knob": 10, "timeline": 48, "trim-handle": 14,
              "waveform": 24, "thumb-gap": 2, "select-outline": 3, "select-check": 22, "checker": 8, "viewer-scrim": 140}
# the CSS variable of each (Swift Size and Kotlin AppSize use the key in camelCase)
MEDIA_CSS = {"tool-tray": "tool-tray-h", "tool-item": "tool-item-w", "slider-track": "slider-track-h",
             "slider-tick": "slider-tick-h", "playhead": "playhead-w", "timeline": "timeline-h",
             "trim-handle": "trim-handle-w", "waveform": "waveform-h", "checker": "checker-size", "viewer-scrim": "viewer-scrim-h"}
# one haptic per role: SwiftUI sensoryFeedback (iOS 17+; Theme.swift falls back to the UIKit generators), Compose
# HapticFeedbackType (Compose UI 1.8+) and the Android HapticFeedbackConstants it maps to, and a navigator.vibrate
# pattern in ms for the web (Android browsers only; iOS Safari has no vibration)
HAPTIC = {
    "selection": {"ios": "selection", "compose": "SegmentTick", "android": "SEGMENT_TICK", "web": [10]},
    "snap": {"ios": "impact(weight: .light)", "compose": "GestureThresholdActivate",
             "android": "GESTURE_THRESHOLD_ACTIVATE", "web": [16]},
    "success": {"ios": "success", "compose": "Confirm", "android": "CONFIRM", "web": [12, 80, 24]},
    "failure": {"ios": "error", "compose": "Reject", "android": "REJECT", "web": [32, 60, 32]},
}


# ---------- contrast audit ----------
COLUMNS = list(SURFACES) + ["menu-active", "frost/bg", "frost/mid", "selected"]


LEGEND = "'!' is below the assertion (fails), '~' passes the assertion but misses the target"


def audit(t):
    """print the contrast matrix of every scheme; return the failures and the cells that miss their target"""
    fails, near, out, low = [], {}, [], {}
    for level in LEVELS:
        N = NEED[level]
        out.append(f"\n[{level}]")
        rows = [(tier, *N[tier]) for tier in TIERS] + [(fg, *N["accent"]) for fg in ["primary-text"] + STATUS]
        for mode in MODES:
            k = key(mode, level)
            C = t["color"][k]
            B = backgrounds(C)
            out.append(f"{k}: frost {C['frost']} -> over bg {B['frost/bg']}, over {MID_GREY} {B['frost/mid']}")
            out.append(f"  {'':17}" + "".join(f"{c:>12}" for c in COLUMNS) + "   need / target")
            for fg, need, target in rows:
                cells, vals = [], []
                for col in COLUMNS:
                    r = contrast(C[fg], B[col])
                    vals.append(r)
                    cells.append(f"{r:>11.2f}{'!' if r < need else ('~' if r < target else ' ')}")
                    if r < need:
                        fails.append(f"{k}: {fg} on {col} {r:.2f} < {need}")
                    elif r < target:
                        near.setdefault((k, fg, target), []).append(r)
                low[(k, fg)] = min(vals)
                out.append(f"  {fg:17}" + "".join(cells) + f"   {need:g} / {target:g}")
            acc = N["accent"][0]
            pairs = [("on-primary", b, TEXT) for b in ("primary", "primary-hover", "primary-pressed")]
            pairs += [("primary", b, NON_TEXT) for b in ("bg", "surface")]
            pairs += [(f, b, NON_TEXT) for f in ("border-strong", "focus") for b in ("bg", "surface", "surface-2", "elevated")]
            pairs += [("primary-text", "primary-container", acc)] + [(s, s + "-container", acc) for s in STATUS]
            pairs += [("on-" + s, s, TEXT) for s in STATUS]
            pairs += [("text", "selection", N["text"][0]), ("text-2", "selection", N["text-2"][0])]
            pairs += [("on-inverse", "inverse-surface", TEXT), ("inverse-primary", "inverse-surface", TEXT)]
            # the slider's filled part against its track, and the media selection outline on the pages a grid sits on
            pairs += [("primary", "surface-3", NON_TEXT)] + [("media-selected", b, NON_TEXT) for b in ("bg", "surface")]
            pairs += [("on-media", b, TEXT) for b in ("media-black", "media-dark")]
            checks = [(f"{f} / {b}", C[f], C[b], need) for f, b, need in pairs]
            # Compose's colorScheme.primary is primary-text, so its onPrimary (checkbox ticks, switch thumbs) sits on it
            checks.append(("M3 onPrimary / primary-text", ink_on(C["primary-text"], C), C["primary-text"], TEXT))
            # white viewer controls on the scrim over the worst photo, a white one (and so over any lighter canvas step)
            checks.append(("on-media / viewer-scrim over white", C["on-media"], over(C["viewer-scrim"], C["media-white"]), TEXT))
            # the video scrubber: its white played part against the track, on black and on the scrim over a white photo
            checks.append(("scrubber on-media / media-track over media-black", C["on-media"],
                           over(C["media-track"], C["media-black"]), NON_TEXT))
            checks.append(("scrubber on-media / media-track over scrim over white", C["on-media"],
                           over(C["media-track"], over(C["viewer-scrim"], C["media-white"])), NON_TEXT))
            if mode == "dark":
                # the editor and viewer are dark pages: their text, links, outline and playhead sit on the dark canvas steps
                for b in ("media-black", "media-dark"):
                    checks += [(f"{f} / {b}", C[f], C[b], N[f][0]) for f in TIERS[:3]]
                    checks += [(f"primary-text / {b}", C["primary-text"], C[b], acc),
                               (f"media-selected / {b}", C["media-selected"], C[b], NON_TEXT),
                               (f"playhead primary / {b}", C["primary"], C[b], NON_TEXT)]
            row = []
            for label, f, b, need in checks:
                r = contrast(f, b)
                row.append(f"{label} {r:.2f}{'!' if r < need else ''}")
                if r < need:
                    fails.append(f"{k}: {label} {r:.2f} < {need:g}")
            out.append("  pairs (on-* and fills 4.5; borders, focus, slider fill, scrubber, media outline and playhead 3; the rest as the matrix):")
            for i in range(0, len(row), 4):
                out.append("    " + "   ".join(row[i:i + 4]))
    # the viewer scrim holds at least the checked opacity under the controls: every stop but the last, which fades out
    held = min(o for _, o in PALETTE["media"]["scrim_stops"][:-1])
    if held < PALETTE["media"]["alpha"]["viewer-scrim"][1]:
        fails.append(f"viewer scrim gradient drops to {held:g} under the controls, below the checked viewer-scrim opacity")
    # high contrast only ever adds contrast: every row's lowest value is at least the standard one
    for mode in MODES:
        for fg in list(TIERS) + ["primary-text"] + STATUS:
            s, h = low[(mode, fg)], low[(mode + "-hc", fg)]
            if h < s - 1e-9:
                fails.append(f"{mode}-hc: {fg} lowest {h:.2f} is below standard {s:.2f}")
    print(f"contrast ({LEGEND}; every row is checked on every column)" + "\n".join(out))
    return fails, near


def near_summary(near):
    """one line for the end of the output, where tail still shows it"""
    if not near:
        return f"legend: {LEGEND}; no '~' cells"
    parts = [f"{k} {fg} x{len(v)} ({min(v):.2f}-{max(v):.2f}, target {target:g})" for (k, fg, target), v in near.items()]
    return f"legend: {LEGEND}; '~' cells: " + ", ".join(parts)


def credit(t):
    s = t["source"]
    note = f"; app icon keeps {s['icon-accent']}" if "icon-accent" in s else ""
    return f"accent {s['accent']} ({s['en']}){note}"


def camel(k):
    p = k.replace(".", "_").split("-")
    return p[0] + "".join(x[:1].upper() + x[1:] for x in p[1:])


def pascal(k):
    c = camel(k)
    return c[:1].upper() + c[1:]


def num(x):
    return f"{x:g}"


def fill(template, **subs):
    for k, v in subs.items():
        template = template.replace(f"@@{k}@@", str(v))
    return template


def opaque_keys(t):
    """tokens that are opaque in all four schemes (border is translucent except in high contrast)"""
    return [k for k in ORDER if all(t["color"][s][k].startswith("#") for s in t["color"])]


# ---------- emit: CSS ----------
def shadow_css(layers):
    if not layers:
        return "none"
    return ", ".join(f"{x}px {y}px {b}px{f' {s}px' if s else ''} rgba(0, 0, 0, {a:g})" for x, y, b, s, a in layers)


def legacy_type(F):
    """old phone text name -> the new phone style with the same size, line height and weight, or None"""
    same = {(v["size"], v["line"], v["weight"]): k for k, v in reversed(list(F["phone"].items()))}
    return {k: same.get(v) for k, v in LEGACY_PHONE_TYPE.items()}


def css(t):
    out = [f"""/* {t['name']} theme: generated by rian-app-theme (graphite), {credit(t)}.
   Fonts: <link rel="stylesheet" href="{t['font']['web']['load']}">
   (or self-host InterVariable.woff2 4.1). Colours: light and dark follow prefers-color-scheme, or
   data-theme="light" / "dark" on any element; prefers-contrast: more switches to the high-contrast set. */"""]
    S, F, M = t["size"], t["font"]["web"], t["motion"]
    common = [f"  --r-{k}: {v}px;" for k, v in t["radius"].items()]
    common += [f"  --s-{k.replace('.', '_')}: {v}px;" for k, v in t["space"].items()]
    common.append(f"  --hit-min: {S['hit-min']['ios']}px; /* 48 on Android */")
    common += [f"  --control-h-{k}: {v}px;" for k, v in S["control-h"]["desktop"].items()]
    common += [f"  --control-h-mobile-{k}: {v}px;" for k, v in S["control-h"]["mobile"].items()]
    row = S["row"]
    common += [f"  --row-h: {row['desktop']}px;", f"  --row-h-compact: {row['compact']}px;",
               f"  --row-h-mobile: {row['mobile']}px;", f"  --row-h-mobile-single: {row['mobile-single']}px;",
               f"  --sidebar-w: {S['sidebar']['width']}px;", f"  --sidebar-item-h: {S['sidebar']['item']}px;",
               f"  --view-header-h: {S['view-header']}px;", f"  --filter-bar-h: {S['filter-bar']}px;",
               f"  --kbd-h: {S['kbd']}px;"]
    common.append("  /* media and AI components: tool tray, sliders, crop handles, video timeline, thumbnail grid and its selection,\n"
                  "     checkerboard squares, viewer scrim; the prompt field grows from its minimum height to max-lines, then scrolls */")
    common += [f"  --{MEDIA_CSS.get(k, k)}: {v}px;" for k, v in S["media"].items()]
    common += [f"  --prompt-min-h: {S['prompt']['min']}px;", f"  --prompt-max-lines: {S['prompt']['max-lines']};"]
    common += [f"  --font: {F['family']};", f"  --font-mono: {F['mono']};"]
    common.append("  /* desktop and web text: --td-* is a font shorthand, --tr-td-* its tracking (the .td-* classes add opsz and features) */")
    for k, v in F["scale"].items():
        common.append(f"  --td-{k}: {v['weight']} {v['size']}px/{v['line']}px var(--font);")
        common.append(f"  --tr-td-{k}: {v['tracking']:g}em;")
    common.append("  /* phone-sized text for mobile web: the same sizes as the iOS text styles, in Inter (long-text 17/28 for Chinese paragraphs) */")
    for k, v in F["phone"].items():
        common.append(f"  --t-{k}: {v['weight']} {v['size']}px/{v['line']}px var(--font);")
        common.append(f"  --tr-{k}: {v['tracking']:g}em;")
    common.append("  /* old phone text names, kept for one version: same size and line height as before, in Inter */")
    for k, new in legacy_type(F).items():
        size, line, weight = LEGACY_PHONE_TYPE[k]
        common.append(f"  --t-{k}: var(--t-{new});" if new else f"  --t-{k}: {weight} {size}px/{line}px var(--font);")
        common.append(f"  --tr-{k}: var(--tr-{new});" if new else f"  --tr-{k}: {inter_tracking(size):g}em;")
    common.append("  /* motion: durations, plus the enter and exit curves; exits take 2/3 of the entry */")
    common += [f"  --m-{k}: {v}ms;" for k, v in M["duration"].items()]
    common += [f"  --m-{k}-exit: {v}ms;" for k, v in M["exit"].items()]
    common += [f"  --ease-{k}: cubic-bezier({', '.join(num(x) for x in v)});" for k, v in M["ease"].items()]
    common += [f"  --icon-{k}: {v}px;" for k, v in t["icon"]["size"].items()]
    common.append(f"  --icon-stroke: {t['icon']['stroke']};")
    common += [f"  --frost-blur: {t['blur']['frost']}px;", f"  --frost-saturate: {t['blur']['saturate']};"]
    G = t["gradient"]["viewer-scrim"]
    stops = ", ".join(f"{rgba(G['color'], o)} {p * 100:g}%" for p, o in G["stops"])
    common += ["  /* the viewer scrim, from the screen edge inward: white controls of the photo and video viewer sit on it */",
               f"  --viewer-scrim-top: linear-gradient(to bottom, {stops});",
               f"  --viewer-scrim-bottom: linear-gradient(to top, {stops});",
               "  --checker-image: repeating-conic-gradient(var(--c-checker-a) 0 25%, var(--c-checker-b) 0 50%);"]
    common.append("  /* gestures, for your scripts: zoom range from fit, pan momentum per ms, rubber band, viewer dismissal\n"
                  "     (share of the height, pt/s), slider and dial detent (share of the range) */")
    common += [f"  --gesture-{k}: {num(v)};" for k, v in M["gesture"].items()]
    common.append("  /* haptics: navigator.vibrate patterns in ms (Android browsers; iOS Safari has no vibration), e.g.\n"
                  "     navigator.vibrate?.(getComputedStyle(document.documentElement).getPropertyValue('--haptic-snap').split(',').map(Number)) */")
    common += [f"  --haptic-{k}: {', '.join(str(x) for x in v['web'])};" for k, v in t["haptic"].items()]
    common += ["  /* old names, kept for one version: --m-spring bounced and is now the standard entry; --icon-xl (28) is lg (24).",
               "     --control-h-sm / md / lg changed meaning (desktop 24 / 28 / 32): see rules.md, upgrading */",
               "  --m-spring: var(--m-standard) var(--ease-enter);", "  --icon-xl: var(--icon-lg);"]
    out.append(":root {\n" + "\n".join(common) + "\n}")

    rgb_keys = set(opaque_keys(t))

    def block(sel, k, indent=""):
        C, mode = t["color"][k], k.split("-")[0]
        lines = [f"  --c-{n}: {v};" for n, v in C.items()]
        lines += [f"  --c-{n}-rgb: {' '.join(str(x) for x in rgb(C[n]))};" for n in ORDER if n in rgb_keys]
        lines += [f"  --elev-{n}: {shadow_css(layers)};" for n, layers in t["elevation"][mode].items()]
        lines.append("  /* old names, kept for one version; elev-1 was the card shadow, and cards now have none */")
        lines += ["  --c-state-hover: var(--c-hover);", "  --c-state-pressed: var(--c-pressed);", "  --elev-1: var(--elev-0);"]
        lines.append(f"  color-scheme: {mode};")
        text = f"{sel} {{\n" + "\n".join(lines) + "\n}"
        return text.replace("\n", "\n" + indent) if indent else text

    def media(query, sel, k):
        return f"@media {query} {{\n  " + block(sel, k, "  ") + "\n}"

    light, dark, auto_dark = ':root, [data-theme="light"]', '[data-theme="dark"]', ':root:not([data-theme="light"])'
    out.append(block(light, "light"))
    out.append(media("(prefers-color-scheme: dark)", auto_dark, "dark"))
    out.append(block(dark, "dark"))
    out.append("/* high contrast (prefers-contrast: more): the text tiers, primary-text and the status colours move\n"
               "   further from the surfaces, border becomes border-strong and the frost is 94 % opaque */")
    out.append(media("(prefers-contrast: more)", light, "light-hc"))
    out.append(media("(prefers-contrast: more) and (prefers-color-scheme: dark)", auto_dark, "dark-hc"))
    out.append(media("(prefers-contrast: more)", dark, "dark-hc"))

    out.append("""/* keyboard focus: a 2 px ring in the focus colour, 2 px away from the control */
:focus-visible { outline: 2px solid var(--c-focus); outline-offset: 2px; }
::selection { background: var(--c-selection); }""")
    out.append("""/* text fields match :focus-visible on a click too, so they never take that ring. A form field (.input) turns its
   border focus-coloured and 1 px thicker (2 px in all). An inline-edit field (.inline-edit: titles, descriptions) shows
   only the caret; your script adds .kb-focus when it is entered with the keyboard and removes it on blur (rules.md). */
.input { box-sizing: border-box; height: var(--control-h-lg); padding: 0 10px; border: 1px solid var(--c-border-strong);
  border-radius: var(--r-sm); background: var(--c-surface); color: var(--c-text); font: var(--td-body); }
textarea.input { height: auto; min-height: var(--control-h-lg); padding: 6px 10px; }
.input::placeholder { color: var(--c-text-placeholder); opacity: 1; }
.input:focus { outline: none; border-color: var(--c-focus); box-shadow: 0 0 0 1px var(--c-focus); }
.inline-edit { border-radius: var(--r-sm); }
.inline-edit:hover { background: var(--c-surface-2); cursor: text; }
.inline-edit:focus { background: none; }
.inline-edit:focus-visible { outline: none; }
.inline-edit.kb-focus { outline: 2px solid var(--c-focus); outline-offset: 2px; }""")
    out.append("""/* hover: rows, menu items and ghost buttons, only where a pointer can hover. The highlight appears at once and
   fades out over 150 ms. Touch screens get the pressed state instead: at once on touch, a fast fade on release. */
.hoverable { transition: background-color var(--m-hover-out) var(--ease-exit); }
@media (hover: hover) {
  .hoverable:hover { background-color: var(--c-hover); transition-duration: var(--m-hover-in); }
}
@media (hover: none) {
  .hoverable { transition-duration: var(--m-fast); }
}
.hoverable:active { background-color: var(--c-pressed); transition-duration: 0ms; }""")
    out.append("""/* frost (glass): floating bars, the mobile-web tab bar and custom floating buttons; never cards, lists, menus,
   dialogs or toasts (those are elevated). A full-width bar keeps only the hairline on its content side, e.g. border-width: 0 0 1px. */
.frost {
  background: var(--c-frost);
  -webkit-backdrop-filter: blur(var(--frost-blur)) saturate(var(--frost-saturate));
  backdrop-filter: blur(var(--frost-blur)) saturate(var(--frost-saturate));
  border: 1px solid var(--c-frost-border);
  box-shadow: inset 0 1px 0 var(--c-frost-highlight);
}
.frost.floating { box-shadow: inset 0 1px 0 var(--c-frost-highlight), var(--elev-2); }""")
    out.append("""/* keyboard hint: 18 px high, micro 510 with tabular digits, text-2 on surface-2 and a hairline; keys
   4 px apart. A sequence is <kbd class="kbd">G</kbd><span class="kbd-then">then</span><kbd class="kbd">S</kbd>. */
.kbd { box-sizing: border-box; display: inline-grid; place-items: center; min-width: var(--kbd-h); height: var(--kbd-h);
  padding: 0 4px; border-radius: var(--r-xs); font: var(--td-micro); letter-spacing: var(--tr-td-micro);
  font-variant-numeric: tabular-nums; color: var(--c-text-2); background: var(--c-surface-2); border: 1px solid var(--c-border); }
.kbd + .kbd { margin-left: 4px; }
.kbd-then { margin: 0 4px; font: var(--td-micro); color: var(--c-text-3); }
/* the keyboard layer (kbd hints, shortcuts in tooltips and menus, hover) is optional: it shows where a pointer can hover
   (Mac, desktop, an iPad or tablet with a trackpad), or once your script sets data-keyboard on <html> after a
   hardware-keyboard shortcut. Phones never show it; the command menu's phone entry is the search field */
@media (hover: none) {
  :root:not([data-keyboard]) :is(.kbd, .kbd-then) { display: none; }
}""")
    out.append("""/* media pages: the transparency checkerboard; the viewer scrim at the top and bottom edges, under white controls
   (tapping the picture hides both); a selected picture gets an outline inside its edge plus a check badge, never a tint */
.checker { background: var(--checker-image) 0 0 / calc(2 * var(--checker-size)) calc(2 * var(--checker-size)); }
.viewer-scrim-top, .viewer-scrim-bottom { height: var(--viewer-scrim-h); pointer-events: none; }
.viewer-scrim-top { background: var(--viewer-scrim-top); }
.viewer-scrim-bottom { background: var(--viewer-scrim-bottom); }
.media-selected { outline: var(--select-outline) solid var(--c-media-selected); outline-offset: calc(-1 * var(--select-outline)); }""")
    feats = ", ".join(f'"{x}"' for x in F["features"])
    # each text style keeps its tracking in --tr, which inherits: Latin runs inside CJK text take it back from there
    td = [f'.td-{k} {{ font: var(--td-{k}); --tr: var(--tr-td-{k}); letter-spacing: var(--tr); '
          f'font-variation-settings: "opsz" {v["opsz"]}; font-feature-settings: {feats}; }}' for k, v in F["scale"].items()]
    out.append("/* desktop and web text styles: Inter with Linear's cv01 and ss03; opsz 32 is Inter Display */\n" + "\n".join(td))
    phone = [f".t-{k} {{ font: var(--t-{k}); --tr: var(--tr-{k}); letter-spacing: var(--tr); font-feature-settings: {feats};"
             f"{' font-variant-numeric: tabular-nums;' if k in TABULAR else ''} }}" for k in F["phone"]]
    out.append("/* phone-sized text styles for mobile web */\n" + "\n".join(phone))
    out.append("/* old phone text classes, kept for one version */\n" + "\n".join(
        f".t-{k} {{ font: var(--t-{k}); --tr: var(--tr-{k}); letter-spacing: var(--tr); font-feature-settings: {feats}; }}"
        for k in LEGACY_PHONE_TYPE))
    names = ", ".join([f".td-{k}" for k in F["scale"]] + [f".t-{k}" for k in F["phone"]] + [f".t-{k}" for k in LEGACY_PHONE_TYPE])
    out.append("/* Chinese, Japanese and Korean keep their natural spacing: the tracking above is for Latin. On a Chinese page,\n"
               "   Latin words and figures inside these styles get it back when marked lang=\"en\" or .num */\n"
               f":is({names}):is(:lang(zh), :lang(ja), :lang(ko)) {{ letter-spacing: 0; }}\n"
               f":is({names}) :is(:lang(en), .num), :is({names}).num {{ letter-spacing: var(--tr); }}")
    out.append("""/* tabular digits for amounts, times and counts. !important because a font shorthand (the styles above, or your
   own font: var(--td-*)) resets font-variant-numeric, so class="td-caption num" would otherwise lose it */
.num { font-variant-numeric: tabular-nums !important; }""")
    out.append("""/* line icons: Lucide, 1.5 px at every size; default text-3, clickable accents primary-text */
.icon { width: var(--icon-sm); height: var(--icon-sm); flex: none; fill: none; stroke: currentColor;
  stroke-width: var(--icon-stroke); stroke-linecap: round; stroke-linejoin: round; color: var(--c-text-3); }
.icon * { vector-effect: non-scaling-stroke; }
.icon.md { width: var(--icon-md); height: var(--icon-md); }
.icon.lg { width: var(--icon-lg); height: var(--icon-lg); }
.icon.xl { width: var(--icon-lg); height: var(--icon-lg); } /* old name (28 px), kept for one version */
.is-active > .icon, .icon.active { color: var(--c-primary-text); }""")
    out.append("@media (prefers-reduced-motion: reduce) {\n  /* no movement or scaling: every duration goes to 0 */\n  :root {\n"
               + "\n".join(f"    --m-{k}: 0ms;" for k in M["duration"]) + "\n"
               + "\n".join(f"    --m-{k}-exit: 0ms;" for k in M["exit"]) + "\n  }\n}")
    return "\n\n".join(out) + "\n"


# ---------- emit: SwiftUI ----------
SWIFT_DEFAULT_WEIGHT = {"headline": "semibold"}  # every other system text style is regular
# the UIKit generator for each sensoryFeedback, for iOS 15 and 16
UIKIT_HAPTIC = {"selection": "UISelectionFeedbackGenerator().selectionChanged()",
                "impact(weight: .light)": "UIImpactFeedbackGenerator(style: .light).impactOccurred()",
                "success": "UINotificationFeedbackGenerator().notificationOccurred(.success)",
                "error": "UINotificationFeedbackGenerator().notificationOccurred(.error)"}

SWIFT = """// @@title@@
// iOS 15 or later. On iOS 26 and later .frost() is Liquid Glass; earlier versions get a material fallback.
import GameController
import SwiftUI
import UIKit

extension UIColor {
    convenience init(hex: UInt32, alpha: CGFloat = 1) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: alpha)
    }

    /// One of four values, picked from the traits: light or dark, standard or Increase Contrast.
    /// UIKit resolves it again whenever the traits change, so views follow the setting by themselves.
    static func scheme(light: UIColor, dark: UIColor, lightHC: UIColor, darkHC: UIColor) -> UIColor {
        UIColor { traits in
            let high = traits.accessibilityContrast == .high
            if traits.userInterfaceStyle == .dark {
                return high ? darkHC : dark
            }
            return high ? lightHC : light
        }
    }
}

extension Color {
    /// A colour with light, dark and Increase Contrast values (0xRRGGBB, with an opacity per value).
    init(light: UInt32, dark: UInt32, lightHC: UInt32, darkHC: UInt32,
         alpha: (light: CGFloat, dark: CGFloat, lightHC: CGFloat, darkHC: CGFloat) = (1, 1, 1, 1)) {
        self.init(uiColor: .scheme(light: UIColor(hex: light, alpha: alpha.light),
                                   dark: UIColor(hex: dark, alpha: alpha.dark),
                                   lightHC: UIColor(hex: lightHC, alpha: alpha.lightHC),
                                   darkHC: UIColor(hex: darkHC, alpha: alpha.darkHC)))
    }
}

/// Colours. Surfaces, darkest first in dark mode: canvas (sidebar and outer frame), bg (page), surface (cards,
/// grouped lists, inputs), surface2 (hover, the keyboard-cursor row, secondary buttons), surface3 (pressed,
/// the selected filter pill); elevated is for menus, popovers, sheets and toasts, menuActive for their current item.
/// Text: text, text2 (secondary), text3 (metadata, section headers, icons), textPlaceholder (placeholders,
/// disabled, decoration; never text that must be read). primary is the fill (white text on it, same in both
/// modes); primaryText is links, the selected tab, the focus ring and income amounts. selected tints
/// multi-selected rows. borderStrong is only for inputs, checkboxes and switches that are off; border is the hairline.
/// inProgress (= info) is a running task. Media pages (editor, viewer) are dark: mediaBlack, mediaDark, mediaMid and
/// mediaWhite are the chroma-0 canvas steps (viewer black, editor dark grey by default), checkerA / checkerB the
/// transparency checkerboard, onMedia the white controls on viewerScrim, mediaEdge the dark edge under white handles,
/// mediaGuide the white guides (thirds grid, waveform), mediaTrack the video scrubber's track (its played part is
/// onMedia, not the primary: the primary falls short over a bright frame), mediaSelected the outline of a selected picture.
enum Palette {
@@palette@@

    // old names, kept for one version
    @available(*, deprecated, renamed: "hover") static var stateHover: Color { hover }
    @available(*, deprecated, renamed: "pressed") static var statePressed: Color { pressed }
}

enum Radius {
@@radius@@
}

enum Space {
@@space@@
}

/// Sizes: the minimum hit area, control heights (lg is the primary button), list rows and the filter pill
/// (36 tall; pad its hit area to 44 with .contentShape(Capsule()) and vertical padding).
enum Size {
    static let hitMin: CGFloat = @@hit@@
@@controls@@
    static let row: CGFloat = @@row@@
    static let rowSingle: CGFloat = @@row_single@@
    static let pill: CGFloat = 36
    /// media and AI components: the editor's tool tray and slider, crop handles, the video timeline and its waveform, the
    /// thumbnail grid and its selection, checkerboard squares and the viewer scrim's height; the prompt field grows from
    /// promptMin to promptMaxLines lines, then scrolls (its corner radius stays promptMin / 2)
@@media_sizes@@
    static let promptMin: CGFloat = @@prompt_min@@
    static let promptMaxLines = @@prompt_lines@@
}

/// Text styles: the system styles, so Dynamic Type works (check up to AX5); SF Pro tracks itself.
/// Page titles use the navigation bar's large title; sectionHeader goes with Palette.text3, rowMeta with Palette.text2.
/// Paragraphs of long (Chinese) text use the .longText() view modifier: longText plus @@long_spacing@@ pt line spacing, 17/@@long_line@@.
extension Font {
@@fonts@@
}

/// Motion: a near-critically damped spring for things that move, short ease-outs for colour and opacity;
/// exits take two thirds of the entry; zoom is the grid-to-viewer transition and a double-tap zoom. With Reduce Motion on (@Environment(\\.accessibilityReduceMotion)),
/// drop movement and scaling and keep at most a fade. Liquid Glass keeps its own morphing.
enum Motion {
    static let spring = Animation.spring(response: @@spring_response@@, dampingFraction: @@spring_damping@@)
@@motion@@
}

/// Gestures on photos and video. Pinch from fit (1) to zoomMax; a double tap toggles fit and zoomDoubleTap at the
/// tap point. Pans keep their momentum (deceleration per ms, UIScrollView's .normal) and rubber-band at the edges
/// (rubberBand), springing back with Motion.spring. A swipe down closes the viewer past dismissDistance of the height
/// or dismissVelocity pt/s, the background fading with the drag. The grid opens the viewer with a zoom: on iOS 18
/// .navigationTransition(.zoom(sourceID:in:)), earlier matchedGeometryEffect with Motion.spring. Sliders and dials
/// snap to their detent within detentZone of the range: snapped(_:in:) plus Haptic.snap when the value lands on it.
/// (Not named Gesture: that is SwiftUI's protocol.)
enum MediaGesture {
@@gesture@@

    /// The value, pulled to `target` when it is within detentZone of the range from it.
    static func snapped(_ value: Double, in range: ClosedRange<Double>, to target: Double = 0) -> Double {
        abs(value - target) <= (range.upperBound - range.lowerBound) * detentZone ? target : value
    }
}

/// Haptics, one per role: selection (a tool, a segment, a picture picked), snap (a slider or dial reaching its detent,
/// a crop edge meeting a guide), success (an export or save finished), failure (it failed). Play them on the event,
/// never on every frame: sensoryFeedback plays whenever its trigger changes, so a slider gives it a condition,
/// .sensoryFeedback(Haptic.snap.feedback, trigger: value) { old, new in new == 0 && old != 0 } (iOS 17 and later);
/// earlier, call Haptic.snap.play() from the action when the value lands on the detent.
enum Haptic {
    case selection, snap, success, failure

    @available(iOS 17.0, *)
    var feedback: SensoryFeedback {
        switch self {
@@haptic_feedback@@
        }
    }

    @MainActor func play() {
        switch self {
@@haptic_play@@
        }
    }
}

/// Icons: SF Symbols at .regular weight; default colour Palette.text3, clickable accents Palette.primaryText.
enum Icon {
    static let sm: CGFloat = @@icon_sm@@
    static let md: CGFloat = @@icon_md@@
    static let lg: CGFloat = @@icon_lg@@
    static let weight: Font.Weight = .regular
}

/// elev-2 (menus, popovers, toasts, floating bars) and elev-3 (sheets, dialogs, the command menu), as in theme.css:
/// light mode has two soft layers, dark mode one stronger layer. Cards and lists have no shadow, only the hairline.
struct Elevation: ViewModifier {
    var level: Int
    @Environment(\\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        let l = Elevation.layers(level, dark: colorScheme == .dark)
        return content
            .shadow(color: .black.opacity(l[0].opacity), radius: l[0].radius, x: 0, y: l[0].y)
            .shadow(color: .black.opacity(l[1].opacity), radius: l[1].radius, x: 0, y: l[1].y)
    }

    /// [y offset, radius (half the CSS blur), opacity], two layers per level (unused layers are clear)
    static func layers(_ level: Int, dark: Bool) -> [(y: CGFloat, radius: CGFloat, opacity: Double)] {
        switch (level, dark) {
@@shadows@@
        default: return [(0, 0, 0), (0, 0, 0)]
        }
    }
}

/// Card: solid surface and a 1 pt hairline; no shadow.
struct Card: ViewModifier {
    var radius: CGFloat = Radius.lg
    private var shape: RoundedRectangle { RoundedRectangle(cornerRadius: radius, style: .continuous) }

    func body(content: Content) -> some View {
        content
            .background { shape.fill(Palette.surface) }
            .overlay { shape.strokeBorder(Palette.border, lineWidth: 1) }
    }
}

/// Frost: custom floating controls (a floating action button or bar), never content such as lists and cards;
/// toasts, menus and sheets use elevated. System bars, toolbars and TabView already get Liquid Glass on iOS 26:
/// give them no background.
/// - edges: the sides that get the 1 pt hairline below iOS 26. A top bar uses .bottom, a bottom bar .top, floating pieces .all.
/// - radius: defaults to Radius.lg for .all and to 0 otherwise, so a full-width bar stays square.
/// - floating: adds elev-2 below iOS 26 (Liquid Glass draws its own depth).
/// - interactive: Liquid Glass reacts to touch (buttons and other tappable controls).
/// Several glass pieces side by side go in one GlassEffectContainer on iOS 26.
struct Frost: ViewModifier {
    var radius: CGFloat? = nil
    var edges: Edge.Set = .all
    var floating = false
    var interactive = false
    private var shape: RoundedRectangle {
        RoundedRectangle(cornerRadius: radius ?? (edges == .all ? Radius.lg : 0), style: .continuous)
    }

    @ViewBuilder func body(content: Content) -> some View {
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            content.glassEffect(.regular.interactive(interactive), in: shape)
        } else {
            fallback(content)
        }
        #else
        fallback(content)
        #endif
    }

    /// Below iOS 26: the frost colour (@@frost_pct@@ % elevated, @@frost_hc_pct@@ % with Increase Contrast) over the system
    /// blur, a hairline, and a 1 pt highlight along the top edge, as theme.css does.
    private func fallback(_ content: Content) -> some View {
        content
            .background { fill }
            .overlay { hairline }
            .overlay { highlight }
    }

    private var material: some View {
        shape.fill(Palette.frost).background(.ultraThinMaterial, in: shape)
    }

    @ViewBuilder private var fill: some View {
        if floating {
            material.modifier(Elevation(level: 2))
        } else {
            material
        }
    }

    private var highlight: some View {
        shape.strokeBorder(LinearGradient(colors: [Palette.frostHighlight, Palette.frostHighlight.opacity(0)],
                                          startPoint: .top, endPoint: UnitPoint(x: 0.5, y: 0.35)), lineWidth: 1)
    }

    @ViewBuilder private var hairline: some View {
        if edges == .all {
            shape.strokeBorder(Palette.frostBorder, lineWidth: 1)
        } else {
            ZStack {
                if edges.contains(.top) { Palette.frostBorder.frame(height: 1).frame(maxHeight: .infinity, alignment: .top) }
                if edges.contains(.bottom) { Palette.frostBorder.frame(height: 1).frame(maxHeight: .infinity, alignment: .bottom) }
                if edges.contains(.leading) { Palette.frostBorder.frame(width: 1).frame(maxWidth: .infinity, alignment: .leading) }
                if edges.contains(.trailing) { Palette.frostBorder.frame(width: 1).frame(maxWidth: .infinity, alignment: .trailing) }
            }
        }
    }
}

/// The viewer scrim: a fixed dark gradient from the top or bottom edge inward, under the viewer's white controls
/// (Palette.onMedia), in place of glass over the photo. Tapping the picture hides the controls and the scrim together.
/// It holds @@scrim_pct@@ % black under the controls, so white text and icons pass 4.5:1 even over a white photo.
struct ViewerScrim: View {
    var edge: VerticalEdge = .top

    var body: some View {
        LinearGradient(stops: [
@@scrim_stops@@
        ], startPoint: edge == .top ? .top : .bottom, endPoint: edge == .top ? .bottom : .top)
            .frame(height: Size.viewerScrim)
            .allowsHitTesting(false)
    }
}

/// The transparency checkerboard behind a cut-out: checkerA and checkerB squares of Size.checker.
struct Checkerboard: View {
    var square: CGFloat = Size.checker

    var body: some View {
        Canvas { context, size in
            context.fill(Path(CGRect(origin: .zero, size: size)), with: .color(Palette.checkerA))
            var squares = Path()
            for row in 0 ..< Int((size.height / square).rounded(.up)) {
                for column in stride(from: row % 2 == 0 ? 1 : 0, to: Int((size.width / square).rounded(.up)), by: 2) {
                    squares.addRect(CGRect(x: CGFloat(column) * square, y: CGFloat(row) * square, width: square, height: square))
                }
            }
            context.fill(squares, with: .color(Palette.checkerB))
        }
    }
}

/// A selected picture (thumbnail grid, generated results): a Size.selectOutline outline of mediaSelected inside its
/// edge and a check badge in the bottom trailing corner. Never a tint over the picture: it changes how its colours read.
struct MediaSelected: ViewModifier {
    var selected: Bool

    func body(content: Content) -> some View {
        content
            .overlay {
                if selected { Rectangle().strokeBorder(Palette.mediaSelected, lineWidth: Size.selectOutline) }
            }
            .overlay(alignment: .bottomTrailing) {
                if selected {
                    Image(systemName: "checkmark.circle.fill")
                        .symbolRenderingMode(.palette)
                        .foregroundStyle(Palette.onPrimary, Palette.primary)
                        .font(.system(size: Size.selectCheck))
                        .background { Circle().strokeBorder(Palette.onMedia, lineWidth: 1.5) }
                        .padding(6)
                }
            }
    }
}

/// The keyboard layer (kbd hints, shortcuts in menus and tooltips, hover) is optional: it shows on iPad and Mac while a
/// hardware keyboard is connected, and never on iPhone. Put .keyboardLayer() on the root view; it follows the keyboard
/// as it connects and disconnects, and .kbd() reads it.
private struct HardwareKeyboardKey: EnvironmentKey {
    static let defaultValue = false
}

extension EnvironmentValues {
    var hardwareKeyboard: Bool {
        get { self[HardwareKeyboardKey.self] }
        set { self[HardwareKeyboardKey.self] = newValue }
    }
}

struct KeyboardLayer: ViewModifier {
    @State private var connected = false

    func body(content: Content) -> some View {
        content
            .environment(\\.hardwareKeyboard, connected)
            .onAppear { connected = KeyboardLayer.isConnected }
            .onReceive(NotificationCenter.default.publisher(for: .GCKeyboardDidConnect)) { _ in connected = KeyboardLayer.isConnected }
            .onReceive(NotificationCenter.default.publisher(for: .GCKeyboardDidDisconnect)) { _ in connected = KeyboardLayer.isConnected }
    }

    @MainActor static var isConnected: Bool {
        UIDevice.current.userInterfaceIdiom != .phone && GCKeyboard.coalesced != nil
    }
}

/// Keyboard hint, part of the keyboard layer: @@kbd@@ pt high, caption2 medium with tabular digits, text2 on surface2
/// with a hairline. Show ⌘ ⌥ ⇧ ⌃ ↵, keys 4 pt apart, e.g. Text("⌘K").kbd(); without a hardware keyboard it draws nothing.
struct Kbd: ViewModifier {
    @Environment(\\.hardwareKeyboard) private var keyboard
    private var shape: RoundedRectangle { RoundedRectangle(cornerRadius: Radius.xs, style: .continuous) }

    @ViewBuilder func body(content: Content) -> some View {
        if keyboard {
            content
                .font(Font.caption2.weight(.medium).monospacedDigit())
                .foregroundStyle(Palette.text2)
                .padding(.horizontal, 4)
                .frame(minWidth: @@kbd@@, minHeight: @@kbd@@)
                .background { shape.fill(Palette.surface2) }
                .overlay { shape.strokeBorder(Palette.border, lineWidth: 1) }
        }
    }
}

extension View {
    func card(radius: CGFloat = Radius.lg) -> some View { modifier(Card(radius: radius)) }
    func frost(radius: CGFloat? = nil, edges: Edge.Set = .all, floating: Bool = false, interactive: Bool = false) -> some View {
        modifier(Frost(radius: radius, edges: edges, floating: floating, interactive: interactive))
    }
    func kbd() -> some View { modifier(Kbd()) }
    func keyboardLayer() -> some View { modifier(KeyboardLayer()) }
    func mediaSelected(_ selected: Bool) -> some View { modifier(MediaSelected(selected: selected)) }
    /// Long text (notes, descriptions, Chinese paragraphs): the body style with @@long_spacing@@ pt between lines.
    func longText() -> some View { font(.longText).lineSpacing(@@long_spacing@@) }
    /// Put it on a background shape, never on a view with text in it.
    func elev2() -> some View { modifier(Elevation(level: 2)) }
    func elev3() -> some View { modifier(Elevation(level: 3)) }
}
"""


def swift(t):
    T = t["color"]
    palette = []
    for k in ORDER:
        vals = [split(T[s][k]) for s in ("light", "dark", "light-hc", "dark-hc")]
        hexes = ", ".join(f"{lab}: 0x{h}" for lab, (h, _) in zip(("light", "dark", "lightHC", "darkHC"), vals))
        alphas = [a for _, a in vals]
        alpha = "" if all(a == 1 for a in alphas) else f", alpha: ({', '.join(num(a) for a in alphas)})"
        palette.append(f"    static let {camel(k)} = Color({hexes}{alpha})")

    fonts = []
    for k, v in t["font"]["ios"]["styles"].items():
        w = "" if v["weight"] == SWIFT_DEFAULT_WEIGHT.get(v["style"], "regular") else f".weight(.{v['weight']})"
        tab = ".monospacedDigit()" if v.get("tabular") else ""
        fonts.append(f"    /// {v['size']} pt at the default size")
        fonts.append(f"    static let {camel(k)} = Font.{v['style']}{w}{tab}")

    E = t["elevation"]
    shadows = []
    for n in ("2", "3"):
        for dark in (False, True):
            layers = (E["dark" if dark else "light"][n] + [[0, 0, 0, 0, 0]] * 2)[:2]
            cells = ", ".join(f"({num(y)}, {num(b / 2)}, {num(a)})" for _, y, b, _, a in layers)
            shadows.append(f"        case ({n}, {'true' if dark else 'false'}): return [{cells}]")

    M = t["motion"]
    x1, y1, x2, y2 = M["ease"]["enter"]
    e1, f1, e2, f2 = M["ease"]["exit"]
    mot = []
    for k in M["exit"]:
        mot.append(f"    static let {k} = Animation.timingCurve({num(x1)}, {num(y1)}, {num(x2)}, {num(y2)}, "
                   f"duration: {num(M['duration'][k] / 1000)})")
        mot.append(f"    static let {k}Exit = Animation.timingCurve({num(e1)}, {num(f1)}, {num(e2)}, {num(f2)}, "
                   f"duration: {num(M['exit'][k] / 1000)})")

    S = t["size"]
    G = t["gradient"]["viewer-scrim"]
    gesture = [f"    static let {camel(k)}: CGFloat = {num(v)}" for k, v in M["gesture"].items() if k != "detent"]
    gesture.append(f"    static let detentZone: Double = {num(M['gesture']['detent'])}")
    return fill(
        SWIFT,
        title=f"{t['name']} theme: generated by rian-app-theme (graphite), {credit(t)}",
        palette="\n".join(palette),
        radius="\n".join(f"    static let {k}: CGFloat = {v}" for k, v in t["radius"].items() if k != "full"),
        space="\n".join(f"    static let s{k.replace('.', '_')}: CGFloat = {v}" for k, v in t["space"].items()),
        hit=S["hit-min"]["ios"],
        controls="\n".join(f"    static let control{pascal(k)}: CGFloat = {v}" for k, v in S["control-h"]["mobile"].items()),
        row=S["row"]["mobile"], row_single=S["row"]["mobile-single"],
        fonts="\n".join(fonts),
        spring_response=num(M["ios"]["spring"]["response"]), spring_damping=num(M["ios"]["spring"]["dampingFraction"]),
        motion="\n".join(mot),
        icon_sm=t["icon"]["size"]["sm"], icon_md=t["icon"]["size"]["md"], icon_lg=t["icon"]["size"]["lg"],
        shadows="\n".join(shadows),
        frost_pct=round(t["blur"]["opacity"]["standard"] * 100), frost_hc_pct=round(t["blur"]["opacity"]["high"] * 100),
        kbd=S["kbd"],
        media_sizes="\n".join(f"    static let {camel(k)}: CGFloat = {v}" for k, v in S["media"].items()),
        prompt_min=S["prompt"]["min"], prompt_lines=S["prompt"]["max-lines"],
        gesture="\n".join(gesture),
        haptic_feedback="\n".join(f"        case .{k}: return .{v['ios']}" for k, v in t["haptic"].items()),
        haptic_play="\n".join(f"        case .{k}: {UIKIT_HAPTIC[v['ios']]}" for k, v in t["haptic"].items()),
        scrim_pct=round(PALETTE["media"]["alpha"]["viewer-scrim"][1] * 100),
        scrim_stops=",\n".join(f"            .init(color: .black.opacity({num(o)}), location: {num(pos)})" for pos, o in G["stops"]),
        long_spacing=t["font"]["ios"]["styles"]["long-text"]["line-spacing"], long_line=t["font"]["web"]["phone"]["long-text"]["line"],
    )


# ---------- emit: Jetpack Compose ----------
# Material 3 role -> token, or (light token, dark token) where the two modes differ. "@on-primary-text" is
# the ink on primary-text: white in light mode, bg in dark mode
COMPOSE_ROLES = [
    ("primary", "primary-text"), ("onPrimary", "@on-primary-text"), ("primaryContainer", "primary-container"),
    ("onPrimaryContainer", "on-primary-container"), ("inversePrimary", "inverse-primary"),
    ("secondary", "text-2"), ("onSecondary", "bg"),
    ("secondaryContainer", "surface-3"), ("onSecondaryContainer", "text"),
    ("tertiary", "info"), ("onTertiary", "on-info"), ("tertiaryContainer", "info-container"),
    ("onTertiaryContainer", "info"),
    ("background", "bg"), ("onBackground", "text"), ("surface", "bg"), ("onSurface", "text"),
    ("surfaceVariant", "surface-2"), ("onSurfaceVariant", "text-2"), ("surfaceTint", "bg"),
    ("inverseSurface", "inverse-surface"), ("inverseOnSurface", "on-inverse"),
    ("error", "danger"), ("onError", "on-danger"), ("errorContainer", "danger-container"),
    ("onErrorContainer", "danger"),
    ("outline", "border-strong"), ("outlineVariant", "border"), ("scrim", "scrim"),
    ("surfaceBright", ("bg", "surface-3")), ("surfaceDim", ("surface-3", "canvas")),
    ("surfaceContainerLowest", "canvas"), ("surfaceContainerLow", "bg"), ("surfaceContainer", "surface"),
    ("surfaceContainerHigh", "surface-2"), ("surfaceContainerHighest", "surface-3"),
]
# colours read through AppTheme.colors; the filled primary is primaryFill there, since colorScheme.primary is primary-text
EXTENDED = ["canvas", "surface", "surface-2", "surface-3", "elevated", "menu-active", "border", "border-strong",
            "text", "text-2", "text-3", "text-placeholder",
            "primary", "on-primary", "primary-hover", "primary-pressed", "primary-text", "selected", "focus",
            "success", "on-success", "success-container", "warning", "on-warning", "warning-container",
            "info", "on-info", "info-container", "in-progress", "hover", "pressed", "disabled-fg", "disabled-bg",
            "scrim", "scrim-menu", "frost", "frost-border", "frost-highlight",
            "media-black", "media-dark", "media-mid", "media-white", "checker-a", "checker-b",
            "on-media", "viewer-scrim", "media-edge", "media-guide", "media-track", "media-selected"]
KT_NAME = {"primary": "primaryFill", "on-primary": "onPrimaryFill", "primary-hover": "primaryFillHover",
           "primary-pressed": "primaryFillPressed"}

KOTLIN = """// @@title@@
// Android, Compose UI 1.8 or later (Compose BOM 2025.04.01, Material 3 1.3.2; Haptic uses 1.8's feedback types).
// Material 3 1.4 stable (BOM 2025.09.01) is the baseline.
// A fixed brand scheme: no dynamic colour.
package theme

import android.app.UiModeManager
import android.content.res.Configuration
import android.os.Build
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.SpringSpec
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsHoveredAsState
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.abs

/** Material 3 roles, four schemes: light, dark, and the high-contrast pair (system contrast >= 0.5 on API 34+).
 *  primary is primary-text (links, the selected tab, focus, checkbox and switch fills), so TextButton and every
 *  component that draws text in primary passes @@acc@@:1; the filled button uses AppTheme.colors.primaryFill (AppButton).
 *  surface = bg, so TopAppBar, ListItem and Scaffold sit on the page colour; surfaceContainerLowest…Highest are
 *  canvas, bg, surface, surface-2 and surface-3; secondaryContainer is surface-3, so the NavigationBar indicator
 *  and the selected FilterChip are neutral. outline (inputs, checkboxes) = border-strong; outlineVariant (cards,
 *  dividers) = border. Every role up to Material 3 1.3 is set; the 1.4 fixed roles are unused here.
 *  Checkbox and Switch fill with primary (primary-text); the check mark and thumb are onPrimary: white in light mode,
 *  the dark bg colour in dark mode (@@onp_dark@@:1). Keep it: white on the dark primary-text is only @@white_dark@@:1. */
val LightColors = lightColorScheme(
@@light@@
)

val DarkColors = darkColorScheme(
@@dark@@
)

val LightHighContrastColors = lightColorScheme(
@@light_hc@@
)

val DarkHighContrastColors = darkColorScheme(
@@dark_hc@@
)

/** Colours Material 3 has no role for: read them with AppTheme.colors, e.g. AppTheme.colors.success.
 *  primaryFill is the filled primary (white text on it, the same in both modes); primaryText is colorScheme.primary.
 *  surface is the card colour (colorScheme.surface is the page). textPlaceholder is only for placeholders, disabled
 *  text and decoration. Material components replace the scrim's alpha with their own: pass scrimColor = scrim to
 *  ModalBottomSheet and ModalNavigationDrawer for this theme's. inProgress (= info) is a running task.
 *  Media pages (editor, viewer) are dark: AppTheme(dark = true) around them. mediaBlack, mediaDark, mediaMid and
 *  mediaWhite are the chroma-0 canvas steps (viewer black, editor dark grey by default), checkerA / checkerB the
 *  transparency checkerboard, onMedia the white controls on the viewer scrim, mediaEdge the dark edge under white
 *  handles, mediaGuide the white guides (thirds grid, waveform), mediaTrack the video scrubber's track (its played part
 *  is onMedia, not the primary: the primary falls short over a bright frame), mediaSelected the outline of a selected picture. */
@Immutable
data class ExtendedColors(
@@ext_fields@@
)

val LightExtendedColors = ExtendedColors(
@@ext_light@@
)

val DarkExtendedColors = ExtendedColors(
@@ext_dark@@
)

val LightHighContrastExtendedColors = ExtendedColors(
@@ext_light_hc@@
)

val DarkHighContrastExtendedColors = ExtendedColors(
@@ext_dark_hc@@
)

@Deprecated("Renamed to hover; kept for one version", ReplaceWith("hover"))
val ExtendedColors.stateHover: Color get() = hover

@Deprecated("Renamed to pressed; kept for one version", ReplaceWith("pressed"))
val ExtendedColors.statePressed: Color get() = pressed

val LocalExtendedColors = staticCompositionLocalOf { LightExtendedColors }

object AppTheme {
    val colors: ExtendedColors
        @Composable @ReadOnlyComposable get() = LocalExtendedColors.current
}

/** The system contrast setting (Settings > Accessibility > Colour and motion > Contrast), API 34 and later:
 *  0 is standard, 0.5 medium, 1 high; 0.5 and up gives the high-contrast schemes. Follows changes live. */
@Composable
fun isSystemHighContrast(): Boolean {
    if (Build.VERSION.SDK_INT < 34) return false
    if (LocalInspectionMode.current) return false  // Android Studio previews may lack the system service
    val context = LocalContext.current
    val modes = remember(context) { context.getSystemService(UiModeManager::class.java) } ?: return false
    var level by remember(modes) { mutableFloatStateOf(modes.contrast) }
    DisposableEffect(modes) {
        val listener = UiModeManager.ContrastChangeListener { level = it }
        modes.addContrastChangeListener(context.mainExecutor, listener)
        onDispose { modes.removeContrastChangeListener(listener) }
    }
    return level >= 0.5f
}

/** Frost (glass) when a blur library such as Haze is used: blur 24 dp, saturation 1.5, fill AppTheme.colors.frost
 *  (@@frost_pct@@ % elevated; @@frost_hc_pct@@ % in high contrast), a 1 dp frostBorder and a 1 dp frostHighlight along the top.
 *  Compose has no system backdrop blur, so bars are opaque by default (TopAppBar bg, NavigationBar surface). */
object Frost {
    val blur = @@blur@@.dp
    const val SATURATION = @@saturate@@f
}

/** Icons: Material Symbols Rounded, weight 300, fill 0 (the selected tab's icon fill 1); default colour text-3,
 *  clickable accents colorScheme.primary. Use them as vector drawables. */
object IconSize {
    val sm = @@icon_sm@@.dp
    val md = @@icon_md@@.dp
    val lg = @@icon_lg@@.dp
    const val WEIGHT = 300
}

/** Corner radii; tags and avatars are TagShape (CircleShape). */
object Radius {
@@radius@@
}

/** Spacing: a 4 dp grid plus 2, e.g. Modifier.padding(Space.s4). */
object Space {
@@space@@
}

/** Sizes: the minimum touch target, control heights (lg is the primary button), list rows, bars and the FAB. */
object AppSize {
    val hitMin = @@hit@@.dp
@@controls@@
    val row = @@row@@.dp
    val rowSingle = @@hit@@.dp
    val navigationBar = 80.dp
    val fab = 56.dp

    /** Media and AI components: the editor's tool tray and slider, crop handles, the video timeline and its waveform,
     *  the thumbnail grid and its selection, checkerboard squares and the viewer scrim's height; the prompt field grows
     *  from promptMin to PROMPT_MAX_LINES lines, then scrolls (its corner radius stays promptMin / 2). */
@@media_sizes@@
    val promptMin = @@prompt_min@@.dp
    const val PROMPT_MAX_LINES = @@prompt_lines@@
}

/** Motion: tween(Motion.STANDARD_MS, easing = Motion.Enter) to appear, tween(Motion.STANDARD_EXIT_MS, easing = Motion.Exit)
 *  to leave. The springs are MotionScheme.standard()'s: spatial (position, size) damping @@sp_damp@@ / stiffness @@sp_stiff@@;
 *  effects (colour, opacity) damping @@ef_damp@@ / stiffness @@ef_stiff@@. Not the expressive scheme: it bounces.
 *  With Remove animations on, drop movement and scaling and keep at most a fade. */
object Motion {
@@motion@@
    val Enter = CubicBezierEasing(@@enter@@)
    val Exit = CubicBezierEasing(@@exit@@)
    fun <T> spatial(): SpringSpec<T> = spring(dampingRatio = @@sp_damp@@f, stiffness = @@sp_stiff@@f)
    fun <T> effects(): SpringSpec<T> = spring(dampingRatio = @@ef_damp@@f, stiffness = @@ef_stiff@@f)
}

/** Gestures on photos and video. Pinch from fit (1) to ZOOM_MAX; a double tap toggles fit and ZOOM_DOUBLE_TAP at the
 *  tap point. Pans fling with the platform decay (rememberSplineBasedDecay(), as lists do) and spring back from the
 *  edges with Motion.spatial(). A swipe down closes the viewer past DISMISS_DISTANCE of the height or dismissVelocity
 *  per second, the background fading with the drag. The grid opens the viewer with a shared element
 *  (SharedTransitionLayout, Motion.ZOOM_MS). Sliders and dials snap to their detent within DETENT_ZONE of the range:
 *  snapped(value, range) plus Haptic.snap when the value lands on it. */
object MediaGesture {
@@gesture@@

    /** The value, pulled to [target] when it is within DETENT_ZONE of the range from it. */
    fun snapped(value: Float, range: ClosedFloatingPointRange<Float>, target: Float = 0f): Float =
        if (abs(value - target) <= (range.endInclusive - range.start) * DETENT_ZONE) target else value
}

/** Haptics, one per role: selection (a tool, a segment, a picture picked), snap (a slider or dial reaching its detent,
 *  a crop edge meeting a guide), success (an export or save finished), failure (it failed). Play them on the event,
 *  never on every frame: LocalHapticFeedback.current.performHapticFeedback(Haptic.snap). Needs Compose UI 1.8; the
 *  system maps each to HapticFeedbackConstants (@@haptic_android@@). */
object Haptic {
@@haptic@@
}

/** The viewer scrim: a fixed dark gradient from the top or bottom edge inward, under the viewer's white controls
 *  (AppTheme.colors.onMedia), in place of glass over the photo, which would shift its colours. Tapping the picture hides
 *  the controls and the scrim together. It holds @@scrim_pct@@ % black under the controls, so white text and icons pass
 *  4.5:1 even over a white photo, e.g. Box(Modifier.fillMaxWidth().height(ViewerScrim.height).background(ViewerScrim.top)) */
object ViewerScrim {
    val height = AppSize.viewerScrim
    val top = Brush.verticalGradient(
@@scrim_top@@
    )
    val bottom = Brush.verticalGradient(
@@scrim_bottom@@
    )
}

/** The transparency checkerboard behind a cut-out: Modifier.checkerboard(AppTheme.colors). */
fun Modifier.checkerboard(colors: ExtendedColors, square: Dp = AppSize.checker): Modifier = drawBehind {
    val s = square.toPx()
    drawRect(colors.checkerA)
    var row = 0
    while (row * s < size.height) {
        var column = if (row % 2 == 0) 1 else 0
        while (column * s < size.width) {
            drawRect(colors.checkerB, topLeft = Offset(column * s, row * s), size = Size(s, s))
            column += 2
        }
        row++
    }
}

/** A selected picture (thumbnail grid, generated results): an AppSize.selectOutline outline of mediaSelected inside its
 *  edge, drawn over the picture; add the AppSize.selectCheck check badge (primaryFill circle, white check, 1.5 dp
 *  white ring) at the bottom end. Never a tint over the picture: it changes how its colours read. */
fun Modifier.mediaSelected(selected: Boolean, colors: ExtendedColors): Modifier = drawWithContent {
    drawContent()
    if (selected) {
        val w = AppSize.selectOutline.toPx()
        drawRect(colors.mediaSelected, topLeft = Offset(w / 2, w / 2), size = Size(size.width - w, size.height - w), style = Stroke(w))
    }
}

/** The keyboard layer (shortcut hints in menus and tooltips, hover) is optional: show it only while a hardware keyboard
 *  is attached to a tablet or Chromebook (smallest width 600 dp and up), never on phones, as on iOS. Follows the
 *  keyboard as it comes and goes. */
@Composable
fun hasHardwareKeyboard(): Boolean {
    val config = LocalConfiguration.current
    return config.smallestScreenWidthDp >= 600 &&
        config.keyboard == Configuration.KEYBOARD_QWERTY && config.hardKeyboardHidden == Configuration.HARDKEYBOARDHIDDEN_NO
}

/** Material 3 picks corners by size key: text fields extraSmall, chips small, cards medium, sheets extraLarge. */
val AppShapes = Shapes(
@@shapes@@
)

/** Buttons are @@button_r@@ dp (not Material's pill); tags and avatars are full pills. */
val ButtonShape = RoundedCornerShape(@@button_r@@.dp)
val TagShape = CircleShape

@Deprecated("Renamed to TagShape; kept for one version", ReplaceWith("TagShape"))
val ChipShape = TagShape

/** Roboto Flex (OFL): put the variable font in res/font as roboto_flex.ttf and pass
 *  AppTheme(fontFamily = robotoFlex(R.font.roboto_flex)); each weight sets the font's wght axis.
 *  Until then FontFamily.Default (the system Roboto) is used. */
fun robotoFlex(resId: Int): FontFamily = FontFamily(listOf(400, 500, 600, 700).map { Font(resId, FontWeight(it)) })

/** Material 3's own line height style: centred, not trimmed, so single-line text keeps its full line height. */
private val CentredLine = LineHeightStyle(LineHeightStyle.Alignment.Center, LineHeightStyle.Trim.None)

/** The Material 3 type scale in Roboto Flex. List row titles bodyLarge, metadata bodyMedium in text-2,
 *  labels and tags labelMedium; body text never below 12 sp. */
fun appTypography(family: FontFamily = FontFamily.Default) = Typography(
@@type@@
)

val AppTypography = appTypography()

/** Tabular digits, for amounts and counts: Text("−¥32.00", style = MaterialTheme.typography.bodyLarge.tabular) */
val TextStyle.tabular: TextStyle get() = copy(fontFeatureSettings = "tnum")

/** Timecodes and running times (timeline labels, player time, export time left), tabular so they never jitter:
 *  Text("0:12 / 1:04", style = MaterialTheme.typography.timecode) */
val Typography.timecode: TextStyle get() = @@timecode@@.tabular

/** The theme. dark and highContrast follow the system; the colour scheme is always this one (no dynamic colour).
 *  On Material 3 1.5.0-beta01 and later you may use, with the same arguments,
 *  MaterialExpressiveTheme(colorScheme = colors, motionScheme = MotionScheme.standard(), shapes = AppShapes,
 *  typography = typography, content = content), passing the colour scheme explicitly; never MotionScheme.expressive(). */
@Composable
fun AppTheme(
    dark: Boolean = isSystemInDarkTheme(),
    highContrast: Boolean = isSystemHighContrast(),
    fontFamily: FontFamily = FontFamily.Default,
    content: @Composable () -> Unit,
) {
    val colors = when {
        dark && highContrast -> DarkHighContrastColors
        dark -> DarkColors
        highContrast -> LightHighContrastColors
        else -> LightColors
    }
    val extended = when {
        dark && highContrast -> DarkHighContrastExtendedColors
        dark -> DarkExtendedColors
        highContrast -> LightHighContrastExtendedColors
        else -> LightExtendedColors
    }
    val typography = remember(fontFamily) { appTypography(fontFamily) }
    CompositionLocalProvider(LocalExtendedColors provides extended) {
        MaterialTheme(colorScheme = colors, shapes = AppShapes, typography = typography, content = content)
    }
}

/** TopAppBar: opaque bg, and the same when content scrolls under it (no tonal lift); once scrolled, a 1 dp
 *  outlineVariant line under it, which you draw yourself, e.g. in a Column:
 *  TopAppBar(title = { Text("明细") }, colors = appTopBarColors(), scrollBehavior = scrollBehavior)
 *  if (scrollBehavior.state.contentOffset < 0f) HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
 *  with scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior() and Modifier.nestedScroll(scrollBehavior.nestedScrollConnection) on the Scaffold. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun appTopBarColors(): TopAppBarColors = TopAppBarDefaults.topAppBarColors(
    containerColor = MaterialTheme.colorScheme.background,
    scrolledContainerColor = MaterialTheme.colorScheme.background,
)

/** NavigationBar items: the indicator pill is surface-3 (neutral); the selected icon (fill 1) and label are primary-text. */
@Composable
fun appNavigationItemColors(): NavigationBarItemColors = NavigationBarItemDefaults.colors(
    selectedIconColor = MaterialTheme.colorScheme.primary,
    selectedTextColor = MaterialTheme.colorScheme.primary,
    indicatorColor = MaterialTheme.colorScheme.secondaryContainer,
    unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
    unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
)

/** Navigation bar: surface fill, a 1 dp outlineVariant line along the top, no tonal elevation; 80 dp plus the system
 *  gesture inset. Use it instead of NavigationBar, with NavigationBarItem(colors = appNavigationItemColors()) inside. */
@Composable
fun AppNavigationBar(
    modifier: Modifier = Modifier,
    content: @Composable RowScope.() -> Unit,
) = Column(modifier) {
    HorizontalDivider(thickness = 1.dp, color = MaterialTheme.colorScheme.outlineVariant)
    NavigationBar(containerColor = AppTheme.colors.surface, tonalElevation = 0.dp, content = content)
}

/** Primary button: primaryFill, white label, @@button_r@@ dp corners, @@button_h@@ dp tall, no shadow; darker on hover and press
 *  (at once on the way in, fading over Motion.HOVER_OUT_MS on the way out). One per screen. Use it instead of Button. */
@Composable
fun AppButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    interactionSource: MutableInteractionSource? = null,
    content: @Composable RowScope.() -> Unit,
) {
    val source = interactionSource ?: remember { MutableInteractionSource() }
    val pressed by source.collectIsPressedAsState()
    val hovered by source.collectIsHoveredAsState()
    val c = AppTheme.colors
    val fill by animateColorAsState(
        targetValue = when {
            pressed -> c.primaryFillPressed
            hovered -> c.primaryFillHover
            else -> c.primaryFill
        },
        animationSpec = tween(if (pressed || hovered) Motion.HOVER_IN_MS else Motion.HOVER_OUT_MS, easing = Motion.Exit),
        label = "fill",
    )
    Button(
        onClick = onClick,
        modifier = modifier.heightIn(min = AppSize.controlLg),
        enabled = enabled,
        shape = ButtonShape,
        colors = ButtonDefaults.buttonColors(
            containerColor = fill,
            contentColor = c.onPrimaryFill,
            disabledContainerColor = c.disabledBg,
            disabledContentColor = c.disabledFg,
        ),
        elevation = null,
        interactionSource = source,
        content = content,
    )
}

/** Secondary button: surface-2 fill, 1 dp border, text-coloured label, same shape and height as AppButton.
 *  A destructive action is this button with contentColor MaterialTheme.colorScheme.error, never a red fill. */
@Composable
fun AppOutlinedButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    contentColor: Color = MaterialTheme.colorScheme.onSurface,
    interactionSource: MutableInteractionSource? = null,
    content: @Composable RowScope.() -> Unit,
) {
    val source = interactionSource ?: remember { MutableInteractionSource() }
    OutlinedButton(
        onClick = onClick,
        modifier = modifier.heightIn(min = AppSize.controlLg),
        enabled = enabled,
        shape = ButtonShape,
        colors = ButtonDefaults.outlinedButtonColors(
            containerColor = AppTheme.colors.surface2,
            contentColor = contentColor,
            disabledContainerColor = AppTheme.colors.surface2,
            disabledContentColor = AppTheme.colors.disabledFg,
        ),
        border = BorderStroke(1.dp, if (enabled) MaterialTheme.colorScheme.outlineVariant else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f)),
        interactionSource = source,
        content = content,
    )
}

/** Card: surface fill (AppTheme.colors.surface), a 1 dp outlineVariant border, no shadow, Shapes.large corners.
 *  Use it instead of Card (Material's Card is surfaceContainerHighest, i.e. surface-3, with no border) and of a bare
 *  OutlinedCard (colorScheme.surface, the page colour). */
@Composable
fun AppCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) = OutlinedCard(
    modifier = modifier,
    shape = MaterialTheme.shapes.large,
    colors = CardDefaults.outlinedCardColors(containerColor = AppTheme.colors.surface),
    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    content = content,
)

/** Slider: the filled part and the thumb are primaryFill (the slider is one of the primary's uses), the track is
 *  surface-3 (neutral). Compose keeps Material's handle in the fill colour, where iOS and the web draw a white round
 *  thumb (rules.md). A slider with a zero (exposure, warmth) snaps to it: onValueChange = { v ->
 *  val s = MediaGesture.snapped(v, range); if (s == 0f && value != 0f) haptics.performHapticFeedback(Haptic.snap); value = s } */
@Composable
fun appSliderColors(): SliderColors = SliderDefaults.colors(
    thumbColor = AppTheme.colors.primaryFill,
    activeTrackColor = AppTheme.colors.primaryFill,
    inactiveTrackColor = AppTheme.colors.surface3,
    activeTickColor = AppTheme.colors.onPrimaryFill,
    inactiveTickColor = AppTheme.colors.text3,
)

/** Filter chip: Material's FilterChip, 32 dp tall (48 dp touch target), Shapes.small corners, labelLarge.
 *  Unselected: no fill, 1 dp border, text-2 label. Selected: surface-3 fill (neutral, never the primary), text
 *  label, no border, and the 18 dp check from selectedIcon (shown only while selected). Use it instead of FilterChip, e.g.
 *  AppChip(selected, onClick, "全部", selectedIcon = { Icon(painterResource(R.drawable.check_rounded), null, Modifier.size(18.dp)) }) */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppChip(
    selected: Boolean,
    onClick: () -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    selectedIcon: (@Composable () -> Unit)? = null,
) = FilterChip(
    selected = selected,
    onClick = onClick,
    label = { Text(label, style = MaterialTheme.typography.labelLarge, maxLines = 1) },
    modifier = modifier,
    enabled = enabled,
    leadingIcon = if (selected) selectedIcon else null,
    shape = MaterialTheme.shapes.small,
    colors = FilterChipDefaults.filterChipColors(
        containerColor = Color.Transparent,
        labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
        iconColor = MaterialTheme.colorScheme.onSurfaceVariant,
        selectedContainerColor = MaterialTheme.colorScheme.secondaryContainer,
        selectedLabelColor = MaterialTheme.colorScheme.onSurface,
        selectedLeadingIconColor = MaterialTheme.colorScheme.onSurface,
    ),
    border = FilterChipDefaults.filterChipBorder(
        enabled = enabled,
        selected = selected,
        borderColor = MaterialTheme.colorScheme.outlineVariant,
    ),
)

/** Status tag: the status colour on its own container, full pill, 24 dp tall, labelMedium, with a leading status
 *  icon (✓ / ! / i at IconSize.sm, tinted with the status colour). Always pass the icon when the status shares the
 *  primary's accent (info on a blue theme, success on a green one): without it the tag reads as a link.
 *  Danger is Material's error role: MaterialTheme.colorScheme.error / errorContainer.
 *  Use the Material Symbols Rounded check / warning / error / info glyphs at fill 0 (as vector drawables), e.g.
 *  StatusTag("已入账", AppTheme.colors.success, AppTheme.colors.successContainer,
 *      icon = { Icon(painterResource(R.drawable.check_rounded), contentDescription = null) }) */
@Composable
fun StatusTag(
    text: String,
    color: Color,
    container: Color,
    modifier: Modifier = Modifier,
    icon: (@Composable () -> Unit)? = null,
) = Surface(modifier = modifier, shape = TagShape, color = container, contentColor = color) {
    Row(
        modifier = Modifier.padding(start = if (icon != null) 6.dp else 8.dp, end = 8.dp, top = 4.dp, bottom = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (icon != null) Box(Modifier.size(IconSize.sm), contentAlignment = Alignment.Center) { icon() }
        Text(text, style = MaterialTheme.typography.labelMedium, maxLines = 1)
    }
}

/** New-item FAB: 56 dp, primaryFill with a white "+", @@fab_r@@ dp corners, Material's default (elev-2 like) shadow. */
@Composable
fun AppFab(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) = FloatingActionButton(
    onClick = onClick,
    modifier = modifier,
    shape = RoundedCornerShape(@@fab_r@@.dp),
    containerColor = AppTheme.colors.primaryFill,
    contentColor = AppTheme.colors.onPrimaryFill,
    content = content,
)
"""


def kt_colour(colour):
    h, a = split(colour)
    return "Color(0x%02X%s)" % (round(a * 255), h)


def kt_sp(x):
    return f"({num(x)}).sp" if x < 0 else f"{num(x)}.sp"


def kotlin(t):
    T = t["color"]

    def scheme_rows(k):
        M, dark = T[k], k.startswith("dark")
        rows = []
        for role, tok in COMPOSE_ROLES:
            if tok == "@on-primary-text":
                colour = ink_on(M["primary-text"], M)
            else:
                colour = M[tok[1] if dark else tok[0]] if isinstance(tok, tuple) else M[tok]
            rows.append(f"    {role} = {kt_colour(colour)},")
        return "\n".join(rows)

    def ext_rows(k):
        return "\n".join(f"    {KT_NAME.get(n, camel(n))} = {kt_colour(T[k][n])}," for n in EXTENDED)

    type_rows = [f"    {slot} = TextStyle(fontFamily = family, fontSize = {s}.sp, lineHeight = {lh}.sp, "
                 f"fontWeight = FontWeight.W{w}, letterSpacing = {kt_sp(tr)}, lineHeightStyle = CentredLine),"
                 for slot, (s, lh, w, tr) in ANDROID_TYPE.items()]

    M = t["motion"]
    mot = [f"    const val {k.upper().replace('-', '_')}_MS = {v}" for k, v in M["duration"].items()]
    mot += [f"    const val {k.upper()}_EXIT_MS = {v}" for k, v in M["exit"].items()]
    sp, ef = M["android"]["spatial"], M["android"]["effects"]

    r, S = t["radius"], t["size"]
    g, G = M["gesture"], t["gradient"]["viewer-scrim"]
    gesture = [f"    const val ZOOM_DOUBLE_TAP = {num(g['zoom-double-tap'])}f", f"    const val ZOOM_MAX = {num(g['zoom-max'])}f",
               f"    const val DISMISS_DISTANCE = {num(g['dismiss-distance'])}f", f"    val dismissVelocity = {num(g['dismiss-velocity'])}.dp",
               f"    const val DETENT_ZONE = {num(g['detent'])}f"]
    scrim = lambda stops: "\n".join(f"        {num(pos)}f to {kt_colour(rgba(G['color'], o))}," for pos, o in stops)
    shapes = {"extraSmall": r["xs"], "small": r["sm"], "medium": r["md"], "large": r["lg"], "extraLarge": r["xl"]}
    dk = T["dark"]
    return fill(
        KOTLIN,
        title=f"{t['name']} theme: generated by rian-app-theme (graphite), {credit(t)}",
        acc=num(NEED["standard"]["accent"][0]),
        onp_dark=f"{contrast(ink_on(dk['primary-text'], dk), dk['primary-text']):.1f}",
        white_dark=f"{contrast(W, dk['primary-text']):.1f}",
        light=scheme_rows("light"), dark=scheme_rows("dark"),
        light_hc=scheme_rows("light-hc"), dark_hc=scheme_rows("dark-hc"),
        ext_fields="\n".join(f"    val {KT_NAME.get(n, camel(n))}: Color," for n in EXTENDED),
        ext_light=ext_rows("light"), ext_dark=ext_rows("dark"),
        ext_light_hc=ext_rows("light-hc"), ext_dark_hc=ext_rows("dark-hc"),
        frost_pct=round(t["blur"]["opacity"]["standard"] * 100), frost_hc_pct=round(t["blur"]["opacity"]["high"] * 100),
        blur=t["blur"]["frost"], saturate=num(t["blur"]["saturate"]),
        icon_sm=t["icon"]["size"]["sm"], icon_md=t["icon"]["size"]["md"], icon_lg=t["icon"]["size"]["lg"],
        radius="\n".join(f"    val {k} = {v}.dp" for k, v in r.items() if k != "full"),
        space="\n".join(f"    val s{k.replace('.', '_')} = {v}.dp" for k, v in t["space"].items()),
        hit=S["hit-min"]["android"],
        controls="\n".join(f"    val control{pascal(k)} = {v}.dp" for k, v in S["control-h"]["mobile"].items()),
        row=S["row"]["android"],
        motion="\n".join(mot),
        enter=", ".join(num(x) + "f" for x in M["ease"]["enter"]), exit=", ".join(num(x) + "f" for x in M["ease"]["exit"]),
        sp_damp=num(sp["dampingRatio"]), sp_stiff=num(sp["stiffness"]),
        ef_damp=num(ef["dampingRatio"]), ef_stiff=num(ef["stiffness"]),
        shapes=",\n".join(f"    {k} = RoundedCornerShape({v}.dp)" for k, v in shapes.items()),
        button_r=r["lg"], button_h=S["control-h"]["mobile"]["lg"], fab_r=r["xl"],
        type="\n".join(type_rows),
        media_sizes="\n".join(f"    val {camel(k)} = {v}.dp" for k, v in S["media"].items()),
        prompt_min=S["prompt"]["min"], prompt_lines=S["prompt"]["max-lines"],
        gesture="\n".join(gesture),
        haptic="\n".join(f"    val {k} = HapticFeedbackType.{v['compose']}" for k, v in t["haptic"].items()),
        haptic_android=", ".join(f"{k} {v['android']}" for k, v in t["haptic"].items()),
        scrim_pct=round(PALETTE["media"]["alpha"]["viewer-scrim"][1] * 100),
        scrim_top=scrim(G["stops"]),
        scrim_bottom=scrim([(round(1 - pos, 4), o) for pos, o in reversed(G["stops"])]),
        timecode=ANDROID_TIMECODE,
    )


# ---------- emit: Tailwind ----------
def tailwind(t):
    solid = set(opaque_keys(t))
    colors = ",\n".join(
        [f"        '{k}': " + (f"'rgb(var(--c-{k}-rgb) / <alpha-value>)'" if k in solid else f"'var(--c-{k})'") for k in ORDER]
        + ["        // old names, kept for one version\n        'state-hover': 'var(--c-hover)'",
           "        'state-pressed': 'var(--c-pressed)'"])
    radius = ",\n".join(f"        '{k}': 'var(--r-{k})'" for k in t["radius"])
    sizes = ",\n".join(
        f"        '{k}': ['{v['size']}px', {{ lineHeight: '{v['line']}px', letterSpacing: '{v['tracking']:g}em', "
        f"fontWeight: '{v['weight']}' }}]" for k, v in t["font"]["web"]["scale"].items())
    S = t["size"]
    heights = [f"'control-{k}': 'var(--control-h-{k})'" for k in S["control-h"]["desktop"]]
    heights += [f"'control-mobile-{k}': 'var(--control-h-mobile-{k})'" for k in S["control-h"]["mobile"]]
    heights += ["row: 'var(--row-h)'", "'row-compact': 'var(--row-h-compact)'", "'row-mobile': 'var(--row-h-mobile)'",
                "'view-header': 'var(--view-header-h)'", "kbd: 'var(--kbd-h)'"]
    key = lambda k: k if k.isidentifier() else f"'{k}'"
    heights += [f"{key(k)}: 'var(--{MEDIA_CSS.get(k, k)})'" for k in ("tool-tray", "slider-track", "timeline", "waveform", "viewer-scrim")]
    widths = ["sidebar: 'var(--sidebar-w)'"] + [f"{key(k)}: 'var(--{MEDIA_CSS.get(k, k)})'" for k in ("tool-item", "playhead", "trim-handle")]
    M, tc = t["motion"], t["font"]["web"]["phone"]["timecode"]
    durations = [f"'{k}': 'var(--m-{k})'" for k in M["duration"]] + [f"'{k}-exit': 'var(--m-{k}-exit)'" for k in M["exit"]]
    return f"""// {t['name']} theme: Tailwind (v3.3+) preset, graphite style. Load theme.css first: colours, radii, shadows,
// heights and durations read its CSS variables (and it defines .frost, .kbd and .hoverable). Opaque colours take
// opacity modifiers, e.g. bg-primary/10. fontSize holds the desktop scale (text-body, text-small, text-caption …);
// the .td-* classes in theme.css add Inter's opsz and the cv01 / ss03 features, so prefer them for display text.
// focus-visible:ring is the focus ring: 2 px of focus, 2 px away, the gap in bg (ring-offset-surface etc. elsewhere).
// Media: bg-checker (the checkerboard, image and square size), bg-viewer-scrim-top / -bottom with h-viewer-scrim, and a
// selected picture is outline outline-select outline-offset-select outline-media-selected: an outline inside its edge,
// drawn over the picture (a ring is an inset shadow, which an <img> covers), never a tint; theme.css's .media-selected
// is the same. text-timecode is the phone timecode size: add tabular-nums. The kbd hints and hover are an optional
// layer: theme.css hides .kbd on touch screens, and future.hoverOnlyWhenSupported keeps hover: off touch screens (a
// future block in your own config replaces this one: add the flag there).
module.exports = {{
  future: {{ hoverOnlyWhenSupported: true }},
  theme: {{
    extend: {{
      colors: {{
{colors}
      }},
      borderColor: {{ DEFAULT: 'var(--c-border)' }},
      ringColor: {{ DEFAULT: 'var(--c-focus)' }},
      ringWidth: {{ DEFAULT: '2px' }},
      outlineWidth: {{ select: 'var(--select-outline)' }},
      outlineOffset: {{ select: 'calc(-1 * var(--select-outline))' }},
      ringOffsetWidth: {{ DEFAULT: '2px' }},
      ringOffsetColor: {{ DEFAULT: 'var(--c-bg)' }},
      borderRadius: {{
{radius}
      }},
      fontSize: {{
{sizes},
        'timecode': ['{tc['size']}px', {{ lineHeight: '{tc['line']}px', letterSpacing: '{tc['tracking']:g}em', fontWeight: '{tc['weight']}' }}]
      }},
      boxShadow: {{ e2: 'var(--elev-2)', e3: 'var(--elev-3)', e1: 'var(--elev-1)' /* old name: none, cards have no shadow */ }},
      fontFamily: {{ sans: ['var(--font)'], mono: ['var(--font-mono)'] }},
      transitionDuration: {{ {', '.join(durations)} }},
      transitionTimingFunction: {{ enter: 'var(--ease-enter)', exit: 'var(--ease-exit)' }},
      height: {{ {', '.join(heights)} }},
      minHeight: {{ hit: 'var(--hit-min)', prompt: 'var(--prompt-min-h)' }},
      minWidth: {{ hit: 'var(--hit-min)', kbd: 'var(--kbd-h)' }},
      width: {{ {', '.join(widths)} }},
      gap: {{ thumb: 'var(--thumb-gap)' }},
      backgroundImage: {{ checker: 'var(--checker-image)', 'viewer-scrim-top': 'var(--viewer-scrim-top)', 'viewer-scrim-bottom': 'var(--viewer-scrim-bottom)' }},
      backgroundSize: {{ checker: 'calc(2 * var(--checker-size)) calc(2 * var(--checker-size))' }},
    }},
  }},
}};
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--accent",
                    help="the app icon's accent, by name: 蓝 blue (default), 绿 green, 紫 violet; "
                         "灰 gray, 珊瑚 coral and 黄 yellow give a 蓝 UI primary. One of the two tones in "
                         "assets/palette.json (e.g. #3B7BEA) also works; any other colour value is refused")
    ap.add_argument("--category",
                    help="the app's category when there is no icon yet: 工具 tools, 图片 image, 视频 video (蓝), "
                         "AI (紫), 健康 health, 财务 finance (绿). With --accent too, the icon accent wins")
    ap.add_argument("-o", "--out", default="theme-out")
    a = ap.parse_args()
    t = derive(a.name, a.accent, a.category)
    fails, near = audit(t)
    if fails:
        print("\nFAIL: contrast check failed, nothing written:\n  " + "\n  ".join(fails))
        print(near_summary(near))
        sys.exit(1)
    os.makedirs(a.out, exist_ok=True)
    files = {"tokens.json": json.dumps(t, ensure_ascii=False, indent=2), "theme.css": css(t),
             "Theme.swift": swift(t), "Theme.kt": kotlin(t), "tailwind.preset.js": tailwind(t)}
    for f, body in files.items():
        open(os.path.join(a.out, f), "w", encoding="utf-8").write(body)
    print()
    for k, C in t["color"].items():
        print(f"{k:9} primary {C['primary']}  primary-text {C['primary-text']}  text {C['text']}  "
              f"text-2 {C['text-2']}  text-3 {C['text-3']}  placeholder {C['text-placeholder']}")
    print("wrote", ", ".join(files), "to", a.out)
    print(near_summary(near))
    print("contrast: all pass (standard, high)")


if __name__ == "__main__":
    main()
