# 项目架构白皮书 (Architecture Guidelines)

## 1. 核心理念 (Core Principles)

### 1.1 离线优先 (Offline-First)
*   **原则**: 应用的所有核心功能（包括背单词、复习、查看解析）必须在**完全无网络**的情况下正常工作。
*   **实现**: 核心词库 (`netem_full_list.json`) 随包分发，用户学习进度存储于 IndexedDB，图片资源（尽可能）离线化或提供占位符。

### 1.2 纯静态化 (Pure Static)
*   **原则**: 不依赖任何运行时后端（如 Python/Node.js Server）。所有逻辑必须在客户端浏览器中执行。
*   **实现**: 
    *   **Backend-Free**: 移除所有服务器端渲染 (SSR)。
    *   **API Simulation**: `local_api.js` 负责拦截并模拟传统后端 API 的响应，直接操作 IndexedDB。

### 1.3 隐私至上 (Privacy-First)
*   **原则**: 用户数据属于用户。
*   **实现**: 所有学习记录、设置、API Key 仅存储在用户设备的浏览器存储中，绝不上传至任何中心服务器（除非用户主动导出备份）。

---

## 2. 技术栈 (Tech Stack)

### 2.1 前端核心 (Frontend Core)
*   **HTML5**: 语义化标签结构。
*   **Tailwind CSS**: 实用优先的 CSS 框架，负责所有样式（包括深色模式）。
*   **JavaScript (ES6+)**: 原生 JS 开发，不使用 React/Vue/Angular 等重型框架，保持极度轻量和高性能。
    *   *理由*: 为了极致的加载速度和对老旧 Android WebView 的兼容性。

### 2.2 数据存储 (Data Storage)
*   **IndexedDB**: 浏览器原生 NoSQL 数据库，用于存储海量结构化数据。
*   **Dexie.js**: IndexedDB 的轻量级封装库，提供易用的 Promise API。
    *   **Table `learning_progress`**: 存储每个单词的学习阶段、复习时间。
    *   **Table `explanations`**: 缓存 AI 生成的单词解析，避免重复消耗 Token。
    *   **Table `checkins`**: 记录每日打卡数据。

### 2.3 移动端容器 (Mobile Container)
*   **Capacitor**: 将 Web 应用封装为原生 Android/iOS 应用。
    *   **Plugins**: 使用 `Filesystem` 插件进行备份文件的读写，使用 `App` 插件处理后台运行和返回键。

---

## 3. 架构分层 (Architecture Layers)

### 3.1 视图层 (View Layer) - `app/index.html`
*   **职责**: 负责 UI 渲染和用户交互。
*   **规范**: 
    *   禁止直接操作 `window.db`。
    *   所有数据获取必须通过 `LocalAPI` 或 `ebbinghaus.js` 提供的服务接口。
    *   DOM 操作应封装在独立的函数中（如 `renderCard()`, `updateUI()`）。

### 3.2 逻辑控制层 (Controller Layer) - `app/static/js/*.js`
*   **`local_api.js`**: 
    *   **核心职责**: 路由分发器。拦截类似 `/api/ebbinghaus/action` 的请求，调用底层逻辑。
    *   **规范**: 模拟 `fetch` 的响应格式 `{ status: 'success', data: ... }`，确保前端代码无需大幅修改即可适配。
*   **`ebbinghaus.js`**:
    *   **核心职责**: 记忆算法实现。计算下一次复习时间、处理复习阶段流转。
*   **`llm.js`**:
    *   **核心职责**: AI 接口封装。负责拼接 Prompt、调用 OpenAI/DeepSeek 接口、处理流式响应。

### 3.3 数据层 (Data Layer) - `app/static/js/db.js`
*   **职责**: 数据库初始化、Schema 定义、数据迁移。
*   **规范**: 
    *   所有数据库操作（CRUD）应封装为 `db.transaction`。
    *   严禁在 UI 渲染循环中直接进行重型数据库查询。

---

## 4. 关键数据流 (Key Data Flows)

### 4.1 单词学习流程
1.  **UI**: 用户点击 "Know" / "Forget"。
2.  **Controller**: `submitReview(verb, quality)` 调用 `ebbinghaus.js`。
3.  **Algorithm**: `ebbinghaus.js` 计算新的 `next_review_time` 和 `stage`。
4.  **DB**: `db.learning_progress.put({...})` 更新记录。
5.  **UI**: 触发 `renderCard()` 更新界面。

### 4.2 AI 解析流程
1.  **UI**: 用户进入 "Analysis" 模式。
2.  **Controller**: 检查 `db.explanations` 是否有缓存。
    *   *有缓存*: 直接返回缓存数据。
    *   *无缓存*: 调用 `llm.js` 发起 API 请求 -> 获取 JSON -> 存入 `db.explanations` -> 返回数据。
3.  **UI**: 渲染解析卡片。

---

## 5. 扩展性设计 (Extensibility)

*   **模块化**: 新增功能（如“拼写练习”）应作为独立 JS 模块引入，不侵入现有核心逻辑。
*   **插件化 (规划中)**: 未来支持通过 `plugins/` 目录加载第三方 JS 脚本，通过 `window.NETEM_HOOKS` 暴露生命周期钩子。
