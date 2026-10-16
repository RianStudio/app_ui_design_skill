#!/usr/bin/env python3
"""Render the review sheet for a theme written by build.py, and measure it.

    python3 scripts/preview.py out/                                    # timer screen, desktop window dark
    python3 scripts/preview.py out/ --screen list --icon ledgerly-1024.png --icon-dark ledgerly-dark.png
    python3 scripts/preview.py out/ --screen notes --desktop-mode light

Writes out/preview.png: a 1960 px wide sheet, saved at --scale 2 (3920 px). From the top:
  1. title row: app name, icon accent -> UI primary, primary and primary-text values, time of the render;
  2. iPhone (390 x 844 pt) light at rest; iPhone dark scrolled, content under the glass bars, with a toast;
     Android (Material 3, Pixel 412 x 915 dp); a component strip in light and dark (desktop sizes);
  3. a 1280 x 800 desktop window (inverted-L layout, keyboard-cursor row, two multi-selected rows, the command
     menu open over scrim-menu); beside it the desktop type scale, and either a dialog or, when the icon accent
     is 珊瑚 / 黄 / 灰, an "icon x UI" cell: the warm icon next to the blue UI it falls back to, dark and light;
  4. swatches of the four schemes: light, dark, light-hc, dark-hc, each with its lowest contrast per text tier.

Screens: timer (focus timer), notes (notes app: long Chinese text, highlight, search field) and list (ledger:
amounts, filter pills, list grouped by day). Each has phone, Android and desktop content.

Then prints four checks, each PASS or FAIL (exit status 1 when one fails; preview.png is written either way):
  frost light / frost dark    bar text and icons over the content scrolled under them, >= 3:1 (dark on the
                              second iPhone, light on a scrolled light iPhone rendered off the sheet); glass
                              only: the scroll-edge fade is hidden while measuring, the inline title is skipped
  accent area desktop         pixels in the primary's hue (+-25 deg, LCh chroma >= 20) <= 5 % of the window,
                              measured with the command menu and its scrim hidden
  accent area phone           the same, <= 8 % of each phone screen (worst of the three)
Counting the faint selected tint too (chroma >= 4) is printed as INFO only.

Fonts: Inter (variable, opsz 14..32), Roboto Flex, Material Symbols Rounded and a Noto Sans SC subset come from
Google Fonts and are cached in ~/.cache/rian-app-theme/fonts; offline (or --offline) the sheet falls back to the
locally installed fonts and says so. The iPhone screens use Inter in place of SF Pro.

Needs Playwright + Chromium, numpy and Pillow (set CHROMIUM_PATH to use an existing Chromium).
"""
import argparse, base64, datetime, glob, hashlib, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # importing build.py must not leave a __pycache__ in the skill
sys.path.insert(0, HERE)
from build import COLUMNS, NEED, PALETTE, STATUS, TIERS, backgrounds, contrast, hex_to_lch, over  # noqa: E402

SCHEMES = ("light", "dark", "light-hc", "dark-hc")
SCHEME_NAME = {"light": "浅色 · 标准", "dark": "深色 · 标准", "light-hc": "浅色 · 高对比", "dark-hc": "深色 · 高对比"}
MODE_NAME = {"light": "浅色", "dark": "深色"}
BOARD_W = 1960  # 410 + 410 + 432 (phones) + 556 (component strip) + 3 gaps of 24 + 2 x 40 padding
FROST_MIN, DESK_MAX, PHONE_MAX = 3.0, 5.0, 8.0
HUE_BAND, STRONG_CHROMA, FAINT_CHROMA = 25, 20, 4


# ---------- icons: Lucide on a 24 grid, 1.5 px non-scaling stroke ----------
LUCIDE = {
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "inbox": '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "list": '<path d="M3 12h.01"/><path d="M3 18h.01"/><path d="M3 6h.01"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M8 6h13"/>',
    "chart": '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "card": '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>',
    "wallet": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "hash": '<line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>',
    "chev-down": '<path d="m6 9 6 6 6-6"/>',
    "chev-left": '<path d="m15 18-6-6 6-6"/>',
    "chev-right": '<path d="m9 18 6-6-6-6"/>',
    "filter": '<path d="M3 6h18"/><path d="M7 12h10"/><path d="M10 18h4"/>',
    "sliders": '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
    "utensils": '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>',
    "train": '<path d="M8 3.1V7a4 4 0 0 0 8 0V3.1"/><path d="m9 15-1-1"/><path d="m15 15 1-1"/><path d="M9 19c-2.8 0-5-2.2-5-5v-4a8 8 0 0 1 16 0v4c0 2.8-2.2 5-5 5Z"/><path d="m8 19-2 3"/><path d="m16 19 2 3"/>',
    "coffee": '<path d="M10 2v2"/><path d="M14 2v2"/><path d="M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"/><path d="M6 2v2"/>',
    "bag": '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    "cart": '<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>',
    "banknote": '<rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "phone": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
    "car": '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
    "file-down": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M12 18v-6"/><path d="m9 15 3 3 3-3"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "pin": '<path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>',
    "archive": '<rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "briefcase": '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "bulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "history": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "home": '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "pen": '<path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "receipt": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/>',
    "dumbbell": '<path d="M14.4 14.4 9.6 9.6"/><path d="M18.657 21.485a2 2 0 1 1-2.829-2.828l-1.767 1.768a2 2 0 1 1-2.829-2.829l6.364-6.364a2 2 0 1 1 2.829 2.829l-1.768 1.767a2 2 0 1 1 2.828 2.829z"/><path d="m21.5 21.5-1.4-1.4"/><path d="M3.9 3.9 2.5 2.5"/><path d="M6.404 12.768a2 2 0 1 1-2.829-2.829l1.768-1.767a2 2 0 1 1-2.828-2.829l2.828-2.828a2 2 0 1 1 2.829 2.828l1.767-1.768a2 2 0 1 1 2.829 2.829z"/>',
    "zap": '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
    "tag": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>',
    "merge": '<path d="m8 6 4-4 4 4"/><path d="M12 2v10.3a4 4 0 0 1-1.172 2.872L4 22"/><path d="m20 22-5-5"/>',
    "arrow-in": '<path d="M17 7 7 17"/><path d="M17 17H7V7"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "timer": '<line x1="10" x2="14" y1="2" y2="2"/><line x1="12" x2="15" y1="14" y2="11"/><circle cx="12" cy="14" r="8"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "square": '<rect width="18" height="18" x="3" y="3" rx="2"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "more": '<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>',
}
# Material Symbols Rounded names for the Android screen; LUCIDE stands in when the font is unavailable
MS_FALLBACK = {"add": "plus", "check": "check", "search": "search", "more_vert": "more", "settings": "settings",
               "receipt_long": "receipt", "bar_chart": "chart", "savings": "wallet", "payments": "banknote",
               "restaurant": "utensils", "coffee": "coffee", "subway": "train", "bakery_dining": "utensils",
               "shopping_cart": "cart", "local_taxi": "car", "timer": "timer", "history": "history",
               "menu_book": "book", "edit_note": "pen", "mail": "mail", "description": "file-text",
               "folder": "folder", "star": "star", "play_arrow": "play", "flight": "briefcase",
               "lightbulb": "bulb", "restaurant_menu": "utensils", "push_pin": "pin"}


def ic(name, size=16, cls="", bar=""):
    """a Lucide icon; bar names it as something on a glass bar, which the frost check measures"""
    attr = f' data-bar="{bar}"' if bar else ""
    return (f'<svg class="ic {cls}"{attr} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{LUCIDE[name]}</svg>')


class Glyphs:
    """Material Symbols Rounded (weight 300, fill 0; 'fill' for the selected navigation item), or Lucide without the font"""
    msr = True
    used = set()

    @classmethod
    def ms(cls, name, extra="", size=24):
        cls.used.add(name)
        if cls.msr:
            return f'<i class="ms {extra}" style="font-size:{size}px;width:{size}px;height:{size}px">{name}</i>'
        return ic(MS_FALLBACK.get(name, "square"), size, extra)


def status_icon(kind):
    """Linear-style status circles, 16 px; a ledger draws only the exceptions"""
    if kind == "booked":  # the default state of a ledger row: nothing to say, keep the slot so titles align
        return '<span class="st-empty"></span>'
    if kind == "done":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="var(--c-success)"/>'
                '<path d="M5 8.2l2 2 4-4.3" stroke="var(--c-on-success)" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    if kind == "todo":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.25" fill="none" '
                'stroke="var(--c-text-3)" stroke-width="1.5"/></svg>')
    if kind == "backlog":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.25" fill="none" '
                'stroke="var(--c-text-3)" stroke-width="1.5" stroke-dasharray="2.2 2"/></svg>')
    if kind == "progress":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.25" fill="none" stroke="var(--c-warning)" stroke-width="1.5"/>'
                '<path d="M8 8V4a4 4 0 0 1 0 8z" fill="var(--c-warning)"/></svg>')
    if kind == "cancel":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="var(--c-text-3)"/>'
                '<path d="M5.6 5.6l4.8 4.8M10.4 5.6l-4.8 4.8" stroke="var(--c-bg)" stroke-width="1.6" stroke-linecap="round"/></svg>')
    return ""


def checkbox(on=True):
    if on:
        return ('<svg class="cb" width="16" height="16" viewBox="0 0 16 16"><rect x="1" y="1" width="14" height="14" rx="4" fill="var(--c-primary)"/>'
                '<path d="M4.6 8.2l2.2 2.2 4.6-4.8" stroke="var(--c-on-primary)" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return ('<svg class="cb" width="16" height="16" viewBox="0 0 16 16"><rect x="1.5" y="1.5" width="13" height="13" rx="3.5" '
            'fill="none" stroke="var(--c-border-strong)"/></svg>')


def kbd(*keys):
    """theme.css .kbd keys, 4 px apart"""
    return '<span class="kbds">' + "".join(f'<kbd class="kbd">{k}</kbd>' for k in keys) + "</span>"


def seq(*keys):
    """a G sequence: G 然后 I"""
    return '<span class="kbds">' + '<span class="kbd-then">然后</span>'.join(f'<kbd class="kbd">{k}</kbd>' for k in keys) + "</span>"


def money(v, dec=2):
    """one format everywhere: −¥32.00 / +¥18,500.00 (U+2212 minus)"""
    return ("+" if v > 0 else "−" if v < 0 else "") + "¥" + f"{abs(v):,.{dec}f}"


# ---------- app icon ----------
class AppIcon:
    """the icon PNGs from rian-app-icon (default appearance in light places, the dark variant in dark ones), drawn
    under the iOS mask; without --icon a neutral stand-in in the icon accent, labelled as such"""

    def __init__(self, light, dark, tones):
        self.given = bool(light)
        self.src = {}
        if light:
            self.src["light"] = self._png(light)
            self.src["dark"] = self._png(dark) if dark else self.src["light"]
        else:
            self.src["light"] = self.src["dark"] = self._stand_in(tones)

    @staticmethod
    def _png(path):
        return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()

    @staticmethod
    def _stand_in(tones):
        a, b = tones
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><defs>'
               f'<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#26282B"/><stop offset="1" stop-color="#191C1F"/></linearGradient>'
               f'<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>'
               f'<rect width="1024" height="1024" fill="url(#g)"/><circle cx="470" cy="560" r="230" fill="#E6E8EB"/>'
               f'<circle cx="720" cy="300" r="110" fill="url(#a)"/></svg>')
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

    def css(self):
        return "".join(f'.appicon.m-{m} {{ background-image: url("{s}"); }}\n' for m, s in self.src.items())

    def __call__(self, size, mode):
        return f'<i class="appicon m-{mode}" style="width:{size}px;height:{size}px;border-radius:{size * .2237:.2f}px"></i>'


# ---------- content ----------
def P(icon, ms, title, meta, right, sub="", void=False):
    """a phone row: Lucide icon (iOS), Material Symbol (Android), title, meta, trailing value and the line under it;
    void: refunded or cancelled (title and value struck through in text-3)"""
    return {"icon": icon, "ms": ms, "title": title, "meta": meta, "right": right, "sub": sub, "void": void}


def D(lead, status, title, note, tag, meta, time, value="", flag=""):
    """a desktop row; flag: cursor (keyboard cursor, surface-2), sel (multi-selected), void (struck through)"""
    return {"lead": lead, "status": status, "title": title, "note": note, "tag": tag, "meta": meta, "time": time,
            "value": value, "flag": flag}


def C(icon, label, keys, current=False):
    """a command menu item"""
    return {"icon": icon, "label": label, "keys": keys, "current": current}


EXPORT = "导出本月记录 CSV"  # one action, one name: command menu, context menu, shortcut sheet
SHORTCUTS = "快捷键速查"  # the ? sheet: the same name in the command menu's footer and wherever it is listed

