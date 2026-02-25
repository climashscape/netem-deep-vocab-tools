
with open('scripts/explain_verbs/append_visual_prompt.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('scripts/explain_verbs/prompt.py', 'a', encoding='utf-8') as f:
    f.write("\n" + content)
