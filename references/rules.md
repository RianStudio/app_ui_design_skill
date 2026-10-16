# 主题规则：石墨

一句话：**深石墨和纸白两套 LCh 中性色阶梯，用 1 px 发丝线和明度差分层，单一强调色，键盘优先，排得密但不挤。** 中性色和 app 图标的底是同一种石墨（色相 265），图标放在侧栏顶部和导航栏里看起来是一家。

线条、密度和克制来自 Linear；材质、字体和图标规格来自 Apple；无障碍硬指标和动效参数来自 Google。

## 原则

1. **三个输入推出所有颜色。** base（色相 265 的冷石墨）、accent（图标强调色映射来的主色）、contrast（`standard` / `high`）。所有表面、边框、文字都在 CIE LCh（D65）里推导，不手写色值。深色优先。
2. **明度差加发丝线分层，不靠投影。** `canvas` < `bg` < `surface` < `surface-2` < `surface-3`，每级约 2.5 L，再加 1 px `border`。卡片不加投影，只有浮层和弹窗有一层大而淡的影子。一个区域只用一道线。
3. **一个强调色，只有七种用途。** 主按钮、焦点环、多选行浅底、链接、复选框和开关打开、进度、未读圆点。侧栏当前项、键盘光标行、菜单当前项、筛选 pill 选中都是中性色。一屏主色面积：桌面 ≤ 5 %，手机 ≤ 8 %。界面主色只有蓝、绿、紫，暖色只留在图标里。
4. **填充和文字分开。** `primary` 是填充（白字 ≥ 4.5:1，深浅同值）；`primary-text` 是链接、选中文字和焦点环（深色更亮、浅色更暗）。不要拿 `primary` 写字，也不要拿 `primary-text` 做按钮底（Compose 的复选框和开关例外，见「用法速查」）。
5. **密但不挤。** 桌面和 Web 正文 13–14、列表行 36；手机沿用平台字号和 44 / 48 点击区，不套桌面密度。
6. **键盘优先。** 每个动作只有一个名字和一个快捷键，都能在 ⌘K 里搜到；快捷键写在 tooltip、菜单、命令菜单和空状态里，顺便教会用户。
7. **立即响应。** 本地操作乐观更新，不显示 spinner；悬停 0 ms 出现、150 ms 淡出；动效短，几乎不回弹。
8. **可读性是硬指标。** 对比度表（见「颜色」）由 `build.py` 断言，不过就不输出；高对比档一起生成，跟随系统设置。不要手动调回去。
9. **平台原生。** iOS 用系统栏和 Liquid Glass，Android 用 Material 3 组件和全部颜色角色，Web 和桌面用倒 L 布局。

## 颜色

### 三个输入

| 输入 | 规则 |
|---|---|
| base | 色相 265，彩度深色 1.6、浅色 1.2，纯白不加彩度。不跟主色变 |
| accent | 图标强调色按 SKILL.md 第 1 步的表映射成主色：蓝→蓝，绿→绿，紫→紫，珊瑚、黄、灰→蓝。主色保留强调色的色相和彩度，只调 L，超出色域时降彩度 |
| contrast | `standard`（相当于 Linear 的 30）和 `high`（相当于 Linear 的 100），两档都生成 |

**强调色**（浅 → 主），和 `rian-app-icon` 的强调色表相同：

| 名 | 色值 | 在界面里 |
|---|---|---|
| 蓝 | `#7AAEFF → #3B7BEA` | 默认主色；珊瑚、黄、灰的图标也用它；`info` 的来源 |
| 绿 | `#6FD3A6 → #23A36B` | 图标是绿时做主色；`success` 的来源 |
| 紫 | `#B3A6FF → #7A63F0` | 图标是紫时做主色 |
| 黄 | `#FFD978 → #F2AE2E` | 不做主色，只留在图标；`warning` 的来源 |
| 珊瑚 | `#FF9C86 → #EC5B45` | 不做主色，只留在图标；`danger` 的来源 |
| 灰 | `#C8C7C3 → #8E8D89` | 不做主色：和次要文字太像，选中和未选中分不出 |

### 中性色阶梯

L 来自 `assets/palette.json` 的 `ladder` 和 `text`；文字和 `border-strong` 由 `build.py` 只往对比度更高的方向微调。下表色值是 `build.py` 的实际输出，和主色无关，以 `tokens.json` 为准。

| token | 深色 L | 深色 | 浅色 L | 浅色 | 用在 |
|---|---|---|---|---|---|
| `canvas` | 5.5 | `#111215` | 97.5 | `#F6F8FA` | 倒 L 外框：侧栏、桌面顶栏。比内容区暗，让内容占主导 |
| `bg` | 8 | `#16181A` | 100 | `#FFFFFF` | 主内容区、手机页面 |
| `surface` | 10.5 | `#1B1D1F` | 100 | `#FFFFFF` | 卡片、列表组、输入框底 |
| `surface-2` | 13 | `#202224` | 96.5 | `#F4F5F7` | 悬停或键盘光标所在的行、侧栏当前项、次按钮、代码块 |
| `surface-3` | 16 | `#26282A` | 94 | `#ECEEF0` | 按下、筛选 pill 选中、导航指示器、骨架块、进度条剩余段 |
| `elevated` | 12 | `#1E2022` | 100 | `#FFFFFF` | 弹出菜单、命令菜单、弹窗、toast、tooltip |
| `menu-active` | `elevated` 叠白 8 % | `#303234` | 同 `surface-3` | `#ECEEF0` | 命令菜单、右键菜单、弹出菜单的当前项（深色下 `surface-3` 叠在 `elevated` 上只差 4 L，看不出来） |
| `border-strong` | 46 | `#6B6D70` | 59 | `#8D8E90` | 只给控件边界：表单输入框、复选框、关闭态的开关（≥ 3:1） |
| `text` | 96 | `#F2F4F7` | 10 | `#1B1C1D` | 标题、正文 |
| `text-2` | 78 | `#BFC1C4` | 31 | `#48494B` | 次要文字、未选中的标签、手机列表的元数据 |
| `text-3` | 64 | `#999B9E` | 43 | `#646667` | 元数据、时间、分组标题、编号、图标默认色 |
| `text-placeholder` | 52 | `#7A7C7F` | 55 | `#828486` | 只给占位、禁用、装饰；不写要读的字 |

带透明度的 token（叠在下面的颜色上）：

| token | 深色 | 浅色 | 用在 |
|---|---|---|---|
| `border` | 白 7 % | 黑 8 % | 发丝线：卡片、分隔、弹层边。纯装饰，不要求对比度 |
| `hover` | 白 4 % | 黑 4 % | 悬停层，叠在行和按钮上 |
| `pressed` | 白 7 % | 黑 7 % | 按下层 |
| `scrim` | 黑 50 % | 黑 20 % | 只给弹窗和底部弹窗 |
| `scrim-menu` | 黑 24 % | 黑 8 % | ⌘K 命令菜单和弹出层后面：后面的列表仍然看得清 |
| `frost` | `elevated` 80 % | 白 80 % | 浮动栏的玻璃（高对比 94 %） |
| `frost-border` | 白 8 % | 黑 6 % | 玻璃边线 |
| `frost-highlight` | 白 6 % | 白 50 % | 玻璃顶部 1 px 内高光 |

