---
name: rian-app-theme
description: Design an app's UI theme in Rian's house style, the graphite style after Linear with Apple and Google platform specs - graphite and paper-white neutral ladders in LCh, hairlines instead of card shadows, one accent from the app icon, thin line icons and brand surfaces that reuse the icon's graphite and line mark, a high-contrast set alongside. Phone first. Exports colour, type, spacing, radii, elevation, motion, haptics, media tokens and a frost material as CSS, SwiftUI, Jetpack Compose and Tailwind, asserts WCAG contrast, and renders a phone preview (list, photo editor or AI chat screens; a desktop window is optional). Also covers editors and viewers, AI chat and generation, long tasks, paywalls, onboarding, settings and an optional keyboard layer. Use when asked for an app theme, design tokens, colour scheme, dark mode or UI style, and when building screens of an app that uses this theme. Not for chart palettes, slides or marketing sites. 用于按 Rian 的石墨风格生成 app UI 主题、配色、深色和高对比模式、设计 token，以及用这套主题写界面。
---

# Rian App Theme

把 app 图标的强调色变成一整套 UI 主题：深浅两种模式 × 标准和高对比两档，共四套颜色 token；手机和桌面两套字号，加上间距、圆角、阴影、尺寸、动效、触感、媒体色组（编辑器和查看器用）、品牌色组（图标的石墨底、主体和强调色，给品牌位用）、界面图标规范和 frost 材质。导出成 CSS、SwiftUI、Compose 和 Tailwind，并渲染一张以手机为主的对照图：样例界面的 iPhone 浅色和深色、Android，再加三部共用外壳或媒体、AI 页面；桌面窗口可选。

风格和图标 skill（`rian-app-icon`）是同一种：**石墨**。深石墨和纸白两套 LCh 中性色阶梯（色相 265，和图标的底是同一种石墨），用 1 px 发丝线和明度差分层，单一强调色，排得密但不挤；照片和生成结果放在彩度 0 的中性画布上。只有这一种风格，键盘层和桌面窗口是可选的附加层。线条、密度和克制来自 Linear；材质、字体和图标规格来自 Apple；无障碍硬指标和动效参数来自 Google。

**生成主题不需要先读 `references/rules.md`**：颜色、对比度、尺寸都由脚本决定。之后写界面代码时，按 app 的类型读其中几节（见最后的「之后写界面」）。

**节奏**：按第 1 步的表直接定主色，不用等用户确认；生成、预览各跑一次，第 3 步三项都过就交付。不要反复调色。

## 工作流程

### 1. 定主色

主题只从一个颜色来：图标的**强调色**。六个色名见 `assets/palette.json`，和图标 skill 的强调色表相同。界面主色按这张表定，没有例外：

| 图标强调色 | 界面主色 |
|---|---|
| 蓝 | 蓝 |
| 绿 | 绿 |
| 紫 | 紫 |
| 珊瑚、黄、灰 | 蓝（原色只留在图标和品牌插图里） |

- **有图标时**：把图标强调色的**色名**原样传给 `--accent`：蓝、绿、紫、珊瑚、黄、灰，中英文都可以（`--accent coral`）。脚本自己换算（珊瑚、黄、灰会打印一行提示，`tokens.json` 的 `source.icon-accent` 记下图标色）。传色值时只认六色表里的「浅」「主」两个值（如 `#3B7BEA`），别的色值会被拒。
- **还没有图标时**：按类别传 `--category`，脚本取图标 skill 给这个类别的强调色，再按上表换算：

  | 类别 | 界面主色 |
  |---|---|
  | AI | 紫 |
  | 工具、图片、视频 | 蓝 |
  | 健康、财务 | 绿 |

  两个都传时以图标为准（不一致时打印一行提示）。
- **只有品牌色**：先按图标 skill 的选法换成六色里最接近的一个（绿除外，绿只给健康、财务），再按上表换算：红、橙、黄、棕、灰，以及健康、财务以外的绿，都落到蓝。不要自造颜色。
- **什么都没有**：蓝。不传 `--accent` 和 `--category` 就是蓝。

主色只取强调色的色相和彩度，明度由脚本按对比度定。中性色固定是石墨（色相 265），不跟主色变。

红色（珊瑚）永远不做界面主色；界面上不要出现红色、橙色或黄色的主按钮。

信息不全时自己补一个合理版本，标明「这是我的假设」，然后继续。

