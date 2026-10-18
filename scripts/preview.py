#!/usr/bin/env python3
"""Render the review sheet for a theme written by build.py, and measure it.

    python3 scripts/preview.py out/                                    # timer screen
    python3 scripts/preview.py out/ --screen list --icon ledgerly-1024.png --icon-dark ledgerly-dark.png
    python3 scripts/preview.py out/ --screen editor                    # photo editor: canvas, slider, crop, viewer
    python3 scripts/preview.py out/ --screen chat                      # AI chat and image generation
    python3 scripts/preview.py out/ --screen notes --desktop           # add the desktop window
    python3 scripts/preview.py out/ --icon squeeze-1024.png --mark squeeze-mark.png  # the icon's subject for brand art

Writes out/preview.png: a 1960 px wide sheet of phones, saved at --scale 2 (3920 px). From the top:
  1. title row: app name, icon accent -> UI primary, primary and primary-text values, time of the render;
  2. the sample screen: two iPhones (390 x 844 pt) and an Android phone (Material 3, Pixel 412 x 915 dp), plus the
     component strip at phone sizes, light and dark;
  3. three more phones: for timer, notes and list the shared shell (settings, paywall, onboarding); for editor the
     photo grid with multi-select, the viewer and a permission pre-prompt; for chat the third-party AI consent, the
     paywall with credits and the report sheet. Beside them the phone type scale, and either the screen's bottom sheet or,
     when the icon accent is 珊瑚 / 黄 / 灰, an "icon x UI" cell: the warm icon next to the blue UI it falls back to;
  4. with --desktop (timer, notes and list): a 1280 x 800 desktop window (inverted-L layout, keyboard-cursor row,
     two multi-selected rows, the command menu open over scrim-menu), the desktop type scale and a dialog;
  5. brand surfaces: the launch screen, the about panel, an empty state in light and dark and the export-complete page,
     on the icon's graphite with the icon's own subject as the art (--mark, else <name>-mark.png next to --icon, else
     keyed out of the --icon PNG, else a stand-in); the paywall, onboarding, permission and consent art is the same;
  6. swatches of the four schemes (light, dark, light-hc, dark-hc) and of the media tokens.

UI icons are solid (Material Symbols Rounded, FILL 1, weight 500; on the iPhone screens in place of SF Symbols' .fill).

Screens: timer (focus timer), notes (long Chinese text, highlight, search field), list (ledger: amounts, filter
pills, list grouped by day), editor (photo editor, a dark page in every scheme: neutral canvas, before/after divider,
slider with a zero detent, tool tray, checkerboard cut-out, export progress, crop handles, viewer scrim) and chat
(AI: bubbles, action row, generation states, prompt field with attachment, aspect, send and stop, credits).

Then prints the checks, each PASS or FAIL (exit status 1 when one fails; preview.png is written either way):
  frost light / frost dark    bar text and icons over list content scrolled under them, >= 3:1
  frost photo light / dark    the same over a photo grid (a bright sky and a saturated photo among them)
  viewer scrim                white viewer controls over a bright photo, through the scrim, >= 4.5:1
                              (all on phones rendered off the sheet; glass and scrim only: the scroll-edge fade is
                              hidden while measuring)
  accent area phone           pixels in the primary's hue (+-25 deg, LCh chroma >= 20) <= 8 % of each phone screen
                              (worst of them), measured with photos, canvases, generated images and brand art hidden
                              (the checks and outlines drawn over them still count)
  accent area conversion      the same for the paywall, onboarding, permission, consent and sample-empty screens, <= 15 %
  accent area desktop         with --desktop: <= 5 % of the window, measured with the command menu hidden
  safe area                   paywall, onboarding, permission, consent, export and report sheets end above the home
                              indicator (iOS) or the gesture bar (Android): nothing pushed into it
Counting the faint selected tint too (chroma >= 4), or the photos, is printed as INFO only.

The photos are procedural (numpy), so the sheet needs no image files. Fonts: Inter (variable, opsz 14..32), Roboto
Flex, Material Symbols Rounded and a Noto Sans SC subset come from Google Fonts and are cached in
~/.cache/rian-app-theme/fonts; offline (or --offline) the sheet falls back to the locally installed fonts and says so.
The iPhone screens use Inter in place of SF Pro.

Needs Playwright + Chromium, numpy and Pillow (set CHROMIUM_PATH to use an existing Chromium).
"""
import argparse, base64, datetime, glob, hashlib, io, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # importing build.py must not leave a __pycache__ in the skill
sys.path.insert(0, HERE)
from build import COLUMNS, NEED, PALETTE, STATUS, TIERS, backgrounds, contrast, hex_to_lch, over  # noqa: E402

SCHEMES = ("light", "dark", "light-hc", "dark-hc")
SCHEME_NAME = {"light": "浅色 · 标准", "dark": "深色 · 标准", "light-hc": "浅色 · 高对比", "dark-hc": "深色 · 高对比"}
MODE_NAME = {"light": "浅色", "dark": "深色"}
BOARD_W = 1960  # 410 + 410 + 432 (phones) + 556 (component strip) + 3 gaps of 24 + 2 x 40 padding
FROST_MIN, SCRIM_MIN, DESK_MAX, PHONE_MAX, CONVERSION_MAX = 3.0, 4.5, 5.0, 8.0, 15.0
HUE_BAND, STRONG_CHROMA, FAINT_CHROMA = 25, 20, 4


# ---------- icons: solid, like the app icon's pieces ----------
# The sheet draws every UI icon from Material Symbols Rounded, FILL 1, weight 500 (the iPhone screens use it in place of
# SF Symbols' .fill variant at .semibold). LUCIDE is only the offline fallback, drawn at a heavier 2.25 px.
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
    "alert": '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
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
    "more-h": '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    "wand": '<path d="M15 4V2"/><path d="M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/><path d="M17.8 11.8 19 13"/><path d="M15 9h.01"/><path d="M17.8 6.2 19 5"/><path d="m3 21 9-9"/><path d="M12.2 6.2 11 5"/>',
    "contrast": '<circle cx="12" cy="12" r="10"/><path d="M12 18a6 6 0 0 0 0-12v12z"/>',
    "droplet": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    "thermometer": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "crop": '<path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/>',
    "scissors": '<circle cx="6" cy="6" r="3"/><path d="M8.12 8.12 12 12"/><path d="M20 4 8.12 15.88"/><circle cx="6" cy="18" r="3"/><path d="M14.8 14.8 20 20"/>',
    "share": '<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" x2="12" y1="2" y2="15"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "arrow-up": '<path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>',
    "paperclip": '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
    "image": '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>',
    "thumbs-up": '<path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
    "thumbs-down": '<path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "updown": '<path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "flip": '<path d="m3 7 5 5-5 5V7"/><path d="m21 7-5 5 5 5V7"/><path d="M12 20v2"/><path d="M12 14v2"/><path d="M12 8v2"/><path d="M12 2v2"/>',
    "coins": '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1v4"/><path d="m16.71 13.88.7.71-2.82 2.82"/>',
    "panel": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/>',
    "move-h": '<path d="m18 8 4 4-4 4"/><path d="M2 12h20"/><path d="m6 8-4 4 4 4"/>',
    "palette": '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>',
    "gem": '<path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/>',
    "buoy": '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/>',
    "grid": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
}
# the sheet's icon names -> Material Symbols Rounded
MS_NAME = {"search": "search", "plus": "add", "inbox": "inbox", "list": "list", "chart": "bar_chart", "target": "target",
           "card": "credit_card", "wallet": "account_balance_wallet", "settings": "settings", "hash": "tag",
           "chev-down": "expand_more", "chev-left": "chevron_left", "chev-right": "chevron_right", "filter": "filter_list",
           "sliders": "tune", "utensils": "restaurant", "train": "train", "coffee": "coffee", "bag": "shopping_bag",
           "cart": "shopping_cart", "banknote": "payments", "phone": "smartphone", "car": "directions_car",
           "file-down": "download", "file-text": "description", "folder": "folder", "pin": "push_pin", "archive": "archive",
           "clock": "schedule", "alert": "error", "book": "menu_book", "briefcase": "work", "mail": "mail", "bulb": "lightbulb",
           "history": "history", "star": "star", "play": "play_arrow", "home": "home", "pen": "edit_square", "help": "help",
           "receipt": "receipt_long", "dumbbell": "fitness_center", "zap": "bolt", "x": "close", "trash": "delete",
           "tag": "sell", "merge": "merge", "arrow-in": "south_west", "copy": "content_copy", "timer": "timer",
           "sun": "light_mode", "square": "square", "check": "check", "more": "more_vert", "more-h": "more_horiz",
           "wand": "auto_fix_high", "contrast": "contrast", "droplet": "water_drop", "thermometer": "thermostat",
           "crop": "crop", "scissors": "content_cut", "share": "ios_share", "heart": "favorite", "arrow-up": "arrow_upward",
           "paperclip": "attach_file", "image": "image", "refresh": "refresh", "thumbs-up": "thumb_up",
           "thumbs-down": "thumb_down", "flag": "flag", "bell": "notifications", "globe": "language", "info": "info",
           "shield": "shield", "updown": "unfold_more", "rotate-ccw": "rotate_left", "flip": "flip", "coins": "toll",
           "panel": "menu", "move-h": "swap_horiz", "palette": "palette", "gem": "diamond", "buoy": "support",
           "grid": "grid_view", "layers": "layers"}
# Material Symbols Rounded names for the Android screen; LUCIDE stands in when the font is unavailable
MS_FALLBACK = {"add": "plus", "check": "check", "search": "search", "more_vert": "more", "settings": "settings",
               "receipt_long": "receipt", "bar_chart": "chart", "savings": "wallet", "payments": "banknote",
               "restaurant": "utensils", "coffee": "coffee", "subway": "train", "bakery_dining": "utensils",
               "shopping_cart": "cart", "local_taxi": "car", "timer": "timer", "history": "history",
               "menu_book": "book", "edit_note": "pen", "mail": "mail", "description": "file-text",
               "folder": "folder", "star": "star", "play_arrow": "play", "flight": "briefcase",
               "lightbulb": "bulb", "restaurant_menu": "utensils", "push_pin": "pin", "close": "x",
               "content_copy": "copy", "refresh": "refresh", "thumb_up": "thumbs-up", "thumb_down": "thumbs-down",
               "flag": "flag", "arrow_upward": "arrow-up", "crop": "crop", "rotate_left": "rotate-ccw", "flip": "flip",
               "tune": "sliders", "content_cut": "scissors", "filter": "layers", "notifications": "bell",
               "expand_more": "chev-down", "radio_button_checked": "target", "radio_button_unchecked": "square",
               "bolt": "zap", "menu": "panel", "image": "image", "aspect_ratio": "crop"}


def ic(name, size=16, cls="", bar=""):
    """a solid UI icon (Material Symbols Rounded, FILL 1, weight 500); bar names it as something on a glass bar, which
    the frost check measures. Without the font, a Lucide line icon at 2.25 px stands in"""
    attr = f' data-bar="{bar}"' if bar else ""
    if Glyphs.msr:
        Glyphs.used.add(MS_NAME[name])
        return (f'<i class="ms ic {cls}"{attr} style="font-size:{size}px;width:{size}px;height:{size}px">{MS_NAME[name]}</i>')
    return (f'<svg class="ic {cls}"{attr} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">{LUCIDE[name]}</svg>')


class Glyphs:
    """Material Symbols Rounded (FILL 1, weight 500: solid like the app icon), or Lucide without the font"""
    msr = True
    used = set()

    @classmethod
    def ms(cls, name, extra="", size=24):
        cls.used.add(name)
        if cls.msr:
            return f'<i class="ms {extra}" style="font-size:{size}px;width:{size}px;height:{size}px">{name}</i>'
        return ic(MS_FALLBACK.get(name, "square"), size, extra)


def status_icon(kind):
    """Linear-style status circles, 16 px, with 2 px rings so they weigh the same as the solid icons; a ledger draws only
    the exceptions"""
    if kind == "booked":  # the default state of a ledger row: nothing to say, keep the slot so titles align
        return '<span class="st-empty"></span>'
    if kind == "done":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="var(--c-success)"/>'
                '<path d="M5 8.2l2 2 4-4.3" stroke="var(--c-on-success)" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    if kind == "todo":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" '
                'stroke="var(--c-text-3)" stroke-width="2"/></svg>')
    if kind == "backlog":
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" '
                'stroke="var(--c-text-3)" stroke-width="2" stroke-dasharray="2.6 2.1"/></svg>')
    if kind == "progress":  # in progress is information (in-progress = info), never a warning
        return ('<svg class="st" width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="var(--c-in-progress)" stroke-width="2"/>'
                '<path d="M8 8V4.5a3.5 3.5 0 0 1 0 7z" fill="var(--c-in-progress)"/></svg>')
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


