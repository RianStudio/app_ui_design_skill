# 主题规则：石墨

一句话：**深石墨和纸白两套 LCh 中性色阶梯，用 1 px 发丝线和明度差分层，单一强调色，排得密但不挤；照片、视频和生成结果放在彩度 0 的中性画布上，界面退到后面。** 中性色和 app 图标的底是同一种石墨（色相 265），图标放在导航栏和侧栏顶部里看起来是一家。只有这一种风格；键盘层、桌面窗口这些是可选的附加层，不是另一种风格。

线条、密度和克制来自 Linear；材质、字体和图标规格来自 Apple；无障碍硬指标和动效参数来自 Google。

## 原则

1. **三个输入推出所有颜色。** base（色相 265 的冷石墨）、accent（图标强调色映射来的主色）、contrast（`standard` / `high`）。所有表面、边框、文字都在 CIE LCh（D65）里推导，不手写色值。深色优先。
2. **明度差加发丝线分层，不靠投影。** `canvas` < `bg` < `surface` < `surface-2` < `surface-3`，每级约 2.5 L，再加 1 px `border`。卡片不加投影，只有浮层和弹窗有一层大而淡的影子。一个区域只用一道线。
3. **一个强调色，用途有限。** 主按钮、焦点环、多选行浅底、链接、复选框和开关打开、进度（含滑块填充段和播放头）、媒体选中描边、未读圆点。侧栏当前项、键盘光标行、菜单当前项、筛选 pill 选中、当前工具都是中性色。一屏主色面积：桌面 ≤ 5 %，手机 ≤ 8 %，照片和生成结果不算；引导、付费墙、权限预请求和同意页放宽到 ≤ 15 %。界面主色只有蓝、绿、紫，暖色只留在图标里，红色永远不做主色。
4. **填充和文字分开。** `primary` 是填充（白字 ≥ 4.5:1，深浅同值）；`primary-text` 是链接、选中文字和焦点环（深色更亮、浅色更暗）。不要拿 `primary` 写字，也不要拿 `primary-text` 做按钮底（Compose 的复选框和开关例外，见「用法速查」）。
5. **密但不挤。** 桌面和 Web 正文 13–14、列表行 36；手机沿用平台字号和 44 / 48 点击区，不套桌面密度。
6. **一个动作一个名字，键盘是可选层。** 每个动作只有一个名字，都能搜到：桌面是 ⌘K，手机是搜索入口。快捷键提示、tooltip 里的快捷键和悬停效果是键盘层，只在桌面、Web 和接了键盘的 iPad / Mac 上出现；手机上不显示，也不靠它们教用户。
7. **立即响应，慢的讲清楚。** 瞬时的本地操作乐观更新，不显示 spinner；超过 1 s 的处理（抠图、转码、放大、生成、批量导出）走「长任务」：确定进度、剩余时间、取消、能在后台继续。动效短，几乎不回弹。
8. **可读性是硬指标。** 对比度表（见「颜色」）由 `build.py` 断言，不过就不输出；高对比档一起生成，跟随系统设置。不要手动调回去。
9. **平台原生。** iOS 用系统栏和 Liquid Glass，Android 用 Material 3 组件和全部颜色角色，Web 和桌面用倒 L 布局。手机优先：先把 iPhone 和 Android 做对。
10. **看颜色的地方用中性底。** 编辑页、查看页在四套颜色里都是深色，画布用彩度 0 的 `media-*`；照片上不叠玻璃（会改颜色），也不叠主色浅底（会染色）。

## 颜色

### 三个输入

| 输入 | 规则 |
|---|---|
| base | 色相 265，彩度深色 1.6、浅色 1.2，纯白不加彩度。不跟主色变 |
| accent | 图标强调色按 SKILL.md 第 1 步的表映射成主色：蓝→蓝，绿→绿，紫→紫，珊瑚、黄、灰→蓝。还没有图标时按类别选（`--category`）：AI 紫；工具、图片、视频蓝；健康、财务绿。有图标时以图标为准。主色保留强调色的色相和彩度，只调 L，超出色域时降彩度 |
| contrast | `standard`（相当于 Linear 的 30）和 `high`（相当于 Linear 的 100），两档都生成 |

**强调色**（浅 → 主），和 `rian-app-icon` 的强调色表相同：

| 名 | 色值 | 在界面里 |
|---|---|---|
| 蓝 | `#7AAEFF → #3B7BEA` | 默认主色；珊瑚、黄、灰的图标也用它；`info` 的来源 |
| 绿 | `#6FD3A6 → #23A36B` | 图标是绿时做主色；`success` 的来源 |
| 紫 | `#B3A6FF → #7A63F0` | 图标是紫时做主色 |
| 黄 | `#FFD978 → #F2AE2E` | 不做主色，只留在图标；`warning` 的来源 |
| 珊瑚 | `#FF9C86 → #EC5B45` | 不做主色，只留在图标；`danger` 的来源。红色系永远不做界面主色 |
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
| `selected` | 多选的行：`primary` 在深色叠 16 %、浅色叠 10 % 合成到 `bg` 上。照片和生成结果选中不用它，用 `media-selected` 描边加勾 |
| `focus` | 等于 `primary-text`，2 px 实色环 |
| `primary-container` / `on-primary-container` | 给 Compose 和同源状态徽章用：`primary` 混向 surface 85 %（深）/ 90 %（浅）；字等于 `primary-text` |
| `selection` | 文字选中的底：`primary` 在深色叠 28 %、浅色叠 16 %。`text` 和 `text-2` 在上面也要过对比度 |

`build.py` 的实际输出（深 / 浅；高对比深 / 浅）：

| 主色 | `primary` | `primary-hover` / `primary-pressed` | `primary-text` | `primary-text` 高对比 |
|---|---|---|---|---|
| 蓝（图标蓝、珊瑚、黄、灰） | `#2B72E0` | `#0F69D5` / `#005FC4` | `#6E97FF` / `#0064CD` | `#ADBDFF` / `#004CA0` |
| 绿 | `#008755` | `#007C4D` / `#007146` | `#34AF76` / `#00764A` | `#5FD599` / `#005B38` |
| 紫 | `#755FEB` | `#6955E0` / `#5D4BD4` | `#A389FF` / `#6350DA` | `#C9B4FF` / `#4338BE` |

**主色的用途只有这些**：主按钮、焦点环、多选行的浅底（`selected`）、链接、复选框和开关打开、进度（进度条、滑块的填充段、视频播放头）、照片选中的描边（`media-selected`）和勾、未读圆点（6 px）。侧栏当前项和键盘光标行用中性的 `surface-2`，菜单当前项用 `menu-active`，筛选 pill、比例 chip 选中和当前工具用 `surface-3`，都不用主色。

一屏主色面积桌面 ≤ 5 %、手机 ≤ 8 %；`selected` 是状态，不计入。照片、视频帧、画布和生成结果的像素也不计入（照片里的蓝天不是主色）：`preview.py` 量的时候把它们挖掉。引导、付费墙、权限预请求和第三方 AI 同意页是转化界面，放宽到 ≤ 15 %。

### 状态色

- 来源：`success` ← 绿、`warning` ← 黄、`danger` ← 珊瑚、`info` ← 蓝。各自有 `X`（文字和图标，≥ 4.5:1，算法同 `primary-text`）、`X-container`（浅底，`X` 的强调色「主」混向 surface 85 % / 90 %）、`on-X`（实心状态色上的字：浅色是白，深色是 `bg` 色）。
- 实际输出（深 / 浅）：`warning` `#F2AE2E` / `#8A5F00`，`danger` `#FF6C54` / `#BE3224`，`info` `#6E97FF` / `#0064CD`，`success` `#34AF76` / `#00764A`。
- 和主色同源的状态（绿主题的 `success`、蓝主题的 `info`）直接复用 `primary-text` 和 `primary-container`，徽章上必须带图标，否则读起来像链接或选中态。
- 只在状态出现时用。红色只用于错误和危险操作。
- `in-progress` 等于 `info`：进行中、处理中、生成中、队列里正在跑的那一项都用它。`warning` 只给真要注意的事（有冲突、快满了、余额不足），不然处理队列里的「进行中」会被读成出错。
- 状态图标是一组 16 px 的圆：待办 `text-3` 空心圈；积压虚线圈；进行中 `in-progress` 部分填充的饼；完成 `success` 实心勾；取消 `text-3` 实心叉。
- 「完成」是默认态的列表（记账：已入账）不画状态图标，只留 16 px 列宽让标题对齐，只给例外画：待确认（空心圈）、报销中（`in-progress` 饼）、已退款（`text-3` 实心叉，标题和金额加删除线）。
- 优先级：三根递增竖条（`text-3`）；紧急是 `danger` 实心圆角方块加「!」。

