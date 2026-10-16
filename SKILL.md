---
name: rian-app-theme
description: Design an app's UI theme (colour tokens for light and dark, type scale, spacing, radii, elevation, UI icon guidelines and an Apple-style frost material) in Rian's minimal line style with rounded corners, drawing on Apple, Google and Notion, matched to the app's icon, and export it as CSS variables, SwiftUI, Jetpack Compose and Tailwind. Use when asked for an app theme, design tokens, colour scheme, dark mode palette or UI style for an app. 用于按 Rian 的极简线条风格生成 app UI 主题和设计 token。
---

# Rian App Theme

把 app 图标的强调色变成一整套 UI 主题：浅色和深色两套颜色 token、字号、间距、圆角、投影、界面图标规范和「磨砂」材质，导出成 CSS、SwiftUI、Compose 和 Tailwind，并渲染一张样例界面对照图。

风格和图标 skill（`rian-app-icon`）是同一种：**极简线条**。白纸一样的中性色界面，1 px 细线分层，圆角，颜色只点在需要你按的地方。中性色和细线学 Notion，磨砂、字号和圆角学 Apple，色彩角色和可访问性学 Google。规则在 `references/rules.md`，动笔前要读。

## 工作流程

### 1. 定强调色

主题只从一个颜色来：图标的**强调色**。六个色名见 `assets/palette.json`，和图标 skill 的强调色表相同。

- **默认用蓝**。用户没有特别要求时就用蓝，脚本不传 `--accent` 即是蓝。
- **珊瑚、黄这类暖色永远不做 UI 主色**，即使图标的强调色是暖色：暖色留在图标里，界面主色换成蓝（脚本会自动替换并提示）。界面上不要出现红色的主按钮。
- 图标是绿、紫或灰时，界面主色可以跟图标用同一个颜色；拿不准就用蓝。
- 用户有品牌色：从蓝、绿、紫、灰里选最接近的一个，不要自造颜色。

信息不全时自己补一个合理版本，标明「这是我的假设」，然后继续。

### 2. 生成

```bash
python3 scripts/build.py --name Tide -o themes/tide               # 蓝
python3 scripts/build.py --name Tide --accent 紫 -o themes/tide   # 也可以写 violet
```

脚本按规则推导所有颜色，并逐个检查 WCAG 对比度：正文和强调色对表面至少 4.5:1，占位文字至少 3:1，不达标会自动加深或提亮。输出 `tokens.json`、`theme.css`、`Theme.swift`、`Theme.kt`、`tailwind.preset.js`。

**不要手改生成的颜色。** 想调颜色，就换一个强调色重新生成；中性色要改时改 `assets/palette.json`，规则本身要改时改 `build.py` 的 `derive()`。

### 3. 预览、自检

```bash
python3 scripts/preview.py themes/tide --icon path/to/tide-1024.png
```

打开 `preview.png` 亲眼看，逐条检查 `references/rules.md` 末尾的验收清单。最常见的问题：

| 看到 | 改 |
|---|---|
| 整个界面太花 | 主色只留给可点的元素；列表图标、未选中的标签、装饰一律用灰 |
| 线太多、显得乱 | 卡片已经有一道细线，里面就不要再套描边；分隔线只在列表行之间，从文字左边开始 |
| 深色模式的主按钮是深色字 | 正常：深色模式的主色提亮了，白字过不了对比度，脚本换成同色系的深色字（Material 的做法） |
| 磨砂看不出来 | 正常：磨砂在内容滚到下面时才显现；静止时靠 1 px 细线和浮起的投影区分 |
| 和图标对不上 | 确认强调色和图标一致；图标是珊瑚或黄时，界面用蓝是对的 |
| 用户想用 Font Awesome 等粗图标 | 说明不合适的原因（见 `rules.md`「图标」），推荐各平台的线性图标库 |

### 4. 交付

给用户：预览图、三行说明（强调色、主色在浅色和深色下的色值、生成了哪些文件）和输出目录。告诉他们各平台怎么接入（见 `references/rules.md` 的「接入」），以及该用哪套界面图标库（见「图标」：iOS 用 SF Symbols Regular，Android 用 Material Symbols Rounded 400，Web 用 Lucide 1.75 或 Phosphor Regular）。

用户用什么语言说话，说明就用什么语言。
