# 数据管理规范 (Data Management Guidelines)

## 1. 核心词库管理 (Vocabulary Management)

### 1.1 数据源 (Source of Truth)
*   **唯一源**: `tools/data/netem_full_list.json`
*   **格式**: JSON Array
    *   **Fields**:
        *   `单词` (String, Unique): 单词拼写。
        *   `词频` (Number): 出现次数。
        *   `序号` (Number): 排序索引。
        *   `释义` (String): 基础释义。
        *   `pos` (String): 词性。

### 1.2 更新流程 (Update Workflow)
1.  **编辑**: 手动修改 `tools/data/netem_full_list.json`。
2.  **验证**: 运行 `python tools/checkers/check_duplicates.py` 确保无重复。
3.  **同步**: 运行 `python tools/utils/update_full_list_js.py` 生成 `app/static/js/data_full_list.js`。
4.  **提交**: `git commit -m "feat(data): update vocabulary list"`。

---

## 2. 数据库架构 (Database Schema)

### 2.1 技术选型
*   **IndexedDB**: 原生浏览器数据库。
*   **Dexie.js**: ORM 封装。

### 2.2 Schema 定义 (`app/static/js/db.js`)
*   **Version 1**:
    *   `learning_progress`: `&verb, stage, next_review, last_review, status`
    *   `explanations`: `&query_key, content, image_url`
    *   `checkins`: `&date, count`

### 2.3 迁移策略 (Migration Strategy)
*   **原则**: 向下兼容，绝不破坏现有用户数据。
*   **实现**: 在 `db.version(x).stores({...})` 中定义新 Schema。Dexie 会自动处理数据迁移。
*   **测试**: 在发布新版本前，必须使用包含旧数据的浏览器环境进行测试，确保升级后数据完整。

---

## 3. 用户数据备份 (User Data Backup)

### 3.1 导出 (Export)
*   **格式**: JSON 或 ZIP (如果包含图片)。
*   **内容**:
    *   `learning_progress`: 所有学习记录。
    *   `settings`: 用户偏好设置。
    *   `explanations`: 本地缓存的 AI 解析。
    *   `checkins`: 打卡记录。
*   **文件名**: `netem_backup_YYYY-MM-DD.json`。

### 3.2 导入 (Import)
*   **逻辑**:
    1.  读取备份文件。
    2.  校验数据格式。
    3.  **合并策略 (Merge Strategy)**:
        *   对于 `learning_progress`: 优先保留 `stage` 更高或 `next_review` 更晚的记录。
        *   对于 `explanations`: 优先保留有内容的记录。
        *   对于 `settings`: 覆盖当前设置（需用户确认）。

---

## 4. 缓存管理 (Cache Management)

### 4.1 AI 解析缓存
*   **存储**: `explanations` 表。
*   **Key**: `query_key` (通常是单词的小写形式)。
*   **过期策略**: 目前无自动过期，用户可手动清除。

### 4.2 图片缓存
*   **策略**: 优先使用 Base64 编码的小图，或稳定的 CDN 链接。
*   **离线**: 对于关键图标，直接打包进 APK (`assets/` 目录)。
