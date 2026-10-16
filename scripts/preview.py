#!/usr/bin/env python3
"""Render a review sheet for a generated theme: one sample screen in light and dark, at rest and scrolled, plus swatches.

    python3 scripts/preview.py out/                                   # timer screen
    python3 scripts/preview.py out/ --screen notes --icon margin-1024.png --icon-dark margin-dark.png

Writes out/preview.png. Top row: light and dark at rest. Bottom row: the same screen scrolled, so
content sits under the frosted nav bar and tab bar and the frost is actually tested. Below them,
a swatch for every colour token in both modes.

Screens: timer (focus timer: progress, segmented control, list, chips, buttons), notes (a notes app:
long Chinese body text in body-long, a highlighted phrase, a list of notes) and list (a ledger:
summary card, chip row, amounts).

Also prints the contrast of the bar text over the scrolled content, measured on the render
(target 3:1 or more). Needs Playwright + Chromium (same setup as rian-app-icon's render.py;
set CHROMIUM_PATH to use an existing Chromium).
"""
import argparse, base64, glob, json, os, re, tempfile

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
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.4-4.4"/>',
    "note": '<path d="M14.5 3.5H7A1.5 1.5 0 0 0 5.5 5v14A1.5 1.5 0 0 0 7 20.5h10a1.5 1.5 0 0 0 1.5-1.5V7.5z"/><path d="M14.5 3.5v4h4M9 12.5h6M9 16h4"/>',
    "folder": '<path d="M3.5 7A1.5 1.5 0 0 1 5 5.5h4l2 2.5h8A1.5 1.5 0 0 1 20.5 9.5V17a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 17z"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
    "pie": '<path d="M19.5 14.5A8 8 0 1 1 9.5 4.4"/><path d="M13 3.5a7.5 7.5 0 0 1 7.5 7.5H13z"/>',
    "wallet": '<path d="M18.5 7.5V6A1.5 1.5 0 0 0 17 4.5H6A2.5 2.5 0 0 0 3.5 7v10A2.5 2.5 0 0 0 6 19.5h12.5A1.5 1.5 0 0 0 20 18V9a1.5 1.5 0 0 0-1.5-1.5H6"/><path d="M16 13.5h.01"/>',
    "food": '<path d="M6 3.5v5a3 3 0 0 0 6 0v-5M9 3.5v17M18 20.5v-17c-2.2 1.2-3.5 3.6-3.5 6.5v4H18"/>',
    "coffee": '<path d="M5 9h11v4.5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5z"/><path d="M16 10.5h1.5a2.5 2.5 0 0 1 0 5H16M9 3.5v2M12.5 3.5v2"/>',
    "bus": '<rect x="5" y="4" width="14" height="13" rx="2.5"/><path d="M5 11h14M8 20v-3M16 20v-3M8.5 14h.01M15.5 14h.01"/>',
    "bag": '<path d="M5 8h14l-1.2 12H6.2z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>',
    "income": '<circle cx="12" cy="12" r="8"/><path d="m15 9-6 6M9 10v5h5"/>',
    # status icons for status chips: a chip whose status shares the primary's accent is told apart by its icon
    "success": '<circle cx="12" cy="12" r="8"/><path d="m8.5 12.2 2.4 2.4 4.6-4.8"/>',
    "warning": '<path d="M10.7 5.3a1.5 1.5 0 0 1 2.6 0l6.9 12a1.5 1.5 0 0 1-1.3 2.2H5.1a1.5 1.5 0 0 1-1.3-2.2z"/><path d="M12 10v3.5M12 16.5h.01"/>',
    "danger": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4.5M12 16h.01"/>',
    "info": '<circle cx="12" cy="12" r="8"/><path d="M12 11v5M12 8h.01"/>',
}

STATUS_GLYPHS = ('<svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor">'
                 '<rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/>'
                 '<rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>'
                 '<svg width="26" height="12" viewBox="0 0 26 12"><rect x=".5" y=".5" width="22" height="11" rx="3.5" '
                 'fill="none" stroke="currentColor" stroke-opacity=".4"/><rect x="2.5" y="2.5" width="16" height="7" rx="2" '
                 'fill="currentColor"/><path d="M24.5 4v4" stroke="currentColor" stroke-opacity=".4" stroke-linecap="round"/></svg>')


