import gradio as gr
import os
import sys

# Ensure we can import the explain_verbs logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from explain_verbs import get_client, explain_verb
except ImportError:
    # If running from root
    try:
        from scripts.explain_verbs.explain_verbs import get_client, explain_verb
    except ImportError:
         print("Could not import explain_verbs. Please run from project root or scripts/explain_verbs/")
         sys.exit(1)

def process_request(verbs_input, mode):
    client = get_client()
    if not client:
        return "Error: API Key not configured. Please check .env file."
    
    verbs = verbs_input.split()
    if not verbs:
        return "Please enter at least one verb."
    
    # Simple logic to determine prompt
    if mode.startswith("Single"):
        results = []
        for verb in verbs:
            # We call the imported function which handles the prompt construction internally?
            # Wait, explain_verb takes (client, user_input, model)
            # We need to construct the user_input string here.
            prompt = f"请解析\"{verb}\""
            result = explain_verb(client, prompt)
            results.append(result)
        return "\n\n---\n\n".join(results)

    elif mode.startswith("List"):
         prompt = f"请解析这组动词：[{', '.join(verbs)}]"
         return explain_verb(client, prompt)

    elif mode.startswith("Compare"):
         prompt = f"请对比以下动词：{', '.join(verbs)}"
         return explain_verb(client, prompt)
    
    return "Invalid mode selected."

def main():
    # 🌿 自定义复古自然主义主题
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.emerald,
        secondary_hue=gr.themes.colors.stone,
        neutral_hue=gr.themes.colors.stone,
        font=['Times New Roman', 'ui-serif', 'system-ui', 'serif'],
        radius_size=gr.themes.sizes.radius_sm,
    ).set(
        body_background_fill="#fdfbf7",
        body_text_color="#4a4a4a",
        background_fill_primary="#f7f5f0",
        background_fill_secondary="#efece6",
        border_color_primary="#dcd9d0",
        block_title_text_color="#5D4037",
        block_label_text_color="#795548",
        input_background_fill="#ffffff",
        button_primary_background_fill="#4CAF50",
        button_primary_background_fill_hover="#45a049",
        button_primary_text_color="white",
        button_secondary_background_fill="#e0e0e0",
        button_secondary_text_color="#333",
    )

    # 📜 CSS 样式微调
    custom_css = """
    .gradio-container {
        font-family: 'Times New Roman', serif !important;
        max-width: 1000px !important;
        margin: auto !important;
    }
    
    h1 {
        font-family: 'Times New Roman', serif;
        color: #2E7D32 !important;
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 2.5rem !important;
    }
    
    .subtitle {
        text-align: center;
        color: #555;
        font-style: italic;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }

    .output-markdown {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    
    /* 让输入框更有质感 */
    textarea, input {
        border: 1px solid #ccc !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    """

    with gr.Blocks(title="English Verb Cognitive Parser") as demo:
        gr.Markdown("# 🇬🇧 英语核心动词深度认知解析系统")
        gr.Markdown("<div class='subtitle'>穿过语言的迷雾，触摸每一个动词的灵魂纹理。</div>")
        
        with gr.Row():
            with gr.Column(scale=1, variant="panel"):
                gr.Markdown("### 🧭 探索指南")
                verbs_input = gr.Textbox(
                    label="输入动词 (用空格分隔)", 
                    placeholder="e.g. make do get",
                    lines=1
                )
                mode_input = gr.Radio(
                    choices=["Single (One by one)", "List (Group analysis)", "Compare (Contrast analysis)"],
                    value="Single (One by one)",
                    label="解析模式",
                    info="选择最适合您当前学习目标的模式"
                )
                submit_btn = gr.Button("开始解析 / Start Analysis", variant="primary", size="lg")
                
                gr.Markdown("""
                ---
                #### 📚 模式说明
                - **Single**: 逐个击破，深度剖析每个词的认知内核。
                - **List**: 批量处理，寻找词群共性。
                - **Compare**: 辨析差异，明晰边界。
                """)
                
            with gr.Column(scale=2):
                output_display = gr.Markdown(label="解析结果", elem_classes="output-markdown")
        
        submit_btn.click(
            fn=process_request,
            inputs=[verbs_input, mode_input],
            outputs=output_display
        )
    
    # Pass theme and css here instead of in Blocks
    demo.launch(server_name="127.0.0.1", server_port=7860, theme=theme, css=custom_css)

if __name__ == "__main__":
    main()