# Each screen: phone and Android content (groups, newest first within a day), desktop content (the same records on the
# same days), the component strip's labels (strip) and the sample words of the type scale and swatches (sample:
# Chinese, then Latin and figures, then the swatch text).
SCREENS = {
    "list": {
        "label": "账本",
        "title": "明细", "sub": "2026年10月 · 128 笔",
        "tabs": [("list", "receipt_long", "明细"), ("chart", "bar_chart", "统计"), ("target", "savings", "预算"),
                 ("settings", "settings", "设置")],
        "new_prominent": True,
        "pills": ["全部", "餐饮", "交通", "购物", "收入"],
        "groups": [
            ("今天 · 10月16日 周五", "支出 ¥66.50", [
                P("coffee", "coffee", "咖啡", "Manner · 支付宝", money(-18), "14:05"),
                P("utensils", "restaurant", "午餐", "沙县小吃 · 招行信用卡", money(-32), "12:30"),
                P("banknote", "payments", "工资", "星河科技 · 招商银行", money(18500), "09:00"),
                P("train", "subway", "地铁", "2号线 · 交通卡", money(-4), "08:40"),
                P("utensils", "bakery_dining", "早餐", "全家 · 微信", money(-12.5), "08:12")]),
            ("昨天 · 10月15日 周四", "支出 ¥258.40", [
                P("car", "local_taxi", "打车", "滴滴 · 招行信用卡", money(-46), "22:47"),
                P("utensils", "restaurant", "晚餐", "外卖 · 微信", money(-28), "20:10"),
                P("cart", "shopping_cart", "超市", "盒马 · 支付宝", money(-126.4), "19:20"),
                P("phone", "receipt_long", "话费", "中国移动 · 支付宝", money(-58), "10:00")]),
            ("10月14日 周三", "支出 ¥415.30", [
                P("bag", "receipt_long", "退货", "优衣库 T恤 · 已退款", money(-99), "16:32", void=True),
                P("utensils", "restaurant", "午餐", "公司食堂 · 微信", money(-26), "12:05"),
                P("zap", "receipt_long", "电费", "国家电网 · 支付宝", money(-186.3), "11:18"),
                P("train", "subway", "地铁", "2号线 · 交通卡", money(-4), "08:41"),
                P("dumbbell", "receipt_long", "健身", "乐刻 · 招行信用卡", money(-199), "07:30")]),
            ("10月13日 周二", "支出 ¥3,591.70", [
                P("car", "local_taxi", "打车", "滴滴 · 微信", money(-23.5), "23:10"),
                P("cart", "shopping_cart", "超市", "盒马 · 支付宝", money(-68.2), "20:15"),
                P("home", "receipt_long", "房租", "自动扣款 · 招商银行", money(-3500), "09:00")]),
        ],
        "toast": f'已记一笔 · 午餐 <span class="num">{money(-32)}</span>',
        "strip": {"ok": "保存", "field": ("金额", '<span class="num">32.00</span>'),
                  "tags": ["餐饮", ("warning", "报销中"), ("info", "已对账")], "badges": ("已入账", "报销中", "同步失败"),
                  "danger": "删除这一条",
                  "menu": [("copy", "复制一条", ("⌘", "D")), ("tag", "改分类", ("L",)), ("wallet", "改账户", ("A",))]},
        "sample": ("记一笔", "Ledger 4,286.50", "午餐 −¥32.00"),
        "desktop": {
            "nav": [("inbox", "待确认", "3"), ("list", "明细", ""), ("chart", "统计", ""), ("target", "预算", "")],
            "current": 1,
            "sections": [("账户", [("card", "招商银行", "¥23,410"), ("card", "招行信用卡", "−¥2,184"),
                                   ("wallet", "支付宝", "¥1,208"), ("wallet", "微信零钱", "¥356")]),
                         ("标签", [("hash", "餐饮", "42"), ("hash", "交通", "26"), ("hash", "购物", "17"), ("hash", "居家", "9")])],
            "view": ("list", "明细"), "view_tabs": [("全部", "128"), ("支出", ""), ("收入", "")],
            "period": "2026年10月", "chips": [("card", "账户", "全部")],
            "sums": [("支出", "¥4,286.50"), ("收入", "¥18,500.00"), ("结余", "¥14,213.50")],
            "cols": {"meta": 76, "time": 36, "value": 96},
            "groups": [
                ("今天", "10月16日 周五", [money(-66.5), money(18500)], [
                    D("coffee", "booked", "咖啡", "Manner · 燕麦拿铁", "餐饮", "支付宝", "14:05", money(-18)),
                    D("utensils", "todo", "午餐", "沙县小吃 · 和同事 AA", "餐饮", "招行信用卡", "12:30", money(-32), "cursor"),
                    D("banknote", "booked", "工资", "星河科技 · 10月", "收入", "招商银行", "09:00", money(18500)),
                    D("train", "booked", "地铁", "2号线 · 静安寺 → 陆家嘴", "交通", "交通卡", "08:40", money(-4)),
                    D("utensils", "booked", "早餐", "全家 · 饭团和豆浆", "餐饮", "微信", "08:12", money(-12.5))]),
                ("昨天", "10月15日 周四", [money(-258.4)], [
                    D("car", "progress", "打车", "滴滴 · 加班回家，报销中", "交通", "招行信用卡", "22:47", money(-46)),
                    D("utensils", "booked", "晚餐", "外卖 · 黄焖鸡米饭", "餐饮", "微信", "20:10", money(-28), "sel"),
                    D("cart", "booked", "超市", "盒马 · 牛奶、鸡蛋、青菜", "购物", "支付宝", "19:20", money(-126.4), "sel"),
                    D("phone", "booked", "话费", "中国移动 · 10月套餐", "生活", "支付宝", "10:00", money(-58))]),
                ("10月14日", "周三", [money(-415.3)], [
                    D("bag", "cancel", "退货", "优衣库 T恤 · 已退款", "购物", "支付宝", "16:32", money(-99), "void"),
                    D("utensils", "booked", "午餐", "公司食堂 · 工作餐", "餐饮", "微信", "12:05", money(-26)),
                    D("zap", "booked", "电费", "国家电网 · 9月", "居家", "支付宝", "11:18", money(-186.3)),
                    D("train", "booked", "地铁", "2号线 · 静安寺 → 陆家嘴", "交通", "交通卡", "08:41", money(-4)),
                    D("dumbbell", "booked", "健身", "乐刻 · 月卡续费", "运动", "招行信用卡", "07:30", money(-199))]),
            ],
            "bulk": ("已选 <b class=\"num\">2</b> 条", [("tag", "改分类"), ("wallet", "改账户"), ("merge", "合并")]),
            # 「转到」and「最近」have no 记 in them, so the fuzzy match leaves 动作 and 帮助
            "cmdk": {"chip": "10月", "query": "记", "groups": [
                ("动作", [C("plus", "记一笔", kbd("C"), True), C("arrow-in", "记一笔收入", kbd("⇧", "C")),
                          C("file-down", EXPORT, kbd("⌘", "⇧", "E"))]),
                ("帮助", [C("help", "记账入门", "")])]},
            "mini": {"view": "明细", "link": "查看统计", "rows": [("utensils", "午餐", money(-32), False),
                                                              ("cart", "超市", money(-126.4), True),
                                                              ("banknote", "工资", money(18500), False)],
                     "foot": "10月 · 已用 71%", "pct": 71, "action": "记一笔"},
            "dialog": {"title": EXPORT, "body": "导出 2026年10月的 128 笔记录，包含分类、账户和备注。",
                       "field": "文件名", "value": "{app}-2026-10.csv", "ok": "导出"},
        },
    },
    "timer": {
        "label": "计时",
        "title": "专注", "sub": "10月16日 周五 · 已完成 2 次",
        "tabs": [("timer", "timer", "专注"), ("history", "history", "记录"), ("chart", "bar_chart", "统计"),
                 ("settings", "settings", "设置")],
        "new_prominent": False,  # the screen's one primary action is 开始专注
        "pills": ["全部", "论文", "写作", "工作", "阅读"],
        "groups": [
            ("接下来", "3 项 · 共 90 分钟", [
                P("book", "menu_book", "读论文", "论文 · 第 3 节", "50 分钟", "14:00"),
                P("pen", "edit_note", "写周报", "工作 · 本周进展", "25 分钟", "15:30"),
                P("mail", "mail", "回邮件", "工作 · 4 封待回", "15 分钟", "16:00")]),
            ("今天已完成", "2 次 · 75 分钟", [
                P("file-text", "description", "整理笔记", "论文 · 文献卡片 12 张", "25 分钟", "11:05"),
                P("book", "menu_book", "读书", "阅读 · 《深度工作》第 4 章", "50 分钟", "09:40")]),
            ("昨天", "4 次 · 2 小时 30 分", [
                P("book", "menu_book", "读论文", "论文 · 第 2 节", "50 分钟", "16:10"),
                P("pen", "edit_note", "改开题报告", "写作 · 第二稿", "50 分钟", "14:20"),
                P("mail", "mail", "回邮件", "工作 · 6 封", "25 分钟", "10:05"),
                P("book", "menu_book", "晨读", "阅读 · 《置身事内》", "25 分钟", "07:40")]),
            ("10月14日 周三", "3 次 · 1 小时 40 分", [
                P("book", "menu_book", "读论文", "论文 · 第 1 节", "50 分钟", "15:00"),
                P("file-text", "description", "整理文献", "论文 · 12 篇摘要", "25 分钟", "10:30"),
                P("mail", "mail", "回邮件", "工作 · 3 封", "25 分钟", "09:10")]),
        ],
        "toast": "已完成一次专注 · 整理笔记 25 分钟",
        "strip": {"ok": "创建", "field": ("任务名", "读论文"),
                  "tags": ["论文", ("warning", "进行中"), ("info", "已同步")], "badges": ("已完成", "进行中", "同步失败"),
                  "danger": "删除这次专注",
                  "menu": [("copy", "复制任务", ("⌘", "D")), ("folder", "改项目", ("P",)), ("clock", "改时长", ("T",))]},
        "sample": ("开始专注", "Focus 25:00", "专注 25 分钟"),
        "desktop": {
            "nav": [("sun", "今天", "7"), ("history", "专注记录", ""), ("chart", "统计", ""), ("target", "目标", "")],
            "current": 0,
            "sections": [("项目", [("book", "论文", "6"), ("pen", "写作", "3"), ("briefcase", "工作", "5"), ("book", "阅读", "2")])],
            "view": ("sun", "今天"), "view_tabs": [("全部", "7"), ("待开始", ""), ("已完成", "")],
            "period": "10月16日 周五", "chips": [("folder", "项目", "全部")],
            "sums": [("已专注", "1 小时 15 分"), ("目标", "3 小时"), ("还差", "1 小时 45 分")],
            "cols": {"meta": 72, "time": 36, "value": 64},
            "groups": [
                ("进行中", "", ["剩余 18 分钟"], [
                    D("book", "progress", "读论文", "Attention Is All You Need · 第 3 节", "论文", "2 / 3 个", "14:00", "50 分钟")]),
                ("待开始", "", ["共 90 分钟"], [
                    D("pen", "todo", "写周报", "本周进展和下周计划", "工作", "1 个", "15:30", "25 分钟", "cursor"),
                    D("mail", "todo", "回邮件", "4 封待回 · 先回导师", "工作", "1 个", "16:00", "15 分钟", "sel"),
                    D("chart", "todo", "改论文图表", "图 3 和图 4 重新配色", "论文", "2 个", "16:30", "50 分钟", "sel")]),
                ("已完成", "", ["共 75 分钟"], [
                    D("file-text", "done", "整理笔记", "文献卡片 12 张", "论文", "1 个", "11:05", "25 分钟"),
                    D("book", "done", "读书", "《深度工作》第 4 章", "阅读", "2 个", "09:40", "50 分钟"),
                    D("sun", "cancel", "晨间计划", "今天跳过", "工作", "—", "08:30", "15 分钟", "void")]),
            ],
            "bulk": ("已选 <b class=\"num\">2</b> 项", [("folder", "改项目"), ("clock", "改时长"), ("merge", "合并")]),
            "cmdk": {"chip": "今天", "query": "专注", "groups": [
                ("动作", [C("play", "开始专注", kbd("F"), True), C("plus", "新建专注任务", kbd("C")),
                          C("square", "结束本次专注", kbd("⌘", "."))]),
                ("转到", [C("history", "专注记录", seq("G", "R"))])]},
            "mini": {"view": "专注", "link": "查看统计", "rows": [("pen", "写周报", "25 分钟", False),
                                                            ("book", "读论文", "50 分钟", True),
                                                            ("mail", "回邮件", "15 分钟", False)],
                     "foot": "今日 2 / 4", "pct": 42, "action": "开始专注"},
            "dialog": {"title": "新建专注任务", "body": "任务会加到「待开始」，默认 1 个番茄（25 分钟）。",
                       "field": "任务名", "value": "改论文图表", "ok": "创建"},
        },
    },
    "notes": {
        "label": "笔记",
        "title": "笔记", "sub": "86 篇 · 已同步",
        "tabs": [("file-text", "description", "笔记"), ("folder", "folder", "文件夹"), ("star", "star", "收藏"),
                 ("settings", "settings", "设置")],
        "new_prominent": True,
        "trail": "meta",  # the trailing date is metadata, not an amount
        "pills": ["全部", "读书", "工作", "生活", "灵感"],
        "groups": [
            ("最近 7 天", "5 篇", [
                P("file-text", "description", "产品周会纪要", "下周三前确认首页改版的范围和排期", "昨天"),
                P("file-text", "description", "旅行清单", "护照、转换插头、充电宝、折叠伞", "10月12日"),
                P("file-text", "description", "周末菜单", "排骨汤、清炒时蔬、番茄炒蛋", "10月11日"),
                P("file-text", "description", "图标灵感", "界面图标的线宽和 app 图标保持一致", "10月10日"),
                P("file-text", "description", "健身计划", "周二、四、六力量训练，周日慢跑 5 公里", "10月9日")]),
            ("本月更早", "2 篇", [
                P("file-text", "description", "读书摘录", "好的设计是尽可能少的设计。", "10月3日"),
                P("file-text", "description", "国庆出行", "高铁 G7 次，10月1日 08:00 虹桥出发", "9月30日")]),
            ("9月", "23 篇", [
                P("file-text", "description", "番茄牛腩", "牛腩冷水下锅焯水，番茄分两次放", "9月28日"),
                P("file-text", "description", "租房备忘", "合同 11 月到期，提前一个月和房东确认", "9月20日"),
                P("file-text", "description", "播客笔记", "会员制的定价逻辑：先算留存，再定价格", "9月16日"),
                P("file-text", "description", "开学准备", "给侄子买的书包和文具清单", "9月5日")]),
        ],
        "toast": "已归档「旅行清单」",
        "strip": {"ok": "保存", "field": ("标题", "关于专注"),
                  "tags": ["读书", ("warning", "草稿"), ("info", "已共享")], "badges": ("已保存", "有冲突", "同步失败"),
                  "danger": "删除这篇笔记",
                  "menu": [("copy", "复制一篇", ("⌘", "D")), ("folder", "移到文件夹", ("M",)), ("tag", "加标签", ("L",))]},
        "sample": ("关于专注", "Notes 41,280", "笔记 386 字"),
        "desktop": {
            "nav": [("file-text", "全部笔记", "86"), ("pin", "置顶", "3"), ("clock", "最近", ""), ("archive", "归档", "12")],
            "current": 0,
            "sections": [("文件夹", [("folder", "读书", "24"), ("folder", "工作", "31"), ("folder", "生活", "18"), ("folder", "灵感", "13")])],
            "view": ("file-text", "全部笔记"), "view_tabs": [("全部", "86"), ("置顶", ""), ("本周", "")],
            "period": "", "chips": [("clock", "排序", "按修改时间"), ("folder", "文件夹", "全部")],
            "sums": [("本周新增", "7 篇"), ("共", "41,280 字")],
            "cols": {"meta": 64, "time": 64, "value": 0},
            "groups": [
                ("置顶", "", ["2 篇"], [
                    D("pin", "", "关于专注", "真正消耗精力的不是工作本身，而是在几件事之间来回切换", "读书", "386 字", "10月14日"),
                    D("pin", "", "年度目标", "今年读完 24 本书，跑一次半程马拉松", "生活", "1,204 字", "1月2日", "", "cursor")]),
                ("最近 7 天", "", ["5 篇"], [
                    D("file-text", "", "产品周会纪要", "下周三前确认首页改版的范围和排期", "工作", "642 字", "昨天"),
                    D("file-text", "", "旅行清单", "护照、转换插头、充电宝、折叠伞", "生活", "128 字", "10月12日", "", "sel"),
                    D("file-text", "", "图标灵感", "界面图标的线宽和 app 图标保持一致", "灵感", "96 字", "10月10日", "", "sel")]),
                ("更早", "", ["78 篇"], [
                    D("file-text", "", "读书摘录", "好的设计是尽可能少的设计。", "读书", "210 字", "10月3日"),
                    D("file-text", "", "番茄牛腩", "牛腩冷水下锅焯水，番茄分两次放", "生活", "356 字", "9月28日"),
                    D("file-text", "", "租房备忘", "合同 11 月到期，提前一个月和房东确认", "生活", "88 字", "9月20日")]),
            ],
            "bulk": ("已选 <b class=\"num\">2</b> 篇", [("folder", "移到文件夹"), ("tag", "加标签"), ("archive", "归档")]),
            "cmdk": {"chip": "全部笔记", "query": "归档", "groups": [
                ("动作", [C("archive", "归档选中的笔记", kbd("E"), True), C("history", "撤销归档", kbd("⌘", "Z"))]),
                ("转到", [C("archive", "归档", seq("G", "A"))])]},
            "mini": {"view": "全部笔记", "link": "查看归档", "rows": [("pin", "关于专注", "10月14日", False),
                                                               ("file-text", "旅行清单", "10月12日", True),
                                                               ("file-text", "图标灵感", "10月10日", False)],
                     "foot": "86 篇", "pct": 0, "action": "新建笔记"},
            "dialog": {"title": "移到文件夹", "body": "把选中的 2 篇笔记移到另一个文件夹，原文件夹里不再显示。",
                       "field": "文件夹", "value": "生活", "ok": "移动"},
        },
    },
}


