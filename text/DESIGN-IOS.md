# 深圳大学医院就医陪伴小程序 · iOS 风视觉设计规范

> 版本 v1.0 · 适老化保留版
> 适用范围：`frontend/miniprogram/` 下全部 7 个页面 + `app.wxss` + `app.json`（tabBar / navigationBar）

---

## 1. 设计原则

1. **系统级扁平（Flat, System-like）**：去除原"适老化"风格中的大面积渐变、彩色粗描边、浓重投影与高饱和彩色图标；改用 iOS 原生 UIKit 观感——分组灰底、白色卡片、hairline 分隔线、克制的填充色。
2. **层级干净**：只用「页面灰底 → 白色卡片 → 卡片内分组」三层；卡片之间用留白与 hairline 分隔，不堆叠阴影。
3. **克制用色**：主色仅用于可操作元素（按钮、选中态、链接、强调数字），大面积背景为中性灰白；语义色（成功/警告/危险/紫/青）只在对应语义场景出现。
4. **适老化可读性保留**：
   - 正文字号下限 32rpx（16pt），辅助文字下限 28rpx（14pt），标题下限 40rpx（20pt）；
   - 正文与背景对比度 ≥ 7:1（WCAG AAA），次要文字对比度 ≥ 4.5:1；
   - 可点击元素最小高度 88rpx（44pt），按钮高度 96rpx（48pt）；
   - 行高 ≥ 1.5 倍字号，段落间距充足。
5. **圆角与间距统一**：卡片/按钮统一 24rpx 圆角，输入框 20rpx，标签 pill 999rpx；外边距以 32rpx 为基准栅格。

---

## 2. 配色 Token（iOS 系统语义）

主色采用 iOS 系统蓝 `#007AFF`。全部色值为 hex，直接写入 WXSS。

### 2.1 背景与表面

| Token | 色值 | 用途 |
|---|---|---|
| `--bg-grouped` | `#F2F2F7` | 页面全局背景（iOS systemGroupedBackground） |
| `--bg-base` | `#FFFFFF` | 卡片、cell、输入框、导航栏底 |
| `--bg-elevated` | `#FFFFFF` | 浮层、底部输入条 |
| `--fill-quaternary` | `#F2F2F7` | 输入框底色、未选中 tab 底 |
| `--fill-tertiary` | `#E5E5EA` | 未选中按钮底色、分隔条浅底 |
| `--separator` | `#C6C6C8` | hairline 分隔线（0.5px 视觉） |
| `--opaque-separator` | `#EFEFF0` | 卡片内行间分隔（稍浅） |

### 2.2 主色（系统蓝）

| Token | 色值 | 用途 |
|---|---|---|
| `--blue` | `#007AFF` | 主按钮、选中态、链接、tabBar selected |
| `--blue-pressed` | `#0056CC` | 按钮按压态 |
| `--blue-tint` | `#E3F0FF` | 浅蓝填充（dept 信息框、选中行底、AI 头像底） |
| `--blue-tint-2` | `#D1E4FF` | 浅蓝描边 / 数字圆圈底 |

### 2.3 文本

| Token | 色值 | 用途 |
|---|---|---|
| `--label` | `#1C1C1E` | 一级标题、正文（近黑，高对比） |
| `--label-2` | `#3A3A3C` | 二级正文、说明 |
| `--label-3` | `#6D6D72` | 辅助文字、占位、hint |
| `--label-invert` | `#FFFFFF` | 蓝底白字 |

> 适老化说明：`--label-3` 由 iOS 默认 `#8E8E93` 加深为 `#6D6D72`，以保证灰字在白底上对比度 ≥ 4.5:1。

### 2.4 语义色

| Token | 色值 | 用途 |
|---|---|---|
| `--red` | `#FF3B30` | 危险按钮、错误、路线终点、警示 |
| `--orange` | `#FF9500` | 需空腹标签、警告提示、换楼层标记 |
| `--green` | `#34C759` | 成功态、已完成、起点 |
| `--purple` | `#AF52DE` | 用药须知图标 |
| `--teal` | `#5AC8FA` | 辅强调（可选） |

### 2.5 图标底色（统一浅 tint + 饱和图标字）

iOS 风不使用原"彩色实心圆 + 白字"，改为 **浅 tint 圆角方块 + 饱和色字**：

