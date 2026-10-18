#!/usr/bin/env python3
"""
Lint UI source written with this theme for the tells that make a screen read as generated, and for the
theme's own bans that a reader can see in the code: hard-coded colours, gradients and shadows outside the
tokens, emoji, stock copy, placeholders, weight 700, eyebrow labels, monospace outside code, index numbering
and invented proof. The idea and the dated registry come from Taste-Skill (references/tells.md).

  python3 scripts/lint.py <files or folders> [--allow rule,rule] [--quiet]

Scans .swift .kt .kts .ts .tsx .js .jsx .vue .svelte .html .css .scss. Skips the generated theme files
(theme.css, Theme.swift, Theme.kt, tailwind.preset.js, tokens.json) and node_modules, build, dist, .git.

Each finding prints as  path:line  FAIL|WARN  rule  the line  -> what to do.  FAIL is a rule of the theme
(rules.md, 不要); WARN is a tell that needs a reason. Exit code 1 when any FAIL is left.

To keep one line on purpose, write  lint-allow: <rule>  in a comment on that line and say why next to it
(an elevated menu that really floats, a real user count with its source). --allow turns a rule off for the
whole run; say so in the report.
"""

import argparse
import re
import sys
from pathlib import Path

EXTS = {".swift", ".kt", ".kts", ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".html", ".css", ".scss"}
SKIP_FILES = {"theme.css", "Theme.swift", "Theme.kt", "tailwind.preset.js", "tokens.json"}
SKIP_DIRS = {"node_modules", "build", "dist", ".git", ".next", "Pods", "DerivedData"}
CSSISH = {".css", ".scss", ".html", ".vue", ".svelte", ".tsx", ".jsx", ".ts", ".js"}

# tokens that may legitimately carry a gradient: the brand panel and tile, the viewer and photo scrims
GRADIENT_OK = re.compile(r"brand-(surface|tile)|brandSurface|brandTile|scrim|Scrim|media-", re.I)
EMOJI = re.compile("[\u2600-\u2604\u2607-\u26FF\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF✨⭐❤⚡✅❌⬆⬇➡]")

ZH_STOCK = ["赋能", "一站式", "无缝", "极致体验", "全方位", "颠覆", "革命性", "下一代", "轻松搞定", "尽在掌握",
            "了解更多", "立即体验", "立即开始", "开始使用", "开启.{0,8}之旅", "释放.{0,4}潜能", "让.{0,10}更简单",
            "智能.{0,2}助力", "打造专属"]
EN_STOCK = [r"get started", r"learn more", r"unlock (your|the) (full )?potential", r"supercharge", r"seamless(ly)?",
            r"elevate (your)?", r"effortless(ly)?", r"cutting[- ]edge", r"all[- ]in[- ]one", r"game[- ]?changer",
            r"revolutioni[sz]e", r"next[- ]gen(eration)?", r"empower", r"unleash", r"to the next level",
            r"not just an? \w+", r"look no further"]


def rx(*parts, flags=0):
    return re.compile("|".join(parts), flags)