### 高对比档

- `text` 取端点：深色 L 100（`#FFFFFF`），浅色 L 6（`#121315`）。
- `text-2` 深 91 `#E3E5E8` / 浅 21 `#313334`（≥ 10:1）；`text-3` 深 78 `#BFC1C4` / 浅 31 `#48494B`（≥ 7:1）；`text-placeholder` 深 64 `#999B9E` / 浅 43 `#646667`（≥ 4.5:1）。
- `primary-text` 和各状态色从标准档的 L 出发，只往对比度更高的方向走（深色升 L、浅色降 L），到 ≥ 7:1 为止。例：绿的 `primary-text` 深 L 77.5 `#5FD599`、浅 L 33.5 `#005B38`。
- 每一项的最低对比度都不低于标准档（`build.py` 断言）。
- `border` 换成 `border-strong`（不透明）；`frost` 不透明度提到 .94。
- 表面阶梯、`border-strong`、`primary` 填充和 `selected` 不变。

### 主色

| token | 规则 |
|---|---|
| `primary` | 填充：主按钮、复选框和开关打开、进度、FAB。四套同值，取白字刚好 ≥ 4.5:1 的最高 L（三种主色都是 L 49.5） |
| `on-primary` | 白 `#FFFFFF` |
| `primary-hover` / `primary-pressed` | `primary` 的 L 分别 −4、−8，四套一样（悬停变暗；再提亮白字就不过了） |
| `primary-text` | 链接、选中的标签文字和图标、收入金额。在所有表面、`frost` 和 `selected` 上 ≥ 4.5:1：深色约 L 64，浅色约 L 43.5；高对比约 L 77.5 / 33.5 |
| `selected` | 多选的行：`primary` 在深色叠 16 %、浅色叠 10 % 合成到 `bg` 上 |
| `focus` | 等于 `primary-text`，2 px 实色环 |
| `primary-container` / `on-primary-container` | 给 Compose 和同源状态徽章用：`primary` 混向 surface 85 %（深）/ 90 %（浅）；字等于 `primary-text` |
| `selection` | 文字选中的底：`primary` 在深色叠 28 %、浅色叠 16 %。`text` 和 `text-2` 在上面也要过对比度 |

`build.py` 的实际输出（深 / 浅；高对比深 / 浅）：

| 主色 | `primary` | `primary-hover` / `primary-pressed` | `primary-text` | `primary-text` 高对比 |
|---|---|---|---|---|
| 蓝（图标蓝、珊瑚、黄、灰） | `#2B72E0` | `#0F69D5` / `#005FC4` | `#6E97FF` / `#0064CD` | `#ADBDFF` / `#004CA0` |
| 绿 | `#008755` | `#007C4D` / `#007146` | `#34AF76` / `#00764A` | `#5FD599` / `#005B38` |
| 紫 | `#755FEB` | `#6955E0` / `#5D4BD4` | `#A389FF` / `#6350DA` | `#C9B4FF` / `#4338BE` |

**主色只有七种用途**：主按钮、焦点环、多选行的浅底（`selected`）、链接、复选框和开关打开、进度、未读圆点（6 px）。侧栏当前项和键盘光标行用中性的 `surface-2`，菜单当前项用 `menu-active`，筛选 pill 选中用 `surface-3`，都不用主色。一屏主色面积桌面 ≤ 5 %、手机 ≤ 8 %；`selected` 是状态，不计入这个预算。

### 状态色

- 来源：`success` ← 绿、`warning` ← 黄、`danger` ← 珊瑚、`info` ← 蓝。各自有 `X`（文字和图标，≥ 4.5:1，算法同 `primary-text`）、`X-container`（浅底，`X` 的强调色「主」混向 surface 85 % / 90 %）、`on-X`（实心状态色上的字：浅色是白，深色是 `bg` 色）。
- 实际输出（深 / 浅）：`warning` `#F2AE2E` / `#8A5F00`，`danger` `#FF6C54` / `#BE3224`，`info` `#6E97FF` / `#0064CD`，`success` `#34AF76` / `#00764A`。
- 和主色同源的状态（绿主题的 `success`、蓝主题的 `info`）直接复用 `primary-text` 和 `primary-container`，徽章上必须带图标，否则读起来像链接或选中态。
- 只在状态出现时用。红色只用于错误和危险操作。
- 状态图标是一组 16 px 的圆：待办 `text-3` 空心圈；积压虚线圈；进行中 `warning` 部分填充的饼；完成 `success` 实心勾；取消 `text-3` 实心叉。
- 「完成」是默认态的列表（记账：已入账）不画状态图标，只留 16 px 列宽让标题对齐，只给例外画：待确认（空心圈）、报销中（`warning` 饼）、已退款（`text-3` 实心叉，标题和金额加删除线）。
- 优先级：三根递增竖条（`text-3`）；紧急是 `danger` 实心圆角方块加「!」。

### 对比度要求

`build.py` 对四套颜色都断言下表，标准和高对比各打印一张矩阵；任何一项不过就什么都不写、退出码 1。「所有底」是矩阵的十列：`canvas`、`bg`、`surface`、`surface-2`、`surface-3`、`elevated`、`menu-active`、`frost/bg`、`frost/mid`、`selected`（`frost/bg`、`frost/mid` 是玻璃叠在 `bg` 和 `#808080` 上的合成色）。

| 前景 | 底 | 标准 | 高对比 |
|---|---|---|---|
| `text` | 所有底，再加 `selection` | ≥ 7:1（目标 15:1，没到标 `~`） | ≥ 12:1（目标 15:1） |
| `text-2` | 所有底，再加 `selection` | ≥ 7:1 | ≥ 10:1 |
| `text-3` | 所有底 | ≥ 4.5:1 | ≥ 7:1 |
| `text-placeholder` | 所有底 | ≥ 3:1 | ≥ 4.5:1 |
| `primary-text`、各状态色 | 所有底，再加各自的 container | ≥ 4.5:1 | ≥ 7:1 |
| `on-primary` | `primary`、`primary-hover`、`primary-pressed` | ≥ 4.5:1 | ≥ 4.5:1 |
| `on-X` | 实心的 `X` | ≥ 4.5:1 | ≥ 4.5:1 |
| `primary`（作为填充） | `bg`、`surface` | ≥ 3:1 | ≥ 3:1 |
| `border-strong`、`focus` | `bg`、`surface`、`surface-2`、`elevated` | ≥ 3:1 | ≥ 3:1 |
| `on-inverse`、`inverse-primary` | `inverse-surface` | ≥ 4.5:1 | ≥ 4.5:1 |
| 栏上的文字 | 滚到栏下的真实内容（`preview.py` 实测） | ≥ 3:1 | |

另加一条：高对比档每一行在所有底上的最低值，不低于标准档的同一行。`border` 发丝线是纯装饰，不要求对比度。

## Token

token 名是 `build.py`、`tokens.json` 和各平台输出共用的契约，写界面时只用这些名字。

