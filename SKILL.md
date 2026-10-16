---
name: rian-app-theme
description: Design an app's UI theme in Rian's house style, the graphite style after Linear with Apple and Google platform specs - graphite and paper-white neutral ladders derived in LCh, 1 px hairlines and lightness steps instead of card shadows, one accent taken from the app icon, and a high-contrast set built alongside the standard one. Exports colour tokens (light, dark and both high-contrast), type, spacing, radii, elevation, motion and a frost material as CSS, SwiftUI, Jetpack Compose and Tailwind, asserts WCAG contrast, and renders a preview with iPhone, Android and a desktop window with the command menu open. Also covers keyboard-first UX: command menu, shortcuts, optimistic updates, inline editing. Use when asked for an app theme, design tokens, colour scheme, dark mode or UI style, and when building screens of an app that uses this theme. Not for chart palettes, slides or marketing sites. 用于按 Rian 的石墨风格（Linear 式：LCh 中性色阶梯、发丝线分层、单一强调色、键盘优先）生成 app UI 主题、配色、深色和高对比模式、设计 token，以及用这套主题写界面。
---

# Rian App Theme

把 app 图标的强调色变成一整套 UI 主题：深浅两种模式 × 标准和高对比两档，共四套颜色 token；桌面和手机两套字号，加上间距、圆角、阴影、尺寸、动效、界面图标规范和 frost 材质。导出成 CSS、SwiftUI、Compose 和 Tailwind，并渲染一张对照图：两部 iPhone、一部 Android、一个打开 ⌘K 命令菜单的桌面窗口。

风格和图标 skill（`rian-app-icon`）是同一种：**石墨**。深石墨和纸白两套 LCh 中性色阶梯（色相 265，和图标的底是同一种石墨），用 1 px 发丝线和明度差分层，单一强调色，键盘优先，排得密但不挤。线条、密度和克制来自 Linear；材质、字体和图标规格来自 Apple；无障碍硬指标和动效参数来自 Google。

**生成主题不需要先读 `references/rules.md`**：颜色、对比度、尺寸都由脚本决定。之后写界面代码时，再读其中的「用法速查」「命令菜单」「UX 模式」「图标」「不要」。

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

- **有图标时**：把图标强调色的**色名**原样传给 `--accent`：蓝、绿、紫、珊瑚、黄、灰，中英文都可以（`--accent coral`）。脚本自己换算（珊瑚、黄、灰会打印一行提示，`tokens.json` 的 `source.icon-accent` 记下图标色）。传色值时只认六色表里的「浅」「主」两个值（如 `#3B7BEA`），别的色值会被拒。
- **只有品牌色、没有图标时**：红、橙、黄、棕、灰 → 蓝；其余取最接近的蓝、绿、紫。不要自造颜色。
- **什么都没有**：蓝。不传 `--accent` 就是蓝。

主色只取强调色的色相和彩度，明度由脚本按对比度定。中性色固定是石墨（色相 265），不跟主色变。

红色（珊瑚）永远不做界面主色；界面上不要出现红色、橙色或黄色的主按钮。

信息不全时自己补一个合理版本，标明「这是我的假设」，然后继续。

### 2. 生成

```bash
python3 scripts/build.py --name Tide --accent 珊瑚 -o themes/tide   # 图标是珊瑚 → 界面蓝
python3 scripts/build.py --name Ledgerly --accent 绿 -o themes/ledgerly
```

色名中英文都可以（`--accent green`）。脚本在 CIE LCh（D65）里推导所有颜色：

- **中性色**：按 `assets/palette.json` 的 `base`（色相 265，彩度深 1.6、浅 1.2）和 `ladder` 生成 `canvas` → `surface-3` 的阶梯和四级文字。
- **主色**：色相和彩度固定，只走 L（步长 0.5）。`primary` 是填充，取白字刚好 ≥ 4.5:1 的最高 L，深浅两种模式同值；`primary-text` 是链接和选中文字，深色往亮走、浅色往暗走，直到在每个底上 ≥ 4.5:1。状态色同法。
- **两档对比度一起生成**：`standard` 和 `high`，深浅各一，输出 `light`、`dark`、`light-hc`、`dark-hc` 四套。高对比档的 `text` 取端点（纯白 / L 6），`text-2` ≥ 10:1，`text-3`、`primary-text` 和状态色 ≥ 7:1，`border` 换成 `border-strong`，frost 不透明度从 .80 提到 .94。Web 按 `prefers-contrast: more`、iOS 按「增强对比度」、Android 14 以上按系统对比度设置自动切换，不用另外做。