def ic(name, cls=""):
    return f'<svg class="icon {cls}" viewBox="0 0 24 24">{ICONS[name]}</svg>'


CHEV = f'<span class="chev">{ic("chev", "sm")}</span>'


def row(icon, title, sub, trail=CHEV):
    """a list row: icon tile, title, a readable second line (text-2), then a trailing chevron or amount"""
    return (f'<div class="li"><i class="tile">{ic(icon, "md")}</i><div class="grow"><div class="t-body">{title}</div>'
            f'<div class="t-footnote muted">{sub}</div></div>{trail}</div>')


def money(amount):
    """a ledger row's amount; income in the success colour, spending in plain text with a real minus sign (U+2212)"""
    cls = "amt in" if amount.startswith("+") else "amt"
    return f'<span class="{cls} t-body num">{amount}</span>'


def chip(status, text):
    """a status chip: status colour on its container, with the status icon"""
    return f'<span class="chip {status} t-caption">{ic(status, "sm")}{text}</span>'


def note(title, snippet, date):
    return (f'<div class="li note"><div class="grow"><div class="row between"><span class="t-headline">{title}</span>'
            f'<span class="t-footnote muted">{date}</span></div><div class="t-subhead muted clip">{snippet}</div></div></div>')


def week(bars):
    cols = "".join(f'<div class="col"><span class="track"><i style="height:{h}%"></i></span>'
                   f'<span class="t-caption muted">{d}</span></div>' for d, h in bars)
    return f'<div class="cols">{cols}</div>'


