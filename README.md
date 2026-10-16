# rian-app-theme

一个 Claude skill：用 app 图标的强调色生成整套 UI 主题。颜色 token 有深浅两种模式 × 标准和高对比两档，共四套；另有桌面和手机两套字号，以及间距、圆角、阴影、尺寸、动效、frost 材质和界面图标规范。一次导出 CSS 变量、SwiftUI、Jetpack Compose 和 Tailwind，并渲染一张对照图：iPhone 浅色和深色、Android、打开 ⌘K 命令菜单的桌面窗口。所有文字色和主色都放在每个表面和玻璃上检查 WCAG 对比度，标准和高对比两档任何一项不过，脚本就不输出。

风格是**石墨**（Linear 式，结合 Apple 与 Google）：深石墨和纸白两套中性色阶梯，在 CIE LCh 里从同一个色相（265）推导出来；用 1 px 发丝线和明度差分层，卡片不加投影；单一强调色，只用在主按钮、焦点、链接、进度这几处；键盘优先，有 ⌘K 命令菜单、单键和 G 序列快捷键、乐观更新、内联编辑；桌面排得密（正文 13–14、行高 36），手机沿用平台字号和点击区。线条、密度和克制学 Linear，材质、字体和图标规格学 Apple（iOS 26 Liquid Glass），无障碍硬指标和动效参数学 Google（Material 3）。它和图标 skill [rian-app-icon](https://github.com/RianStudio/app_logo_design_skill) 用同一套强调色和同一种石墨，图标放进界面里是一家人。

![Ledgerly 主题](examples/ledgerly/preview.png)

## 安装

**Claude Code**：把整个仓库复制到 `~/.claude/skills/rian-app-theme/`（个人）或项目里的 `.claude/skills/rian-app-theme/`。

**Claude.ai / Claude 桌面版**：把仓库打成 zip，在 Settings → Capabilities → Skills 上传。

预览脚本需要一次性安装：

```bash
pip install playwright pillow numpy && playwright install chromium
```

第一次预览会从 Google Fonts 下载 Inter、Roboto Flex、Material Symbols Rounded 和用到的 Noto Sans SC 字，缓存在 `~/.cache/rian-app-theme/fonts`；离线时加 `--offline` 用本机字体。

## 用法

直接对 Claude 说，例如：

> 给 Ledgerly 做一套 UI 主题。

界面主色按图标的强调色定：蓝→蓝，绿→绿，紫→紫；珊瑚、黄、灰只留在 app 图标里，界面用蓝。没有图标时默认蓝。中性色永远是石墨，不跟主色变。

也可以直接跑脚本：

```bash
python3 scripts/build.py --name Ledgerly --accent 绿 -o themes/ledgerly   # 传图标强调色的色名，中英文都可以
python3 scripts/preview.py themes/ledgerly --screen list \
  --icon icons/ledgerly-1024.png --icon-dark icons/ledgerly-dark.png
```

`icons/` 是 rian-app-icon 的 `render.py ledgerly.svg -o icons --variants` 的输出目录，里面有默认外观 `ledgerly-1024.png` 和深色外观 `ledgerly-dark.png`。

`build.py` 全部通过时打印 `contrast: all pass (standard, high)`；`preview.py` 在主题目录里写出 `preview.png`（1960 宽的画板，2x 截图），最后打印 `frost light`、`frost dark`（栏上文字对滚到下面的内容 ≥ 3:1）和 `accent area desktop`、`accent area phone`（主色面积桌面 ≤ 5 %、手机 ≤ 8 %）四行，都应该是 PASS；有 FAIL 时退出码是 1。`--screen` 选样例界面（`timer` 默认、`notes`、`list`），`--desktop-mode light` 把桌面窗口换成浅色。

## 示例

| 示例 | 图标色 | 界面主色 | `primary`（深浅同值） | `primary-text`（深 / 浅） | 样例界面 |
|---|---|---|---|---|---|
| [Ledgerly 记账](examples/ledgerly/) | 绿 | 绿 | `#008755` | `#34AF76` / `#00764A` | `list` |
| [Tide 专注计时](examples/tide/) | 珊瑚 | 蓝 | `#2B72E0` | `#6E97FF` / `#0064CD` | `timer` |
| [Margin 笔记](examples/margin/) | 黄 | 蓝 | `#2B72E0` | `#6E97FF` / `#0064CD` | `notes` |

色值来自当前的 `build.py`，以各示例 `tokens.json` 的 `color.*.primary`、`color.*.primary-text` 为准；高对比档的 `primary-text` 更亮或更暗一档（绿 `#5FD599` / `#005B38`，蓝 `#ADBDFF` / `#004CA0`）。Tide 和 Margin 的图标是暖色，界面都换成蓝，所以两套颜色只差名字和记下的图标色；Ledgerly 的图标是绿，界面跟着用绿。重新生成：

```bash
ICON_SKILL=~/.claude/skills/rian-app-icon   # rian-app-icon 仓库的位置，按实际改
python3 $ICON_SKILL/scripts/render.py $ICON_SKILL/examples/ledgerly.svg -o /tmp/icons --variants   # 写出 /tmp/icons/ledgerly-1024.png 和 ledgerly-dark.png
python3 scripts/build.py --name Ledgerly --accent 绿 -o examples/ledgerly
python3 scripts/preview.py examples/ledgerly --screen list \
  --icon /tmp/icons/ledgerly-1024.png --icon-dark /tmp/icons/ledgerly-dark.png
```

Tide 把 `ledgerly`、`Ledgerly`、`绿`、`list` 换成 `tide`、`Tide`、`珊瑚`、`timer`。Margin 的旧图标已经从 rian-app-icon 删掉（旧风格），重新生成时用 `--name Margin --accent 黄 -o examples/margin`，预览用 `--screen notes` 并省略 `--icon` 和 `--icon-dark`，图标位置是石墨占位图。Tide 和 Margin 的图标是暖色，预览里桌面窗口旁边多一格「图标 × 界面」；Ledgerly 那格是确认弹窗。

## 结构

```
SKILL.md                    工作流程（Claude 读这个）
references/rules.md         主题规则：颜色和对比度、token、组件用法、命令菜单、UX 模式、图标、平台适配、接入方式
assets/palette.json         强调色（与 rian-app-icon 相同）、石墨中性色的 LCh 输入（base、ladder、text、alpha）
scripts/build.py            强调色 → tokens.json / theme.css / Theme.swift / Theme.kt / tailwind.preset.js（四套颜色，断言对比度）
scripts/preview.py          对照图：iPhone 浅色和深色、Android、组件条、⌘K 打开的桌面窗口、字号表、四套色板；量 frost 和主色面积
examples/                   三套示例主题
```

## License

MIT