| 组 | 内容 |
|---|---|
| 表面 | `canvas`、`bg`、`surface`、`surface-2`、`surface-3`、`elevated`、`menu-active` |
| 线 | `border`、`border-strong` |
| 文字 | `text`、`text-2`、`text-3`、`text-placeholder` |
| 主色 | `primary`、`on-primary`、`primary-hover`、`primary-pressed`、`primary-text`、`selected`、`focus`、`primary-container`、`on-primary-container`、`selection` |
| 状态 | `success`、`warning`、`danger`、`info`，各自的 `-container` 和 `on-*` |
| 叠层 | `hover`、`pressed`、`scrim`、`scrim-menu` |
| 材质 | `frost`、`frost-border`、`frost-highlight` |
| 禁用 | `disabled-fg`（= `text-placeholder`）、`disabled-bg`（= `surface-3`），给填充按钮的禁用态 |
| 反色 | `inverse-surface`（另一种模式的 `surface-3`）、`on-inverse`、`inverse-primary`：只给 Compose 的 inverse 角色（M3 Snackbar）。自定义 toast 用 `elevated` |
| 颜色集 | `light`、`dark`、`light-hc`、`dark-hc` |
| 圆角 | xs 4（kbd、复选框）· sm 6（桌面按钮、输入框、菜单项、侧栏项）· md 8（桌面卡片、列表悬停底、toast）· lg 12（手机卡片和按钮、弹出菜单、命令菜单）· xl 16（弹窗、底部弹窗）· full（标签、头像、筛选 pill、浮动标签栏）。iOS 用 continuous 圆角 |
| 间距 | 4 栅格加 2，key 是 4 的倍数：0.5 = 2 · 1 = 4 · 2 = 8 · 3 = 12 · 4 = 16 · 5 = 20 · 6 = 24 · 8 = 32 · 10 = 40 · 12 = 48 |
| 控件高 | 桌面 `control-h.desktop`：xs 20 · sm 24 · md 28（默认按钮）· lg 32（输入框、主按钮）。手机 `control-h.mobile`：md 44 · lg 50（主按钮） |
| 行和栏 | `row`：desktop 36 · compact 32 · mobile 60（iOS 双行）· mobile-single 44 · android 72（双行）；`sidebar`：width 240（可调 200–320）· item 28；`view-header` 44；`filter-bar` 36；`kbd` 18 |
| 点击区 | `hit-min`：iOS 44 pt，Android 48 dp |
| 阴影 | `elev-0` · `elev-2` · `elev-3`，见下表 |
| 动效 | `hover-in` · `hover-out` · `fast` · `standard` · `slow`，加进场、退场两条曲线，见下表 |
| 模糊 | frost：模糊 24、饱和度 1.5、不透明度 .80（高对比 .94） |
| 图标 | 尺寸 16 / 20 / 24，线宽 1.5 px，不随尺寸缩放 |

从旧版（极简线条）改名的 token 见「接入 → 从旧版升级」。

### 字体

| 平台 | 字体 | 设置 |
|---|---|---|
| Web / 桌面 | Inter Variable（Google Fonts `Inter:opsz,wght@14..32,100..900`）；中文回落 PingFang SC、Noto Sans SC；等宽 `ui-monospace, "SF Mono", "JetBrains Mono"` | 字重只用 400 / 510 / 590，不用 700。`font-feature-settings: "cv01", "ss03"`；金额和计数加 `tabular-nums`。opsz 32 就是 Inter Display，不另外加载 |
| iOS | SF Pro（系统字体），中文 PingFang SC | 510 对应 `.medium`，590 对应 `.semibold`；不另加字距 |
| Android | Roboto Flex（放在 `res/font`，或用 Compose 的可下载字体） | 用 M3 type scale；不用 Google Sans Flex |

中文、日文、韩文不加字距。

**Web / 桌面字号**（字号 / 行高 / 字重 / 字距 em）：

| token | 值 | 用在 |
|---|---|---|
| `display` | 32 / 38 / 590 / −0.022，opsz 32 | 空状态大标题、引导页 |
| `title-1` | 24 / 32 / 590 / −0.0195 | 页面标题 |
| `title-2` | 18 / 24 / 590 / −0.0143 | 弹窗标题、详情标题 |
| `title-3` | 15 / 20 / 590 / −0.0088 | 分组标题、卡片标题、空状态标题 |
| `body` | 14 / 20 / 400 / −0.0062 | 正文、输入框 |
| `body-medium` | 14 / 20 / 510 / −0.0062 | 按钮、强调正文 |
| `small` | 13 / 18 / 400 / −0.0032 | 列表行标题、侧栏项（这两处用 510） |
| `caption` | 12 / 16 / 510 / +0.0005 | 元数据、标签、tooltip |
| `micro` | 11 / 14 / 510 / +0.0048 | kbd、角标 |

**手机字号**（iOS 用系统文字样式，Dynamic Type 要能放大到 AX5，至少 200 %；括号里是默认大小下的字号 / 行高。手机 Web 用同样的数字和 Inter）：

| token | iOS | 用在 |
|---|---|---|
| `page-title` | `.largeTitle` + bold（34 / 41） | 页面标题；用系统导航栏的大标题时不用自己设 |
| `card-title` | `.headline`（17 / 22） | 卡片标题、月度卡片 |
| `long-text` | `.body`（17 / 22），长段中文用 `.longText()`：加 6 pt 行距，合 17 / 28 | 长文、说明。手机 Web 的 `--t-long-text` 直接是 17 / 28 |
| `row-title` | `.subheadline` + `.medium`（15 / 20） | 列表行标题（比 Apple 默认的 17 紧凑一档） |
| `row-meta` | `.footnote`（13 / 18） | 元数据，配 `text-2` |
| `section-header` | `.footnote` + `.medium`（13 / 18） | 分组标题，配 `text-3` |
| `tag-label` | `.caption` + `.medium`（12 / 16） | 标签、筛选 pill |
| `amount` | `.subheadline` + `.medium`，等宽数字（15 / 20） | 列表里的金额 |

Android 用 M3 type scale（sp）：列表行标题 `bodyLarge` 16；元数据 `bodyMedium` 14、`text-2`；标签 `labelMedium` 12 / 500；FilterChip `labelLarge`；正文不小于 12 sp。

### 阴影

| token | 浅色 | 深色 | 用在 |
|---|---|---|---|
| `elev-0` | 无 | 无 | 卡片、列表：只有边框 |
| `elev-2` | `0 4px 12px rgba(0,0,0,.06), 0 8px 24px rgba(0,0,0,.10)` | `0 8px 24px rgba(0,0,0,.50)` | 弹出菜单、tooltip、toast、浮动栏、FAB |
| `elev-3` | `0 8px 16px rgba(0,0,0,.06), 0 24px 64px rgba(0,0,0,.12)` | `0 16px 48px rgba(0,0,0,.60)` | 弹窗、命令菜单 |

弹层一律是 `elevated` 底 + 1 px `border` + 对应阴影。

### 动效

| token | 值 | 用在 |
|---|---|---|
| `hover-in` | 0 ms | 悬停高亮立刻出现 |
| `hover-out` | 150 ms | 悬停高亮淡出 |
| `fast` | 100 ms | 按下、勾选、kbd、颜色和透明度变化 |
| `standard` | 180 ms | 弹出菜单、tooltip、命令菜单出现 |
| `slow` | 250 ms | 弹窗、侧面板、页面切换 |
| `fast-exit` · `standard-exit` · `slow-exit` | 67 · 120 · 167 ms（进场的 2/3） | 所有退场 |

