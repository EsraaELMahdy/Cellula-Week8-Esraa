import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / "app.env")

MODEL = "openrouter/free"

SYSTEM = (
    "You rewrite a user's question into a clear, standalone search query "
    "for a document search system. Use the chat history to replace pronouns "
    "and vague words. Expand abbreviations. Keep the same language as the question. "
    "Do not answer the question. Return only the rewritten query on one line."
)


def rewrite_query(question: str, history: list[dict] | None = None) -> str:
    # without history there are no pronouns to fix, so we save the request
    if not history:
        return question

    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "put_your_key_here":
        print("WARNING: OPENROUTER_API_KEY is missing, the question is used without rewriting.")
        return question

    lines = [f'{m["role"]}: {m["content"]}' for m in history[-6:]]
    user_msg = "Chat history:\n" + "\n".join(lines) + "\n\nQuestion: " + question
    try:
        client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        return text.splitlines()[0] if text else question
    except Exception as e:
        print("WARNING: query rewriter failed, using the original question:", type(e).__name__)
        return question
