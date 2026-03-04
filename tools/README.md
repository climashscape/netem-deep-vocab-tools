# NETEM Deep Vocab Tools - 工具脚本

本目录包含用于数据处理、维护和静态站点开发的实用脚本。

## 目录结构

*   `data/`: 包含源数据文件 (JSON, SQL)。
*   `checkers/`: 用于数据完整性检查的脚本。
*   `exporters/`: 用于导出数据的脚本 (旧版)。
*   `utils/`: 通用实用脚本 (代理, 转换器等)。
*   `legacy/`: 来自以前版本的归档脚本。
*   `doc_gen/`: 用于生成文档的脚本。
*   `json_gen/`: 用于从 SQL 生成 JSON 的脚本。
*   `spelling/`: 用于处理拼写变体的脚本。
*   `def_update/`: 用于格式化定义的脚本。

## 核心脚本

*   `utils/dev_proxy.py`: 用于本地开发的简单 HTTP 代理，用于解决从 localhost 调用 LLM API 时的 CORS 跨域问题。
*   `checkers/check_duplicates.py`: 检查词汇表中是否存在重复条目。
*   `legacy/export_data_for_build.py`: 导出用于生产构建的数据 (旧版)。
*   `utils/update_full_list_js.py`: 更新静态站点使用的 `data_full_list.js` 文件。

## 使用方法

大多数脚本都是 Python 脚本，可以直接从根目录运行：

```bash
python tools/checkers/check_duplicates.py
```

请确保您已安装必要的依赖项：

```bash
pip install -r tools/requirements.txt
```
