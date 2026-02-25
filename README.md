# 考研词汇词频排序数据与深度背单词工具 (NETEM Deep Vocab Tools)

**版本号：v0.x (Pre-release)**

本项目是一个专为考研英语设计的**深度背单词工具**。它不仅提供《全国硕士研究生招生考试英语（一）考试大纲》5530 个词汇的科学词频排序数据，还配套了基于 AI 的动词深度解析、视觉助记及多端交互工具，旨在帮助考生通过科学的统计规律和 AI 辅助记忆，高效攻克考研核心词汇。

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

### 运行 AI 解析工具

1.  **安装依赖**：
    *   在项目根目录下运行：`pip install -r requirements.txt`。
2.  **配置 AI 密钥**：
    *   进入 `scripts/explain_verbs/` 目录。
    *   配置 `config.json` 或 `.env` 文件，填入你的 `OPENAI_API_KEY`。
3.  **启动工具**：
    *   运行 Web 版：`python app.py`。
    *   运行 GUI 版：`python gui.py`。

## 项目结构

```text
.
├── scripts/
│   ├── explain_verbs/       # 动词 AI 解析系统 (FastAPI + Gradio)
│   ├── spelling-variations/  # 拼写变体处理逻辑 (Node.js)
│   ├── generate-doc/        # 文档生成工具
│   ├── generate_json/       # SQL 转 JSON 工具
│   └── update_def/          # 释义格式化工具
├── netem_full_list.json     # 核心词频 JSON 数据
├── netem_full_list.sql      # 核心词频 SQL 数据
├── requirements.txt         # 统一 Python 依赖管理
└── vocabulary.db            # 项目数据库
```

## 鸣谢 (Acknowledgements)

感谢以下项目及个人为本项目提供的数据支持与灵感：

*   **[exam-data/NETEM-Deep-Vocab-Tools](https://github.com/exam-data/NETEMVocabulary/)**：本项目原始词频数据及 PDF 版本的主要来源。
*   **[awxiaoxian2020/spelling-variations](https://github.com/awxiaoxian2020/spelling-variations/)**：提供了考纲词汇的拼写变体数据支持。
*   所有为本项目提供反馈和建议的用户。

## 许可证

*   **数据**：基于 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 共享。
*   **代码**：基于 [MIT License](LICENSE-CODE)。

---
*如果想自行生成文档，请参阅[相关说明](https://github.com/exam-data/scripts-docs/blob/main/docs/how-to-generate-docs.md)。*