class BrandMark:
    """the icon's subject alone (its body pieces and accent piece, glow kept, no background) for brand art on the
    graphite brand panel: --mark (rian-app-icon render.py --variants' <name>-mark.png or .svg), else the <name>-mark.png
    next to --icon, else keyed out of the --icon PNG (its base is the known graphite gradient), else a stand-in in the
    icon accent. It is only ever scaled as a whole, so the cuts stay 48 / 1024 of the icon."""

    def __init__(self, mark, icon, tones):
        self.how = "stand-in"
        if not mark and icon:
            sib = re.sub(r"-1024\.png$", "-mark.png", icon)
            mark = sib if sib != icon and os.path.isfile(sib) else None
        if mark:
            self.how = "mark"
            data = open(mark, "rb").read()
            if mark.lower().endswith(".svg"):
                vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', data.decode()).group(1).split()]
                self.ratio = vb[2] / vb[3]
                self.src = "data:image/svg+xml;base64," + base64.b64encode(data).decode()
            else:
                from PIL import Image
                im = Image.open(io.BytesIO(data))
                self.ratio = im.width / im.height
                self.src = "data:image/png;base64," + base64.b64encode(data).decode()
        elif icon:
            self.how = "keyed"
            self.src, self.ratio = self._keyed(icon)
        else:
            self.src, self.ratio = self._stand_in(tones), 1.0

    @staticmethod
    def _keyed(path):
        """the icon PNG minus its graphite base: alpha from the distance to the base gradient at each row"""
        import numpy as np
        from PIL import Image
        im = Image.open(path).convert("RGB").resize((1024, 1024))
        a = np.asarray(im).astype(float)
        top, bot = (np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) for h in PALETTE["brand"]["surface"])
        t = np.linspace(0, 1, 1024)[:, None, None]
        base = top * (1 - t) + bot * t
        d = np.abs(a - base).max(axis=2)
        alpha = np.clip((d - 4) / 20, 0, 1)
        ys, xs = np.nonzero(alpha > .02)
        x0, y0, x1, y1 = max(xs.min() - 8, 0), max(ys.min() - 8, 0), min(xs.max() + 9, 1024), min(ys.max() + 9, 1024)
        # un-premultiply against the base so half-covered edge pixels keep their own colour
        fg = np.where(alpha[..., None] > 0, (a - base * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3), 0)
        rgba = np.dstack([np.clip(fg, 0, 255), alpha * 255]).astype("uint8")[y0:y1, x0:x1]
        buf = io.BytesIO()
        Image.fromarray(rgba, "RGBA").save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), (x1 - x0) / (y1 - y0)

    @staticmethod
    def _stand_in(tones):
        """a body piece and an accent piece in the icon's gradients, the cut between them 48 / 1024 of the box (28 in 600)"""
        a, b = tones
        body_a, body_b = PALETTE["brand"]["body"]
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600"><defs>'
               f'<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{body_a}"/><stop offset="1" stop-color="{body_b}"/></linearGradient>'
               f'<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>'
               f'<mask id="m"><rect width="600" height="600" fill="#fff"/><circle cx="430" cy="170" r="158" fill="#000"/></mask></defs>'
               f'<rect x="20" y="120" width="460" height="460" rx="110" fill="url(#b)" mask="url(#m)"/>'
               f'<circle cx="430" cy="170" r="130" fill="url(#a)"/></svg>')
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

    def __call__(self, h, max_w=None):
        """the mark at height h (the icon subject's height), in pt; a wide mark is fitted into max_w"""
        if max_w and h * self.ratio > max_w:
            h = max_w / self.ratio
        return (f'<img class="bmark" data-brand alt="" src="{self.src}" '
                f'style="height:{h}px;width:{h * self.ratio:.1f}px">')


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
# same days; --desktop), the component strip's labels (strip), the shared shell (shell: paywall features, onboarding,
# settings), the bottom sheet of the right column (sheet) and the sample words of the type scale and swatches (sample:
# Chinese, then Latin and figures, then the swatch text). editor and chat draw their own phones.
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
                  "tags": ["餐饮", ("in-progress", "报销中"), ("success", "已对账")],
                  "badges": [("success", "已入账"), ("info", "报销中"), ("danger", "同步失败")],
                  "danger": "删除这一条", "seg": ("支出", "收入", "转账"), "step": ("提前提醒", "3 天"),
                  "slider": ("预算提醒线", "80 %", 80, False), "task": ("导入支付宝账单", 62, "第 2 / 3 个文件 · 还剩约 8 秒"),
                  "menu": [("copy", "复制一条", ("⌘", "D")), ("tag", "改分类", ("L",)), ("wallet", "改账户", ("A",))]},
        "shell": {"pitch": "账户、统计和预算不设上限",
                  "features": ["不限账户和账本", "按分类的月度统计和预算", "导出 CSV 和 Excel", "同步到 iPad 和 Mac"],
                  "onboard": ("记一笔只要 3 秒", "打开就是数字键盘：输入金额，选个分类，就记好了。"),
                  "demo": ("utensils", "午餐", money(-32), "餐饮 · 招行信用卡"),
                  "general": [("默认账户", "招商银行")]},
        "sheet": {"title": EXPORT, "rows": [("value", "范围", "2026年10月 · 128 笔"), ("seg", "格式", ("CSV", "Excel", "PDF")),
                                             ("switch", "包含备注", True)],
                  "ok": "导出", "note": "导出后可以存到「文件」，或者分享给别人"},
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
                  "tags": ["论文", ("in-progress", "进行中"), ("success", "已同步")],
                  "badges": [("success", "已完成"), ("info", "进行中"), ("danger", "同步失败")],
                  "danger": "删除这次专注", "seg": ("专注", "短休", "长休"), "step": ("番茄个数", "2"),
                  "slider": ("白噪音音量", "60 %", 60, False), "task": ("导出专注记录 PDF", 62, "第 52 / 84 页 · 还剩约 6 秒"),
                  "menu": [("copy", "复制任务", ("⌘", "D")), ("folder", "改项目", ("P",)), ("clock", "改时长", ("T",))]},
        "shell": {"pitch": "专注统计和白噪音全部解锁",
                  "features": ["不限项目和任务", "专注统计和每周回顾", "白噪音和自定义时长", "同步到 iPad 和 Mac"],
                  "onboard": ("一次只做一件事", "选一个任务，开始 25 分钟专注。中途想到别的事，先记下来，结束再看。"),
                  "demo": ("book", "读论文", "25:00", "论文 · 第 3 节"),
                  "general": [("默认时长", "25 分钟")]},
        "sheet": {"title": "导出专注记录", "rows": [("value", "范围", "2026年10月 · 46 次"), ("seg", "格式", ("PDF", "CSV", "图片")),
                                                  ("switch", "包含每周回顾", True)],
                  "ok": "导出", "note": "导出后可以存到「文件」，或者分享给别人"},
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
                  "tags": ["读书", ("text-3", "草稿"), ("info", "已共享")],
                  "badges": [("success", "已保存"), ("warning", "有冲突"), ("danger", "同步失败")],
                  "danger": "删除这篇笔记", "seg": ("列表", "卡片", "时间线"), "step": ("正文字号", "17"),
                  "slider": ("行距", "1.6 倍", 55, False), "task": ("导出 86 篇笔记 PDF", 62, "第 53 / 86 篇 · 还剩约 20 秒"),
                  "menu": [("copy", "复制一篇", ("⌘", "D")), ("folder", "移到文件夹", ("M",)), ("tag", "加标签", ("L",))]},
        "shell": {"pitch": "笔记、搜索和导出不设上限",
                  "features": ["不限笔记和文件夹", "全文搜索和标签", "导出 PDF 和 Markdown", "同步到 iPad 和 Mac"],
                  "onboard": ("想到就记", "打开就是一页新笔记，写完不用点保存，标题自动取第一行。"),
                  "demo": ("file-text", "关于专注", "386 字", "读书 · 刚刚保存"),
                  "general": [("新笔记位置", "全部笔记")]},
        "sheet": {"title": "导出笔记", "rows": [("value", "范围", "选中的 2 篇"), ("seg", "格式", ("PDF", "Markdown", "纯文本")),
                                              ("switch", "包含图片", True)],
                  "ok": "导出", "note": "导出后可以存到「文件」，或者分享给别人"},
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
    # editor and chat have no desktop window: their pages are phone pages
    "editor": {
        "label": "照片编辑",
        "tabs": [("grid", "image", "图库"), ("wand", "tune", "编辑"), ("settings", "settings", "设置")],
        "strip": {"ok": "完成", "field": ("文件名", '<span lang="en">IMG_2041</span>'),
                  "tags": ["人像", ("in-progress", "处理中"), ("success", "已保存")],
                  "badges": [("success", "已导出"), ("info", "处理中"), ("danger", "导出失败")],
                  "danger": "删除这张照片", "seg": ("JPEG", "PNG", "HEIC"), "step": ("导出倍率", "2×"),
                  "slider": ("曝光", "+12", 12, True), "task": ("导出 4 张照片", 62, "第 3 / 4 张 · 还剩约 12 秒"),
                  "menu": [("copy", "拷贝调整", ("⌘", "⇧", "C")), ("share", "分享", ("⌘", "⇧", "S")), ("heart", "收藏", ("F",))]},
        # tool tray: icon, name, value (empty: not adjusted); the first is the current tool
        "tools": [("sun", "曝光", "+12"), ("contrast", "对比度", "+8"), ("droplet", "饱和度", ""), ("thermometer", "色温", "−4"),
                  ("layers", "阴影", ""), ("sliders", "锐化", "")],
        "modes": ["调整", "滤镜", "裁剪", "抠图"],
        "queue": [("done", "IMG_2041", "已完成 · 3.1 MB"), ("done", "IMG_2042", "已完成 · 2.8 MB"),
                  ("progress", "IMG_2043", "62 %"), ("todo", "IMG_2044", "排队中")],
        "sheet": {"title": "导出 4 张照片", "rows": [("seg", "格式", ("JPEG", "PNG", "HEIC")), ("slider", "质量", "85 %", 85),
                                                  ("value", "尺寸", "原始 · 4032 × 3024"), ("value", "预估体积", "约 9.6 MB")],
                  "ok": "保存到相册", "alt": "分享", "note": "导出要几秒到几分钟；离开 app 也会继续，系统会显示进度"},
        "sample": ("调整曝光", "4032 × 3024", "曝光 +12"),
        "type": {"amount": "9.6 MB → 3.2 MB", "timecode": "01:24 / 03:10"},
    },
    "chat": {
        "label": "AI 绘图",
        "tabs": [("panel", "menu", "对话"), ("image", "image", "作品"), ("settings", "settings", "设置")],
        "strip": {"ok": "发送", "field": ("提示词", "海边小镇"),
                  "tags": ["胶片", ("in-progress", "生成中"), ("success", "已保存")],
                  "badges": [("success", "已完成"), ("info", "生成中"), ("danger", "生成失败")],
                  "danger": "删除这段对话", "seg": ("1:1", "3:4", "16:9"), "step": ("张数", "4"),
                  "slider": ("风格强度", "70 %", 70, False), "task": ("生成 4 张图", 62, "第 3 / 4 张 · 还剩约 15 秒"),
                  "menu": [("copy", "复制", ("⌘", "C")), ("refresh", "重新生成", ("⌘", "R")), ("flag", "举报", ())]},
        "model": "标准模型", "credits": 128,
        "prompt": "黄昏时的海边小镇，白色房子沿着山坡排开，窗户透出暖黄的灯光，胶片质感",
        "samples": [("dusk", "黄昏的海边小镇"), ("flowers", "雨后的花园，微距"), ("night", "霓虹灯下的街角"), ("sea", "夏天的海，俯拍")],
        "shell": {"pitch": "每月 500 点，放大和去背景",
                  "features": ["每月 500 点，约 500 张图", "4K 放大和去背景", "高峰时优先排队", "生成的图可以商用"]},
        "sheet": {"title": "选择模型", "rows": [("radio", "标准", "1 点 / 张 · 约 15 秒", True), ("radio", "精细", "2 点 / 张 · 约 40 秒", False),
                                              ("radio", "快速", "0.5 点 / 张 · 约 5 秒", False)],
                  "ok": "", "note": "点数余额 128 · 每月 1 日加 500 点"},
        "sample": ("生成 4 张图", "Credits 128", "消耗 4 点"),
        "type": {"amount": "128 点", "timecode": "00:15"},
    },
}


