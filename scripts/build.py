#!/usr/bin/env python3
"""Build an app UI theme in the minimal line style, using the same accent colour as the app icon.

    python3 scripts/build.py --name Tide -o out/                 # default accent: 蓝 (blue)
    python3 scripts/build.py --name Tide --accent 紫 -o out/     # or --accent violet

Writes tokens.json, theme.css, Theme.swift, Theme.kt and tailwind.preset.js to the output folder.
Accent names come from assets/palette.json (Chinese or English names both work). The UI primary
follows the icon accent: 蓝→蓝, 绿→绿, 紫→紫. 珊瑚 coral, 黄 yellow and 灰 gray stay in the app icon
and the UI primary falls back to 蓝 (the script prints a note).

Every foreground colour is tuned against every surface it can sit on (bg, surface, surface-2,
surface-3, and the frost material over the page and over mid-grey content), then the script prints
the full contrast matrix. If any pair falls short it exits with status 1 and writes nothing.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = json.load(open(os.path.join(HERE, "..", "assets", "palette.json"), encoding="utf-8"))
DEFAULT_ACCENT = "蓝"
FROST_ALPHA = 0.88      # frost opacity, both modes
MID_GREY = "#808080"    # stands in for blurred content scrolling under a bar
TEXT, LARGE = 4.5, 3.0  # WCAG: body text; placeholders, control borders, large text and icons
CONTAINER = {"light": 0.90, "dark": 0.85}  # how far a -container is mixed toward the surface
DARK_SHADOW = 2.6       # dark mode multiplies shadow alpha by this

ORDER = ["bg", "surface", "surface-2", "surface-3", "border", "border-strong",
         "text", "text-2", "text-placeholder",
         "primary", "on-primary", "primary-container", "on-primary-container",
         "success", "success-container", "on-success", "warning", "warning-container", "on-warning",
         "danger", "danger-container", "on-danger", "info", "info-container", "on-info",
         "disabled-fg", "disabled-bg", "state-hover", "state-pressed", "focus", "scrim", "selection",
         "inverse-surface", "on-inverse", "frost", "frost-border", "shadow"]


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


def lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rgba(h, a):
    r, g, b = rgb(h)
    return f"rgba({r}, {g}, {b}, {a})"


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


def reach(start, toward, backs, target, ink):
    """walk from start toward `toward` (then on to ink) until the colour reaches `target` against
    every background in `backs`, a list or a function of the candidate (for its own container)"""
    for a, b in ((start, toward), (toward, ink)):
        for i in range(101):
            c = mix(a, b, i / 100)
            bs = backs(c) if callable(backs) else backs
            if min(contrast(c, x) for x in bs) >= target:
                return c
    return ink


def on(c):
    """text on a filled colour: white when it passes (the Apple look), else a deep shade of the
    colour itself (the Material dark look), else plain near-black"""
    return next(x for x in ("#FFFFFF", mix(c, "#000000", 0.82), "#111113") if contrast(x, c) >= TEXT or x == "#111113")


def backgrounds(C):
    """every opaque background a foreground can sit on; frost is composited over the page and over
    mid-grey content (saturate() leaves greys unchanged, and blur only evens content out)"""
    B = {k: C[k] for k in ("bg", "surface", "surface-2", "surface-3")}
    B["frost/bg"] = over(C["frost"], C["bg"])
    B["frost/mid"] = over(C["frost"], MID_GREY)
    return B


def find(name):
    for k, v in PALETTE["accent"].items():
        if name in (k, v["en"]):
            return k, v
    sys.exit(f"unknown accent {name!r}; choose from: " +
             ", ".join(f"{k} ({v['en']})" for k, v in PALETTE["accent"].items()))


# ---------- derive ----------
def derive(name, accent):
    ak, a = find(accent)
    source = {"accent": ak, "en": a["en"]}
    ui = a.get("ui_primary", ak)
    if ui != ak:
        why = ("a warm accent" if a.get("warm") else
               "too close to the grey text (selected and unselected would look the same)")
        print(f"note: {ak} ({a['en']}) is {why} and never the UI primary; "
              f"using {ui} instead (keep {ak} in the app icon)")
        source["icon-accent"] = ak
        ak, a = find(ui)
        source.update(accent=ak, en=a["en"])

    colors = {}
    for mode in ("light", "dark"):
        N = dict(PALETTE["neutral"][mode])
        dark = mode == "dark"
        ink = "#FFFFFF" if dark else "#000000"
        k = CONTAINER[mode]
        N["frost"] = rgba(N["frost"], FROST_ALPHA)
        B = list(backgrounds(N).values())
        C = dict(N)

        def tone(tones, extra):
            """an accent's text-safe colour: light mode darkens the main tone, dark mode lifts it toward
            the light tone, until it passes on every background and on `extra` (its container)"""
            lt, mn = tones
            toward = lt if dark else mix(mn, "#000000", 0.5)
            return reach(mn, toward, lambda c: B + extra(c), TEXT, ink)

        p = tone(a["tones"], lambda c: [mix(c, N["surface"], k)])
        C["primary"] = p
        C["on-primary"] = on(p)
        C["primary-container"] = mix(p, N["surface"], k)
        C["on-primary-container"] = reach(p, ink, [C["primary-container"]], TEXT, ink)
        # secondary text also sits on selected rows (primary-container)
        C["text-2"] = reach(N["text-2"], ink, B + [C["primary-container"]], TEXT, ink)
        C["text-placeholder"] = reach(N["text-placeholder"], ink, B, LARGE, ink)
        # control borders (inputs, checkboxes, switches that are off) sit on the page and its surfaces
        C["border-strong"] = reach(N["border-strong"], ink, B[:3], LARGE, ink)

        # status colours are text on their own container (chips, banners) and on every surface;
        # a status from the primary's own accent reuses the primary instead of a near-twin
        for s, src in PALETTE["status"].items():
            if src == ak:
                C[s], C[s + "-container"], C["on-" + s] = p, C["primary-container"], C["on-primary"]
                continue
            tones = PALETTE["accent"][src]["tones"]
            box = mix(tones[1], N["surface"], k)
            C[s] = tone(tones, lambda c, box=box: [box])
            C[s + "-container"] = box
            C["on-" + s] = on(C[s])

        C["disabled-fg"] = rgba(N["text"], 0.30)
        C["disabled-bg"] = rgba(N["text"], 0.06)
        # state layers go over the content: rows, list items, plain and outlined buttons
        C["state-hover"] = rgba(N["text"], 0.06)
        C["state-pressed"] = rgba(N["text"], 0.10)
        C["focus"] = p
        C["selection"] = mix(p, N["surface"], 0.65 if dark else 0.75)
        colors[mode] = {key: C[key] for key in ORDER}

    return {
        "name": name,
        "source": source,
        "color": colors,
        "radius": {"xs": 4, "sm": 6, "md": 8, "lg": 12, "xl": 16, "full": 9999},
        "space": {"1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48},
        "size": {"hit-min": {"ios": 44, "android": 48}, "control-h": {"sm": 32, "md": 44, "lg": 50}},
        "font": {
            "family": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', Roboto, 'Noto Sans SC', 'Helvetica Neue', sans-serif",
            "mono": "'SF Mono', ui-monospace, 'JetBrains Mono', Menlo, monospace",
            # [size, line height, weight, tracking in pt]
            "scale": {
                "large-title": [34, 41, 700, 0.37], "title-1": [28, 34, 700, 0.36], "title-2": [22, 28, 600, 0.35],
                "title-3": [20, 25, 600, 0.38], "headline": [17, 22, 600, -0.41], "body": [17, 22, 400, -0.41],
                "body-long": [17, 28, 400, -0.41],
                "callout": [16, 21, 400, -0.32], "subhead": [15, 20, 400, -0.24], "footnote": [13, 18, 400, -0.08],
                "caption": [12, 16, 500, 0.0],
            },
        },
        # layers: [x, y, blur, spread, alpha]; dark mode multiplies alpha by 2.6.
        # elev-1 is one soft drop: the card's own 1 px border is its edge
        "elevation": {
            "1": [[0, 1, 2, 0, 0.06]],
            "2": [[0, 2, 6, 0, 0.06], [0, 8, 24, 0, 0.10]],
            "3": [[0, 4, 12, 0, 0.08], [0, 20, 48, 0, 0.16]],
        },
        "icon": {"size": {"sm": 16, "md": 20, "lg": 24, "xl": 28}, "stroke": 1.75,
                 "ios": "SF Symbols, weight .regular, scale .medium",
                 "android": "Material Symbols Rounded, weight 400, fill 0, grade 0, optical size 24",
                 "web": "Lucide at stroke-width 1.75, or Phosphor Regular"},
        "blur": {"frost": 20, "saturate": 1.8},
        "motion": {"fast": "160ms cubic-bezier(.2, 0, 0, 1)", "standard": "240ms cubic-bezier(.2, 0, 0, 1)",
                   "spring": "420ms cubic-bezier(.34, 1.36, .64, 1)"},
    }


# ---------- contrast audit ----------
STATUS = list(PALETTE["status"])
COLUMNS = ["bg", "surface", "surface-2", "surface-3", "frost/bg", "frost/mid"]
# foreground, threshold, the backgrounds it is checked on
ROWS = ([("text", TEXT, COLUMNS), ("text-2", TEXT, COLUMNS), ("text-placeholder", LARGE, COLUMNS),
         ("border-strong", LARGE, COLUMNS[:3]), ("primary", TEXT, COLUMNS)] +
        [(s, TEXT, COLUMNS) for s in STATUS])


def audit(t):
    """print the foreground x background contrast matrix for both modes; return the failures"""
    fails, out = [], []
    for mode in ("light", "dark"):
        C, other = t["color"][mode], t["color"]["dark" if mode == "light" else "light"]
        B = backgrounds(C)
        out.append(f"\n{mode}: frost {C['frost']} -> over bg {B['frost/bg']}, over {MID_GREY} {B['frost/mid']}")
        out.append(f"  {'':17}" + "".join(f"{c:>10}" for c in COLUMNS) + "    need")
        for fg, need, cols in ROWS:
            cells = []
            for col in COLUMNS:
                if col not in cols:
                    cells.append(f"{'.':>10}")
                    continue
                r = contrast(C[fg], B[col])
                bad = r < need
                cells.append(f"{r:>9.2f}{'!' if bad else ' '}")
                if bad:
                    fails.append(f"{mode}: {fg} on {col} {r:.2f} < {need}")
            out.append(f"  {fg:17}" + "".join(cells) + f"    {need}")
        pairs = [("on-primary", "primary"), ("on-primary-container", "primary-container"),
                 ("primary", "primary-container"), ("text", "primary-container"), ("text-2", "primary-container"),
                 ("text", "selection")]
        pairs += [p for s in STATUS for p in ((s, s + "-container"), ("on-" + s, s))]
        pairs += [("on-inverse", "inverse-surface")]
        checks = [(f"{f} / {b}", C[f], C[b]) for f, b in pairs]
        checks.append(("inverse-primary / inverse-surface", other["primary"], C["inverse-surface"]))
        out.append("  pairs (need 4.5):")
        row = []
        for label, f, b in checks:
            r = contrast(f, b)
            bad = r < TEXT
            row.append(f"{label} {r:.2f}{'!' if bad else ''}")
            if bad:
                fails.append(f"{mode}: {label} {r:.2f} < {TEXT}")
        for i in range(0, len(row), 3):
            out.append("    " + "   ".join(row[i:i + 3]))
    print("contrast (need: 4.5 text; 3.0 text-placeholder and border-strong; '.' = not used there)" + "\n".join(out))
    return fails


def credit(t):
    s = t["source"]
    note = f"; app icon keeps {s['icon-accent']}" if "icon-accent" in s else ""
    return f"accent {s['accent']} ({s['en']}){note}"


def camel(k):
    p = k.split("-")
    return p[0] + "".join(x.title() for x in p[1:])


def pascal(k):
    return "".join(x.title() for x in k.split("-"))


def motion(v):
    """'160ms cubic-bezier(.2, 0, 0, 1)' -> (160, [0.2, 0.0, 0.0, 1.0])"""
    ms = int(re.match(r"\s*(\d+)ms", v).group(1))
    curve = [float(x) for x in re.search(r"cubic-bezier\(([^)]*)\)", v).group(1).split(",")]
    return ms, curve


def num(x):
    return f"{x:g}"


def fill(template, **subs):
    for k, v in subs.items():
        template = template.replace(f"@@{k}@@", str(v))
    return template


# ---------- emit: CSS ----------
def shadow_css(layers, colour, k=1.0):
    return ", ".join(f"{x}px {y}px {b}px{f' {s}px' if s else ''} {rgba(colour, round(min(a * k, 1), 3))}"
                     for x, y, b, s, a in layers)


def css(t):
    out = [f"/* {t['name']} theme: generated by rian-app-theme, {credit(t)} */"]

    def block(sel, mode):
        C = t["color"][mode]
        lines = [f"  --c-{k}: {v};" for k, v in C.items() if k != "shadow"]
        lines += [f"  --c-{k}-rgb: {' '.join(str(v) for v in rgb(c))};"
                  for k, c in C.items() if k != "shadow" and c.startswith("#")]
        k = 1.0 if mode == "light" else DARK_SHADOW
        lines += [f"  --elev-{n}: {shadow_css(L, C['shadow'], k)};" for n, L in t["elevation"].items()]
        lines.append(f"  color-scheme: {mode};")
        return f"{sel} {{\n" + "\n".join(lines) + "\n}"

    size = t["size"]
    common = [f"  --r-{k}: {v}px;" for k, v in t["radius"].items()]
    common += [f"  --s-{k}: {v}px;" for k, v in t["space"].items()]
    common.append(f"  --hit-min: {size['hit-min']['ios']}px; /* 48 on Android */")
    common += [f"  --control-h-{k}: {v}px;" for k, v in size["control-h"].items()]
    common += [f"  --font: {t['font']['family']};", f"  --font-mono: {t['font']['mono']};"]
    for k, (sz, lh, w, tr) in t["font"]["scale"].items():
        common.append(f"  --t-{k}: {w} {sz}px/{lh}px var(--font);")
        common.append(f"  --tr-{k}: {tr / sz:.4f}em;")
    common += [f"  --m-{k}: {v};" for k, v in t["motion"].items()]
    common += [f"  --icon-{k}: {v}px;" for k, v in t["icon"]["size"].items()]
    common.append(f"  --icon-stroke: {t['icon']['stroke']};")
    out.append(":root {\n" + "\n".join(common) + "\n}")
    out.append(block(":root, [data-theme=\"light\"]", "light"))
    out.append("@media (prefers-color-scheme: dark) {\n" + block(":root:not([data-theme=\"light\"])", "dark").replace("\n", "\n  ") + "\n}")
    out.append(block("[data-theme=\"dark\"]", "dark"))
    out.append("""/* keyboard focus: a 2 px ring in the focus colour, 2 px away from the control */