### 2. 生成

```bash
python3 scripts/build.py --name Tide --accent 珊瑚 -o themes/tide       # 图标是珊瑚 → 界面蓝
python3 scripts/build.py --name Ledgerly --accent 绿 -o themes/ledgerly
python3 scripts/build.py --name Ask --category AI -o themes/ask         # 还没有图标 → 紫
```

色名中英文都可以（`--accent green`、`--category image`）；类别的英文名和图标 skill 的 `data-category` 一样（tools、image、video、ai、health、finance）。脚本在 CIE LCh（D65）里推导所有颜色：

- **中性色**：按 `assets/palette.json` 的 `base`（色相 265，彩度深 1.6、浅 1.2）和 `ladder` 生成 `canvas` → `surface-3` 的阶梯和四级文字。
- **主色**：色相和彩度固定，只走 L（步长 0.5）。`primary` 是填充，取白字刚好 ≥ 4.5:1 的最高 L，深浅两种模式同值；`primary-text` 是链接和选中文字，深色往亮走、浅色往暗走，直到在每个底上 ≥ 4.5:1。状态色同法；`in-progress` 等于 `info`。
- **品牌色组**：品牌面板 `brand-surface-top → bottom` 跟着模式走：深色是图标的石墨（`#26282B → #191C1F`），浅色是浅石墨（L 96 → 92，色相 265，约 `#F2F4F6 → #E7E8EA`），都是上亮下暗的顶光；app 图标方块 `brand-tile-top → bottom` 四套都是石墨。主体的线 `brand-line`（平涂，浅色深线 `#2A2C2F`、深色亮线 `#E6E8EB`），图标强调色原色 `brand-accent`（取 `--accent` 或 `--category` 给的图标色，**不映射**：珊瑚的图标这里还是珊瑚），面板上的字 `on-brand` / `on-brand-2`（本模式的 `text` / `text-2`），`brand-edge`（深色面板和方块外一圈 1 px 白 12 %，浅色透明）。字、`primary` 填充、`focus` 和 `brand-line` 在面板渐变两端都过对比度；`brand-accent` 在深色面板上断言 3:1，浅色面板上只报数（主体靠深线认，同图标的浅色外观）。只给品牌位（启动页、引导、付费墙、权限预请求、同意页、空状态、关于页、导出完成页），强调色原色永远不进控件。
- **媒体色组**：四档彩度 0 的画布（`media-black`、`media-dark`、`media-mid`、`media-white`）、棋盘格、查看器遮罩、白色手柄和参考线、照片选中描边。编辑页和查看页在四套里都是深色，所以这组在四套里同值（选中描边跟 `primary-text`）。
- **两档对比度一起生成**：`standard` 和 `high`，深浅各一，输出 `light`、`dark`、`light-hc`、`dark-hc` 四套。高对比档的 `text` 取端点（纯白 / L 6），`text-2` ≥ 10:1，`text-3`、`primary-text` 和状态色 ≥ 7:1，`border` 换成 `border-strong`，frost 不透明度从 .80 提到 .94。Web 按 `prefers-contrast: more`、iOS 按「增强对比度」、Android 14 以上按系统对比度设置自动切换，不用另外做。

每个前景色都放在它可能出现的每个底上检查 WCAG 对比度（表见 `rules.md`「颜色」），包括滑块填充段对轨道、白色控件在遮罩叠白图上、播放头对深色画布。标准和高对比各打印一张矩阵（`!` 是不过，`~` 是过了断言但没到目标）。全过时打印四套的主色和文字色、一行 `legend:`（重复图例，并列出所有 `~` 格子，用 `tail` 也看得到）和一行 `contrast: all pass (standard, high)`，再写文件；有不过的组合时，列出失败项、什么都不写、退出码 1。

输出 `tokens.json`、`theme.css`、`Theme.swift`、`Theme.kt`、`tailwind.preset.js`。

**不要手改生成的颜色。** 想调颜色，就换一个强调色重新生成；中性色要改时改 `assets/palette.json`（`base`、`ladder`、`text`、`alpha`、`media`），规则本身要改时改 `build.py` 的 `derive()`。

### 3. 预览、自检

