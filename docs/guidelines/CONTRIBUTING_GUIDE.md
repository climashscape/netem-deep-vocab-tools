# 开发与贡献指南 (Contributing Guide)

## 1. 行为准则 (Code of Conduct)

本项目遵循开放、包容、友好的开源社区准则。
*   尊重每一位贡献者。
*   保持专业、客观的讨论。
*   禁止骚扰、歧视或攻击性言论。

---

## 2. 提交规范 (Commit Convention)

### 2.1 Commit Message Format
我们采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

格式: `<type>(<scope>): <subject>`

#### 常用类型 (Type):
*   `feat`: 新功能 (Feature)
*   `fix`: 修复 Bug (Bug Fix)
*   `docs`: 文档更新 (Documentation)
*   `style`: 代码格式调整 (Formatting, missing semi colons, etc)
*   `refactor`: 代码重构 (Code Refactoring)
*   `perf`: 性能优化 (Performance Improvement)
*   `test`: 测试相关 (Adding missing tests)
*   `chore`: 构建过程或辅助工具变动 (Build process, auxiliary tools)

#### 示例:
*   `feat(app): add offline TTS support`
*   `fix(db): correct migration logic for v6.6.6`
*   `docs(readme): update installation guide`

### 2.2 Git Flow
1.  **Fork** 本仓库。
2.  **Clone** 到本地。
3.  基于 `main` 分支创建新的功能分支: `git checkout -b feat/my-feature`。
4.  进行开发并提交 Commit。
5.  **Push** 到您的 Fork 仓库。
6.  提交 **Pull Request (PR)** 到本仓库的 `main` 分支。

---

## 3. 代码风格 (Coding Style)

### 3.1 JavaScript (ES6+)
*   **缩进**: 4 空格。
*   **变量**: 优先使用 `const`，其次 `let`，禁止使用 `var`。
*   **函数**: 优先使用箭头函数 `() => {}` (除非涉及 `this` 上下文)。
*   **注释**: 
    *   关键逻辑必须添加注释。
    *   函数头使用 JSDoc 格式注释参数和返回值。
    *   禁止提交无用的 `console.log`。

### 3.2 CSS (Tailwind CSS)
*   **类名顺序**: 遵循 `Layout -> Box Model -> Typography -> Visual -> Misc` 的顺序（推荐使用 VS Code 插件自动排序）。
*   **命名**: 自定义 CSS 类名使用 `kebab-case` (e.g., `.verb-card`).
*   **响应式**: 优先移动端适配，使用 `md:` `lg:` 前缀适配大屏。

### 3.3 HTML
*   **语义化**: 使用 `<header>`, `<main>`, `<footer>`, `<nav>`, `<article>` 等标签。
*   **属性顺序**: `id`, `class`, `name`, `data-*`, `src`, `href`, `title`, `alt`。

---

## 4. 开发流程 (Development Workflow)

### 4.1 环境准备
1.  安装 **Python 3.8+** 和 **Node.js 18+**。
2.  安装依赖: `pip install -r tools/requirements.txt` 和 `npm install`。

### 4.2 本地开发
1.  启动带有 API 代理的开发服务器:
    ```bash
    python tools/utils/dev_proxy.py
    ```
2.  打开浏览器访问 `http://localhost:8000/`。
3.  修改 `app/` 下的代码，刷新浏览器查看效果。

### 4.3 数据更新
如果您修改了 `tools/data/netem_full_list.json` 中的原始数据：
1.  运行更新脚本:
    ```bash
    python tools/utils/update_full_list_js.py
    ```
2.  验证 `app/static/js/data_full_list.js` 是否已更新。

### 4.4 测试 (Testing)
*   **手动测试**: 在浏览器中模拟断网环境，确保应用依然可用。
*   **移动端测试**: 使用 Chrome DevTools 模拟移动端设备尺寸和触摸事件。

---

## 5. 提交 PR 检查清单 (PR Checklist)
- [ ] 代码符合上述风格规范。
- [ ] 所有新功能均已在本地测试通过。
- [ ] 文档已更新（如有必要）。
- [ ] 提交信息符合 Conventional Commits 规范。
- [ ] 未包含敏感信息（如 API Key, Token）。
