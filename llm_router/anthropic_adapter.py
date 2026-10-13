"""Optional adapter for the Anthropic Messages API. Requires `pip install anthropic` and ANTHROPIC_API_KEY.

Model IDs are passed in, not hard-coded, so you can swap models without touching the router.
"""
from __future__ import annotations

from .router import Tier


def anthropic_tier(name: str, model_id: str, usd_per_1k_in: float, usd_per_1k_out: float, max_tokens: int = 1024) -> Tier:
    import anthropic  # imported lazily so the core package has zero dependencies

    client = anthropic.Anthropic()

    def call(prompt: str):
        msg = client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return text, msg.usage.input_tokens, msg.usage.output_tokens

    return Tier(name, call, usd_per_1k_in, usd_per_1k_out)