:focus-visible { outline: 2px solid var(--c-focus); outline-offset: 2px; }
::selection { background: var(--c-selection); }""")
    out.append(f"""/* frost material: bars, sheets, popovers and floating controls (never cards).
   Floating pieces add box-shadow: var(--elev-2); a full-width bar keeps only the hairline
   on its content side, e.g. border-width: 0 0 1px. */
.frost {{
  background: var(--c-frost);
  -webkit-backdrop-filter: blur({t['blur']['frost']}px) saturate({t['blur']['saturate']});
  backdrop-filter: blur({t['blur']['frost']}px) saturate({t['blur']['saturate']});
  border: 1px solid var(--c-frost-border);
}}""")
    names = [f".t-{k}" for k in t["font"]["scale"]]
    out.append("\n".join(f".t-{k} {{ font: var(--t-{k}); letter-spacing: var(--tr-{k}); }}" for k in t["font"]["scale"]))
    out.append("/* Chinese, Japanese and Korean keep their natural spacing: the tracking above is for Latin */\n"
               f":is({', '.join(names)}):is(:lang(zh), :lang(ja), :lang(ko)) {{ letter-spacing: 0; }}")
    out.append("""/* line icons: one library, one stroke; selected = primary colour, same stroke */
.icon { width: var(--icon-lg); height: var(--icon-lg); fill: none; stroke: currentColor;
  stroke-width: var(--icon-stroke); stroke-linecap: round; stroke-linejoin: round; flex: none; }
