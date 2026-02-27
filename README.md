# 考研词汇词频排序数据与深度背单词工具 (NETEM Deep Vocab Tools)

**版本号：v2.0.0 (Stable)**

## 项目状态 (Project Status)
- ✅ **核心词汇数据**：已集成 5530 个考研大纲词汇及详尽词频统计。
- ✅ **离线化架构**：已完成从 Python 后端向纯前端 (IndexedDB + Dexie.js) 的迁移，支持 100% 离线运行。
- ✅ **多端支持**：支持 Web 端、移动端 (PWA/APK) 交互。
- ✅ **AI 深度解析**：支持通过 LLM 进行动词深度解析及视觉助记生成。
- ✅ **严格缓存模式**：新增 Strict Cache Mode，无 API Key 时自动回退至离线词库，避免无效调用。
- ✅ **智能数据同步**：支持从后端获取最新缓存数据，并自动导入遗留数据 (Legacy Import)。

本项目是一个专为考研英语设计的**深度背单词工具**。它不仅提供《全国硕士研究生招生考试英语（一）考试大纲》5530 个词汇的科学词频排序数据，还配套了基于 AI 的动词深度解析、视觉助记及多端交互工具，旨在帮助考生通过科学的统计规律和 AI 辅助记忆，高效攻克考研核心词汇。

## 版本更新 (v2.0.0 Changelog)
这是第一版开始正式发布的编译后的app。

- **Fix**: 改进移动端输入框的触摸事件处理，防止父元素阻止原生聚焦和文本选择
- **Refactor**: 重构卡片滑动逻辑，使用更精确的触摸跟踪和边界检测
- **Fix**: 修复设置页面中导入/导出模态框的层级问题
- **Feat**: 优化分析模式设置的同步逻辑，确保本地和服务器设置一致性
- **Feat**: 增强学习模式中的自动跳转功能，提升用户体验

## 版本更新 (v1.1.1 Changelog)
- **Fix**: 修复 Android 物理返回键逻辑，现在可以正确关闭各类弹窗 (详情页/设置/排除列表等) 而非直接退出应用。
- **Fix**: 优化数据导入导出功能，支持 `.json` 格式的本地备份与恢复，解决跨平台兼容性问题。
- **Fix**: 调整 UI 顶部状态栏间距，适配沉浸式状态栏设计。
- **Feat**: 改进离线缓存和数据库同步机制，支持从后端获取缓存数据。
- **Feat**: 优化离线模式下的缓存回退逻辑，依次尝试 IndexedDB、后端 API 和本地 JSON。
- **Feat**: 添加严格缓存模式 (Strict Cache Mode)，避免在没有 API 密钥时生成 AI 内容。
- **Feat**: 改进数据库初始化，自动导入遗留数据并处理大小写重复问题。
- **Feat**: 增强数据导出功能，过滤遗留数据以减少文件大小。
- **Feat**: 添加动词排除功能，支持用户自定义学习列表。
- **Fix**: 修复 Service Worker 缓存版本和 Android 构建配置。

## 核心数据 (Core Data)

