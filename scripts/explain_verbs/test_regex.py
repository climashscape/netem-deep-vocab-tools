
import re

def normalize_markdown(raw_markdown):
    section_keys = ['三维理解', '本质动作', '关键洞察', '深度解析', '应用场景', '错误纠正', '对比分析', '本质', '场景比喻']
    key_pattern = '|'.join(section_keys)
    
    # Python regex for: (^|\n)\s*(?:[*#]\s*)*(key)(?:\s*[*#：:])*\s*
    # We use multiline mode (?m) so ^ matches start of line
    pattern = r'(?m)(^|\n)\s*(?:[*#]\s*)*(' + key_pattern + r')(?:[\s*#：:])*\s*'
    
    print(f"Pattern: {pattern}")
    
    def replace_func(match):
        return f"{match.group(1)}#### {match.group(2)}\n\n"
        
    normalized = re.sub(pattern, replace_func, raw_markdown)
    return normalized

test_cases = [
    "## # # 三维理解",
    "* *三维理解",
    "**三维理解**",
    "### 三维理解",
    "## # # 本质动作",
    "* *本质动作：**",
    "**场景比喻：**",
    "\n\n* *关键洞察",
    "前文\n* *深度解析**\n后文"
]

for case in test_cases:
    result = normalize_markdown(case)
    print(f"Original: {repr(case)}")
    print(f"Result:   {repr(result)}")
    print("-" * 20)