# ---------- photos: procedural, so the sheet needs no image files ----------
def photo_array(kind, w, h, seed=0):
    """an RGB float array (0..1): sky (bright blue sky over green hills: the blue sits in the UI blue's hue), bright
    (snow under a pale sky: the hardest case for white controls), dusk, flowers (saturated), sea, food, night"""
    import numpy as np
    from PIL import Image, ImageFilter
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
    x = np.ones((h, 1)) * np.linspace(0, 1, w)[None, :]
    C = lambda *v: np.array(v, float) / 255
    full = lambda *v: np.broadcast_to(C(*v), (h, w, 3))

    def noise(scale):  # smooth value noise, 0..1
        n = rng.random((max(2, h // scale), max(2, w // scale)))
        return np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float) / 255

    def blur(a, r):
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
        return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(float) / 255

    def mix(a, b, t):
        t = np.clip(t, 0, 1)[..., None]
        return a * (1 - t) + b * t

    if kind == "sky":
        horizon = 0.66 + 0.05 * np.sin(x * 5 + seed) + 0.03 * np.sin(x * 13 + seed * 2)
        img = mix(full(52, 120, 222), C(170, 210, 246), y / 0.66)
        cl = noise(max(8, w // 8)) * 0.7 + noise(max(4, w // 25)) * 0.3
        img = mix(img, C(250, 252, 255), blur(np.clip((cl - 0.52) * 3.2, 0, 1) * (y < 0.6), w / 100))
        img = np.where((y > horizon)[..., None], mix(full(92, 150, 70), C(28, 58, 30), (y - horizon) * 3), img)
    elif kind == "bright":
        img = mix(full(226, 236, 248), C(252, 253, 255), y * 1.4)
        ridge = 0.5 + 0.08 * np.sin(x * 7 + seed) + 0.04 * np.sin(x * 19)
        snow = mix(full(255, 255, 255), C(214, 226, 240), noise(max(6, w // 10)) * 0.6)
        img = np.where((y > ridge)[..., None], snow, img)
    elif kind == "dusk":
        img = mix(full(54, 44, 112), C(236, 120, 84), y / 0.62)
        img = mix(img, C(255, 196, 120), (y - 0.5) * 6)
        sun = np.hypot((x - 0.3 - 0.4 * (seed % 3) / 2) * w / h, y - 0.58)
        img = mix(img, C(255, 232, 170), (0.07 - sun) * 40)
        hills = 0.64 + 0.06 * np.sin(x * 4 + seed) + 0.025 * np.sin(x * 17)
        town = (y > hills - 0.05) & (np.sin(x * 60 + seed) > 0.2) & (y > hills - 0.02 - 0.03 * (np.sin(x * 23) > 0))
        img = np.where((y > hills)[..., None] | town[..., None], full(36, 26, 44), img)
        lights = (rng.random((h, w)) > 0.997) & (y > hills - 0.04)
        img = mix(img, C(255, 214, 140), blur(lights.astype(float), 1.2) * 4)
    elif kind == "flowers":
        img = mix(full(40, 96, 46), C(16, 48, 22), y)
        img = mix(img, C(120, 170, 70), noise(max(4, w // 16)) * 0.5)
        for c in ((230, 40, 60), (250, 200, 30), (210, 50, 160), (250, 120, 30), (240, 240, 235)):
            for _ in range(5):
                cx, cy, r = rng.random(), rng.random(), 0.05 + rng.random() * 0.07
                d = np.hypot((x - cx) * w / h, y - cy)
                img = mix(img, C(*c) * (0.75 + 0.25 * (1 - d / r))[..., None], (r - d) * 60)
    elif kind == "sea":
        img = mix(full(120, 190, 230), C(200, 230, 245), y / 0.4)
        sea = mix(mix(full(20, 120, 150), C(10, 60, 90), (y - 0.4) * 2), C(200, 235, 240),
                  np.clip((noise(max(3, w // 50)) - 0.7) * 4, 0, 1) * 0.6)
        img = np.where((y > 0.42)[..., None], sea, img)
        sand = mix(full(232, 210, 170), C(210, 180, 140), y)
        img = np.where((y > 0.78 + 0.04 * np.sin(x * 6 + seed))[..., None], sand, img)
    elif kind == "food":
        img = mix(full(120, 72, 44), C(70, 40, 26), y)
        d = np.hypot((x - 0.5) * w / h, y - 0.52)
        img = mix(img, C(244, 240, 232), (0.36 - d) * 50)
        img = mix(img, C(214, 110, 40), np.clip((0.24 - d) * 50, 0, 1) * (0.6 + 0.4 * noise(max(4, w // 30))))
        img = mix(img, C(90, 150, 60), np.clip((noise(max(4, w // 25)) - 0.72) * 6, 0, 1) * (d < 0.22))
    else:  # night
        img = mix(full(10, 14, 34), C(40, 30, 60), y)
        for _ in range(9):
            bx, bw, bh = rng.random(), 0.06 + rng.random() * 0.1, 0.2 + rng.random() * 0.3
            m = (np.abs(x - bx) < bw / 2) & (y > 1 - bh)
            img = np.where(m[..., None], full(22, 24, 40), img)
            win = m & (rng.random((h, w)) > 0.985)
            img = mix(img, C(255, 214, 150), blur(win.astype(float), 0.8) * 3)
    img = img + (rng.random((h, w, 1)) - 0.5) * 0.025  # a little grain
    return np.clip(img, 0, 1)


class Photos:
    """each photo once, as a CSS class with the JPEG inlined; elements carry data-photo (left out of the accent area)"""
    used = {}

    @classmethod
    def cls(cls, kind, w, h, seed=0, blur=0):
        name = f"ph-{kind}-{w}x{h}-{seed}" + (f"-b{blur}" if blur else "")
        cls.used[name] = (kind, w, h, seed, blur)
        return name

    @staticmethod
    def jpeg(kind, w, h, seed, blur):
        import io
        import numpy as np
        from PIL import Image, ImageFilter
        im = Image.fromarray((photo_array(kind, w, h, seed) * 255).astype(np.uint8))
        if blur:
            im = im.filter(ImageFilter.GaussianBlur(blur))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=84)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    @classmethod
    def css(cls):
        return "".join(f'.{n} {{ background-image: url("{cls.jpeg(*k)}"); }}\n' for n, k in cls.used.items())


def ph(kind, w, h, seed=0, cls="", style="", blur=0):
    """a photo filling its box (w x h: the pixels generated, twice the box at --scale 2)"""
    return f'<div data-photo class="photo {Photos.cls(kind, w, h, seed, blur)} {cls}" style="{style}"></div>'


# ---------- phone frames ----------
STATUS_BAR = """<div class="sbar"><b class="num">9:41</b><span class="glyphs">
  <svg width="18" height="12" viewBox="0 0 18 12"><rect x="0" y="8" width="3" height="4" rx="1" fill="currentColor"/><rect x="5" y="5.5" width="3" height="6.5" rx="1" fill="currentColor"/><rect x="10" y="3" width="3" height="9" rx="1" fill="currentColor"/><rect x="15" y="0" width="3" height="12" rx="1" fill="currentColor"/></svg>
  <svg width="16" height="12" viewBox="0 0 16 12"><path d="M8 2.2c2.3 0 4.4.9 6 2.4l1.1-1.2A10.3 10.3 0 0 0 8 .6C5.3.6 2.8 1.6.9 3.4L2 4.6c1.6-1.5 3.7-2.4 6-2.4zm0 3.4c1.4 0 2.6.5 3.6 1.4l1.1-1.2A7 7 0 0 0 8 4c-1.8 0-3.4.7-4.7 1.8l1.1 1.2c1-.9 2.2-1.4 3.6-1.4zM8 9a1.6 1.6 0 1 0 0 3.2A1.6 1.6 0 0 0 8 9z" fill="currentColor"/></svg>
  <svg width="27" height="13" viewBox="0 0 27 13"><rect x=".5" y=".5" width="23" height="12" rx="3.8" fill="none" stroke="currentColor" opacity=".4"/><rect x="2" y="2" width="18" height="9" rx="2.5" fill="currentColor"/><path d="M25 4.5v4c.8-.3 1.3-1.1 1.3-2s-.5-1.7-1.3-2z" fill="currentColor" opacity=".45"/></svg>
</span></div><div class="island"></div>"""
ANDROID_BAR = """<div class="asb"><b class="num">9:41</b><span class="grow"></span><span class="aglyphs">
    <svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 13.5 1 6.2a10 10 0 0 1 14 0z" fill="currentColor"/></svg>
    <svg width="16" height="16" viewBox="0 0 16 16"><path d="M15 2v12H3z" fill="currentColor"/></svg>
    <svg width="10" height="16" viewBox="0 0 10 16"><rect x="3" y="0" width="4" height="2" rx=".5" fill="currentColor"/><rect x="0.5" y="1.5" width="9" height="14" rx="2" fill="currentColor"/></svg>
  </span><i class="punch"></i></div>"""


def _frame_attrs(pid, label, conversion):
    return (f' id="{pid}"' if pid else "", f' data-label="{label}"' + (" data-conversion" if conversion else ""))


def ios_frame(inner, mode, label, caption="", pid="", cls="", conversion=False):
    """an iPhone, 390 x 844 pt: inner, then the status bar and the home indicator; label names it in the checks,
    conversion marks the screens with the looser accent budget (onboarding, paywall, permission and consent)"""
    i, a = _frame_attrs(pid, label, conversion)
    cap = f'<div class="cap">{caption}</div>' if caption else ""
    return (f'<div class="phone"{i} data-theme="{mode}"><div class="frame"><div class="screen {cls}" data-region="phone"{a}>'
            f'{inner}{STATUS_BAR}<i class="home"></i></div></div>{cap}</div>')


def android_frame(inner, mode, label, caption="", pid="", cls="", conversion=False):
    """a Pixel, 412 x 915 dp, Material 3"""
    i, a = _frame_attrs(pid, label, conversion)
    cap = f'<div class="cap">{caption}</div>' if caption else ""
    return (f'<div class="android"{i} data-theme="{mode}"><div class="aframe"><div class="ascreen {cls}" data-region="android"{a}>'
            f'{ANDROID_BAR}{inner}<i class="ahandle"></i></div></div>{cap}</div>')


# ---------- phone controls ----------
def gbtn(icon, bar="", prom=False, size=20):
    """an iOS 26 glass button, 44 pt"""
    return (f'<span class="gbtn prom">{ic(icon, size)}</span>' if prom
            else f'<span class="gbtn frost floating">{ic(icon, size, bar=bar)}</span>')


def gpill(label, prom=False, bar=False):
    """a glass capsule with a word; prom: the screen's one primary action (.glassProminent)"""
    b = f' data-bar="{label}"' if bar else ""
    return f'<span class="gpill{" prom" if prom else " frost floating"} t-row-title"><b{b}>{label}</b></span>'


def pbtn(label, kind="pri", icon="", cls=""):
    """a phone button, 50 high, radius 12: pri (primary fill), second (surface-2), plain (text only)"""
    return f'<span class="pbtn {kind} {cls}">{ic(icon, 20) if icon else ""}{label}</span>'


def segmented(opts, sel=0, cls=""):
    return (f'<span class="segc {cls}">' + "".join(f'<span class="seg{" on" if i == sel else ""}">{o}</span>'
                                                   for i, o in enumerate(opts)) + "</span>")


def stepper():
    return '<span class="stp"><b>−</b><i></i><b>+</b></span>'


def switch(on=True):
    return f'<span class="sw2{" on" if on else ""}"></span>'


def radio(on=False):
    return f'<span class="rad{" on" if on else ""}"></span>'


def slider(value, detent=False):
    """detent: value -100..100, filled from the zero tick; otherwise 0..100 from the left. Track surface-3, fill
    primary (an allowed use), white thumb"""
    if detent:
        left, width, pos = (50, value / 2, 50 + value / 2) if value >= 0 else (50 + value / 2, -value / 2, 50 + value / 2)
        tick = '<i class="sl-tick"></i>'
    else:
        left, width, pos, tick = 0, value, value, ""
    return (f'<div class="sl"><i class="sl-track"></i><i class="sl-fill" style="left:{left:g}%;width:{width:g}%"></i>{tick}'
            f'<i class="sl-thumb" style="left:{pos:g}%"></i></div>')


def seg_bar(pct, cls="mbar"):
    """used | 2 px gap | remaining: the icon's cut, echoed once in the UI"""
    return f'<div class="{cls}"><i class="used" style="width:calc({pct}% - 1px)"></i><i class="rest"></i></div>'


def progress(pct):
    """a determinate bar: used | 2 px gap | remaining"""
    return seg_bar(pct, "xbar")


def check_badge():
    """the check on a selected picture: a primary disc (white on it passes 4.5:1), white tick and ring"""
    return ('<svg class="chk" width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="10" fill="var(--c-primary)" '
            'stroke="#fff" stroke-width="1.5"/><path d="M6.8 11.2l2.8 2.8 5.6-5.8" stroke="#fff" stroke-width="1.8" fill="none" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg>')


class Brand:
    """the brand mark of this sheet and the app's category (set in main)"""
    mark = None
    category = ""


def brand_art(w, h, mark_h, overlay=""):
    """onboarding, paywall, consent, permission and empty-state art: the app icon's own mark on the graphite brand panel,
    lit from the top like the icon (light and dark mode alike). The mark keeps the icon's own margin: at most 64 % of the
    panel's height (18 % above and below, like the subject in the icon) and the width less 48 a side. With a real UI
    fragment (a notification, a sample row) the fragment sits at the bottom and the mark is centred in the space above
    it, 24 or more clear of it. The icon's accent appears only in the mark; the panel's corner is r-xl"""
    return (f'<div class="art bpanel{" over" if overlay else ""}" style="width:{w}px;height:{h}px"><span class="bp-mark">'
            f'{Brand.mark(min(mark_h, h * .64), w - 2 * 48)}</span>{overlay}</div>')


def demo_card(sh):
    icon, title, value, meta = sh["demo"]
    return (f'<div class="demo">{ic(icon, 22, "t3")}<span class="pt"><b class="t-row-title">{title}</b>'
            f'<span class="t-row-meta">{meta}</span></span><b class="t-amount num">{value}</b></div>')


# ---------- the list screens: timer, notes, list ----------
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


def ios_phone(name, scr, mode, icon, scrolled=False, toast=False, pid="", caption="", label=""):
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
    new_btn = gbtn("plus", prom=True, size=22) if scr["new_prominent"] else gbtn("plus", "新建图标", size=22)
    toast_html = (f'<div class="ptoast">{status_icon("done")}<span class="t-row-meta">{scr["toast"]}</span>'
                  f'<span class="undo t-row-title">撤销</span></div>') if toast else ""
    inline = f'<div class="inline t-card-title">{scr["title"]}</div>' if scrolled else ""
    edge_top = '<div class="edge-top"></div>' if scrolled else ""
    inner = f'''
  <div class="pc"{' data-scroll="psh"' if scrolled else ""}>
    <div class="ltitle t-page-title">{scr["title"]}</div><div class="lsub t-row-meta">{scr["sub"]}</div>
    {hero_ios(name)}
    <div class="pills">{pills}</div>
    {body}
  </div>
  {edge_top}
  <div class="plead">{icon(32, mode)}</div>{inline}
  <div class="ptb">{gbtn("filter", "筛选图标")}{new_btn}</div>
  <div class="edge"></div>
  {toast_html}
  <nav class="tabbar frost floating">{tabs}</nav>
  <span class="stab frost floating">{ic("search", 24, bar="搜索图标")}</span>'''
    return ios_frame(inner, mode, label or f"iPhone {MODE_NAME[mode]}", caption, pid)


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
    inner = f'''
  <div class="acontent" data-scroll="achips">{hero_android(name)}<div class="achips">{chips}</div>{body}</div>
  <header class="atop"><span class="atitle m3-titleLarge">{scr["title"]}</span><span class="grow"></span>
    <span class="aib">{Glyphs.ms("search")}</span><span class="aib">{Glyphs.ms("more_vert")}</span></header>
  {fab}
  <nav class="anav">{nav}</nav>'''
    return android_frame(inner, mode, f"Android {MODE_NAME[mode]}", caption)


# ---------- the shared shell: settings, paywall, onboarding ----------
def settings_ios(scr, mode, app, caption=""):
    """the fixed order: 通用, 外观, 语言, 会员, 支持, 关于 (About carries the signature and the other apps)"""
    def group(head, rows, foot=""):
        return (f'<div class="sg-h t-section-header">{head}</div><div class="sg">{"".join(rows)}</div>'
                + (f'<div class="sg-f t-row-meta">{foot}</div>' if foot else ""))

    def row(label, value="", chev=True, link=False):
        return (f'<div class="sr"><span class="t-row-title{" lnk" if link else ""}">{label}</span><span class="grow"></span>'
                f'<span class="t-row-meta t2">{value}</span>{ic("chev-right", 16, "t3") if chev else ""}</div>')
    body = (group("通用", [row(k, v) for k, v in scr["shell"]["general"]])
            + group("外观", [f'<div class="sr">{segmented(("跟随系统", "浅色", "深色"), 0, "full")}</div>'])
            + group("语言", [row("语言", "简体中文")])
            + group("会员", [row("管理订阅", "年付"), row("恢复购买", "", False, True)])
            + group("支持", [row("给我们评分"), row("发送反馈", "邮件"), row("帮助")])
            + group("关于", [row(f"关于 {app}", '<span class="num">2.3.0</span>'), row("更多 Rian Studio 的 app")],
                    "A Rian Studio app"))
    inner = f'''<div class="pc set">{body}</div>
  <div class="nbar"><span class="nb-l">{gbtn("chev-left")}</span><b class="t-card-title">设置</b></div>'''
    return ios_frame(inner, mode, f"iPhone {MODE_NAME[mode]} · 设置", caption, cls="grouped")


PLANS = [("年付", "¥98 / 年", "约 ¥8.17 / 月 · 7 天免费试用"), ("月付", "¥18 / 月", ""), ("终身", "¥198", "一次买断")]
# the credits paywall: subscriptions and credit packs in one component, two groups
CREDIT_PLANS = [("订阅", [("年付", "¥98 / 年", "每月 500 点 · 7 天免费试用"), ("月付", "¥18 / 月", "每月 500 点")]),
                ("点数包", [("100 点", "¥12", "不过期")])]


def paywall_ios(scr, mode, icon, app, caption="", credits=False):
    """one paywall for every app, the same layout and wording, only the benefits change: yearly, monthly, lifetime or
    credits, a trial; restore purchases, terms and privacy, the price and auto-renewal in words (App Store 3.1.2);
    StoreKit 2 on iOS"""
    feats = "".join(f'<div class="feat">{ic("check", 18)}<span class="t-row-title">{f}</span></div>'
                    for f in scr["shell"]["features"][:3 if credits else 4])

    def plan(i, n, p, m):
        return (f'<div class="plan{" on" if i == 0 else ""}">{radio(i == 0)}<span class="pt"><b class="t-row-title">{n}</b>'
                + (f'<span class="t-row-meta">{m}</span>' if m else "") + f'</span><b class="t-amount num">{p}</b></div>')
    if credits:
        plans = "".join(f'<div class="plan-h t-section-header">{head}</div>' + "".join(plan(g + i, *r) for i, r in enumerate(group))
                        for g, (head, group) in enumerate(CREDIT_PLANS))
    else:
        plans = "".join(plan(i, *r) for i, r in enumerate(PLANS))
    low = (f'<div class="low t-row-meta">{ic("coins", 16)}<span>点数不够这次生成（还差 <b class="num">1</b> 点）</span></div>'
           if credits else "")
    inner = f'''<div class="pw{" credits" if credits else ""}">
    {brand_art(350, 100 if credits else 140, PALETTE["brand"]["mark"]["min" if credits else "empty"])}
    <div class="pw-title t-title-1">{scr["shell"]["pitch"]}</div><div class="pw-sub t-row-meta">{app} 会员 · 随时可以取消</div>
    {low}<div class="feats">{feats}</div>
    <div class="plans">{plans}</div>
    {pbtn("免费试用 7 天")}
    <p class="fine t-row-meta">试用结束后按 <span class="num">¥98</span> / 年自动续费。到期前至少 24 小时在 设置 › Apple 账户 › 订阅 里取消，就不会续费。</p>
    <div class="links t-row-meta"><span>恢复购买</span><i></i><span>使用条款</span><i></i><span>隐私政策</span></div>
  </div>
  <div class="plead">{gbtn("x")}</div>'''
    return ios_frame(inner, mode, f"iPhone {MODE_NAME[mode]} · 付费墙", caption, conversion=True)


def onboarding_android(scr, mode, caption=""):
    """at most three screens; the first shows the core feature at work"""
    title, body = scr["shell"]["onboard"]
    inner = f'''<div class="onb">
    <div class="onb-skip m3-labelLarge">跳过</div>
    {brand_art(364, 232, PALETTE["brand"]["mark"]["empty"], demo_card(scr["shell"]))}
    <div class="dots"><i class="on"></i><i></i><i></i></div>
    <div class="m3-headlineSmall onb-t">{title}</div><p class="m3-bodyLarge onb-b">{body}</p>
    <div class="grow"></div>{pbtn("继续")}
  </div>'''
    return android_frame(inner, mode, f"Android {MODE_NAME[mode]} · 引导", caption, conversion=True)


# ---------- editor: media pages are dark in every scheme ----------
def editor_adjust_ios(scr, caption=""):
    """neutral canvas (media-dark), before/after divider, the current tool's slider with its zero tick, tool tray, modes"""
    tools = "".join(f'<span class="tool{" on" if i == 0 else ""}{" set" if v else ""}"><span class="tool-ic">{ic(i_, 22)}</span>'
                    f'<b class="t-tag-label">{n}</b></span>' for i, (i_, n, v) in enumerate(scr["tools"]))
    modes = "".join(f'<span class="mode t-row-title{" on" if i == 0 else ""}">{m}</span>' for i, m in enumerate(scr["modes"]))
    name, value = scr["tools"][0][1], scr["tools"][0][2]
    inner = f'''<div class="ed">
    <div class="ed-top">{gbtn("x")}<b class="t-card-title">{scr["modes"][0]}</b>{gpill("完成", prom=True)}</div>
    <div class="ed-canvas" style="height:476px"><div class="ba">
      {ph("sky", 716, 536, 2)}<div class="before">{ph("sky", 716, 536, 2)}</div>
      <i class="ba-line" style="left:45%"></i><span class="ba-knob" style="left:45%">{ic("move-h", 18)}</span>
      <span class="ba-chip t-tag-label" style="left:12px">原图</span><span class="ba-chip t-tag-label" style="right:12px">调整后</span>
    </div></div>
    <div class="ed-sl"><div class="sl-head"><b class="t-row-title">{name}</b><span class="t-timecode num">{value}</span></div>{slider(12, True)}</div>
    <div class="tray">{tools}</div>
    <div class="modes">{modes}</div>
  </div>'''
    return ios_frame(inner, "dark", "iPhone · 编辑", caption, cls="media")


PLANT = """<svg class="plant" width="210" height="270" viewBox="0 0 210 270">
  <ellipse cx="105" cy="258" rx="62" ry="8" fill="#000" opacity=".18"/>
  <path d="M58 182h94l-10 72a8 8 0 0 1-8 7H76a8 8 0 0 1-8-7z" fill="#C9734F"/><rect x="52" y="172" width="106" height="16" rx="5" fill="#B5603E"/>
  <path d="M105 172C102 130 92 96 70 70" stroke="#3E7A3A" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M105 172C110 120 128 86 150 58" stroke="#3E7A3A" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M105 172c-2-40 2-80 6-112" stroke="#3E7A3A" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M70 70C40 64 22 40 24 14c30 2 50 24 46 56z" fill="#4E9A48"/><path d="M150 58c8-30 34-46 58-42-2 30-26 48-58 42z" fill="#5BAA52"/>
  <path d="M111 60c-14-24-10-48 8-60 14 20 12 44-8 60z" fill="#4E9A48"/><path d="M96 122c-30 4-52-10-62-32 26-8 52 4 62 32z" fill="#5BAA52"/>
  <path d="M116 112c22-20 48-22 66-10-16 22-42 26-66 10z" fill="#4E9A48"/></svg>"""


def editor_cutout_ios(scr, caption=""):
    """the cut-out on the checkerboard, then the long task: determinate progress, time left, cancel, the queue"""
    q = "".join(f'<div class="qrow">{status_icon(k)}<b class="t-row-title num">{n}</b><span class="grow"></span>'
                f'<span class="t-row-meta num{" ip" if k == "progress" else ""}">{m}</span></div>' for k, n, m in scr["queue"])
    title, pct, left = scr["strip"]["task"]
    inner = f'''<div class="ed">
    <div class="ed-top">{gbtn("chev-left")}<b class="t-card-title">{scr["modes"][3]}</b>{gbtn("share")}</div>
    <div class="ed-canvas checker" data-photo style="height:330px">{PLANT}</div>
    <div class="xsheet">
      <i class="grab"></i>
      <div class="xs-h">{status_icon("progress")}<b class="t-card-title">正在{title}</b><span class="grow"></span><b class="t-amount num">{pct} %</b></div>
      {progress(pct)}
      <div class="t-row-meta t2">{left}</div>
      <div class="qlist">{q}</div>
      <div class="xs-note t-row-meta">{ic("info", 16)}<span>可以离开 app：系统会显示进度，完成后发通知</span></div>
      {pbtn("取消导出", "second")}
    </div>
  </div>'''
    return ios_frame(inner, "dark", "iPhone · 导出", caption, cls="media")


def editor_crop_android(scr, caption=""):
    """crop on the full-bleed black canvas: white handles, rule-of-thirds guides, the outside dimmed, rotation dial, ratios"""
    ticks = "".join(f'<i class="{"big" if k % 5 == 0 else ""}"></i>' for k in range(-24, 25))
    ratios = "".join(f'<span class="achip m3-labelLarge{" on" if i == 0 else ""}">{Glyphs.ms("check", size=18) if i == 0 else ""}{r}</span>'
                     for i, r in enumerate(("自由", "原始", "1:1", "4:5", "16:9")))
    inner = f'''<div class="ed">
    <header class="atop media"><span class="aib">{Glyphs.ms("close")}</span><span class="atitle m3-titleLarge">裁剪</span>
      <span class="grow"></span><span class="atext m3-labelLarge">完成</span></header>
    <div class="cr-canvas">{ph("sea", 824, 1000, 4)}
      <div class="cr-box"><i class="g v1"></i><i class="g v2"></i><i class="g h1"></i><i class="g h2"></i>
        <i class="hd c-tl"></i><i class="hd c-tr"></i><i class="hd c-bl"></i><i class="hd c-br"></i>
        <i class="eh e-t"></i><i class="eh e-b"></i><i class="eh e-l"></i><i class="eh e-r"></i></div></div>
    <div class="dial"><b class="m3-labelLarge num">−3°</b><div class="ticks">{ticks}</div><i class="dial-0"></i></div>
    <div class="achips ratio">{ratios}</div>
    <div class="cr-tools"><span class="aib">{Glyphs.ms("rotate_left")}</span><span class="aib">{Glyphs.ms("flip")}</span>
      <span class="grow"></span><span class="atext m3-labelLarge">还原</span></div>
  </div>'''
    return android_frame(inner, "dark", "Android · 裁剪", caption, cls="media")


# scrolled to the top edge (the frost photo check), the brightest, darkest and most saturated photos sit under the
# Cancel capsule (third cell) and the toolbar (the last two rows)
GRID = [("sky", 0), ("flowers", 1), ("bright", 2), ("sea", 3), ("food", 4), ("night", 5), ("bright", 6), ("flowers", 7),
        ("sky", 8), ("dusk", 9), ("food", 10), ("sea", 11), ("flowers", 12), ("night", 13), ("dusk", 14), ("bright", 15),
        ("night", 16), ("sky", 17), ("flowers", 18), ("bright", 19), ("night", 20)]


def grid_ios(mode, caption="", pid="", scrolled=False, label=""):
    """the photo grid in select mode: an outline inside the edge plus a check, never a tint; the limited-library notice"""
    sel = {1, 4, 6}
    cells = "".join(f'<div class="cell{" media-selected" if i in sel else ""}">{ph(k, 258, 258, s)}'
                    + (check_badge() if i in sel else '<i class="chk-off"></i>') + "</div>" for i, (k, s) in enumerate(GRID))
    inner = f'''<div class="pc"{' data-scroll="pgrid"' if scrolled else ""}>
    <div class="ltitle t-page-title">图库</div><div class="lsub t-row-meta">已选 <span class="num">3</span> 张</div>
    <div class="limited t-row-meta">{ic("info", 16)}<span class="grow">只能看到你选的 <span class="num">24</span> 张照片</span><b class="lnk">管理</b></div>
    <div class="pgrid">{cells}</div>
  </div>
  {'<div class="edge-top"></div>' if scrolled else ""}
  <div class="ptb">{gpill("取消", bar=True)}</div>
  <div class="edge"></div>
  <nav class="gtool frost floating">{ic("share", 22, bar="分享图标")}<b class="t-row-title" data-bar="已选 3 张">已选 3 张</b>
    {ic("heart", 22, bar="收藏图标")}{ic("trash", 22, bar="删除图标")}</nav>'''
    return ios_frame(inner, mode, label or f"iPhone {MODE_NAME[mode]} · 图库", caption, pid)


def viewer_ios(kind="sky", seed=21, caption="", pid="", toast=True, label="iPhone · 查看"):
    """full-bleed photo; the controls are white on the fixed dark scrim, not on glass; a tap hides both"""
    t = (f'<div class="ptoast vw-toast">{status_icon("done")}<span class="t-row-meta">已保存到相册</span>'
         f'<span class="undo t-row-title">分享</span></div>') if toast else ""
    inner = f'''<div class="vw">{ph(kind, 780, 1688, seed, "vw-photo")}
    <div class="viewer-scrim-top vw-s top"></div><div class="viewer-scrim-bottom vw-s bot"></div>
    <div class="vw-bar top"><span class="vib">{ic("chev-left", 24, bar="返回图标")}</span>
      <span class="vw-t"><b class="t-row-title" data-bar="日期">10月16日</b><span class="t-row-meta num" data-bar="时间">14:05</span></span>
      <span class="vib">{ic("more-h", 24, bar="更多图标")}</span></div>
    <div class="vw-bar bot"><span class="vib">{ic("share", 24, bar="分享图标")}</span><span class="vib">{ic("heart", 24, bar="收藏图标")}</span>
      <span class="vib">{ic("sliders", 24, bar="编辑图标")}</span><span class="vib">{ic("trash", 24, bar="删除图标")}</span></div>
    {t}
  </div>'''
    return ios_frame(inner, "dark", label, caption, pid, cls="media")


def permission_android(mode, icon, app, caption=""):
    """our own page first, then the system dialog: what we ask for and why (here notifications: Android 13+)"""
    card = (f'<div class="notif"><div class="nh">{icon(18, mode)}<span class="m3-labelMedium t2">{app} · 现在</span></div>'
            f'<b class="m3-titleSmall">导出完成</b><span class="m3-bodyMedium t2">'
            f'{"1 段视频" if Brand.category == "视频" else "4 张照片"}已保存到相册，点按查看</span></div>')
    inner = f'''<div class="onb perm">
    {brand_art(364, 262, PALETTE["brand"]["mark"]["min"], card)}
    <div class="m3-headlineSmall onb-t">导出完成时通知你</div>
    <p class="m3-bodyLarge onb-b">导出要几秒到几分钟。允许通知后可以离开 app：进度显示在通知栏，完成后提醒你。</p>
    <p class="m3-bodyMedium onb-n t3">下一步是系统的权限对话框；以后也可以在系统设置里改。</p>
    <div class="grow"></div>{pbtn("继续")}{pbtn("以后再说", "plain")}
  </div>'''
    return android_frame(inner, mode, f"Android {MODE_NAME[mode]} · 权限预请求", caption, conversion=True)


# ---------- chat: AI conversation and image generation ----------
def credit_chip(n, bar=False):
    b = ' data-bar="点数"' if bar else ""
    return f'<span class="gpill frost floating credit t-row-title">{ic("coins", 18)}<b class="num"{b}>{n}</b></span>'


def actions_row():
    """copy, regenerate, good, bad, report: text-3 icons in 44 pt targets"""
    return ('<div class="acts">' + "".join(f'<span class="act">{ic(i, 18)}</span>' for i in
                                           ("copy", "refresh", "thumbs-up", "thumbs-down", "flag")) + "</div>")


def composer(text, right, extra="", lines=3):
    """the prompt field: min 48, grows to 6 lines, then scrolls; attach on the left, send or stop on the right"""
    return (f'<div class="composer frost floating"><span class="cbtn">{ic("paperclip", 22)}</span>'
            f'<div class="cfield t-long-text" style="-webkit-line-clamp:{lines}">{text}</div>{extra}{right}</div>')


def send_btn(on=True):
    return f'<span class="send{" on" if on else ""}">{ic("arrow-up", 20)}</span>'


def stop_btn():
    return '<span class="send stop"><i></i></span>'


def chat_ios(scr, mode, caption=""):
    """bubbles (the user's on surface-2; the reply with no bubble, in long-text), the action row, streaming"""
    inner = f'''<div class="pc chat">
    <div class="bub t-long-text">帮我写一段海边小镇的画面描述，适合做明信片</div>
    <div class="reply t-long-text"><p>可以这样写：{scr["prompt"]}。想更像明信片，可以加上<mark>「俯拍、上方留白」</mark>。</p></div>
    {actions_row()}
    <div class="bub img">{ph("dusk", 192, 256, 3, "att")}</div>
    <div class="bub t-long-text">按这张图的色调生成 4 张</div>
    <div class="reply t-long-text"><p>好的，按这张图的暖色调生成 4 张<i class="caret-s"></i></p></div>
  </div>
  <div class="edge-top"></div>
  <div class="nbar"><span class="nb-l">{gbtn("panel")}</span><span class="model t-card-title">{scr["model"]}{ic("chev-down", 16, "t3")}</span>
    <span class="nb-r">{credit_chip(scr["credits"])}</span></div>
  <div class="edge"></div>
  {composer("再加一点雾气，远处的灯塔亮着灯，整体偏蓝绿色调，像 90 年代的胶片", send_btn())}'''
    return ios_frame(inner, mode, f"iPhone {MODE_NAME[mode]} · 对话", caption)


def generate_ios(scr, mode, caption=""):
    """the four states of a generation: done, streaming (steps), failed with retry (no credit charged), queued; a
    refused prompt; the composer with stop while it runs"""
    cells = (f'<div class="gcell">{ph("dusk", 350, 350, 5)}</div>'
             f'<div class="gcell run">{ph("dusk", 350, 350, 6, blur=14)}<span class="ring"><svg width="56" height="56" viewBox="0 0 56 56">'
             '<circle cx="28" cy="28" r="24" fill="none" stroke="rgba(255,255,255,.32)" stroke-width="4"/>'
             '<circle cx="28" cy="28" r="24" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-dasharray="90.5 151" '
             'transform="rotate(-90 28 28)"/></svg><b class="t-timecode num">18 / 30</b></span></div>'
             f'<div class="gcell fail">{ic("alert", 22)}<b class="t-row-title">生成失败</b><span class="t-row-meta">没有扣点数</span>'
             f'<span class="pbtn second sm">重试</span></div>'
             f'<div class="gcell queue">{ic("clock", 22, "t2")}<b class="t-row-title">排队中</b><span class="t-row-meta">前面还有 <span class="num">2</span> 个</span></div>')
    inner = f'''<div class="pc gen">
    <div class="pcard"><p class="t-row-title">{scr["prompt"]}</p>
      <div class="gchips"><span class="tagp">1:1</span><span class="tagp">4 张</span><span class="tagp">胶片</span>
        <span class="grow"></span><span class="t-row-meta t3 num">消耗 4 点</span></div></div>
    <div class="ggrid">{cells}</div>
    <div class="refused">{ic("shield", 20)}<div><b class="t-row-title">这条提示词不能生成</b>
      <p class="t-row-meta">提示词里有真实人物的名字。换一种描述再试，这次没有扣点数。</p><b class="lnk t-row-meta">查看内容规则</b></div></div>
  </div>
  <div class="nbar"><span class="nb-l">{gbtn("chev-left")}</span><b class="t-card-title">生成</b><span class="nb-r">{credit_chip(scr["credits"] - 4)}</span></div>
  <div class="edge"></div>
  {composer(scr["prompt"], stop_btn(), '<span class="aspect t-tag-label">1:1</span>', 1)}'''
    return ios_frame(inner, mode, f"iPhone {MODE_NAME[mode]} · 生成", caption)


def chat_android(scr, mode, caption=""):
    """a new chat: sample prompts with sample pictures in place of an empty page; send stays disabled until there is text"""
    cards = "".join(f'<div class="scard">{ph(k, 330, 220, 30 + i)}<span class="m3-bodyMedium">{t}</span></div>'
                    for i, (k, t) in enumerate(scr["samples"]))
    inner = f'''<header class="atop"><span class="aib">{Glyphs.ms("menu")}</span><span class="achip m3-labelLarge model-chip">{scr["model"]}
      {Glyphs.ms("expand_more", size=18)}</span><span class="grow"></span>
    <span class="achip m3-labelLarge credit-chip">{Glyphs.ms("bolt", size=18)}<span class="num">{scr["credits"]}</span></span></header>
  <div class="acontent ach">
    {brand_art(328, 100, PALETTE["brand"]["mark"]["min"])}
    <div class="m3-headlineSmall onb-t">想生成什么？</div><p class="m3-bodyMedium t2 ach-sub">点一个示例试试，或者直接描述你想要的画面</p>
    <div class="samples">{cards}</div>
  </div>
  <div class="acomp"><span class="aib">{Glyphs.ms("add")}</span><span class="m3-bodyLarge ph-t">描述你想要的画面</span><span class="grow"></span>
    <span class="aib">{Glyphs.ms("aspect_ratio")}</span><span class="asend">{Glyphs.ms("arrow_upward")}</span></div>'''
    return android_frame(inner, mode, f"Android {MODE_NAME[mode]} · 新对话", caption, conversion=True)


def consent_ios(mode, caption=""):
    """before personal data goes to a third-party AI: what, to whom, for what, how long; ask, and let people say no
    (App Store 5.1.2(i))"""
    items = [("image", "会发送什么", "你选的照片和输入的提示词"),
             ("globe", "发给谁", "Acme AI（第三方模型服务商，示例名），只用来生成这一次的图"),
             ("shield", "怎么保存", "处理完 30 天内删除，不用来训练模型"),
             ("sliders", "不同意也能用", "调整、裁剪、抠图都在本机完成")]
    rows = "".join(f'<div class="cons">{ic(i, 22, "t2")}<div><b class="t-row-title">{t}</b><p class="t-row-meta">{d}</p></div></div>'
                   for i, t, d in items)
    inner = f'''<div class="pw consent">
    {brand_art(350, 140, PALETTE["brand"]["mark"]["empty"])}
    <div class="pw-title t-title-1">要把照片发给第三方 AI 吗？</div>
    <div class="conss">{rows}</div>
    <div class="grow"></div>
    {pbtn("同意并继续")}{pbtn("不同意", "plain")}
    <p class="fine t-row-meta">随时可以在 设置 › 通用 里撤回 · <b class="lnk">隐私政策</b></p>
  </div>
  <div class="plead">{gbtn("x")}</div>'''
    return ios_frame(inner, mode, f"iPhone {MODE_NAME[mode]} · 第三方 AI 同意", caption, conversion=True)


def report_android(scr, mode, caption=""):
    """report or flag a reply or a picture from inside the app (Google Play AI-generated content policy)"""
    opts = ["冒犯或仇恨", "色情或低俗", "暴力或危险", "侵犯隐私或版权", "其他"]
    rows = "".join(f'<div class="rrow">{radio(i == 1)}<span class="m3-bodyLarge">{o}</span></div>' for i, o in enumerate(opts))
    inner = f'''<header class="atop"><span class="aib">{Glyphs.ms("menu")}</span><span class="atitle m3-titleLarge">对话</span></header>
  <div class="acontent"><div class="areply m3-bodyLarge"><p>{scr["prompt"]}。</p><p>海面很平静，远处有一艘小渔船。</p></div></div>
  <div class="ascrim"></div>
  <div class="bsheet"><i class="bgrab"></i><div class="m3-titleLarge">举报这条回复</div>
    <p class="m3-bodyMedium t2">我们会在 24 小时内处理，举报内容只用于审核。</p>
    {rows}
    <div class="afield m3-bodyLarge"><span class="t3">补充说明（可选）</span></div>
    <div class="bs-act">{pbtn("提交举报")}</div></div>'''
    return android_frame(inner, mode, f"Android {MODE_NAME[mode]} · 举报", caption)


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


# ---------- dialog and type scale (desktop, --desktop) ----------
def dialog(scr, mode, app):
    g = scr["desktop"]["dialog"]
    value = g["value"].replace("{app}", app)
    return f'''<div class="dlg-stage" data-theme="{mode}"><div class="dlg">
  <div class="td-title-2">{g["title"]}</div><p class="dlg-body">{g["body"]}</p>
  <label class="dlg-field"><span>{g["field"]}</span><span class="fin focus wide">{value}<span class="icaret"></span></span></label>
  <div class="dlg-act"><span class="b second">取消<kbd class="kbd">Esc</kbd></span>
    <span class="b pri">{g["ok"]}<span class="kbds"><kbd class="kbd on-pri">⌘</kbd><kbd class="kbd on-pri">↵</kbd></span></span></div>
</div></div>'''


def desktop_type_scale(t, mode, scr):
    """the desktop scale; the Latin and figures are marked lang="en" so they keep Inter's tracking on a Chinese page"""
    zh, latin, _ = scr["sample"]
    rows = ""
    for k, v in t["font"]["web"]["scale"].items():
        rows += (f'<div class="ty"><span class="ty-k">{k}<small>{v["size"]} / {v["line"]} · {v["weight"]}</small></span>'
                 f'<span class="td-{k} ty-s">{zh} <span lang="en">{latin}</span></span></div>')
    return f'<div class="tyb" data-theme="{mode}">{rows}</div>'


# ---------- component strip, type scale, bottom sheet, icon x UI (phone sizes) ----------
def strip(mode, scr):
    """the components at phone sizes, one column per mode, labelled with the screen's own words"""
    s = scr["strip"]
    tags = "".join(f'<span class="tagp">{t}</span>' if isinstance(t, str) else
                   f'<span class="tagp"><i class="pdot" style="background:var(--c-{t[0]})"></i>{t[1]}</span>' for t in s["tags"])
    glyph = {"success": status_icon("done").replace("var(--c-success)", "currentColor").replace("var(--c-on-success)", "var(--c-success-container)"),
             "info": status_icon("progress").replace("var(--c-in-progress)", "currentColor")}
    badges = "".join(f'<span class="badge {k}">{glyph.get(k, "")}{label}</span>' for k, label in s["badges"])
    sl_label, sl_value, sl_pct, detent = s["slider"]
    title, pct, left = s["task"]
    first = s["menu"][0]
    menu = "".join(f'<div class="cm t-long-text">{label}<span class="grow"></span>{ic(icon, 20)}</div>' for icon, label, _k in s["menu"][:2])
    rows = [
        ("按钮 · 主 / 按下 / 次", pbtn(s["ok"]) + pbtn("按下", "prs") + pbtn("取消", "second")),
        ("分段控件 · 步进器", segmented(s["seg"], 0, "full")
         + f'<span class="stp-row"><span class="t-row-meta t2">{s["step"][0]} <b class="num">{s["step"][1]}</b></span>{stepper()}</span>'),
        ("滑块 · 0 点吸附" if detent else "滑块",
         f'<div class="slw"><div class="sl-head"><b class="t-row-title">{sl_label}</b><span class="t-timecode num t2">{sl_value}</span></div>'
         f'{slider(sl_pct, detent)}</div>'),
        ("输入框 · 聚焦", f'<span class="fin2 t-long-text">{s["field"][0]}</span><span class="fin2 focus t-long-text">{s["field"][1]}<span class="icaret"></span></span>'),
        ("标签 · 状态徽章（进行中是 info）", f'<div class="wrap">{tags}</div><div class="wrap">{badges}</div>'),
        ("长任务 · 确定进度",
         f'<div class="task"><div class="task-h">{status_icon("progress")}<b class="t-row-title">{title}</b><span class="grow"></span>'
         f'<b class="t-amount num">{pct} %</b></div>{progress(pct)}<div class="task-f"><span class="t-row-meta t2">{left}</span>'
         f'<span class="grow"></span><span class="tbtn t-row-title">取消</span></div></div>'),
        ("开关 · 单选", switch(True) + switch(False) + radio(True) + radio(False)),
        ("长按菜单", f'<div class="cmenu">{menu}<div class="cm danger t-long-text">{s["danger"]}<span class="grow"></span>{ic("trash", 20)}</div></div>'),
        ("可选层 · iPad / Mac 接键盘时", kbd("⌘", "K") + seq("G", "I")
         + (f'<span class="tip">{first[1]} {kbd(*first[2])}</span>' if first[2] else "")),
    ]
    return (f'<div class="ps" data-theme="{mode}"><div class="cs-h">{MODE_NAME[mode]}</div>'
            + "".join(f'<div class="crow"><span class="clab">{k}</span><span class="cval">{v}</span></div>' for k, v in rows)
            + "</div>")


TYPE_DEFAULT = {"amount": "−¥32.00", "timecode": "01:24 / 03:10"}


def phone_type_scale(t, mode, scr):
    """the phone styles (theme.css .t-*, the iOS text styles), Inter standing in for SF Pro"""
    zh, latin, _ = scr["sample"]
    own = {**TYPE_DEFAULT, **scr.get("type", {})}
    ios = t["font"]["ios"]["styles"]
    rows = ""
    for k, v in t["font"]["web"]["phone"].items():
        sample = f'<span class="num">{own[k]}</span>' if k in own else f'{zh} <span lang="en">{latin}</span>'
        rows += (f'<div class="ty"><span class="ty-k">{k}<small>{v["size"]} / {v["line"]} · {v["weight"]} · {ios[k]["style"]}</small></span>'
                 f'<span class="t-{k} ty-s">{sample}</span></div>')
    return f'<div class="tyb" data-theme="{mode}">{rows}</div>'


def sheet(scr, mode):
    """the screen's bottom sheet at phone size: elevated, radius 16 on top, over scrim"""
    g = scr["sheet"]
    rows = ""
    for r in g["rows"]:
        k = r[0]
        if k == "value":
            rows += f'<div class="shr"><span class="t-row-title">{r[1]}</span><span class="grow"></span><span class="t-row-meta t2 num">{r[2]}</span></div>'
        elif k == "seg":
            rows += f'<div class="shr"><span class="t-row-title">{r[1]}</span><span class="grow"></span>{segmented(r[2])}</div>'
        elif k == "switch":
            rows += f'<div class="shr"><span class="t-row-title">{r[1]}</span><span class="grow"></span>{switch(r[2])}</div>'
        elif k == "slider":
            rows += (f'<div class="shr col"><div class="sl-head"><b class="t-row-title">{r[1]}</b><span class="t-timecode num t2">{r[2]}</span></div>'
                     f'{slider(r[3])}</div>')
        elif k == "radio":
            rows += (f'<div class="shr">{radio(r[3])}<span class="pt"><b class="t-row-title">{r[1]}</b><span class="t-row-meta t2">{r[2]}</span>'
                     f'</span></div>')
    act = (pbtn(g["alt"], "second") if g.get("alt") else "") + (pbtn(g["ok"]) if g["ok"] else "")
    return (f'<div class="sh-stage" data-theme="{mode}"><div class="psheet"><i class="grab"></i>'
            f'<div class="sh-t"><b class="t-card-title">{g["title"]}</b><span class="xbtn">{ic("x", 16)}</span></div>{rows}'
            + (f'<div class="sh-act">{act}</div>' if act else "") + f'<p class="t-row-meta t3">{g["note"]}</p></div></div>')


ACTION = {"list": "记一笔", "timer": "开始专注", "notes": "新建笔记", "editor": "保存到相册", "chat": "生成 4 张"}


def phone_mini(name, scr, mode, icon, app):
    """the warm icon on its blue UI, phone-sized: the icon at the top, the primary button, the current tab"""
    tabs = "".join(f'<span class="tab{" on" if i == 0 else ""}">{ic(lu, 22)}<b>{lab}</b></span>' for i, (lu, _ms, lab) in enumerate(scr["tabs"][:3]))
    return (f'<div class="pmini" data-theme="{mode}"><div class="pm-top">{icon(28, mode)}<b class="t-card-title">{app}</b>'
            f'<span class="grow"></span><b class="lnk t-row-meta">全部</b></div>{pbtn(ACTION[name])}<nav class="pm-tabs frost">{tabs}</nav></div>')


# ---------- brand surfaces: where the app icon's own material enters the UI ----------
EMPTY = {"list": ("还没有记录", "记下第一笔，月底就能看到钱花在了哪里"), "timer": ("还没有专注记录", "开始第一次专注，这里会按天记下时长"),
         "notes": ("还没有笔记", "写下第一条，之后可以按标签和全文搜索"), "editor": ("还没有作品", "导出过的照片会出现在这里"),
         "chat": ("还没有作品", "生成过的图会出现在这里，可以再编辑")}
# what the export-complete page says, by the app's category, else by the sample screen (a video app exports clips)
EXPORTED = {"视频": ("已导出 1 段 · ", "48 MB", "已保存到相册 · 0:42 · 1080p"), "editor": ("已导出 4 张 · ", "9.6 MB", "已保存到相册"),
            "chat": ("已导出 4 张 · ", "9.6 MB", "已保存到相册"), "notes": ("已导出 86 篇 · ", "3.2 MB", "PDF 已保存到「文件」"),
            "list": ("已导出 128 笔 · ", "24 KB", "CSV 已保存到「文件」"), "timer": ("已导出 30 天 · ", "12 KB", "CSV 已保存到「文件」")}


def brand_row(t, screen, icon, app):
    """launch screen, the about panel, an empty state in light and dark, the export-complete page: the icon's graphite,
    body and accent at brand positions only; the controls keep the primary"""
    hero, empty = PALETTE["brand"]["mark"]["hero"], PALETTE["brand"]["mark"]["empty"]
    title, line = EMPTY[screen]
    cat = Brand.category
    label, action = SCREENS[screen]["label"], ACTION[screen]
    if screen == "editor":  # an editor's empty library asks for something to edit
        action = "导入视频" if cat == "视频" else "导入照片"
    if cat == "视频" and screen == "editor":
        label, line = "视频剪辑", "导出过的视频会出现在这里"
    badge = f'<span class="bbadge t-tag-label"><i data-brand></i>{cat} app</span>' if cat else ""
    chev = ic("chev-right", 16, "t3")

    def card(inner, mode, cap, cls=""):
        return (f'<div class="bslot"><div class="bcard {cls}" data-theme="{mode}">{inner}</div>'
                f'<div class="cap">{cap}</div></div>')

    def row(label):
        return f'<div class="sr"><span class="t-row-title">{label}</span><span class="grow"></span>{chev}</div>'

    launch = card(f'<div class="blaunch">{Brand.mark(hero)}</div>', "dark",
                  "<b>启动页</b> · 浅色、深色同一张：图标的石墨底加图标主体，不放字")
    about = card(f'<div class="bnav t-card-title">关于</div>'
                 f'<div class="babout">{icon(72, "light")}<b class="t-card-title">{app}</b>'
                 f'<span class="t-row-meta num t2">版本 2.3.0（231）</span>{badge}</div>'
                 f'<div class="sg">{row("更多 Rian Studio 的 app")}{row("隐私政策")}{row("开源许可")}</div>'
                 f'<div class="sg-f t-row-meta">A Rian Studio app</div>', "light",
                 "<b>关于 · 浅色</b> · app 图标 72 直接放在页面上（图标自己就是品牌方块，不再套面板）"
                 + ("；类别徽章的圆点是图标强调色" if cat else ""), "grouped")

    def empty_state(mode):
        return card(f'<div class="bnav t-card-title">{label}</div><div class="bempty">{brand_art(240, 140, empty)}'
                    f'<b class="t-card-title">{title}</b><span class="t-row-meta t2">{line}</span>{pbtn(action)}</div>',
                    mode, f"<b>空状态 · {MODE_NAME[mode]}</b> · 品牌面板 240 × 140 放 {empty} 高的图标主体（上下各留 18 %）"
                          + ("；深色下面板外有一圈 brand-edge 细线" if mode == "dark" else "") + "；按钮仍是 primary")
    done, size, note = EXPORTED["视频" if cat == "视频" else screen]
    export = card(f'<div class="bnav t-card-title">导出完成</div>'
                  f'<div class="bpanel bexport" data-theme="dark"><span class="bx-mark">{Brand.mark(empty)}</span>'
                  f'<b class="t-card-title bx-t"><span class="bx-ok">{ic("check", 14)}</span>{done}<span class="num">{size}</span></b>'
                  f'<span class="t-row-meta b2">{note}</span></div>'
                  f'<div class="bact">{pbtn("分享")}{pbtn("完成", "second")}</div>', "dark",
                  "<b>导出完成 · 深色</b> · 品牌面板上是图标主体，结果一行前面是 success 勾（不压在主体上）；「分享」是 primary，强调色不进按钮")
    L = t["color"]["light"]
    return (f'<div class="panel brow"><h3>品牌位 · 图标的石墨底、顶光、主体和强调色只在这些地方进界面，工作界面不变</h3>'
            f'<div class="bcards">{launch}{about}{empty_state("light")}{empty_state("dark")}{export}</div>'
            f'<div class="note2">brand-surface {L["brand-surface-top"]} → {L["brand-surface-bottom"]}（图标的底，深浅同值）· '
            f'brand-accent {t["source"].get("brand-accent", "")} {L["brand-accent-light"]} → {L["brand-accent"]}（图标原色，只在图标主体和徽章圆点里，'
            f'不进按钮和选中态）· 面板里的字和控件用深色那套 token（on-brand {L["on-brand"]}、on-brand-2 {L["on-brand-2"]}）</div></div>')


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
        stat += f'<span class="sbadge" style="background:{C["info-container"]};color:{C["in-progress"]}">in-progress = info</span>'
        frost = (f'<div class="fz"><i class="fz-stripes"></i><span style="background:{C["frost"]};box-shadow:inset 0 1px 0 {C["frost-highlight"]},'
                 f' inset 0 0 0 1px {C["frost-border"]};color:{C["text"]}">frost · {alpha_label(C["frost"])}</span></div>')
        out += (f'<div class="spanel" style="background:{C["bg"]};color:{C["text"]};border-color:{over(C["border"], C["bg"])}">'
                f'<h4>{SCHEME_NAME[k]} <span style="color:{C["text-3"]}">{k}</span></h4><div class="sws">{chips}</div>'
                f'<div class="txs">{texts}</div><div class="sws">{acc}</div><div class="stats">{stat}</div>{frost}</div>')
    return out


def media_strip(t):
    """the media tokens: the same in every scheme, because editor and viewer pages are dark in all of them"""
    C = t["color"]["dark"]
    lv = PALETTE["media"]["canvas"]
    chips = "".join(f'<div class="msw"><i style="background:{C[n]}"></i><b>{n}</b><span>L {lv[k]:g} · 彩度 0 · {C[n]}</span></div>'
                    for n, k in (("media-black", "black"), ("media-dark", "dark"), ("media-mid", "mid"), ("media-white", "white")))
    chips += (f'<div class="msw"><i class="checker"></i><b>checker-a / -b</b><span>{C["checker-a"]} / {C["checker-b"]} · 格 '
              f'{t["size"]["media"]["checker"]}</span></div>')
    white = contrast(C["on-media"], over(C["viewer-scrim"], "#FFFFFF"))
    chips += (f'<div class="msw"><i class="scr"><b>Aa</b></i><b>viewer-scrim</b><span>{alpha_label(C["viewer-scrim"])} · '
              f'白字叠在白图上 {white:.1f}:1</span></div>')
    chips += (f'<div class="msw"><i class="guide"><span class="sel-demo"></span></i><b>media-guide · media-selected</b>'
              f'<span>{alpha_label(C["media-guide"])} · 深 {C["media-selected"]} / 浅 {t["color"]["light"]["media-selected"]}</span></div>')
    play = contrast(C["primary"], C["media-dark"])
    scrub = contrast(C["on-media"], over(C["media-track"], over(C["viewer-scrim"], "#FFFFFF")))
    chips += (f'<div class="msw"><i style="background:{C["media-dark"]}"><span class="playhead"></span>'
              f'<span class="scrub"><b></b></span></i><b>播放头 · 拖动条</b>'
              f'<span>primary 对 media-dark {play:.1f}:1；白段对 media-track（亮图上）{scrub:.1f}:1</span></div>')
    g, h = t["motion"]["gesture"], t["haptic"]
    note = (f'触感：选中 {h["selection"]["ios"]} / {h["selection"]["android"]} · 吸附 {h["snap"]["ios"]} / {h["snap"]["android"]} · '
            f'完成 {h["success"]["ios"]} / {h["success"]["android"]} · 失败 {h["failure"]["ios"]} / {h["failure"]["android"]}。'
            f'手势：双击放大到 {g["zoom-double-tap"]:g} 倍，最大 {g["zoom-max"]:g} 倍；下滑超过屏高 {g["dismiss-distance"] * 100:g} % '
            f'或 {g["dismiss-velocity"]:g} pt/s 关闭查看器；网格到查看器 zoom {t["motion"]["duration"]["zoom"]} ms。')
    return (f'<div class="panel mpanel"><h3>媒体色组 · 每套颜色里都一样（编辑页和查看页强制深色）</h3>'
            f'<div class="msws">{chips}</div><div class="note2">{note}</div></div>')


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
/* brand row: launch, about, empty states, export complete */
.brow { grid-column: 1 / -1; }
.bcards { display: flex; gap: 24px; margin: 14px 0 12px; }
.bslot { width: 352px; flex: none; }
.bslot .cap { margin-top: 8px; }
.bcard { position: relative; height: 470px; border-radius: 28px; overflow: hidden; background: var(--c-bg); color: var(--c-text);
  box-shadow: 0 0 0 1px rgba(0,0,0,.10); display: flex; flex-direction: column; }
.bcard.grouped { background: var(--c-canvas); }
.bnav { height: 52px; display: grid; place-items: center; flex: none; }
.blaunch { flex: 1; display: grid; place-items: center; background: var(--brand-surface); }
.babout { padding: 14px 16px 4px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.babout .appicon { box-shadow: 0 0 0 1px var(--c-brand-edge); margin-bottom: 8px; }
.b2 { color: var(--c-on-brand-2); }
.bbadge { margin-top: 8px; height: 24px; padding: 0 10px 0 8px; display: inline-flex; align-items: center; gap: 6px; border-radius: 12px;
  border: 1px solid var(--c-border); color: var(--c-text-2); }
.bbadge i { width: 8px; height: 8px; border-radius: 50%; background: var(--brand-accent); }
.bcard .sg { margin-top: 20px; }
.bcard .sg-f { padding-top: 8px; }
.bempty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 0 28px 40px; text-align: center; }
.bempty .bpanel { margin-bottom: 18px; }
.bempty .pbtn { margin-top: 18px; align-self: stretch; }
.bexport { margin: 4px 16px 0; padding: 24px 16px 20px; display: flex; flex-direction: column; align-items: center; gap: 2px;
  background: var(--brand-surface); color: var(--c-on-brand); }
.bx-mark { margin: 8px 0 22px; }
.bx-t { display: flex; align-items: center; gap: 8px; }
.bx-ok { width: 20px; height: 20px; border-radius: 50%; display: grid; place-items: center; background: var(--c-success); color: var(--c-on-success); }
.bact { display: flex; flex-direction: column; gap: 8px; padding: 20px 16px 0; }
.palette { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
.measure { padding: 80px 40px 40px; } /* below the sheet: measured, never in preview.png */

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
.mbar { height: 6px; margin: 10px 0 8px; display: flex; gap: 2px; }
.mbar i { display: block; height: 100%; border-radius: 3px; }
.mbar .used { background: var(--c-primary); }
.mbar .rest { flex: 1; background: var(--c-surface-3); }
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

/* ---------- Android (Material 3, Roboto Flex, Material Symbols Rounded, FILL 1, 500) ---------- */
.android { width: 432px; }
.aframe { padding: 10px; border-radius: 48px; background: #0B0C0E; box-shadow: 0 0 0 1.5px #3A3B3E, 0 24px 56px rgba(15,17,21,.22); }
.ascreen { position: relative; width: 412px; height: 915px; border-radius: 38px; overflow: hidden; background: var(--c-bg); color: var(--c-text);
  font-family: "Roboto Flex", "Noto Sans SC", sans-serif; }
.ascreen [class^="m3-"] { font-family: "Roboto Flex", "Noto Sans SC", sans-serif; }
.ms { font-family: "Material Symbols Rounded"; font-style: normal; font-weight: normal; line-height: 1; display: inline-block; flex: none;
  overflow: hidden; white-space: nowrap; font-feature-settings: "liga"; font-variation-settings: "FILL" 1, "wght" 500, "GRAD" 0, "opsz" 24; }
.ms.ic { display: block; }
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

/* ---------- strip rows; the dialog's buttons and field (desktop sizes) ---------- */
.comp { padding: 16px 16px 16px; }
.comp-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.cs-h { font: 590 12px/16px var(--font); color: var(--c-text-2); padding: 10px 0 4px; }
.crow { display: flex; flex-direction: column; gap: 6px; padding: 8px 0 10px; border-top: 1px solid var(--c-border); }
.clab { font: var(--td-caption); color: var(--c-text-3); }
.cval { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.b { height: var(--control-h-md); padding: 0 12px; border-radius: var(--r-sm); display: inline-flex; align-items: center; gap: 6px;
  font: var(--td-body-medium); font-size: 13px; white-space: nowrap; }
.b.pri { background: var(--c-primary); color: var(--c-on-primary); }
.b.pri .kbds { margin-left: 2px; }
.b.pri.prs { background: var(--c-primary-pressed); }
.b.second { background: var(--c-surface-2); border: 1px solid var(--c-border); color: var(--c-text); }
.b .kbd { margin-left: 2px; }
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

/* ---------- right column: type scale, dialog ---------- */
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
/* ---------- phone pages: media, controls ---------- */
.screen.media, .ascreen.media { background: var(--c-media-black); color: var(--c-on-media); }
.ascreen.media .asb { background: var(--c-media-black); color: var(--c-on-media); }
.screen.grouped { background: var(--c-canvas); }
.photo { background-size: cover; background-position: center; }
.lnk { color: var(--c-primary-text); font-weight: 510; }
.gpill { position: relative; height: 44px; padding: 0 16px; border-radius: 22px; display: inline-flex; align-items: center; color: var(--c-text); }
.gpill b { font-weight: inherit; }
.gpill.prom { background: var(--c-primary); color: var(--c-on-primary); box-shadow: inset 0 1px 0 rgba(255,255,255,.22), var(--elev-2); }
.nbar { position: absolute; top: 54px; left: 16px; right: 16px; height: 44px; display: flex; align-items: center; justify-content: center; z-index: 4; }
.nbar .nb-l { position: absolute; left: 0; top: 0; }
.nbar .nb-r { position: absolute; right: 0; top: 0; }
.pbtn { height: var(--control-h-mobile-lg); padding: 0 16px; border-radius: var(--r-lg); display: flex; align-items: center; justify-content: center;
  gap: 8px; font: var(--t-card-title); white-space: nowrap; flex: none; }
.pbtn.pri { background: var(--c-primary); color: var(--c-on-primary); }
.pbtn.prs { background: var(--c-primary-pressed); color: var(--c-on-primary); }
.pbtn.second { background: var(--c-surface-2); border: 1px solid var(--c-border); color: var(--c-text); }
.pbtn.plain { color: var(--c-primary-text); font-weight: 510; }
.pbtn.sm { height: 36px; padding: 0 14px; font: var(--t-row-title); border-radius: 18px; }
.segc { height: 32px; padding: 2px; border-radius: var(--r-md); background: var(--c-surface-3); display: inline-flex; flex: none; }
.segc.full { flex: 1; }
.seg { flex: 1; min-width: 44px; padding: 0 10px; display: grid; place-items: center; border-radius: var(--r-sm); font: var(--t-row-meta);
  font-weight: 510; color: var(--c-text-2); white-space: nowrap; }
.seg.on { background: var(--c-elevated); color: var(--c-text); box-shadow: 0 0 0 .5px rgba(0,0,0,.06), 0 2px 6px rgba(0,0,0,.12); }
[data-theme="dark"] .seg.on { background: var(--c-menu-active); box-shadow: none; }
.stp { height: 32px; border-radius: var(--r-md); background: var(--c-surface-3); display: inline-flex; align-items: center; flex: none; }
.stp b { width: 40px; display: grid; place-items: center; font: 400 20px/1 var(--font); color: var(--c-text); }
.stp i { width: 1px; height: 18px; background: var(--c-border-strong); opacity: .5; }
.stp-row { width: 100%; display: flex; align-items: center; justify-content: space-between; }
.stp-row b { color: var(--c-text); font-weight: 510; }
.sw2 { position: relative; width: 51px; height: 31px; border-radius: 16px; background: var(--c-surface-3); flex: none;
  box-shadow: inset 0 0 0 1px var(--c-border-strong); }
.sw2::after { content: ""; position: absolute; left: 2px; top: 2px; width: 27px; height: 27px; border-radius: 50%; background: #FFFFFF;
  box-shadow: 0 0 0 .5px rgba(0,0,0,.08), 0 2px 6px rgba(0,0,0,.2); }
.sw2.on { background: var(--c-primary); box-shadow: none; }
.sw2.on::after { left: 22px; }
.rad { position: relative; width: 22px; height: 22px; border-radius: 50%; box-shadow: inset 0 0 0 1.5px var(--c-border-strong); flex: none; }
.rad.on { background: var(--c-primary); box-shadow: none; }
.rad.on::after { content: ""; position: absolute; inset: 7px; border-radius: 50%; background: var(--c-on-primary); }
.sl { position: relative; height: 32px; }
.sl-track, .sl-fill { position: absolute; top: 50%; height: var(--slider-track-h); margin-top: -2px; border-radius: 2px; }
.sl-track { left: 0; right: 0; background: var(--c-surface-3); }
.sl-fill { background: var(--c-primary); }
.sl-tick { position: absolute; left: 50%; top: 50%; width: 2px; height: var(--slider-tick-h); margin: -4px 0 0 -1px; border-radius: 1px; background: var(--c-text-3); }
.sl-thumb { position: absolute; top: 50%; width: var(--slider-thumb); height: var(--slider-thumb); margin: -12px 0 0 -12px; border-radius: 50%;
  background: #FFFFFF; box-shadow: 0 0 0 .5px rgba(0,0,0,.12), 0 2px 8px rgba(0,0,0,.25); }
.sl-head { display: flex; justify-content: space-between; align-items: baseline; }
.xbar { height: 6px; margin: 10px 0 8px; display: flex; gap: 2px; }
.xbar i { display: block; height: 100%; border-radius: 3px; }
.xbar .used { background: var(--c-primary); }
.xbar .rest { flex: 1; background: var(--c-surface-3); }
.grab { display: block; width: 36px; height: 5px; border-radius: 3px; background: var(--c-border-strong); opacity: .6; margin: 0 auto 12px; }
.art { position: relative; margin: 0 auto; flex: none; }
/* brand art: the icon's graphite, top-lit, the same in light and dark; the mark is the icon's own subject */
.bpanel { background: var(--brand-surface); border-radius: var(--r-xl); display: grid; place-items: center; overflow: hidden;
  box-shadow: 0 0 0 1px var(--c-brand-edge); }
.bp-mark, .bmark { display: block; }
.bpanel.over { display: flex; flex-direction: column; align-items: center; padding-bottom: 14px; }
.bpanel.over .bp-mark { flex: 1; display: grid; place-items: center; min-height: 0; padding-bottom: 24px; }
.bpanel.over .demo, .bpanel.over .notif { position: relative; left: auto; bottom: auto; margin: 0; flex: none; }
.pw .bpanel { margin-bottom: 6px; }
.ach .bpanel { margin-bottom: 20px; }
.demo { position: absolute; left: 50%; bottom: 4px; width: 288px; height: 64px; margin-left: -144px; padding: 0 16px; display: flex; align-items: center;
  gap: 12px; background: var(--c-elevated); color: var(--c-text); border: 1px solid var(--c-border); border-radius: var(--r-lg); box-shadow: var(--elev-2); }
.demo .pt span { color: var(--c-text-2); }

/* settings (inset grouped), paywall, consent */
.pc.set { padding-top: 98px; }
.sg-h { padding: 16px 32px 6px; color: var(--c-text-3); }
.sg { margin: 0 16px; background: var(--c-surface); border-radius: var(--r-lg); }
.sr { position: relative; height: var(--row-h-mobile-single); display: flex; align-items: center; gap: 8px; padding: 0 12px 0 16px; }
.sr + .sr::before { content: ""; position: absolute; top: 0; left: 16px; right: 0; height: 1px; background: var(--c-border); }
.sr .segc { margin-right: 4px; }
.sg-f { padding: 6px 32px 0; color: var(--c-text-3); }
.pw { position: absolute; inset: 0; padding: 112px 20px 34px; display: flex; flex-direction: column; } /* the panel starts under the close button */
.pw-title { text-align: center; margin-top: 10px; }
.pw-sub { text-align: center; color: var(--c-text-2); margin-top: 2px; }
.feats { display: flex; flex-direction: column; gap: 8px; margin: 16px 0 16px 12px; }
.feat { display: flex; align-items: center; gap: 10px; }
.feat .ic { color: var(--c-primary-text); }
.plans { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.plan-h { color: var(--c-text-3); margin: 2px 0 -2px 4px; }
.pw.credits .feats { margin: 12px 0 12px 12px; }
.pw.credits .plans { margin-bottom: 12px; }
.plan { height: 60px; padding: 0 16px; border-radius: var(--r-lg); border: 1px solid var(--c-border); background: var(--c-surface);
  display: flex; align-items: center; gap: 12px; }
.plan.on { border: 2px solid var(--c-primary-text); padding: 0 15px; }
.plan .pt { flex: 1; display: flex; flex-direction: column; gap: 1px; }
.plan .pt span { color: var(--c-text-2); }
.fine { margin-top: 10px; color: var(--c-text-3); text-align: center; }
.links { display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 6px; color: var(--c-text-2); }
.links i { width: 3px; height: 3px; border-radius: 50%; background: var(--c-text-3); }
.low { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 8px 12px; border-radius: var(--r-md);
  background: var(--c-warning-container); color: var(--c-warning); }
.low b { font-weight: 590; }
.pw .pbtn + .pbtn { margin-top: 6px; }
.conss { display: flex; flex-direction: column; gap: 14px; margin: 16px 4px 0; }
.cons { display: flex; gap: 14px; }
.cons p { color: var(--c-text-2); margin-top: 2px; }

/* Android shell: onboarding, permission pre-prompt, report sheet */
.onb { position: absolute; top: 44px; left: 0; right: 0; bottom: 28px; padding: 8px 24px 16px; display: flex; flex-direction: column; }
.onb-skip { align-self: flex-end; height: 48px; padding: 0 12px; display: grid; place-items: center; color: var(--c-text-2); margin-right: -12px; }
.onb.perm { padding-top: 56px; }
.dots { display: flex; gap: 8px; justify-content: center; margin: 24px 0 20px; }
.dots i { width: 8px; height: 8px; border-radius: 4px; background: var(--c-text-placeholder); }
.dots i.on { width: 20px; background: var(--c-text); }
.onb-t { color: var(--c-text); text-align: center; }
.perm .onb-t { margin-top: 28px; }
.onb-b { margin-top: 12px; color: var(--c-text-2); text-align: center; }
.onb-n { margin-top: 12px; text-align: center; }
.onb .pbtn + .pbtn { margin-top: 8px; }
.notif { position: absolute; left: 50%; bottom: 6px; width: 300px; margin-left: -150px; padding: 12px 16px 14px; display: flex; flex-direction: column;
  gap: 2px; background: var(--c-elevated); color: var(--c-text); border: 1px solid var(--c-border); border-radius: 20px; box-shadow: var(--elev-2); }
.nh { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.areply { padding: 16px; color: var(--c-text); }
.areply p + p { margin-top: 8px; }
.ascrim { position: absolute; inset: 0; background: var(--c-scrim); z-index: 4; }
.bsheet { position: absolute; left: 0; right: 0; bottom: 0; z-index: 5; padding: 0 24px 40px; background: var(--c-elevated); color: var(--c-text);
  border-radius: var(--r-xl) var(--r-xl) 0 0; }
.bgrab { display: block; width: 32px; height: 4px; border-radius: 2px; background: var(--c-border-strong); opacity: .6; margin: 16px auto 20px; }
.bsheet > .m3-bodyMedium { margin: 6px 0 8px; }
.rrow { height: 48px; display: flex; align-items: center; gap: 16px; }
.afield { height: 56px; margin: 8px 0 16px; padding: 0 16px; border: 1px solid var(--c-border-strong); border-radius: var(--r-sm); display: flex; align-items: center; }

/* editor */
.ed { position: absolute; inset: 0; display: flex; flex-direction: column; }
.ed-top { position: absolute; top: 54px; left: 16px; right: 16px; height: 44px; display: flex; align-items: center; justify-content: space-between; z-index: 4; }
.ed-top > b { position: absolute; left: 0; right: 0; text-align: center; pointer-events: none; }
.ed-canvas { position: relative; flex: none; margin-top: 104px; background: var(--c-media-dark); display: grid; place-items: center; overflow: hidden; }
.ed-canvas.checker { background: var(--checker-image) 0 0 / calc(2 * var(--checker-size)) calc(2 * var(--checker-size)); }
.ba { position: relative; width: 358px; height: 268px; }
.ba .photo, .before { position: absolute; inset: 0; }
.before { clip-path: inset(0 55% 0 0); }
.before .photo { filter: saturate(.45) brightness(.86) contrast(.9); }
.ba-line { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--c-on-media); box-shadow: 0 0 0 .5px var(--c-media-edge); }
.ba-knob { position: absolute; top: 50%; width: 36px; height: 36px; margin: -18px 0 0 -18px; border-radius: 50%; background: var(--c-on-media);
  color: var(--c-media-black); display: grid; place-items: center; box-shadow: var(--elev-2); }
.ba-chip { position: absolute; top: 12px; height: 24px; padding: 0 8px; border-radius: 12px; background: var(--c-viewer-scrim); color: var(--c-on-media);
  display: inline-flex; align-items: center; }
.ed-sl { padding: 12px 24px 0; }
.ed-sl .sl-head .t-timecode { color: var(--c-on-media); }
.tray { height: var(--tool-tray-h); display: flex; padding: 0 8px; margin-top: 10px; overflow: hidden; }
.tool { width: var(--tool-item-w); flex: none; display: flex; flex-direction: column; align-items: center; gap: 2px; color: var(--c-text-3); }
.tool-ic { width: 44px; height: 44px; border-radius: 22px; display: grid; place-items: center; }
.tool.set .tool-ic { box-shadow: inset 0 0 0 1.5px var(--c-surface-3); color: var(--c-text-2); }
.tool.on { color: var(--c-on-media); }
.tool.on .tool-ic { background: var(--c-surface-3); box-shadow: inset 0 0 0 1.5px var(--c-on-media); color: var(--c-on-media); }
.modes { display: flex; justify-content: center; gap: 28px; margin-top: 14px; }
.mode { color: var(--c-text-3); }
.mode.on { color: var(--c-on-media); }
.plant { display: block; }
.xsheet { position: absolute; left: 0; right: 0; bottom: 0; top: 446px; padding: 8px 20px 34px; background: var(--c-elevated); color: var(--c-text);
  border-radius: var(--r-xl) var(--r-xl) 0 0; display: flex; flex-direction: column; }
.xs-h { display: flex; align-items: center; gap: 8px; }
.qlist { margin-top: 8px; }
.qrow { height: var(--row-h-mobile-single); display: flex; align-items: center; gap: 10px; border-top: 1px solid var(--c-border); }
.qrow .t-row-meta { color: var(--c-text-2); }
.qrow .ip { color: var(--c-in-progress); }
.xs-note { display: flex; gap: 8px; align-items: center; color: var(--c-text-3); margin: 6px 0 12px; }
.atop.media { background: var(--c-media-black); border-bottom: 0; color: var(--c-on-media); }
.atop.media .aib { color: var(--c-on-media); }
.atext { height: 40px; padding: 0 12px; display: grid; place-items: center; color: var(--c-primary-text); }
.cr-canvas { position: absolute; top: 108px; left: 0; right: 0; height: 500px; overflow: hidden; }
.cr-canvas .photo { position: absolute; inset: 0; }
.cr-box { position: absolute; left: 40px; right: 40px; top: 50px; bottom: 50px; border: 1px solid var(--c-on-media); box-shadow: 0 0 0 999px var(--c-viewer-scrim); }
.cr-box .g { position: absolute; background: var(--c-media-guide); }
.g.v1, .g.v2 { top: 0; bottom: 0; width: 1px; }
.g.v1 { left: 33.33%; } .g.v2 { left: 66.67%; }
.g.h1, .g.h2 { left: 0; right: 0; height: 1px; }
.g.h1 { top: 33.33%; } .g.h2 { top: 66.67%; }
.hd { position: absolute; width: var(--crop-handle); height: var(--crop-handle); border: 0 solid var(--c-on-media); }
.hd.c-tl { left: -3px; top: -3px; border-width: var(--crop-stroke) 0 0 var(--crop-stroke); }
.hd.c-tr { right: -3px; top: -3px; border-width: var(--crop-stroke) var(--crop-stroke) 0 0; }
.hd.c-bl { left: -3px; bottom: -3px; border-width: 0 0 var(--crop-stroke) var(--crop-stroke); }
.hd.c-br { right: -3px; bottom: -3px; border-width: 0 var(--crop-stroke) var(--crop-stroke) 0; }
.eh { position: absolute; background: var(--c-on-media); border-radius: 2px; }
.eh.e-t, .eh.e-b { left: 50%; width: 24px; height: var(--crop-stroke); margin-left: -12px; }
.eh.e-t { top: -3px; } .eh.e-b { bottom: -3px; }
.eh.e-l, .eh.e-r { top: 50%; width: var(--crop-stroke); height: 24px; margin-top: -12px; }
.eh.e-l { left: -3px; } .eh.e-r { right: -3px; }
.dial { position: absolute; top: 620px; left: 0; right: 0; height: 56px; display: flex; flex-direction: column; align-items: center; }
.dial b { color: var(--c-on-media); }
.ticks { display: flex; gap: 6px; align-items: flex-end; height: 18px; margin-top: 8px; }
.ticks i { width: 1px; height: 8px; background: var(--c-text-3); }
.ticks i.big { height: 14px; background: var(--c-text-2); }
.dial-0 { position: absolute; bottom: 4px; left: 50%; width: 2px; height: 24px; margin-left: -1px; border-radius: 1px; background: var(--c-on-media); }
.achips.ratio { position: absolute; top: 690px; left: 0; right: 0; }
.cr-tools { position: absolute; bottom: 36px; left: 8px; right: 8px; height: 56px; display: flex; align-items: center; }

/* photo grid and viewer */
.limited { margin: 12px 16px 0; padding: 10px 12px; border-radius: var(--r-lg); background: var(--c-surface-2); display: flex; align-items: center;
  gap: 8px; color: var(--c-text-2); }
.limited .ic { color: var(--c-info); }
.pgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--thumb-gap); margin-top: 12px; }
.cell { position: relative; aspect-ratio: 1; }
.cell .photo { position: absolute; inset: 0; }
.cell.media-selected .photo { box-shadow: inset 0 0 0 var(--select-outline) var(--c-media-selected); }
.chk { position: absolute; right: 6px; bottom: 6px; }
.chk-off { position: absolute; right: 6px; bottom: 6px; width: 22px; height: 22px; border-radius: 50%; background: rgba(0,0,0,.12);
  box-shadow: inset 0 0 0 1.5px #FFFFFF, 0 0 2px rgba(0,0,0,.4); }
.gtool { position: absolute; left: 16px; right: 16px; bottom: 24px; height: 56px; border-radius: 28px; z-index: 3; display: flex; align-items: center;
  justify-content: space-between; padding: 0 20px; color: var(--c-text-2); }
.gtool b { color: var(--c-text); }
.vw { position: absolute; inset: 0; background: var(--c-media-black); }
.vw-photo { position: absolute; inset: 0; }
.vw-s { position: absolute; left: 0; right: 0; z-index: 2; }
.vw-s.top { top: 0; } .vw-s.bot { bottom: 0; }
.vw-bar { position: absolute; left: 8px; right: 8px; height: 44px; z-index: 3; display: flex; align-items: center; justify-content: space-between;
  color: var(--c-on-media); }
.vw-bar.top { top: 54px; }
.vw-bar.bot { bottom: 34px; padding: 0 12px; }
.vib { width: 44px; height: 44px; display: grid; place-items: center; }
.vw-t { display: flex; flex-direction: column; align-items: center; }
.vw-toast { bottom: 96px; }

/* chat and generation */
.pc.chat, .pc.gen { padding: 108px 16px 0; display: flex; flex-direction: column; }
.bub { align-self: flex-end; max-width: 286px; margin-top: 14px; padding: 8px 14px; border-radius: var(--r-xl); background: var(--c-surface-2);
  color: var(--c-text); }
.bub.img { padding: 0; background: none; }
.att { width: 96px; height: 128px; border-radius: var(--r-lg); }
.reply { margin-top: 14px; color: var(--c-text); }
.reply p + p { margin-top: 8px; }
.acts { display: flex; margin: 2px 0 0 -12px; }
.act { width: 44px; height: 44px; display: grid; place-items: center; color: var(--c-text-3); }
.caret-s { display: inline-block; width: 10px; height: 10px; margin-left: 6px; border-radius: 50%; background: var(--c-text); vertical-align: 1px; }
.model { display: inline-flex; align-items: center; gap: 4px; }
.credit { gap: 6px; padding: 0 14px 0 12px; }
.credit .ic { color: var(--c-text-2); }
.composer { position: absolute; left: 12px; right: 12px; bottom: 30px; z-index: 3; min-height: var(--prompt-min-h); padding: 4px 4px 4px 2px;
  border-radius: calc(var(--prompt-min-h) / 2); display: flex; align-items: flex-end; gap: 2px; }
.cbtn { width: 40px; height: 40px; display: grid; place-items: center; flex: none; color: var(--c-text-2); }
.composer .cfield { flex: 1; min-width: 0; margin: 8px 4px; line-height: 24px; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden;
  color: var(--c-text); }
.send { width: 40px; height: 40px; border-radius: 20px; display: grid; place-items: center; flex: none; background: var(--c-disabled-bg); color: var(--c-disabled-fg); }
.send.on { background: var(--c-primary); color: var(--c-on-primary); }
.send.stop { background: var(--c-text); }
.send.stop i { width: 12px; height: 12px; border-radius: 3px; background: var(--c-bg); }
.aspect { height: 28px; margin: 0 4px 6px; padding: 0 10px; border-radius: 14px; border: 1px solid var(--c-border-strong); display: inline-flex; align-items: center;
  flex: none; color: var(--c-text-2); }
.pcard { padding: 12px 14px; border-radius: var(--r-lg); background: var(--c-surface); border: 1px solid var(--c-border); }
.gchips { display: flex; gap: 6px; align-items: center; margin-top: 10px; }
.ggrid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
.gcell { position: relative; aspect-ratio: 1; border-radius: var(--r-lg); overflow: hidden; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 4px; }
.gcell .photo { position: absolute; inset: 0; }
.ring { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; color: var(--c-on-media); }
.ring b { text-shadow: 0 1px 2px rgba(0,0,0,.4); }
.gcell.fail { background: var(--c-surface-2); color: var(--c-text-2); }
.gcell.fail .t-row-meta { color: var(--c-text-3); }
.gcell.fail .pbtn { margin-top: 6px; }
.gcell.queue { background: var(--c-surface-2); color: var(--c-text); }
.gcell.queue .t-row-meta { color: var(--c-text-2); }
.refused { display: flex; gap: 12px; margin-top: 12px; padding: 12px 14px; border-radius: var(--r-lg); background: var(--c-surface-2); color: var(--c-text); }
.refused > .ic { flex: none; margin-top: 1px; color: var(--c-text-2); }
.refused p { margin: 2px 0 4px; color: var(--c-text-2); }
.model-chip { margin-left: 4px; }
.credit-chip { margin-right: 8px; }
.acontent.ach { padding: 20px 16px 0; display: flex; flex-direction: column; align-items: center; }
.ach-sub { margin-top: 6px; text-align: center; }
.samples { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 20px; width: 100%; }
.scard { border-radius: var(--r-lg); background: var(--c-surface); border: 1px solid var(--c-border); overflow: hidden; }
.scard .photo { height: 110px; }
.scard span { display: block; padding: 10px 12px; color: var(--c-text); }
.acomp { position: absolute; left: 12px; right: 12px; bottom: 40px; height: 56px; border-radius: 28px; background: var(--c-surface-3);
  display: flex; align-items: center; padding: 0 8px 0 4px; z-index: 3; }
.acomp .aib { width: 44px; }
.ph-t { color: var(--c-text-placeholder); }
.asend { width: 40px; height: 40px; border-radius: 20px; display: grid; place-items: center; background: var(--c-disabled-bg); color: var(--c-disabled-fg); }

/* ---------- phone component strip ---------- */
.ps { background: var(--c-bg); color: var(--c-text); border-radius: 10px; padding: 2px 12px 8px; box-shadow: 0 0 0 1px var(--c-border); }
.ps .crow { padding: 8px 0 10px; }
.ps .cval > .pbtn { flex: 1; padding: 0 6px; }
.ps .wrap { display: flex; gap: 6px; flex-wrap: wrap; width: 100%; }
.ps .tagp { height: 24px; }
.ps .badge { height: 24px; font: var(--t-tag-label); }
.ps .badge svg { width: 14px; height: 14px; }
.badge.info { background: var(--c-info-container); color: var(--c-info); }
.slw, .task { width: 100%; }
.task-h, .task-f { display: flex; align-items: center; gap: 8px; }
.task .xbar { margin: 8px 0 2px; }
.tbtn { height: 44px; display: grid; place-items: center; padding: 0 4px; margin: -10px 0 -12px; color: var(--c-text); }
.fin2 { flex: 1; min-width: 0; height: var(--control-h-mobile-md); padding: 0 12px; border-radius: 10px; background: var(--c-surface);
  border: 1px solid var(--c-border-strong); display: flex; align-items: center; color: var(--c-text-placeholder); white-space: nowrap; }
.fin2.focus { border-color: var(--c-focus); box-shadow: 0 0 0 1px var(--c-focus); color: var(--c-text); }
.cmenu { width: 100%; background: var(--c-elevated); border: 1px solid var(--c-border); border-radius: var(--r-lg); box-shadow: var(--elev-2); overflow: hidden; }
.cm { height: 44px; padding: 0 14px 0 16px; display: flex; align-items: center; gap: 10px; color: var(--c-text); }
.cm + .cm { border-top: 1px solid var(--c-border); }
.cm .ic { color: var(--c-text-2); }
.cm.danger { border-top: 6px solid var(--c-surface-2); }
.cm.danger, .cm.danger .ic { color: var(--c-danger); }
.tip { height: 26px; padding: 0 4px 0 8px; display: inline-flex; align-items: center; gap: 6px; border-radius: var(--r-sm);
  background: var(--c-inverse-surface); color: var(--c-on-inverse); font: var(--td-caption); }

/* ---------- right column: type scale, sheet, icon x UI; media swatches ---------- */
.sh-stage { position: relative; height: 420px; border-radius: 10px; overflow: hidden; display: flex; align-items: flex-end; justify-content: center;
  background: repeating-linear-gradient(180deg, var(--c-bg) 0 59px, var(--c-surface-2) 59px 60px); }
.sh-stage::before { content: ""; position: absolute; inset: 0; background: var(--c-scrim); }
.psheet { position: relative; width: 390px; padding: 8px 20px 18px; background: var(--c-elevated); color: var(--c-text);
  border-radius: var(--r-xl) var(--r-xl) 0 0; box-shadow: var(--elev-3); }
.sh-t { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.xbtn { width: 30px; height: 30px; border-radius: 15px; background: var(--c-surface-3); display: grid; place-items: center; color: var(--c-text-2); }
.shr { min-height: 52px; display: flex; align-items: center; gap: 12px; border-top: 1px solid var(--c-border); }
.shr.col { flex-direction: column; align-items: stretch; justify-content: center; gap: 0; padding: 8px 0 2px; }
.shr .pt { flex: 1; display: flex; flex-direction: column; }
.sh-act { display: flex; gap: 8px; margin-top: 14px; }
.sh-act .pbtn { flex: 1; }
.psheet > p { margin-top: 10px; text-align: center; }
.pminis { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pmini { padding: 12px; border-radius: 14px; background: var(--c-bg); color: var(--c-text); box-shadow: 0 0 0 1px rgba(0,0,0,.12);
  display: flex; flex-direction: column; gap: 12px; }
.pm-top { display: flex; align-items: center; gap: 10px; }
.pm-top .appicon { box-shadow: 0 0 0 1px var(--c-border); }
.pm-tabs { height: 56px; border-radius: 28px; padding: 3px; display: flex; }
.pm-tabs .tab { border-radius: 25px; }
.mpanel { grid-column: 1 / -1; }
.msws { display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 14px; }
.msw { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.msw > i { position: relative; height: 64px; border-radius: 8px; box-shadow: inset 0 0 0 1px rgba(127,127,127,.28); overflow: hidden; display: block; }
.msw > i.scr { display: grid; place-items: center; background: linear-gradient(var(--c-viewer-scrim), var(--c-viewer-scrim)), #FFFFFF; }
.msw > i.scr b { font: 590 20px/1 var(--font); color: var(--c-on-media); }
.msw > i.guide { background: linear-gradient(90deg, transparent 33%, var(--c-media-guide) 33% calc(33% + 1px), transparent 0 66%,
  var(--c-media-guide) 66% calc(66% + 1px), transparent 0), var(--c-media-mid); }
.sel-demo { position: absolute; inset: 0; box-shadow: inset 0 0 0 var(--select-outline) var(--c-media-selected); border-radius: 8px; }
.playhead { position: absolute; left: 50%; top: 8px; bottom: 22px; width: var(--playhead-w); background: var(--c-primary); }
.scrub { position: absolute; left: 10px; right: 10px; bottom: 9px; height: var(--slider-track-h); border-radius: 2px; background: var(--c-media-track); }
.scrub b { display: block; width: 62%; height: 100%; border-radius: 2px; background: var(--c-on-media); }
.playhead::before { content: ""; position: absolute; left: 50%; top: -2px; width: var(--playhead-knob); height: var(--playhead-knob);
  margin-left: calc(var(--playhead-knob) / -2); border-radius: 50%; background: var(--c-primary); }
.msw b { font: 510 11px/14px var(--font); color: #1B1C1D; }
.msw span { font: 400 10.5px/14px var(--font); color: #55575A; font-variant-numeric: tabular-nums; }
"""


def m3_css(t):
    """Material 3 type scale from tokens.json (sp = px here)"""
    out = ""
    for k, v in t["font"]["android"]["scale"].items():
        out += (f'.m3-{k} {{ font-size: {v["size"]}px; line-height: {v["line"]}px; font-weight: {v["weight"]}; '
                f'letter-spacing: {v["tracking"]:g}px; }}\n')
    return out


# ---------- the sheet ----------
LIST_SCREENS = ("timer", "notes", "list")


def rows_for(screen, scr, icon, app):
    """the six phones of the sheet: the sample screen (row 1) and the shell or media screens (row 2)"""
    if screen in LIST_SCREENS:
        return ([ios_phone(screen, scr, "light", icon, caption="<b>iPhone · 浅色</b> · 静止态；筛选 pill 视觉高 36，点击区补到 44"),
                 ios_phone(screen, scr, "dark", icon, scrolled=True, toast=True, pid="ios-dark",
                           caption="<b>iPhone · 深色</b> · 滚动态：内容在玻璃栏下面，toast 是自定义浮层"),
                 android(screen, scr, "light", caption="<b>Android · 浅色</b> · M3：TopAppBar 不透明，滚动后只加 1 px border")],
                [settings_ios(scr, "light", app, caption="<b>iPhone · 浅色 · 设置</b> · 固定顺序：通用、外观、语言、会员、支持、关于"),
                 paywall_ios(scr, "dark", icon, app, caption="<b>iPhone · 深色 · 付费墙</b> · 恢复购买、条款、隐私、价格和自动续费写清楚"),
                 onboarding_android(scr, "light", caption="<b>Android · 浅色 · 引导</b> · 最多 3 屏，第一屏就演示核心功能")])
    if screen == "editor":
        return ([editor_adjust_ios(scr, caption="<b>iPhone · 编辑</b> · 系统浅色也强制深色；画布 media-dark（L 18，彩度 0）；前后对比；滑块 0 点吸附"),
                 editor_cutout_ios(scr, caption="<b>iPhone · 抠图和导出</b> · 棋盘格；长任务：确定进度、剩余时间、取消、后台继续"),
                 editor_crop_android(scr, caption="<b>Android · 裁剪</b> · 白色手柄和三分线，框外压暗；比例 chip 选中是中性色")],
                [grid_ios("light", caption="<b>iPhone · 浅色 · 图库</b> · 选中是描边加勾，不叠浅蓝底；受限访问时说明并给「管理」"),
                 viewer_ios(caption="<b>iPhone · 查看</b> · 白色控件在固定深色渐变上，不用玻璃；轻点画面隐藏"),
                 permission_android("light", icon, app, caption="<b>Android · 浅色 · 权限预请求</b> · 先用自己的一屏讲为什么，再弹系统对话框")])
    return ([chat_ios(scr, "light", caption="<b>iPhone · 浅色 · 对话</b> · 用户气泡 surface-2，回复不加气泡；操作行里有举报"),
             generate_ios(scr, "dark", caption="<b>iPhone · 深色 · 生成</b> · 完成、生成中、失败可重试、排队；被拒的提示词；生成时是停止键"),
             chat_android(scr, "light", caption="<b>Android · 浅色 · 新对话</b> · 空状态放示例图和示例提示词；没有字时发送键禁用")],
            [consent_ios("light", caption="<b>iPhone · 浅色 · 第三方 AI 同意</b> · 发什么、发给谁、存多久，可以拒绝"),
             paywall_ios(scr, "dark", icon, app, credits=True, caption="<b>iPhone · 深色 · 付费墙（点数）</b> · 余额不足时出现；订阅和点数包同一个组件"),
             report_android(scr, "light", caption="<b>Android · 浅色 · 举报</b> · app 内举报 AI 生成的内容")])


def measure_phones(screen, icon):
    """off the sheet: list content under the glass (both modes), a photo grid under the glass, a bright photo under the
    viewer scrim"""
    name = screen if screen in LIST_SCREENS else "timer"
    scr = SCREENS[name]
    return (ios_phone(name, scr, "light", icon, scrolled=True, pid="m-frost-light")
            + ios_phone(name, scr, "dark", icon, scrolled=True, pid="m-frost-dark")
            + grid_ios("light", pid="m-photo-light", scrolled=True) + grid_ios("dark", pid="m-photo-dark", scrolled=True)
            + viewer_ios("bright", 5, pid="m-viewer", toast=False))


def page(t, theme_css, screen, icon, desk_mode, with_desktop=False, fonts_css="", font_note=""):
    scr = SCREENS[screen]
    app = t["name"]
    s = t["source"]
    warm = "icon-accent" in s
    L, Dk = t["color"]["light"], t["color"]["dark"]
    accent = f'图标强调色 <b>{s.get("icon-accent", s["accent"])}</b> → 界面主色 <b>{s["accent"]}</b>'
    if s.get("category"):
        accent = f'类别 <b>{s["category"]}</b> · ' + accent
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    head = (f'<div class="bhead">{icon(48, "light")}<div><h1>{app} · 主题预览</h1>'
            f'<p>{accent} · primary {Dk["primary"]}（深浅同值，按下 {Dk["primary-pressed"]}）· '
            f'primary-text 深 {Dk["primary-text"]} / 浅 {L["primary-text"]} · 中性色 LCh 色相 {t["base"]["hue"]} · '
            f'样例界面 {scr["label"]}（--screen {screen}）· {font_note} · 生成于 {now}'
            + ("" if icon.given else " · <b>未传 --icon，图标处是占位图</b>") + "</p></div></div>")
    row1, row2 = rows_for(screen, scr, icon, app)
    comp = (f'<div class="panel comp"><h3>组件条 · 手机尺寸</h3><div class="comp-cols">{strip("light", scr)}{strip("dark", scr)}</div>'
            f'<div class="note2">按钮高 50、圆角 12；分段 32；开关 51 × 31；点击区 44（Android 48）。最后一行是可选层，只在 iPad / Mac 接键盘时出现</div></div>')
    if warm:
        extra = (f'<div class="panel"><h3>图标 × 界面</h3><div class="iu-head">{icon(72, "light")}'
                 f'<p><b>{s["icon-accent"]}只留在图标和品牌插图里，界面主色回落到{s["accent"]}。</b>primary {Dk["primary"]} · primary-text 深 '
                 f'{Dk["primary-text"]} / 浅 {L["primary-text"]}。图标底和界面中性色是同一种石墨（色相 {t["base"]["hue"]}）。</p></div>'
                 f'<div class="pminis">{phone_mini(screen, scr, "light", icon, app)}{phone_mini(screen, scr, "dark", icon, app)}</div></div>')
    else:
        extra = (f'<div class="panel"><h3>底部弹窗 · 深色</h3>{sheet(scr, "dark")}'
                 f'<div class="note2">elevated、顶部圆角 16、elev-3、遮罩 scrim；主按钮一屏一个</div></div>')
    rcol = (f'<div class="rcol"><div class="panel"><h3>手机字号 · Inter 代替 SF Pro（浅色）</h3>{phone_type_scale(t, "light", scr)}</div>'
            f'{extra}</div>')
    desk = ""
    if with_desktop:
        other = "light" if desk_mode == "dark" else "dark"
        q = scr["desktop"]["cmdk"]["query"]
        desk = (f'<div class="desk">{desktop(screen, scr, desk_mode, icon, app)}<div class="cap"><b>桌面 · {MODE_NAME[desk_mode]}（可选，--desktop）</b>'
                f' · 1280 × 800，倒 L 布局；第二行是键盘光标行（surface-2），两行多选（selected）；⌘K 输入「{q}」，'
                f'当前项 menu-active，遮罩 scrim-menu；视图头不放主色按钮</div></div>'
                f'<div class="rcol"><div class="panel"><h3>桌面字号 · Inter（{MODE_NAME[other]}）</h3>{desktop_type_scale(t, other, scr)}</div>'
                f'<div class="panel"><h3>弹窗 · {MODE_NAME[desk_mode]}</h3>{dialog(scr, desk_mode, app)}'
                f'<div class="note2">elevated、圆角 16、elev-3、遮罩 scrim；primary 填充只用在弹窗和表单的确认上</div></div></div>')
    pal = f'{brand_row(t, screen, icon, app)}<div class="palette">{swatches(t, scr)}</div>{media_strip(t)}'
    measure = f'<div class="measure">{measure_phones(screen, icon)}</div>'
    css = (fonts_css + "\n" + theme_css + "\n" + CSS.replace("@@W@@", str(BOARD_W)) + m3_css(t) + icon.css() + Photos.css())
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>'
            f'<body><div class="board">{head}{"".join(row1)}{comp}{"".join(row2)}{rcol}{desk}{pal}</div>{measure}</body></html>')


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
        return "", "字体：本机（离线；界面图标退回 Lucide 线性 2.25 px）", False
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
    note = "字体 Inter 可变 + Noto Sans SC（iPhone 屏用 Inter 代替 SF Pro），Android 屏 Roboto Flex；界面图标 Material Symbols Rounded 实心 500（iPhone 屏代替 SF Symbols .fill）"
    if miss:
        note = "字体缺 " + "、".join(m.split("（")[0] for m in miss) + "，用本机字体代替" + (
            "；界面图标退回 Lucide 线性 2.25 px" if not msr else "")
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
  add('.board .phone .gbtn', 'iOS glass button'); add('.board .phone .ppill', 'iOS filter pill'); add('.board .phone .prow', 'iOS row');
  add('.board .phone .tabbar', 'iOS tab bar'); add('#ios-dark .ptoast', 'iOS toast'); add('.board .sr', 'iOS settings row');
  add('.board .android .atop', 'M3 TopAppBar'); add('.board .android .achip', 'M3 FilterChip'); add('.board .android .arow', 'M3 list item');
  add('.board .android .afab', 'M3 FAB'); add('.board .android .anav', 'M3 NavigationBar + inset');
  add('.ps .pbtn', 'phone button'); add('.ps .segc', 'segmented'); add('.ps .stp', 'stepper'); add('.ps .sw2', 'switch');
  add('.ps .sl-thumb', 'slider thumb'); add('.ps .cm', 'context menu item'); add('.board .plan', 'paywall plan');
  add('.board .tool', 'tool item'); add('.board .tray', 'tool tray'); add('.board .hd', 'crop handle'); add('.board .chk', 'select check');
  const pf = document.querySelector('.board .composer'); if (pf) out['prompt field min-height'] = getComputedStyle(pf).minHeight;
  add('.board .send', 'send button'); add('.board .act', 'reply action');
  add('.win .r', 'desktop row'); add('.win .si', 'sidebar item'); add('.win .ci', 'command item'); add('.win .kbd', 'kbd');
  return out; }"""
# each phone on the sheet: its label and whether it is a conversion screen; data-idx lets Python take its screenshot
PHONES = """() => [...document.querySelectorAll('.board [data-label]')].map((s, i) => { s.dataset.idx = i;
  return {label: s.dataset.label, conversion: s.hasAttribute('data-conversion')}; })"""
# the accent area is measured with photos, canvases, generated images and brand art hidden: what shows through is the
# neutral page or canvas, and the checks and outlines drawn over the photos still count
HIDE_PHOTOS = "[data-photo], [data-brand] { visibility: hidden !important; }"
# full-screen pages and sheets whose content must end above the home indicator (iOS) or the gesture bar (Android):
# the last child's bottom against the container's bottom padding
SAFE = """() => [...document.querySelectorAll('.board [data-label]')].flatMap(s =>
  [...s.querySelectorAll('.pw, .onb, .xsheet, .bsheet')].map(el => { const r = el.getBoundingClientRect();
    const end = Math.max(...[...el.children].map(c => c.getBoundingClientRect().bottom));
    return [s.dataset.label, Math.round(end - (r.bottom - parseFloat(getComputedStyle(el).paddingBottom)))]; }))"""
# scrolled screens: the iPhone content moves up until a section header sits under the nav bar, with rows still
# under the tab bar; the Android content until the filter chips meet the TopAppBar; the photo grid to the top edge
SCROLL = """() => document.querySelectorAll('[data-scroll]').forEach(c => {
  const screen = c.parentElement.clientHeight, kind = c.dataset.scroll;
  let a = c.querySelector('.' + kind), top = 0;
  if (kind === 'psh') {  // iPhone: the deepest header that still leaves 60 px of rows under the tab bar
    top = 104;
    for (const h of c.querySelectorAll('.psh')) if (c.offsetHeight - h.offsetTop + top >= screen + 60) a = h;
  }
  c.style.transform = `translateY(${top - a.offsetTop}px)`; })"""
# the frost and scrim checks hide the bar text and the iOS scroll edge effect: the glass (or the viewer scrim) alone
# over the raw content
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
    """the share of the image in the primary's hue: strong (chroma >= 20) and incl. the faint selected tint (>= 4)"""
    import numpy as np
    chroma, h = lch_arrays(img)
    near = np.abs((h - hue + 180) % 360 - 180) <= HUE_BAND
    return float((near & (chroma >= STRONG_CHROMA)).mean() * 100), float((near & (chroma >= FAINT_CHROMA)).mean() * 100)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="theme folder written by build.py (reads tokens.json and theme.css, writes preview.png)")
    ap.add_argument("--screen", choices=list(SCREENS), default="timer",
                    help="sample screen: timer (default), notes, list, editor or chat")
    ap.add_argument("--icon", metavar="PNG", help="app icon, rian-app-icon's <name>-1024.png (default appearance)")
    ap.add_argument("--icon-dark", metavar="PNG", help="dark app icon for the dark UI, render.py --variants' <name>-dark.png (default: --icon)")
    ap.add_argument("--mark", metavar="PNG|SVG", help="the icon's subject for brand art, render.py --variants' <name>-mark.png "
                    "(default: the <name>-mark.png next to --icon, else keyed out of --icon)")
    ap.add_argument("--desktop", action="store_true", help="add the desktop window, its type scale and a dialog (timer, notes and list)")
    ap.add_argument("--desktop-mode", choices=("dark", "light"), default="dark", help="mode of the desktop window (default dark)")
    ap.add_argument("--offline", action="store_true", help="skip Google Fonts and use the locally installed fonts")
    ap.add_argument("--scale", type=float, default=2, help="device scale factor of the screenshot (default 2)")
    a = ap.parse_args()
    if a.desktop and "desktop" not in SCREENS[a.screen]:
        ap.error("--desktop works with --screen timer, notes or list; editor and chat are phone pages")

    t = json.load(open(os.path.join(a.out, "tokens.json"), encoding="utf-8"))
    theme_css = open(os.path.join(a.out, "theme.css"), encoding="utf-8").read()
    for p in (a.icon, a.icon_dark, a.mark):
        if p and not os.path.isfile(p):
            sys.exit(f"icon not found: {p}")
    s = t["source"]
    tones = PALETTE["accent"].get(s.get("icon-accent", s["accent"]), PALETTE["accent"]["蓝"])["tones"]
    icon = AppIcon(a.icon, a.icon_dark, tones)
    Dk = t["color"]["dark"]
    Brand.mark = BrandMark(a.mark, a.icon, (Dk["brand-accent-light"], Dk["brand-accent"]))
    Brand.category = s.get("category", "")

    draft = page(t, theme_css, a.screen, icon, a.desktop_mode, a.desktop)  # collects the characters and symbols in use
    fonts_css, note, Glyphs.msr = fonts(draft, a.offline)
    html = page(t, theme_css, a.screen, icon, a.desktop_mode, a.desktop, fonts_css, note)
    out = os.path.join(a.out, "preview.png")

    glass = {"frost light": "#m-frost-light .screen", "frost dark": "#m-frost-dark .screen",
             "frost photo light": "#m-photo-light .screen", "frost photo dark": "#m-photo-dark .screen", "viewer scrim": "#m-viewer .screen"}
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
        safe = pg.evaluate(SAFE)
        phones = pg.evaluate(PHONES)
        full = [png_array(pg.locator(f'.board [data-idx="{i}"]').screenshot()) for i in range(len(phones))]
        hidden = pg.add_style_tag(content=HIDE_PHOTOS)
        shots = [png_array(pg.locator(f'.board [data-idx="{i}"]').screenshot()) for i in range(len(phones))]
        hidden.evaluate("e => e.remove()")
        items = {k: pg.evaluate(BAR_ITEMS, sel) for k, sel in glass.items()}
        pg.add_style_tag(content=HIDE_BAR)  # the glass or the scrim alone, behind where the bar text was
        backs = {k: png_array(pg.locator(sel).screenshot()) for k, sel in glass.items()}
        if a.desktop:
            pg.add_style_tag(content="[data-bar], .edge, .edge-top { visibility: visible !important; } " + HIDE_MENU)
            desk = png_array(pg.locator(".board .win").screenshot())
        b.close()
    print("wrote", out)
    print("sizes: " + "; ".join(f"{k} {v}" for k, v in sizes.items()))

    fails = 0
    for k in glass:
        text, c = frost_check(backs[k], items[k], a.scale)
        need = SCRIM_MIN if k == "viewer scrim" else FROST_MIN
        what = {"frost light": "list content scrolled under the glass", "frost dark": "list content scrolled under the glass",
                "frost photo light": "a photo grid scrolled under the glass", "frost photo dark": "a photo grid scrolled under the glass",
                "viewer scrim": "white viewer controls over a bright photo, through the scrim"}[k]
        ok = c >= need
        fails += not ok
        print(f"{k}: lowest contrast {c:.1f}:1 ({text}; {what}); target >= {need:g}  {'PASS' if ok else 'FAIL'}")
    hue = hex_to_lch(t["color"]["dark"]["primary"])[2]
    area = [(ph_["label"], ph_["conversion"]) + accent_area(img, hue) + accent_area(whole, hue)[:1]
            for ph_, img, whole in zip(phones, shots, full)]
    for conv, limit, name in ((False, PHONE_MAX, "phone"), (True, CONVERSION_MAX, "conversion")):
        group = [r for r in area if r[1] == conv]
        if not group:
            continue
        worst = max(group, key=lambda r: r[2])
        ok = worst[2] <= limit
        fails += not ok
        print(f"accent area {name}: {worst[2]:.1f}% ({worst[0]}, the highest of " + ", ".join(f"{r[0]} {r[2]:.1f}%" for r in group)
              + f"; photos, canvases, generated images and brand art hidden); target <= {limit:g}%  {'PASS' if ok else 'FAIL'}")
        print("  INFO incl. the selected tint: " + ", ".join(f"{r[0]} {r[3]:.1f}%" for r in group))
        media = [r for r in group if r[4] - r[2] >= 0.5]
        if media:
            print("  INFO with the photos and brand art counted: " + ", ".join(f"{r[0]} {r[4]:.1f}%" for r in media))
    pushed = [f"{label} +{px} px" for label, px in safe if px > 0]
    fails += bool(pushed)
    print(f"safe area: {len(safe)} pages and sheets, " + (", ".join(pushed) + " into the home indicator or gesture bar  FAIL"
                                                          if pushed else "all end above the home indicator or gesture bar  PASS"))
    if a.desktop:
        strong, faint = accent_area(desk, hue)
        ok = strong <= DESK_MAX
        fails += not ok
        print(f"accent area desktop: {strong:.1f}% of the window in the primary hue (command menu hidden); "
              f"target <= {DESK_MAX:g}%  {'PASS' if ok else 'FAIL'}")
        print(f"  INFO incl. the selected tint: {faint:.1f}%")
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
