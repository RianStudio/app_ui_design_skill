# 主题规则：极简线条

一句话：**界面是一张白纸（或深灰的纸），1 px 细线分出层次，颜色只出现在需要你按的地方。** 和图标同一套强调色、同一种线条语言：圆头圆角、粗细统一，所以图标放在界面里像是从里面长出来的。

## 原则

1. **中性为主，颜色克制。** 背景、表面、文字都是中性灰：浅色是 Notion 式的白和米灰，深色是 #191919 起的一层层深灰。主色只用在按钮、选中态、进度、链接上，一屏里主色面积不超过 10%。
2. **用线分层，不用色块。** 卡片、列表、输入框靠 1 px 细线和极淡的投影跟背景分开，不靠灰底色块堆叠。一个区域只用一道线：卡片有边框，里面就不再套描边。
3. **圆角，但不圆胖。** 圆角收得比较紧：小控件 6–8，卡片和按钮 12，弹窗 16。**full（胶囊）只给三样：标签和徽章（含筛选标签）、浮动标签栏、浮动按钮。** iOS 用 continuous 圆角。
4. **磨砂是唯一的材质。** 导航栏、标签栏、浮层、底部弹窗用 Apple 式磨砂：88% 的磨砂色、背景模糊 20、饱和度 1.8、一道 1 px 细线，不加任何颜色。卡片和列表不用磨砂。
5. **一个强调色，默认蓝。** 主色按映射表来自图标的强调色：蓝→蓝，绿→绿，紫→紫，珊瑚、黄、灰→蓝。暖色和灰只留在 app 图标里，界面上没有红色、橙色或黄色的主按钮。状态色（成功、警告、危险、信息）来自同一套强调色，只在状态出现时用。
6. **深浅两套，同等对待。** 深色模式不是反色：页面 #191919，表面一层比一层亮（#202020、#2A2A2A、#333333），细线换成更亮的深灰，主色往浅处提亮。
7. **可读性先于风格。** 所有要读的文字和强调色都过 WCAG 4.5:1，放在 bg、surface、surface-2、surface-3 和磨砂上都要过（状态色放在自己的 `-container` 底上也是）；占位文字、控件边框 3:1。脚本自动保证，不要手动调回去。
8. **系统字体，克制的字重。** 用 SF Pro / PingFang SC / Roboto / Noto Sans SC；只用 400、500、600、700 四档，字号沿用 Apple 的文字样式。中文、日文、韩文不加字距。

## 颜色

**强调色**（浅 → 主），和 `rian-app-icon` 的强调色表相同：

| 名 | 色值 | 在界面里 |
|---|---|---|
| 蓝 | `#7AAEFF → #3B7BEA` | 默认主色；珊瑚、黄、灰的图标也用它；也是「信息」 |
| 绿 | `#6FD3A6 → #23A36B` | 图标是绿时做主色；也是「成功」 |
| 紫 | `#B3A6FF → #7A63F0` | 图标是紫时做主色 |
| 灰 | `#C8C7C3 → #8E8D89` | 不做主色：和次要文字太像，选中和未选中分不出来 |
| 黄 | `#FFD978 → #F2AE2E` | 不做主色，只留在图标；也是「警告」 |
| 珊瑚 | `#FF9C86 → #EC5B45` | 不做主色，只留在图标；也是「危险」 |

主色在浅色模式下从「主」往深处走，深色模式下从「主」往「浅」提亮，直到在每个表面和磨砂上都到 4.5:1。主按钮上的字优先用白色，白色过不了 4.5:1 时（深色模式常见）换成同色系的深色。状态色和主色同源时（蓝主题的「信息」、绿主题的「成功」），直接用主色的那几个值，不另生成一个近似色。

**中性色**（`text-2`、`text-placeholder`、`border-strong` 是起点，脚本会按对比度微调）：

