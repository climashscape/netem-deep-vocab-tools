import json
import os
from pathlib import Path

# 仓库根目录：本脚本位于 tools/generate-doc/，向上回溯两级。
# 路径不再依赖当前工作目录（原先按 CWD 相对解析，只有在仓库根运行才正确）。
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_within(base_dir, *parts):
    """把 *parts* 解析到 base_dir 之下，拒绝越界路径（CWE-22）。

    候选路径先经 realpath 归一（折叠 ``..`` 段并解析符号链接），
    落点在 base_dir 之外（含绝对路径与 ``..`` 穿越）一律拒绝。
    """
    base = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base, *parts))
    if os.path.commonpath([base, candidate]) != base:
        raise ValueError(
            "Refusing path outside %s: %r" % (base, os.path.join(*parts))
        )
    return candidate


# 输入的JSON文件名和输出的JSONL文件名（固定锚定在仓库的 tools/data/ 内）
input_json_file = _resolve_within(_REPO_ROOT, 'tools', 'data', 'netem_full_list.json')
output_jsonl_file = _resolve_within(_REPO_ROOT, 'tools', 'data', 'netem_full_list.jsonl')

# 读取JSON文件
data = json.loads(Path(input_json_file).read_text(encoding='utf-8'))

# 获取JSON对象的第一个键，假设您只有一个对象
obj_name = list(data.keys())[0]

# 获取包含对象的列表
obj_list = data.get(obj_name, [])

# 打开JSONL文件以写入
# 遍历对象列表并将每个对象以JSONL格式写入JSONL文件
Path(output_jsonl_file).write_text(
    ''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in obj_list),
    encoding='utf-8',
)

print(f"转换完成，已将数据写入 {output_jsonl_file}")