| 模块 | 底色 | 字色 |
|---|---|---|
| 导诊（蓝） | `#E3F0FF` | `#007AFF` |
| 导航（绿） | `#E8F8EE` | `#248A3D` |
| 流程（橙） | `#FFF4E5` | `#B25E00` |
| 用药（紫） | `#F3E8FF` | `#8944AB` |
| 挂号（红） | `#FFEBEA` | `#D70015` |
| 我的（灰） | `#EBEBEE` | `#4D4D54` |

---

## 3. 字体层级

小程序不自带 SF Pro，使用系统默认 `-apple-system` 栈（微信内置已渲染为苹方/思源黑体）。**只改字号/字重/行高，不引入字体文件。**

| 层级 | rpx | pt | 字重 | 行高 | 用途 |
|---|---|---|---|---|---|
| `large-title` | 56rpx | 28 | 700 | 1.25 | 页面大标题（科室名、对话欢迎） |
| `title-1` | 44rpx | 22 | 700 | 1.3 | 卡片主标题、当前步骤标题 |
| `title-2` | 36rpx | 18 | 600 | 1.35 | 区块标题、列表主文案 |
| `headline` | 34rpx | 17 | 600 | 1.4 | 卡片内小标题、按钮文字 |
| `body` | 32rpx | 16 | 400 | 1.65 | 正文（适老化下限） |
| `callout` | 30rpx | 15 | 400 | 1.55 | 次要正文、picker 文字 |
| `footnote` | 28rpx | 14 | 400 | 1.45 | hint、tag、时间戳（适老化下限） |

> 全局 `page` 字号 32rpx、行高 1.65。

---

## 4. 间距 / 圆角 / 栅格

- **页面左右边距**：32rpx（16pt）
- **卡片水平外边距**：24rpx（左右各 24，卡片宽 ≈ 屏幕 - 48rpx）
- **卡片垂直间距**：24rpx
- **卡片内边距**：32rpx
- **元素间垂直间距**：16rpx（小）/ 24rpx（中）
- **列表行高**：最小 96rpx（48pt），padding 上下 24rpx

圆角：
- 卡片 / 主按钮：`24rpx`
- 输入框 / 次级按钮 / 信息框：`20rpx`
- 标签 pill / 头像：`999rpx`（pill）或 `24rpx`（方形图标）
- 聊天气泡：`24rpx`，尾巴侧 `8rpx`

阴影：仅保留极弱投影（`0 2rpx 12rpx rgba(0,0,0,0.04)`）用于浮层；卡片**不投影**，靠底色区分。

---

## 5. 组件规范

### 5.1 导航栏（navigationBar）
- `navigationBarBackgroundColor`: `#F2F2F7`（与页面同色，iOS 大标题风格）
- `navigationBarTextStyle`: `black`
- 标题文字黑色、居中
- 各页面 `navigationBarTitleText` 保留原文案。

### 5.2 底部 tabBar
- `backgroundColor`: `#FFFFFF`
- `color`: `#8E8E93`（未选中）
- `selectedColor`: `#007AFF`
- `borderStyle`: `white`（顶部 hairline 用 `#C6C6C8`，由 `borderStyle` 字段控制为 white 以隐藏黑边）
- 图标沿用现有 PNG（保持线性风格即可，不重做）。

### 5.3 卡片 `.card`
- 白底 `#FFFFFF`
- 圆角 24rpx
- 内边距 32rpx
- 左右外边距 24rpx
- 无投影（或极弱）
- 标题用 `.title-2`，正文用 `.body`。

### 5.4 按钮
- **主按钮 `.btn-primary`**：蓝底 `#007AFF`、白字、高度 96rpx、圆角 24rpx、字号 34rpx、字重 600、整宽。按压态 `#0056CC`。
- **次按钮 `.btn-secondary`**：浅蓝底 `#E3F0FF`、蓝字 `#007AFF`、高度 96rpx、圆角 24rpx、无描边（iOS style secondary button）。
- **危险按钮 `.btn-danger`**：红底 `#FF3B30`、白字。
- **禁用 `.disabled`**：灰底 `#E5E5EA`、灰字 `#8E8E93`。

### 5.5 表单
- 外层 `.form-row`：flex 行，padding 上下 20rpx
- 标签 `.form-label`：宽 140rpx、字重 600、颜色 `--label`
- 输入框 / picker `.form-input` `.form-picker`：浅灰底 `#F2F2F7`、圆角 20rpx、内边距 22rpx 24rpx、字号 32rpx、无边框。
- 行与行之间用 hairline `#EFEFF0` 分隔（在同一卡片内分组列表）。