# ---------- phone (iOS 26) ----------
STATUS_BAR = """<div class="sbar"><b class="num">9:41</b><span class="glyphs">
  <svg width="18" height="12" viewBox="0 0 18 12"><rect x="0" y="8" width="3" height="4" rx="1" fill="currentColor"/><rect x="5" y="5.5" width="3" height="6.5" rx="1" fill="currentColor"/><rect x="10" y="3" width="3" height="9" rx="1" fill="currentColor"/><rect x="15" y="0" width="3" height="12" rx="1" fill="currentColor"/></svg>
  <svg width="16" height="12" viewBox="0 0 16 12"><path d="M8 2.2c2.3 0 4.4.9 6 2.4l1.1-1.2A10.3 10.3 0 0 0 8 .6C5.3.6 2.8 1.6.9 3.4L2 4.6c1.6-1.5 3.7-2.4 6-2.4zm0 3.4c1.4 0 2.6.5 3.6 1.4l1.1-1.2A7 7 0 0 0 8 4c-1.8 0-3.4.7-4.7 1.8l1.1 1.2c1-.9 2.2-1.4 3.6-1.4zM8 9a1.6 1.6 0 1 0 0 3.2A1.6 1.6 0 0 0 8 9z" fill="currentColor"/></svg>
  <svg width="27" height="13" viewBox="0 0 27 13"><rect x=".5" y=".5" width="23" height="12" rx="3.8" fill="none" stroke="currentColor" opacity=".4"/><rect x="2" y="2" width="18" height="9" rx="2.5" fill="currentColor"/><path d="M25 4.5v4c.8-.3 1.3-1.1 1.3-2s-.5-1.7-1.3-2z" fill="currentColor" opacity=".45"/></svg>
</span></div><div class="island"></div>"""


def seg_bar(pct, cls="mbar"):
    """used | 2 px gap | remaining: the icon's cut, echoed once in the UI"""
    return f'<div class="{cls}"><i class="used" style="width:calc({pct}% - 1px)"></i><i class="rest"></i></div>'


def hero_ios(name):
    if name == "list":
        return f'''<div class="mcard">
      <div class="mrow t-row-meta"><span>10月支出</span><span class="t3">预算 <span class="num">¥6,000</span></span></div>
      <div class="mbig num">¥4,286.50</div>{seg_bar(71.4)}
      <div class="mrow t-row-meta"><span>剩余 <span class="num">¥1,713.50</span> · 还有 15 天</span><span class="num">71%</span></div></div>'''
    if name == "timer":
        return f'''<div class="mcard">
      <div class="mrow t-row-meta"><span>今日专注</span><span class="t3">目标 3 小时</span></div>
      <div class="mbig num">1 小时 15 分</div>{seg_bar(42)}
      <div class="mrow t-row-meta"><span>还差 105 分钟 · 下一个：读论文</span><span class="num">42%</span></div>
      <span class="mbtn pri">{ic("play", 18)}开始专注</span></div>'''
    # notes: the iOS search field, then a pinned note with long Chinese text and a highlight
    return f'''<div class="search t-long-text">{ic("search", 18)}<span>搜索笔记</span></div>
    <article class="ncard">
      <div class="t-card-title">关于专注</div>
      <div class="t-row-meta t2">{ic("pin", 13)}置顶 · 10月14日 · 386 字</div>
      <p class="t-long-text long">这周把讲专注的那一章又读了一遍。作者说，真正消耗精力的不是工作本身，而是在几件事之间来回切换：每切换一次，都要花时间重新找回刚才的思路。</p>
      <p class="t-long-text long">所以我打算试一个简单的办法：<mark>每天上午只做一件最重要的事</mark>，消息和邮件留到下午统一处理。先坚持两周，再回来看看效果。</p>
      <div class="tags"><span class="tagp">读书</span><span class="tagp"><i class="pdot" style="background:var(--c-info)"></i>已同步</span></div>
    </article>'''


def ios_phone(name, scr, mode, icon, scrolled=False, toast=False, pid="", caption=""):
    body = ""
    for head, total, rows in scr["groups"]:
        body += f'<div class="psh t-section-header"><span>{head}</span><span class="num">{total}</span></div><div class="plist">'
        for r in rows:
            cls = " in" if r["right"].startswith("+") else ""
            trail = ("t-row-meta t3" if scr.get("trail") == "meta" else "t-amount") + " num" + cls
            body += (f'<div class="prow{" void" if r["void"] else ""}">{ic(r["icon"], 20, "picon")}<span class="pt"><b class="t-row-title">{r["title"]}</b>'
                     f'<span class="t-row-meta">{r["meta"]}</span></span><span class="pa"><b class="{trail}">{r["right"]}</b>'
                     f'<span class="t-row-meta num">{r["sub"]}</span></span></div>')
        body += "</div>"
    pills = "".join(f'<span class="ppill t-row-title{" on" if i == 0 else ""}">{p}</span>' for i, p in enumerate(scr["pills"]))
    tabs = "".join(f'<span class="tab{" on" if i == 0 else ""}">{ic(lu, 24, bar=lab + " 图标")}<b data-bar="{lab}">{lab}</b></span>'
                   for i, (lu, _ms, lab) in enumerate(scr["tabs"]))
    new_btn = (f'<span class="gbtn prom">{ic("plus", 22)}</span>' if scr["new_prominent"]
               else f'<span class="gbtn frost floating">{ic("plus", 22, bar="新建图标")}</span>')
    toast_html = (f'<div class="ptoast">{status_icon("done")}<span class="t-row-meta">{scr["toast"]}</span>'
                  f'<span class="undo t-row-title">撤销</span></div>') if toast else ""
    inline = f'<div class="inline t-card-title">{scr["title"]}</div>' if scrolled else ""
    edge_top = '<div class="edge-top"></div>' if scrolled else ""
    return f'''
<div class="phone" id="{pid}" data-theme="{mode}"><div class="frame"><div class="screen" data-region="phone">
  <div class="pc"{' data-scroll="psh"' if scrolled else ""}>
    <div class="ltitle t-page-title">{scr["title"]}</div><div class="lsub t-row-meta">{scr["sub"]}</div>
    {hero_ios(name)}
    <div class="pills">{pills}</div>
    {body}
  </div>
  {edge_top}{STATUS_BAR}
  <div class="plead">{icon(32, mode)}</div>{inline}
  <div class="ptb"><span class="gbtn frost floating">{ic("filter", 20, bar="筛选图标")}</span>{new_btn}</div>
  <div class="edge"></div>
  {toast_html}
  <nav class="tabbar frost floating">{tabs}</nav>
  <span class="stab frost floating">{ic("search", 24, bar="搜索图标")}</span>
  <i class="home"></i>
</div></div>{f'<div class="cap">{caption}</div>' if caption else ""}</div>'''


# ---------- Android (Material 3, Pixel 412 x 915 dp) ----------
def hero_android(name):
    if name == "list":
        return f'''<div class="acard"><div class="arow2 m3-bodyMedium"><span>10月支出</span><span class="t3">预算 ¥6,000</span></div>
      <div class="abig m3-headlineSmall num">¥4,286.50</div>{seg_bar(71.4)}
      <div class="arow2 m3-bodyMedium"><span>剩余 ¥1,713.50 · 还有 15 天</span><span class="num">71%</span></div></div>'''
    if name == "timer":
        return f'''<div class="acard"><div class="arow2 m3-bodyMedium"><span>今日专注</span><span class="t3">目标 3 小时</span></div>
      <div class="abig m3-headlineSmall num">1 小时 15 分</div>{seg_bar(42)}
      <div class="arow2 m3-bodyMedium"><span>还差 105 分钟 · 下一个：读论文</span><span class="num">42%</span></div></div>'''
    return f'''<div class="asearch m3-bodyLarge">{Glyphs.ms("search")}<span>搜索笔记</span></div>
    <div class="acard"><div class="m3-titleMedium">关于专注</div><div class="m3-bodyMedium t2">置顶 · 10月14日 · 386 字</div>
      <p class="m3-bodyLarge along">作者说，真正消耗精力的不是工作本身，而是在几件事之间来回切换。所以我打算：<mark>每天上午只做一件最重要的事</mark>。</p></div>'''