.icon.sm { width: var(--icon-sm); height: var(--icon-sm); }
.icon.md { width: var(--icon-md); height: var(--icon-md); }
.icon.xl { width: var(--icon-xl); height: var(--icon-xl); }
.is-active > .icon, .icon.active { color: var(--c-primary); }""")
    return "\n\n".join(out) + "\n"


# ---------- emit: SwiftUI ----------
SWIFT_FONT = {"large-title": "largeTitle", "title-1": "title", "title-2": "title2", "title-3": "title3",
              "headline": "headline", "body": "body", "callout": "callout", "subhead": "subheadline",
              "footnote": "footnote", "caption": "caption"}
SWIFT_DEFAULT_WEIGHT = {"headline": 600}  # every other system text style is regular
SWIFT_WEIGHT = {400: "regular", 500: "medium", 600: "semibold", 700: "bold"}

SWIFT = """// @@title@@
import SwiftUI
import UIKit

extension Color {
    /// A colour that follows light and dark mode.
    init(light: UInt32, dark: UInt32, lightAlpha: CGFloat = 1, darkAlpha: CGFloat = 1) {
        self.init(uiColor: UIColor { traits in
            traits.userInterfaceStyle == .dark ? UIColor(hex: dark, alpha: darkAlpha) : UIColor(hex: light, alpha: lightAlpha)
        })
    }
}