```bash
ICON_SKILL=~/.claude/skills/rian-app-icon   # rian-app-icon 的目录，按实际改
python3 $ICON_SKILL/scripts/render.py tide.svg -o icons --variants   # 写出 icons/tide-1024.png、tide-dark.png、tide-mark.png 和 tide-mark-light.png
python3 scripts/preview.py themes/tide --screen timer \
  --icon icons/tide-1024.png --icon-dark icons/tide-dark.png
```

- `--screen` 选最接近这个 app 的样例界面：
  - `timer`（计时、工具类，默认）、`notes`（笔记、阅读类：长段中文、高亮、搜索框）、`list`（账本、列表类：金额、筛选 pill、按天分组的列表）。第二行是共用外壳：设置、付费墙、引导。
  - `editor`（照片、视频、相机类）：编辑、抠图和导出、裁剪，第二行是图库多选、查看器、权限预请求。
  - `chat`（AI 聊天、生成类）：对话、生成的四种状态、新对话的示例空状态，第二行是第三方 AI 同意、点数付费墙、举报。

  组件条、字号表和色板的示例字也跟着界面换。翻译、天气这类不贴的用 `timer`。
- `--icon` 用 `rian-app-icon` 的 `render.py` 写出的 `<name>-1024.png`（默认石墨外观）；`--icon-dark` 用加 `--variants` 时同一个 `-o` 目录里的 `<name>-dark.png`。已经渲染过就直接用那个目录；没有深色版就省略，深色界面沿用 `--icon`。还没有图标就两个都省略：图标位置画一个石墨占位图，标题行注明「未传 --icon」。
- 品牌插图用图标自己的主体，平涂（和界面图标一样没有渐变）：浅色模式是深线（`<name>-mark-light`），深色模式是亮线（`<name>-mark`）。`--mark` 传 `render.py --variants` 写出的 `<name>-mark.png`（或 `.svg`，旁边的 `-mark-light.svg` 一起用）；不传时自动找 `--icon` 旁边的 `<name>-mark.png`，再没有就从 `--icon` 的 PNG 里把石墨底抠掉；连 `--icon` 也没有时画一个占位主体（一圈 60 / 1024 的圆角线框加一块强调色）。PNG 在脚本里压平成两种线色，所以旧的渐变 mark 和抠出来的主体也是平的。
- `--desktop`（可选，只给 `timer`、`notes`、`list`）：再加一行 1280 × 800 的桌面窗口，倒 L 布局，有键盘光标行和两行多选，⌘K 命令菜单打开，旁边是另一种模式的桌面字号表和一个确认弹窗。桌面窗口默认深色，`--desktop-mode light` 换成浅色。app 有 iPad、Mac 或 Web 版时才加。
- 第一次运行会从 Google Fonts 下载 Inter、Roboto Flex、Material Symbols Rounded 和用到的 Noto Sans SC 字，缓存在 `~/.cache/rian-app-theme/fonts`。没有网络时自动退回本机字体（`--offline` 强制），标题行注明，断言照常。iPhone 屏上用 Inter 代替 SF Pro。照片是脚本自己画的，不需要图片文件。

预览图是 1960 宽的画板，按 2x 截图（3920 px 宽），从上到下：

1. 标题行：app 名；类别、图标色 → 界面主色；`primary` 和按下、深浅两种 `primary-text`；中性色色相；样例界面；字体；生成时间。
2. 第一行：样例界面的三部手机（iPhone 390 × 844 pt，Android 是 M3 的 Pixel 412 × 915 dp）；浅色和深色两列手机尺寸的组件条（按钮、分段控件和步进器、滑块、输入框、标签和状态徽章、长任务进度、开关和单选、长按菜单，最后一行是键盘层）。
3. 第二行：三部共用外壳或媒体、AI 页面；右边一列是手机字号表，下面一格，图标是珊瑚、黄、灰时是「图标 × 界面」（图标配上回落到蓝的界面小窗口，深浅各一），否则是这个界面的底部弹窗。
4. 加 `--desktop` 时：桌面窗口这一行。
5. 品牌位：启动页、关于、空状态、导出完成（浅色），空状态、导出完成（深色）六张小屏。浅色是浅石墨面板加深线主体，深色是石墨面板加亮线主体（主体上下各留 18 %，不被别的东西压住）；关于页的 app 图标深浅都是石墨，有类别时带类别徽章；按钮仍是 `primary`；下面一行写品牌色组的值。
6. 色板：`light`、`dark`、`light-hc`、`dark-hc` 四列，每列有中性色阶梯、各档文字在最差背景上的对比度、主色一族、状态色和 frost 条；下面是媒体色组和触感、手势参数。

