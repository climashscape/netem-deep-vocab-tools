# 发布流程规范 (Release Workflow)

## 1. 版本号管理 (Versioning)

本项目遵循 [Semantic Versioning 2.0.0](https://semver.org/)。

格式: `MAJOR.MINOR.PATCH`
*   **MAJOR**: 不兼容的 API 修改。
*   **MINOR**: 向下兼容的功能性新增。
*   **PATCH**: 向下兼容的问题修正。

示例: `v6.6.6`

---

## 2. 发布前检查清单 (Pre-Release Checklist)

### 2.1 代码冻结 (Code Freeze)
*   确保 `main` 分支处于稳定状态，无未解决的 Critical Issue。
*   所有新功能已完成开发并通过初步测试。

### 2.2 数据同步 (Data Sync)
*   **原始数据**: 检查 `tools/data/netem_full_list.json` 是否为最新。
*   **前端数据**: 运行 `python tools/utils/update_full_list_js.py`，确保 `app/static/js/data_full_list.js` 与原始数据一致。
*   **备份测试**: 导出一次备份文件 (`.json`)，并在本地模拟导入，确保数据迁移逻辑正常。

### 2.3 版本号更新 (Version Update)
*   **UI 显示**: 修改 `app/index.html` 中的版本号显示。
*   **配置**: 修改 `package.json` 中的 `version` 字段。
*   **原生配置**: 修改 `android/app/build.gradle` 中的 `versionName` 和 `versionCode`。
*   **文档**: 更新 `README.md` 中的版本号。
*   **VERSION 文件**: 更新根目录下的 `VERSION` 文件。

---

## 3. 构建流程 (Build Process)

### 3.1 准备环境
确保已安装 JDK 17+ 和 Android SDK。

### 3.2 同步前端资源
```bash
# 1. 安装依赖
npm install

# 2. 将 app 目录代码同步到 android 工程
npx cap sync
```

### 3.3 构建 APK
#### 方式 A: 命令行 (推荐)
```bash
cd android
./gradlew assembleRelease
```
生成的 APK 位于: `android/app/build/outputs/apk/release/app-release-unsigned.apk` (需签名)。

#### 方式 B: Android Studio
1.  打开 `android/` 目录。
2.  `Build > Generate Signed Bundle / APK...`。
3.  选择 `APK` -> `Next`。
4.  选择签名密钥 (Key Store) -> `Next`。
5.  选择 `release` 变体 -> `Finish`。

---

## 4. 发布与分发 (Release & Distribution)

### 4.1 GitHub Release
1.  在 GitHub 上创建一个新的 Release。
2.  Tag 名称: `v6.6.6` (与版本号一致)。
3.  标题: `v6.6.6 - [简要描述]`。
4.  内容: 
    *   **新特性 (Features)**
    *   **修复 (Fixes)**
    *   **重要说明 (Important Notes)**
5.  **附件**: 上传构建好的 `app-release.apk`。

### 4.2 通知 (Notification)
*   在社区/群组通知用户更新。
*   如果涉及重大更新，建议通过应用内公告提示用户（需手动更新 `usually.md` 或相关公告文件）。

---

## 5. 回滚流程 (Rollback Plan)

如果在发布后发现严重 Bug：
1.  **立即停止分发**: 删除 GitHub Release 中的 APK。
2.  **定位问题**: 分析错误日志，确认是否为关键 Bug。
3.  **修复**: 提交 `hotfix` 分支进行紧急修复。
4.  **重新发布**: 版本号递增 (e.g., `v6.6.7`)，重复上述流程。