def android(name, scr, mode, caption=""):
    chips = "".join(f'<span class="achip m3-labelLarge{" on" if i == 0 else ""}">{Glyphs.ms("check", size=18) if i == 0 else ""}{p}</span>'
                    for i, p in enumerate(scr["pills"]))
    body = ""
    for head, total, rows in scr["groups"]:
        body += f'<div class="ash m3-titleSmall"><span>{head}</span><span class="num">{total}</span></div>'
        for r in rows:
            cls = " in" if r["right"].startswith("+") else ""
            trail = ("m3-labelSmall t3" if scr.get("trail") == "meta" else "m3-bodyLarge") + " num" + cls
            body += (f'<div class="arow{" void" if r["void"] else ""}">{Glyphs.ms(r["ms"], "lead")}<span class="at"><b class="m3-bodyLarge">{r["title"]}</b>'
                     f'<span class="m3-bodyMedium">{r["meta"]}</span></span><span class="aa"><b class="{trail}">{r["right"]}</b>'
                     f'<span class="m3-labelSmall num">{r["sub"]}</span></span></div>')
    nav = "".join(f'<span class="anv{" on" if i == 0 else ""}"><span class="aind">{Glyphs.ms(ms, "fill" if i == 0 else "")}</span>'
                  f'<b class="m3-labelMedium">{lab}</b></span>' for i, (_lu, ms, lab) in enumerate(scr["tabs"]))
    fab = (f'<span class="afab ext m3-labelLarge">{Glyphs.ms("play_arrow")}开始专注</span>' if name == "timer"
           else f'<span class="afab">{Glyphs.ms("add")}</span>')
    return f'''
<div class="android" data-theme="{mode}"><div class="aframe"><div class="ascreen" data-region="android">
  <div class="asb"><b class="num">9:41</b><span class="grow"></span><span class="aglyphs">
    <svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 13.5 1 6.2a10 10 0 0 1 14 0z" fill="currentColor"/></svg>
    <svg width="16" height="16" viewBox="0 0 16 16"><path d="M15 2v12H3z" fill="currentColor"/></svg>
    <svg width="10" height="16" viewBox="0 0 10 16"><rect x="3" y="0" width="4" height="2" rx=".5" fill="currentColor"/><rect x="0.5" y="1.5" width="9" height="14" rx="2" fill="currentColor"/></svg>
  </span><i class="punch"></i></div>
  <div class="acontent" data-scroll="achips">{hero_android(name)}<div class="achips">{chips}</div>{body}</div>
  <header class="atop"><span class="atitle m3-titleLarge">{scr["title"]}</span><span class="grow"></span>
    <span class="aib">{Glyphs.ms("search")}</span><span class="aib">{Glyphs.ms("more_vert")}</span></header>
  {fab}
  <nav class="anav">{nav}</nav>
  <i class="ahandle"></i>
</div></div>{f'<div class="cap">{caption}</div>' if caption else ""}</div>'''


# ---------- desktop window ----------
def highlight(label, q):
    """matched characters 590 + text, the rest text-2"""
    return label.replace(q, f"<em>{q}</em>") if q else label


def desktop(name, scr, mode, icon, app):
    d = scr["desktop"]
    cols = d["cols"]
    rows = []
    for title, sub, sums, items in d["groups"]:
        right = "".join(f'<span class="num">{s}</span>' for s in sums)
        rows.append(f'<div class="gh">{ic("chev-down", 12, "t3")}<b>{title}</b><span class="t3">{sub}</span>'
                    f'<span class="t3 num">{len(items)}</span><span class="grow"></span><span class="gh-sum">{right}</span>'
                    f'<span class="ib sm">{ic("plus", 16)}</span></div>')
        for r in items:
            flag = r["flag"]
            lead = checkbox() if flag == "sel" else ic(r["lead"], 16, "t3")
            val_cls = " in" if r["value"].startswith("+") else ""
            st = status_icon(r["status"]) if r["status"] else ""
            rows.append(
                f'<div class="r{" " + flag if flag else ""}"><span class="lead">{lead}</span>{st}<b class="tt">{r["title"]}</b>'
                f'<span class="note">{r["note"]}</span><span class="grow"></span><span class="pill">{r["tag"]}</span>'
                + (f'<span class="meta" style="width:{cols["meta"]}px">{r["meta"]}</span>' if cols["meta"] else "")
                + (f'<span class="tm num" style="width:{cols["time"]}px">{r["time"]}</span>' if cols["time"] else "")
                + (f'<span class="val num{val_cls}" style="width:{cols["value"]}px">{r["value"]}</span>' if cols["value"] else "")
                + "</div>")
    nav = "".join(f'<div class="si{" on" if i == d["current"] else ""}">{ic(i_, 16)}<span>{t}</span><span class="grow"></span>'
                  f'<span class="cnt num">{c}</span></div>' for i, (i_, t, c) in enumerate(d["nav"]))
    secs = "".join(f'<div class="sec">{s} {ic("chev-down", 12)}</div><div class="nav">'
                   + "".join(f'<div class="si">{ic(i_, 16)}<span>{t}</span><span class="grow"></span><span class="cnt num">{c}</span></div>'
                             for i_, t, c in items) + "</div>" for s, items in d["sections"])
    count = lambda n: f' <span class="num t3">{n}</span>' if n else ""
    vtabs = "".join(f'<span class="fp{" on" if i == 0 else ""}">{t}{count(n)}</span>' for i, (t, n) in enumerate(d["view_tabs"]))
    period = (f'<span class="ib sm">{ic("chev-left", 16)}</span><b class="month">{d["period"]}</b>'
              f'<span class="ib sm">{ic("chev-right", 16)}</span>') if d["period"] else ""
    chips = "".join(f'<span class="chip">{ic(i_, 14)}{k} <span class="t3">是</span> {v}</span>' for i_, k, v in d["chips"])
    sums = "".join(f'<span class="sum">{k} <b class="num">{v}</b></span>' for k, v in d["sums"])
    lead, acts = d["bulk"]
    bulk = "".join(f'<span class="bb">{ic(i_, 16)}{t}</span>' for i_, t in acts)
    q = d["cmdk"]["query"]
    res = ""
    for g, items in d["cmdk"]["groups"]:
        res += f'<div class="cg">{g}</div>'
        for it in items:
            res += (f'<div class="ci{" cur" if it["current"] else ""}{" hl" if q else ""}">{ic(it["icon"], 16)}'
                    f'<span class="lab">{highlight(it["label"], q)}</span><span class="grow"></span>{it["keys"]}</div>')
    inp = (f'<span class="q">{q}</span><span class="caret"></span>' if q
           else '<span class="caret"></span><span class="ph">输入命令或搜索…</span>')
    return f'''
<div class="win" data-theme="{mode}" data-region="desktop">
  <aside class="side">
    <div class="tl"><i></i><i></i><i></i></div>
    <div class="ws"><span class="ws-name">{icon(20, mode)}<b>{app}</b>{ic("chev-down", 12, "t3")}</span><span class="grow"></span>
      <span class="ib">{ic("search", 16)}</span><span class="ib">{ic("pen", 16)}</span></div>
    <div class="nav">{nav}</div>{secs}
    <div class="grow"></div>
    <div class="sync"><i class="dot"></i><span>已同步 · 刚刚</span><span class="grow"></span><span class="ib">{ic("help", 16)}</span></div>
  </aside>
  <main class="main">
    <header class="vh">
      <span class="crumb">{ic(d["view"][0], 16, "t3")}<b>{d["view"][1]}</b></span><span class="tabs-v">{vtabs}</span>
      <span class="grow"></span>
      <span class="btn ghost">{ic("filter", 16)}筛选</span><span class="btn sec2">{ic("sliders", 16)}显示</span>
    </header>
    <div class="fb">{period}{chips}<span class="chip dashed">{ic("plus", 14)}筛选</span><span class="grow"></span>{sums}</div>
    <div class="list">{"".join(rows)}</div>
    <div class="bulk"><span class="n">{lead}</span><i class="vr"></i>{bulk}
      <span class="bb danger">{ic("trash", 16)}删除<kbd class="kbd">⌫</kbd></span><i class="vr"></i><span class="bb">{ic("x", 16)}<kbd class="kbd">Esc</kbd></span></div>
  </main>
  <div class="scrim"></div>
  <div class="cmdk">
    <div class="ctx"><span class="cchip">{icon(14, mode)}{app} · {d["cmdk"]["chip"]}</span></div>
    <div class="inp">{inp}</div>
    <div class="res">{res}</div>
    <div class="cf"><span>{kbd("↑", "↓")} 选择</span><span>{kbd("↵")} 执行</span><span>{kbd("esc")} 关闭</span>
      <span class="grow"></span><span>{kbd("?")} {SHORTCUTS}</span></div>
  </div>
</div>'''


# ---------- component strip, dialog, icon x UI, type scale ----------
def components(mode, scr):
    """the components at desktop sizes, one column per mode, labelled with the screen's own words"""
    s = scr["strip"]
    tags = "".join(f'<span class="pill">{t}</span>' if isinstance(t, str) else
                   f'<span class="pill"><i class="pdot" style="background:var(--c-{t[0]})"></i>{t[1]}</span>' for t in s["tags"])
    done = status_icon("done").replace("var(--c-success)", "currentColor").replace("var(--c-on-success)", "var(--c-success-container)")
    ok, warn, bad = s["badges"]
    menu = "".join(f'<div class="mi{" cur" if i == 1 else ""}">{ic(icon, 16)}{label}<span class="grow"></span>{kbd(*keys)}</div>'
                   for i, (icon, label, keys) in enumerate(s["menu"]))
    rows = [
        ("主按钮 · 默认 / 悬停 / 按下", f'<span class="b pri">{s["ok"]}<span class="kbds"><kbd class="kbd on-pri">⌘</kbd><kbd class="kbd on-pri">↵</kbd></span></span>'
                                    '<span class="b pri hov">悬停</span><span class="b pri prs">按下</span>'),
        ("次按钮 · 幽灵按钮 · 悬停", f'<span class="b second">取消</span><span class="b ghost">{ic("filter", 16)}筛选</span>'
                                  f'<span class="b ghost hov">{ic("sliders", 16)}显示</span><span class="ib2">{ic("pen", 16)}</span>'),
        ("危险操作", f'<span class="b second danger">{ic("trash", 16)}{s["danger"]}</span>'),
        ("输入框 · 聚焦态", f'<span class="fin">{s["field"][0]}</span><span class="fin focus">{s["field"][1]}<span class="icaret"></span></span>'),
        ("标签", tags),
        ("状态徽章", f'<span class="badge success">{done}{ok}</span><span class="badge warning">{warn}</span>'
                    f'<span class="badge danger">{bad}</span>'),
        ("kbd", kbd("⌘", "K") + seq("G", "I") + kbd("Esc")),
        ("复选框 · 开关", checkbox(True) + checkbox(False) + '<span class="tg on"></span><span class="tg"></span>'),
        ("菜单（当前项 menu-active）", f'<div class="mm">{menu}<i class="msep"></i>'
                                    f'<div class="mi danger">{ic("trash", 16)}删除<span class="grow"></span>{kbd("⌫")}</div></div>'),
    ]
    return (f'<div class="cs" data-theme="{mode}"><div class="cs-h">{MODE_NAME[mode]}</div>'
            + "".join(f'<div class="crow"><span class="clab">{k}</span><span class="cval">{v}</span></div>' for k, v in rows)
            + "</div>")


def dialog(scr, mode, app):
    g = scr["desktop"]["dialog"]
    value = g["value"].replace("{app}", app)
    return f'''<div class="dlg-stage" data-theme="{mode}"><div class="dlg">
  <div class="td-title-2">{g["title"]}</div><p class="dlg-body">{g["body"]}</p>
  <label class="dlg-field"><span>{g["field"]}</span><span class="fin focus wide">{value}<span class="icaret"></span></span></label>
  <div class="dlg-act"><span class="b second">取消<kbd class="kbd">Esc</kbd></span>
    <span class="b pri">{g["ok"]}<span class="kbds"><kbd class="kbd on-pri">⌘</kbd><kbd class="kbd on-pri">↵</kbd></span></span></div>
</div></div>'''