### 5.6 列表 Cell
- 白底、左右内边距 32rpx、上下 24rpx
- 行间分隔线 `#EFEFF0`，从文字起始位置缩进（不顶格）
- 选中行：浅蓝底 `#E3F0FF`、圆角 20rpx。

### 5.7 标签 `.tag`
- pill 形（圆角 999rpx）、字号 26rpx、padding 8rpx 20rpx
- 默认：浅蓝底 `#E3F0FF`、蓝字 `#007AFF`
- `.tag-warn`：浅橙底 `#FFF4E5`、深橙字 `#B25E00`（"需空腹"）
- `.tag-success`：浅绿底 `#E8F8EE`、深绿字 `#248A3D`

### 5.8 分段控件 `.mode-tabs`（iOS UISegmentedControl 风格）
- 外层白底、圆角 16rpx、内边距 4rpx、margin 24rpx
- 每个 tab：padding 20rpx 0、字号 30rpx、颜色 `--label-2`
- 选中 tab：白底 `#FFFFFF`、字重 600、字色 `--label`、带极弱投影 `0 2rpx 8rpx rgba(0,0,0,0.06)`
- 未选中：透明底、灰字。

> 即"分段控件"而非"蓝底白字大按钮"，符合 iOS 风。

### 5.9 聊天气泡
- 用户气泡：蓝底 `#007AFF`、白字、右对齐、圆角 24rpx、右下圆角 8rpx
- AI 气泡：白底 `#FFFFFF`、字色 `--label`、左对齐、圆角 24rpx、左下圆角 8rpx、极弱阴影
- 气泡 max-width 78%、padding 24rpx 28rpx、字号 32rpx、行高 1.65

### 5.10 底部输入栏
- 白底、顶部 hairline `#C6C6C8`、padding 16rpx 24rpx
- 输入框：浅灰底 `#F2F2F7`、圆角 20rpx、padding 20rpx 24rpx
- 发送按钮：蓝底白字、圆角 20rpx、padding 16rpx 32rpx、最小高度 72rpx

### 5.11 首页网格入口
- 去掉"圆形彩色实心图标"，改为 **白色卡片 + 浅 tint 圆角方块图标（64rpx）+ 黑色标题 + 灰色副标题**
- 每行 2 个，卡片间 24rpx 间距
- 卡片白底、圆角 24rpx、无投影（或极弱）。

### 5.12 步骤时间线（journey）
- 当前步骤：蓝色大数字圆（`#007AFF` 底白字）+ 浅蓝行底 `#E3F0FF`
- 已完成步骤：灰色数字圆 `#E5E5EA`、灰字、透明度 0.6
- 待办：浅蓝数字圆 `#D1E4FF`、蓝字
- 步骤间用 hairline 连接。

---

## 6. 适老化可读性硬性要求（验收清单）

- [ ] 任何正文不小于 32rpx；hint 不小于 28rpx。
- [ ] 主文字 `#1C1C1E` 在白底上对比度 ≈ 16:1。
- [ ] 辅助文字 `#6D6D72` 在白底上对比度 ≈ 5.4:1（≥ 4.5:1）。
- [ ] 按钮高度 ≥ 96rpx，列表行高 ≥ 96rpx，tab 点击区 ≥ 88rpx。
- [ ] 不用浅灰文字承载关键信息；"需空腹"等关键提示用橙色标签而非灰字。
- [ ] 行高 ≥ 1.5 倍字号。

---

## 7. 页面级改造要点

| 页面 | 关键改动 |
|---|---|
| index | 去掉蓝色渐变 hero，改为白底大标题（iOS Large Title）；AI 卡片改为浅蓝 tint 圆角条；6 宫格改为 2 列白卡 + 浅 tint 图标方块。 |
| guide | 分段控件改为 UISegmentedControl 风格；卡片左侧蓝条去掉，改为顶部 hairline + 标题；tag 用 pill。 |
| chat | 分段控件风格统一；气泡 iOS 化；底部输入栏 hairline 分隔。 |
| journey | dept-header 去掉顶部蓝条，改为大标题 + 浅蓝信息框；步骤时间线重绘；tip-item 改浅橙底深橙字。 |
| navigate | picker 行改为 iOS 表单行（左标签右值）；floor-tab 改为分段控件风格；路线点用系统红。 |
| register | 表单改为 iOS grouped 列表风格；doctor-row 选中浅蓝底；成功卡顶部绿条去掉，改为绿色 check 语义标签。 |
| my | 就诊人信息卡 + 记录列表 iOS grouped；关于卡灰底。 |
