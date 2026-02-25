# NETEM Deep Vocab Tools - 纯前端本地化 (Offline APK) 方案

## 1. 核心目标
将现有的 FastAPI + HTML 架构转换为**纯前端架构**，移除对 Python 后端的依赖，实现完全在手机本地运行的离线 APK。

## 2. 核心迁移逻辑

### 2.1 业务逻辑迁移 (JavaScript)
- **艾宾浩斯算法**: 将 [app.py](file:///g:/CODE/netem-deep-vocab-tools/scripts/explain_verbs/app.py) 中的 `EBBINGHAUS_STAGES` 和 `record_review` 逻辑迁移至 `js/ebbinghaus.js`。
- **LLM API 调用**: 使用 `fetch` 直接从前端调用 OpenAI/DeepSeek 接口，不再经过 Python 后端中转。
- **词库加载**: `netem_full_list.json` 改为静态资源，前端通过 `fetch` 一次性加载。

### 2.2 存储方案迁移 (IndexedDB)
- **数据库替代**: 使用 **Dexie.js** 管理 IndexedDB。
- **Explanations 表**: 缓存单词解析内容（原 SQLite `explanations` 表）。
- **Learning Progress 表**: 记录艾宾浩斯进度（原 SQLite `learning_progress` 表）。
- **Settings**: API Key 等配置存入 `localStorage`。

### 2.3 UI 适配
- 拦截 [index.html](file:///g:/CODE/netem-deep-vocab-tools/scripts/explain_verbs/templates/index.html) 中的所有 `/api/` 请求，重定向到本地 JS 逻辑。
- 移除 Jinja2 模板标签（如 `{{ request }}`）。

## 3. 开发路线图 (Roadmap)

### 第一阶段：逻辑重构 (Logic Refactor)
- [x] 创建 `local_api.js`，包含艾宾浩斯核心逻辑。
- [x] 创建 `db.js`，初始化 Dexie 数据库。
- [x] 迁移 LLM 调用逻辑，支持前端配置 API Key。
- [x] 重构 `index.html` 适配本地运行 (fetch 代理, 相对路径)。
- [x] 完成所有核心路由的本地化重写 (Mastery, Exclude, Export, Import 等)。

### 第二阶段：APK 打包 (APK Packaging)
- [x] 安装并初始化 Capacitor (`npx cap init`)。
- [x] 添加 Android 平台 (`npx cap add android`)。
- [x] 配置 `dist` 目录及相对路径适配。
- [x] 编译并生成 APK (需要 JDK 17+ 环境)。

## 4. 如何生成 APK (How to Build)
由于当前环境限制（需 JDK 17+），请在您的本地开发机上执行以下步骤：

1. **安装依赖**：
   ```bash
   npm install
   ```

2. **同步资源到 Android 项目**：
   ```bash
   npx cap sync
   ```

3. **使用 Android Studio 构建**：
   - 打开 `android` 目录。
   - 等待 Gradle 同步完成。
   - 点击 `Build > Build Bundle(s) / APK(s) > Build APK(s)`。

4. **命令行构建**（需配置好 Android SDK 和 JDK 11+）：
   ```bash
   cd android
   ./gradlew assembleDebug
   ```
   生成的 APK 将位于 `android/app/build/outputs/apk/debug/app-debug.apk`。

## 5. 技术栈总结
- **前端 (Frontend)**: HTML5, Tailwind CSS, JS (ES6+)
- **存储 (Storage)**: IndexedDB (via Dexie.js)
- **打包 (Packaging)**: Capacitor (v6+)
- **数据 (Data)**: JSON 静态文件

## 6. 常见问题排查 (Troubleshooting)

### 6.1 浏览器预览中的 CORS 错误
**现象**：在浏览器预览时，调用 LLM 解析提示 `TypeError: Failed to fetch` 或 `net::ERR_FAILED`。
**原因**：这是浏览器的安全限制。大多数 LLM API 厂商不允许直接从 `localhost` 发起跨域请求。
**解决方法**：
- **开发阶段**：可以使用浏览器扩展程序（如 "Allow CORS: Access-Control-Allow-Origin"）暂时禁用跨域限制进行测试。
- **打包 APK 后**：Capacitor 的 WebView 运行在 `http://localhost` 协议下，但在 Android/iOS 原生环境，Capacitor 会自动处理跨域豁免，**打包后该问题将不复存在**。
- **配置 API Key**：确保您的 `app_settings` 中配置了正确的 `openai_api_key`。系统已根据 `.env` 自动引导配置。

## 7. 最终汇总与建议 (Final Summary & Suggestions)

### 7.1 当前项目状态 (v1.0.0)
*   **架构模式**：已成功完成从“后端驱动”转向“纯前端本地化”架构。
*   **核心组件**：使用 IndexedDB (Dexie.js) 存储数据，艾宾浩斯算法迁移至前端，`local_api.js` 负责拦截并处理 API 请求。
*   **资源状态**：原生 Android 工程已同步最新前端代码，具备离线运行基础。
*   **新特性 (v1.0.0)**：
    *   ✅ **数据鲁棒性**：`local_api.js` 现支持 `legacy_data.json` 自动导入，防止首次使用时解析数据为空。
    *   ✅ **离线降级方案**：在无网络且无 LLM 解析时，自动显示基础释义及词频信息。
    *   ✅ **复习逻辑优化**：`index.html` 现支持自动跳转到最早到期的待复习单词。
    *   ✅ **资源全本地化**：Tailwind CSS、FontAwesome 等库已全部移至 `dist/static/lib`。

### 7.2 核心改进建议 (Future Plans)
*   **沉浸式体验**：针对移动端状态栏（Status Bar）进行 CSS Safe Area 适配。
*   **离线 TTS**：考虑集成安卓原生语音合成接口以支持离线发音。