def mini(scr, mode, icon, app):
    """the warm icon on its blue UI: the top of the sidebar plus a corner of the main view"""
    d = scr["desktop"]
    m = d["mini"]
    nav = "".join(f'<div class="si{" on" if i == d["current"] else ""}">{ic(i_, 16)}<span>{t}</span></div>'
                  for i, (i_, t, _c) in enumerate(d["nav"][:3]))
    rows = "".join(f'<div class="mr{" sel" if s else ""}"><span class="lead">{checkbox(True) if s else ic(i_, 16, "t3")}</span>'
                   f'<b>{t}</b><span class="grow"></span><span class="t3 num">{v}</span></div>' for i_, t, v, s in m["rows"])
    prog = seg_bar(m["pct"], "mprog") if m["pct"] else '<span class="grow"></span>'
    return f'''<div class="mini" data-theme="{mode}">
  <aside class="msb"><div class="ws"><span class="ws-name">{icon(20, mode)}<b>{app}</b>{ic("chev-down", 12, "t3")}</span>
    <span class="grow"></span><span class="ib">{ic("pen", 16)}</span></div><div class="nav">{nav}</div></aside>
  <div class="mmain"><div class="mvh"><b>{m["view"]}</b><span class="grow"></span><a class="lnk">{m["link"]}</a></div>{rows}
    <div class="mfoot"><span class="t3 num">{m["foot"]}</span>{prog}<span class="b pri sm">{m["action"]}</span></div></div>
</div>'''


def type_scale(t, mode, scr):
    """the desktop scale; the Latin and figures are marked lang="en" so they keep Inter's tracking on a Chinese page"""
    zh, latin, _ = scr["sample"]
    rows = ""
    for k, v in t["font"]["web"]["scale"].items():
        rows += (f'<div class="ty"><span class="ty-k">{k}<small>{v["size"]} / {v["line"]} · {v["weight"]}</small></span>'
                 f'<span class="td-{k} ty-s">{zh} <span lang="en">{latin}</span></span></div>')
    return f'<div class="tyb" data-theme="{mode}">{rows}</div>'


# ---------- swatches ----------
def alpha_label(c):
    """'rgba(255, 255, 255, 0.07)' -> '白 7 %'"""
    r, g, b, a = (float(v) for v in re.findall(r"[\d.]+", c))
    base = {(255, 255, 255): "白", (0, 0, 0): "黑"}.get((r, g, b), "#%02X%02X%02X" % (int(r), int(g), int(b)))
    return f"{base} {a * 100:g} %"


def swatches(t, scr):
    sample = scr["sample"][2]
    out = ""
    for k in SCHEMES:
        C, lv = t["color"][k], t["levels"][k]
        level = "high" if k.endswith("-hc") else "standard"
        B = backgrounds(C)
        low = lambda fg: min(contrast(C[fg], B[c]) for c in COLUMNS)
        chips = ""
        for n in ("canvas", "bg", "surface", "surface-2", "surface-3", "elevated", "menu-active", "border", "border-strong"):
            L = f"L {lv[n]:g} · " if n in lv else ""
            fill = over(C[n], C["bg"]) if C[n].startswith("rgba") else C[n]
            val = C[n] if not C[n].startswith("rgba") else alpha_label(C[n])
            chips += f'<div class="sw"><i style="background:{fill}"></i><b>{n}</b><span>{L}{val}</span></div>'
        texts = ""
        for n in list(TIERS) + ["primary-text"]:
            need = NEED[level][n if n in TIERS else "accent"][0]
            m = low(n)
            texts += (f'<div class="tx"><b style="color:{C[n]}">Aa {sample}</b><span style="color:{C["text-3"]}">{n} · L {lv[n]:g} · {C[n]}</span>'
                      f'<span class="ok" style="color:{C["text-2"]}">{m:.1f} ≥ {need:g}</span></div>')
        acc = ""
        for n in ("primary", "primary-hover", "primary-pressed", "selected", "focus", "selection"):
            acc += f'<div class="sw"><i style="background:{C[n]}"></i><b>{n}</b><span>{C[n]}</span></div>'
        stat = ""
        for s in STATUS:
            m = low(s)
            stat += (f'<span class="sbadge" style="background:{C[s + "-container"]};color:{C[s]}">{s} {m:.1f}</span>')
        frost = (f'<div class="fz"><i class="fz-stripes"></i><span style="background:{C["frost"]};box-shadow:inset 0 1px 0 {C["frost-highlight"]},'
                 f' inset 0 0 0 1px {C["frost-border"]};color:{C["text"]}">frost · {alpha_label(C["frost"])}</span></div>')
        out += (f'<div class="spanel" style="background:{C["bg"]};color:{C["text"]};border-color:{over(C["border"], C["bg"])}">'
                f'<h4>{SCHEME_NAME[k]} <span style="color:{C["text-3"]}">{k}</span></h4><div class="sws">{chips}</div>'
                f'<div class="txs">{texts}</div><div class="sws">{acc}</div><div class="stats">{stat}</div>{frost}</div>')
    return out


