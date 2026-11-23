import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / "app.env")

MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")


class LLMError(Exception):
    """The LLM call failed or gave an answer we cannot use."""


def ask_llm(system: str, user: str) -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key in {"put_your_key_here", "your_api_key_here"}:
        raise LLMError("OPENROUTER_API_KEY is missing. Copy app.env.example to app.env and add your key.")
    try:
        client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1", timeout=60, max_retries=1)
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except Exception as e:
        raise LLMError(f"LLM request failed: {type(e).__name__}: {e}") from e

    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise LLMError("The LLM returned an empty answer.")
    return text


def ask_json(system: str, user: str):
    """Ask for JSON. We try twice because the free model sometimes breaks the format."""
    for attempt in range(2):
        text = ask_llm(system, user)
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise LLMError("The LLM did not return valid JSON.")