### 媒体色组

编辑页、查看页、相机页在四套颜色里都是深色（「平台适配」写了各平台怎么强制）。浅色模式下编辑页被白色包围，照片会显得发暗；`bg` 带一点冷色，也会影响判断。所以这组颜色在四套里同值，彩度都是 0：

| token | 值 | 用在 |
|---|---|---|
| `media-black` | L 0 `#000000` | 查看器和视频播放的底 |
| `media-dark` | L 18 `#2C2C2C` | 编辑器画布（默认）：照片四周的留白 |
| `media-mid` | L 50 `#777777` | 中灰画布：调曝光、调色时 |
| `media-white` | L 100 `#FFFFFF` | 白画布：白底商品图、印刷品 |
| `checker-a` / `checker-b` | L 96 `#F3F3F3` / L 86 `#D7D7D7` | 透明棋盘格，格 8（抠图） |
| `on-media` | 白 | 画布和遮罩上的图标、文字，裁剪手柄，前后对比分隔线 |
| `viewer-scrim` | 黑 56 % | 查看器遮罩控件下面的浓度；渐变从边缘的 64 % 到 70 % 处的 56 %，再淡到 0，高 140 |
| `media-edge` | 黑 32 % | 白色手柄和分隔线外面 0.5 px 的暗边，白图上也看得见 |
| `media-guide` | 白 50 % | 三分线、视频拖动条的轨道 |
| `media-selected` | 同 `primary-text` | 选中照片的 3 px 内描边 |

- 画布四档让用户在编辑页里选（黑、深灰、中灰、白），默认编辑器 `media-dark`、查看器 `media-black`。
- 查看器的控件放在 `viewer-scrim` 渐变上，不用玻璃：`frost` 带 1.5 倍饱和度和模糊，会改变下面照片的颜色。白字在遮罩叠白图上 ≥ 4.5:1（`build.py` 断言，实际 4.95:1）。
- 照片的选中是 `media-selected` 描边加 22 圆勾（`primary` 底白勾），不叠 `selected` 或 `selection` 浅底。

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
| `primary`（滑块填充段） | `surface-3`（轨道） | ≥ 3:1 | ≥ 3:1 |
| `media-selected` | `bg`、`surface` | ≥ 3:1 | ≥ 3:1 |
| `on-media` | `media-black`、`media-dark`；`viewer-scrim` 叠在白图上 | ≥ 4.5:1 | ≥ 4.5:1 |
| `text`、`text-2`、`text-3`、`primary-text`（深色两套） | `media-black`、`media-dark` | 同各自的要求 | 同各自的要求 |
| `media-selected`、播放头 `primary`（深色两套） | `media-black`、`media-dark` | ≥ 3:1 | ≥ 3:1 |
| 栏上的文字和图标 | 滚到栏下的列表，和亮、暗、高饱和的照片（`preview.py` 实测） | ≥ 3:1 | |
| 查看器的白色控件 | 遮罩叠在亮照片上（`preview.py` 实测） | ≥ 4.5:1 | |

另加一条：高对比档每一行在所有底上的最低值，不低于标准档的同一行。`border` 发丝线是纯装饰，不要求对比度。

## Token

token 名是 `build.py`、`tokens.json` 和各平台输出共用的契约，写界面时只用这些名字。

| 组 | 内容 |
|---|---|
| 表面 | `canvas`、`bg`、`surface`、`surface-2`、`surface-3`、`elevated`、`menu-active` |
| 线 | `border`、`border-strong` |
| 文字 | `text`、`text-2`、`text-3`、`text-placeholder` |
| 主色 | `primary`、`on-primary`、`primary-hover`、`primary-pressed`、`primary-text`、`selected`、`focus`、`primary-container`、`on-primary-container`、`selection` |
| 状态 | `success`、`warning`、`danger`、`info`，各自的 `-container` 和 `on-*`；`in-progress`（= `info`） |
| 媒体 | `media-black`、`media-dark`、`media-mid`、`media-white`、`checker-a`、`checker-b`、`on-media`、`viewer-scrim`、`media-edge`、`media-guide`、`media-selected`。四套同值，只有 `media-selected` 跟着 `primary-text` 变 |
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
| 媒体尺寸 | `size.media`：工具托盘高 64、工具项宽 64；滑块轨道 4、圆钮 24、0 点刻度 8；裁剪角手柄 20、线宽 3；播放头 2、圆头 10；时间线高 48、剪辑手柄宽 14；缩略图间隙 2；选中描边 3、勾 22；棋盘格 8；查看器遮罩高 140 |
| 提示词框 | `size.prompt`：最小高 48，随文字长到 6 行，再多就在框里滚动 |
| 阴影 | `elev-0` · `elev-2` · `elev-3`，见下表 |
| 动效 | `hover-in` · `hover-out` · `fast` · `standard` · `slow` · `zoom`，加进场、退场两条曲线，见下表 |
| 手势 | `motion.gesture`：放大倍数、惯性、边缘阻尼、下滑关闭、吸附范围，见「动效 → 手势」 |
| 触感 | `haptic`：`selection`、`snap`、`success`、`failure` 四种，见「动效 → 触感」 |
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
| `timecode` | `.footnote` + `.medium`，等宽数字（13 / 18） | 视频时间码、滑块数值、生成步数、剩余时间 |

Android 用 M3 type scale（sp）：列表行标题 `bodyLarge` 16；元数据 `bodyMedium` 14、`text-2`；标签 `labelMedium` 12 / 500；FilterChip `labelLarge`；时间码 `labelLarge` 等宽数字（`Typography.timecode`）；正文不小于 12 sp。

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
| `zoom` | 300 ms | 网格到查看器的放大转场、双击放大 |
| `fast-exit` · `standard-exit` · `slow-exit` · `zoom-exit` | 67 · 120 · 167 · 200 ms（进场的 2/3） | 所有退场 |

- 曲线：`enter` 是 `cubic-bezier(.2, 0, 0, 1)`（同 Material emphasized），`exit` 是 `cubic-bezier(.3, 0, 1, 1)`。
- iOS：`.spring(response: 0.3, dampingFraction: 0.9)`，几乎不回弹；Liquid Glass 自带的形变保留，不另加弹跳。
- Android：`MotionScheme.standard()`（空间运动 damping 0.9 / stiffness 700，颜色和透明度 damping 1.0 / stiffness 1600）。不用 expressive 方案，它的 fast 档 damping 0.6，回弹太明显。
- 「减弱动态效果」打开时，所有位移和缩放改成 0 ms 或纯淡入淡出。

**手势**（照片和视频；`motion.gesture`）：

| 参数 | 值 | 用在 |
|---|---|---|
| `zoom-double-tap` | 2.5 | 双击在适合屏幕（1 倍）和 2.5 倍之间切换，以点的位置为中心 |
| `zoom-max` | 8 | 捏合放大的上限；缩到小于 1 倍时松手弹回 |
| `deceleration` | .998 / ms | 拖动松手后的惯性，同 UIScrollView 的 `.normal`。Android 用平台的 `rememberSplineBasedDecay()` |
| `rubber-band` | .55 | 拖过边缘的阻尼，松手用 `spring` 弹回 |
| `dismiss-distance` · `dismiss-velocity` | 屏高 25 % · 800 pt/s | 查看器下滑关闭：超过任一个就关；背景随拖动变淡，照片跟手缩小 |
| `detent` | 范围的 2 % | 滑块和旋转刻度离 0 点（或默认值）在这个范围里就吸过去，同时给一次 `snap` 触感 |

网格到查看器用放大转场（`zoom` 300 ms）：iOS 18 起 `.navigationTransition(.zoom(sourceID:in:))` 加 `.matchedTransitionSource`，更早用 `matchedGeometryEffect` 加 `Motion.spring`；Compose 用 `SharedTransitionLayout` 和 `Modifier.sharedElement`；Web 用 View Transitions（`view-transition-name`）。「减弱动态效果」时改成淡入淡出。

**触感**（`haptic`）：只在事件发生时震一次，不跟着每一帧、每一格刻度震；系统关了触感就不震（系统自己处理）。

| 角色 | 什么时候 | iOS 17 起 | iOS 15–16 | Android | Web |
|---|---|---|---|---|---|
| `selection` | 换工具、换分段、选中一张照片 | `.sensoryFeedback(.selection, trigger:)` | `UISelectionFeedbackGenerator` | `SEGMENT_TICK` | `vibrate(10)` |
| `snap` | 滑块或刻度吸到 0 点；裁剪边碰到参考线；剪辑手柄碰到播放头 | `.impact(weight: .light)` | `UIImpactFeedbackGenerator(style: .light)` | `GESTURE_THRESHOLD_ACTIVATE` | `vibrate(16)` |
| `success` | 导出、保存、生成完成 | `.success` | `UINotificationFeedbackGenerator`，`.success` | `CONFIRM` | `vibrate([12, 80, 24])` |
| `failure` | 导出、生成失败 | `.error` | 同上，`.error` | `REJECT` | `vibrate([32, 60, 32])` |