- 曲线：`enter` 是 `cubic-bezier(.2, 0, 0, 1)`（同 Material emphasized），`exit` 是 `cubic-bezier(.3, 0, 1, 1)`。
- iOS：`.spring(response: 0.3, dampingFraction: 0.9)`，几乎不回弹；Liquid Glass 自带的形变保留，不另加弹跳。
- Android：`MotionScheme.standard()`（空间运动 damping 0.9 / stiffness 700，颜色和透明度 damping 1.0 / stiffness 1600）。不用 expressive 方案，它的 fast 档 damping 0.6，回弹太明显。
- 「减弱动态效果」打开时，所有位移和缩放改成 0 ms 或纯淡入淡出。

## 用法速查

**布局**：

- **Web / 桌面**是倒 L：`canvas` 的侧栏和顶栏框住 `bg` 主视图；视图头（高 44）放视图名、筛选和显示选项，下面可以有筛选条（高 36）；属性放右侧面板。
- **手机**：页面 `bg`，列表组和卡片 `surface`；iOS 用系统栏，Android 见「平台适配」。
- **分隔**：先靠明度阶梯，再靠 1 px `border`。桌面列表行之间不画线，组之间用组头分开；手机列表用从文字左边开始的内缩分隔线（Android 双行列表不画线）。卡片里不再套描边。

| 组件 | 规格 |
|---|---|
| 卡片、列表组 | `surface` 底、1 px `border`、`elev-0`；圆角桌面 md 8、手机 lg 12。Compose 用 `AppCard`，不直接用 `Card`（默认是 `surface-3` 灰底、无描边） |
| 主按钮 | `primary` 底、`on-primary` 字、`body-medium`；悬停 `primary-hover`、按下 `primary-pressed`。桌面高 28 / 32、圆角 6、左右内边距 12；手机高 50、圆角 12。不加影子。一屏最多一个。桌面列表、看板这类顶层视图的视图头不放主按钮：新建入口是侧栏的编辑图标加 C 键（tooltip 写「记一笔 C」）；主按钮只用在弹窗和表单的确认上 |
| 次按钮 | `surface-2` 底、1 px `border`、`text` 字 |
| 幽灵按钮 | 透明底，悬停叠 `hover`、按下叠 `pressed`；图标按钮 28 × 28、圆角 6 |
| 危险操作 | 次按钮样式，字用 `danger`；不用红底 |
| 禁用 | 文字和图标换 `disabled-fg`（= `text-placeholder`）；填充按钮换成 `disabled-bg` 底、`disabled-fg` 字；不响应悬停 |
| 输入框（表单） | `surface` 底、1 px `border-strong`、圆角 6、桌面高 32、左右内边距 10；聚焦时边框换成 `focus`，再向外扩 1 px（合计 2 px 实色 `focus` 环），外面不再加焦点环；占位 `text-placeholder`。Web 用 `theme.css` 的 `.input` |
| 内联编辑字段 | 标题、描述这类：平时无边框；悬停显示 `surface-2` 底和文本光标；聚焦只显示插入光标；键盘聚焦时加 2 px 焦点环。Web 用 `.inline-edit`，键盘进入时由脚本加 `.kb-focus`（见「接入」） |
| 键盘焦点 | 2 px `focus` 环，离控件 2 px；`theme.css` 已经给 `:focus-visible` 写好。文本框点一下也算 `:focus-visible`，所以 `.input`、`.inline-edit` 自己处理焦点，不吃这个环 |
| 文字选中 | `selection` 底，文字保持 `text`；`theme.css` 已经给 `::selection` 写好 |
| 复选框、开关 | 关闭态边框 `border-strong`；打开、勾选后 `primary` 底、`on-primary` 白勾（Web 和 iOS 自己画的控件）。复选框圆角 xs 4。Compose 的 Checkbox、Switch 取 `colorScheme.primary`，也就是 `primary-text`；勾和开关圆钮取 `onPrimary`：浅色是白，深色是 `bg` 的深色（约 6.4:1，高对比约 9.7:1）。这是有意的，不要改成白色：白色在深色 `primary-text` 上只有约 2.8:1 |
| 列表行（桌面） | 高 36（紧凑 32），左右内边距 12。依次是：优先级 16、编号 `caption` 等宽 `text-3`、状态图标 16、标题 `small` 510 `text`、右侧标签、头像 18、日期 `caption` `text-3`。悬停叠 `hover`（0 ms 进、150 ms 出）；键盘光标行 `surface-2`；多选行 `selected` 加复选框 |
| 记账行（桌面变体） | 分类图标 16 `text-3`、状态图标列（只画例外）、标题 510 `text`、备注 `text-3`、右侧标签、账户、时间 `caption` `text-3`、金额 tabular 右对齐（支出 `text`，收入 `primary-text`） |
| 组头（桌面） | 高 36，吸顶，13 / 590 `text` 加 `text-3` 计数（比 `title-3` 小一档） |
| 列表行（iOS） | 双行 60：行首是裸的 20 pt 线性分类图标（`text-3`，不加底块），贴 16 pt 边距；标题 15 / 510，元数据 13 `text-2`；右侧金额 tabular；分隔线从标题左边开始。单行 44 |
| 列表行（Android） | 双行 72 dp：图标 24、标题 `bodyLarge` 16、元数据 `bodyMedium` 14 `text-2`，不画分隔线。单行 48 |
| 标签 | 高 20（手机 24），圆角 full，左右内边距 8，`caption` `text-2`，1 px `border`，可选 8 px 状态色圆点 |
| 筛选 pill | 选中用 `surface-3` 底加 `text`（中性），不用主色。iOS 视觉高 36、左右内边距 14，点击区用 `.contentShape(Capsule())` 加上下 padding 补到 44。Android 用 M3 FilterChip：高 32、点击区 48、圆角 6，选中带 18 dp 的勾 |
| 进度条 | 高 6（桌面 4），圆角 full；已用段 `primary`，剩余段 `surface-3`，两段之间留 2 px 间隙，不画成连续的条 |
| 状态徽章 | `X-container` 底、`X` 字、圆角 full；和主色同源时带图标 |
| 未读圆点 | 6 px `primary` |
| 侧边栏 | `canvas` 底，宽 240。顶部是工作区切换（高 44，带 app 图标）和搜索、新建两个图标按钮。项高 28、圆角 6、左右内边距 8；图标 16 `text-3`，文字 `small` 510 `text-2`；当前项 `surface-2` 底、`text` 字；计数 `caption` `text-3` 右对齐。分区标题 `caption` `text-3`，可以折叠。底部放同步状态（6 px 圆点加「已同步」） |
| 标签栏 | iOS 用系统 TabView（Liquid Glass），选中色 `primary-text`。Android 用 `AppNavigationBar`（M3 NavigationBar 加顶线）：高 80（另加系统手势区 inset），`surface` 底加顶部 1 px `border`，不加色调提升，指示器 pill 64 × 32 用 `surface-3`，选中的图标（FILL 1）和文字 `primary-text`。Web 手机版是浮动玻璃 pill：高 56、左右各留 16、悬在安全区上方 8，未选中 `text-3`，选中 `primary-text` |
| FAB（Android） | 56 dp，`primary` 底、白色「+」、圆角 16、`elev-2` |
| 弹窗 | `elevated`、圆角 16、`elev-3`、后面铺 `scrim`。宽 440（确认）或 560（表单），内边距 20；标题 `title-2`，正文 `body` `text-2`；操作按钮右对齐，次按钮在左、主按钮在右。Esc 关闭，⌘↵ 确认。手机用系统 sheet |
| toast | `elevated`、1 px `border`、`elev-2`、圆角 8、高 40。左边 16 px 状态图标，中间 `small` 510 文字，右边「撤销」用 `primary-text` 加 kbd ⌘Z。桌面在左下（离开右侧属性面板），手机在标签栏上方居中。停 4 s，悬停时暂停，最多叠 3 条。iOS 是自定义浮层：高 44、圆角 full，「撤销」点击区 44。Android 用 M3 Snackbar |
| kbd | 高 18、最小宽 18、左右内边距 4、圆角 4；`micro` 510 等宽数字，`text-2` 字、`surface-2` 底、1 px `border`；多个键之间隔 4。序列键写成 `G` 然后 `S`，「然后」用 `micro` `text-3`。mac 显示 ⌘ ⌥ ⇧ ⌃ ↵，Windows 和 Linux 显示 Ctrl、Alt、Shift |
| tooltip | `elevated`、`caption`、圆角 6、延迟 500 ms，带 kbd |
| 弹出菜单 | `elevated`、圆角 12、1 px `border`、`elev-2`、后面铺 `scrim-menu`；当前项 `menu-active` |
| 玻璃（frost） | 只给浮在内容上的栏和按钮：Web 手机版的浮动标签栏、自定义浮动按钮。toast 不用玻璃，用 `elevated`（见上面 toast 行）。`frost` + 1 px `frost-border` + 顶部 1 px `frost-highlight`，浮动的再加 `elev-2`。iOS 系统栏自带 Liquid Glass，不另加；卡片、列表、弹窗不用玻璃 |