# Each screen: the tab bar (first tab active) and the content under the large title. One element carries
# data-anchor: in the scrolled phones the content moves up until that element sits under the tab bar
# ("tabs") or the nav bar ("nav"). Readable text is text or text-2; text-placeholder only for
# placeholders, chevrons and decorative icons.
SCREENS = {
    "timer": {
        "label": "计时",
        "tabs": [("home", "首页"), ("chart", "统计"), ("compass", "发现"), ("sliders", "设置")],
        "body": f"""
      <section class="card hero">
        <div class="t-footnote muted">本周</div>
        <div class="t-title-1 num">12 / 20</div>
        <div class="bar"><i style="width:60%"></i></div>
        <div class="t-subhead muted">再完成 8 次就达成目标</div>
      </section>
      <div class="seg t-footnote"><span class="on">今天</span><span>本周</span><span>本月</span></div>
      <section class="card list">
        {row("timer", "深度工作", "25 分钟 · 已完成")}
        {row("book", "阅读", "40 分钟 · 进行中")}
        {row("review", "复盘", "未开始")}
      </section>
      <div class="chips">
        {chip("success", "已完成")}{chip("warning", "将到期")}
        {chip("danger", "已超时")}{chip("info", "新功能")}
      </div>
      <button class="btn primary t-headline">开始专注</button>
      <button class="btn line t-headline">稍后提醒</button>
      <h2 class="sec t-footnote">最近记录</h2>
      <section class="card list">
        {row("timer", "深度工作", "昨天 · 50 分钟")}
      </section>
      <h2 class="sec t-footnote">最近 7 天</h2>
      <section class="card chart" data-anchor="tabs">
        {week([("一", 55), ("二", 80), ("三", 40), ("四", 100), ("五", 70), ("六", 35), ("日", 0)])}
      </section>
      <section class="card list">
        {row("review", "每周复盘", "周日 20:00 提醒")}
      </section>""",
    },
    "notes": {
        "label": "笔记",
        "tabs": [("note", "笔记"), ("folder", "文件夹"), ("search", "搜索"), ("sliders", "设置")],
        "title_anchor": True,  # the large title scrolls under the nav bar
        "body": f"""
      <div class="field t-body">{ic("search", "md")}<span>搜索笔记</span></div>
      <article class="card note-card">
        <div class="t-title-3">关于专注</div>
        <div class="t-footnote muted">置顶 · 10 月 14 日 · 386 字</div>
        <p class="long">这周把讲专注的那一章又读了一遍。作者说，真正消耗精力的不是工作本身，而是在几件事之间来回切换：每切换一次，都要花时间重新找回刚才的思路。</p>
        <p class="long">所以我打算试一个简单的办法：<mark>每天上午只做一件最重要的事</mark>，消息和邮件留到下午统一处理。先坚持两周，再回来看看效果。</p>
        <div class="chips">{chip("info", "读书")}{chip("success", "已同步")}</div>
      </article>
      <h2 class="sec t-footnote">最近笔记</h2>
      <section class="card list">
        {note("产品周会纪要", "下周三前确认首页改版的范围和排期", "昨天")}
        {note("旅行清单", "护照、转换插头、充电宝、折叠伞", "10月12日")}
        {note("读书摘录", "好的设计是尽可能少的设计。", "10月9日")}
        {note("图标灵感", "界面图标的线宽要和 app 图标保持一致", "10月3日")}
        {note("番茄牛腩", "牛腩冷水下锅焯水，番茄分两次放", "9月28日")}
      </section>""",
    },
    "list": {
        "label": "账本",
        "tabs": [("list", "明细"), ("pie", "统计"), ("wallet", "预算"), ("sliders", "设置")],
        "body": f"""
      <section class="card hero">
        <div class="row between t-footnote muted"><span>10 月支出</span><span>预算 ¥6,000</span></div>
        <div class="t-title-1 num" data-anchor="nav">¥4,286.50</div>
        <div class="bar"><i style="width:71%"></i></div>
        <div class="row between t-subhead muted"><span>已用 71%</span><span class="num">还可以花 ¥1,713.50</span></div>
      </section>
      <div class="chips"><span class="fchip t-subhead on">全部</span><span class="fchip t-subhead">餐饮</span>
        <span class="fchip t-subhead">交通</span><span class="fchip t-subhead">购物</span><span class="fchip t-subhead">收入</span></div>
      <h2 class="sec t-footnote">今天</h2>
      <section class="card list">
        {row("food", "午饭", "12:30 · 微信支付", money("−¥32.00"))}
        {row("coffee", "咖啡", "09:10 · 支付宝", money("−¥18.00"))}
        {row("bus", "地铁", "08:42 · 交通卡", money("−¥4.00"))}
      </section>
      <h2 class="sec t-footnote">昨天</h2>
      <section class="card list">
        {row("income", "工资", "10:00 · 招商银行", money("+¥12,000.00"))}
        {row("bag", "超市", "19:20 · Apple Pay", money("−¥236.80"))}
        {row("food", "晚饭", "18:05 · 微信支付", money("−¥86.00"))}
      </section>
      <h2 class="sec t-footnote">10 月 13 日</h2>
      <section class="card list">
        {row("home", "房租", "09:00 · 自动扣款", money("−¥3,500.00"))}
        {row("bus", "打车", "22:40 · 微信支付", money("−¥41.50"))}
        {row("bag", "书店", "15:10 · 支付宝", money("−¥68.00"))}
      </section>""",
    },
}

PHONE = """
<div class="phone {state}" data-theme="{mode}">
  <div class="frame"><div class="screen">
    <div class="content">
      <h1 class="t-large-title"{title_anchor}>{name}</h1>{body}
    </div>
    <header class="nav frost">
      <div class="status t-subhead"><b>9:41</b><span class="glyphs">{status}</span></div>
      <div class="bar-row">
        <span class="hit text-btn link t-body">编辑</span>
        <span class="mid">{icon}<b class="inline t-headline">{name}</b></span>
        <span class="hit icon-btn link" role="button" aria-label="新建">{plus}</span>
      </div>
    </header>
    <nav class="tabs frost">{tabs}</nav>
    <i class="home"></i>
  </div></div>
  <div class="label">{label}</div>
</div>"""