- Android 一列是 `HapticFeedbackConstants`；Compose UI 1.8 起用 `HapticFeedbackType` 的同名项（`SegmentTick`、`GestureThresholdActivate`、`Confirm`、`Reject`），旧系统上会自动换成最接近的效果。
- Web 只有 Android 上的浏览器能振动，iOS Safari 没有 `navigator.vibrate`，不要靠它传达信息。

## 用法速查

**布局**按 app 的类型选一种，先把手机做对：

- **列表型**（记账、待办、笔记）：页面 `bg`，列表组和卡片 `surface`；iOS 用系统栏，Android 见「平台适配」。
- **画布型**（照片和视频编辑、查看、相机）：深色、全屏；画布 `media-dark`（查看器 `media-black`）占满上下两栏之间。顶栏放取消和完成，底部是工具托盘（高 64）和模式切换，参数滑块在托盘上方。见「编辑和查看」「视频」。
- **对话型**（AI 聊天、生成）：消息在 `bg` 上，提示词框浮在底部，顶栏放模型和点数。见「AI」。
- **Web / 桌面**（可选）：倒 L：`canvas` 的侧栏和顶栏框住 `bg` 主视图；视图头（高 44）放视图名、筛选和显示选项，下面可以有筛选条（高 36）；属性放右侧面板。
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
| 进度条 | 高 6（桌面 4），圆角 full；已用段 `primary`，剩余段 `surface-3`，两段之间留 2 px 间隙，不画成连续的条。旁边的状态图标和百分比用 `in-progress` |
| 分段控件 | 2–4 段，互斥；更多选项用菜单。iOS 用系统 `Picker(.segmented)`；Android 用 `SingleChoiceSegmentedButtonRow`（选中段 `secondaryContainer`，即 `surface-3`，带勾）；手机 Web 高 32、圆角 9、`surface-3` 底，选中段 `elevated` 加一层细影子，`row-meta` 字。选中是中性色，不用主色 |
| 步进器 | 小范围的整数（倍率、张数）。iOS 用系统 `Stepper`；自绘时高 32、圆角 9、`surface-3` 底，「−」「+」各宽 40，点击区补到 44；当前值写在左边的标签里（「导出倍率 2×」，等宽数字）；到上下限的一边换 `disabled-fg` |
| 滑块 | 轨道 4 `surface-3`，填充段 `primary`（双向参数从中间往两边填），圆钮 24 白色加细影子；数值写在标题行右边，`timecode` 等宽，带正负号。有中间点（曝光、色温）时画 8 高的 `text-3` 刻度，2 % 内吸附并给 `snap` 触感；双击圆钮回到 0。iOS 用系统 `Slider` 加 `.tint(Palette.primary)`；Compose 用 `Slider(colors = appSliderColors())` |
| 底部弹窗 | `elevated`、顶部圆角 16、`elev-3`、后面铺 `scrim`；顶部抓手 36 × 5。标题 `card-title`，右上角关闭；一屏一个主按钮，次按钮在左。iOS 用系统 sheet（`.presentationDetents`）；Android 用 `ModalBottomSheet(scrimColor = AppTheme.colors.scrim)` |
| 状态徽章 | `X-container` 底、`X` 字、圆角 full；和主色同源时带图标 |
| 未读圆点 | 6 px `primary` |
| 侧边栏 | `canvas` 底，宽 240。顶部是工作区切换（高 44，带 app 图标）和搜索、新建两个图标按钮。项高 28、圆角 6、左右内边距 8；图标 16 `text-3`，文字 `small` 510 `text-2`；当前项 `surface-2` 底、`text` 字；计数 `caption` `text-3` 右对齐。分区标题 `caption` `text-3`，可以折叠。底部放同步状态（6 px 圆点加「已同步」） |
| 标签栏 | iOS 用系统 TabView（Liquid Glass），选中色 `primary-text`。Android 用 `AppNavigationBar`（M3 NavigationBar 加顶线）：高 80（另加系统手势区 inset），`surface` 底加顶部 1 px `border`，不加色调提升，指示器 pill 64 × 32 用 `surface-3`，选中的图标（FILL 1）和文字 `primary-text`。Web 手机版是浮动玻璃 pill：高 56、左右各留 16、悬在安全区上方 8，未选中 `text-3`，选中 `primary-text` |
| FAB（Android） | 56 dp，`primary` 底、白色「+」、圆角 16、`elev-2` |
| 弹窗 | `elevated`、圆角 16、`elev-3`、后面铺 `scrim`。宽 440（确认）或 560（表单），内边距 20；标题 `title-2`，正文 `body` `text-2`；操作按钮右对齐，次按钮在左、主按钮在右。Esc 关闭，⌘↵ 确认。手机用系统 sheet |
| toast | `elevated`、1 px `border`、`elev-2`、圆角 8、高 40。左边 16 px 状态图标，中间 `small` 510 文字，右边「撤销」用 `primary-text`（接了键盘时后面加 kbd ⌘Z）。桌面在左下（离开右侧属性面板），手机在标签栏上方居中。停 4 s，悬停时暂停，最多叠 3 条。iOS 是自定义浮层：高 44、圆角 full，「撤销」点击区 44。Android 用 M3 Snackbar |
| kbd | 键盘层（见「命令菜单和键盘层」），只在桌面、Web 和接了键盘的 iPad / Mac 上出现。高 18、最小宽 18、左右内边距 4、圆角 4；`micro` 510 等宽数字，`text-2` 字、`surface-2` 底、1 px `border`；多个键之间隔 4。序列键写成 `G` 然后 `S`，「然后」用 `micro` `text-3`。mac 显示 ⌘ ⌥ ⇧ ⌃ ↵，Windows 和 Linux 显示 Ctrl、Alt、Shift |
| tooltip | 键盘层：只在有指针悬停时出现，手机上没有，不能是说明的唯一位置。`elevated`、`caption`、圆角 6、延迟 500 ms，带 kbd |
| 弹出菜单 | `elevated`、圆角 12、1 px `border`、`elev-2`、后面铺 `scrim-menu`；当前项 `menu-active` |
| 玻璃（frost） | 只给浮在内容上的栏和按钮：Web 手机版的浮动标签栏、自定义浮动按钮。toast 不用玻璃，用 `elevated`（见上面 toast 行）。`frost` + 1 px `frost-border` + 顶部 1 px `frost-highlight`，浮动的再加 `elev-2`。iOS 系统栏自带 Liquid Glass，不另加；卡片、列表、弹窗不用玻璃 |

## 编辑和查看

编辑器、查看器、相机是深色页面（见「平台适配 → 媒体页强制深色」），颜色用「媒体色组」。这里的主色只出现在滑块填充段、播放头、照片选中的描边和勾、「完成」按钮上。

