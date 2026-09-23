import os

import httpx


def _extract_output_text(payload: dict) -> str:
    parts: list[str] = []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def enrich_with_optional_model(task: str, deterministic_result: str) -> dict:
    provider = os.getenv("MODEL_PROVIDER", "mock").lower()
    if provider != "openai":
        return {
            "provider": "mock",
            "content": deterministic_result,
            "warning": "MODEL_PROVIDER is not openai; deterministic result returned.",
        }

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return {
            "provider": "fallback",
            "content": deterministic_result,
            "warning": "OpenAI credentials or model are missing; deterministic result returned.",
        }

    try:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "instructions": (
                    "You improve the clarity of a crowdfunding operations draft. "
                    "Do not invent metrics, sources, delivery promises, or external actions."
                ),
                "input": f"Task:\n{task}\n\nVerified deterministic result:\n{deterministic_result}",
                "store": False,
                "max_output_tokens": 700,
            },
            timeout=20,
        )
        response.raise_for_status()
        content = _extract_output_text(response.json())
        if not content:
            raise ValueError("Model response did not contain output text")
        return {"provider": "openai", "content": content, "warning": None}
    except (httpx.HTTPError, ValueError) as error:
        return {
            "provider": "fallback",
            "content": deterministic_result,
            "warning": f"Model call failed; deterministic result returned: {type(error).__name__}",
        }
