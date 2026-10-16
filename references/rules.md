# 主题规则：极简线条

一句话：**界面是一张白纸（或深灰的纸），1 px 细线分出层次，颜色只出现在需要你按的地方。** 和图标同一套强调色、同一种线条语言：圆头圆角、粗细统一，所以图标放在界面里像是从里面长出来的。

## 原则

1. **中性为主，颜色克制。** 背景、表面、文字都是中性灰：浅色是 Notion 式的白和米灰，深色是 #191919 起的一层层深灰。主色只用在按钮、选中态、进度、链接上，一屏里主色面积不超过 10%。
2. **用线分层，不用色块。** 卡片、列表、输入框靠 1 px 细线（`border`）和极淡的投影跟背景分开，不靠灰底色块堆叠。一个区域只用一道线：卡片有边框，里面就不再套描边。
3. **圆角，但不圆胖。** 圆角收得比较紧：小控件 6–8，卡片和按钮 12，弹窗 16；只有标签和浮动的标签栏是胶囊。iOS 用 continuous 圆角。
4. **磨砂是唯一的材质。** 导航栏、标签栏、浮层、底部弹窗用 Apple 式磨砂：半透明的表面色、背景模糊 20、饱和度 1.8、一道 1 px 细线，不加任何颜色。卡片和列表不用磨砂。
5. **一个强调色，默认蓝。** 主色来自图标的强调色。珊瑚、黄这类暖色不做主色（界面上没有红色或黄色的主按钮），只留在 app 图标里。状态色（成功、警告、危险、信息）来自同一套强调色，只在状态出现时用。
6. **深浅两套，同等对待。** 深色模式不是反色：页面 #191919，表面一层比一层亮（#202020、#2A2A2A），细线换成更亮的深灰，主色往浅处提亮。
7. **可读性先于风格。** 所有文字和强调色都过 WCAG：正文与强调色 4.5:1（状态色放在自己的 `-container` 底上也是），占位文字 3:1。脚本自动保证，不要手动调回去。
8. **系统字体，克制的字重。** 用 SF Pro / PingFang SC / Roboto / Noto Sans SC；只用 400、500、600、700 四档，字号沿用 Apple 的文字样式。

## 颜色

**强调色**（浅 → 主），和 `rian-app-icon` 的强调色表相同：

| 名 | 色值 | 在界面里 |
|---|---|---|
| 蓝 | `#7AAEFF → #3B7BEA` | 默认主色；也是「信息」 |
| 绿 | `#6FD3A6 → #23A36B` | 可做主色；也是「成功」 |
| 紫 | `#B3A6FF → #7A63F0` | 可做主色 |
| 灰 | `#C8C7C3 → #8E8D89` | 可做主色，最克制 |
| 黄 | `#FFD978 → #F2AE2E` | 不做主色，只留在图标；也是「警告」 |
| 珊瑚 | `#FF9C86 → #EC5B45` | 不做主色，只留在图标；也是「危险」 |

主色在浅色模式下从「主」往深处走，直到对白色表面 4.5:1；深色模式下从「主」往「浅」提亮，直到对深色表面 4.5:1。主按钮上的字优先用白色，白色过不了 4.5:1 时（深色模式常见）换成同色系的深色。

**中性色**（文字灰是起点，脚本会按对比度微调）：

| token | 浅色 | 深色 |
|---|---|---|
| `bg` 页面 | `#FFFFFF` | `#191919` |
| `surface` 卡片、列表 | `#FFFFFF` | `#202020` |
| `surface-2` 次级表面 | `#F7F7F5` | `#2A2A2A` |
| `border` 细线 | `#E9E9E7` | `#313131` |
| `text` · `text-2` · `text-3` | `#1C1C1E` · `#6E6E73` · `#8E8E93` | `#F5F5F7` · `#A1A1A6` · `#76767B` |
| `frost` 磨砂 | 白色 72% | `surface` 60% |
| `frost-border` 磨砂细线 | 黑色 6% | 白色 8% |

## Token

| 组 | 内容 |
|---|---|
| 颜色 | `bg`、`surface`、`surface-2`、`border`、`text`、`text-2`、`text-3`、`primary`、`on-primary`、`primary-container`、`on-primary-container`、`success / warning / danger / info` 及各自的 `-container`、`frost`、`frost-border` |
| 圆角 | xs 4 · sm 6 · md 8 · lg 12 · xl 16 · full；iOS 用 continuous 圆角 |
| 间距 | 4 的倍数：4 8 12 16 20 24 32 40 48 |
| 字号 | large-title 34 · title-1 28 · title-2 22 · title-3 20 · headline 17/600 · body 17 · callout 16 · subhead 15 · footnote 13 · caption 12 |
| 投影 | elev-1 卡片（下移 1 px 的淡影加一圈极淡的细线）、elev-2 浮层与浮动的磨砂、elev-3 弹窗；颜色是近黑 `#0F0F0F`，很淡，深色模式加深 |
| 材质 | frost：模糊 20、饱和度 1.8、1 px 细线、无颜色 |
| 图标 | 尺寸 16 / 20 / 24 / 28，线宽 1.75；各平台图标库见「图标」 |
| 动效 | fast 160 ms、standard 240 ms（缓出），spring 420 ms（轻回弹）；不用夸张的弹跳和视差 |

## 用法速查

