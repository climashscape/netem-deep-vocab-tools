# 界面与体验规范 (UI/UX Guidelines)

## 1. 核心设计语言 (Core Design Language)

本项目采用 **Neumorphism (新拟态)** 设计风格，旨在打造极简、沉浸式的学习体验。

### 1.1 核心元素
*   **背景色**: `#e0e5ec` (Light Mode) / `#2d2d2d` (Dark Mode)。
*   **光影**: 使用双重投影 (Top-Left Highlight, Bottom-Right Shadow) 营造凸起或凹陷的质感。
*   **圆角**: `rounded-2xl` (16px) 或 `rounded-3xl` (24px)，保持柔和。
*   **字体**: 系统默认无衬线字体 (`system-ui`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`)，字重偏粗 (`font-bold`, `font-black`) 以增强可读性。

---

## 2. 交互规范 (Interaction Guidelines)

### 2.1 触控反馈 (Haptic Feedback)
*   **点击**: 所有可交互元素（按钮、卡片）在点击时应有轻微的缩放动画 (`active:scale-95`) 和触觉反馈（Vibration）。
*   **长按**: 支持长按触发特定功能（如长按单词发音）。

### 2.2 手势操作 (Gestures)
*   **左右滑动 (Swipe)**: 
    *   在单词卡片区域左右滑动切换单词。
    *   左滑 (Next): 显示下一个单词。
    *   右滑 (Prev): 显示上一个单词。
*   **下拉刷新 (Pull-to-Refresh)**: 
    *   在列表顶部下拉刷新数据。
    *   触发同步逻辑。

### 2.3 动效 (Animation)
*   **过渡**: 页面切换使用淡入淡出 (`fade-in`, `fade-out`) 或平滑推入 (`slide-in`).
*   **加载**: 使用骨架屏 (Skeleton Screen) 或微动效 (Spinner) 提示加载状态。
*   **时长**: 动画时长控制在 `200ms` - `300ms` 之间，保持流畅感。

---

## 3. 深色模式 (Dark Mode)

### 3.1 适配原则
*   **自动跟随**: 默认跟随系统设置 (`prefers-color-scheme: dark`)。
*   **手动切换**: 提供设置选项允许用户强制开启/关闭。
*   **对比度**: 确保文字与背景对比度至少达到 `4.5:1` (WCAG AA 标准)。

### 3.2 颜色映射
| 元素 | Light Mode | Dark Mode |
| :--- | :--- | :--- |
| 背景 | `#e0e5ec` | `#1a1a1a` |
| 卡片 | `#e0e5ec` | `#2d2d2d` |
| 文字 (主要) | `#374151` (Gray-700) | `#e5e7eb` (Gray-200) |
| 文字 (次要) | `#6b7280` (Gray-500) | `#9ca3af` (Gray-400) |
| 强调色 | `#3b82f6` (Blue-500) | `#60a5fa` (Blue-400) |

---

## 4. 响应式布局 (Responsive Layout)

### 4.1 移动优先 (Mobile-First)
*   设计基准: 375px (iPhone SE/Mini) 宽度。
*   确保在小屏设备上内容不溢出，按钮易于点击（最小点击区域 44x44px）。

### 4.2 平板/桌面适配
*   **最大宽度**: 使用 `max-w-md` 或 `max-w-lg` 限制内容区域宽度，避免在大屏上内容过于拉伸。
*   **居中**: 在大屏设备上，内容区域水平居中显示。

---

## 5. 组件规范 (Component Specs)

### 5.1 按钮 (Buttons)
*   **主按钮**: 凸起效果，蓝色背景，白色文字，大圆角。
*   **次按钮**: 凸起效果，灰色背景，深灰文字。
*   **图标按钮**: 圆形，居中图标，无文字。

### 5.2 卡片 (Cards)
*   **单词卡**: 包含单词、音标、释义、例句。支持点击翻转或展开。
*   **列表项**: 紧凑布局，左侧图标/状态，右侧操作按钮。

### 5.3 弹窗 (Modals)
*   **遮罩**: 半透明黑色背景 (`bg-black/50`)，模糊效果 (`backdrop-blur-sm`)。
*   **动画**: 从底部弹出 (`slide-up`) 或中心缩放 (`scale-in`)。
*   **关闭**: 点击遮罩区域或右上角关闭按钮。
