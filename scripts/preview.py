#!/usr/bin/env python3
"""Render a review sheet for a generated theme: the same sample screen in light and dark, plus swatches.

    python3 scripts/preview.py out/ [--icon path/to/icon-1024.png]

Writes out/preview.png. Needs Playwright + Chromium (same setup as rian-app-icon's render.py;
set CHROMIUM_PATH to use an existing Chromium).
"""
import argparse, base64, glob, json, os

# line icons on a 24 grid, Lucide-style: round caps and joins, stroke from the theme
ICONS = {
    "home": '<path d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z"/>',
    "chart": '<path d="M5 20v-8M12 20V5M19 20v-5"/>',
    "compass": '<circle cx="12" cy="12" r="8"/><path d="m15 9-2 4-4 2 2-4z"/>',
    "sliders": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    "timer": '<circle cx="12" cy="13" r="7"/><path d="M12 9.5V13l2.5 1.5M10 3h4"/>',
    "book": '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5zM13 4h5.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H13z"/>',
    "review": '<path d="M20 12a8 8 0 1 1-2.3-5.6M20 4v4h-4"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "chev": '<path d="m9 6 6 6-6 6"/>',
}

STATUS_GLYPHS = ('<svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor">'
                 '<rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/>'
                 '<rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>'
                 '<svg width="26" height="12" viewBox="0 0 26 12"><rect x=".5" y=".5" width="22" height="11" rx="3.5" '
                 'fill="none" stroke="currentColor" stroke-opacity=".4"/><rect x="2.5" y="2.5" width="16" height="7" rx="2" '
                 'fill="currentColor"/><path d="M24.5 4v4" stroke="currentColor" stroke-opacity=".4" stroke-linecap="round"/></svg>')


def ic(name, cls=""):
    return f'<svg class="icon {cls}" viewBox="0 0 24 24">{ICONS[name]}</svg>'


PHONE = """
<div class="phone" data-theme="{mode}">
  <div class="frame"><div class="screen">
    <header class="nav frost">
      <div class="status t-subhead"><b>9:41</b><span class="glyphs">{status}</span></div>
      <div class="row between"><span class="t-callout link">编辑</span>{icon}<span class="link row">{plus}</span></div>
      <h1 class="t-large-title">{name}</h1>
    </header>
    <main>
      <section class="card hero">
        <div class="t-footnote muted">本周</div>
        <div class="t-title-1">12 / 20</div>
        <div class="bar"><i style="width:60%"></i></div>
        <div class="t-subhead muted">再完成 8 次就达成目标</div>
      </section>
      <div class="seg"><span class="on t-subhead">今天</span><span class="t-subhead">本周</span><span class="t-subhead">本月</span></div>
      <section class="card list">
        <div class="li"><i class="tile">{timer}</i><div><div class="t-body">深度工作</div><div class="t-footnote muted">25 分钟 · 已完成</div></div><span class="chev">{chev}</span></div>
        <div class="li"><i class="tile">{book}</i><div><div class="t-body">阅读</div><div class="t-footnote muted">40 分钟 · 进行中</div></div><span class="chev">{chev}</span></div>
        <div class="li"><i class="tile">{review}</i><div><div class="t-body">复盘</div><div class="t-footnote faint">未开始</div></div><span class="chev">{chev}</span></div>
      </section>
      <div class="chips">
        <span class="chip success t-caption">已完成</span><span class="chip warning t-caption">将到期</span>
        <span class="chip danger t-caption">已超时</span><span class="chip info t-caption">新功能</span>
      </div>
      <button class="btn primary t-headline">开始专注</button>
      <button class="btn line t-headline">稍后提醒</button>
    </main>
    <nav class="tabs frost">
      <span class="tab is-active">{home}<b class="t-caption">首页</b></span><span class="tab">{chart}<b class="t-caption">统计</b></span>
      <span class="tab">{compass}<b class="t-caption">发现</b></span><span class="tab">{sliders}<b class="t-caption">设置</b></span>
    </nav>
  </div></div>
  <div class="label t-footnote">{mode}</div>
</div>"""