| 组件 | 规格 |
|---|---|
| 画布 | 默认 `media-dark`；照片按比例放在两栏之间，四周至少留 16。画布四档（黑、深灰、中灰、白）放在「更多」菜单里，记住用户的选择。透明区域铺棋盘格（`checker-a` / `checker-b`，格 8），不用纯白或纯黑代替 |
| 顶栏 | 左边 × 或「取消」，中间当前模式名（`card-title`），右边「完成」。iOS 用系统 toolbar，「完成」是 `.glassProminent`；Android 的 TopAppBar 用 `media-black` 底、`on-media` 字，「完成」是 `primary-text` 的 TextButton。有改动时按 × 先问「放弃修改？」 |
| 前后对比 | 按住画布看原图，松手回来：这个一定要有。可以再加拖动的竖分隔线：2 px `on-media` 外加 0.5 px `media-edge`，中间 36 的圆形把手；两边上角写「原图」「调整后」（高 24，`viewer-scrim` 底、`on-media` 字） |
| 参数滑块 | 在工具托盘上方，规格同「用法速查 → 滑块」：标题行左边参数名 `row-title`，右边数值 `timecode`；0 点刻度，2 % 内吸附加 `snap` 触感；双击圆钮回到 0 |
| 工具托盘 | 高 64，横向滚动；每项宽 64：44 的圆形图标区，下面 `tag-label` 名字。未选中 `text-3`；改过的工具，图标外加 1.5 px `surface-3` 圈；当前工具 `surface-3` 底、1.5 px `on-media` 圈、`on-media` 字。当前工具是中性色，不用主色。换工具给 `selection` 触感 |
| 模式切换 | 托盘下面一行字：调整、滤镜、裁剪、抠图……，`row-title`，当前项 `on-media`，其余 `text-3` |
| 滤镜条 | 托盘位置换成 64 × 64 的缩略图（用这张照片渲染），下面写滤镜名；当前项 2 px `on-media` 描边。强度用同一个参数滑块 |
| 裁剪 | 框线 1 px `on-media`；四角 L 形手柄 20、线宽 3，四边中间 24 × 3 的短手柄，都是 `on-media` 外加 `media-edge` 暗边；拖动时显示三分线 `media-guide`；框外压 `viewer-scrim`。下面是旋转刻度（±45°，0 点长刻度，回到 0 时吸附加 `snap` 触感）、比例 chip（自由、原始、1:1、4:5、16:9，选中是中性的 `surface-3`），再下面是旋转 90°、翻转、「还原」 |
| 抠图 | 结果放在棋盘格上。要修边时给「保留」「擦除」两支笔和笔刷大小滑块。处理超过 1 s 走「长任务」 |
| 缩略图网格 | 3 列（iPad 和横屏 5–7 列），正方形，间隙 2，铺满屏宽，不加圆角。选择模式下每格右下角有 22 的白圈空心圆；选中后是 3 px `media-selected` 内描边加 22 的圆勾（`primary` 底、白勾、1.5 px 白圈），不叠 `selected` 浅底。手指拖过可以连续选，每选一张给 `selection` 触感。底部浮动栏写「已选 3 张」和分享、收藏、删除 |
| 查看器 | 全屏 `media-black`，照片按比例放。上面返回、日期和时间（`row-title` 加 `row-meta`）、更多；下面分享、收藏、编辑、删除。控件是 `on-media`，放在上下两条 `viewer-scrim` 渐变上（高 140），不用玻璃。轻点照片隐藏或显示控件、遮罩和状态栏，`fast` 淡入淡出。左右滑换照片，捏合和双击放大，下滑关闭（「动效 → 手势」）；从网格进来用放大转场 |
| 选照片 | 只是挑几张来编辑时用系统选择器，不要权限：iOS 16 起 `PhotosPicker`，更早 `PHPickerViewController`；Android 用 Photo Picker（`ActivityResultContracts.PickVisualMedia` / `PickMultipleVisualMedia`；Google Play 要求一次性访问用它，不申请 `READ_MEDIA_IMAGES`）；Web 用 `<input type="file" accept="image/*" multiple>` |
| 相册权限 | app 要显示自己的图库网格时才申请读取，先放自己的预请求页（见「转化界面」）。用户只允许了部分照片时，网格上面放一行 `surface-2` 提示「只能看到你选的 24 张照片 · 管理」：iOS 的「管理」调 `presentLimitedLibraryPicker(from:)`；Android 14 起是部分访问（`READ_MEDIA_VISUAL_USER_SELECTED`），「管理」重新请求权限，系统会再给一次选择 |
| 保存到相册 | 只要写入权限：iOS `PHPhotoLibrary.requestAuthorization(for: .addOnly)`，Info.plist 写 `NSPhotoLibraryAddUsageDescription`；Android 10 起用 MediaStore 写进 `Pictures/<app 名>`，不需要权限（Android 9 及以下要 `WRITE_EXTERNAL_STORAGE`，声明时加 `maxSdkVersion="28"`）。成功后 toast「已保存到相册」，带「分享」，给 `success` 触感 |
| 分享 | iOS 16 起 `ShareLink`，更早 `UIActivityViewController`；Android `Intent.createChooser(Intent(ACTION_SEND))`，文件用 FileProvider 的 content URI；Web 用 `navigator.share({ files })`，先用 `navigator.canShare` 判断，不支持时改成下载。分享的是导出后的文件，不是原图 |

## 视频

| 组件 | 规格 |
|---|---|
| 播放器 | `media-black` 底，控件和查看器一样放在 `viewer-scrim` 上，播放 3 s 后自动隐藏，轻点显示。中间 64 的播放 / 暂停，两边后退、前进 10 s，都是 `on-media`；最下面是拖动条和时间码 |
| 拖动条 | 轨道 4 `media-guide`，已播放段 `primary`，圆头 10 白色；拖动时圆头放大到 24，上方浮出那一帧的缩略图和时间码 |
| 时间线（剪辑） | 高 48，帧缩略图连续排开，圆角 6。播放头宽 2、`primary`，顶上 10 的圆头，贯穿时间线；播放头固定在中间，拖的是时间线（同系统照片 app）。剪辑手柄宽 14，`on-media` 底，中间一道 `media-edge` 竖线；选区外的帧压 `viewer-scrim`。手柄碰到播放头或起止点时吸附加 `snap` 触感 |
| 时间码 | `timecode` 等宽：「当前 / 总长」，`01:24 / 03:10`；超过 1 小时写 `1:02:05`；剪辑时精确到 0.1 s：`00:12.4`。iOS `.font(.timecode)`，Android `MaterialTheme.typography.timecode`，Web `.t-timecode`（自带等宽数字） |
| 导出设置 | 底部弹窗：格式（分段：视频、GIF）、分辨率（720p、1080p、4K）、帧率（30、60）、「兼容性优先」开关（打开时用 H.264，默认 HEVC），下面写预估体积「约 48 MB」（`row-meta`）。主按钮「导出」，导出走「长任务」 |
| GIF | 最长 10 s，宽默认 480，帧率 15，「循环」开关；预估超过 10 MB 时在体积旁边用 `warning` 写「有些聊天 app 会压缩」 |

## AI

对话和生成类 app 的页面在 `bg` 上，跟随系统深浅。生成的图按照片处理：不算进主色面积，选中用 `media-selected`，点开进查看器。

| 组件 | 规格 |
|---|---|
| 提示词框 | 浮在底部、键盘上方，左右各留 12；最小高 48、圆角 24，随文字长到 6 行，再多就在框里滚动。iOS 是浮动玻璃（`.frost(radius: 24, floating: true)`），Android 用 `surface-2` 实底。左边附件按钮，右边发送：40 的圆，有字时 `primary` 底白箭头，没字时 `disabled-bg` / `disabled-fg`；生成中换成停止键（`text` 底、`bg` 色方块）。比例、张数这些参数做成框里的 chip，不另开设置页。占位写「描述你想要的画面」这种具体的话 |
| 消息 | 用户的话在右边的气泡里：`surface-2` 底、圆角 20、最大宽 75 %、`long-text`。回复不加气泡，铺满宽度，`long-text` `text`；代码块 `surface-2`、圆角 8、等宽字体。附的图片 120 × 160，圆角 12 |
| 操作行 | 回复下面一行 18 的图标，`text-3`，点击区 44：复制、重新生成、赞、踩、举报。长按回复调出同样几项（菜单里带字） |
| 流式输出 | 字随到随显示，末尾跟一个 10 px 的 `text` 圆点；不逐字淡入，不放打字音效。用户往上滚就停止自动跟随，右下出现回到底部的按钮 |
| 四种状态 | **生成中**：确定进度（步数「18 / 30」或百分比，`timecode`）。有中间结果时显示模糊的预览，进度环用 `on-media`；没有时 `surface-2` 底，进度环用 `in-progress`。**完成**：直接显示结果，给 `success` 触感。**失败**：重试图标、「生成失败」、写清有没有扣点数，加「重试」次按钮。**排队**：待办空心圈、「排队中」、「前面还有 2 个」 |
| 被拒的提示词 | 单独一张卡：盾牌图标 `text-3`、「这条提示词不能生成」、一句原因、「这次没有扣点数」、「查看内容规则」链接。不用 `danger` 红底，不责备用户 |
| 点数 | 余额是导航栏右边的 chip（`coins` 图标 `text-2` 加等宽数字）。生成前在参数行写「消耗 4 点」（`row-meta` `text-3`）。失败和被拒都不扣，并写出来。余额不够时 chip 换 `warning`，点生成弹出点数版付费墙 |
| 模型选择 | 点导航栏中间的模型名（`card-title` 加 16 的下箭头），弹出底部弹窗：单选，每项写名字和「1 点 / 张 · 约 15 秒」 |
| 历史 | 侧栏：iOS 从左边推入（iPad 是 `NavigationSplitView` 的侧栏），Android 用 `ModalNavigationDrawer`。按今天、昨天、7 天内、更早分组，行标题是对话的第一句；左滑删除。「作品」页是缩略图网格，规则同「编辑和查看」 |
| 举报 | 每条回复和每张生成的图都能在 app 里举报（操作行的旗子、长按菜单）。底部弹窗列原因：冒犯或仇恨、色情或低俗、暴力或危险、侵犯隐私或版权、其他，加一个可选的说明框和「提交」。提交后 toast「已收到举报」，这条内容在本机先隐藏。Google Play 的 AI 生成内容政策要求 app 内举报；App Store 审核指南 1.2 对用户生成的内容也要求能举报 |
| 第三方 AI 同意 | 第一次把照片、语音或文字发给第三方模型之前，用一整页说清楚：发什么、发给谁（写服务商的名字）、拿去做什么、存多久，然后「同意并继续」和「不同意」，两个都在这一屏上，不藏。不同意时本机能做的功能照常可用。这是 App Store 审核指南 5.1.2(i) 的要求。同意记在 设置 › 通用 里（「第三方 AI」一项），随时可以撤回 |

