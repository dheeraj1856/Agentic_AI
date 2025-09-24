
from __future__ import annotations

import os, json, requests
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Any, List

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr

# --------- Load environment variables ---------
load_dotenv(override=True)

# --------- Configuration ---------
@dataclass(frozen=True)
class AppConfig:
    name: str = "your name"
    model: str = "gpt-4o-mini" #or any other model you want to use
    pushover_token: str = os.getenv("PUSHOVER_TOKEN", "")
    pushover_user: str = os.getenv("PUSHOVER_USER", "")
    summary_path: Path = Path("your summary.txt")
    linkedin_pdf_path: Path = Path("your linkedin.pdf")

# --------- Side-effects isolated in helpers ---------
def push(text: str, cfg: AppConfig) -> None:
    """Fire-and-forget Pushover notification; safe if creds missing."""
    if not (cfg.pushover_token and cfg.pushover_user):
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": cfg.pushover_token, "user": cfg.pushover_user, "message": text},
            timeout=10,
        )
    except Exception:
        # Don't crash the app on push failures
        pass

def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def read_pdf_text(path: Path) -> str:
    text = []
    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            ptxt = page.extract_text() or ""
            if ptxt:
                text.append(ptxt)
    except Exception:
        pass
    return "\n".join(text)

# --------- Tool functions (business logic) ---------
def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided", _cfg: AppConfig | None = None) -> Dict[str, str]:
    if _cfg:
        push(f"Recording {name} with email {email} and notes {notes}", _cfg)
    return {"recorded": "ok"}

def record_unknown_question(question: str, _cfg: AppConfig | None = None) -> Dict[str, str]:
    if _cfg:
        push(f"Recording {question}", _cfg)
    return {"recorded": "ok"}

# JSON schemas must keep the same names & shapes to preserve model behavior
RECORD_USER_DETAILS_JSON = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional information about the conversation that's worth recording to give context"},
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

RECORD_UNKNOWN_QUESTION_JSON = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

TOOLS_JSON = [{"type": "function", "function": RECORD_USER_DETAILS_JSON},
              {"type": "function", "function": RECORD_UNKNOWN_QUESTION_JSON}]

# --------- Tool registry (different approach from original) ---------
ToolFn = Callable[..., Dict[str, Any]]

def make_tool_registry(cfg: AppConfig) -> Dict[str, ToolFn]:
    # Bind cfg into closures so tools can push notifications
    def _record_user_details(**kwargs): return record_user_details(_cfg=cfg, **kwargs)
    def _record_unknown_question(**kwargs): return record_unknown_question(_cfg=cfg, **kwargs)
    return {
        "record_user_details": _record_user_details,
        "record_unknown_question": _record_unknown_question,
    }

# --------- System prompt assembly (pure function) ---------
def build_system_prompt(cfg: AppConfig) -> str:
    linkedin_text = read_pdf_text(cfg.linkedin_pdf_path)
    summary_text = read_text_file(cfg.summary_path)

    base = (
        f"You are acting as {cfg.name}. You are answering questions on {cfg.name}'s website, "
        f"particularly questions related to {cfg.name}'s career, background, skills and experience. "
        f"Your responsibility is to represent {cfg.name} for interactions on the website as faithfully as possible. "
        f"You are given a summary of {cfg.name}'s background and LinkedIn profile which you can use to answer questions. "
        "Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
        "If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, "
        "even if it's about something trivial or unrelated to career. "
        "If the user is engaging in discussion, try to steer them towards getting in touch via email; "
        "ask for their email and record it using your record_user_details tool.\n\n"
    )
    base += f"## Summary:\n{summary_text}\n\n## LinkedIn Profile:\n{linkedin_text}\n\n"
    base += f"With this context, please chat with the user, always staying in character as {cfg.name}."
    return base

# --------- Chat orchestration (iteratively resolves tool calls) ---------
def resolve_chat(openai_client: OpenAI, model: str, tools_json: List[Dict[str, Any]],
                 tool_registry: Dict[str, ToolFn],
                 messages: List[Dict[str, str]]) -> str:
    """
    Loop until the model returns a normal assistant message (no pending tool_calls).
    """
    while True:
        resp = openai_client.chat.completions.create(model=model, messages=messages, tools=tools_json)
        choice = resp.choices[0]
        msg = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            # Append the assistant's tool call message first
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

            # For each tool call, execute and append tool results
            for call in msg.tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments or "{}")
                tool_fn = tool_registry.get(tool_name)

                # Defensive default to avoid crashes if schema drifts
                result: Dict[str, Any] = {}
                if tool_fn:
                    try:
                        result = tool_fn(**args)
                    except Exception as e:
                        result = {"error": f"{type(e).__name__}: {e}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                })
            # Continue the loop so the model can consume tool outputs
            continue

        # Normal completion (final assistant message)
        return msg.content or ""

# --------- Gradio app (stateless wrapper over pure functions) ---------
def make_chat_fn(cfg: AppConfig) -> Callable[[str, List[Dict[str, str]]], str]:
    client = OpenAI()
    system = build_system_prompt(cfg)
    registry = make_tool_registry(cfg)

    def chat(user_message: str, history: List[Dict[str, str]]) -> str:
        # history is already in ChatInterface format: [{'role': 'user'|'assistant', 'content': '...'}, ...]
        messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": user_message})
        return resolve_chat(client, cfg.model, TOOLS_JSON, registry, messages)

    return chat

# --------- Entry point ---------
if __name__ == "__main__":
    cfg = AppConfig()
    chat_fn = make_chat_fn(cfg)
    gr.ChatInterface(chat_fn, type="messages").launch()
