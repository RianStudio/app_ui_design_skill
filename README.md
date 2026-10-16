# rian-app-theme

一个 Claude skill：用 app 图标的三种传统色生成整套 UI 主题，包括浅色和深色两套颜色 token、字号、间距、圆角、投影、动效和青瓷釉材质，一次导出 CSS 变量、SwiftUI、Jetpack Compose 和 Tailwind，并渲染一张样例界面对照图。所有文字色和强调色都自动通过 WCAG 对比度检查。

风格是**清冷的东方质感**：极简、偏科技、偏冷淡。界面以冷调中性色为主，主色只出现在需要你按的地方；导航栏、标签栏和浮层用半透明的青瓷釉。它和图标 skill [rian-app-icon](https://github.com/RianStudio/app_logo_design_skill) 用同一套色板和同一种釉，图标放进界面里是一家人。

![Tide 主题](examples/tide/preview.png)

## 安装

**Claude Code**：把整个仓库复制到 `~/.claude/skills/rian-app-theme/`（个人）或项目里的 `.claude/skills/rian-app-theme/`。

**Claude.ai / Claude 桌面版**：把仓库打成 zip，在 Settings → Capabilities → Skills 上传。

预览脚本需要一次性安装：

```bash
pip install playwright && playwright install chromium
```

## 用法

直接对 Claude 说，例如：

> 给 Tide 做一套 UI 主题。

默认配色是**霜白 · 黛 · 月白**：霜白做界面底色，黛做主色，月白做釉面。朱砂、藤黄这类暖色只留在 app 图标里，不做界面主色。

也可以直接跑脚本：

```bash
python3 scripts/build.py --name Tide -o themes/tide          # 霜白 · 黛 · 月白
python3 scripts/preview.py themes/tide --icon tide-1024.png
```

## 示例

| 示例 | 三种颜色 | 主色（浅 / 深） |
|---|---|---|
| [Tide 专注计时](examples/tide/) | 霜白 · 黛 · 月白 | 黛蓝，深色下提亮为灰蓝；图标仍是朱砂 |
| [Margin 笔记](examples/margin/) | 霜白 · 黛 · 月白 | 黛蓝，深色下提亮为灰蓝 |

## 结构

```
SKILL.md                    工作流程（Claude 读这个）
references/rules.md         主题规则、token、组件用法、接入方式
assets/palette.json         传统色板（与 rian-app-icon 相同）
scripts/build.py            三种颜色 → tokens.json / theme.css / Theme.swift / Theme.kt / tailwind.preset.js
scripts/preview.py          样例界面浅色 + 深色对照图
examples/                   两套示例主题
```

## License

MIT