| token | 浅色 | 深色 | 用在 |
|---|---|---|---|
| `bg` | `#FFFFFF` | `#191919` | 页面 |
| `surface` | `#FFFFFF` | `#202020` | 卡片、列表 |
| `surface-2` | `#F7F7F5` | `#2A2A2A` | 次级表面：进度条轨道、代码块、侧栏 |
| `surface-3` | `#F0F0EE` | `#333333` | 第三层：`surface-2` 上还要再分一层时用；骨架屏的占位块 |
| `border` | `#E9E9E7` | `#313131` | 卡片、分隔线、线框按钮 |
| `border-strong` | `#8E8E93` | `#6C6C70` | 只给控件边界：输入框、复选框、关闭态的开关（3:1） |
| `text` | `#1C1C1E` | `#F5F5F7` | 正文、标题 |
| `text-2` | `#6E6E73` | `#A1A1A6` | 次要文字：副标题、时间、分组标题、未选中的标签（4.5:1） |
| `text-placeholder` | `#8E8E93` | `#76767B` | 只给占位文字、禁用文字、chevron 和装饰图标（3:1）；不写要读的字 |
| `inverse-surface` · `on-inverse` | `#2A2A2A` · `#F5F5F7` | `#F5F5F7` · `#1C1C1E` | toast、snackbar |
| `frost` | 白色 88% | `#262628` 88% | 磨砂 |
| `frost-border` | 黑色 6% | 白色 8% | 磨砂细线 |
| `scrim` | 黑色 32% | 黑色 48% | 弹窗后面的遮罩 |

## Token

| 组 | 内容 |
|---|---|
| 颜色 | 表面 `bg`、`surface`、`surface-2`、`surface-3`；线 `border`、`border-strong`；文字 `text`、`text-2`、`text-placeholder`；主色 `primary`、`on-primary`、`primary-container`、`on-primary-container`；状态 `success / warning / danger / info` 及各自的 `-container`、`on-*`；状态层 `disabled-fg`、`disabled-bg`、`state-hover`、`state-pressed`、`focus`、`scrim`、`selection`；反色 `inverse-surface`、`on-inverse`；材质 `frost`、`frost-border`；`shadow` |
| 圆角 | xs 4 · sm 6 · md 8 · lg 12 · xl 16 · full；iOS 用 continuous 圆角 |
| 间距 | 4 的倍数：4 8 12 16 20 24 32 40 48 |
| 尺寸 | `hit-min` 最小点击区：iOS 44、Android 48；`control-h` 控件高：sm 32（分段控件、筛选标签）· md 44（输入框、搜索框）· lg 50（主按钮、次按钮） |
| 字号 | large-title 34 · title-1 28 · title-2 22 · title-3 20 · headline 17/600 · body 17 · body-long 17/28（长段正文）· callout 16 · subhead 15 · footnote 13 · caption 12 |
| 投影 | elev-1 卡片：下移 1 px 的一层淡影，细线由卡片自己的 `border` 提供；elev-2 浮层与浮动的磨砂；elev-3 弹窗。颜色是近黑 `#0F0F0F`，很淡，深色模式 ×2.6 |
| 材质 | frost：88% 磨砂色、模糊 20、饱和度 1.8、1 px 细线、无颜色 |
| 图标 | 尺寸 16 / 20 / 24 / 28，24 网格下线宽 1.75；各平台图标库见「图标」 |
| 动效 | fast 160 ms、standard 240 ms（缓出），spring 420 ms（轻回弹）；不用夸张的弹跳和视差 |

## 用法速查

