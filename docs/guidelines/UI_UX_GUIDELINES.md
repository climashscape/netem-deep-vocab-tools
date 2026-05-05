# 界面与体验规范 (UI/UX Guidelines)

## 1. 核心设计语言 (Core Design Language)

本项目遵循 **Apple Human Interface Guidelines (HIG)** 设计规范，打造原生、清晰、易用的学习体验。

### 1.1 核心元素

*   **配色**：iOS 系统颜色（Light: `#F2F2F7` 背景 / Dark: `#000000` 背景）
*   **阴影**：轻量阴影 (`0 1px 3px rgba(0,0,0,0.08)`)，层次清晰不抢眼
*   **圆角**：`12px` (卡片) / `10px` (按钮)，保持一致性
*   **字体**：系统字体 (`-apple-system`, `SF Pro Display`, `Helvetica Neue`)，字重 500-600

### 1.2 设计原则

1. **清晰**：文字清晰可读，图标精确，装饰适度
2. **依从**：UI 不抢眼，让内容成为焦点
3. **深度**：视觉层次分明，交互逻辑清晰

---

## 2. 交互规范 (Interaction Guidelines)

### 2.1 触控反馈 (Haptic Feedback)

*   **点击**：所有可交互元素点击时有轻微缩放或透明度变化 (`opacity: 0.7`)
*   **长按**：支持长按触发特定功能（如长按预览单词拼写）
*   **触觉反馈**：关键操作（如标记已掌握）可触发轻微震动

### 2.2 手势操作 (Gestures)

*   **左右滑动 (Swipe)**：
    *   在单词卡片区域左右滑动切换单词
    *   左滑 (Next)：显示下一个单词
    *   右滑 (Prev)：显示上一个单词
*   **边缘滑动返回**：
    *   屏幕右边缘左滑返回上一页（Android 风格，非 iOS 下拉）
    *   手势区域：距边缘 20px 内
*   **下拉刷新 (Pull-to-Refresh)**：
    *   在列表顶部下拉刷新数据
    *   触发同步逻辑

### 2.3 动效 (Animation)

*   **过渡**：页面切换使用淡入淡出或平滑推入
*   **加载**：使用骨架屏 (Skeleton Screen) 或系统 Spinner
*   **时长**：动画时长控制在 `150ms` - `300ms`，保持流畅
*   **双缓冲渲染**：卡片切换时先在隐藏容器构建，再原子替换，消除闪烁

---

## 3. 深色模式 (Dark Mode)

### 3.1 适配原则

*   **自动跟随**：默认跟随系统设置 (`prefers-color-scheme: dark`)
*   **手动切换**：提供设置选项允许用户强制开启/关闭
*   **对比度**：确保文字与背景对比度至少达到 `4.5:1` (WCAG AA 标准)

### 3.2 颜色映射 (CSS 变量)

| 元素 | Light Mode | Dark Mode |
| :--- | :--- | :--- |
| 背景 (主) | `#F2F2F7` | `#000000` |
| 背景 (次) | `#FFFFFF` | `#1C1C1E` |
| 背景 (三) | `#F2F2F7` | `#2C2C2E` |
| 文字 (主) | `#1C1C1E` | `#FFFFFF` |
| 文字 (次) | `#3A3A3C` | `#EBEBF5` |
| 文字 (三) | `#8E8E93` | `#8E8E93` |
| 强调色 | `#007AFF` | `#0A84FF` |
| 分隔线 | `rgba(60,60,67,0.12)` | `rgba(84,84,88,0.36)` |

### 3.3 CSS 变量实现

```css
:root {
    --bg-primary: #F2F2F7;
    --text-primary: #1C1C1E;
    --ios-blue: #007AFF;
}

@media (prefers-color-scheme: dark) {
    html:not(.light) {
        --bg-primary: #000000;
        --text-primary: #FFFFFF;
        --ios-blue: #0A84FF;
    }
}
```

---

## 4. 响应式布局 (Responsive Layout)

### 4.1 移动优先 (Mobile-First)

*   **设计基准**：375px (iPhone SE/Mini) 宽度
*   **安全区域**：适配 `env(safe-area-inset-*)` 确保刘海屏/底部指示器不遮挡内容
*   **点击区域**：最小 44×44pt (Apple HIG 标准)

### 4.2 平板/桌面适配

*   **最大宽度**：使用 `max-w-md` 或 `max-w-lg` 限制内容区域宽度
*   **居中**：大屏设备上内容区域水平居中

### 4.3 视口单位

*   使用 `dvh` 替代 `vh`，解决移动端地址栏收起/展开导致的视口高度变化问题

---

## 5. 组件规范 (Component Specs)

### 5.1 按钮 (Buttons)

*   **主按钮**：iOS Blue 背景，白色文字，圆角 12px
*   **次按钮**：`fill-secondary` 背景，圆角 10px
*   **图标按钮**：圆形或方形，居中图标
*   **按下状态**：`opacity: 0.7`，无阴影变化

### 5.2 卡片 (Cards)

*   **单词卡**：包含单词、音标、释义、例句
*   **样式**：`background: var(--bg-secondary)`，轻量阴影，0.5px 分隔线边框
*   **交互**：点击展开详情，支持滑动手势

### 5.3 弹窗 (Modals)

*   **遮罩**：半透明黑色背景，模糊效果
*   **动画**：从底部弹出 (iOS Sheet 风格)
*   **关闭**：仅通过按钮或特定手势关闭，点击空白区域不关闭（防止误操作）
*   **z-index**：确认弹窗 `99999`，普通弹窗 `1000`

### 5.4 Tab Bar

*   **样式**：毛玻璃背景 (`backdrop-blur`)，圆角图标
*   **激活态**：iOS Blue，非激活态：Gray
*   **安全区域**：底部适配 `safe-area-inset-bottom`

---

## 6. 可访问性 (Accessibility)

*   **对比度**：所有文字与背景对比度 ≥ 4.5:1
*   **字体大小**：正文 ≥ 16px，标题 ≥ 20px
*   **触控目标**：最小 44×44pt
*   **色彩盲友好**：不仅依赖颜色传达信息，辅以图标/文字

---

## 7. 参考资源

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [iOS Design Resources](https://developer.apple.com/design/resources/)
- [DESIGN.md](../../DESIGN.md) - 项目设计系统文档