每个前景色都放在它可能出现的每个底上检查 WCAG 对比度（表见 `rules.md`「颜色」），标准和高对比各打印一张矩阵（`!` 是不过，`~` 是过了断言但没到目标）。全过时打印四套的主色和文字色、一行 `legend:`（重复图例，并列出所有 `~` 格子，用 `tail` 也看得到）和一行 `contrast: all pass (standard, high)`，再写文件；有不过的组合时，列出失败项、什么都不写、退出码 1。

输出 `tokens.json`、`theme.css`、`Theme.swift`、`Theme.kt`、`tailwind.preset.js`。

**不要手改生成的颜色。** 想调颜色，就换一个强调色重新生成；中性色要改时改 `assets/palette.json`（`base`、`ladder`、`text`、`alpha`），规则本身要改时改 `build.py` 的 `derive()`。

### 3. 预览、自检

```bash
ICON_SKILL=~/.claude/skills/rian-app-icon   # rian-app-icon 的目录，按实际改
python3 $ICON_SKILL/scripts/render.py tide.svg -o icons --variants   # 写出 icons/tide-1024.png 和 icons/tide-dark.png
python3 scripts/preview.py themes/tide --screen timer \
  --icon icons/tide-1024.png --icon-dark icons/tide-dark.png
```

- `--screen` 选最接近这个 app 的样例界面：`timer`（计时、工具类，默认）、`notes`（笔记、阅读类：长段中文、高亮、搜索框）、`list`（账本、列表类：金额、筛选 pill、按天分组的列表）。三个都不贴的（翻译、聊天、天气、相机……）用 `timer`。每个界面都有手机和桌面两份内容，组件条、字号表和色板的示例字也跟着界面换。
- `--icon` 用 `rian-app-icon` 的 `render.py` 写出的 `<name>-1024.png`（默认石墨外观）；`--icon-dark` 用加 `--variants` 时同一个 `-o` 目录里的 `<name>-dark.png`。已经渲染过就直接用那个目录；没有深色版就省略，深色界面沿用 `--icon`。还没有图标就两个都省略：图标位置画一个石墨占位图，标题行注明「未传 --icon」。
- 桌面窗口默认深色，`--desktop-mode light` 换成浅色；旁边的桌面字号表用另一种模式。
- 第一次运行会从 Google Fonts 下载 Inter、Roboto Flex、Material Symbols Rounded 和用到的 Noto Sans SC 字，缓存在 `~/.cache/rian-app-theme/fonts`。没有网络时自动退回本机字体（`--offline` 强制），标题行注明，断言照常。iPhone 屏上用 Inter 代替 SF Pro。

预览图是 1960 宽的画板，按 2x 截图（3920 px 宽），从上到下：

1. 标题行：app 名；图标色 → 界面主色；`primary` 和悬停 / 按下、深浅两种 `primary-text`；中性色色相；样例界面；字体；生成时间。
2. 第一行：iPhone 浅色静止态（390 × 844 pt）；iPhone 深色滚动态（内容滚到玻璃栏下面，带一条 toast）；Android 浅色（M3，Pixel 412 × 915 dp，内容滚过一点，TopAppBar 只加 1 px `border`）；浅色和深色两列组件条（按钮各态、输入框、标签、徽章、kbd、复选框、开关、菜单）。
3. 第二行：1280 × 800 的桌面窗口，倒 L 布局，有键盘光标行和两行多选，⌘K 命令菜单打开。右边一列：另一种模式的桌面字号表（9 级）；下面一格，图标是珊瑚、黄、灰时是「图标 × 界面」（图标配上回落到蓝的界面小窗口，深浅各一），否则是一个确认弹窗。
4. 色板：`light`、`dark`、`light-hc`、`dark-hc` 四列，每列有中性色阶梯、各档文字在最差背景上的对比度、主色一族、状态色和 frost 条。

脚本先打印一行 `sizes:`，是实测的控件尺寸（iOS 工具栏按钮 44 × 44、筛选 pill 高 36、行高 60，M3 TopAppBar 64、FilterChip 32、列表项 72、FAB 56，桌面行 36、侧栏项 28、命令项 36、kbd 18），和 `references/rules.md` 对不上就是哪里改坏了。最后打印四行断言，每行 PASS 或 FAIL；有 FAIL 时退出码是 1，`preview.png` 照样写出：