| 组件 | 用什么 |
|---|---|
| 页面背景 | `bg` |
| 卡片、列表组 | `surface` + 1 px `border` + `elev-1`，圆角 lg |
| 次要文字 | `text-2`：副标题、时间、分组标题、未选中的标签。`text-placeholder` 只给占位、禁用文字、chevron、装饰图标 |
| 长段正文 | `body-long` 17/28（笔记、文章、说明）；短文字用 `body` |
| 输入框、搜索框 | `surface` + 1 px `border-strong`，圆角 md，高 `control-h` md 44；占位文字和放大镜用 `text-placeholder`；聚焦时边框换成 `primary` |
| 复选框、开关关闭态 | 边框 `border-strong`；打开、勾选后 `primary` |
| 分段控件 | 高 `control-h` sm 32，1 px `border` 外框，圆角 md 8，内缩 3；选中段 `primary-container` 底、`on-primary-container` 字，圆角 xs 4（8 减去内缩 4，内外同心） |
| 进度条轨道、代码块、侧栏 | `surface-2` |
| 分隔线 | `border`，1 px，列表里从文字左边开始 |
| 主按钮 | `primary` 底、`on-primary` 字，圆角 lg，高 `control-h` lg 50，不加投影 |
| 次按钮 | 线框按钮：`surface` 底、1 px `border`、`text` 字，圆角 lg，高 50；要更轻时用 `primary-container` 底、`on-primary-container` 字 |
| 危险操作（删除、退出登录） | 次按钮样式：`surface` 底、1 px `border`、`danger` 字；确认弹窗里用 `danger` 字的文字按钮。不用红底 |
| 禁用 | 按钮：`disabled-bg` 底、`disabled-fg` 字，不加边框；输入框、列表行：文字换成 `text-placeholder` |
| 悬停、按下 | 在列表行、文字按钮、线框按钮上叠 `state-hover`（6%）或 `state-pressed`（10%）；主按钮用平台自带的按下效果 |
| 键盘焦点 | 2 px `focus` 描边，离控件 2 px；`theme.css` 已经给 `:focus-visible` 写好 |
| 文字选中、高亮 | `selection`；笔记里的高亮标记也用它，文字保持 `text` |
| 点击区 | 可点的东西点击区至少 `hit-min`（iOS 44、Android 48）；图形可以更小，用内边距补足 |
| 导航栏 | 磨砂，贴边，只留靠内容那一侧的细线（CSS `border-width: 0 0 1px`）；按钮文字和图标用 `primary` |
| 浮动标签栏 | 磨砂 + `elev-2`，圆角 full，左右各留 20，悬在 home 指示条上方；未选中 `text-2`，选中 `primary` |
| 浮动按钮 | 磨砂 + `elev-2`，圆角 full，至少 `hit-min` 见方；图标 `primary` 或 `text` |
| 底部弹窗、弹出菜单 | 磨砂 + `elev-3`（弹窗）或 `elev-2`（菜单），圆角 xl；后面铺 `scrim` |
| toast、snackbar | `inverse-surface` 底、`on-inverse` 字；里面的操作按钮用另一种模式的 `primary`（Compose 的 `inversePrimary`） |
| 选中的标签、链接、开关 | `primary` |
| 状态标签 / 徽章 | 状态色的 `-container` 底、状态色字，圆角 full。和主色同源的状态（蓝主题的「信息」、绿主题的「成功」）必须带状态图标（✓ / i），否则和选中态分不出 |
| 筛选标签 | 高 `control-h` sm 32，圆角 full；未选中 `surface` 底、1 px `border`、`text-2` 字；选中 `primary-container` 底、`on-primary-container` 字，不加边框 |
| 计数角标 | 实心状态色底、`on-*` 字（如 `danger` 底、`on-danger` 字），圆角 full；实心状态色只用在这种小角标上 |

磨砂和内容的关系：内容滚到导航栏、标签栏下面时，栏上的文字对身后的内容仍要 ≥ 3:1。`preview.py` 的滚动态会量这个值。

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
| 线宽 | 24 网格下 1.75，随尺寸等比缩放（Lucide 默认行为，20 和 16 尺寸下实际约 1.46 和 1.17）。要求各尺寸线宽完全一样时，给 `.icon` 加 `vector-effect: non-scaling-stroke` |
| 颜色 | 默认 `text-2`；chevron 和不可点的装饰图标 `text-placeholder`；选中、可点的强调 `primary`；状态图标用对应状态色 |
| 选中态 | 只换成 `primary` 色，线宽不变。iOS 标签栏、Android 导航栏默认会换成实心版，可以保留；别的地方不要自己混用实心和线性 |
| 列表图标 | 放在 32 × 32、圆角 md 的线框方块里（1 px `border`，无底色），图标 md、颜色 `text-2`；不用彩色底块 |
| 对齐 | 与文字基线居中；图标和文字间距 8（行内）或 12（列表） |

**不用 Font Awesome 当主力图标库**：免费版只有粗的 Solid 和 Regular，细的 Light / Thin 只在付费版；图标线宽、圆角不统一，和系统图标、和 1.75 的细线并排时显得粗笨。已经在用 Pro 版时，可以全站统一用 Light，不与 Solid 混用。

也不要：混用两套图标库；实心和线性图标随意混排；彩色或渐变图标；给图标加投影。App 图标（主屏图标）不在此列，用 `rian-app-icon` 做。

## 不要

- 大面积的主色背景（整屏蓝）；主色只给可交互的东西
- 红色、橙色或黄色的主按钮；红底的删除按钮（危险操作用 `danger` 字）
- 灰色做主色
- 渐变按钮、霓虹描边、彩色投影、浓重的投影
- 用一块块灰底色堆出层次；卡片里再套一层描边
- 用 `text-placeholder` 写要读的文字
- 卡片也用磨砂（磨砂只给浮在内容上方的东西）；磨砂带颜色
- 写死的颜色、圆角和尺寸；大于 16 的圆角。full 只给标签和徽章、浮动标签栏、浮动按钮
- 小于 `hit-min` 的点击区
- 第二个强调色