脚本先打印一行 `sizes:`，是实测的控件尺寸，只列这张图上有的控件：每种界面都有 iOS 玻璃按钮 44 × 44、M3 TopAppBar 64、手机按钮高 50、分段控件 32、步进器 32、滑块圆钮 24；`timer`、`notes`、`list` 另有筛选 pill 高 36、iOS 行高 60、设置行 44、M3 列表项 72、FAB 56、付费墙方案 60；`editor` 另有工具托盘 64、工具项 64、裁剪手柄 20、选中勾 22；`chat` 另有提示词框最小高 48、发送键 40、回复操作 44；加 `--desktop` 时还有桌面行 36、侧栏项 28、命令项 36、kbd 18。和 `references/rules.md` 对不上就是哪里改坏了。最后打印断言，每行 PASS 或 FAIL；有 FAIL 时退出码是 1，`preview.png` 照样写出：

- `frost light`、`frost dark`：栏上文字和图标对滚到下面的列表的最低对比度 ≥ 3:1；`frost photo light`、`frost photo dark`：同样的玻璃对滚到下面的照片网格（有亮天空和高饱和的照片）≥ 3:1。只量玻璃本身：量的时候隐藏 iOS 的滚动边缘渐隐。这四部手机在画板外另外渲染（不在图里）。
- `viewer scrim`：查看器的白色控件透过遮罩、叠在亮照片上 ≥ 4.5:1。
- `accent area phone`：每部手机屏幕上主色像素（LCh 色相 ±25°、彩度 ≥ 20）≤ 8 %，报最高的一部；量的时候把照片、画布、生成的图和品牌插图隐藏（盖在上面的勾和选中描边照算；插图里是图标强调色，不是主色），把它们算进去的数字只报 INFO。`accent area conversion`：引导、付费墙、权限预请求、同意页和示例空状态 ≤ 15 %。把 `selected` 浅底也算进去（彩度 ≥ 4）的数字只报 INFO。
- `safe area`：付费墙、引导、权限预请求、同意页、导出和举报弹窗的内容都在 Home 指示条（Android 是手势条）上方结束，没有被挤进去。
- 加 `--desktop` 时多一行 `accent area desktop`：桌面窗口 ≤ 5 %，命令菜单和遮罩隐藏后量。

打开 `preview.png` 亲眼看，**只查三件事**：

1. **主色符合第 1 步的表，图标和界面是一家**。标题行写着主色和图标色；有「图标 × 界面」那一格时，暖色图标和蓝色界面放在一起站得住；引导、付费墙、权限预请求、同意页和品牌位那一行里，插图就是图标的线稿主体，平涂：浅色模式是浅面板加深线，深色模式是石墨面板加亮线；界面图标是 1.5 px 的细线，和插图的线是一家。
2. **`build.py` 打印了 `contrast: all pass (standard, high)`**。
3. **`preview.py` 的断言全是 PASS**（frost 四行、`viewer scrim`、`accent area` 各行、`safe area`）。

三项都过就交付。用户之后提意见时，常见的情况：

