import argparse
import os
import sys
import json
import time

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: 'python-dotenv' module is required. Please install it using: pip install python-dotenv")
    sys.exit(1)

# Add the current directory to sys.path to import modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from settings import settings
except ImportError:
    # If running from root, maybe settings.py is available differently
    pass

try:
    from prompt import EXPLAIN_VERB_SYSTEM_PROMPT, EXPLAIN_NOUN_SYSTEM_PROMPT, EXPLAIN_CONCEPT_SYSTEM_PROMPT, EXPLAIN_ADJ_ADV_SYSTEM_PROMPT, EXPLAIN_PREP_SYSTEM_PROMPT, EXPLAIN_PREP_CONJ_SYSTEM_PROMPT
except ImportError:
    # Fallback if running from root
    try:
        from scripts.explain_verbs.prompt import EXPLAIN_VERB_SYSTEM_PROMPT, EXPLAIN_NOUN_SYSTEM_PROMPT, EXPLAIN_CONCEPT_SYSTEM_PROMPT, EXPLAIN_ADJ_ADV_SYSTEM_PROMPT, EXPLAIN_PREP_SYSTEM_PROMPT, EXPLAIN_PREP_CONJ_SYSTEM_PROMPT
    except ImportError:
        print("Error: Could not import prompt module.")
        sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: 'openai' module is required. Please install it using: pip install openai")
    sys.exit(1)

def get_client(api_key=None, base_url=None):
    # Try to get from settings first if not provided
    try:
        from settings import settings
        if not api_key:
            api_key = settings.openai_api_key
        if not base_url:
            base_url = settings.openai_base_url
    except ImportError:
        pass

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        # Silently return None if no key found, caller handles error message
        return None
    
    if not base_url:
        base_url = os.environ.get("OPENAI_BASE_URL")
        
    return OpenAI(api_key=api_key, base_url=base_url)

def explain_verb(client, user_input, model=None, pos=None):
    """
    Sends a request to the LLM to explain the word(s).
    """
    if not model:
        try:
            from settings import settings
            model = settings.openai_model
        except ImportError:
            model = os.environ.get("DEFAULT_MODEL", "gpt-4o")

    # Select prompt based on POS
    system_prompt = EXPLAIN_VERB_SYSTEM_PROMPT
    
    if pos == "noun":
        system_prompt = EXPLAIN_NOUN_SYSTEM_PROMPT
    elif pos == "other":
        system_prompt = EXPLAIN_CONCEPT_SYSTEM_PROMPT
    elif pos == "adj_adv" or pos == "adj" or pos == "adv":
        system_prompt = EXPLAIN_ADJ_ADV_SYSTEM_PROMPT
    elif pos == "prep":
        system_prompt = EXPLAIN_PREP_SYSTEM_PROMPT
    elif pos == "prep_conj":
        system_prompt = EXPLAIN_PREP_CONJ_SYSTEM_PROMPT
    elif pos == "noun_verb" or pos == "verb_noun":
        system_prompt = EXPLAIN_VERB_SYSTEM_PROMPT
    # verb uses default

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling API: {e}"

def main():
    parser = argparse.ArgumentParser(description="Explain English verbs using Cognitive Linguistics approach.")
    parser.add_argument("verbs", nargs="*", help="List of verbs to explain (e.g., make do have)")
    parser.add_argument("--file", "-f", help="Path to a file containing verbs (one per line or JSON)")
    parser.add_argument("--json-file", "-j", help="Path to netem_verbs.json to process top N verbs")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Number of verbs to process from JSON file")
    parser.add_argument("--output", "-o", help="Output file path (Markdown). If not specified, prints to stdout.")
    parser.add_argument("--model", "-m", default=None, help="LLM model to use (default: from .env or gpt-4o)")
    parser.add_argument("--prompt-type", choices=["single", "list", "compare"], default="single", help="Type of prompt to construct")
    
    args = parser.parse_args()

    verbs_to_process = []

    if args.verbs:
        verbs_to_process.extend(args.verbs)
    
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if args.file.endswith('.json'):
                     # Simple list in json
                     try:
                         data = json.loads(content)
                         if isinstance(data, list):
                             verbs_to_process.extend(data)
                     except:
                         pass
                else:
                    verbs_to_process.extend([line.strip() for line in content.splitlines() if line.strip()])
    
    if args.json_file:
        if os.path.exists(args.json_file):
            try:
                with open(args.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle netem_verbs.json structure
                    # {"5530考研词汇词频排序表 (Verbs Only)": [{"单词": "be", ...}]}
                    key = list(data.keys())[0]
                    word_list = data[key]
                    count = 0
                    for item in word_list:
                        if count >= args.limit:
                            break
                        word = item.get('单词')
                        if word and word not in verbs_to_process:
                            verbs_to_process.append(word)
                            count += 1
            except Exception as e:
                print(f"Error reading JSON file: {e}")
        else:
            print(f"Warning: JSON file {args.json_file} not found.")

    if not verbs_to_process:
        print("No verbs found or specified.")
        print("Usage examples:")
        print("  python scripts/explain_verbs/explain_verbs.py make do")
        print("  python scripts/explain_verbs/explain_verbs.py --json-file netem_verbs.json --limit 5")
        sys.exit(0)

    client = get_client()
    if not client:
        print("Skipping API call because OPENAI_API_KEY is missing.")
        print("Here is the list of verbs that would have been processed:")
        print(verbs_to_process)
        sys.exit(0)
    
    results = []

    # Process strategy:
    # If "compare", join them in one request
    # If "list", join them in one request (up to a limit?)
    # If "single" (default), iterate and call one by one (better for detailed output)
    
    if args.prompt_type == "compare":
        user_input = f"请对比以下动词：{', '.join(verbs_to_process)}"
        print(f"Processing comparison: {user_input}")
        result = explain_verb(client, user_input, args.model)
        results.append(result)
    elif args.prompt_type == "list":
         user_input = f"请解析这组动词：[{', '.join(verbs_to_process)}]"
         print(f"Processing list: {user_input}")
         result = explain_verb(client, user_input, args.model)
         results.append(result)
    else:
        # One by one
        print(f"Processing {len(verbs_to_process)} verbs one by one...")
        for i, verb in enumerate(verbs_to_process):
            user_input = f"请解析\"{verb}\""
            print(f"[{i+1}/{len(verbs_to_process)}] Explaining '{verb}'...")
            result = explain_verb(client, user_input, args.model)
            results.append(result)
            if i < len(verbs_to_process) - 1:
                time.sleep(1) # Be nice to API limits

    final_output = "\n\n".join(results)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(final_output)
        print(f"Output saved to {args.output}")
    else:
        print("\n" + "="*40 + "\n")
        print(final_output)

if __name__ == "__main__":
    main()