## 命令菜单

⌘K（Windows、Linux 是 Ctrl K）打开。

- **容器**：宽 640（最大 90vw），距顶 20vh；`elevated` 底、圆角 12、1 px `border`、`elev-3`；后面铺 `scrim-menu`（不是弹窗的 `scrim`）。出现：opacity 0 → 1 加 scale .98 → 1，180 ms。
- **上下文 chip**（可选）：高 22，在输入行上方，例如「Ledgerly · 10月」。
- **输入行**：高 52，字号 15，无边框，占位「输入命令或搜索…」，下面一条 `border` 发丝线。
- **结果区**：最高 400，可滚动。
  - 组标题 `caption` `text-3`，内边距 8 / 12 / 4。常用分组：动作、转到、最近、帮助。
  - 项高 36、圆角 8、左右各缩进 6；左边图标 16 `text-3`，中间文字 `body`，右边 kbd。
  - 当前项 `menu-active` 底（中性，不用主色）。
  - 模糊匹配命中的字符用 `text` 加 590 字重，其余字用 `text-2`。没有命中的分组整组隐藏。
- **底栏**：高 36，「↑↓ 选择 · ↵ 执行 · esc 关闭」，`caption` `text-3`。
- **一致性**：命令菜单里的项和右键菜单、按钮、批量操作条、快捷键速查完全一致，每个动作只有一个名字和一个快捷键。

## UX 模式

| 模式 | 规则 |
|---|---|
| ⌘K | 所有页面和动作都能搜到。手机上的对应入口：iOS 用顶部搜索按钮或标签栏的 search 角色，Android 用 SearchBar 展开成全屏搜索 |
| 快捷键 | 单键：C 新建、/ 搜索、? 打开速查。G 序列：G 加首字母跳到对应视图（G I 明细、G S 统计）。J / K 或 ↑ / ↓ 移动，X 选中，↵ 打开，Esc 返回或关闭，⌘Z 撤销。快捷键出现在 tooltip、菜单、命令菜单和空状态里 |
| 乐观更新 | 本地操作立即生效，不显示 spinner。后台同步失败时回滚，并弹出 `danger` toast「没能保存 · 重试」。只有纯网络操作超过 1 s 时，才在按钮里显示 16 px 的 `text-3` 圆环 |
| 内联编辑 | 点一下就能编辑。单行 ↵ 提交，多行 ⌘↵ 提交；Esc 取消并还原；失焦时提交；5 s 内可以用 toast 撤销 |
| 右键菜单 | 所有条目都能右键。宽 220–280，项高 28、圆角 6，`small`，图标 16 `text-3`，kbd 右对齐；分隔线上下各留 4；危险项放最后，用 `danger` 字。子菜单用安全三角（clip-path），鼠标可以斜着移过去。手机上长按调出系统菜单 |
| 空状态 | 视图中央，最大宽 360：24 px 线性图标 `text-3`、`title-3` 标题、一行 `text-2` 说明、一个主按钮加 kbd 提示（「记一笔 C」）。不放插画 |
| 加载骨架 | 300 ms 内不显示任何东西，超过才显示。形状和真实的行一样：高 36，块用 `surface-3`、圆角 4，宽度在 40–70 % 之间固定交替。透明度在 1 和 .5 之间脉冲，周期 1.2 s；「减弱动态效果」时不动。不用 shimmer 扫光 |
| 文案格式 | 日期按系统中文格式，不加空格：「2026年10月」「10月16日 周五」。数量和单位之间留一个空格：「128 笔」「还有 15 天」。金额一律带货币符号和正负号：「−¥32.00」「+¥18,500.00」（减号用 U+2212），等宽数字。一个动作只有一个名字（例：「导出本月记录 CSV」）；作用对象不同就是另一个动作，另起名字 |

## 图标

界面图标是**线性、细、粗细统一**的一套。一个 app 只用一套图标库、一种线宽。

| 平台 | 图标库 | 设置 |
|---|---|---|
| Web / 桌面 | Lucide | 线宽 1.5 px，加 `vector-effect: non-scaling-stroke`，各尺寸下线宽都是 1.5 px；用 `currentColor` 着色 |
| iOS | SF Symbols | `.regular`；和文字并排时跟随文字样式 |
| Android | Material Symbols **Rounded** | weight 300、fill 0、grade 0 |

| 项目 | 规则 |
|---|---|
| 尺寸 | 16（桌面默认：列表、侧栏、菜单、按钮）· 20（手机列表）· 24（栏、空状态） |
| 颜色 | 默认 `text-3`；可点的强调和选中用 `primary-text`；状态图标用对应状态色 |
| 选中态 | 只换颜色，线宽不变。iOS 标签栏、Android 导航栏的选中项可以换实心版（Android FILL 1）；别的地方不混用实心和线性 |
| 列表图标 | 裸图标，不加底块、不加线框方块 |
| 状态和优先级 | 用「颜色 → 状态色」里那组 16 px 的圆和竖条，不用库里的通用图标代替 |
| 对齐 | 和文字垂直居中；图标和文字间距 8（行内、菜单）或 12（手机列表） |

**不用 Font Awesome 当主力图标库**：免费版只有粗的 Solid 和 Regular，细的 Light / Thin 只在付费版；线宽和圆角不统一，和 1.5 px 的细线、和系统图标并排时显得粗笨。已经在用 Pro 版时，可以全站统一用 Light，不和 Solid 混用。