## 长任务

超过 1 s 的处理（抠图、放大、转码、批量导出、生成）都按这一节做；瞬时的本地操作仍然乐观更新，不显示进度。

| 部分 | 规格 |
|---|---|
| 进度 | 确定进度，不只转圈：进度条（同「用法速查 → 进度条」）加百分比（`amount` 等宽）；批量时写「第 3 / 4 张」。一开始算不出来时写「正在准备…」，最多 2 s，之后必须有进度 |
| 剩余时间 | 「还剩约 12 秒」「还剩约 3 分钟」，`row-meta` `text-2`；按最近几秒的速度估算并平滑，不来回跳；前 2 s 不显示 |
| 取消 | 一直看得见：底部弹窗里的「取消导出」次按钮，或单项行尾的 ×。取消后已完成的保留，并写出来：「已导出 2 张，其余已取消」。跑了 30 s 以上的任务，取消前问一次 |
| 后台继续（iOS） | iOS 26 起用 `BGContinuedProcessingTaskRequest`：启动时用 `BGTaskScheduler.shared.register(forTaskWithIdentifier:using:)` 注册，标识符写进 Info.plist 的 `BGTaskSchedulerPermittedIdentifiers`；用户点「导出」时 `submit(BGContinuedProcessingTaskRequest(identifier:title:subtitle:))`，必须由用户的操作触发，不能自己在后台发起。系统会显示进度，用户也能在那里取消。处理中更新 `task.progress` 和 `updateTitle(_:subtitle:)`；写好 `expirationHandler`（系统或用户随时可能停掉它，先存好已完成的部分）；完成调 `setTaskCompleted(success:)`。iOS 26 以下只有 `beginBackgroundTask`，大约 30 s 而且不保证：切到后台时存好进度，回到前台接着做，界面上不写「可以离开 app」 |
| 后台继续（Android） | WorkManager 的长任务（`setForeground`）或前台服务。服务类型 Android 15 起用 `mediaProcessing`（每 24 小时最多 6 小时），更早用 `dataSync`；声明对应的 `FOREGROUND_SERVICE_*` 权限。通知里放进度条（`setProgress`）、剩余时间和「取消」动作；Android 13 起要 `POST_NOTIFICATIONS`，先放预请求页 |
| 服务器上的任务 | AI 生成这类在服务器上跑的任务不需要上面两项：离开 app 也会继续，完成后发推送，回来时结果已经在列表里 |
| 队列 | 多项任务排成行，高 36（手机行内点击区仍是 44 / 48），状态图标用那组 16 px 的圆：进行中 `in-progress` 饼，右边百分比也是 `in-progress`；完成 `success` 勾，右边写体积；排队 `text-3` 空心圈加「排队中」；失败 `danger` 图标加「失败 · 重试」。进行中不用 `warning` |
| 完成 | 在 app 里：toast 写结果「已导出 4 张」，带两个动作「保存到相册」「分享」（导出目标本来就是相册时写「已保存到相册」，只带「分享」），给 `success` 触感。在后台：通知写同样的结果，点按回到结果页。失败时给 `failure` 触感和 `danger` toast「导出失败 · 重试」，写出原因（空间不够、格式不支持） |

## 转化界面

引导、付费墙、权限预请求、第三方 AI 同意、示例空状态。这几页要讲清一件事并让人做决定，可以比工作界面「响」一些：

- 主色面积放宽到一屏 ≤ 15 %（工作界面手机 ≤ 8 %），照片和插图不算。
- 可以放插图，只用一种：几何切片（`preview.py` 的 `slices()`）：几块 `surface-2`、`surface-3` 的圆角矩形和圆，叠一块主色，必要时里面放真实的界面片段或示例图。不用人物插画、3D 渲染、渐变光斑。
- 标题 iOS 用 `.title` 加粗、Android 用 `headlineSmall`、Web 用 `display`，正文一两句。
- 一个主按钮，加一个文字按钮（「以后再说」「跳过」「不同意」），都放在拇指够得到的底部。

| 页 | 规格 |
|---|---|
| 引导 | 最多 3 屏，右上角一直有「跳过」。第一屏就演示核心功能（用示例图做一次真实的调整，或者生成一张），不讲公司和理念；最后一屏的主按钮进入 app 或付费墙。引导里不要权限，等用到时再要。页码是 6 px 圆点，当前 `text`，其余 `surface-3` |
| 权限预请求 | 用到时才出现（第一次导出时要通知，第一次进图库时要相册），先放自己的一页：插图里放这个权限带来的东西（例如一条「导出完成」通知），标题说用户得到什么，正文一句为什么要，再写「下一步是系统的权限对话框」。点「继续」才调系统对话框；点「以后再说」不调，下次用到时再问。被拒以后不反复弹，在用到的地方放一行说明和「去设置」。相机、麦克风同样 |
| 示例空状态 | 媒体和 AI app 第一次打开时不放空白页：图库放 3–4 张标着「示例」的照片，点一下就能编辑；对话页放 4 张示例提示词卡片（示例图加一句话），没有字时发送键禁用。列表型 app 的空状态仍按「UX 模式 → 空状态」 |
| 第三方 AI 同意 | 见「AI」 |

**付费墙**（iOS 用 StoreKit 2，也可以用系统的 `SubscriptionStoreView`（iOS 17）；Android 用 Google Play Billing）：

| 部分 | 规格 |
|---|---|
| 结构 | 从上到下：左上角关闭（一直看得见，不延迟出现）· 插图或示例效果 · 标题（写会员能做什么，不写「升级」）· 3–4 条权益（勾加一句话）· 方案 · 主按钮 · 小字 ·「恢复购买」「使用条款」「隐私政策」三个链接 |
| 方案 | 年付、月付、终身，按需要取。单选卡片高 60、圆角 12、1 px `border`；选中换成 2 px `primary-text` 边，不叠 `selected` 浅底。每张写名字、价格、计费周期；年付可以写折算的月价和「省 33 %」标签（`success-container` 底），但总价要比折算价醒目。默认选年付 |
| 免费试用 | 主按钮写「免费试用 7 天」，下面一行写清试用后多少钱：「试用结束后按 ¥98 / 年自动续费」 |
| 点数 | AI app 的订阅和点数包放在同一个组件里，分两组；点数包写「100 点 · ¥12」。余额不够时从生成按钮进来，顶部加一行 `warning`：「点数不够这次生成（还差 2 点）」 |
| 小字 | App Store 审核指南 3.1.2：订阅名称、时长、价格、自动续费和怎么取消，写在购买按钮附近。写法：「试用结束后按 ¥98 / 年自动续费。到期前至少 24 小时在 设置 › Apple 账户 › 订阅 里取消，就不会续费。」`row-meta` `text-3`，不能更淡 |
| 价格 | 一律用商店给的本地价格（StoreKit 2 `Product.displayPrice`，Play Billing 的 `formattedPrice`），不写死 |
| 恢复购买 | 付费墙和 设置 › 会员 里都有。StoreKit 2 调 `AppStore.sync()`；平时用 `Transaction.currentEntitlements` 判断会员，并一直监听 `Transaction.updates` |

## 共用外壳

每个 Rian Studio 的 app 都有下面这些，结构和文案一样，用户换一个 app 不用重新找。

**设置**，顺序固定：

| 组 | 内容 |
|---|---|
| 通用 | 这个 app 自己的设置（默认格式、导出质量、默认模型……） |
| 外观 | 跟随系统、浅色、深色，三选一，默认跟随系统。编辑页和查看页不受影响，一直是深色 |
| 语言 | iOS 打开系统里这个 app 的设置页（`UIApplication.openSettingsURLString`），在那里换语言；Android 13 起用系统的「应用语言」（`LocaleManager`），更早在 app 里列 简体中文、繁體中文、English |
| 会员 | 当前方案和到期日；「管理订阅」（iOS `.manageSubscriptionsSheet(isPresented:)`，Android 打开 Play 的订阅页）；「恢复购买」 |
| 支持 | 「给我们评分」「发送反馈」「帮助」 |
| 关于 | 版本号、「A Rian Studio app」、「更多 Rian Studio 的 app」、隐私政策、使用条款、开源许可 |

