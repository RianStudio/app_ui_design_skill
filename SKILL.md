---
name: rian-app-theme
description: Design an app's UI theme (colour tokens for light and dark, type scale, spacing, radii, elevation, UI icon guidelines and an Apple-style frost material) in Rian's minimal line style with rounded corners, drawing on Apple, Google and Notion, matched to the app's icon, and export it as CSS variables, SwiftUI, Jetpack Compose and Tailwind. Use when asked for an app theme, design tokens, colour scheme, dark mode palette or UI style for an app, and when building screens of an app that uses this theme. Not for chart palettes, slides or marketing sites. 用于按 Rian 的极简线条风格生成 app UI 主题、主题色、配色、深色模式和设计 token，以及给用这套主题的 app 写界面。
---

# Rian App Theme

把 app 图标的强调色变成一整套 UI 主题：浅色和深色两套颜色 token、字号、间距、圆角、投影、尺寸、界面图标规范和「磨砂」材质，导出成 CSS、SwiftUI、Compose 和 Tailwind，并渲染一张样例界面对照图。

风格和图标 skill（`rian-app-icon`）是同一种：**极简线条**。白纸一样的中性色界面，1 px 细线分层，圆角，颜色只点在需要你按的地方。中性色和细线学 Notion，磨砂、字号和圆角学 Apple，色彩角色和可访问性学 Google。

**生成主题不需要先读 `references/rules.md`**：颜色、对比度、尺寸都由脚本决定。之后写界面代码时，再读其中的「用法速查」「图标」「不要」三节。

**节奏**：按第 1 步的表直接定主色，不用等用户确认；生成、预览各跑一次，第 3 步三项都过就交付。不要反复调色。

## 工作流程

### 1. 定主色

主题只从一个颜色来：图标的**强调色**。六个色名见 `assets/palette.json`，和图标 skill 的强调色表相同。界面主色按这张表定，没有例外：

| 图标强调色 | 界面主色 |
|---|---|
| 蓝 | 蓝 |
| 绿 | 绿 |
| 紫 | 紫 |
| 珊瑚、黄、灰 | 蓝（原色只留在图标里） |

- **有图标时**：把图标的强调色原样传给 `--accent`，脚本自己换算（珊瑚、黄、灰会打印一行提示，`tokens.json` 的 `source.icon-accent` 记下图标色）。
- **只有品牌色、没有图标时**：红、橙、黄、棕、灰 → 蓝；其余取最接近的蓝、绿、紫。不要自造颜色。
- **什么都没有**：蓝。不传 `--accent` 就是蓝。

红色（珊瑚）永远不做界面主色；界面上不要出现红色、橙色或黄色的主按钮。

信息不全时自己补一个合理版本，标明「这是我的假设」，然后继续。

### 2. 生成

```bash
python3 scripts/build.py --name Tide --accent 珊瑚 -o themes/tide   # 图标是珊瑚 → 界面蓝
python3 scripts/build.py --name Ledgerly --accent 绿 -o themes/ledgerly
```

色名中英文都可以（`--accent green`）。脚本按规则推导所有颜色，把每个前景色放在它可能出现的每个底上检查 WCAG 对比度（bg、surface、surface-2、surface-3，以及叠在页面和内容上的磨砂），正文和强调色至少 4.5:1，占位文字和控件边框至少 3:1，不达标会自动加深或提亮。最后打印完整的对比度矩阵；仍有不达标的组合时，列出失败项、什么都不写、退出码 1。

输出 `tokens.json`、`theme.css`、`Theme.swift`、`Theme.kt`、`tailwind.preset.js`。

**不要手改生成的颜色。** 想调颜色，就换一个强调色重新生成；中性色要改时改 `assets/palette.json`，规则本身要改时改 `build.py` 的 `derive()`。

### 3. 预览、自检

```bash
ICON_SKILL=~/.claude/skills/rian-app-icon   # rian-app-icon 的目录，按实际改
python3 $ICON_SKILL/scripts/render.py tide.svg -o icons --variants   # 写出 icons/tide-1024.png 和 icons/tide-dark.png
python3 scripts/preview.py themes/tide --screen timer \
  --icon icons/tide-1024.png --icon-dark icons/tide-dark.png
```

- `--screen` 选最接近这个 app 的样例界面：`timer`（计时、工具类，默认）、`notes`（笔记、阅读类：长段中文、高亮、搜索框）、`list`（账本、列表类：金额、筛选标签、分组列表）。
- `--icon` 用 `rian-app-icon` 的 `render.py` 写出的 `<name>-1024.png`；`--icon-dark` 用加 `--variants` 时同一个 `-o` 目录里的 `<name>-dark.png`。已经渲染过就直接用那个目录；没有深色版就省略，深色手机沿用 `--icon`。
- 预览图第一行是浅色和深色的静止态，第二行是滚动态：内容滚到磨砂导航栏和标签栏下面。下面是所有颜色 token 的色板。
- 脚本最后量一次磨砂：滚动态里栏上文字对身后内容的最低对比度，每种模式一行，例如 `frost light: lowest bar text contrast over scrolled content 4.6:1 (发现); target >= 3  PASS`。

打开 `preview.png` 亲眼看，**只查三件事**：

1. **主色符合第 1 步的表**。预览图标题行写着主色和图标色。
2. **脚本的断言都通过**。`build.py` 最后打印 `contrast: all pass`；`preview.py` 的 `frost light`、`frost dark` 两行都是 PASS。
3. **图标和主色协调**。看导航栏里的图标（浅色、深色各一个）和主按钮、选中的标签放在一起像不像一家。

三项都过就交付。用户之后提意见时，常见的情况：

| 看到 | 改 |
|---|---|
| 整个界面太花 | 主色只留给可点的元素；列表图标、未选中的标签、装饰一律用灰 |
| 线太多、显得乱 | 卡片已经有一道细线，里面就不要再套描边；分隔线只在列表行之间，从文字左边开始 |
| 深色模式的主按钮是深色字 | 正常：深色模式的主色提亮了，白字过不了对比度，脚本换成同色系的深色字（Material 的做法） |
| 静止时看不出磨砂 | 正常：磨砂要在滚动态里看。栏上文字对身后内容 ≥ 3:1，以 `preview.py` 的 frost 行为准 |
| 和图标对不上 | 确认 `--accent` 用的是图标的强调色；图标是珊瑚、黄或灰时，界面用蓝是对的 |
| 用户想用 Font Awesome 等粗图标 | 说明不合适的原因（见 `rules.md`「图标」），推荐各平台的线性图标库 |

### 4. 交付

给用户：预览图、三行说明（图标色 → 界面主色、主色在浅色和深色下的色值、生成了哪些文件）和输出目录。告诉他们各平台怎么接入（见 `references/rules.md` 的「接入」），以及该用哪套界面图标库（见「图标」：iOS 用 SF Symbols Regular，Android 用 Material Symbols Rounded 400，Web 用 Lucide 1.75 或 Phosphor Regular）。

用户用什么语言说话，说明就用什么语言。

### 之后写界面

给用这套主题的 app 写界面时，先读 `references/rules.md` 的「用法速查」「图标」「不要」，颜色、圆角、尺寸都用 token，不写死数值。