# (rule, level, pattern, exemption or None, file kinds or None, what to do)
RULES = [
    ("hardcoded-colour", "FAIL",
     rx(r"(?<![\w&/])#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\b", r"(?<![\w&/-])#[0-9a-fA-F]{3}\b(?![\w-])",
        r"\brgba?\(\s*\d", r"\bhsla?\(\s*\d", r"Color\(\s*red:", r"UIColor\(\s*red:", r"Color\(\s*hex",
        r"Color\(\s*0x[0-9A-Fa-f]{6,8}"),
     None, None,
     "用 token（`var(--…)`、`Theme.…`、`MaterialTheme.colorScheme.…`）；色值只在生成的主题文件里"),
    ("gradient", "FAIL",
     rx(r"(linear|radial|conic)-gradient\(", r"\b(Linear|Radial|Angular|Elliptical)Gradient\(",
        r"Brush\.(linear|vertical|horizontal|radial|sweep)Gradient", r"\bbg-gradient-to-"),
     GRADIENT_OK, None,
     "平涂；渐变只在品牌面板、品牌方块和遮罩的 token 上（`rules.md`「不要」）"),
    ("resting-shadow", "FAIL",
     rx(r"box-shadow\s*:(?!\s*(none|var\(--elev|var\(--focus|0 0 0 (1px|2px)))", r"text-shadow\s*:(?!\s*none)",
        r"filter\s*:[^;]*drop-shadow", r"\.shadow\((?![^)]*(elev|Elev|Theme))", r"cardElevation\(",
        r"\bshadow-(sm|md|lg|xl|2xl|inner)\b"),
     None, None,
     "层次靠明度差和 1 px `border`；只有真浮起来的菜单、弹窗用 `elev-2` / `elev-3`"),
    ("emoji", "FAIL", EMOJI, None, None,
     "用界面图标库（SF Symbols、Material Symbols Rounded、Lucide），或者直接用字"),
    ("stock-copy", "FAIL",
     re.compile("|".join(ZH_STOCK) + "|" + r"\b(" + "|".join(EN_STOCK) + r")\b", re.I), None, None,
     "写它具体做什么：按钮写动作和对象（「开始 25 分钟专注」「导出本月 CSV」），标题写会员能做什么"),
    ("placeholder", "FAIL",
     rx(r"lorem", r"ipsum", r"placeholder text", r"(image|text|title) (goes )?here", r"这里是.{0,6}(文字|标题|描述|图片)",
        r"占位(文字|图)", r"示例文字", flags=re.I),
     None, None,
     "写真实的示例内容（这个 app 的任务名、金额、照片名），交付时列出要换掉的样例"),
    ("weight-700", "FAIL",
     rx(r"font-weight\s*:\s*(700|800|900|bold|bolder)", r"FontWeight\.(Bold|ExtraBold|Black)",
        r"FontWeight\(\s*[7-9]00\s*\)", r"\bfont-(bold|extrabold|black)\b"),
     None, CSSISH | {".kt", ".kts"},
     "字重只用 400 / 510 / 590（Android 400 / 500 / 600）；iOS 的 `.largeTitle` + bold 是系统写法，不算"),
    ("eyebrow", "WARN",
     rx(r"text-transform\s*:\s*uppercase", r"\.textCase\(\s*\.uppercase\s*\)", r"\.uppercase\(\)",
        r"""class(Name)?=["'][^"']*\buppercase\b""", r"\btracking-(wide|wider|widest)\b",
        r"letter-spacing\s*:\s*0?\.(0[5-9]|[1-9])\d*em"),
     None, None,
     "标题上方的小号大写字距标签是套路：把信息放进标题或第一句，或者删掉；分组标题用 `section-header`，句首大写"),
    ("monospace", "WARN",
     rx(r"font(-family)?\s*:[^;]*mono", r"\.monospaced\(\)", r"design:\s*\.monospaced", r"FontFamily\.Monospace",
        r"\bfont-mono\b"),
     None, None,
     "等宽字只给真的代码；数字对齐用等宽数字（`tabular-nums`、`.monospacedDigit()`、`fontFeatureSettings = \"tnum\"`）"),
    ("index-numbering", "WARN",
     rx(r"""["'>]\s*0[1-9]\s*(/|／|\.|·|—)""", r"""["'>]\s*\(0\d\d\)""", r"\bstep\s+0?\d\b", r"第\s*0\d\s*步",
        flags=re.I),
     None, None,
     "顺序靠位置、大小或文字；真是有序列表就用 `<ol>` / 系统的分步控件"),
    ("invented-proof", "WARN",
     rx(r"\d[\d,.]*\s*[kKmMwW万]?\s*\+\s*(users|teams|downloads|customers|reviews|用户|位用户|人在用|下载|好评)",
        r"trusted by", r"loved by", r"rated\s+4\.\d", r"★{3,}|☆", r"五星好评", r"#1\b", r"\bNo\.\s?1\b", r"排名第一",
        flags=re.I),
     None, None,
     "没有真实来源就删；数字是真的时在旁边注明出处，并写 `lint-allow: invented-proof`"),
]

ALLOW_RE = re.compile(r"lint-allow:\s*([\w,\- ]+)")
COMMENT_ONLY = re.compile(r"^\s*(//|/\*|\*|<!--|#(?![0-9a-fA-F]{3}))")


def files_in(paths):
    for p in paths:
        p = Path(p)
        if p.is_file():
            if p.suffix in EXTS and p.name not in SKIP_FILES:
                yield p
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if (f.is_file() and f.suffix in EXTS and f.name not in SKIP_FILES
                        and not SKIP_DIRS.intersection(f.parts)):
                    yield f
        else:
            print(f"lint: 找不到 {p}", file=sys.stderr)


def lint_file(path, off):
    out = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        print(f"lint: 读不了 {path}（{e}）", file=sys.stderr)
        return out
    for n, line in enumerate(lines, 1):
        if COMMENT_ONLY.match(line) and "lint-allow" not in line:
            continue
        m = ALLOW_RE.search(line)
        allowed = {a.strip() for a in m.group(1).replace(",", " ").split()} if m else set()
        for rule, level, pat, ok, kinds, fix in RULES:
            if rule in off or rule in allowed:
                continue
            if kinds is not None and path.suffix not in kinds:
                continue
            hit = pat.search(line)
            if not hit or (ok is not None and ok.search(line)):
                continue
            out.append((path, n, level, rule, line.strip(), fix))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--allow", default="", help="comma-separated rules to switch off for this run")
    ap.add_argument("--quiet", action="store_true", help="only the summary line")
    args = ap.parse_args()
    off = {a.strip() for a in args.allow.split(",") if a.strip()}
    unknown = off - {r[0] for r in RULES}
    if unknown:
        sys.exit(f"lint: 没有这条规则：{', '.join(sorted(unknown))}")

    found, count = [], 0
    for f in files_in(args.paths):
        count += 1
        found += lint_file(f, off)
    fails = sum(1 for x in found if x[2] == "FAIL")
    warns = len(found) - fails
    if not args.quiet:
        for path, n, level, rule, text, fix in found:
            text = text if len(text) <= 96 else text[:93] + "…"
            print(f"{path}:{n}  {level}  {rule}  {text}\n    -> {fix}")
    by_rule = {}
    for x in found:
        by_rule[x[3]] = by_rule.get(x[3], 0) + 1
    detail = "，".join(f"{r} {c}" for r, c in sorted(by_rule.items(), key=lambda kv: -kv[1]))
    print(f"lint: {count} 个文件，{fails} FAIL，{warns} WARN" + (f"（{detail}）" if detail else ""))
    if off:
        print(f"lint: 本次关掉了 {', '.join(sorted(off))}，交付时写明原因")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