## 写界面时自查

- [ ] 浅色、深色两种模式都看过，深色不是简单反色
- [ ] 主色只出现在可交互元素上，一屏面积 ≤ 10%；没有暖色或红底按钮
- [ ] 卡片和列表靠 1 px 细线分开，没有一层套一层的描边
- [ ] 导航栏、标签栏是磨砂，有细线，没有颜色；内容滚到下面时栏上文字仍然清楚
- [ ] 要读的文字只用 `text` 和 `text-2`；`text-placeholder` 只在占位、禁用、chevron、装饰图标上
- [ ] 圆角只用 token；full 只在标签和徽章、浮动标签栏、浮动按钮上
- [ ] 点击区 ≥ `hit-min`，控件高度用 `control-h`
- [ ] 状态色只在对应状态出现；和主色同源的状态徽章带图标
- [ ] 图标只用一套库、一种线宽，选中态做法统一

## 接入

- **Web**：先引入 `theme.css`，用 `var(--c-primary)` 等变量；每个不透明颜色另有 `--c-*-rgb` 通道变量，可写 `rgb(var(--c-primary-rgb) / .1)`。`<html data-theme="dark">` 强制深色，不写则跟随系统。浮在内容上方的元素加 `class="frost"`，浮动的再加 `box-shadow: var(--elev-2)`。尺寸是 `--hit-min`、`--control-h-sm / md / lg`。
- **Tailwind**：在 `presets` 里加 `tailwind.preset.js`（v3.3 以上，仍要先引入 `theme.css`）。可用 `bg-surface`、`text-text-2`、`border-border-strong`、`shadow-e1`、`rounded-lg`、`min-h-hit`、`h-control-md`；透明度修饰符可用，如 `bg-primary/10`。不写颜色的 `border` 默认是 `border` 色，`ring` 默认是 `focus` 色。
- **SwiftUI**：把 `Theme.swift` 加进项目，需要 iOS 15 以上。颜色 `Palette.primary`、圆角 `Radius.lg`、间距 `Space.s4`、尺寸 `Size.hitMin`、`Size.controlLg`；字体 `.font(.appBody)` 等（基于系统文字样式，支持动态字体），长段正文 `.bodyLong()`；动效 `Motion`。卡片加 `.card()`；浮层加 `.frost()`，顶部导航栏 `.frost(edges: .bottom)`，标签栏、浮动按钮 `.frost(radius: 高度的一半, floating: true)`。用 Xcode 26 编译、运行在 iOS 26 及以上时，`.frost()` 自动改用系统的 Liquid Glass（`glassEffect`），它自带边缘和层次，所以不再画细线和投影；更早的系统仍是磨砂色 + 系统模糊 + 细线。
- **Jetpack Compose**：把 `Theme.kt` 放进 `theme` 包，用 `AppTheme { … }` 包住界面，需要 Compose Material 3 1.2 以上。所有 Material 3 颜色角色都已填好，组件自动取 `MaterialTheme.colorScheme`；Material 3 没有的颜色用 `AppTheme.colors`（如 `AppTheme.colors.success`、`AppTheme.colors.textPlaceholder`）。
  - 主按钮用 `AppButton`，次按钮用 `AppOutlinedButton`，筛选标签用 `AppChip(selected, onClick, label)`，状态标签用 `StatusTag("已完成", AppTheme.colors.success, AppTheme.colors.successContainer)`。不要直接用 `Button`、`FilterChip`：它们会变成 Material 默认的胶囊按钮和 8 dp 圆角的标签。
  - 危险操作：`AppOutlinedButton(onClick) { Text("删除", color = MaterialTheme.colorScheme.error) }`。
  - 卡片用 `OutlinedCard`（边框取 `outlineVariant`，即 `border`）；输入框的 `outline` 是 `border-strong`。磨砂用 `Frost.fill(dark)` 和 `Frost.border(dark)`，Compose 没有自带的背景模糊，需要时用 Haze 这类库。尺寸是 `AppSize.hitMin`、`AppSize.controlLg`。
- **其他框架**（UIKit、Flutter、React Native 等）：按 `tokens.json` 同名 key 映射，例如 `color.light.primary`、`color.dark.text-2`、`radius.lg`、`size.control-h.md`、`font.scale.body-long`（字号、行高、字重、字距）。
