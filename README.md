# llm-model-router

Cost-aware routing for LLM calls: **try the cheap model first, escalate to the strong model only when the output fails a validator.**

Most production LLM workloads are a mix of easy and hard steps. Sending everything to the strongest model wastes money; sending everything to the cheapest one wastes quality. This is a tiny, dependency-free implementation of the middle path.

```
prompt ──▶ [small model] ──valid?──▶ done
                │ no
                ▼
          [large model] ──▶ done (flagged if still invalid)
```

## Why a validator, not a classifier
Deciding *up front* whether a task is "hard" is unreliable. Checking the *result* is cheap and exact for structured work: valid JSON, schema match, required fields present, tests pass, a regex hits. The validator is the only thing you have to write.

## Use

```python
from llm_router import Router, Tier

router = Router(
    tiers=[Tier("small", small_fn, 0.001, 0.005), Tier("large", large_fn, 0.003, 0.015)],
    validator=lambda text: text.strip().startswith("{"),
)
result = router.route("Summarise this module as JSON ...")
print(result.tier, result.cost_usd, router.stats.saved_pct)
```

A model is any callable `prompt -> (text, tokens_in, tokens_out)`. `llm_router/anthropic_adapter.py` wraps the Anthropic Messages API (`pip install anthropic`); model IDs and prices are arguments, never hard-coded.

## Try it offline

```bash
python examples/simulated_demo.py
pytest
```

The demo uses **simulated** models with made-up pass rates and prices. It illustrates how the savings arise, it is **not** a benchmark. Measure your own pass rates before trusting any number.

## Design notes
- **Escalate on evidence, not guesses.** Cost of a failed cheap attempt is small compared with the saving on the tasks it handles.
- **Last tier is the fallback of record.** Its answer is returned even if invalid, with `validated=False`, so the caller decides (retry, human review, fail).
- **Stats against a baseline.** `RouterStats` compares actual spend with "everything on the top tier" so the saving is a measured number, not a claim.

## License
MIT