也不要：混用两套图标库；彩色或渐变图标；给图标加投影。App 图标（主屏图标）不在此列，用 `rian-app-icon` 做。

## 平台适配

**iOS 26 / 27（Liquid Glass）**：

- 用系统的 NavigationStack、toolbar 和 TabView，栏不设任何自定义背景；栏和内容的分隔交给 `scrollEdgeEffectStyle(.soft)`。
- 工具栏最多 3 组，文字按钮和图标按钮之间用 `ToolbarSpacer(.fixed)` 隔开。全屏只有一个主操作时用 `.buttonStyle(.glassProminent)` 加 `.tint(primary)`，放在尾侧。
- 自定义的浮动控件用 `.glassEffect(.regular.interactive(), in: .capsule)`，多个放进同一个 `GlassEffectContainer`。内容层（列表、卡片）不用玻璃。
- 部署目标低于 26 时，`.frost()` 回落到 `.ultraThinMaterial` 加发丝线和顶部内高光。
- 列表用 `.plain` 样式加自定义行。
- iOS 27 可选：`.tabBarMinimizeBehavior(.onScrollDown)`；把「新建」做成 `Tab(role: .prominent)`。
- 每个颜色都有浅色、深色、增强对比度的值：`Theme.swift` 用动态 `UIColor`，按 `userInterfaceStyle` × `accessibilityContrast` 四选一。
- 系统栏和控件跟随系统的同心圆角，不强改成小圆角。

**Android（Material 3）**：

- 基线是 Compose Material3 1.4（stable）。用固定品牌色方案，关掉动态取色；M3 颜色角色都已填好（1.4 新增的 fixed 系列除外），组件直接取 `MaterialTheme.colorScheme`；Shapes extraSmall 4 / small 6 / medium 8 / large 12 / extraLarge 16；Typography 用 Roboto Flex（字体文件自己放进 `res/font`，见「接入」）。
- TopAppBar 用不透明的 `bg` 底、高 64，滚动后只加一条 `border`，不加色调提升。
- 必须做到：edge-to-edge（用 WindowInsets）、预测性返回、自定义控件用 `minimumInteractiveComponentSize()`。
- **M3 Expressive**（接受 1.5.0-beta01 时）：用 `MaterialExpressiveTheme(colorScheme = 显式传入, motionScheme = MotionScheme.standard())`；批量操作用 FloatingToolbar；相关按钮用 ButtonGroup。不用 MaterialShapes、LoadingIndicator（仍是实验 API）、expressive 动效、Wavy 进度条。
- Compose 没有系统级背景模糊，栏用不透明底；需要玻璃时用 Haze 这类库，参数同 `frost`。
- 高对比：API 34 以上读 `UiModeManager.getContrast()`，≥ 0.5 时换成 hc 颜色方案。

**Web / 桌面**：

- 倒 L 布局（见「用法速查」）。
- `prefers-color-scheme` 和 `[data-theme]` 切换深浅色，`prefers-contrast: more` 换高对比，`prefers-reduced-motion` 减弱动效；`theme.css` 已经写好这几条。

## 不要

- 大面积的主色（整屏绿、主色顶栏）；主色出现在七种用途以外
- 用主色标侧栏当前项、键盘光标行、菜单当前项或筛选 pill 选中
- 拿 `primary` 写字，或拿 `primary-text` 做按钮底
- 红色、橙色或黄色的主按钮；红底的删除按钮（危险操作用 `danger` 字）
- 灰色做主色；第二个强调色
- 卡片投影；渐变按钮、霓虹描边、彩色投影、内阴影
- 卡片里再套一层描边；桌面列表行之间画分隔线
- 用 `text-placeholder` 写要读的文字
- 卡片和列表用玻璃；玻璃带颜色；Android 栏用色调提升
- 写死的颜色、圆角、尺寸和时长；手写色值代替 LCh 推导
- 弹窗以外用 `scrim`；命令菜单后面铺 `scrim`（用 `scrim-menu`）
- 本地操作显示 spinner；300 ms 内就出骨架；shimmer 扫光
- 同一个动作在不同地方叫不同的名字，或有两个快捷键
- 空状态放插画
- 字重 700；中日韩文字加字距
- 小于 `hit-min` 的点击区；手机套用桌面密度
- 回弹明显的动效（Compose expressive 方案、大弹簧）

## 写界面时自查

- [ ] 浅色、深色都看过；打开系统的增强对比度也看过一次
- [ ] 主色只出现在七种用途上，一屏面积桌面 ≤ 5 %、手机 ≤ 8 %；没有暖色或红底按钮
- [ ] 侧栏当前项、光标行用 `surface-2`，菜单当前项用 `menu-active`，筛选 pill 选中用 `surface-3`
- [ ] 文字用 `text` / `text-2` / `text-3`；`text-placeholder` 只在占位、禁用、装饰上；链接和选中文字用 `primary-text`
- [ ] 层次靠明度差和 1 px `border`；卡片没有投影；浮层是 `elevated` + `border` + `elev-2` / `elev-3`
- [ ] 每个动作有一个名字、一个快捷键，在 ⌘K 里能搜到，tooltip 和菜单里显示 kbd
- [ ] 本地操作乐观更新，失败回滚并给 `danger` toast；可撤销的操作给「撤销 ⌘Z」
- [ ] 悬停 0 ms 进、150 ms 出；「减弱动态效果」下没有位移和缩放
- [ ] 桌面行高 36、正文 13–14；手机点击区 ≥ 44 / 48，字号跟平台
- [ ] 图标只用一套库：Lucide 1.5 px 不缩放 / SF Symbols regular / Material Symbols Rounded 300；默认 `text-3`
- [ ] iOS 用系统栏和 Liquid Glass，栏没有自定义背景；Android TopAppBar 不透明、无色调提升
- [ ] 金额带符号和货币、tabular 数字；日期、数量按「文案格式」

## 接入

API 名称以 `build.py` 的实际输出为准（下面按当前版本写）；拿不准时打开生成的文件看注释。

**从旧版升级**（旧版是「极简线条」主题）。能做别名的在 `theme.css`、`tailwind.preset.js`、`Theme.swift`、`Theme.kt` 里保留一个版本，新代码不要用；做不了别名的必须手动改：