| 看到 | 改 |
|---|---|
| 整个界面太花，或 `accent area` FAIL | 主色只给「主色的用途」（`rules.md`「主色」）；侧栏当前项、键盘光标行、菜单当前项、筛选 pill、比例 chip、当前工具一律中性；列表图标用 `text-3`；「完成」是默认态的列表不画每行的绿勾 |
| 照片里的蓝天、绿树被算成主色 | 不会：量面积时照片、画布、生成的图都隐藏了（`data-photo`），INFO 行另报算进去的数字 |
| `safe area` FAIL | 那一页的内容太长：减插图高度、权益条数或行数，不要把按钮和链接挤到 Home 指示条上 |
| 浅色模式下编辑页、查看页还是黑的 | 正常：媒体页在四套里都是深色，画布彩度 0，看颜色才准（`rules.md`「媒体色组」） |
| 「进行中」是蓝色不是黄色 | 正常：`in-progress` 等于 `info`；`warning` 只给真要注意的事 |
| 手机上没有 kbd 和快捷键提示 | 正常：键盘层只在桌面、Web 和接了键盘的 iPad / Mac 上出现；手机上 ⌘K 对应搜索 |
| 线太多、显得乱 | 一个区域只用一道线；桌面列表行之间不画线，靠组头分组；卡片里不套描边 |
| 深色下层次看不清 | 正常：每级只差约 2.5 L，层次靠明度差加 1 px `border`。不要给卡片加投影；菜单当前项用 `menu-active`，不用 `surface-3` |
| 深色模式的主按钮没有提亮 | 正常：`primary` 是填充，深浅同值，保证白字 ≥ 4.5:1。深色下更亮的是 `primary-text`（链接、选中文字、焦点环） |
| 高对比模式下文字更白、边框更明显 | 正常：高对比档的正文取端点，`border` 换成了 `border-strong` |
| 静止时看不出 frost | 正常：frost 要在滚动态里看。栏上文字对身后内容 ≥ 3:1，以 `preview.py` 的 frost 行为准 |
| 和图标对不上 | 确认 `--accent` 用的是图标的强调色；图标是珊瑚、黄或灰时，界面用蓝是对的，看「图标 × 界面」那一格。插图不是图标的主体时，传 `--mark`（`render.py --variants` 的 `<name>-mark.png`） |
| 浅色模式里品牌面板是浅的 | 正常：浅色模式的面板是浅石墨、主体是深线，深色模式才是图标的石墨加亮线（`rules.md`「品牌色组」）；app 图标本身（关于页）深浅都是石墨 |
| 插图有渐变、和界面图标不像 | 用 `render.py --variants` 重出平涂的 `<name>-mark` / `-mark-light`；`preview.py` 会把 PNG 压平，代码里接的是文件本身 |
| 插图里是珊瑚、黄，按钮却是蓝 | 正常：图标强调色原色（`brand-accent`）只进插图和类别徽章；控件用界面主色 |
| 桌面太挤或太松 | 桌面正文 13–14、列表行 36（紧凑 32）。手机不套桌面密度，沿用平台字号和 44 / 48 点击区 |
| 用户想要红色或橙色主按钮 | 不改：红色只给错误和危险操作；危险操作用次按钮样式加 `danger` 字 |
| 用户想用 Font Awesome 等粗图标 | 说明不合适的原因（见 `rules.md`「图标」），推荐下面各平台的图标库 |

### 4. 交付

给用户：预览图、三行说明（图标色或类别 → 界面主色；`primary` 和深浅两种模式下 `primary-text` 的色值；生成了哪些文件）和输出目录。告诉他们各平台怎么接入（见 `references/rules.md` 的「接入」），深色和高对比都会跟随系统设置，以及该用哪套界面图标库：

| 平台 | 图标库 | 设置 |
|---|---|---|
| Web / 桌面 | Lucide | 线宽 1.5 px，加 `vector-effect: non-scaling-stroke`，16 / 20 / 24 三种尺寸下线宽都不缩放 |
| iOS | SF Symbols | `.regular` |
| Android | Material Symbols Rounded | weight 300、fill 0 |

图标的线稿和界面图标是同一种圆头细线（图标 60 / 1024，界面 1.5 px），不要换成实心图标。品牌位（启动页、引导、付费墙、空状态、导出完成页）的插图用图标平涂的 `<name>-mark-light.svg`（浅色，深线）和 `<name>-mark.svg`（深色，亮线），放在品牌面板上（`rules.md`「转化界面 → 品牌插图」）；品牌方块只给 app 图标本身，深浅都是石墨。

用户用什么语言说话，说明就用什么语言。

### 之后写界面

给用这套主题的 app 写界面时，先读 `references/rules.md` 的这几节，按 app 的类型取：

| app | 读 |
|---|---|
| 所有 app | 「用法速查」「颜色 → 品牌色组」「转化界面 → 品牌插图」「共用外壳」（设置、关于、启动页、评分、反馈、交叉推广、术语表）「UX 模式」「图标」「不要」 |
| 画布型（照片、视频、相机） | 加「编辑和查看」「视频」「长任务」，以及「平台适配 → 媒体页强制深色」 |
| 对话型（AI） | 加「AI」「长任务」 |
| 有引导、付费墙、权限请求 | 加「转化界面」 |
| 有 iPad、Mac 或 Web 版 | 加「命令菜单和键盘层」 |

颜色、圆角、尺寸、动效、触感都用 token，不写死数值；写完按「写界面时自查」过一遍。
