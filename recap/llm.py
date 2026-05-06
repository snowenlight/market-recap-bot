from __future__ import annotations

from pathlib import Path

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-2.5-flash"


def load_prompt(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def generate_summary(
    *,
    api_key: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Call Gemini with Google Search grounding and return the summary text."""
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    return (response.text or "").strip()