iOS 用 `.insetGrouped` 列表，导航标题 inline；Android 用单行列表，分组标题 `labelLarge` `text-3`（不用 M3 默认的主色）。

| 项 | 规格 |
|---|---|
| 关于 | app 图标 64、名字、「版本 1.4.2（212）」`row-meta` 等宽；下面一行「A Rian Studio app」`row-meta` `text-3`，不翻译。再下面是「更多 Rian Studio 的 app」：每个 app 一行（图标 40、名字、一句话、「获取」）；iOS 用 `SKStoreProductViewController` 在 app 里打开商店页，Android 打开 Play 链接 |
| 评分 | iOS 用 `@Environment(\.requestReview)`，Android 用 Play In-App Review API。只在用户刚做成一件事之后请求（第三次成功导出、第五次生成），不在启动时、出错后、付费墙前后请求；次数由系统限制，app 不另外弹「喜欢这个 app 吗」。设置里的「给我们评分」直接打开商店的评分页（iOS `https://apps.apple.com/app/id<ID>?action=write-review`） |
| 发送反馈 | 一页表单：类型（问题、建议）、说明、可选的截图；自动附上 app 版本、系统版本、机型，并列出来给用户看。提交后 toast「已收到，谢谢」 |
| 交叉推广 | 只放两处：关于页的「更多 Rian Studio 的 app」，和导出完成页结果下面的一张小卡片（可以关，关了不再出现）。不在启动、引导、付费墙、编辑过程中放，不做全屏推广。App Store 审核指南 3.2.1(i) 允许在 app 里推广自家的其他 app，前提是 app 不只是一个自家 app 的目录 |
| 本地化 | 简体中文（zh-Hans）、繁體中文（zh-Hant）、English（en）都要有。繁體不是简体逐字转换，用台湾的用词（相簿、設定、匯出）。英文按 Apple 的写法：按钮和标题 Title Case，句子 Sentence case。同一个动作在三种语言里都只有一个名字，按下表 |

**术语表**：

| 简体中文 | 繁體中文 | English |
|---|---|---|
| 导出 | 匯出 | Export |
| 保存到相册 | 儲存到相簿 | Save to Photos |
| 分享 | 分享 | Share |
| 完成 | 完成 | Done |
| 取消 | 取消 | Cancel |
| 撤销 | 還原 | Undo |
| 重试 | 重試 | Try Again |
| 原图 · 调整后 | 原圖 · 調整後 | Original · Edited |
| 已选 3 张 | 已選取 3 張 | 3 Selected |
| 还剩约 12 秒 | 約剩 12 秒 | About 12 seconds left |
| 排队中 | 排隊中 | Queued |
| 生成 · 重新生成 | 生成 · 重新生成 | Generate · Regenerate |
| 点数 | 點數 | Credits |
| 举报 | 檢舉 | Report |
| 设置 | 設定 | Settings |
| 通用 | 一般 | General |
| 外观 · 跟随系统 · 浅色 · 深色 | 外觀 · 跟隨系統 · 淺色 · 深色 | Appearance · System · Light · Dark |
| 语言 | 語言 | Language |
| 会员 | 會員 | Pro |
| 管理订阅 | 管理訂閱 | Manage Subscription |
| 恢复购买 | 恢復購買 | Restore Purchases |
| 免费试用 7 天 | 免費試用 7 天 | Try Free for 7 Days |
| 年付 · 月付 · 终身 | 年繳 · 月繳 · 終身 | Yearly · Monthly · Lifetime |
| 给我们评分 | 為我們評分 | Rate This App |
| 发送反馈 | 傳送意見回饋 | Send Feedback |
| 隐私政策 · 使用条款 | 隱私權政策 · 使用條款 | Privacy Policy · Terms of Use |
| 关于 | 關於 | About |
| 更多 Rian Studio 的 app | 更多 Rian Studio 的 App | More Apps by Rian Studio |
| 以后再说 · 跳过 · 继续 | 以後再說 · 略過 · 繼續 | Not Now · Skip · Continue |

## 命令菜单和键盘层

⌘K（Windows、Linux 是 Ctrl K）打开。命令菜单在桌面、Web 和接了键盘的 iPad / Mac 上出现；手机上对应的入口是搜索（见「UX 模式 → ⌘K」），搜的是同一份动作列表。

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

**键盘层**是可选的一层：kbd 提示、菜单和 tooltip 里的快捷键、悬停效果。只在有键盘或指针时出现；手机上不出现，也不能是做某件事的唯一入口。

| 平台 | 怎么判断 | 写法 |
|---|---|---|
| Web | 触屏（`hover: none`）上 `theme.css` 自动隐藏 `.kbd` 和 `.kbd-then`，`.hoverable` 的悬停只在 `hover: hover` 下生效。平板接了键盘：用户第一次按快捷键时，脚本给 `<html>` 加 `data-keyboard`，kbd 就出来（脚本见「接入」） | `<kbd class="kbd">⌘</kbd><kbd class="kbd">K</kbd>` |
| iOS / iPadOS | 根视图加 `.keyboardLayer()`：读 `GCKeyboard`，跟着键盘连上、断开变化，iPhone 上一直是关。快捷键本身用 `.keyboardShortcut`，iPad 上按住 ⌘ 时系统会列出来 | `Text("⌘K").kbd()`，没有键盘时什么都不画 |
| Android | `hasHardwareKeyboard()`（读 `Configuration.keyboard` 和 `hardKeyboardHidden`）；快捷键用 `Modifier.onKeyEvent`，并在 `onProvideKeyboardShortcuts` 里列出来，给系统的快捷键帮助 | `if (hasHardwareKeyboard())` 再画 kbd |

## UX 模式

| 模式 | 规则 |
|---|---|
| ⌘K | 所有页面和动作都能搜到。手机上的对应入口：iOS 用顶部搜索按钮或标签栏的 search 角色，Android 用 SearchBar 展开成全屏搜索 |
| 快捷键 | 单键：C 新建、/ 搜索、? 打开速查。G 序列：G 加首字母跳到对应视图（G I 明细、G S 统计）。J / K 或 ↑ / ↓ 移动，X 选中，↵ 打开，Esc 返回或关闭，⌘Z 撤销。快捷键出现在 tooltip、菜单、命令菜单和空状态里，都属于键盘层：手机上不显示，也不靠快捷键教用户 |
| 乐观更新 | 瞬时的本地操作立即生效，不显示 spinner。后台同步失败时回滚，并弹出 `danger` toast「没能保存 · 重试」。纯网络操作超过 1 s 时，在按钮里显示 16 px 的 `text-3` 圆环。超过 1 s 的处理（抠图、转码、导出、生成）不在这里，见「长任务」 |
| 内联编辑 | 点一下就能编辑。单行 ↵ 提交，多行 ⌘↵ 提交；Esc 取消并还原；失焦时提交；5 s 内可以用 toast 撤销 |
| 右键菜单 | 所有条目都能右键。宽 220–280，项高 28、圆角 6，`small`，图标 16 `text-3`，kbd 右对齐；分隔线上下各留 4；危险项放最后，用 `danger` 字。子菜单用安全三角（clip-path），鼠标可以斜着移过去。手机上长按调出系统菜单 |
| 空状态 | 列表型 app：视图中央，最大宽 360：24 px 线性图标 `text-3`、`title-3` 标题、一行 `text-2` 说明、一个主按钮（接了键盘时加 kbd 提示「记一笔 C」）。不放插画。媒体和 AI app 第一次打开时放示例素材，见「转化界面 → 示例空状态」 |
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

**媒体页强制深色**（编辑器、查看器、相机、视频播放；系统是浅色时也一样）：

- iOS：编辑器和查看器用 `fullScreenCover` 呈现，根视图加 `.preferredColorScheme(.dark)`（它作用于整个呈现层，所以只加在全屏呈现的根视图上）。推进导航栈的媒体页用 `.environment(\.colorScheme, .dark)` 加 `.toolbarColorScheme(.dark, for: .navigationBar)`。底用 `Palette.mediaBlack.ignoresSafeArea()` 或 `Palette.mediaDark`。查看器隐藏控件时加 `.statusBarHidden(true)` 和 `.persistentSystemOverlays(.hidden)`。
- Android：媒体页包一层 `AppTheme(dark = true) { … }`；TopAppBar 的底用 `AppTheme.colors.mediaBlack`；进入时把状态栏图标改成浅色（`WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false`），离开时还原。查看器隐藏控件时 `hide(WindowInsetsCompat.Type.systemBars())`，行为设成 `BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE`。
- Web：媒体页的根元素写 `data-theme="dark"`，`<meta name="theme-color" content="#000000">`。

**Web / 桌面**（可选）：

