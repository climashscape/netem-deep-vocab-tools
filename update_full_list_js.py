import json
import os

# Define source and target paths
# We use the Dev static file as the source of truth
SOURCE_JSON = os.path.join("scripts", "explain_verbs", "static", "netem_full_list.json")

# Targets for the JS wrapper file
TARGET_JS_DEV = os.path.join("scripts", "explain_verbs", "static", "js", "data_full_list.js")
TARGET_JS_DIST = os.path.join("dist", "static", "js", "data_full_list.js")

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
        
        targets = [TARGET_JS_DEV, TARGET_JS_DIST]
        
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