STYLE = """
* { box-sizing: border-box; margin: 0; }
body { width: 1080px; padding: 40px; background: #F0F0EE; font-family: var(--font); display: flex; flex-direction: column; gap: 32px; }
.phones { display: flex; gap: 48px; justify-content: center; }
.phone { color: var(--c-text); text-align: center; }
.frame { padding: 10px; border-radius: 64px; background: #0A0A0B;
  box-shadow: 0 0 0 1.5px #3A3A3C, 0 24px 48px rgba(15,15,15,.16); }
.screen { position: relative; width: 390px; height: 844px; border-radius: 54px; overflow: hidden; text-align: left;
  background: var(--c-bg); filter: brightness(1); /* backdrop root: frost blurs the screen, not the bezel */ }
.label { margin-top: 26px; color: #8E8E93; text-transform: uppercase; letter-spacing: .12em; }
.status { display: flex; justify-content: space-between; align-items: center; padding: 0 14px; height: 50px; }
.glyphs { display: flex; gap: 6px; align-items: center; }
.nav { position: relative; z-index: 2; padding: 0 16px 12px; border-width: 0 0 1px; }
.nav h1 { margin-top: 4px; }
.row { display: flex; align-items: center; } .between { justify-content: space-between; }
.nav img { width: 30px; height: 30px; border-radius: 7px; box-shadow: 0 0 0 1px var(--c-border); }
.link { color: var(--c-primary); }
main { padding: 16px 16px 0; display: flex; flex-direction: column; gap: 12px; }
.card { background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-lg); box-shadow: var(--elev-1); }
.hero { padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.muted { color: var(--c-text-2); } .faint { color: var(--c-text-3); }
.bar { height: 6px; border-radius: var(--r-full); background: var(--c-surface-2); overflow: hidden; margin: 6px 0 4px;
  box-shadow: inset 0 0 0 1px var(--c-border); }
.bar i { display: block; height: 100%; border-radius: var(--r-full); background: var(--c-primary); }
.seg { display: flex; padding: 3px; gap: 3px; border-radius: var(--r-md); border: 1px solid var(--c-border); background: var(--c-surface); }
.seg span { flex: 1; text-align: center; padding: 5px 0; border-radius: var(--r-sm); color: var(--c-text-2); }
.seg .on { background: var(--c-primary-container); color: var(--c-on-primary-container); font-weight: 600; }
.list { padding: 0 0 0 16px; }
.li { position: relative; display: flex; align-items: center; gap: 12px; padding: 11px 16px 11px 0; }
.li + .li::before { content: ""; position: absolute; top: 0; left: 44px; right: 0; height: 1px; background: var(--c-border); }
.li > div { flex: 1; }
.tile { width: 32px; height: 32px; border-radius: var(--r-md); border: 1px solid var(--c-border); color: var(--c-text-2);
  display: grid; place-items: center; flex: none; }
.chev { color: var(--c-text-3); display: flex; }
.chips { display: flex; gap: 8px; }
.chip { padding: 3px 10px; border-radius: var(--r-full); }
.chip.success { background: var(--c-success-container); color: var(--c-success); }
.chip.warning { background: var(--c-warning-container); color: var(--c-warning); }
.chip.danger { background: var(--c-danger-container); color: var(--c-danger); }
.chip.info { background: var(--c-info-container); color: var(--c-info); }
.btn { border: 0; height: 50px; border-radius: var(--r-lg); font-family: var(--font); }
.btn.primary { background: var(--c-primary); color: var(--c-on-primary); }
.btn.line { background: var(--c-surface); color: var(--c-text); border: 1px solid var(--c-border); box-shadow: var(--elev-1); }
.tabs { position: absolute; left: 20px; right: 20px; bottom: 28px; height: 62px; border-radius: var(--r-full);
  display: flex; justify-content: space-around; align-items: center; box-shadow: var(--elev-2); }
.tab { display: flex; flex-direction: column; align-items: center; gap: 2px; color: var(--c-text-3); }
.tab b { font-weight: 500; }
.tab.is-active { color: var(--c-primary); }
.swatches { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
.sw { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; padding: 14px; border-radius: var(--r-xl);
  background: var(--c-bg); border: 1px solid var(--c-border); }
.sw div { height: 54px; border-radius: var(--r-md); display: flex; align-items: flex-end; padding: 4px 6px; font: 500 9px var(--font);
  box-shadow: inset 0 0 0 1px rgba(127,127,127,.18); }
.title { font: 600 15px var(--font); color: #1C1C1E; margin-bottom: 10px; }
"""

SWATCH_KEYS = ["bg", "surface", "surface-2", "border", "text", "text-2", "text-3", "primary",
               "on-primary", "primary-container", "success", "warning", "danger", "info", "frost", "frost-border"]


def label(c, mode):
    if not c.startswith("#"):  # translucent: drawn over the page colour
        return "#1C1C1E" if mode == "light" else "#F5F5F7"
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return "#000" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#fff"


def find_chromium():
    p = os.environ.get("CHROMIUM_PATH")
    if p:
        return p
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--icon")
    a = ap.parse_args()
    t = json.load(open(os.path.join(a.out, "tokens.json"), encoding="utf-8"))
    theme_css = open(os.path.join(a.out, "theme.css"), encoding="utf-8").read()
    icon = ""
    if a.icon:
        icon = f'<img src="data:image/png;base64,{base64.b64encode(open(a.icon, "rb").read()).decode()}">'
    icons = {"plus": ic("plus"), "timer": ic("timer", "md"), "book": ic("book", "md"), "review": ic("review", "md"),
             "chev": ic("chev", "sm"), "home": ic("home"), "chart": ic("chart"), "compass": ic("compass"), "sliders": ic("sliders")}
    phones = "".join(PHONE.format(mode=m, name=t["name"], icon=icon, status=STATUS_GLYPHS, **icons)
                     for m in ("light", "dark"))
    s = t["source"]
    src = f'{s["accent"]} {s["en"]}' + (f' · 图标 {s["icon-accent"]}' if "icon-accent" in s else "")
    sw = ""
    for m in ("light", "dark"):
        C = t["color"][m]
        cells = "".join(f'<div style="background:{C[k]};color:{label(C[k], m)}">{k}</div>' for k in SWATCH_KEYS)
        sw += f'<div data-theme="{m}"><div class="title">{m} · {src}</div><div class="sw">{cells}</div></div>'
    html = f"<html><head><style>{theme_css}{STYLE}</style></head><body><div class='phones'>{phones}</div><div class='swatches'>{sw}</div></body></html>"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        kw = {"executable_path": find_chromium()} if find_chromium() else {}
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": 1080, "height": 800}, device_scale_factor=2)
        pg.set_content(html)
        pg.screenshot(path=os.path.join(a.out, "preview.png"), full_page=True)
        b.close()
    print("wrote", os.path.join(a.out, "preview.png"))


if __name__ == "__main__":
    main()