extension UIColor {
    convenience init(hex: UInt32, alpha: CGFloat = 1) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: alpha)
    }
}

/// Colours. textPlaceholder is only for placeholders, disabled text, chevrons and decorative icons;
/// borderStrong only for inputs, checkboxes and switches that are off; cards and dividers use border.
enum Palette {
@@palette@@
}

enum Radius {
@@radius@@
}

enum Space {
@@space@@
}

/// Sizes: the minimum hit area, and control heights (lg is the primary button).
enum Size {
    static let hitMin: CGFloat = @@hit@@
@@controls@@
}

/// Text styles: the system styles, so Dynamic Type works; weights as in tokens.json.
extension Font {
@@fonts@@
}

extension View {
    /// Long reading text (notes, articles): body size on @@longlh@@ pt lines.
    func bodyLong() -> some View { font(.appBody).lineSpacing(@@longgap@@) }
}

/// Motion: ease-out for most changes, a light spring for things that appear; no big bounces, no parallax.
enum Motion {
@@motion@@
}

/// Icons: SF Symbols, regular weight, medium scale; selected items only change colour to Palette.primary.
enum Icon {
    static let sm: CGFloat = @@icon_sm@@
    static let md: CGFloat = @@icon_md@@
    static let lg: CGFloat = @@icon_lg@@
    static let xl: CGFloat = @@icon_xl@@
    static let weight: Font.Weight = .regular
}

/// Shadow colours follow the mode: dark mode is @@dark_k@@ times stronger, as in theme.css.
enum Shadow {
@@shadows@@
}

extension View {
    /// elev-1 to elev-3 from theme.css. Put them on a background shape, never on a view with text in it.
@@elev@@
}