- 倒 L 布局（见「用法速查」）。
- `prefers-color-scheme` 和 `[data-theme]` 切换深浅色，`prefers-contrast: more` 换高对比，`prefers-reduced-motion` 减弱动效；`theme.css` 已经写好这几条。

## 不要

- 大面积的主色（整屏绿、主色顶栏）；主色出现在「主色的用途」以外
- 用主色标侧栏当前项、键盘光标行、菜单当前项、筛选 pill、比例 chip 或当前工具
- 拿 `primary` 写字，或拿 `primary-text` 做按钮底
- 红色、橙色或黄色的主按钮；红底的删除按钮（危险操作用 `danger` 字）
- 灰色或红色做主色；第二个强调色
- 卡片投影；渐变按钮、霓虹描边、彩色投影、内阴影
- 卡片里再套一层描边；桌面列表行之间画分隔线
- 用 `text-placeholder` 写要读的文字
- 卡片和列表用玻璃；玻璃带颜色；Android 栏用色调提升
- 照片上叠玻璃或主色浅底（查看器用 `viewer-scrim`，选中用描边加勾）；编辑页、查看页跟着系统变浅色；画布用带色相的 `bg` 或 `surface`
- 写死的颜色、圆角、尺寸和时长；手写色值代替 LCh 推导
- 弹窗以外用 `scrim`；命令菜单后面铺 `scrim`（用 `scrim-menu`）
- 瞬时的本地操作显示 spinner；超过 1 s 的处理只给转圈，没有进度、剩余时间和取消；300 ms 内就出骨架；shimmer 扫光
- iOS 26 以下或没有后台任务时写「可以离开 app」
- 同一个动作在不同地方叫不同的名字，或有两个快捷键
- 工作界面的空状态放插画（转化界面可以用几何切片）；人物插画、3D 渲染、渐变光斑
- 手机上显示 kbd、快捷键提示或悬停效果；某件事只能用快捷键做
- 付费墙的关闭按钮延迟出现或做得很淡；藏起「恢复购买」、总价或自动续费说明；默认选最贵的方案又不写总价
- 启动时、出错后请求评分；自己弹「喜欢这个 app 吗」
- 全屏的自家 app 推广；在启动、引导、付费墙、编辑过程中推广
- 没说清楚就把照片或文字发给第三方 AI；没有举报入口的 AI 内容
- 字重 700；中日韩文字加字距
- 小于 `hit-min` 的点击区；手机套用桌面密度
- 回弹明显的动效（Compose expressive 方案、大弹簧）

## 写界面时自查

- [ ] 浅色、深色都看过；打开系统的增强对比度也看过一次
- [ ] 主色只出现在「主色的用途」里，一屏面积桌面 ≤ 5 %、手机 ≤ 8 %（照片不算；转化界面 ≤ 15 %）；没有暖色或红底按钮，红色不做主色
- [ ] 侧栏当前项、光标行用 `surface-2`，菜单当前项用 `menu-active`，筛选 pill 选中用 `surface-3`
- [ ] 文字用 `text` / `text-2` / `text-3`；`text-placeholder` 只在占位、禁用、装饰上；链接和选中文字用 `primary-text`
- [ ] 层次靠明度差和 1 px `border`；卡片没有投影；浮层是 `elevated` + `border` + `elev-2` / `elev-3`
- [ ] 每个动作有一个名字（三种语言按术语表），在 ⌘K 或手机的搜索里能搜到；kbd 和快捷键提示只在接了键盘时出现
- [ ] 本地操作乐观更新，失败回滚并给 `danger` toast；可撤销的操作给「撤销 ⌘Z」
- [ ] 悬停 0 ms 进、150 ms 出；「减弱动态效果」下没有位移和缩放
- [ ] 桌面行高 36、正文 13–14；手机点击区 ≥ 44 / 48，字号跟平台
- [ ] 图标只用一套库：Lucide 1.5 px 不缩放 / SF Symbols regular / Material Symbols Rounded 300；默认 `text-3`
- [ ] iOS 用系统栏和 Liquid Glass，栏没有自定义背景；Android TopAppBar 不透明、无色调提升
- [ ] 金额带符号和货币、tabular 数字；日期、数量按「文案格式」
- [ ] 编辑页、查看页在浅色系统下也是深色，画布是 `media-*`；照片上没有玻璃和主色浅底；照片选中是描边加勾
- [ ] 超过 1 s 的处理有确定进度、剩余时间和取消；能在后台继续的接上了，不能的没有承诺；进行中用 `in-progress`
- [ ] 有中间点的滑块会吸附；选中、吸附、完成、失败有触感，别处没有
- [ ] AI：提示词框、四种状态、点数、举报、第三方 AI 同意页都有
- [ ] 付费墙有关闭、恢复购买、条款和隐私链接、价格和自动续费说明；设置按 通用、外观、语言、会员、支持、关于 排

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
| 「进行中」用 `warning`（状态饼、标签、队列） | `in-progress`（= `info`） | 不报错，必须搜出来改；`warning` 只留给真要注意的事 |
| kbd 一直显示 | kbd 是键盘层：Web 触屏上自动隐藏；Swift 的 `.kbd()` 要根视图加了 `.keyboardLayer()` 才画 | 不加 `.keyboardLayer()` 时 iPad 上的 kbd 也不画了，必须手动加 |

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
  - 媒体：颜色 `var(--c-media-dark)`、`var(--c-on-media)`、`var(--c-media-selected)`、`var(--c-in-progress)` 等；类 `.checker`（棋盘格）、`.viewer-scrim-top` / `.viewer-scrim-bottom`（高 `--viewer-scrim-h`）、`.media-selected`（只画描边，勾自己放：`primary` 圆、白勾、1.5 px 白圈）；尺寸 `--tool-tray-h`、`--tool-item-w`、`--slider-track-h`、`--slider-thumb`、`--crop-handle`、`--crop-stroke`、`--playhead-w`、`--timeline-h`、`--thumb-gap`、`--select-outline`、`--select-check`、`--prompt-min-h`、`--prompt-max-lines` 等；时间码 `.t-timecode`（自带等宽数字）；动效 `--m-zoom`、`--m-zoom-exit`；手势参数 `--gesture-*`；触感 `--haptic-*`（`navigator.vibrate` 用的毫秒数，iOS Safari 不振动）。
  - 键盘层：触屏上 `.kbd` 自动隐藏；平板接了键盘时，用这几行脚本在第一次按快捷键后显示：

    ```js
    // show the keyboard layer once a hardware keyboard is used: a shortcut, or Tab / arrows outside text fields
    addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || (/^(Tab|Arrow)/.test(e.key) && !e.target.matches('input, textarea, [contenteditable]')))
        document.documentElement.setAttribute('data-keyboard', '');
    });
    ```
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
  - 媒体：`bg-media-black` … `bg-media-white`、`text-on-media`、`text-in-progress`；`bg-checker`（图案和格子大小一起）；`bg-viewer-scrim-top` / `bg-viewer-scrim-bottom` 加 `h-viewer-scrim`；照片选中 `ring-select ring-inset ring-media-selected`；`h-tool-tray`、`h-slider-track`、`h-timeline`、`min-h-prompt`；`text-timecode tabular-nums`；`duration-zoom`、`duration-zoom-exit`。
