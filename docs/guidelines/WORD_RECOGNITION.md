# 单词识别与关联方案手册 (Word Recognition & Linking Scheme)

## 1. 概述 (Overview)

NETEM Deep Vocab Tools 的单词详细解析页面具备**自动识别文本中的英语单词并建立跳转链接**的功能。
该功能旨在帮助用户在阅读解析（如例句、词源分析）时，能够快速点击并跳转到相关单词的详细页面，形成知识网络。

本文档详细描述了当前的单词识别算法、词根提取规则及候选词排序逻辑。

---

## 2. 核心流程 (Core Workflow)

识别流程主要由 `app/index.html` 中的 `getCanonicalLink(word)` 函数驱动。
当渲染 AI 生成的 Markdown 解析内容时，系统会遍历所有文本节点，对每个单词执行以下步骤：

1.  **精确匹配 (Exact Match)**: 检查单词本身是否存在于词库中。
2.  **不规则动词还原 (Irregular Verbs)**: 检查是否为常见不规则动词的变位形式。
3.  **后缀词根提取 (Suffix Stemming)**: 基于启发式规则去除常见后缀，提取词根。
4.  **前缀词根提取 (Prefix Stemming)**: 尝试去除常见前缀，提取词根。
5.  **多级/递归提取 (Recursive Stemming)**: 结合前缀和后缀规则，处理复杂派生词。
6.  **候选词排序 (Ranking)**: 对所有找到的候选词进行排序，供用户选择。

---

## 3. 详细规则 (Detailed Rules)

### 3.1 精确匹配
*   **逻辑**: 直接将当前单词转为小写 (`lower`)，查询 `vocabularyMap`。
*   **示例**: `apple` -> 匹配 `apple`。

### 3.2 不规则动词还原
系统内置了一份常见不规则动词映射表，支持 50+ 组高频动词。
*   **逻辑**: 如果单词在映射表中，添加其原形。
*   **示例**:
    *   `went` -> `go`
    *   `seen` -> `see`
    *   `bought` -> `buy`
    *   `taken` -> `take`

### 3.3 后缀词根提取 (Suffix Stemming)
系统遍历预定义的后缀列表，尝试剥离后缀并还原词根。

#### 支持的后缀列表 (Suffix List)
```javascript
[
    's', 'es', 'ed', 'ing', 'ly', 'ment', 'ion', 'ions', 'ive', 'al', 'ic', 'ness', 
    'able', 'ible', 'ity', 'ous', 'ful', 'less', 'ship', 'er', 'or', 'ist', 'ize', 
    'ise', 'en', 'ify', 'th', 'ier', 'iest', 'ied', 'ies',
    // 扩展后缀 (v6.6.6+)
    'ation', 'cation', 'ition', 'tic', 'ical', 'ance', 'ence', 'ant', 'ent', 'ary', 'ory'
]
```

#### 还原规则 (Transformation Rules)
1.  **直接剥离**: `root = word - suffix`
    *   *条件*: `root` 必须在词库中。
    *   *示例*: `teacher` -> `teach`
2.  **E-还原 (e-deletion)**: `root = (word - suffix) + 'e'`
    *   *适用后缀*: `ing`, `ed`, `er`, `able`, `ive`, `ize`, `ion`, `ation`, `ition`
    *   *示例*: 
        *   `diving` -> `dive`
        *   `creation` -> `create`
        *   `definition` -> `define`
3.  **Y-to-I 还原**: `root = (word - suffix - 'i') + 'y'`
    *   *适用后缀*: `ed`, `ly`, `ies`, 'ied', `ier`, `iest`, `iness`, `cation`, `ication`
    *   *示例*:
        *   `happily` -> `happy`
        *   `application` -> `apply`
        *   `classification` -> `classify`
4.  **双写辅音还原 (Double Consonant)**: `root = word - suffix - last_char`
    *   *适用后缀*: `ing`, `ed`, `er`, `est`
    *   *条件*: 词根末尾两个字符相同。
    *   *示例*: `running` -> `run`

### 3.4 前缀词根提取 (Prefix Stemming)
系统尝试剥离常见前缀，寻找核心词根。

#### 支持的前缀列表 (Prefix List)
```javascript
['at', 'con', 'dis', 'ex', 'in', 're', 'sub', 'trans', 'pro', 'de', 'pre', 'per', 'ad', 'ab', 'com', 'inter', 'intra', 'extra']
```

*   **逻辑**: `root = word - prefix`
*   **示例**: 
    *   `attract` -> `tract`
    *   `distract` -> `tract`

