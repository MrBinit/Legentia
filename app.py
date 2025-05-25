import gradio as gr
import asyncio
from agents import process_legal_document

# Wrapper to pass user language into agent (modification in agent.py required)
def process_sync(document_path, user_language):
    # Validate language input
    user_language = user_language.strip().lower() if user_language else "english"

    if user_language not in ["english", "nepali"]:
        return "Sorry, we currently only support English and Nepali."

    return asyncio.run(process_legal_document(document_path, user_language))


# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 🧾 Legal Document Reviewer (Multi-Agent)")
    gr.Markdown("Upload a legal contract or image. Choose the document's language. The system will analyze and summarize it.")

    file_input = gr.File(label="📄 Upload Legal Document", file_types=[".pdf", ".docx", ".jpg", ".jpeg", ".png"])
    lang_input = gr.Textbox(label="🌐 Document Language (English or Nepali)", placeholder="Default is English")
    output_box = gr.Textbox(label="📝 Final Summary", lines=20)

    process_button = gr.Button("Run Analysis")

    def on_submit(file, language):
        if file is None:
            return "Please upload a legal document."
        return process_sync(file.name, language)

    process_button.click(fn=on_submit, inputs=[file_input, lang_input], outputs=output_box)

# Launch Gradio app
if __name__ == "__main__":
    demo.launch(share = True)