| 旧 | 新 | 处理 |
|---|---|---|
| `--control-h-sm / md / lg` = 32 / 44 / 50（手机控件） | 手机 `--control-h-mobile-md / lg` = 44 / 50；手机筛选 pill 高 36 | **同名改了含义**，现在是桌面的 24 / 28 / 32。不报错，控件只会悄悄变矮，必须搜出来改 |
| `.icon` 默认 24，`.icon.sm` 16、`.icon.xl` 28 | `.icon` 默认 16，`.icon.md` 20、`.icon.lg` 24 | 原来不带尺寸类的 `.icon` 加 `.lg`；`.icon.xl`、`--icon-xl` 留作 24 的别名 |
| `--c-state-hover` / `--c-state-pressed`（Tailwind `bg-state-hover`，Swift `Palette.stateHover`，Kotlin `AppTheme.colors.stateHover`） | `hover` / `pressed` | 别名 |
| `--t-large-title`、`--t-headline`、`--t-body-long`、`--t-footnote`、`--t-caption` 和同名 `.t-*` 类 | `page-title`、`card-title`、`long-text`、`row-meta`、`tag-label` | 别名，字号行高相同 |
| `--t-title-1 / 2 / 3`、`--t-body`、`--t-callout`、`--t-subhead` 和同名类 | 没有对应的语义名 | 保留旧字号和行高（字重 700、600 改成 590），按「手机字号」换成语义名 |
| `--elev-1`（Tailwind `shadow-e1`） | `--elev-0` | 卡片现在没有阴影，别名就是 none |
| `--m-spring`（会回弹） | `--m-standard` 加 `--ease-enter` | 别名，不再回弹 |
| Kotlin `ChipShape` | `TagShape` | `@Deprecated` 别名 |
| Kotlin `AppChip(leadingIcon = if (selected) 勾 else null)` | `AppChip(selectedIcon = 勾)` | 编译报错；勾只在选中时出现，不用自己判断 |
| Swift `Font.appBody` 等、`.bodyLong()`、`.elev1()`、`Size.controlSm`；Kotlin `Motion.SPRING_MS`、`FastEasing`、`AppSize.controlSm` | 「手机字号」的语义名、`.longText()`、`.card()`、`Size.pill`；`Motion.Enter` / `Exit` | 已删除，编译报错，按报错改 |

- **Web**：
  - 先引入 `theme.css`，再加载 Inter：`<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&display=swap">`（或自托管 InterVariable.woff2 4.1）。`theme.css` 不负责加载字体。
  - 颜色是 `var(--c-*)`，例如 `var(--c-primary)`、`var(--c-text-3)`、`var(--c-menu-active)`。四套都不透明的颜色另有 `--c-*-rgb` 通道变量，可写 `rgb(var(--c-primary-rgb) / .1)`；`border`、`hover`、`frost` 这类带透明度的没有。
  - 深浅：`prefers-color-scheme` 自动切换，任何元素上写 `data-theme="light"` 或 `"dark"` 强制；`prefers-contrast: more` 自动换成高对比的两套。
  - 尺寸：圆角 `--r-xs` … `--r-full`；间距 `--s-0_5`、`--s-1` … `--s-12`（`--s-4` 是 16 px）；桌面控件高 `--control-h-xs / sm / md / lg`（20 / 24 / 28 / 32），手机 `--control-h-mobile-md / lg`（44 / 50）；`--row-h`、`--row-h-compact`、`--row-h-mobile`、`--row-h-mobile-single`；`--sidebar-w`、`--sidebar-item-h`、`--view-header-h`、`--filter-bar-h`、`--kbd-h`；`--hit-min`。
  - 字号：桌面用 `.td-*` 类（如 `class="td-small"`，带 opsz、`cv01` / `ss03` 和字距），或 `font: var(--td-small); letter-spacing: var(--tr-td-small)`。手机 Web 用 `.t-row-title`、`.t-row-meta`、`.t-section-header`、`.t-amount` 等（名字同「手机字号」表）。
  - 金额、时间和计数加 `class="num"`（等宽数字），可以和字号类写在一起：`class="td-caption num"`。`.num` 带 `!important`，因为 `font:` 简写会把等宽数字重置掉，你自己 CSS 里的 `font: var(--td-*)` 也一样。
  - 中日韩文字自动去掉字距（`lang="zh-CN"` 等）。中文页面里需要 Inter 字距的拉丁词和数字，包一层 `lang="en"` 或加 `.num`：`<span class="td-display">记一笔 <span lang="en">Ledger</span></span>`。
  - 阴影 `var(--elev-0 / 2 / 3)`（按深浅自动换）；动效 `var(--m-fast)`、`var(--m-standard-exit)`、`var(--ease-enter)`、`var(--ease-exit)`，`prefers-reduced-motion` 下时长自动归零。
  - 现成的类：`.hoverable`（行、菜单项、幽灵按钮：悬停 0 ms 出现、150 ms 淡出，按下叠 `pressed`）；`.frost`（玻璃，带顶部内高光），浮动的写 `class="frost floating"`（多一层 `elev-2`）；`.kbd`，序列键写成 `<kbd class="kbd">G</kbd><span class="kbd-then">然后</span><kbd class="kbd">S</kbd>`；`.icon`（16 px、1.5 px 不缩放、默认 `text-3`），`.icon.md` 20、`.icon.lg` 24，`.icon.active` 换成 `primary-text`。
  - `:focus-visible`（2 px `focus`，offset 2）和 `::selection` 已经写好。
  - 输入框：表单用 `<input class="input">`（`textarea.input`、`select.input` 同样），高 32、`border-strong` 边框，聚焦时边框换成 `focus` 并加粗到 2 px，外面不出环。内联编辑字段（标题、描述）加 `.inline-edit`：悬停 `surface-2` 底，点进去只有插入光标；用键盘进入时加 `.kb-focus` 显示 2 px 环，用下面几行脚本。文本框点一下也算 `:focus-visible`，所以两个类都不吃全局的环；不带这两个类的文本框仍然吃。

    ```js
    // .inline-edit shows the focus ring only when the field was reached from the keyboard
    let viaKey = false;
    addEventListener('keydown', () => { viaKey = true; }, true);
    addEventListener('pointerdown', () => { viaKey = false; }, true);
    addEventListener('focusin', e => { if (e.target.matches('.inline-edit')) e.target.classList.toggle('kb-focus', viaKey); });
    addEventListener('focusout', e => { if (e.target.matches('.inline-edit')) e.target.classList.remove('kb-focus'); });
    ```
- **Tailwind**：在 `presets` 里加 `tailwind.preset.js`（v3.3 以上，仍要先引入 `theme.css`）。
  - 颜色是所有 token 名：`bg-canvas`、`bg-elevated`、`bg-menu-active`、`text-text-2`、`text-text-3`、`text-primary-text`、`border-border-strong`；不透明的可加透明度修饰，如 `bg-primary/10`。不写颜色的 `border` 默认是 `border` 色。
  - 焦点环写 `focus-visible:ring focus-visible:ring-focus`：preset 把 `ring` 的默认宽度和偏移都设成 2 px，就是 2 px `focus` 环、离开 2 px；偏移处填 `bg`，在别的底上加 `ring-offset-surface` 这类。颜色类 `ring-focus` 要写上，不要依赖默认色。
  - 字号是桌面九档：`text-display`、`text-title-1` … `text-caption`、`text-micro`（带行高、字重、字距）；要 opsz 和 `cv01` / `ss03` 时用 `.td-*` 类。
  - 另有 `shadow-e2` / `shadow-e3`、`duration-hover-out`、`duration-standard`、`duration-standard-exit` 等、`ease-enter` / `ease-exit`、`h-control-xs` … `h-control-lg`、`h-control-mobile-md / lg`、`h-row`、`h-row-compact`、`h-row-mobile`、`h-view-header`、`h-kbd`、`min-h-hit`、`min-w-hit`、`min-w-kbd`、`w-sidebar`、`rounded-*`。