/// Card: solid surface, a 1 pt hairline and elev-1. The shadow sits on the background shape, so text stays crisp.
struct Card: ViewModifier {
    var radius: CGFloat = Radius.lg
    private var shape: RoundedRectangle { RoundedRectangle(cornerRadius: radius, style: .continuous) }

    func body(content: Content) -> some View {
        content
            .background { shape.fill(Palette.surface).elev1() }
            .overlay { shape.strokeBorder(Palette.border, lineWidth: 1) }
    }
}

/// Frost: the one material, for bars, sheets, popovers and floating controls; never for cards.
/// - edges: the sides that get the 1 pt hairline. A top bar uses .bottom, a bottom bar .top, floating pieces .all.
/// - radius: defaults to Radius.lg for .all and to 0 otherwise, so a full-width bar stays square.
/// - floating: tab bars, floating buttons and menus add elev-2.
/// iOS 26 and later use Liquid Glass, which draws its own edge and depth. Earlier versions put the
/// frost colour (88% surface) over the system blur, as theme.css does.
struct Frost: ViewModifier {
    var radius: CGFloat? = nil
    var edges: Edge.Set = .all
    var floating = false
    private var shape: RoundedRectangle {
        RoundedRectangle(cornerRadius: radius ?? (edges == .all ? Radius.lg : 0), style: .continuous)
    }