# ---------- CSS ----------
CSS = r"""
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #E3E5E8; font-family: var(--font); font-feature-settings: "cv01", "ss03"; color: #1B1C1D;
  -webkit-font-smoothing: antialiased; }
.grow { flex: 1; min-width: 0; }
.ic { flex: none; display: block; }
.ic * { vector-effect: non-scaling-stroke; }
.t2 { color: var(--c-text-2); }
.t3 { color: var(--c-text-3); }
.appicon { display: block; flex: none; background-size: cover; background-position: center; }
.kbds { display: inline-flex; align-items: center; }
kbd.on-pri { background: rgba(255,255,255,.16); border-color: rgba(255,255,255,.14); color: var(--c-on-primary); }

.board { width: @@W@@px; padding: 36px 40px 44px; display: grid; grid-template-columns: 410px 410px 432px 556px;
  column-gap: 24px; row-gap: 32px; align-items: start; }
.bhead { grid-column: 1 / -1; display: flex; align-items: center; gap: 16px; }
.bhead h1 { font: 590 24px/32px var(--font); letter-spacing: -.0195em; }
.bhead p { font: 400 14px/20px var(--font); color: #55575A; }
.bhead p b { color: #1B1C1D; font-weight: 590; }
.cap { margin-top: 12px; font: 510 13px/18px var(--font); color: #55575A; padding-left: 4px; }
.cap b { color: #1B1C1D; font-weight: 590; }
.desk { grid-column: 1 / 4; }
.rcol { grid-column: 4; display: flex; flex-direction: column; gap: 24px; }
.panel { background: #FFFFFF; border-radius: 12px; box-shadow: 0 0 0 1px rgba(0,0,0,.08); padding: 18px 20px 20px;
  display: flex; flex-direction: column; gap: 12px; }
.panel h3 { font: 590 15px/20px var(--font); color: #1B1C1D; }
.panel .note2 { font: 400 12px/17px var(--font); color: #55575A; }
.palette { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
.measure { padding: 0 40px 40px; } /* below the sheet: measured, never in preview.png */

/* ---------- desktop window ---------- */
.win { position: relative; width: 1280px; height: 800px; border-radius: 12px; overflow: hidden; background: var(--c-canvas);
  color: var(--c-text); font: var(--td-small); display: flex; box-shadow: 0 0 0 1px rgba(0,0,0,.18), 0 24px 64px rgba(15,17,21,.22); }
.win[data-theme="light"] { box-shadow: 0 0 0 1px rgba(0,0,0,.10), 0 24px 64px rgba(15,17,21,.14); }
.side { width: var(--sidebar-w); flex: none; display: flex; flex-direction: column; padding: 0 8px 8px; }
.tl { height: 40px; display: flex; gap: 8px; align-items: center; padding-left: 8px; }
.tl i { width: 12px; height: 12px; border-radius: 50%; background: var(--c-surface-3); box-shadow: inset 0 0 0 1px var(--c-border); }
.ws { height: 44px; display: flex; align-items: center; gap: 2px; margin-top: -4px; }
.ws-name { display: flex; align-items: center; gap: 8px; height: 28px; padding: 0 6px; border-radius: var(--r-sm); }
.ws-name b { font-weight: 590; }
.ib { width: 28px; height: 28px; display: grid; place-items: center; border-radius: var(--r-sm); color: var(--c-text-3); flex: none; }
.ib.sm { width: 24px; height: 24px; }
.nav { display: flex; flex-direction: column; gap: 1px; margin-top: 2px; }
.si { height: var(--sidebar-item-h); display: flex; align-items: center; gap: 8px; padding: 0 8px; border-radius: var(--r-sm);
  color: var(--c-text-2); font-weight: 510; }
.si .ic { color: var(--c-text-3); }
.si.on { background: var(--c-surface-2); color: var(--c-text); }
.si.on .ic { color: var(--c-text-2); }
.cnt { font: var(--td-caption); color: var(--c-text-3); }
.sec { display: flex; align-items: center; gap: 4px; height: 28px; padding: 0 8px; margin-top: 14px; font: var(--td-caption); color: var(--c-text-3); }
.sync { height: 32px; display: flex; align-items: center; gap: 8px; padding: 0 0 0 8px; font: var(--td-caption); color: var(--c-text-3); }
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--c-success); }
.main { position: absolute; left: var(--sidebar-w); top: 8px; right: 8px; bottom: 8px; background: var(--c-bg); border: 1px solid var(--c-border);
  border-radius: var(--r-md); overflow: hidden; display: flex; flex-direction: column; }
.vh { height: var(--view-header-h); flex: none; display: flex; align-items: center; gap: 8px; padding: 0 10px 0 16px; border-bottom: 1px solid var(--c-border); }
.crumb { display: flex; align-items: center; gap: 8px; margin-right: 8px; }
.crumb b { font-weight: 510; }
.tabs-v { display: flex; gap: 4px; }
.fp { height: var(--control-h-sm); padding: 0 10px; display: inline-flex; align-items: center; gap: 6px; border-radius: var(--r-full);
  border: 1px solid var(--c-border); font: var(--td-caption); color: var(--c-text-2); }
.fp.on { background: var(--c-surface-3); color: var(--c-text); border-color: transparent; }
.btn { height: var(--control-h-md); padding: 0 10px; display: inline-flex; align-items: center; gap: 6px; border-radius: var(--r-sm);
  font-weight: 510; color: var(--c-text-2); }
.btn .ic { color: var(--c-text-3); }
.btn.sec2 { background: var(--c-surface-2); border: 1px solid var(--c-border); color: var(--c-text); }
.fb { height: var(--filter-bar-h); flex: none; display: flex; align-items: center; gap: 6px; padding: 0 16px 0 10px; border-bottom: 1px solid var(--c-border); }
.month { font-weight: 510; padding: 0 2px; margin-right: 6px; }
.chip { height: var(--control-h-sm); display: inline-flex; align-items: center; gap: 6px; padding: 0 8px; border-radius: var(--r-sm);
  border: 1px solid var(--c-border); font: var(--td-caption); color: var(--c-text-2); }
.fb > .chip:first-child { margin-left: 6px; }
.chip .ic { color: var(--c-text-3); }
.chip.dashed { border-style: dashed; color: var(--c-text-3); }
.sum { font: var(--td-caption); color: var(--c-text-3); margin-left: 16px; }
.sum b { color: var(--c-text-2); font-weight: 510; margin-left: 4px; }
.list { flex: 1; overflow: hidden; }
.gh { height: var(--row-h); display: flex; align-items: center; gap: 8px; padding: 0 10px 0 18px; background: var(--c-surface);
  border-bottom: 1px solid var(--c-border); }
.r + .gh { border-top: 1px solid var(--c-border); }
.gh b { font-weight: 590; }
.gh-sum { display: flex; gap: 12px; font: var(--td-caption); color: var(--c-text-3); }
.r { height: var(--row-h); display: flex; align-items: center; gap: 10px; padding: 0 16px 0 18px; }
.r.cursor { background: var(--c-surface-2); }
.r.sel { background: var(--c-selected); }
.lead { width: 16px; display: grid; place-items: center; color: var(--c-text-3); flex: none; }
.st { flex: none; }
.st-empty { width: 16px; flex: none; }
.tt { font-weight: 510; flex: none; }
.note { color: var(--c-text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pill { height: 20px; padding: 0 8px; display: inline-flex; align-items: center; gap: 6px; border-radius: var(--r-full);
  border: 1px solid var(--c-border); font: var(--td-caption); color: var(--c-text-2); flex: none; }
.pdot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.meta, .tm { font: var(--td-caption); color: var(--c-text-3); white-space: nowrap; flex: none; }
.val { text-align: right; font-weight: 510; flex: none; white-space: nowrap; }
.val.in { color: var(--c-primary-text); }
.r.void .tt, .r.void .val { color: var(--c-text-3); text-decoration: line-through; text-decoration-thickness: 1px; }
.bulk { position: absolute; left: 50%; bottom: 20px; transform: translateX(-50%); height: 40px; display: flex; align-items: center; gap: 2px;
  padding: 0 6px 0 14px; background: var(--c-elevated); border: 1px solid var(--c-border); border-radius: var(--r-md);
  box-shadow: var(--elev-2); white-space: nowrap; }
.bulk .n { color: var(--c-text-2); font-weight: 510; margin-right: 8px; }
.bulk .n b { color: var(--c-text); }
.vr { width: 1px; height: 20px; background: var(--c-border); margin: 0 6px; }
.bb { height: 28px; display: inline-flex; align-items: center; gap: 6px; padding: 0 8px; border-radius: var(--r-sm); color: var(--c-text-2); font-weight: 510; }
.bb .ic { color: var(--c-text-3); }
.bb.danger, .bb.danger .ic { color: var(--c-danger); }
.bb .kbd { margin-left: 2px; }
.scrim { position: absolute; inset: 0; background: var(--c-scrim-menu); }
.cmdk { position: absolute; left: 50%; top: 20%; width: 640px; max-width: 90%; margin-left: -320px; background: var(--c-elevated);
  border: 1px solid var(--c-border); border-radius: var(--r-lg); box-shadow: var(--elev-3); overflow: hidden; }
.ctx { padding: 12px 14px 0; }
.cchip { height: 22px; display: inline-flex; align-items: center; gap: 6px; padding: 0 8px 0 4px; border-radius: var(--r-sm);
  background: var(--c-surface-2); border: 1px solid var(--c-border); font: var(--td-caption); color: var(--c-text-2); }
.inp { height: 52px; display: flex; align-items: center; padding: 0 18px; font: 400 15px/20px var(--font); border-bottom: 1px solid var(--c-border); }
.inp .ph { color: var(--c-text-placeholder); }
.caret { width: 1.5px; height: 20px; background: var(--c-primary-text); margin: 0 1px; }
.res { padding: 4px 0 6px; max-height: 400px; }
.cg { padding: 8px 18px 4px; font: var(--td-caption); color: var(--c-text-3); }
.ci { height: 36px; margin: 0 6px; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: var(--r-md);
  font: var(--td-body); color: var(--c-text); }
.ci .ic { color: var(--c-text-3); }
.ci.cur { background: var(--c-menu-active); }
.ci.cur .ic { color: var(--c-text-2); }
.ci.hl .lab { color: var(--c-text-2); }
.ci.hl em { font-style: normal; color: var(--c-text); font-weight: 590; }
.cf { height: 36px; display: flex; align-items: center; gap: 14px; padding: 0 14px; border-top: 1px solid var(--c-border);
  font: var(--td-caption); color: var(--c-text-3); }
.cf > span { display: inline-flex; align-items: center; gap: 6px; }

/* ---------- iPhone (iOS 26; Inter stands in for SF Pro) ---------- */
.phone { width: 410px; }
.frame { padding: 10px; border-radius: 64px; background: #0B0C0E; box-shadow: 0 0 0 1.5px #3A3B3E, 0 24px 56px rgba(15,17,21,.22); }
.screen { position: relative; width: 390px; height: 844px; border-radius: 54px; overflow: hidden; background: var(--c-bg); color: var(--c-text);
  isolation: isolate; }
.pc { position: absolute; left: 0; right: 0; top: 0; padding-top: 104px; }
.sbar { position: absolute; top: 0; left: 0; right: 0; height: 54px; display: flex; align-items: center; justify-content: space-between;
  padding: 4px 30px 0 52px; z-index: 4; }
.sbar b { font: 590 17px/22px var(--font); }
.glyphs { display: flex; gap: 6px; align-items: center; }
.island { position: absolute; top: 11px; left: 50%; width: 124px; height: 36px; margin-left: -62px; border-radius: 18px; background: #000; z-index: 5; }
.plead { position: absolute; top: 60px; left: 16px; z-index: 4; }
.plead .appicon { box-shadow: 0 0 0 1px var(--c-border); }
.inline { position: absolute; top: 54px; left: 0; right: 0; height: 44px; display: grid; place-items: center; z-index: 4; }
.ptb { position: absolute; top: 54px; right: 16px; height: 44px; display: flex; gap: 8px; z-index: 4; }
.gbtn { position: relative; width: 44px; height: 44px; border-radius: 22px; display: grid; place-items: center; color: var(--c-text); }
.gbtn.prom { background: var(--c-primary); color: var(--c-on-primary); box-shadow: inset 0 1px 0 rgba(255,255,255,.22), var(--elev-2); }
.ltitle { padding: 2px 16px 0; }
.lsub { padding: 0 16px; color: var(--c-text-2); }
.mcard, .ncard { margin: 14px 16px 0; padding: 14px 16px; background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-lg); }
.mrow { display: flex; justify-content: space-between; color: var(--c-text-2); }
.mbig { margin-top: 2px; font: 590 28px/34px var(--font); }
.mbar, .mprog { height: 6px; margin: 10px 0 8px; display: flex; gap: 2px; }
.mbar i, .mprog i { display: block; height: 100%; border-radius: 3px; }
.mbar .used, .mprog .used { background: var(--c-primary); }
.mbar .rest, .mprog .rest { flex: 1; background: var(--c-surface-3); }
.mbtn { margin-top: 14px; height: var(--control-h-mobile-lg); border-radius: var(--r-lg); display: flex; align-items: center; justify-content: center;
  gap: 8px; font: var(--t-card-title); }
.mbtn.pri { background: var(--c-primary); color: var(--c-on-primary); }
.search { margin: 12px 16px 0; height: 36px; padding: 0 10px; display: flex; align-items: center; gap: 6px; border-radius: 10px;
  background: var(--c-surface-3); color: var(--c-text-placeholder); }
.ncard .t-row-meta { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.ncard .long { margin-top: 10px; }
.tags { display: flex; gap: 8px; margin-top: 12px; }
.tagp { height: 24px; padding: 0 8px; display: inline-flex; align-items: center; gap: 6px; border-radius: var(--r-full);
  border: 1px solid var(--c-border); font: var(--t-tag-label); color: var(--c-text-2); }
mark { background: var(--c-selection); color: inherit; padding: 1px 2px; border-radius: 3px; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
.pills { display: flex; gap: 8px; padding: 12px 16px 0; }
.ppill { height: 36px; padding: 0 14px; display: inline-flex; align-items: center; border-radius: 18px; border: 1px solid var(--c-border);
  color: var(--c-text-2); }
.ppill.on { background: var(--c-surface-3); border-color: transparent; color: var(--c-text); }
.psh { display: flex; justify-content: space-between; padding: 18px 16px 6px; color: var(--c-text-3); }
.plist { padding-left: 16px; }
.prow { position: relative; height: var(--row-h-mobile); display: flex; align-items: center; gap: 14px; padding-right: 16px; }
.prow + .prow::before { content: ""; position: absolute; top: 0; left: 34px; right: 0; height: 1px; background: var(--c-border); }
.picon { color: var(--c-text-3); }
.pt { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.pt span { color: var(--c-text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pa { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; flex: none; }
.pa b.in { color: var(--c-primary-text); }
.prow.void .pt b, .prow.void .pa b { color: var(--c-text-3); text-decoration: line-through; text-decoration-thickness: 1px; }
.pa span { color: var(--c-text-3); }
.edge { position: absolute; left: 0; right: 0; bottom: 0; height: 132px; z-index: 2; pointer-events: none;
  background: linear-gradient(to bottom, rgb(var(--c-bg-rgb) / 0), rgb(var(--c-bg-rgb) / .7) 55%, rgb(var(--c-bg-rgb) / .9));
  -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px);
  -webkit-mask-image: linear-gradient(to bottom, transparent, #000 45%); mask-image: linear-gradient(to bottom, transparent, #000 45%); }
.edge-top { position: absolute; left: 0; right: 0; top: 0; height: 120px; z-index: 3; pointer-events: none; /* the soft scroll edge */
  background: linear-gradient(to bottom, rgb(var(--c-bg-rgb) / .97), rgb(var(--c-bg-rgb) / .93) 72%, rgb(var(--c-bg-rgb) / 0));
  -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
  -webkit-mask-image: linear-gradient(to bottom, #000 72%, transparent); mask-image: linear-gradient(to bottom, #000 72%, transparent); }
.tabbar { position: absolute; left: 16px; width: 286px; bottom: 24px; height: 62px; border-radius: 31px; z-index: 3;
  display: flex; align-items: stretch; padding: 4px; }
.tab { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-radius: 27px; color: var(--c-text-2); }
.tab b { font: 510 10px/12px var(--font); }
.tab.on { color: var(--c-primary-text); background: var(--c-pressed); }
.stab { position: absolute; right: 16px; bottom: 24px; width: 62px; height: 62px; border-radius: 31px; z-index: 3; display: grid; place-items: center;
  color: var(--c-text-2); }
.home { position: absolute; z-index: 5; bottom: 8px; left: 50%; width: 136px; height: 5px; margin-left: -68px; border-radius: 3px; background: var(--c-text); }
.ptoast { position: absolute; z-index: 3; left: 50%; transform: translateX(-50%); bottom: 98px; height: 44px; display: flex; align-items: center; gap: 10px;
  padding: 0 4px 0 14px; white-space: nowrap; background: var(--c-elevated); border: 1px solid var(--c-border); border-radius: 22px;
  box-shadow: var(--elev-2); }
.ptoast .undo { height: 44px; display: grid; place-items: center; padding: 0 12px; color: var(--c-primary-text); }

/* ---------- Android (Material 3, Roboto Flex, Material Symbols Rounded 300) ---------- */
.android { width: 432px; }
.aframe { padding: 10px; border-radius: 48px; background: #0B0C0E; box-shadow: 0 0 0 1.5px #3A3B3E, 0 24px 56px rgba(15,17,21,.22); }
.ascreen { position: relative; width: 412px; height: 915px; border-radius: 38px; overflow: hidden; background: var(--c-bg); color: var(--c-text);
  font-family: "Roboto Flex", "Noto Sans SC", sans-serif; }
.ascreen [class^="m3-"] { font-family: "Roboto Flex", "Noto Sans SC", sans-serif; }
.ms { font-family: "Material Symbols Rounded"; font-style: normal; font-weight: normal; line-height: 1; display: inline-block; flex: none;
  overflow: hidden; white-space: nowrap; font-feature-settings: "liga"; font-variation-settings: "FILL" 0, "wght" 300, "GRAD" 0, "opsz" 24; }
.ms.fill { font-variation-settings: "FILL" 1, "wght" 300, "GRAD" 0, "opsz" 24; }
.asb { position: absolute; top: 0; left: 0; right: 0; height: 44px; z-index: 3; display: flex; align-items: center; padding: 4px 24px 0; background: var(--c-bg); }
.asb b { font: 500 14px/20px "Roboto Flex", sans-serif; }
.aglyphs { display: flex; gap: 6px; align-items: center; }
.punch { position: absolute; left: 50%; top: 14px; width: 22px; height: 22px; margin-left: -11px; border-radius: 50%; background: #000; }
.atop { position: absolute; top: 44px; left: 0; right: 0; height: 64px; z-index: 3; display: flex; align-items: center; padding: 0 4px 0 16px;
  background: var(--c-bg); border-bottom: 1px solid var(--c-border); }
.aib { width: 48px; height: 48px; display: grid; place-items: center; color: var(--c-text-2); }
.acontent { position: absolute; top: 108px; left: 0; right: 0; padding-top: 8px; }
.acard { margin: 0 16px 4px; padding: 14px 16px; background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-lg); }
.arow2 { display: flex; justify-content: space-between; color: var(--c-text-2); }
.abig { margin-top: 2px; }
.along { margin-top: 8px; color: var(--c-text); }
.asearch { margin: 0 16px 12px; height: 56px; padding: 0 16px; display: flex; align-items: center; gap: 16px; border-radius: 28px;
  background: var(--c-surface-3); color: var(--c-text-2); }
.achips { display: flex; gap: 8px; padding: 8px 16px; }
.achip { height: 32px; padding: 0 16px; display: inline-flex; align-items: center; gap: 8px; border-radius: var(--r-sm); border: 1px solid var(--c-border);
  color: var(--c-text-2); }
.achip.on { background: var(--c-surface-3); border-color: transparent; color: var(--c-text); padding: 0 16px 0 8px; }
.achip .ms, .achip .ic { color: var(--c-text); }
.ash { display: flex; justify-content: space-between; align-items: flex-end; height: 40px; padding: 0 16px 6px; color: var(--c-text-3); }
.arow { height: 72px; display: flex; align-items: center; gap: 16px; padding: 0 16px; }
.arow .lead { width: 24px; color: var(--c-text-3); }
.at { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.at span { color: var(--c-text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.aa { display: flex; flex-direction: column; align-items: flex-end; flex: none; }
.aa b.m3-bodyLarge { font-weight: 500; }
.aa b.in { color: var(--c-primary-text); }
.arow.void .at b, .arow.void .aa b { color: var(--c-text-3); text-decoration: line-through; text-decoration-thickness: 1px; }
.aa span { color: var(--c-text-3); margin-top: 2px; }
.afab { position: absolute; right: 16px; bottom: 121px; width: 56px; height: 56px; border-radius: var(--r-xl); z-index: 3; display: flex;
  align-items: center; justify-content: center; gap: 8px; background: var(--c-primary); color: var(--c-on-primary); box-shadow: var(--elev-2); }
.afab.ext { width: auto; padding: 0 20px 0 16px; }
.anav { position: absolute; left: 0; right: 0; bottom: 0; height: 105px; padding-bottom: 24px; z-index: 3; display: flex;
  background: var(--c-surface); border-top: 1px solid var(--c-border); }
.anv { flex: 1; display: flex; flex-direction: column; align-items: center; padding-top: 12px; gap: 4px; color: var(--c-text-2); }
.aind { width: 64px; height: 32px; border-radius: 16px; display: grid; place-items: center; }
.anv.on { color: var(--c-primary-text); }
.anv.on .aind { background: var(--c-surface-3); }
.ahandle { position: absolute; z-index: 4; bottom: 10px; left: 50%; width: 108px; height: 4px; margin-left: -54px; border-radius: 2px; background: var(--c-text-2); }

/* ---------- component strip ---------- */
.comp { padding: 16px 16px 16px; }
.comp-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.cs { background: var(--c-bg); color: var(--c-text); border-radius: 10px; padding: 2px 12px 10px; box-shadow: 0 0 0 1px var(--c-border);
  font: var(--td-small); }
.cs-h { font: 590 12px/16px var(--font); color: var(--c-text-2); padding: 10px 0 4px; }
.crow { display: flex; flex-direction: column; gap: 6px; padding: 8px 0 10px; border-top: 1px solid var(--c-border); }
.clab { font: var(--td-caption); color: var(--c-text-3); }
.cval { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.b { height: var(--control-h-md); padding: 0 12px; border-radius: var(--r-sm); display: inline-flex; align-items: center; gap: 6px;
  font: var(--td-body-medium); font-size: 13px; white-space: nowrap; }
.b.pri { background: var(--c-primary); color: var(--c-on-primary); }
.b.pri .kbds { margin-left: 2px; }
.b.pri.hov { background: var(--c-primary-hover); }
.b.pri.prs { background: var(--c-primary-pressed); }
.b.second { background: var(--c-surface-2); border: 1px solid var(--c-border); color: var(--c-text); }
.b .ic { color: var(--c-text-3); }
.b.ghost { color: var(--c-text-2); padding: 0 8px; }
.b.ghost.hov { background: var(--c-hover); color: var(--c-text); }
.b.danger, .b.danger .ic { color: var(--c-danger); }
.b.sm { height: var(--control-h-sm); padding: 0 10px; font: var(--td-caption); }
.b .kbd { margin-left: 2px; }
.ib2 { width: 28px; height: 28px; display: grid; place-items: center; border-radius: var(--r-sm); color: var(--c-text-3); background: var(--c-hover); }
.fin { width: 104px; height: var(--control-h-lg); padding: 0 10px; border-radius: var(--r-sm); background: var(--c-surface); border: 1px solid var(--c-border-strong);
  display: flex; align-items: center; font: var(--td-body); color: var(--c-text-placeholder); }
.fin.focus { border-color: var(--c-focus); box-shadow: 0 0 0 1px var(--c-focus); color: var(--c-text); }
.fin.wide { width: 100%; }
.icaret { width: 1.5px; height: 18px; background: var(--c-focus); margin-left: 1px; }
.badge { height: 20px; padding: 0 8px; border-radius: var(--r-full); display: inline-flex; align-items: center; gap: 4px; font: var(--td-caption); }
.badge svg { width: 14px; height: 14px; margin-left: -3px; }
.badge.success { background: var(--c-success-container); color: var(--c-success); }
.badge.warning { background: var(--c-warning-container); color: var(--c-warning); }
.badge.danger { background: var(--c-danger-container); color: var(--c-danger); }
.tg { position: relative; width: 32px; height: 18px; border-radius: 9px; box-shadow: inset 0 0 0 1px var(--c-border-strong); }
.tg::after { content: ""; position: absolute; left: 4px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--c-border-strong); }
.tg.on { background: var(--c-primary); box-shadow: none; }
.tg.on::after { left: 16px; top: 2px; width: 14px; height: 14px; background: var(--c-on-primary); }
.mm { width: 220px; padding: 4px; background: var(--c-elevated); border: 1px solid var(--c-border); border-radius: var(--r-lg); box-shadow: var(--elev-2); }
.mi { height: 28px; padding: 0 6px 0 8px; border-radius: var(--r-sm); display: flex; align-items: center; gap: 8px; color: var(--c-text); }
.mi .ic { color: var(--c-text-3); }
.mi.cur { background: var(--c-menu-active); }
.mi.cur .ic { color: var(--c-text-2); }
.mi.danger, .mi.danger .ic { color: var(--c-danger); }
.msep { display: block; height: 1px; background: var(--c-border); margin: 4px 0; }

/* ---------- right column: type scale, dialog, icon x UI ---------- */
.tyb { background: var(--c-bg); color: var(--c-text); border-radius: 10px; padding: 4px 16px; box-shadow: 0 0 0 1px var(--c-border); }
.ty { display: flex; align-items: baseline; gap: 12px; padding: 6px 0; border-top: 1px solid var(--c-border); }
.ty:first-child { border-top: 0; }
.ty-k { width: 112px; flex: none; font: var(--td-caption); color: var(--c-text-2); }
.ty-k small { display: block; font: var(--td-micro); color: var(--c-text-3); }
.ty-s { white-space: nowrap; overflow: hidden; }
.dlg-stage { position: relative; height: 300px; border-radius: 10px; overflow: hidden; display: grid; place-items: center;
  background: repeating-linear-gradient(180deg, var(--c-bg) 0 36px, var(--c-surface-2) 36px 37px); }
.dlg-stage::before { content: ""; position: absolute; inset: 0; background: var(--c-scrim); }
.dlg { position: relative; width: 440px; padding: 20px; background: var(--c-elevated); color: var(--c-text); border: 1px solid var(--c-border);
  border-radius: var(--r-xl); box-shadow: var(--elev-3); font: var(--td-body); }
.dlg-body { margin-top: 6px; color: var(--c-text-2); }
.dlg-field { display: flex; flex-direction: column; gap: 6px; margin-top: 14px; font: var(--td-caption); color: var(--c-text-2); }
.dlg-act { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
.dlg-act .b { height: var(--control-h-lg); }
.iu-head { display: flex; gap: 14px; align-items: center; }
.iu-head .appicon { box-shadow: 0 0 0 1px rgba(0,0,0,.08); }
.iu-head p { font: 400 12px/17px var(--font); color: #55575A; }
.iu-head p b { color: #1B1C1D; font-weight: 590; }
.mini { position: relative; height: 164px; border-radius: 10px; overflow: hidden; background: var(--c-canvas); color: var(--c-text);
  font: var(--td-small); box-shadow: 0 0 0 1px rgba(0,0,0,.12); }
.msb { width: 168px; padding: 4px 6px; }
.msb .ws { margin-top: 0; height: 40px; }
.msb .ws-name { padding: 0 4px; gap: 7px; }
.mmain { position: absolute; left: 168px; top: 6px; right: 6px; bottom: 6px; background: var(--c-bg); border: 1px solid var(--c-border);
  border-radius: var(--r-md); display: flex; flex-direction: column; }
.mvh { height: 34px; flex: none; display: flex; align-items: center; padding: 0 12px; border-bottom: 1px solid var(--c-border); }
.mvh b { font-weight: 510; }
.lnk { color: var(--c-primary-text); font: var(--td-caption); }
.mr { height: 28px; display: flex; align-items: center; gap: 10px; padding: 0 12px; }
.mr b { font-weight: 510; }
.mr.sel { background: var(--c-selected); }
.mr .t3 { font: var(--td-caption); }
.mfoot { margin-top: auto; height: 36px; flex: none; display: flex; align-items: center; gap: 10px; padding: 0 6px 0 12px; border-top: 1px solid var(--c-border); }
.mfoot .t3 { font: var(--td-caption); }
.mprog { flex: 1; height: 4px; margin: 0; }
.mprog i { border-radius: 2px; }

/* ---------- swatches ---------- */
.spanel { border-radius: 12px; border: 1px solid; padding: 16px 16px 18px; font: var(--td-small); }
.spanel h4 { font: 590 13px/18px var(--font); margin-bottom: 10px; }
.spanel h4 span { font-weight: 510; margin-left: 4px; }
.sws { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 10px; margin-bottom: 12px; }
.sw { display: grid; grid-template-columns: 22px 1fr; column-gap: 8px; align-items: center; min-width: 0; }
.sw i { grid-row: span 2; width: 22px; height: 22px; border-radius: 5px; box-shadow: inset 0 0 0 1px rgba(127,127,127,.28); }
.sw b { font: 510 11px/13px var(--font); }
.sw span { font: 400 10px/12px var(--font); opacity: .72; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.txs { display: flex; flex-direction: column; gap: 2px; margin-bottom: 12px; }
.tx { display: flex; align-items: baseline; gap: 10px; padding: 4px 0; }
.tx b { font: 510 13px/18px var(--font); width: 112px; flex: none; white-space: nowrap; font-variant-numeric: tabular-nums; }
.tx span { font: 400 10.5px/14px var(--font); font-variant-numeric: tabular-nums; white-space: nowrap; }
.tx span:not(.ok) { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.tx .ok { margin-left: auto; flex: none; }
.stats { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.sbadge { height: 20px; padding: 0 8px; border-radius: 10px; display: inline-flex; align-items: center; font: 510 11px/14px var(--font);
  font-variant-numeric: tabular-nums; }
.fz { position: relative; height: 34px; border-radius: 8px; overflow: hidden; }
.fz-stripes { position: absolute; inset: 0; background: repeating-linear-gradient(135deg, #808080 0 8px, #2B72E0 8px 16px, #F2F4F7 16px 24px); filter: blur(3px); }
.fz span { position: absolute; inset: 5px 0; display: flex; align-items: center; padding-left: 10px; font: 510 12px/16px var(--font); }
"""