- **SwiftUI**：把 `Theme.swift` 加进项目，需要 iOS 15 以上；用 Xcode 26 编译、跑在 iOS 26 以上时 `.frost()` 是 Liquid Glass。
  - 颜色 `Palette.*`（token 名转小驼峰：`Palette.canvas`、`Palette.elevated`、`Palette.menuActive`、`Palette.text3`、`Palette.primaryText`、`Palette.selected`），每个都按深浅和「增强对比度」自动四选一。
  - 字体 `.font(.rowTitle)`、`.rowMeta`、`.sectionHeader`、`.cardTitle`、`.longText`、`.tagLabel`、`.amount`（等宽数字）、`.pageTitle`，都基于系统文字样式，支持 Dynamic Type。页面标题优先用导航栏的大标题。长段中文用 `Text(…).longText()`（`.longText` 加 6 pt 行距，合 17 / 28）。
  - 圆角 `Radius.lg`；间距 `Space.s4`（16）；尺寸 `Size.hitMin`、`Size.controlMd`、`Size.controlLg`、`Size.row`（60）、`Size.rowSingle`（44）、`Size.pill`（36）；图标 `Icon.sm / md / lg`、`Icon.weight`。
  - 动效 `Motion.spring`（`.spring(response: 0.3, dampingFraction: 0.9)`），`Motion.fast`、`.standard`、`.slow` 和对应的 `fastExit`、`standardExit`、`slowExit`。
  - 卡片 `.card()`（实底加发丝线，无阴影）；浮层阴影 `.elev2()`、`.elev3()`，加在背景形状上，不加在带字的视图上。
  - 自定义浮动控件加 `.frost(radius: 高度的一半, floating: true, interactive: true)`：iOS 26 以上是 `glassEffect(.regular.interactive())`，以下是 `.ultraThinMaterial` + `frost` 色 + 发丝线 + 顶部高光。贴边的栏用 `.frost(edges: .bottom)` 或 `.top`。系统栏、toolbar、TabView 不要加 `.frost()`，也不设背景。几个玻璃控件并排时放进同一个 `GlassEffectContainer`。
  - kbd：`Text("⌘K").kbd()`（iPad 和 Mac Catalyst 接硬件键盘时显示）。
- **Jetpack Compose**：把 `Theme.kt` 放进 `theme` 包，用 `AppTheme { … }` 包住界面。需要 Compose Material 3 1.2 以上，基线是 1.4。
  - `AppTheme(dark, highContrast, fontFamily)`：深浅跟随系统；`highContrast` 默认读 `isSystemHighContrast()`（API 34 以上的系统对比度 ≥ 0.5）；固定品牌色，没有动态取色。
  - 字体：把 Roboto Flex 可变字体放进 `res/font/roboto_flex.ttf`，传 `AppTheme(fontFamily = robotoFlex(R.font.roboto_flex))`；不传时是系统 Roboto。金额用 `MaterialTheme.typography.bodyLarge.tabular`。
  - 颜色角色：`colorScheme.primary` 是 `primary-text`，所以 TextButton、选中的导航项、复选框和开关这类拿 primary 着色的组件在深色下也过 4.5:1（复选框的勾和开关圆钮是 `onPrimary`，深色下是深色，不要改成白）；`colorScheme.surface` 是 `bg`；`surfaceContainerLowest` … `surfaceContainerHighest` 依次是 `canvas`、`bg`、`surface`、`surface-2`、`surface-3`；`secondaryContainer` 是 `surface-3`（导航指示器和选中的 FilterChip 因此是中性色）；`outline` 是 `border-strong`，`outlineVariant` 是 `border`；`error` / `errorContainer` 是 `danger`。
  - Material 3 没有的颜色用 `AppTheme.colors`：`primaryFill`（即 `primary`）、`onPrimaryFill`、`primaryFillHover`、`primaryFillPressed`、`primaryText`、`surface`（卡片色）、`surface2`、`surface3`、`canvas`、`elevated`、`menuActive`、`text3`、`textPlaceholder`、`selected`、`success`、`warning`、`info` 及其 container、`hover`、`pressed`、`scrim`、`scrimMenu`、`frost` 等。
  - 组件：主按钮 `AppButton`（`primaryFill` 底，悬停和按下变暗：进 0 ms、出 150 ms），次按钮 `AppOutlinedButton`（危险操作传 `contentColor = MaterialTheme.colorScheme.error`；两个按钮都能传 `interactionSource`），卡片 `AppCard`（`surface` 底、1 dp `outlineVariant`、无阴影），筛选 `AppChip(selected, onClick, label, selectedIcon = { 18 dp 的勾 })`（勾只在选中时出现），状态 `StatusTag("已入账", AppTheme.colors.success, AppTheme.colors.successContainer, icon = { … })`，新建 `AppFab`，底栏 `AppNavigationBar`。不要直接用 `Button`、`Card`、`FilterChip`、`FloatingActionButton`、`NavigationBar`。
  - 栏：`TopAppBar(colors = appTopBarColors(), scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior())`：不透明 `bg`，滚动后不变色；滚动后的 1 dp 线自己画，放在同一个 `Column` 里：`if (scrollBehavior.state.contentOffset < 0f) HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)`。底栏 `AppNavigationBar { NavigationBarItem(colors = appNavigationItemColors(), …) }`（`surface` 底、顶部 1 dp 线、无色调提升）。ModalBottomSheet、ModalNavigationDrawer 传 `scrimColor = AppTheme.colors.scrim`。
  - 尺寸：`Radius.lg`、`Space.s4`、`AppSize.hitMin`（48）、`AppSize.controlLg`（50）、`AppSize.row`（72）、`AppSize.rowSingle`（48）、`AppSize.navigationBar`、`AppSize.fab`；`IconSize.sm / md / lg`、`IconSize.WEIGHT`（300）；`ButtonShape`（12）、`TagShape`（全圆）；`AppShapes` 是 4 / 6 / 8 / 12 / 16。
  - 动效：`tween(Motion.STANDARD_MS, easing = Motion.Enter)` 进场，`tween(Motion.STANDARD_EXIT_MS, easing = Motion.Exit)` 退场；弹簧用 `Motion.spatial()`、`Motion.effects()`（即 `MotionScheme.standard()` 的参数）。
  - 玻璃：Compose 没有系统背景模糊，栏默认不透明；要玻璃时用 Haze 这类库，参数取 `Frost.blur`、`Frost.SATURATION` 和 `AppTheme.colors.frost / frostBorder / frostHighlight`。
  - M3 Expressive（1.5.0-beta01 以上）：把 `AppTheme` 里的 `MaterialTheme` 换成 `MaterialExpressiveTheme(colorScheme = colors, motionScheme = MotionScheme.standard(), shapes = AppShapes, typography = typography, content = content)`，见 `Theme.kt` 的注释；不用 `MotionScheme.expressive()`。
- **其他框架**（UIKit、Flutter、React Native 等）：按 `tokens.json` 的 key 映射，例如 `color.light.primary`、`color.dark-hc.text-2`、`radius.lg`、`space.4`（16）、`size.control-h.desktop.md`、`size.row.desktop`、`font.web.scale.small`（size、line、weight、tracking、opsz）、`font.ios.styles.row-title`、`font.android.scale.bodyLarge`、`elevation.dark.2`（阴影层数组）、`motion.duration.hover-out`、`motion.ease.enter`、`blur.frost`、`icon.size.sm`。四套颜色都要接上，按系统的深浅和对比度设置选一套。