### 3.5 多级/递归提取 (Recursive Stemming)
为了处理如 `distracting` 这样的复杂单词，系统采用多级策略：
1.  **前缀 -> 后缀**: 先去前缀 (`distracting` -> `tracting`)，再去后缀 (`tracting` -> `tract`)。
2.  **后缀 -> 前缀**: 先去后缀 (`distracting` -> `distract`)，再去前缀 (`distract` -> `tract`)。

这确保了无论是 `presentation` (present + ation) 还是 `unhappiness` (un + happy + ness) 都能尽可能找到核心词根。

---

## 4. 候选词排序 (Ranking Strategy)

当一个单词匹配到多个候选词时（例如 `running` 可能匹配 `run` 和 `running`），系统按以下优先级排序：

1.  **完全匹配优先**: 如果候选词与原词完全一致，排在第一位。
2.  **长度降序**: 较长的词通常更具体（Specific），排在前面。
    *   例如 `presentation`: `presentation` (原词) > `present` (词根)。
3.  **长度升序**: 较短的词排在最后。

**UI 表现**: 
*   点击单词时，如果只有一个候选词，直接跳转。
*   如果有多个候选词，弹出 "Jump to..." 菜单供用户选择。

---

## 5. 交互设计 (Interaction Design)

*   **样式**: 
    *   默认: 无特殊颜色，仅鼠标悬停时显示下划线和淡蓝色背景。
    *   目的: 减少阅读干扰，保持沉浸感。
*   **弹窗 (Popup)**:
    *   触发: 点击多义词/派生词。
    *   行为: 
        *   显示所有候选词及其简要释义。
        *   支持点击跳转。
        *   支持点击外部区域关闭。
        *   **移动端优化**: 拦截系统返回键/侧滑手势，优先关闭弹窗而非退出页面。

---

## 6. 未来改进方向 (Future Improvements)

*   [x] **词形还原库 (Lemmatizer)**: 引入更专业的 NLP 库（`compromise.js`）以处理更复杂的变形。
    *   **实现**: 已集成 `compromise.js` (v14)，采用分级策略增强识别率：
        1.  **通用词根**: 使用 `doc.compute('root')` 获取基础词根。
        2.  **动词特定优化**: 检测到动词时，强制提取不定式 (Infinitive)。
        3.  **名词特定优化**: 检测到名词时，强制提取单数形式 (Singular)。
        4.  **形容词/副词优化**: 深入 JSON 结构提取词根（解决 `happily` -> `happy`, `harder` -> `hard` 等问题）。
    *   **保留机制**: 原有的后缀/前缀规则作为兜底策略继续运行。
*   [ ] **上下文感知**: 根据上下文判断词性，减少无关候选词。
*   [ ] **词组识别 (Phrasal Verbs)**: 
    *   **目标**: 识别句子中的固定搭配（如 `look forward to`），避免单独处理 `look`, `forward`, `to`。
    *   **技术方案**:
        *   建立高频词组库（Trie 树结构优化查询）。
        *   利用 NLP 库的 N-gram 功能进行滑动窗口检测。
        *   识别到词组时，将整个短语作为一个交互单元，链接到该短语的释义页。
*   [ ] **词库外单词学习 (Out-of-Vocabulary Learning)**: 
    *   **目标**: 允许用户点击并学习未包含在核心词库（5530词）中的单词，实现无限扩展。
    *   **机制设计**: 
        *   **独立存储**: 使用 `IndexedDB` 建立 `extra-vocabulary` 表，与核心 `vocabulary` 表隔离。
        *   **即时查询**: 点击生词时，调用第三方 API (如 Free Dictionary API) 获取释义并缓存。
        *   **统一交互**: 与**单词识别弹窗**合并。
            *   若单词存在于核心词库：弹窗显示核心词条候选（优先）。
            *   若单词为生词（OOV）：弹窗显示在线查询结果，并提供“收藏”按钮。
        *   **轻量收藏**: 仅支持添加到生词本进行查阅，不追踪记忆曲线（无 SM-2 进度）。
    *   **兼容性与入口**: 
        *   **UI 集成**: 将生词本集成到 **Mastery 页面**。
        *   **交互设计**: 类比 Review 页面的 Library/Session 切换，Mastery 页面顶部增加 Tab 切换：
            *   **Core (核心)**: 展示已掌握的考纲词汇（现有功能）。
            *   **Notebook (生词本)**: 展示收集的 OOV 单词。
        *   **视觉区分**: 生词本中的单词卡片使用不同色系（如紫色主题），以示区分。
        *   **数据导出**: 支持将生词本独立导出为 Anki 卡片。
