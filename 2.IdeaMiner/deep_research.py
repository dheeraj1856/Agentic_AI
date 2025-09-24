
import asyncio
import gradio as gr
from dotenv import load_dotenv

# Import the orchestrator (unchanged public API: ResearchManager().run(query))
from research_manager import ResearchManager

load_dotenv(override=True)


async def _controller(query: str):
    """
    Thin controller that owns one ResearchManager per request.
    Keeps UI code small and readable. Streams chunks out exactly as before.
    """
    manager = ResearchManager()
    async for chunk in manager.run(query):
        # Yield verbatim so the visible output doesn't change
        yield chunk


def _bind_ui():
    """
    Build the UI in one place so main stays tiny.
    """
    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
        gr.Markdown("# Deep Research")
        query_textbox = gr.Textbox(label="What topic would you like to research?")
        run_button = gr.Button("Run", variant="primary")
        report = gr.Markdown(label="Report")

        # Gradio can consume an async generator directly; we pass our controller.
        run_button.click(fn=_controller, inputs=query_textbox, outputs=report)
        query_textbox.submit(fn=_controller, inputs=query_textbox, outputs=report)
    return ui


# Create and launch the app
ui = _bind_ui()
ui.launch(inbrowser=True)