    @ViewBuilder func body(content: Content) -> some View {
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            content.glassEffect(.regular, in: shape)
        } else {
            fallback(content)
        }
        #else
        fallback(content)
        #endif
    }

    private func fallback(_ content: Content) -> some View {
        content
            .background { fill }
            .overlay { hairline }
    }

    private var material: some View {
        shape.fill(Palette.frost).background(.ultraThinMaterial, in: shape)
    }

    @ViewBuilder private var fill: some View {
        if floating {
            material.elev2()
        } else {
            material
        }
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

extension View {
    func card(radius: CGFloat = Radius.lg) -> some View { modifier(Card(radius: radius)) }
    func frost(radius: CGFloat? = nil, edges: Edge.Set = .all, floating: Bool = false) -> some View {
        modifier(Frost(radius: radius, edges: edges, floating: floating))
    }
}
"""


def swift_colour(light, dark):
    (lh, la), (dh, da) = split(light), split(dark)
    alpha = "" if la == da == 1 else f", lightAlpha: {la:g}, darkAlpha: {da:g}"
    return f"Color(light: 0x{lh}, dark: 0x{dh}{alpha})"


def swift(t):
    L, D = t["color"]["light"], t["color"]["dark"]
    palette = [f"    static let {camel(k)} = {swift_colour(L[k], D[k])}" for k in L if k != "shadow"]

    fonts = []
    for k, style in SWIFT_FONT.items():
        w = t["font"]["scale"][k][2]
        weight = "" if w == SWIFT_DEFAULT_WEIGHT.get(k, 400) else f".weight(.{SWIFT_WEIGHT[w]})"
        fonts.append(f"    static let app{pascal(k)} = Font.{style}{weight}")
    body, long = t["font"]["scale"]["body"], t["font"]["scale"]["body-long"]

    shadows, elev = [], []
    for n, layers in t["elevation"].items():
        names = [f"e{n}"] if len(layers) == 1 else [f"e{n}{c}" for c in "abc"[:len(layers)]]
        chain = []
        for nm, (x, y, b, s, a) in zip(names, layers):
            dark_a = round(min(a * DARK_SHADOW, 1), 3)
            shadows.append(f"    static let {nm} = Color(light: 0x{split(L['shadow'])[0]}, dark: 0x{split(D['shadow'])[0]}, "
                           f"lightAlpha: {a:g}, darkAlpha: {dark_a:g})")
            chain.append(f"shadow(color: Shadow.{nm}, radius: {num(b / 2)}, x: {x}, y: {y})")
        elev.append(f"    func elev{n}() -> some View {{ {'.'.join(chain)} }}")

    mot = []
    for k, v in t["motion"].items():
        ms, (x1, y1, x2, y2) = motion(v)
        mot.append(f"    static let {camel(k)} = Animation.timingCurve({num(x1)}, {num(y1)}, {num(x2)}, {num(y2)}, duration: {num(ms / 1000)})")

    return fill(
        SWIFT,
        title=f"{t['name']} theme: generated by rian-app-theme, {credit(t)}",
        palette="\n".join(palette),
        radius="\n".join(f"    static let {k}: CGFloat = {v}" for k, v in t["radius"].items() if k != "full"),
        space="\n".join(f"    static let s{k}: CGFloat = {v}" for k, v in t["space"].items()),
        hit=t["size"]["hit-min"]["ios"],
        controls="\n".join(f"    static let control{pascal(k)}: CGFloat = {v}" for k, v in t["size"]["control-h"].items()),
        fonts="\n".join(fonts),
        longlh=long[1], longgap=long[1] - body[1],
        motion="\n".join(mot),
        icon_sm=t["icon"]["size"]["sm"], icon_md=t["icon"]["size"]["md"],
        icon_lg=t["icon"]["size"]["lg"], icon_xl=t["icon"]["size"]["xl"],
        dark_k=num(DARK_SHADOW), shadows="\n".join(shadows), elev="\n".join(elev),
    )


# ---------- emit: Jetpack Compose ----------
# Material 3 role -> token, or (light token, dark token) where the two modes differ
COMPOSE_ROLES = [
    ("primary", "primary"), ("onPrimary", "on-primary"), ("primaryContainer", "primary-container"),
    ("onPrimaryContainer", "on-primary-container"), ("inversePrimary", None),
    ("secondary", "text-2"), ("onSecondary", "surface"),
    ("secondaryContainer", "primary-container"), ("onSecondaryContainer", "on-primary-container"),
    ("tertiary", "info"), ("onTertiary", "on-info"), ("tertiaryContainer", "info-container"),
    ("onTertiaryContainer", "info"),
    ("background", "bg"), ("onBackground", "text"), ("surface", "surface"), ("onSurface", "text"),
    ("surfaceVariant", "surface-2"), ("onSurfaceVariant", "text-2"), ("surfaceTint", "surface"),
    ("inverseSurface", "inverse-surface"), ("inverseOnSurface", "on-inverse"),
    ("error", "danger"), ("onError", "on-danger"), ("errorContainer", "danger-container"),
    ("onErrorContainer", "danger"),
    ("outline", "border-strong"), ("outlineVariant", "border"), ("scrim", "scrim"),
    ("surfaceBright", ("surface", "surface-3")), ("surfaceDim", ("surface-3", "bg")),
    ("surfaceContainerLowest", ("surface", "bg")), ("surfaceContainerLow", "surface"),
    ("surfaceContainer", "surface-2"), ("surfaceContainerHigh", "surface-2"),
    ("surfaceContainerHighest", "surface-3"),
]
# colours Material 3 has no role for
EXTENDED = ["surface-3", "border-strong", "text-placeholder",
            "success", "on-success", "success-container", "warning", "on-warning", "warning-container",
            "info", "on-info", "info-container", "disabled-fg", "disabled-bg", "state-hover", "state-pressed",
            "focus", "selection", "frost", "frost-border"]
# Material 3 type slot -> (scale key, weight override)
COMPOSE_TYPE = [("displaySmall", "large-title", None), ("headlineMedium", "title-1", None),
                ("headlineSmall", "title-2", None), ("titleLarge", "title-3", None),
                ("titleMedium", "headline", None), ("titleSmall", "subhead", 600),
                ("bodyLarge", "body", None), ("bodyMedium", "subhead", None), ("bodySmall", "footnote", None),
                ("labelLarge", "headline", None), ("labelSmall", "caption", None)]
COMPOSE_EXTRA_TYPE = ["callout", "body-long"]  # no Material 3 slot

KOTLIN = """// @@title@@
// Needs Compose Material 3 1.2 or later (surfaceBright, surfaceDim and the surfaceContainer roles).
package theme

import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

/** Every Material 3 role is set, so nothing falls back to the purple baseline.
 *  outline (inputs, checkboxes) = border-strong; outlineVariant (cards, dividers) = border. */
val LightColors = lightColorScheme(
@@light@@
)

val DarkColors = darkColorScheme(
@@dark@@
)

/** Colours Material 3 has no role for: read them with AppTheme.colors, e.g. AppTheme.colors.success.
 *  textPlaceholder is only for placeholders, disabled text, chevrons and decorative icons. */
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

val LocalExtendedColors = staticCompositionLocalOf { LightExtendedColors }

object AppTheme {
    val colors: ExtendedColors
        @Composable @ReadOnlyComposable get() = LocalExtendedColors.current
}

/** Frost: translucent fill + 1 dp hairline for bars, sheets and floating controls (never cards).
 *  Compose has no built-in backdrop blur: use the fill as is (it is 88% opaque), or blur with a library such as Haze. */
object Frost {
    fun fill(dark: Boolean) = if (dark) DarkExtendedColors.frost else LightExtendedColors.frost
    fun border(dark: Boolean) = if (dark) DarkExtendedColors.frostBorder else LightExtendedColors.frostBorder
}

/** Icons: Material Symbols Rounded, weight 400, fill 0, grade 0; selected = primary colour. */
object IconSize {
    val sm = @@icon_sm@@.dp; val md = @@icon_md@@.dp
    val lg = @@icon_lg@@.dp; val xl = @@icon_xl@@.dp
    const val WEIGHT = 400
}

/** Corner radii; full is ChipShape (CircleShape). */
object Radius {
@@radius@@
}

/** Spacing: multiples of 4, e.g. Modifier.padding(Space.s4). */
object Space {
@@space@@
}

/** Sizes: the minimum touch target, and control heights (lg is the primary button). */
object AppSize {
    val hitMin = @@hit@@.dp
@@controls@@
}

/** Motion: ease-out for most changes, a light spring for things that appear; e.g. tween(Motion.STANDARD_MS, easing = Motion.StandardEasing). */
object Motion {
@@motion@@
}

/** Material 3 picks corners by size key: text fields use extraSmall, chips small, cards medium, sheets large. */
val AppShapes = Shapes(
@@shapes@@
)

/** Buttons are @@button_r@@ dp (not Material's pill); chips and tags are full pills. AppButton and AppChip pass these. */
val ButtonShape = RoundedCornerShape(@@button_r@@.dp)
val ChipShape = CircleShape

val AppTypography = Typography(
@@type@@
)

/** Text styles with no Material 3 slot. */
object AppTextStyles {
@@extra_type@@
}

@Composable
fun AppTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    CompositionLocalProvider(LocalExtendedColors provides if (dark) DarkExtendedColors else LightExtendedColors) {
        MaterialTheme(
            colorScheme = if (dark) DarkColors else LightColors,
            shapes = AppShapes,
            typography = AppTypography,
            content = content,
        )
    }
}