- `frost light`、`frost dark`：栏上文字和图标对滚到下面的内容的最低对比度 ≥ 3:1。只量玻璃本身：量的时候隐藏 iOS 的滚动边缘渐隐，滚动态居中的小标题不量。深色在第二部 iPhone 上量；浅色在画板外另渲染的一部浅色滚动态 iPhone 上量（不在图里）。
- `accent area desktop`：桌面窗口里主色像素（LCh 色相 ±25°、彩度 ≥ 20）≤ 5 %，命令菜单和遮罩隐藏后量；把 `selected` 浅底也算进去（彩度 ≥ 4）的数字只报 INFO。
- `accent area phone`：每部手机的屏幕 ≤ 8 %，报三部里最高的一部；INFO 同上。

打开 `preview.png` 亲眼看，**只查三件事**：

1. **主色符合第 1 步的表**。标题行写着主色和图标色；有「图标 × 界面」那一格时，暖色图标和蓝色界面放在一起站得住。
2. **`build.py` 打印了 `contrast: all pass (standard, high)`**。
3. **`preview.py` 的 `frost light`、`frost dark` 两行 PASS，且 `accent area desktop`、`accent area phone` 都 PASS**。

三项都过就交付。用户之后提意见时，常见的情况：

| 看到 | 改 |
|---|---|
| 整个界面太花，或 `accent area` FAIL | 主色只给七种用途（`rules.md`「主色」）；侧栏当前项、键盘光标行、菜单当前项、筛选 pill 选中一律中性；列表图标用 `text-3`；「完成」是默认态的列表不画每行的绿勾 |
| 线太多、显得乱 | 一个区域只用一道线；桌面列表行之间不画线，靠组头分组；卡片里不套描边 |
| 深色下层次看不清 | 正常：每级只差约 2.5 L，层次靠明度差加 1 px `border`。不要给卡片加投影；菜单当前项用 `menu-active`，不用 `surface-3` |
| 深色模式的主按钮没有提亮 | 正常：`primary` 是填充，深浅同值，保证白字 ≥ 4.5:1。深色下更亮的是 `primary-text`（链接、选中文字、焦点环） |
| 高对比模式下文字更白、边框更明显 | 正常：高对比档的正文取端点，`border` 换成了 `border-strong` |
| 静止时看不出 frost | 正常：frost 要在滚动态里看。栏上文字对身后内容 ≥ 3:1，以 `preview.py` 的 frost 行为准 |
| 和图标对不上 | 确认 `--accent` 用的是图标的强调色；图标是珊瑚、黄或灰时，界面用蓝是对的，看「图标 × 界面」那一格 |
| 桌面太挤或太松 | 桌面正文 13–14、列表行 36（紧凑 32）。手机不套桌面密度，沿用平台字号和 44 / 48 点击区 |
| 用户想要红色或橙色主按钮 | 不改：红色只给错误和危险操作；危险操作用次按钮样式加 `danger` 字 |
| 用户想用 Font Awesome 等粗图标 | 说明不合适的原因（见 `rules.md`「图标」），推荐下面各平台的图标库 |

### 4. 交付

给用户：预览图、三行说明（图标色 → 界面主色；`primary` 和深浅两种模式下 `primary-text` 的色值；生成了哪些文件）和输出目录。告诉他们各平台怎么接入（见 `references/rules.md` 的「接入」），深色和高对比都会跟随系统设置，以及该用哪套界面图标库：

| 平台 | 图标库 | 设置 |
|---|---|---|
| Web / 桌面 | Lucide | 线宽 1.5 px，加 `vector-effect: non-scaling-stroke`，16 / 20 / 24 三种尺寸下线宽都不缩放 |
| iOS | SF Symbols | `.regular` |
| Android | Material Symbols Rounded | weight 300、fill 0 |

用户用什么语言说话，说明就用什么语言。

### 之后写界面

给用这套主题的 app 写界面时，先读 `references/rules.md` 的「用法速查」「命令菜单」「UX 模式」「图标」「不要」。颜色、圆角、尺寸、动效都用 token，不写死数值；写完按「写界面时自查」过一遍。
