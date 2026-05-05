# 考研词汇词频排序数据与深度背单词工具 (NETEM Deep Vocab Tools)

**版本号：v6.6.6 (Static/Offline Edition)**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Web%20%7C%20Android-green.svg)
![Status](https://img.shields.io/badge/status-Stable-success.svg)

## 1. 项目简介 (Introduction)

**NETEM Deep Vocab Tools** 是一个专为考研英语设计的**深度背单词工具**。它基于《全国硕士研究生招生考试英语（一）考试大纲》要求的 5530 个词汇，结合科学的**词频统计**、**艾宾浩斯记忆曲线**和**AI 深度解析**，帮助考生高效攻克考研核心词汇。

本项目目前已发展为**纯静态、离线化**的架构，支持在 Web 端和 Android 端（通过 Capacitor）运行，无需依赖任何后端服务器，数据完全存储在用户本地。

### 核心价值
*   **科学排序**：基于 200+ 套真题统计的词频数据，优先复习高频词。
*   **深度解析**：通过 AI (OpenAI/DeepSeek) 生成动词的深度解析、词源、搭配及视觉助记。
*   **离线优先**：所有学习进度、笔记、设置均存储在本地 (IndexedDB)，随时随地学习。
*   **极简主义**：无广告、无社交干扰，专注于沉浸式学习体验。

---

## 2. 核心功能 (Features)

### 📚 科学词库
*   **词频统计**：集成 5530 个大纲词汇，按真题出现频率排序。
*   **词形还原**：采用 Lemmatization 策略，精准统计词汇频率。
*   **高频筛选**：自动标记高频词（出现 >40 次），重点突破。
*   **智能单词识别**：集成 `compromise.js` NLP 库，词性感知的词根提取，提升单词识别率。
*   **生词本 (Notebook)**：支持收藏词库外单词（OOV），统一管理 Core/Notebook/Excluded 三类词汇。

### 🧠 深度学习模式
*   **4 阶段学习法**：
    1.  **初识 (Preview)**：查看基础释义与词频。
    2.  **解析 (Analysis)**：AI 生成深度解析（词源、语境、助记）。
    3.  **视觉 (Visual)**：AI 生成视觉助记描述（可对接绘图 AI）。
    4.  **复习 (Review)**：基于艾宾浩斯曲线的智能复习安排。
*   **AI 辅助**：
    *   支持自定义 API Key (OpenAI / DeepSeek / Custom)。
    *   **Strict Cache Mode**：无 Key 时自动回退至内置离线词库，不消耗 Token。
*   **音标与发音**：单词详情支持英式/美式音标显示与发音，点击标题即可播放。
*   **每日目标**：设置每日学习目标（新词数量），追踪学习进度。
*   **签到系统**：显示总签到天数和连续签到天数，激励持续学习。

### 💾 离线架构
*   **本地存储**：使用 IndexedDB (Dexie.js) 存储所有数据，容量大、速度快。
*   **数据导出/导入**：支持 JSON/ZIP 格式备份学习进度，跨设备同步。
*   **自动备份**：支持多种备份频率选择（每日/每周/每月），自动保存学习数据。
*   **PWA 支持**：可作为渐进式 Web 应用安装到桌面或手机。

### 📱 移动端体验
*   **手势操作**：支持左右滑动切换单词、边缘右滑返回、长按删除确认。
*   **沉浸式 UI**：Neumorphism（新拟态）设计风格，适配移动端触控。
*   **触摸优化**：使用 `dvh` 单位替代 `vh`，解决移动端视口高度问题；优化卡片拖拽与滚动冲突。
*   **Android APK**：提供原生 Android 安装包，性能更佳。

---

## 3. 快速开始 (Getting Started)

### 方式一：Web 预览 (推荐)
本项目是纯静态网站，您可以直接在浏览器中运行。

1.  **克隆项目**：
    ```bash
    git clone https://github.com/your-repo/netem-deep-vocab-tools.git
    cd netem-deep-vocab-tools
    ```
2.  **启动本地服务器**：
    *   如果您安装了 Python：
        ```bash
        python tools/utils/dev_proxy.py
        ```
        访问 `http://localhost:8000/` 即可。
        *(注：`dev_proxy.py` 是一个带代理功能的开发服务器，可解决本地调用 AI API 的跨域问题)*
    *   或者使用 VS Code 的 **Live Server** 插件打开 `app/index.html`。

### 方式二：Android 安装
您可以自己构建 APK，或者下载 Release 页面的预编译版本（如果有）。

1.  **环境准备**：
    *   Node.js (v18+)
    *   Android Studio (及 SDK)
    *   Java JDK 17+

2.  **构建步骤**：
    ```bash
    # 1. 安装依赖
    npm install

    # 2. 同步前端资源到 Android 工程
    npx cap sync

    # 3. 打开 Android Studio 构建
    npx cap open android
    ```
    在 Android Studio 中点击 `Build > Build APK` 即可。

---

## 4. 开发指南 (Development Guide)

### 📂 项目结构
```text
.
├── app/                 # [核心] Web 应用源码 (HTML/JS/CSS/Static)
│   ├── static/          # 静态资源
│   │   ├── js/          # 核心逻辑 (ebbinghaus.js, db.js, local_api.js 等)
│   │   ├── lib/         # 第三方库 (Tailwind, FontAwesome, Dexie)
│   │   └── netem_full_list.json # 核心词库
│   └── index.html       # 应用入口
├── android/             # Android 原生工程 (Capacitor 托管)
├── tools/               # 开发与维护脚本 (Python/Node.js)
│   ├── checkers/        # 数据检查工具
│   ├── utils/           # 实用工具 (dev_proxy, converters)
│   └── data/            # 原始数据源
├── docs/                # 项目文档
│   ├── guidelines/      # 开发规范 (架构、发布、UI/UX、单词识别等)
│   └── ROADMAP.md       # 长期规划
├── DESIGN.md            # 设计系统文档 (视觉主题、组件、交互模式)
├── package.json         # 项目依赖配置
└── capacitor.config.json # Capacitor 配置文件
```

### 📚 文档资源
详细的开发文档请参考 `docs/` 目录：
*   [**架构白皮书**](docs/guidelines/ARCHITECTURE.md): 了解离线优先架构设计。
*   [**开发与贡献指南**](docs/guidelines/CONTRIBUTING_GUIDE.md): 代码风格与 Git 规范。
*   [**发布流程**](docs/guidelines/RELEASE_WORKFLOW.md): 版本管理与 APK 构建流程。
*   [**UI/UX 规范**](docs/guidelines/UI_UX_GUIDELINES.md): 新拟态设计风格指南。
*   [**单词识别机制**](docs/guidelines/WORD_RECOGNITION.md): NLP 词形还原与生词本设计。
*   [**项目路线图**](docs/ROADMAP.md): 未来功能规划。

**设计系统**：项目包含完整的设计规范文档 [DESIGN.md](DESIGN.md)，涵盖产品设计意图、信息架构、视觉主题、组件系统、交互模式等内容。

### 🔧 常用工具 (Tools)
所有维护脚本均位于 `tools/` 目录下：

*   **启动开发服务器** (带 API 代理)：
    ```bash
    python tools/utils/dev_proxy.py
    ```
*   **检查数据重复**：
    ```bash
    python tools/checkers/check_duplicates.py
    ```
*   **更新前端词库 JS**：
    ```bash
    python tools/utils/update_full_list_js.py
    ```
    *(当您修改了 `tools/data/` 下的原始数据后，需运行此脚本更新 `app/` 中的 JS 文件)*

### ⚙️ 配置说明
应用内的设置（如 API Key）均存储在浏览器的 `localStorage` 中。
*   **API Key**：在应用设置页面输入。
*   **自定义模型**：支持在设置中配置 `Base URL` 和 `Model Name` (如 DeepSeek, Moonshot 等)。

---

## 5. 常见问题 (FAQ)

**Q: 为什么 AI 解析无法使用？**
A: 请检查：
1. 是否在设置中填写了正确的 API Key。
2. 网络环境是否可以访问 OpenAI/DeepSeek API。
3. 如果在浏览器本地开发，请使用 `python tools/utils/dev_proxy.py` 启动，以避免 CORS 跨域问题。

**Q: 数据会丢失吗？**
A: 数据存储在浏览器的 IndexedDB 中。
*   **安全**：刷新页面不会丢失。
*   **风险**：清除浏览器缓存或卸载 APP 会导致数据丢失。
*   **建议**：定期使用“导出备份”功能下载 JSON/ZIP 备份文件。

**Q: 如何更新词库？**
A: 修改 `tools/data/netem_full_list.json`，然后运行 `python tools/utils/update_full_list_js.py`，最后重新部署或构建 APK。

---

## 6. 鸣谢 (Acknowledgements)

感谢以下项目及个人为本项目提供的数据支持与灵感：

*   **[exam-data/NETEMVocabulary](https://github.com/exam-data/NETEMVocabulary/)**：本项目原始词频数据的主要来源。
*   **[awxiaoxian2020/spelling-variations](https://github.com/awxiaoxian2020/spelling-variations/)**：提供了考纲词汇的拼写变体数据支持。
*   所有为本项目提供反馈和建议的用户。

## 7. 许可证 (License)

*   **数据**：基于 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 共享。
*   **代码**：基于 [MIT License](LICENSE-CODE)。

---
*Generated by Trae AI based on v6.6.6 architecture.*