- **SwiftUI**：把 `Theme.swift` 加进项目，需要 iOS 15 以上；用 Xcode 26 编译、跑在 iOS 26 以上时 `.frost()` 是 Liquid Glass。
  - 颜色 `Palette.*`（token 名转小驼峰：`Palette.canvas`、`Palette.elevated`、`Palette.menuActive`、`Palette.text3`、`Palette.primaryText`、`Palette.selected`），每个都按深浅和「增强对比度」自动四选一。
  - 字体 `.font(.rowTitle)`、`.rowMeta`、`.sectionHeader`、`.cardTitle`、`.longText`、`.tagLabel`、`.amount`（等宽数字）、`.pageTitle`，都基于系统文字样式，支持 Dynamic Type。页面标题优先用导航栏的大标题。长段中文用 `Text(…).longText()`（`.longText` 加 6 pt 行距，合 17 / 28）。
  - 圆角 `Radius.lg`；间距 `Space.s4`（16）；尺寸 `Size.hitMin`、`Size.controlMd`、`Size.controlLg`、`Size.row`（60）、`Size.rowSingle`（44）、`Size.pill`（36）；图标 `Icon.sm / md / lg`、`Icon.weight`。
  - 动效 `Motion.spring`（`.spring(response: 0.3, dampingFraction: 0.9)`），`Motion.fast`、`.standard`、`.slow` 和对应的 `fastExit`、`standardExit`、`slowExit`。
  - 卡片 `.card()`（实底加发丝线，无阴影）；浮层阴影 `.elev2()`、`.elev3()`，加在背景形状上，不加在带字的视图上。
  - 自定义浮动控件加 `.frost(radius: 高度的一半, floating: true, interactive: true)`：iOS 26 以上是 `glassEffect(.regular.interactive())`，以下是 `.ultraThinMaterial` + `frost` 色 + 发丝线 + 顶部高光。贴边的栏用 `.frost(edges: .bottom)` 或 `.top`。系统栏、toolbar、TabView 不要加 `.frost()`，也不设背景。几个玻璃控件并排时放进同一个 `GlassEffectContainer`。
  - 媒体：`Palette.mediaBlack / mediaDark / mediaMid / mediaWhite`、`checkerA / checkerB`、`onMedia`、`viewerScrim`、`mediaEdge`、`mediaGuide`、`mediaSelected`、`inProgress`；视图 `Checkerboard()`、`ViewerScrim(edge: .top)`，修饰 `.mediaSelected(isSelected)`（描边加勾）；尺寸 `Size.toolTray`、`Size.sliderThumb`、`Size.cropHandle`、`Size.timeline`、`Size.selectOutline`、`Size.viewerScrim`、`Size.promptMin`、`Size.promptMaxLines` 等；时间码 `.font(.timecode)`。
  - 手势和触感：`MediaGesture.zoomDoubleTap`、`.zoomMax`、`.deceleration`、`.dismissDistance`、`.dismissVelocity`；滑块吸附 `MediaGesture.snapped(value, in: -100...100)`；触感 iOS 17 起 `.sensoryFeedback(Haptic.snap.feedback, trigger: value)`，更早在动作里调 `Haptic.snap.play()`；转场 `Motion.zoom` / `Motion.zoomExit`。
  - 键盘层：根视图加 `.keyboardLayer()`；`Text("⌘K").kbd()` 只在 iPad、Mac 接了硬件键盘时画，iPhone 上不画。
- **Jetpack Compose**：把 `Theme.kt` 放进 `theme` 包，用 `AppTheme { … }` 包住界面。需要 Compose Material 3 1.2 以上，基线是 1.4。
  - `AppTheme(dark, highContrast, fontFamily)`：深浅跟随系统；`highContrast` 默认读 `isSystemHighContrast()`（API 34 以上的系统对比度 ≥ 0.5）；固定品牌色，没有动态取色。
  - 字体：把 Roboto Flex 可变字体放进 `res/font/roboto_flex.ttf`，传 `AppTheme(fontFamily = robotoFlex(R.font.roboto_flex))`；不传时是系统 Roboto。金额用 `MaterialTheme.typography.bodyLarge.tabular`。
  - 颜色角色：`colorScheme.primary` 是 `primary-text`，所以 TextButton、选中的导航项、复选框和开关这类拿 primary 着色的组件在深色下也过 4.5:1（复选框的勾和开关圆钮是 `onPrimary`，深色下是深色，不要改成白）；`colorScheme.surface` 是 `bg`；`surfaceContainerLowest` … `surfaceContainerHighest` 依次是 `canvas`、`bg`、`surface`、`surface-2`、`surface-3`；`secondaryContainer` 是 `surface-3`（导航指示器和选中的 FilterChip 因此是中性色）；`outline` 是 `border-strong`，`outlineVariant` 是 `border`；`error` / `errorContainer` 是 `danger`。
  - Material 3 没有的颜色用 `AppTheme.colors`：`primaryFill`（即 `primary`）、`onPrimaryFill`、`primaryFillHover`、`primaryFillPressed`、`primaryText`、`surface`（卡片色）、`surface2`、`surface3`、`canvas`、`elevated`、`menuActive`、`text3`、`textPlaceholder`、`selected`、`success`、`warning`、`info` 及其 container、`hover`、`pressed`、`scrim`、`scrimMenu`、`frost` 等。
  - 组件：主按钮 `AppButton`（`primaryFill` 底，悬停和按下变暗：进 0 ms、出 150 ms），次按钮 `AppOutlinedButton`（危险操作传 `contentColor = MaterialTheme.colorScheme.error`；两个按钮都能传 `interactionSource`），卡片 `AppCard`（`surface` 底、1 dp `outlineVariant`、无阴影），筛选 `AppChip(selected, onClick, label, selectedIcon = { 18 dp 的勾 })`（勾只在选中时出现），状态 `StatusTag("已入账", AppTheme.colors.success, AppTheme.colors.successContainer, icon = { … })`，新建 `AppFab`，底栏 `AppNavigationBar`。不要直接用 `Button`、`Card`、`FilterChip`、`FloatingActionButton`、`NavigationBar`。
  - 栏：`TopAppBar(colors = appTopBarColors(), scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior())`：不透明 `bg`，滚动后不变色；滚动后的 1 dp 线自己画，放在同一个 `Column` 里：`if (scrollBehavior.state.contentOffset < 0f) HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)`。底栏 `AppNavigationBar { NavigationBarItem(colors = appNavigationItemColors(), …) }`（`surface` 底、顶部 1 dp 线、无色调提升）。ModalBottomSheet、ModalNavigationDrawer 传 `scrimColor = AppTheme.colors.scrim`。
  - 尺寸：`Radius.lg`、`Space.s4`、`AppSize.hitMin`（48）、`AppSize.controlLg`（50）、`AppSize.row`（72）、`AppSize.rowSingle`（48）、`AppSize.navigationBar`、`AppSize.fab`；`IconSize.sm / md / lg`、`IconSize.WEIGHT`（300）；`ButtonShape`（12）、`TagShape`（全圆）；`AppShapes` 是 4 / 6 / 8 / 12 / 16。
  - 动效：`tween(Motion.STANDARD_MS, easing = Motion.Enter)` 进场，`tween(Motion.STANDARD_EXIT_MS, easing = Motion.Exit)` 退场；弹簧用 `Motion.spatial()`、`Motion.effects()`（即 `MotionScheme.standard()` 的参数）。
  - 媒体：`AppTheme.colors.mediaBlack` …、`onMedia`、`mediaSelected`、`inProgress`；`Modifier.checkerboard(AppTheme.colors)`、`Modifier.mediaSelected(selected, AppTheme.colors)`（只画描边，勾按 `AppSize.selectCheck` 自己放）、`ViewerScrim.top` / `ViewerScrim.bottom` 加 `ViewerScrim.height`；尺寸 `AppSize.toolTray`、`AppSize.cropHandle`、`AppSize.timeline`、`AppSize.promptMin`、`AppSize.PROMPT_MAX_LINES` 等；时间码 `MaterialTheme.typography.timecode`；滑块 `Slider(colors = appSliderColors())`。
  - 手势和触感：`MediaGesture.ZOOM_DOUBLE_TAP`、`ZOOM_MAX`、`DISMISS_DISTANCE`、`dismissVelocity`，吸附 `MediaGesture.snapped(v, range)`；触感 `LocalHapticFeedback.current.performHapticFeedback(Haptic.snap)`（Compose UI 1.8 起）；转场 `Motion.ZOOM_MS` / `ZOOM_EXIT_MS`。
  - 键盘层：`if (hasHardwareKeyboard())` 才画快捷键提示。
  - 玻璃：Compose 没有系统背景模糊，栏默认不透明；要玻璃时用 Haze 这类库，参数取 `Frost.blur`、`Frost.SATURATION` 和 `AppTheme.colors.frost / frostBorder / frostHighlight`。
  - M3 Expressive（1.5.0-beta01 以上）：把 `AppTheme` 里的 `MaterialTheme` 换成 `MaterialExpressiveTheme(colorScheme = colors, motionScheme = MotionScheme.standard(), shapes = AppShapes, typography = typography, content = content)`，见 `Theme.kt` 的注释；不用 `MotionScheme.expressive()`。
- **其他框架**（UIKit、Flutter、React Native 等）：按 `tokens.json` 的 key 映射，例如 `color.light.primary`、`color.dark-hc.text-2`、`radius.lg`、`space.4`（16）、`size.control-h.desktop.md`、`size.row.desktop`、`font.web.scale.small`（size、line、weight、tracking、opsz）、`font.ios.styles.row-title`、`font.android.scale.bodyLarge`、`elevation.dark.2`（阴影层数组）、`motion.duration.hover-out`、`motion.ease.enter`、`blur.frost`、`icon.size.sm`；媒体和 AI 的 `color.dark.media-dark`、`size.media.tool-tray`、`size.prompt.min`、`size.prompt.max-lines`、`gradient.viewer-scrim`（颜色和渐变停点）、`motion.duration.zoom`、`motion.gesture.zoom-max`、`haptic.snap.ios`、`font.ios.styles.timecode`、`font.android.timecode`。四套颜色都要接上，按系统的深浅和对比度设置选一套。