def m3_css(t):
    """Material 3 type scale from tokens.json (sp = px here)"""
    out = ""
    for k, v in t["font"]["android"]["scale"].items():
        out += (f'.m3-{k} {{ font-size: {v["size"]}px; line-height: {v["line"]}px; font-weight: {v["weight"]}; '
                f'letter-spacing: {v["tracking"]:g}px; }}\n')
    return out


# ---------- the sheet ----------
def page(t, theme_css, screen, icon, desk_mode, fonts_css="", font_note=""):
    scr = SCREENS[screen]
    app = t["name"]
    s = t["source"]
    warm = "icon-accent" in s
    L, Dk = t["color"]["light"], t["color"]["dark"]
    accent = f'图标强调色 <b>{s.get("icon-accent", s["accent"])}</b> → 界面主色 <b>{s["accent"]}</b>'
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    head = (f'<div class="bhead">{icon(48, "light")}<div><h1>{app} · 主题预览</h1>'
            f'<p>{accent} · primary {Dk["primary"]}（深浅同值，悬停 / 按下 {Dk["primary-hover"]} / {Dk["primary-pressed"]}）· '
            f'primary-text 深 {Dk["primary-text"]} / 浅 {L["primary-text"]} · 中性色 LCh 色相 {t["base"]["hue"]} · '
            f'样例界面 {scr["label"]}（--screen {screen}）· {font_note} · 生成于 {now}'
            + ("" if icon.given else " · <b>未传 --icon，图标处是占位图</b>") + "</p></div></div>")
    other = "light" if desk_mode == "dark" else "dark"
    row1 = (ios_phone(screen, scr, "light", icon, caption="<b>iPhone · 浅色</b> · 静止态；筛选 pill 视觉高 36，点击区补到 44")
            + ios_phone(screen, scr, "dark", icon, scrolled=True, toast=True, pid="ios-dark",
                        caption="<b>iPhone · 深色</b> · 滚动态：内容在玻璃栏下面，toast 是自定义浮层")
            + android(screen, scr, "light", caption="<b>Android · 浅色</b> · M3：TopAppBar 不透明，滚动后只加 1 px border")
            + f'<div class="panel comp"><h3>组件条 · 桌面尺寸</h3><div class="comp-cols">{components("light", scr)}{components("dark", scr)}</div>'
              f'<div class="note2">按钮 28、输入框 32、kbd 18、开关 32 × 18；主按钮一屏最多一个</div></div>')
    q = scr["desktop"]["cmdk"]["query"]
    desk = (f'<div class="desk">{desktop(screen, scr, desk_mode, icon, app)}<div class="cap"><b>桌面 · {MODE_NAME[desk_mode]}</b>'
            f' · 1280 × 800，倒 L 布局；第二行是键盘光标行（surface-2），两行多选（selected）；⌘K 输入「{q}」，'
            f'当前项 menu-active，遮罩 scrim-menu；视图头不放主色按钮</div></div>')
    if warm:
        extra = (f'<div class="panel"><h3>图标 × 界面</h3><div class="iu-head">{icon(88, "light")}'
                 f'<p><b>{s["icon-accent"]}只留在图标里，界面主色回落到{s["accent"]}。</b>primary {Dk["primary"]} · primary-text 深 '
                 f'{Dk["primary-text"]} / 浅 {L["primary-text"]}。图标底和界面中性色是同一种石墨（色相 {t["base"]["hue"]}）。</p></div>'
                 f'{mini(scr, "dark", icon, app)}{mini(scr, "light", icon, app)}</div>')
    else:
        extra = (f'<div class="panel"><h3>弹窗 · {MODE_NAME[desk_mode]}</h3>{dialog(scr, desk_mode, app)}'
                 f'<div class="note2">elevated、圆角 16、elev-3、遮罩 scrim；primary 填充只用在弹窗和表单的确认上</div></div>')
    rcol = (f'<div class="rcol"><div class="panel"><h3>桌面字号 · Inter（{MODE_NAME[other]}）</h3>{type_scale(t, other, scr)}</div>{extra}</div>')
    pal = f'<div class="palette">{swatches(t, scr)}</div>'
    measure = (f'<div class="measure">{ios_phone(screen, scr, "light", icon, scrolled=True, pid="ios-light-measure")}</div>')
    css = (fonts_css + "\n" + theme_css + "\n" + CSS.replace("@@W@@", str(BOARD_W)) + m3_css(t) + icon.css())
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>'
            f'<body><div class="board">{head}{row1}{desk}{rcol}{pal}</div>{measure}</body></html>')