| 组件 | 用什么 |
|---|---|
| 页面背景 | `bg` |
| 卡片、列表组 | `surface` + 1 px `border` + `elev-1`，圆角 lg |
| 输入框 | `surface` + 1 px `border`，圆角 md；聚焦时边框换成 `primary` |
| 分段控件 | 1 px `border` 外框，圆角 md；选中段 `primary-container` 底、`on-primary-container` 字，圆角 sm |
| 进度条轨道、代码块、侧栏 | `surface-2` |
| 分隔线 | `border`，1 px，列表里从文字左边开始 |
| 主按钮 | `primary` 底、`on-primary` 字，圆角 lg，高 50，不加投影 |
| 次按钮 | 线框按钮：`surface` 底、1 px `border`、`text` 字；要更轻时用 `primary-container` 底、`on-primary-container` 字 |
| 导航栏 | 磨砂，贴边，只留靠内容那一侧的细线（CSS `border-width: 0 0 1px`） |
| 标签栏、浮动按钮 | 磨砂 + `elev-2`，浮在内容上方，圆角 full |
| 底部弹窗、弹出菜单 | 磨砂 + `elev-3`（弹窗）或 `elev-2`（菜单），圆角 xl |
| 选中的标签、链接、开关 | `primary` |
| 标签 / 徽章 | 状态色的 `-container` 底、状态色字，圆角 full |

磨砂在 CSS 里是 `.frost`，SwiftUI 里是 `.frost()`；卡片在 SwiftUI 里是 `.card()`。

## 图标

界面图标是**线性、圆头圆角、粗细统一**的一套，和 app 图标的墨线是同一种语言。一个 app 只用一套图标库、一种线宽。

| 平台 | 默认图标库 | 设置 |
|---|---|---|
| iOS | SF Symbols | 字重 `.regular`，scale `.medium`；和正文并排时字重跟随文字 |
| Android | Material Symbols **Rounded** | weight 400、fill 0、grade 0、optical size 24 |
| Web / 跨平台 | Lucide，或 Phosphor **Regular** | Lucide 设 `stroke-width: 1.75`；都用 `currentColor` 着色 |

| 项目 | 规则 |
|---|---|
| 尺寸 | sm 16（列表箭头、行内）· md 20（列表图标）· lg 24（导航栏、标签栏）· xl 28（空状态、大按钮）；token 为 `--icon-*`、`Icon.*`、`IconSize.*` |
| 线宽 | 1.75 px（24 网格），全站统一 |
| 颜色 | 默认 `text-2`；不可点的装饰图标 `text-3`；选中、可点的强调 `primary`；状态图标用对应状态色 |
| 选中态 | 只换成 `primary` 色，线宽不变。iOS 标签栏、Android 导航栏默认会换成实心版，可以保留；别的地方不要自己混用实心和线性 |
| 列表图标 | 放在 32 × 32、圆角 md 的线框方块里（1 px `border`，无底色），图标 md、颜色 `text-2`；不用彩色底块 |
| 对齐 | 与文字基线居中；图标和文字间距 8（行内）或 12（列表） |

**不用 Font Awesome 当主力图标库**：免费版只有粗的 Solid 和 Regular，细的 Light / Thin 只在付费版；图标线宽、圆角不统一，和系统图标、和 1.75 的细线并排时显得粗笨。已经在用 Pro 版时，可以全站统一用 Light，不与 Solid 混用。

也不要：混用两套图标库；实心和线性图标随意混排；彩色或渐变图标；给图标加投影。App 图标（主屏图标）不在此列，用 `rian-app-icon` 做。

## 不要

- 大面积的主色背景（整屏蓝）；主色只给可交互的东西
- 红色、橙色或黄色的主按钮
- 渐变按钮、霓虹描边、彩色投影、浓重的投影
- 用一块块灰底色堆出层次；卡片里再套一层描边
- 卡片也用磨砂（磨砂只给浮在内容上方的东西）；磨砂带颜色
- 大于 16 的圆角（标签和胶囊除外）
- 第二个强调色

## 验收清单

- [ ] 浅色、深色两张都看过，深色不是简单反色
- [ ] 主色只出现在可交互元素上，一屏面积 ≤ 10%；没有暖色主按钮
- [ ] 卡片和列表靠 1 px 细线分开，没有一层套一层的描边
- [ ] 导航栏、标签栏是磨砂，有细线，没有颜色
- [ ] 正文、次要文字、按钮文字都清楚（脚本输出的对比度 text-3 ≥ 3，其余 ≥ 4.5）
- [ ] 圆角统一：控件 6–8，卡片和按钮 12，弹窗 16
- [ ] app 图标放在导航栏里和界面协调
- [ ] 状态色只在对应状态出现
- [ ] 图标只用一套库、一种线宽，选中态做法统一

## 接入

- **Web**：先引入 `theme.css`，用 `var(--c-primary)` 等变量；`<html data-theme="dark">` 强制深色，不写则跟随系统。浮在内容上方的元素加 `class="frost"`。Tailwind 项目在 `presets` 里加 `tailwind.preset.js`，即可用 `bg-surface`、`text-text-2`、`border-border`、`shadow-e1`、`rounded-lg`。
- **SwiftUI**：把 `Theme.swift` 加进项目，用 `Palette.primary`、`Radius.lg`、`Space.s4`；卡片加 `.card()`，浮层加 `.frost()`。需要 iOS 15 以上。
- **Jetpack Compose**：把 `Theme.kt` 放进 `theme` 包，用 `AppTheme { … }` 包住界面，组件自动取 `MaterialTheme.colorScheme`。卡片用 `OutlinedCard`（边框取 `outlineVariant`，即 `border`）；磨砂用 `Frost.fill(dark)` 和 `Frost.border(dark)`，Compose 没有自带的背景模糊，需要时用 Haze 这类库。