STYLE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: 1080px; padding: 36px 40px 44px; background: #F0F0EE; font-family: var(--font); color: #1C1C1E;
  display: flex; flex-direction: column; gap: 36px; }
.head { text-align: center; font: 600 17px/22px var(--font); }
.head span { color: #6E6E73; font-weight: 400; }
.phones { display: grid; grid-template-columns: repeat(2, 410px); justify-content: center; gap: 32px 56px; }
.phone { text-align: center; }
.frame { padding: 10px; border-radius: 64px; background: #0A0A0B;
  box-shadow: 0 0 0 1.5px #3A3A3C, 0 24px 48px rgba(15,15,15,.16); }
.screen { position: relative; width: 390px; height: 844px; border-radius: 54px; overflow: hidden; text-align: left;
  color: var(--c-text); background: var(--c-bg); filter: brightness(1); /* backdrop root: frost blurs the screen, not the bezel */ }
.label { margin-top: 14px; font: 500 13px/18px var(--font); color: #6E6E73; letter-spacing: .04em; }

/* scrolling content: starts under the nav bar; the scrolled phones shift it up (see SCROLL) */
.content { position: absolute; top: 0; left: 0; right: 0; padding: 106px 16px 0; display: flex; flex-direction: column; gap: 12px; }
.content h1 { margin-bottom: 2px; }

/* nav bar: frost, flush with the edges, a hairline only on the content side */
.nav { position: absolute; top: 0; left: 0; right: 0; z-index: 2; padding: 0 16px 6px; border-width: 0 0 1px; }
.status { display: flex; justify-content: space-between; align-items: center; height: 50px; padding: 0 14px; }
.glyphs { display: flex; gap: 6px; align-items: center; }
.bar-row { position: relative; height: 44px; display: flex; align-items: center; justify-content: space-between; }
.hit { display: flex; align-items: center; min-width: var(--hit-min, 44px); height: var(--hit-min, 44px); }
.icon-btn { justify-content: center; margin-right: calc((24px - var(--hit-min, 44px)) / 2); } /* 44 pt target, glyph on the 16 pt margin */
.mid { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; gap: 8px; }
.mid img { width: 30px; height: 30px; border-radius: 7px; box-shadow: 0 0 0 1px var(--c-border); }
.inline { display: none; }
.scrolled .inline { display: block; }
.link { color: var(--c-primary); }

/* tab bar: floating frost capsule; unselected items are text-2 (readable), the selected one primary */
.tabs { position: absolute; left: 20px; right: 20px; bottom: 28px; height: 62px; z-index: 2; border-radius: var(--r-full);
  display: flex; justify-content: space-around; align-items: center; box-shadow: var(--elev-2); }
.tab { display: flex; flex-direction: column; align-items: center; gap: 2px; min-width: var(--hit-min, 44px); color: var(--c-text-2); }
.tab b { font-weight: 500; }
.tab.is-active { color: var(--c-primary); }
.home { position: absolute; z-index: 3; bottom: 8px; left: 50%; width: 134px; height: 5px; margin-left: -67px;
  border-radius: 3px; background: var(--c-text); }

.row { display: flex; align-items: center; } .between { justify-content: space-between; }
.grow { flex: 1; min-width: 0; }
.muted { color: var(--c-text-2); }
.num { font-variant-numeric: tabular-nums; }
.clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card { background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-lg); box-shadow: var(--elev-1); }
.hero { padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.bar { height: 6px; border-radius: var(--r-full); background: var(--c-surface-2); overflow: hidden; margin: 6px 0 4px;
  box-shadow: inset 0 0 0 1px var(--c-border); }
.bar i { display: block; height: 100%; border-radius: var(--r-full); background: var(--c-primary); }
.sec { color: var(--c-text-2); margin: 6px 0 -4px 16px; font-weight: 400; }

/* segmented control: control-h sm; inset 1 + 3 = 4, so the selected segment is r-md 8 - 4 = r-xs 4 (concentric) */
.seg { display: flex; gap: 3px; height: var(--control-h-sm, 32px); padding: 3px; border: 1px solid var(--c-border);
  border-radius: var(--r-md); background: var(--c-surface); }
.seg span { flex: 1; display: grid; place-items: center; border-radius: var(--r-xs); color: var(--c-text-2); font-weight: 500; }
.seg .on { background: var(--c-primary-container); color: var(--c-on-primary-container); font-weight: 600; }

.list { padding: 0 0 0 16px; }
.li { position: relative; display: flex; align-items: center; gap: 12px; padding: 11px 16px 11px 0; }
.li + .li::before { content: ""; position: absolute; top: 0; left: 44px; right: 0; height: 1px; background: var(--c-border); }
.li.note + .li.note::before { left: 0; }
.li.note .grow { display: flex; flex-direction: column; gap: 2px; }
.tile { width: 32px; height: 32px; border-radius: var(--r-md); border: 1px solid var(--c-border); color: var(--c-text-2);
  display: grid; place-items: center; flex: none; }
.chev { color: var(--c-text-placeholder); display: flex; }
.amt { flex: none; }
.amt.in { color: var(--c-success); }

.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px 3px 7px; border-radius: var(--r-full); }
.chip.success { background: var(--c-success-container); color: var(--c-success); }
.chip.warning { background: var(--c-warning-container); color: var(--c-warning); }
.chip.danger { background: var(--c-danger-container); color: var(--c-danger); }
.chip.info { background: var(--c-info-container); color: var(--c-info); }
.fchip { height: var(--control-h-sm, 32px); padding: 0 14px; display: inline-flex; align-items: center; border-radius: var(--r-full);
  border: 1px solid var(--c-border); background: var(--c-surface); color: var(--c-text-2); }
.fchip.on { background: var(--c-primary-container); border-color: transparent; color: var(--c-on-primary-container); font-weight: 600; }

.btn { border: 0; height: var(--control-h-lg, 50px); border-radius: var(--r-lg); font-family: var(--font); }
.btn.primary { background: var(--c-primary); color: var(--c-on-primary); }
.btn.line { background: var(--c-surface); color: var(--c-text); border: 1px solid var(--c-border); }

.chart { padding: 14px 16px 10px; }
.cols { display: flex; justify-content: space-between; height: 128px; }
.col { width: 30px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.track { flex: 1; width: 100%; display: flex; align-items: flex-end; border-radius: var(--r-sm); background: var(--c-surface-2); overflow: hidden; }
.track i { display: block; width: 100%; border-radius: var(--r-sm); background: var(--c-primary); }

/* notes: input fields take border-strong; placeholder text and its decorative icon take text-placeholder */
.field { height: var(--control-h-md, 44px); display: flex; align-items: center; gap: 8px; padding: 0 12px;
  background: var(--c-surface); border: 1px solid var(--c-border-strong); border-radius: var(--r-md); color: var(--c-text-placeholder); }
.note-card { padding: 16px; display: flex; flex-direction: column; gap: 4px; }
.note-card .chips { margin-top: 10px; }
.long { margin-top: 10px; font: var(--t-body-long, 400 17px/28px var(--font)); letter-spacing: var(--tr-body-long, 0); }
mark { background: var(--c-selection); color: inherit; padding: 1px 2px; border-radius: 3px;
  -webkit-box-decoration-break: clone; box-decoration-break: clone; }

/* swatches */
.swatches { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
.pane-title { font: 600 15px/20px var(--font); color: #1C1C1E; margin-bottom: 10px; }
.sw { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px 8px; padding: 14px; border-radius: var(--r-xl);
  background: var(--c-bg); border: 1px solid var(--c-border); }
.cell { min-width: 0; }
.blk { position: relative; height: 46px; border-radius: var(--r-md); display: grid; place-items: center; overflow: hidden;
  font: 600 15px/1 var(--font); box-shadow: inset 0 0 0 1px rgba(127,127,127,.2); }
.blk small { font: 600 9px/11px var(--font); text-align: center; padding: 0 3px; }
.blk.split { grid-template-rows: 1fr 1fr; place-items: stretch; }
.blk.split span { display: grid; place-items: center; font: 600 11px/1 var(--font); }
.blk .over { position: absolute; inset: 0; }
.blk.frosted::before { content: ""; position: absolute; inset: 0;
  background: repeating-linear-gradient(135deg, var(--c-primary) 0 7px, var(--c-text) 7px 14px, var(--c-bg) 14px 21px); }
.blk.frosted .over { inset: 8px 0 8px 0; }
.blk.ring { outline: 2px solid var(--c-focus); outline-offset: -6px; }
.blk.lift { background: var(--c-surface); }
.blk.lift i { width: 34px; height: 22px; border-radius: 6px; background: var(--c-surface); box-shadow: var(--elev-3); }
.cap { margin-top: 5px; font: 500 9.5px/12px var(--font); color: var(--c-text); overflow: hidden; }
.cap b, .cap span { display: block; }
.cap span { white-space: nowrap; }
.cap b { font-weight: 600; }
.cap span { color: var(--c-text-2); font-family: var(--font-mono); font-size: 9px; }
"""

# Swatches, one row each (six cells). "a/b" draws ink a on fill b; "a|b" stacks two pairs in one cell.
SWATCH_ROWS = [
    ["bg", "surface", "surface-2", "surface-3", "border", "border-strong"],
    ["text", "text-2", "text-placeholder", "disabled-fg/disabled-bg", "on-inverse/inverse-surface", "text/selection"],
    ["on-primary/primary", "on-primary-container/primary-container", "focus", "state-hover", "state-pressed", "scrim"],
    ["on-success/success|success/success-container", "on-warning/warning|warning/warning-container",
     "on-danger/danger|danger/danger-container", "on-info/info|info/info-container", "frost", "shadow"],
]
INK = {"text", "text-2", "text-placeholder"}             # drawn as text on surface
OVER = {"state-hover", "state-pressed", "scrim"}         # translucent layers, drawn over surface

# moves the scrolled phones' content until the data-anchor element sits under its bar
SCROLL = """() => [...document.querySelectorAll('.phone.scrolled')].map(ph => {
  const c = ph.querySelector('.content'), a = ph.querySelector('[data-anchor]');
  if (!a) return 0;
  const bar = a.dataset.anchor === 'nav' ? ph.querySelector('.bar-row') : ph.querySelector('.tabs');
  const ar = a.getBoundingClientRect(), br = bar.getBoundingClientRect();
  const s = Math.max(0, Math.round(ar.top + ar.height / 2 - br.top - br.height / 2));
  c.style.transform = `translateY(${-s}px)`;
  return s;
})"""

# the text sitting on the frost in the scrolled phones, with its colour and box
BAR_TEXT = """() => [...document.querySelectorAll('.phone.scrolled')].flatMap(ph =>
  [...ph.querySelectorAll('.tab b, .nav .text-btn, .nav .inline')].map(el => {
    const r = el.getBoundingClientRect();
    return {mode: ph.dataset.theme, text: el.textContent.trim(), color: getComputedStyle(el).color,
            box: [r.left, r.top, r.right, r.bottom]};
  }))"""
HIDE_BAR_TEXT = ".phone.scrolled .tab b, .phone.scrolled .nav .text-btn, .phone.scrolled .nav .inline { color: transparent !important; }"


# ---------- colour helpers ----------
def parse(c):
    """'#RRGGBB' or 'rgba(r, g, b, a)' -> ((r, g, b), alpha)"""
    if c.startswith("#"):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)), 1.0
    v = [float(x) for x in re.findall(r"[\d.]+", c)]
    return tuple(v[:3]), (v[3] if len(v) > 3 else 1.0)


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def over(c, base):
    """composite a token colour over an opaque one"""
    (rgb, a), (brgb, _) = parse(c), parse(base)
    return tuple(rgb[i] * a + brgb[i] * (1 - a) for i in range(3))


def auto_ink(c, C):
    """dark or light caption for a fill, whichever reads better"""
    rgb = over(c, C["bg"])
    return "#1C1C1E" if contrast(rgb, (28, 28, 30)) >= contrast(rgb, (245, 245, 247)) else "#F5F5F7"


def value(c):
    rgb, a = parse(c)
    h = "#%02X%02X%02X" % tuple(round(v) for v in rgb)
    return h if a >= 1 else f"{h} {round(a * 100)}%"


# ---------- swatches ----------
def swatch(blk, key, C):
    """a colour block with the token name (wrapping at hyphens) and its value under it"""
    name = key.replace("-", "-<wbr>")
    return f'<div class="cell">{blk}<div class="cap"><b>{name}</b><span>{value(C[key])}</span></div></div>'


def cell(spec, C):
    """one swatch; returns '' when the theme lacks a token it needs"""
    def has(*ks):
        return all(k in C for k in ks)

    if "|" in spec:  # status: solid with its on-colour, then the container with the status colour as text
        (i1, f1), (i2, f2) = (p.split("/") for p in spec.split("|"))
        if not has(f1, f2):
            return ""
        blk = (f'<div class="blk split"><span style="background:var(--c-{f1});color:var(--c-{i1}, {auto_ink(C[f1], C)})">Aa</span>'
               f'<span style="background:var(--c-{f2});color:var(--c-{i2}, {auto_ink(C[f2], C)})">Aa</span></div>')
        return swatch(blk, f1, C)
    if "/" in spec:  # ink on fill
        ink, fill = spec.split("/")
        if not has(fill):
            return ""
        blk = (f'<div class="blk" style="background:var(--c-{fill});color:var(--c-{ink}, {auto_ink(C[fill], C)})">'
               f'<small>{ink if ink in C else ""}</small></div>')
        return swatch(blk, fill, C)
    k = spec
    if k not in C:
        return ""
    if k in INK:
        blk = f'<div class="blk" style="background:var(--c-surface);color:var(--c-{k})">Aa</div>'
    elif k in OVER:
        under = "background:var(--c-surface)"
        if k == "scrim":
            under = "background:repeating-linear-gradient(90deg,var(--c-surface) 0 8px,var(--c-text) 8px 10px)"
        blk = f'<div class="blk" style="{under}"><i class="over" style="background:var(--c-{k})"></i></div>'
    elif k == "frost":
        blk = '<div class="blk frosted"><i class="over frost"></i></div>'
    elif k == "focus":
        blk = '<div class="blk ring" style="background:var(--c-surface)"></div>'
    elif k == "shadow":
        blk = '<div class="blk lift"><i></i></div>'
    else:
        blk = f'<div class="blk" style="background:var(--c-{k});color:{auto_ink(C[k], C)}"></div>'
    return swatch(blk, k, C)


def swatches(C):
    used = {k for spec in sum(SWATCH_ROWS, []) for k in re.split(r"[/|]", spec)}
    rows = [r[:] for r in SWATCH_ROWS]
    rest = [k for k in C if k not in used and not k.endswith("-rgb")]  # tokens added later still show up
    if "frost-border" in rest:
        rest.remove("frost-border")  # drawn as the frost swatch's hairline
    for i in range(0, len(rest), 6):
        rows.append(rest[i:i + 6])
    return "".join(cell(s, C) for r in rows for s in r)


# ---------- render ----------
def find_chromium():
    p = os.environ.get("CHROMIUM_PATH")
    if p:
        return p
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    return hits[-1] if hits else None


def img(path):
    if not path:
        return ""
    return f'<img src="data:image/png;base64,{base64.b64encode(open(path, "rb").read()).decode()}" alt="">'


def bar_contrast(backdrop, items, scale):
    """contrast of each bar label against the frost behind it, measured on a render with the bar text hidden"""
    from PIL import Image
    back = Image.open(backdrop).convert("RGB")
    out = []
    for it in items:
        ink = parse("rgba(" + it["color"].split("(", 1)[1])[0]
        crop = back.crop(tuple(round(v * scale) for v in it["box"])).tobytes()
        cs = sorted(contrast(ink, crop[i:i + 3]) for i in range(0, len(crop), 3))
        if cs:
            out.append((it["mode"], it["text"], cs[len(cs) // 20]))  # 5th percentile: the worst patch behind it
    return out


def page(t, theme_css, screen, icon=None, icon_dark=None):
    """the review sheet as one HTML page"""
    scr = SCREENS[screen]
    icons = {"light": img(icon), "dark": img(icon_dark or icon)}
    tabs = "".join(f'<span class="tab{" is-active" if i == 0 else ""}">{ic(n)}<b class="t-caption">{label}</b></span>'
                   for i, (n, label) in enumerate(scr["tabs"]))
    names = {"light": "浅色", "dark": "深色"}
    phones = ""
    for state in ("rest", "scrolled"):
        for m in ("light", "dark"):
            title_anchor = ' data-anchor="nav"' if state == "scrolled" and scr.get("title_anchor") else ""
            phones += PHONE.format(state=state, mode=m, name=t["name"], icon=icons[m], status=STATUS_GLYPHS,
                                   plus=ic("plus"), tabs=tabs, body=scr["body"], title_anchor=title_anchor,
                                   label=names[m] + (" · 滚动后，内容在磨砂栏下面" if state == "scrolled" else ""))
    s = t["source"]
    src = f'主色 {s["accent"]} {s["en"]}' + (f' · 图标 {s["icon-accent"]}' if "icon-accent" in s else "")
    head = f'<div class="head">{t["name"]} <span>· {src} · 样例界面 {scr["label"]}（--screen {screen}）</span></div>'
    sw = "".join(f'<div data-theme="{m}"><div class="pane-title">{names[m]} {m}</div>'
                 f'<div class="sw">{swatches(t["color"][m])}</div></div>' for m in ("light", "dark"))
    return (f'<html lang="zh-CN"><head><meta charset="utf-8"><style>{theme_css}{STYLE}</style></head><body>{head}'
            f'<div class="phones">{phones}</div><div class="swatches">{sw}</div></body></html>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="theme folder written by build.py (reads tokens.json and theme.css, writes preview.png)")
    ap.add_argument("--screen", choices=list(SCREENS), default="timer",
                    help="sample screen: timer (default), notes or list")
    ap.add_argument("--icon", metavar="PNG", help="app icon shown in the nav bar, e.g. rian-app-icon's <name>-1024.png")
    ap.add_argument("--icon-dark", metavar="PNG",
                    help="dark app icon for the dark phones, e.g. render.py --variants' <name>-dark.png (default: --icon)")
    a = ap.parse_args()

    t = json.load(open(os.path.join(a.out, "tokens.json"), encoding="utf-8"))
    theme_css = open(os.path.join(a.out, "theme.css"), encoding="utf-8").read()
    html = page(t, theme_css, a.screen, a.icon, a.icon_dark)
    out = os.path.join(a.out, "preview.png")
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            kw = {"executable_path": find_chromium()} if find_chromium() else {}
            b = p.chromium.launch(**kw)
            pg = b.new_page(viewport={"width": 1080, "height": 800}, device_scale_factor=2)
            pg.set_content(html)
            pg.evaluate("document.fonts.ready")
            pg.evaluate(SCROLL)
            items = pg.evaluate(BAR_TEXT)
            pg.screenshot(path=out, full_page=True)
            pg.add_style_tag(content=HIDE_BAR_TEXT)  # second shot: the frost alone, behind where the bar text was
            pg.screenshot(path=tmp, full_page=True)
            b.close()
        print("wrote", out)
        res = bar_contrast(tmp, items, 2)
    finally:
        os.remove(tmp)
    for m in ("light", "dark"):
        r = [x for x in res if x[0] == m]
        if r:
            text, c = min(((x[1], x[2]) for x in r), key=lambda x: x[1])
            print(f"frost {m}: lowest bar text contrast over scrolled content {c:.1f}:1 ({text}); "
                  f"target >= 3  {'PASS' if c >= 3 else 'FAIL'}")


if __name__ == "__main__":
    main()
