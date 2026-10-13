"""Runs offline with simulated models. The numbers it prints are a SIMULATION of the pattern,
not a benchmark of any real model: change the pass rates to match your own measurements.

    python examples/simulated_demo.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm_router import Router, Tier  # noqa: E402

random.seed(7)


def make_model(pass_rate: float):
    """Pretend model: returns valid JSON with probability pass_rate, otherwise malformed text."""

    def call(prompt: str):
        ok = random.random() < pass_rate
        text = json.dumps({"summary": "ok"}) if ok else "Sure! Here is the summary: ok"
        return text, 400, 120

    return call


def is_valid_json(text: str) -> bool:
    try:
        value = json.loads(text)
        return isinstance(value, dict) and "summary" in value
    except ValueError:
        return False


tiers = [
    Tier("small", make_model(0.80), usd_per_1k_in=0.001, usd_per_1k_out=0.005),
    Tier("large", make_model(0.99), usd_per_1k_in=0.003, usd_per_1k_out=0.015),
]
router = Router(tiers, validator=is_valid_json)

for i in range(1000):
    router.route(f"task {i}", baseline_tokens=(400, 120))

s = router.stats
print(f"tasks={s.tasks}  served_by={s.served_by}")
print(f"cost=${s.cost_usd:.2f}  all-large baseline=${s.baseline_usd:.2f}  saved={s.saved_pct}%")
