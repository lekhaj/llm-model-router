import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm_router import Router, Tier  # noqa: E402


def model(text, t_in=100, t_out=50):
    return lambda prompt: (text, t_in, t_out)


def test_cheap_tier_wins_when_valid():
    r = Router([Tier("s", model("good"), 0.001, 0.002), Tier("l", model("good"), 0.01, 0.02)], lambda t: t == "good")
    res = r.route("x")
    assert res.tier == "s" and res.validated and len(res.attempts) == 1


def test_escalates_when_invalid():
    r = Router([Tier("s", model("bad"), 0.001, 0.002), Tier("l", model("good"), 0.01, 0.02)], lambda t: t == "good")
    res = r.route("x")
    assert res.tier == "l" and res.validated
    assert [a[0] for a in res.attempts] == ["s", "l"]
    assert res.cost_usd > 0


def test_last_tier_returned_unvalidated_when_all_fail():
    r = Router([Tier("s", model("bad"), 0.001, 0.002), Tier("l", model("bad"), 0.01, 0.02)], lambda t: t == "good")
    res = r.route("x")
    assert res.tier == "l" and not res.validated


def test_stats_show_savings_vs_top_tier_baseline():
    r = Router([Tier("s", model("good"), 0.001, 0.002), Tier("l", model("good"), 0.01, 0.02)], lambda t: t == "good")
    for _ in range(10):
        r.route("x", baseline_tokens=(100, 50))
    assert r.stats.saved_pct == 90.0 and r.stats.served_by == {"s": 10}


def test_retries_within_tier():
    calls = {"n": 0}

    def flaky(prompt):
        calls["n"] += 1
        return ("good" if calls["n"] == 2 else "bad"), 10, 10

    r = Router([Tier("s", flaky, 0.001, 0.001)], lambda t: t == "good", max_tier_attempts=2)
    res = r.route("x")
    assert res.validated and len(res.attempts) == 2
