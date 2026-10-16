#!/usr/bin/env python3
"""Build an app UI theme in the minimal line style, using the same accent colour as the app icon.

    python3 scripts/build.py --name Tide -o out/                 # default accent: 蓝 (blue)
    python3 scripts/build.py --name Tide --accent 紫 -o out/     # or --accent violet

Writes tokens.json, theme.css, Theme.swift, Theme.kt and tailwind.preset.js to the output folder.
Accent names come from assets/palette.json (Chinese or English names both work). Warm accents
(珊瑚 coral, 黄 yellow) stay in the app icon and never become the UI primary: the script uses 蓝 instead.
Every text and accent colour is checked against WCAG contrast and nudged until it passes.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = json.load(open(os.path.join(HERE, "..", "assets", "palette.json"), encoding="utf-8"))
DEFAULT_ACCENT = "蓝"


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


def reach(start, toward, bg, target):
    """walk from start toward `toward` until the contrast with bg reaches target;
    if even `toward` falls short, keep going to black or white, whichever is further from bg"""
    ink = "#000000" if lum(bg) > 0.18 else "#FFFFFF"
    for a, b in ((start, toward), (toward, ink)):
        for i in range(0, 101):
            c = mix(a, b, i / 100)
            if contrast(c, bg) >= target:
                return c
    return ink


def rgba(h, a):
    r, g, b = rgb(h)
    return f"rgba({r}, {g}, {b}, {a})"


def split(c):
    """'#RRGGBB' or 'rgba(r, g, b, a)' -> ('RRGGBB', alpha)"""
    if c.startswith("#"):
        return c.lstrip("#").upper(), 1.0
    r, g, b, a = (float(v) for v in re.findall(r"[\d.]+", c))
    return "%02X%02X%02X" % (int(r), int(g), int(b)), a


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
    if a.get("warm"):
        # warm accents stay in the app icon; the UI primary is never coral or yellow
        print(f"note: {ak} ({a['en']}) is a warm accent and never the UI primary; "
              f"using {DEFAULT_ACCENT} instead (keep {ak} in the app icon)")
        source["icon-accent"] = ak
        ak, a = find(DEFAULT_ACCENT)
        source.update(accent=ak, en=a["en"])
    hi, main = a["tones"]

    L = dict(PALETTE["neutral"]["light"])
    D = dict(PALETTE["neutral"]["dark"])
    shadow = {"light": L.pop("shadow"), "dark": D.pop("shadow")}
    for M, ink in ((L, "#000000"), (D, "#FFFFFF")):
        M["text-2"] = reach(M["text-2"], ink, M["surface-2"], 4.5)
        M["text-3"] = reach(M["text-3"], ink, M["surface"], 3.0)

    def tone(lt, mn):
        """an accent's text-safe colour: light mode darkens the main tone, dark mode lifts it toward the light tone"""
        return (reach(mn, mix(mn, "#000000", 0.5), L["surface"], 4.5),
                reach(mn, lt, D["surface"], 4.5))

    pL, pD = tone(hi, main)
    for M, p, k in ((L, pL, 0.90), (D, pD, 0.80)):
        M["primary"] = p
        # white on the accent when it passes (the Apple look); otherwise a deep shade of the accent
        # itself (the Material dark look), and plain near-black if even that falls short
        deep = mix(p, "#000000", 0.82)
        M["on-primary"] = next(c for c in ("#FFFFFF", deep, "#111113") if contrast(c, p) >= 4.5 or c == "#111113")
        M["primary-container"] = mix(p, M["surface"], k)
        M["on-primary-container"] = reach(p, "#000000" if M is L else "#FFFFFF", M["primary-container"], 4.5)

    # status colours are text on their own container (chips, banners), so they pass 4.5:1 there,
    # and with it on the plain surface too
    for k, src in PALETTE["status"].items():
        lt, mn = PALETTE["accent"][src]["tones"]
        lc, dc = mix(mn, L["surface"], 0.90), mix(mn, D["surface"], 0.80)
        L[k], D[k] = reach(mn, mix(mn, "#000000", 0.5), lc, 4.5), reach(mn, lt, dc, 4.5)
        L[k + "-container"], D[k + "-container"] = lc, dc

    # frost: the translucent material for bars, sheets, popovers and floating controls; no tint
    L["frost"] = "rgba(255, 255, 255, 0.72)"
    L["frost-border"] = "rgba(0, 0, 0, 0.06)"
    D["frost"] = rgba(D["surface"], 0.6)
    D["frost-border"] = "rgba(255, 255, 255, 0.08)"
    L["shadow"], D["shadow"] = shadow["light"], shadow["dark"]

    return {
        "name": name,
        "source": source,
        "color": {"light": L, "dark": D},
        "radius": {"xs": 4, "sm": 6, "md": 8, "lg": 12, "xl": 16, "full": 9999},
        "space": {"1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48},
        "font": {
            "family": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', Roboto, 'Noto Sans SC', 'Helvetica Neue', sans-serif",
            "mono": "'SF Mono', ui-monospace, 'JetBrains Mono', Menlo, monospace",
            "scale": {
                "large-title": [34, 41, 700, 0.37], "title-1": [28, 34, 700, 0.36], "title-2": [22, 28, 600, 0.35],
                "title-3": [20, 25, 600, 0.38], "headline": [17, 22, 600, -0.41], "body": [17, 22, 400, -0.41],
                "callout": [16, 21, 400, -0.32], "subhead": [15, 20, 400, -0.24], "footnote": [13, 18, 400, -0.08],
                "caption": [12, 16, 500, 0.0],
            },
        },
        # layers: [x, y, blur, spread, alpha]; dark mode multiplies alpha by 2.6
        "elevation": {
            "1": [[0, 1, 2, 0, 0.06], [0, 0, 0, 1, 0.04]],
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


def credit(t):
    s = t["source"]
    note = f"; app icon keeps {s['icon-accent']}" if "icon-accent" in s else ""
    return f"accent {s['accent']} ({s['en']}){note}"


# ---------- emit ----------
def shadow_css(layers, colour, k=1.0):
    return ", ".join(f"{x}px {y}px {b}px{f' {s}px' if s else ''} {rgba(colour, round(min(a * k, 1), 3))}"
                     for x, y, b, s, a in layers)


def css(t):
    out = [f"/* {t['name']} theme: generated by rian-app-theme, {credit(t)} */"]

    def block(sel, mode):
        C = t["color"][mode]
        lines = [f"  --c-{k}: {v};" for k, v in C.items() if k != "shadow"]
        k = 1.0 if mode == "light" else 2.6
        lines += [f"  --elev-{n}: {shadow_css(L, C['shadow'], k)};" for n, L in t["elevation"].items()]
        lines.append(f"  color-scheme: {mode};")
        return f"{sel} {{\n" + "\n".join(lines) + "\n}"

    common = [f"  --r-{k}: {v}px;" for k, v in t["radius"].items()]
    common += [f"  --s-{k}: {v}px;" for k, v in t["space"].items()]
    common += [f"  --font: {t['font']['family']};", f"  --font-mono: {t['font']['mono']};"]
    for k, (size, lh, w, tr) in t["font"]["scale"].items():
        common.append(f"  --t-{k}: {w} {size}px/{lh}px var(--font);")
        common.append(f"  --tr-{k}: {tr / size:.4f}em;")
    common += [f"  --m-{k}: {v};" for k, v in t["motion"].items()]
    common += [f"  --icon-{k}: {v}px;" for k, v in t["icon"]["size"].items()]
    common.append(f"  --icon-stroke: {t['icon']['stroke']};")
    out.append(":root {\n" + "\n".join(common) + "\n}")
    out.append(block(":root, [data-theme=\"light\"]", "light"))
    out.append("@media (prefers-color-scheme: dark) {\n" + block(":root:not([data-theme=\"light\"])", "dark").replace("\n", "\n  ") + "\n}")
    out.append(block("[data-theme=\"dark\"]", "dark"))
    out.append(f"""/* frost material: bars, sheets, popovers and floating controls (never cards).
   Floating pieces add box-shadow: var(--elev-2); a full-width bar keeps only the hairline
   on its content side, e.g. border-width: 0 0 1px. */
.frost {{
  background: var(--c-frost);
  -webkit-backdrop-filter: blur({t['blur']['frost']}px) saturate({t['blur']['saturate']});
  backdrop-filter: blur({t['blur']['frost']}px) saturate({t['blur']['saturate']});
  border: 1px solid var(--c-frost-border);
}}""")
    for k in t["font"]["scale"]:
        out.append(f".t-{k} {{ font: var(--t-{k}); letter-spacing: var(--tr-{k}); }}")
    out.append("""/* line icons: one library, one stroke; selected = primary colour, same stroke */
.icon { width: var(--icon-lg); height: var(--icon-lg); fill: none; stroke: currentColor;
  stroke-width: var(--icon-stroke); stroke-linecap: round; stroke-linejoin: round; flex: none; }
.icon.sm { width: var(--icon-sm); height: var(--icon-sm); }
.icon.md { width: var(--icon-md); height: var(--icon-md); }
.icon.xl { width: var(--icon-xl); height: var(--icon-xl); }
.is-active > .icon, .icon.active { color: var(--c-primary); }""")
    return "\n\n".join(out) + "\n"


def swift(t):
    L, D = t["color"]["light"], t["color"]["dark"]

    def camel(k):
        p = k.split("-")
        return p[0] + "".join(x.title() for x in p[1:])

    rows = []
    for k in L:
        if k == "shadow":
            continue
        (lh, la), (dh, da) = split(L[k]), split(D[k])
        alpha = "" if la == da == 1 else f", lightAlpha: {la:g}, darkAlpha: {da:g}"
        rows.append(f"    static let {camel(k)} = Color(light: 0x{lh}, dark: 0x{dh}{alpha})")
    radii = "\n".join(f"    static let {k}: CGFloat = {v}" for k, v in t["radius"].items() if k != "full")
    space = "\n".join(f"    static let s{k}: CGFloat = {v}" for k, v in t["space"].items())
    return f"""// {t['name']} theme: generated by rian-app-theme, {credit(t)}
import SwiftUI

extension Color {{
    init(light: UInt32, dark: UInt32, lightAlpha: CGFloat = 1, darkAlpha: CGFloat = 1) {{
        self.init(uiColor: UIColor {{
            $0.userInterfaceStyle == .dark ? UIColor(hex: dark, alpha: darkAlpha) : UIColor(hex: light, alpha: lightAlpha)
        }})
    }}
}}

extension UIColor {{
    convenience init(hex: UInt32, alpha: CGFloat = 1) {{
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: alpha)
    }}
}}

enum Palette {{
{chr(10).join(rows)}
}}

enum Radius {{
{radii}
}}

enum Space {{
{space}
}}

/// Icons: SF Symbols, regular weight, medium scale; selected items only change colour to Palette.primary.
enum Icon {{
    static let sm: CGFloat = {t['icon']['size']['sm']}
    static let md: CGFloat = {t['icon']['size']['md']}
    static let lg: CGFloat = {t['icon']['size']['lg']}
    static let xl: CGFloat = {t['icon']['size']['xl']}
    static let weight: Font.Weight = .regular
}}

/// Card: solid surface, a 1 pt hairline and a barely-there shadow.
struct Card: ViewModifier {{
    var radius: CGFloat = Radius.lg
    private var shape: RoundedRectangle {{ RoundedRectangle(cornerRadius: radius, style: .continuous) }}
    func body(content: Content) -> some View {{
        content
            .background(Palette.surface, in: shape)
            .overlay(shape.strokeBorder(Palette.border, lineWidth: 1))
            .shadow(color: .black.opacity(0.06), radius: 1, y: 1)
    }}
}}

/// Frost: the system material (blur + saturation), a 1 pt hairline and no tint.
/// For bars, sheets, popovers and floating controls; never for cards.
struct Frost: ViewModifier {{
    var radius: CGFloat = Radius.lg
    private var shape: RoundedRectangle {{ RoundedRectangle(cornerRadius: radius, style: .continuous) }}
    func body(content: Content) -> some View {{
        content
            .background(.regularMaterial, in: shape)
            .overlay(shape.strokeBorder(Palette.frostBorder, lineWidth: 1))
    }}
}}

extension View {{
    func card(radius: CGFloat = Radius.lg) -> some View {{ modifier(Card(radius: radius)) }}
    func frost(radius: CGFloat = Radius.lg) -> some View {{ modifier(Frost(radius: radius)) }}
}}
"""


def kotlin(t):
    L, D = t["color"]["light"], t["color"]["dark"]

    def c(colour):
        h, a = split(colour)
        return "Color(0x%02X%s)" % (round(a * 255), h)

    def scheme(M, fn):
        m = {"primary": "primary", "onPrimary": "on-primary", "primaryContainer": "primary-container",
             "onPrimaryContainer": "on-primary-container",
             "secondary": "text-2", "onSecondary": "surface",
             "secondaryContainer": "primary-container", "onSecondaryContainer": "on-primary-container",
             "error": "danger", "errorContainer": "danger-container", "onErrorContainer": "danger",
             "background": "bg", "onBackground": "text", "surface": "surface", "onSurface": "text",
             "surfaceVariant": "surface-2", "onSurfaceVariant": "text-2", "surfaceTint": "surface",
             "surfaceContainerLowest": "surface", "surfaceContainerLow": "surface",
             "surfaceContainer": "surface-2", "surfaceContainerHigh": "surface-2",
             "surfaceContainerHighest": "surface-2",
             "outline": "text-3", "outlineVariant": "border"}
        body = ",\n".join(f"    {k} = {c(M[v])}" for k, v in m.items())
        return f"val {fn} = {'lightColorScheme' if fn.startswith('Light') else 'darkColorScheme'}(\n{body}\n)"

    type_rows = []
    names = {"large-title": "displaySmall", "title-1": "headlineMedium", "title-2": "headlineSmall",
             "title-3": "titleLarge", "headline": "titleMedium", "body": "bodyLarge", "callout": "bodyMedium",
             "subhead": "titleSmall", "footnote": "bodySmall", "caption": "labelSmall"}
    for k, (size, lh, w, tr) in t["font"]["scale"].items():
        type_rows.append(f"    {names[k]} = TextStyle(fontSize = {size}.sp, lineHeight = {lh}.sp, "
                         f"fontWeight = FontWeight.W{w}, letterSpacing = ({tr / size:.4f}).em)")
    r = t["radius"]
    return f"""// {t['name']} theme: generated by rian-app-theme, {credit(t)}
package theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

{scheme(L, 'LightColors')}

{scheme(D, 'DarkColors')}

/** Frost: translucent fill + 1 dp hairline for bars, sheets and floating controls (never cards).
 *  Compose has no built-in backdrop blur: use the fill as is, or blur with a library such as Haze. */
object Frost {{
    fun fill(dark: Boolean) = if (dark) {c(D['frost'])} else {c(L['frost'])}
    fun border(dark: Boolean) = if (dark) {c(D['frost-border'])} else {c(L['frost-border'])}
}}

/** Icons: Material Symbols Rounded, weight 400, fill 0, grade 0; selected = primary colour. */
object IconSize {{
    val sm = {t['icon']['size']['sm']}.dp; val md = {t['icon']['size']['md']}.dp
    val lg = {t['icon']['size']['lg']}.dp; val xl = {t['icon']['size']['xl']}.dp
    const val WEIGHT = 400
}}

val AppShapes = Shapes(
    extraSmall = RoundedCornerShape({r['xs']}.dp), small = RoundedCornerShape({r['sm']}.dp),
    medium = RoundedCornerShape({r['md']}.dp), large = RoundedCornerShape({r['lg']}.dp),
    extraLarge = RoundedCornerShape({r['xl']}.dp)
)

val AppTypography = Typography(
{(","+chr(10)).join(type_rows)}
)

@Composable
fun AppTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) =
    MaterialTheme(colorScheme = if (dark) DarkColors else LightColors,
                  shapes = AppShapes, typography = AppTypography, content = content)
"""


def tailwind(t):
    keys = [k for k in t["color"]["light"] if k != "shadow"]
    colors = ",\n".join(f"        '{k}': 'var(--c-{k})'" for k in keys)
    radius = ",\n".join(f"        '{k}': 'var(--r-{k})'" for k in t["radius"])
    return f"""// {t['name']} theme: Tailwind preset. Load theme.css first; values read its CSS variables (and it defines .frost).
module.exports = {{
  theme: {{
    extend: {{
      colors: {{
{colors}
      }},
      borderRadius: {{
{radius}
      }},
      boxShadow: {{ e1: 'var(--elev-1)', e2: 'var(--elev-2)', e3: 'var(--elev-3)' }},
      fontFamily: {{ sans: ['var(--font)'], mono: ['var(--font-mono)'] }},
    }},
  }},
}};
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--accent", default=DEFAULT_ACCENT, help="蓝 blue (default), 绿 green, 紫 violet, 灰 gray")
    ap.add_argument("-o", "--out", default="theme-out")
    a = ap.parse_args()
    t = derive(a.name, a.accent)
    os.makedirs(a.out, exist_ok=True)
    files = {"tokens.json": json.dumps(t, ensure_ascii=False, indent=2), "theme.css": css(t),
             "Theme.swift": swift(t), "Theme.kt": kotlin(t), "tailwind.preset.js": tailwind(t)}
    for f, body in files.items():
        open(os.path.join(a.out, f), "w", encoding="utf-8").write(body)
    for mode in ("light", "dark"):
        C = t["color"][mode]
        checks = [("text-2", "surface-2"), ("text-3", "surface"), ("primary", "surface"), ("on-primary", "primary"),
                  ("on-primary-container", "primary-container"), ("danger", "danger-container")]
        print(mode + ": " + ", ".join(f"{a}/{b} {contrast(C[a], C[b]):.1f}" for a, b in checks))
    print("wrote", ", ".join(files), "to", a.out)


if __name__ == "__main__":
    main()
