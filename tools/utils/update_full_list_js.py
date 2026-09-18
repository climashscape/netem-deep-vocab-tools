import json
import os

# Repository root: this script lives in tools/utils/, two levels below root.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_within(base_dir, *parts):
    """Resolve *parts* under base_dir and refuse path escapes (CWE-22).

    The candidate path is fully resolved (``..`` segments and symlinks
    collapsed via realpath); anything landing outside base_dir — including
    absolute paths and ``..`` traversal — is rejected with ValueError.
    """
    base = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base, *parts))
    if os.path.commonpath([base, candidate]) != base:
        raise ValueError(
            "Refusing path outside %s: %r" % (base, os.path.join(*parts))
        )
    return candidate


# Define source and target paths
# We use the Tools data file as the source of truth. Paths are anchored to
# the repository root (no CWD dependence) and boundary-checked.
SOURCE_JSON = _resolve_within(_REPO_ROOT, "tools", "data", "netem_full_list.json")

# Target for the JS wrapper file in the app
TARGET_JS_APP = _resolve_within(_REPO_ROOT, "app", "static", "js", "data_full_list.js")

def main():
    print(f"Reading source: {SOURCE_JSON}")
    if not os.path.exists(SOURCE_JSON):
        print("Error: Source JSON not found!")
        return

    try:
        with open(SOURCE_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Create JS content
        # window.NETEM_FULL_LIST = { ... }
        js_content = f"window.NETEM_FULL_LIST = {json.dumps(data, ensure_ascii=False)};"
        
        targets = [TARGET_JS_APP]
        
        for target in targets:
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                print(f"✅ Generated: {target} ({len(js_content)} bytes)")
            except Exception as e:
                print(f"❌ Failed to write {target}: {e}")
                
    except Exception as e:
        print(f"Error processing full list: {e}")

if __name__ == "__main__":
    main()