/** Primary button: primary fill, on-primary label, @@button_r@@ dp corners, @@button_h@@ dp tall, no shadow. Use it instead of Button. */
@Composable
fun AppButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    colors: ButtonColors = ButtonDefaults.buttonColors(
        disabledContainerColor = AppTheme.colors.disabledBg,
        disabledContentColor = AppTheme.colors.disabledFg,
    ),
    content: @Composable RowScope.() -> Unit,
) = Button(
    onClick = onClick,
    modifier = modifier.heightIn(min = AppSize.controlLg),
    enabled = enabled,
    shape = ButtonShape,
    colors = colors,
    content = content,
)

/** Secondary button: surface fill, 1 dp border, text-coloured label, same shape and height as AppButton. */
@Composable
fun AppOutlinedButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit,
) = OutlinedButton(
    onClick = onClick,
    modifier = modifier.heightIn(min = AppSize.controlLg),
    enabled = enabled,
    shape = ButtonShape,
    colors = ButtonDefaults.outlinedButtonColors(
        containerColor = MaterialTheme.colorScheme.surface,
        contentColor = MaterialTheme.colorScheme.onSurface,
    ),
    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    content = content,
)

/** Filter chip: full pill, subhead label (bodyMedium; FilterChip's default labelLarge is the 17 sp headline);
 *  unselected = surface fill, 1 dp border and text-2 label; selected = primary-container fill, on-primary-container
 *  label, no border. Use it instead of FilterChip. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppChip(
    selected: Boolean,
    onClick: () -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    leadingIcon: (@Composable () -> Unit)? = null,
) = FilterChip(
    selected = selected,
    onClick = onClick,
    label = { Text(label, style = MaterialTheme.typography.bodyMedium, fontWeight = if (selected) FontWeight.W600 else null) },
    modifier = modifier,
    enabled = enabled,
    leadingIcon = leadingIcon,
    shape = ChipShape,
    colors = FilterChipDefaults.filterChipColors(containerColor = MaterialTheme.colorScheme.surface),
    border = FilterChipDefaults.filterChipBorder(
        enabled = enabled,
        selected = selected,
        borderColor = MaterialTheme.colorScheme.outlineVariant,
    ),
)

/** Status tag: the status colour on its own container, full pill,
 *  e.g. StatusTag("已完成", AppTheme.colors.success, AppTheme.colors.successContainer). */
@Composable
fun StatusTag(text: String, color: Color, container: Color, modifier: Modifier = Modifier) =
    Surface(modifier = modifier, shape = ChipShape, color = container, contentColor = color) {
        Text(text, style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp))
    }