### 词频排序
*   **数据源**：基于 [exam-data/NETEMVocabulary](https://github.com/exam-data/NETEMVocabulary/)，核心数据源于《2024年全国硕士研究生招生考试英语（一）考试大纲词汇表》要求的 5530 个词汇。
*   **统计范围**：分析了约 200 套试卷（包括四六级、考研英语一/二、专四专八等）。
*   **处理策略**：采用词形还原（Lemmatization）策略，确保词频统计的准确性。
*   **高频词汇**：前 **2444** 个单词出现 **40** 次以上（平均每 5 套试卷出现一次），定义为高频词汇。

### 数据格式
*   **JSON**: [netem_full_list.json](netem_full_list.json) - 包含序号、词频、单词、释义、POS 等完整信息。
*   **SQL**: [netem_full_list.sql](netem_full_list.sql) - 方便导入各种数据库。
*   **SQLite**: `vocabulary.db` - 项目内置的轻量级数据库。

## 工具体系 (Tools Ecosystem)

项目在 `scripts/` 目录下提供了一套完整的词汇处理工具：

### 1. 动词深度解析系统 (explain_verbs)
这是一个功能强大的动词学习与管理系统：
*   **AI 智能解析**：集成 OpenAI 兼容接口，自动生成词汇深度解析、例句和助记。
*   **Web 界面 (FastAPI)**：提供可视化的词汇管理后台。
*   **本地 GUI (Gradio)**：精美的复古自然主义风格界面，支持单词解析、批量解析和对比分析。
*   **图像生成**：集成 Pollinations/Dicebear，为单词生成视觉辅助。

### 2. 拼写变体处理 (spelling-variations)
*   处理考纲中具有多种拼写形式的单词（如 color/colour），确保数据的统一性。

### 3. 文档生成 (generate-doc)
*   支持从 SQL 数据库自动生成格式化的 Markdown/JSONL 文档。

### 4. 释义格式化 (update_def)
*   统一和标准化词汇释义的显示格式，减轻记忆负担。

## 快速开始

### 获取数据
1. 直接下载根目录下的 `netem_full_list.json` 或 `netem_full_list.sql` 即可使用。
2. 也可以去 [Release 页面](https://github.com/exam-data/NETEM-Deep-Vocab-Tools/releases) 下载 PDF 版本。

### 1. 运行后端解析工具 (Backend/GUI Mode)
1.  **安装依赖**：
    *   在项目根目录下运行：`pip install -r requirements.txt`。
2.  **配置 AI 密钥**：
    *   进入 `scripts/explain_verbs/` 目录。
    *   配置 `config.json` 或 `.env` 文件，填入你的 `OPENAI_API_KEY`。
3.  **启动工具**：
    *   运行 Web 版 (FastAPI)：`python app.py`。
    *   运行 GUI 版 (Gradio)：`python gui.py`。

### 2. 运行离线版/移动端 (Offline/Mobile)
*   **Web 预览**：在根目录下直接通过静态服务器（如 `Live Server` 或 `python -m http.server`）打开 `dist/index.html`。
*   **Android 构建**：
    1.  安装依赖：`npm install`
    2.  同步资源：`npx cap sync`
    3.  通过 Android Studio 构建：打开 `android/` 目录并生成 APK。
    *   *详细步骤请参考 [OFFLINE_APK_PLAN.md](OFFLINE_APK_PLAN.md)*。

## 项目结构 (Project Structure)

```text
.
├── android/             # Android 原生工程 (Capacitor 托管)
├── dist/                # 纯前端静态资源 (离线版/PWA/APK 核心)
│   ├── static/          # JS、CSS 及离线词库数据
│   └── index.html       # 离线版入口
├── scripts/
│   ├── explain_verbs/   # 动词 AI 解析系统 (FastAPI + Gradio)
│   │   ├── static/      # 前端本地化逻辑 (local_api.js, db.js)
│   │   ├── templates/   # 网页模板
│   │   └── app.py       # FastAPI 后端入口
│   ├── spelling-variations/ # 拼写变体处理逻辑 (Node.js)
│   ├── generate-doc/    # 文档生成工具
│   ├── generate_json/   # SQL 转 JSON 工具
│   └── update_def/      # 释义格式化工具
├── netem_full_list.json # 核心词频 JSON 数据
├── netem_full_list.sql  # 核心词频 SQL 数据
├── requirements.txt     # Python 依赖管理
├── package.json         # 前端及 Capacitor 依赖管理
├── capacitor.config.json # Capacitor 配置文件
└── vocabulary.db        # 项目数据库 (SQLite)
```

## 鸣谢 (Acknowledgements)

感谢以下项目及个人为本项目提供的数据支持与灵感：

*   **[exam-data/NETEM-Deep-Vocab-Tools](https://github.com/exam-data/NETEMVocabulary/)**：本项目原始词频数据的主要来源。
*   **[awxiaoxian2020/spelling-variations](https://github.com/awxiaoxian2020/spelling-variations/)**：提供了考纲词汇的拼写变体数据支持。
*   所有为本项目提供反馈和建议的用户。

## 许可证

*   **数据**：基于 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 共享。
*   **代码**：基于 [MIT License](LICENSE-CODE)。

---
*如果想自行生成文档，请参阅[相关说明](https://github.com/exam-data/scripts-docs/blob/main/docs/how-to-generate-docs.md)。*
