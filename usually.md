启动静态版预览python -m http.server 8000 --directory dist


要将本项目编译成 APK，您需要遵循基于 **Capacitor** 的标准工作流。由于我们已经完成了“纯前端本地化”的改造，所有的核心逻辑都已经包含在 `dist` 目录中。

以下是具体的操作步骤：

### **第一步：环境准备**
确保您的电脑上已安装以下工具：
1.  **Node.js**: 用于运行 `npm` 和 `npx` 命令。
2.  **JDK 17+**: Android 编译必需。
3.  **Android Studio**: 推荐安装，它自带了 SDK 管理器和调试工具。

### **第二步：同步前端资源**
在终端（PowerShell）中运行以下命令，将最新的代码同步到安卓工程中：

```powershell
# 1. 安装项目依赖（如果还没安装过）
npm install

# 2. 将 dist 目录的代码同步到安卓原生项目
npx cap sync
```

### **第三步：生成 APK**
您有两种方式生成 APK：

#### **方法 A：使用命令行（最快）**
在项目根目录下直接运行：
```powershell
cd android
./gradlew assembleDebug
```
*   **结果**：编译完成后，您可以在以下路径找到 APK 文件：
    `g:\CODE\netem-deep-vocab-tools\android\app\build\outputs\apk\debug\app-debug.apk`

#### **方法 B：使用 Android Studio（推荐用于调试）**
1.  启动 **Android Studio**。
2.  选择 **Open**，然后打开项目中的 `android` 文件夹。
3.  等待底部的 Gradle 进度条跑完（初次打开可能需要下载一些依赖）。
4.  在顶部菜单栏选择：**Build > Build Bundle(s) / APK(s) > Build APK(s)**。
5.  完成后，右下角会弹出提示，点击 **locate** 即可定位到生成的 APK。

### **重要注意事项**
1.  **跨域问题**：在手机上运行 APK 时，Capacitor 会自动处理跨域限制，因此您填写的 OpenAI/DeepSeek API Key 应该可以正常直接调用，无需代理。
2.  **资源路径**：请确保所有资源引用都是相对路径（如 `static/js/...` 而不是 `/static/js/...`）。根据目前的 `dist` 结构，这已经适配好了。
3.  **图标与启动页**：如果您想更换图标，可以修改 `assets/icon.png` 和 `assets/splash.png`，然后运行 `npx cap-assets generate --android`。

**您需要我现在帮您运行 `npm install` 和 `npx cap sync` 吗？**