# ---------- fonts ----------
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
GF = "https://fonts.googleapis.com/css2?family="


def cache_dir():
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    d = os.path.join(root, "rian-app-theme", "fonts")
    os.makedirs(d, exist_ok=True)
    return d


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def cached(url, name):
    p = os.path.join(cache_dir(), name)
    if not os.path.exists(p):
        data = fetch(url)
        open(p, "wb").write(data)
    return open(p, "rb").read()


def embed(css_url, tag, family, keep=None):
    """a Google Fonts stylesheet with its woff2 files inlined as data URIs, renamed to `family`"""
    css = cached(css_url, tag + ".css").decode()
    if keep:
        blocks = [b for n, b in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S) if n in keep]
    else:
        blocks = re.findall(r"@font-face \{.*?\}", css, re.S)
    rules = []
    for i, blk in enumerate(blocks):
        url = re.search(r"url\((.*?)\)", blk).group(1)
        data = base64.b64encode(cached(url, f"{tag}-{i}.woff2")).decode()
        blk = re.sub(r"font-family: '[^']+';", f"font-family: '{family}';", blk)
        rules.append(blk.replace(url, f"data:font/woff2;base64,{data}"))
    if not rules:
        raise RuntimeError("no @font-face in " + css_url)
    return rules


def fonts(html, offline=False):
    """@font-face rules for the sheet, and a note on what was used"""
    if offline:
        return "", "字体：本机（离线）", False
    rules, miss = [], []
    q = urllib.parse.quote
    try:  # the family name theme.css asks for first
        rules += embed(GF + "Inter:opsz,wght@14..32,100..900", "inter", "InterVariable", ("latin", "latin-ext"))
        rules += embed(GF + "Inter:opsz,wght@14..32,100..900&text=" + q("⌘⇧↵⌥⌃⌫←→↑↓"), "inter-keys", "InterVariable")
    except Exception as e:
        miss.append(f"Inter（{e}）")
    try:
        rules += embed(GF + "Roboto+Flex:opsz,wght@8..144,100..1000", "roboto-flex", "Roboto Flex", ("latin", "latin-ext"))
    except Exception as e:
        miss.append(f"Roboto Flex（{e}）")
    msr = True
    try:
        names = ",".join(sorted(Glyphs.used))
        tag = "msr-" + hashlib.sha1(names.encode()).hexdigest()[:10]
        rules += embed(GF + "Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=" + names,
                       tag, "Material Symbols Rounded")
    except Exception as e:
        msr = False
        miss.append(f"Material Symbols（{e}）")
    chars = "".join(sorted({ch for ch in html if ord(ch) >= 0x2E80}))
    try:
        tag = "notosc-" + hashlib.sha1(chars.encode()).hexdigest()[:10]
        rules += embed(GF + "Noto+Sans+SC:wght@100..900&text=" + q(chars), tag, "Noto Sans SC")
    except Exception as e:
        miss.append(f"Noto Sans SC（{e}）")
    note = "字体 Inter 可变 + Noto Sans SC（iPhone 屏用 Inter 代替 SF Pro），Android 屏 Roboto Flex + Material Symbols Rounded 300"
    if miss:
        note = "字体缺 " + "、".join(m.split("（")[0] for m in miss) + "，用本机字体代替"
        print("fonts: missing " + "; ".join(miss))
    return "\n".join(rules), note, msr


# ---------- render and measure ----------
def find_chromium():
    p = os.environ.get("CHROMIUM_PATH")
    if p:
        return p
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    return hits[-1] if hits else None


BAR_ITEMS = """sel => { const root = document.querySelector(sel), R = root.getBoundingClientRect();
  return [...root.querySelectorAll('[data-bar]')].map(el => { const r = el.getBoundingClientRect();
    return {text: el.dataset.bar, color: getComputedStyle(el).color, box: [r.left - R.left, r.top - R.top, r.right - R.left, r.bottom - R.top]}; }); }"""
SIZES = """() => { const out = {}; const add = (sel, what) => { const el = document.querySelector(sel); if (!el) return;
    const r = el.getBoundingClientRect(); out[what] = Math.round(r.width) + ' x ' + Math.round(r.height); };
  add('.phone .gbtn', 'iOS toolbar button'); add('.phone .ppill', 'iOS filter pill'); add('.phone .prow', 'iOS row');
  add('.phone .tabbar', 'iOS tab bar'); add('#ios-dark .ptoast', 'iOS toast');
  add('.android .atop', 'M3 TopAppBar'); add('.android .achip', 'M3 FilterChip'); add('.android .arow', 'M3 list item');
  add('.android .afab', 'M3 FAB'); add('.android .aind', 'M3 nav indicator'); add('.android .anav', 'M3 NavigationBar + inset');
  add('.win .r', 'desktop row'); add('.win .si', 'sidebar item'); add('.win .ci', 'command item'); add('.win .kbd', 'kbd');
  return out; }"""
# scrolled screens: the iPhone content moves up until a section header sits under the nav bar, with rows still
# under the tab bar; the Android content until the filter chips meet the TopAppBar
SCROLL = """() => document.querySelectorAll('[data-scroll]').forEach(c => {
  const screen = c.parentElement.clientHeight, kind = c.dataset.scroll;
  let a = c.querySelector('.' + kind), top = 0;
  if (kind === 'psh') {  // iPhone: the deepest header that still leaves 60 px of rows under the tab bar
    top = 104;
    for (const h of c.querySelectorAll('.psh')) if (c.offsetHeight - h.offsetTop + top >= screen + 60) a = h;
  }
  c.style.transform = `translateY(${top - a.offsetTop}px)`; })"""
# the frost check hides the bar text and the iOS scroll edge effect: the glass alone over the raw content
HIDE_BAR = "[data-bar], .edge, .edge-top { visibility: hidden !important; }"
HIDE_MENU = ".win .scrim, .win .cmdk { display: none !important; }"


def png_array(data):
    import io
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB")).astype(float)


def rel_lum(a):
    import numpy as np
    a = a / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def lch_arrays(a):
    """CIE LCh (D65) of an RGB array: chroma and hue"""
    import numpy as np
    a = a / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    A, B = 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])
    return np.hypot(A, B), np.degrees(np.arctan2(B, A)) % 360


def frost_check(back, items, scale):
    """lowest contrast of the bar text and icons against what is behind them (5th percentile of each patch)"""
    import numpy as np
    worst = None
    for it in items:
        ink = [float(v) for v in re.findall(r"[\d.]+", it["color"])[:3]]
        x0, y0, x1, y1 = (int(round(v * scale)) for v in it["box"])
        patch = back[max(0, y0):y1, max(0, x0):x1].reshape(-1, 3)
        if not len(patch):
            continue
        lp, li = rel_lum(patch), rel_lum(np.array(ink))
        cs = (np.maximum(lp, li) + 0.05) / (np.minimum(lp, li) + 0.05)
        c5 = float(np.percentile(cs, 5))
        if worst is None or c5 < worst[1]:
            worst = (it["text"], c5)
    return worst


def accent_area(img, hue):
    import numpy as np
    chroma, h = lch_arrays(img)
    near = np.abs((h - hue + 180) % 360 - 180) <= HUE_BAND
    return float((near & (chroma >= STRONG_CHROMA)).mean() * 100), float((near & (chroma >= FAINT_CHROMA)).mean() * 100)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="theme folder written by build.py (reads tokens.json and theme.css, writes preview.png)")
    ap.add_argument("--screen", choices=list(SCREENS), default="timer", help="sample screen: timer (default), notes or list")
    ap.add_argument("--icon", metavar="PNG", help="app icon, rian-app-icon's <name>-1024.png (default appearance)")
    ap.add_argument("--icon-dark", metavar="PNG", help="dark app icon for the dark UI, render.py --variants' <name>-dark.png (default: --icon)")
    ap.add_argument("--desktop-mode", choices=("dark", "light"), default="dark", help="mode of the desktop window (default dark)")
    ap.add_argument("--offline", action="store_true", help="skip Google Fonts and use the locally installed fonts")
    ap.add_argument("--scale", type=float, default=2, help="device scale factor of the screenshot (default 2)")
    a = ap.parse_args()

    t = json.load(open(os.path.join(a.out, "tokens.json"), encoding="utf-8"))
    theme_css = open(os.path.join(a.out, "theme.css"), encoding="utf-8").read()
    for p in (a.icon, a.icon_dark):
        if p and not os.path.isfile(p):
            sys.exit(f"icon not found: {p}")
    s = t["source"]
    tones = PALETTE["accent"].get(s.get("icon-accent", s["accent"]), PALETTE["accent"]["蓝"])["tones"]
    icon = AppIcon(a.icon, a.icon_dark, tones)

    draft = page(t, theme_css, a.screen, icon, a.desktop_mode)  # collects the characters and symbols in use
    fonts_css, note, Glyphs.msr = fonts(draft, a.offline)
    html = page(t, theme_css, a.screen, icon, a.desktop_mode, fonts_css, note)
    out = os.path.join(a.out, "preview.png")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        kw = {"executable_path": find_chromium()} if find_chromium() else {}
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": BOARD_W, "height": 1200}, device_scale_factor=a.scale)
        pg.set_content(html)
        pg.evaluate("document.fonts.ready")
        pg.evaluate(SCROLL)
        pg.wait_for_timeout(300)
        pg.locator(".board").screenshot(path=out)
        sizes = pg.evaluate(SIZES)
        frost_items = {m: pg.evaluate(BAR_ITEMS, sel) for m, sel in
                       (("light", "#ios-light-measure .screen"), ("dark", "#ios-dark .screen"))}
        pg.add_style_tag(content=HIDE_BAR)  # the frost alone, behind where the bar text was
        backs = {m: png_array(pg.locator(sel).screenshot()) for m, sel in
                 (("light", "#ios-light-measure .screen"), ("dark", "#ios-dark .screen"))}
        pg.add_style_tag(content="[data-bar], .edge, .edge-top { visibility: visible !important; } " + HIDE_MENU)
        shots = {"desktop": png_array(pg.locator(".board .win").screenshot()),
                 "iPhone 浅色": png_array(pg.locator(".board .phone:not(#ios-dark) .screen").screenshot()),
                 "iPhone 深色": png_array(pg.locator("#ios-dark .screen").screenshot()),
                 "Android": png_array(pg.locator(".board .ascreen").screenshot())}
        b.close()
    print("wrote", out)
    print("sizes: " + "; ".join(f"{k} {v}" for k, v in sizes.items()))

    fails = 0
    for m in ("light", "dark"):
        text, c = frost_check(backs[m], frost_items[m], a.scale)
        ok = c >= FROST_MIN
        fails += not ok
        print(f"frost {m}: lowest bar text contrast over scrolled content {c:.1f}:1 ({text}; glass only, no scroll edge); target >= {FROST_MIN:g}  "
              f"{'PASS' if ok else 'FAIL'}")
    hue = hex_to_lch(t["color"]["dark"]["primary"])[2]
    strong, faint = accent_area(shots["desktop"], hue)
    ok = strong <= DESK_MAX
    fails += not ok
    print(f"accent area desktop: {strong:.1f}% of the window in the primary hue (command menu hidden); "
          f"target <= {DESK_MAX:g}%  {'PASS' if ok else 'FAIL'}")
    print(f"  INFO incl. the selected tint: {faint:.1f}%")
    phones = {k: accent_area(v, hue) for k, v in shots.items() if k != "desktop"}
    worst = max(phones, key=lambda k: phones[k][0])
    ok = phones[worst][0] <= PHONE_MAX
    fails += not ok
    print(f"accent area phone: {phones[worst][0]:.1f}% ({worst}, the highest of "
          + ", ".join(f"{k} {v[0]:.1f}%" for k, v in phones.items()) + f"); target <= {PHONE_MAX:g}%  {'PASS' if ok else 'FAIL'}")
    print("  INFO incl. the selected tint: " + ", ".join(f"{k} {v[1]:.1f}%" for k, v in phones.items()))
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
