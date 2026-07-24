"""Gemini-powered resume screening with forced-JSON output and retry logic."""
from __future__ import annotations

import json
import os
import re

import httpx

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = """You are an expert technical recruiter and resume screener.
Compare the RESUME against the JOB DESCRIPTION and respond with ONLY a single
JSON object — no markdown, no code fences, no prose before or after.

The JSON must match this exact schema:
{
  "match_score": <integer 0-100, how well the resume matches the job>,
  "missing_keywords": [<strings: important skills/terms in the JD absent from the resume>],
  "suggestions": [<strings: concrete rewrite suggestions to improve the match>]
}

Rules:
- match_score is a single integer from 0 to 100.
- missing_keywords and suggestions are arrays of short strings (max 8 items each).
- Return valid JSON only. Do not wrap it in ``` fences."""


def _build_prompt(resume_text: str, job_description: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== JOB DESCRIPTION ===\n{job_description.strip()}\n\n"
        f"=== RESUME ===\n{resume_text.strip()}\n\n"
        "Return the JSON now."
    )


def _extract_json(text: str) -> dict:
    """Parse a JSON object out of the model's raw text, tolerating stray prose/fences."""
    text = text.strip()
    # Strip ```json ... ``` fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        # Otherwise grab the first {...} block.
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    return json.loads(text)


def _validate(data: dict) -> dict:
    """Coerce/validate the parsed object into the expected schema or raise ValueError."""
    if not isinstance(data, dict):
        raise ValueError("Response was not a JSON object")

    score = data.get("match_score")
    if isinstance(score, str):
        score = re.sub(r"[^0-9]", "", score) or 0
    score = int(float(score))
    score = max(0, min(100, score))

    def _string_list(value):
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    return {
        "match_score": score,
        "missing_keywords": _string_list(data.get("missing_keywords")),
        "suggestions": _string_list(data.get("suggestions")),
    }


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    # Send the key as a header, not a query param, so it never lands in logs/URLs.
    resp = httpx.post(
        GEMINI_URL,
        headers={"x-goog-api-key": api_key},
        json=payload,
        timeout=60,
    )
    if resp.status_code == 429:
        raise RuntimeError(
            "Gemini rate limit / quota exceeded (HTTP 429). Wait a minute and retry, "
            "or set a different GEMINI_MODEL (e.g. gemini-1.5-flash) in your .env."
        )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def screen_resume(resume_text: str, job_description: str, max_retries: int = 2) -> dict:
    """Screen a resume against a job description, retrying if the model returns bad JSON."""
    prompt = _build_prompt(resume_text, job_description)
    last_error: Exception | None = None

    for _ in range(max_retries + 1):
        try:
            raw = _call_gemini(prompt)
            parsed = _extract_json(raw)
            return _validate(parsed)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            last_error = exc
            # Nudge the model harder on the next attempt.
            prompt += "\n\nYour previous reply was not valid JSON. Return ONLY the JSON object."

    raise ValueError(f"Model did not return valid JSON after retries: {last_error}")