"""


def kt_colour(colour):
    h, a = split(colour)
    return "Color(0x%02X%s)" % (round(a * 255), h)


def kt_text(size, lh, w, tr):
    return (f"TextStyle(fontSize = {size}.sp, lineHeight = {lh}.sp, fontWeight = FontWeight.W{w}, "
            f"letterSpacing = ({tr / size:.4f}).em)")


def kotlin(t):
    L, D = t["color"]["light"], t["color"]["dark"]

    def scheme(M, other, dark):
        rows = []
        for role, key in COMPOSE_ROLES:
            if key is None:  # inversePrimary: the other mode's primary, for snackbar actions on inverseSurface
                colour = other["primary"]
            else:
                colour = M[key[1] if dark else key[0]] if isinstance(key, tuple) else M[key]
            rows.append(f"    {role} = {kt_colour(colour)},")
        return "\n".join(rows)

    scale = t["font"]["scale"]
    type_rows = []
    for slot, key, weight in COMPOSE_TYPE:
        size, lh, w, tr = scale[key]
        type_rows.append(f"    {slot} = {kt_text(size, lh, weight or w, tr)},")
    extra = [f"    val {camel(k)} = {kt_text(*scale[k])}" for k in COMPOSE_EXTRA_TYPE]

    mot = []
    for k, v in t["motion"].items():
        ms, curve = motion(v)
        mot.append(f"    const val {k.upper()}_MS = {ms}")
        mot.append(f"    val {pascal(k)}Easing = CubicBezierEasing({', '.join(num(x) + 'f' for x in curve)})")

    r = t["radius"]
    shapes = {"extraSmall": r["md"], "small": r["md"], "medium": r["lg"], "large": r["xl"], "extraLarge": r["xl"]}
    return fill(
        KOTLIN,
        title=f"{t['name']} theme: generated by rian-app-theme, {credit(t)}",
        light=scheme(L, D, False), dark=scheme(D, L, True),
        ext_fields="\n".join(f"    val {camel(k)}: Color," for k in EXTENDED),
        ext_light="\n".join(f"    {camel(k)} = {kt_colour(L[k])}," for k in EXTENDED),
        ext_dark="\n".join(f"    {camel(k)} = {kt_colour(D[k])}," for k in EXTENDED),
        icon_sm=t["icon"]["size"]["sm"], icon_md=t["icon"]["size"]["md"],
        icon_lg=t["icon"]["size"]["lg"], icon_xl=t["icon"]["size"]["xl"],
        radius="\n".join(f"    val {k} = {v}.dp" for k, v in r.items() if k != "full"),
        space="\n".join(f"    val s{k} = {v}.dp" for k, v in t["space"].items()),
        hit=t["size"]["hit-min"]["android"],
        controls="\n".join(f"    val control{pascal(k)} = {v}.dp" for k, v in t["size"]["control-h"].items()),
        motion="\n".join(mot),
        shapes=",\n".join(f"    {k} = RoundedCornerShape({v}.dp)" for k, v in shapes.items()),
        button_r=r["lg"], button_h=t["size"]["control-h"]["lg"],
        type="\n".join(type_rows), extra_type="\n".join(extra),
    )


# ---------- emit: Tailwind ----------
def tailwind(t):
    C = t["color"]["light"]
    colors = ",\n".join(
        f"        '{k}': " + (f"'rgb(var(--c-{k}-rgb) / <alpha-value>)'" if C[k].startswith("#") else f"'var(--c-{k})'")
        for k in C if k != "shadow")
    radius = ",\n".join(f"        '{k}': 'var(--r-{k})'" for k in t["radius"])
    heights = ", ".join(f"'control-{k}': 'var(--control-h-{k})'" for k in t["size"]["control-h"])
    return f"""// {t['name']} theme: Tailwind (v3.3+) preset. Load theme.css first: every value reads its CSS variables
// (and theme.css defines .frost). Opaque colours take opacity modifiers, e.g. bg-primary/10.
// Text styles are not here: use theme.css's .t-* classes (class="t-body"), which also drop the tracking for CJK.
module.exports = {{
  theme: {{
    extend: {{
      colors: {{
{colors}
      }},
      borderColor: {{ DEFAULT: 'var(--c-border)' }},
      ringColor: {{ DEFAULT: 'var(--c-focus)' }},
      ringOffsetColor: {{ DEFAULT: 'var(--c-bg)' }},
      borderRadius: {{
{radius}
      }},
      boxShadow: {{ e1: 'var(--elev-1)', e2: 'var(--elev-2)', e3: 'var(--elev-3)' }},
      fontFamily: {{ sans: ['var(--font)'], mono: ['var(--font-mono)'] }},
      minHeight: {{ hit: 'var(--hit-min)' }},
      minWidth: {{ hit: 'var(--hit-min)' }},
      height: {{ {heights} }},
    }},
  }},
}};
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--accent", default=DEFAULT_ACCENT,
                    help="the app icon's accent: 蓝 blue (default), 绿 green, 紫 violet; "
                         "灰 gray, 珊瑚 coral and 黄 yellow give a 蓝 UI primary")
    ap.add_argument("-o", "--out", default="theme-out")
    a = ap.parse_args()
    t = derive(a.name, a.accent)
    fails = audit(t)
    if fails:
        print("\nFAIL: contrast check failed, nothing written:\n  " + "\n  ".join(fails))
        sys.exit(1)
    os.makedirs(a.out, exist_ok=True)
    files = {"tokens.json": json.dumps(t, ensure_ascii=False, indent=2), "theme.css": css(t),
             "Theme.swift": swift(t), "Theme.kt": kotlin(t), "tailwind.preset.js": tailwind(t)}
    for f, body in files.items():
        open(os.path.join(a.out, f), "w", encoding="utf-8").write(body)
    for mode in ("light", "dark"):
        C = t["color"][mode]
        print(f"{mode}: primary {C['primary']}, on-primary {C['on-primary']}, primary-container {C['primary-container']}")
    print("contrast: all pass")
    print("wrote", ", ".join(files), "to", a.out)


if __name__ == "__main__":
    main()
