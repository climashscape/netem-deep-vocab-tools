# CODEBUDDY.md This file provides guidance to WorkBuddy when working with code in this repository.

## 常用命令

### 开发服务器
```bash
python tools/utils/dev_proxy.py
```
启动带 API 代理的开发服务器，访问 `http://localhost:8000/`。解决本地调用 LLM API 的 CORS 跨域问题。

### Android 构建
```bash
npm install
npx cap sync
npx cap open android
```
同步前端资源到 Android 工程，然后在 Android Studio 中构建 APK。

### 数据维护
```bash
python tools/checkers/check_duplicates.py  # 检查词库重复
python tools/utils/update_full_list_js.py  # 更新前端词库 JS
pip install -r tools/requirements.txt      # 安装 Python 依赖
```

---

## 架构概览

### 核心理念：离线优先 + 纯静态

本项目是**纯静态 Web 应用**，无后端服务器。所有核心功能必须在完全无网络环境下正常工作。

- **数据存储**：IndexedDB (Dexie.js)，所有用户数据在本地
- **词库分发**：`app/static/netem_full_list.json` 随包分发，5530 个考研词汇
- **移动端**：Capacitor 封装为原生 Android 应用

### 三层架构

```
┌─────────────────────────────────────────────────────────┐
│  视图层 (View Layer)                                     │
│  app/index.html                                          │
│  - 禁止直接操作 window.db                                │
│  - 通过 LocalAPI 或 Ebbinghaus 获取数据                  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  控制层 (Controller Layer)                               │
│  app/static/js/*.js                                      │
│  - local_api.js: API 路由分发器，模拟后端 API 响应       │
│  - ebbinghaus.js: 艾宾浩斯记忆算法实现                   │
│  - llm.js: AI 接口封装 (OpenAI/DeepSeek)                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  数据层 (Data Layer)                                     │
│  app/static/js/db.js                                     │
│  - Dexie.js 封装 IndexedDB                              │
│  - Tables: explanations, learning_progress, checkins,   │
│            learn_batch, verbs, extra_vocabulary         │
└─────────────────────────────────────────────────────────┘
```

### 关键数据流

**单词学习流程**：
1. 用户点击 "Know" / "Forget"
2. `submitReview(verb, quality)` 调用 `Ebbinghaus.recordReview()`
3. 计算新的 `next_review_time` 和 `stage`
4. 更新 `db.learning_progress`
5. 触发 UI 更新

**AI 解析流程**：
1. 用户进入 "Analysis" 模式
2. 检查 `db.explanations` 是否有缓存
3. 有缓存 → 直接返回；无缓存 → 调用 `llm.js` → 存入 DB → 返回
4. **Strict Cache Mode**：无 API Key 时自动回退离线词库

### LocalAPI 路由系统

`local_api.js` 是核心路由分发器，拦截 `/api/*` 请求：

| 路由 | 功能 |
|------|------|
| `/api/verbs` | 获取词库列表 |
| `/api/explain` | 获取单词解析（含缓存逻辑） |
| `/api/ebbinghaus/record` | 记录复习结果 |
| `/api/ebbinghaus/due` | 获取待复习单词 |
| `/api/checkins` | 打卡记录 |
| `/api/export` | 导出备份 |
| `/api/import` | 导入备份 |

### 艾宾浩斯记忆算法

`ebbinghaus.js` 实现 9 阶段记忆曲线：

```javascript
const EBBINGHAUS_STAGES = [
    5,      // Stage 1: 5 分钟
    30,     // Stage 2: 30 分钟
    720,    // Stage 3: 12 小时
    1440,   // Stage 4: 1 天
    2880,   // Stage 5: 2 天
    5760,   // Stage 6: 4 天
    10080,  // Stage 7: 7 天
    21600,  // Stage 8: 15 天
    43200   // Stage 9: 30 天
];
```

- 记住 → 阶段 +1
- 忘记 → 重置到 Stage 1
- Stage 9 完成后标记为 `mastered`

### IndexedDB Schema

```javascript
// Version 8: 新增复合索引用于 72x 查询加速
db.version(8).stores({
    learning_progress: 'verb, stage, last_review, next_review, status, [status+next_review]'
});

// Version 7: 原始 schema（保留兼容）
db.version(7).stores({
    explanations: '[mode+query_key], mode, query_key, created_at',
    learning_progress: 'verb, stage, last_review, next_review, status',
    checkins: 'date',
    learn_batch: 'verb',
    verbs: 'word, frequency, pos, original_word',
    extra_vocabulary: 'word, definition, created_at'
});
```

**重要**：
- Dexie 不支持修改主键，如需修改 Schema 必须删除旧表重建
- v8 新增 `[status+next_review]` 复合索引，用于加速待复习单词查询（72x 提升）

---

## 代码风格

### JavaScript (ES6+)
- 缩进：4 空格
- 变量：优先 `const`，其次 `let`，禁止 `var`
- 函数：优先箭头函数 `() => {}`
- 注释：关键逻辑必须注释，函数头使用 JSDoc

### CSS (Tailwind CSS)
- 类名顺序：Layout → Box Model → Typography → Visual → Misc
- 自定义类名：kebab-case (e.g., `.verb-card`)

### Git Commit
遵循 [Conventional Commits](https://www.conventionalcommits.org/)：
```
feat(app): add offline TTS support
fix(db): correct migration logic for v6.6.6
docs(readme): update installation guide
```

---

## 开发注意事项

### 数据更新流程
修改 `tools/data/netem_full_list.json` 后，必须运行：
```bash
python tools/utils/update_full_list_js.py
```
更新 `app/static/js/data_full_list.js`。

### 版本发布
发布新版本时需更新：
1. `VERSION` 文件
2. `package.json` 的 `version` 字段
3. `android/app/build.gradle` 的 `versionName` 和 `versionCode`
4. `README.md` 中的版本号
5. `app/index.html` 中的版本号显示

### 离线测试
在浏览器中模拟断网环境，确保应用依然可用。这是核心验收标准。

### DB 迁移
`db.js` 中的 `initDB()` 包含自动恢复逻辑：
- 检测到 Schema 不兼容时自动删除旧 DB 重建
- 支持 `versionchange` 事件处理多标签页冲突
