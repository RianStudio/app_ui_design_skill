# rian-app-theme

一个 Claude skill：用 app 图标的强调色生成整套 UI 主题，包括浅色和深色两套颜色 token、字号、间距、圆角、投影、尺寸、动效和磨砂材质，一次导出 CSS 变量、SwiftUI、Jetpack Compose 和 Tailwind，并渲染一张样例界面对照图。所有文字色和强调色都放在每个表面和磨砂上检查 WCAG 对比度，不达标脚本就不输出。

风格是**极简线条**：白纸一样的中性色界面，1 px 细线分层，圆角收得紧，主色只出现在需要你按的地方；导航栏、标签栏和浮层用 Apple 式的半透明磨砂。中性色和细线学 Notion，磨砂、字号和圆角学 Apple，色彩角色和可访问性学 Google。它和图标 skill [rian-app-icon](https://github.com/RianStudio/app_logo_design_skill) 用同一套强调色和同一种圆头圆角的线条，图标放进界面里是一家人。

![Tide 主题](examples/tide/preview.png)

## 安装

**Claude Code**：把整个仓库复制到 `~/.claude/skills/rian-app-theme/`（个人）或项目里的 `.claude/skills/rian-app-theme/`。

**Claude.ai / Claude 桌面版**：把仓库打成 zip，在 Settings → Capabilities → Skills 上传。

预览脚本需要一次性安装：

```bash
pip install playwright pillow && playwright install chromium
```

## 用法

直接对 Claude 说，例如：

> 给 Tide 做一套 UI 主题。

界面主色按图标的强调色定：蓝→蓝，绿→绿，紫→紫；珊瑚、黄、灰只留在 app 图标里，界面用蓝。没有图标时默认蓝。

也可以直接跑脚本：

```bash
python3 scripts/build.py --name Tide --accent 珊瑚 -o themes/tide   # 传图标的强调色，中英文都可以；珊瑚 → 界面蓝
python3 scripts/preview.py themes/tide --screen timer --icon tide-1024.png --icon-dark tide-dark.png
```

## 示例

| 示例 | 图标色 | 界面主色 | 主色（浅 / 深） | 样例界面 |
|---|---|---|---|---|
| [Tide 专注计时](examples/tide/) | 珊瑚 | 蓝 | `#336AC9` / `#629BF7` | `timer` |
| [Margin 笔记](examples/margin/) | 黄 | 蓝 | `#336AC9` / `#629BF7` | `notes` |
| [Ledgerly 记账](examples/ledgerly/) | 绿 | 绿 | `#1B7C52` / `#35AF79` | `list` |

Tide 和 Margin 的图标是暖色，界面都换成蓝，所以两套 token 只差名字和记下的图标色；Ledgerly 的图标是绿，界面跟着用绿。图标来自 rian-app-icon 的示例，深色图标由它的 `render.py --variants` 生成。重新生成：

```bash
python3 scripts/build.py --name Ledgerly --accent 绿 -o examples/ledgerly
python3 scripts/preview.py examples/ledgerly --screen list --icon ledgerly-1024.png --icon-dark ledgerly-dark.png
```

## 结构

```
SKILL.md                    工作流程（Claude 读这个）
references/rules.md         主题规则、颜色、token、组件用法、图标、接入方式
assets/palette.json         强调色（与 rian-app-icon 相同）和中性色
scripts/build.py            强调色 → tokens.json / theme.css / Theme.swift / Theme.kt / tailwind.preset.js
scripts/preview.py          样例界面（timer / notes / list）浅色 + 深色、静止 + 滚动态对照图，并量磨砂上文字的对比度
examples/                   三套示例主题
```

## License

MIT
