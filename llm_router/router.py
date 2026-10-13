from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

# A model is any callable: prompt -> (text, input_tokens, output_tokens)
ModelFn = Callable[[str], "tuple[str, int, int]"]
Validator = Callable[[str], bool]


@dataclass(frozen=True)
class Tier:
    """One rung of the ladder. Order tiers cheapest first."""

    name: str
    call: ModelFn
    usd_per_1k_in: float
    usd_per_1k_out: float

    def cost(self, tokens_in: int, tokens_out: int) -> float:
        return tokens_in / 1000 * self.usd_per_1k_in + tokens_out / 1000 * self.usd_per_1k_out


@dataclass
class RouteResult:
    text: str
    tier: str
    attempts: list  # [(tier_name, passed_validation, cost_usd)]
    cost_usd: float
    validated: bool


@dataclass
class RouterStats:
    tasks: int = 0
    cost_usd: float = 0.0
    baseline_usd: float = 0.0  # what the same tasks would cost on the top tier alone
    served_by: dict = field(default_factory=dict)

    @property
    def saved_pct(self) -> float:
        if self.baseline_usd == 0:
            return 0.0
        return round(100 * (1 - self.cost_usd / self.baseline_usd), 1)


class Router:
    """Try tiers in order; accept the first output the validator approves.

    The last tier is the fallback of record: its answer is returned even if it fails
    validation (flagged via ``validated=False``) so the caller decides what to do.
    """

    def __init__(self, tiers: list, validator: Validator, max_tier_attempts: int = 1):
        if not tiers:
            raise ValueError("at least one tier is required")
        self.tiers = list(tiers)
        self.validator = validator
        self.max_tier_attempts = max_tier_attempts
        self.stats = RouterStats()

    def route(self, prompt: str, baseline_tokens: Optional[tuple] = None) -> RouteResult:
        attempts, total = [], 0.0
        last_text, last_tier, ok = "", self.tiers[-1].name, False
        for i, tier in enumerate(self.tiers):
            is_last = i == len(self.tiers) - 1
            for _ in range(self.max_tier_attempts):
                text, t_in, t_out = tier.call(prompt)
                cost = tier.cost(t_in, t_out)
                total += cost
                ok = bool(self.validator(text))
                attempts.append((tier.name, ok, round(cost, 6)))
                last_text, last_tier = text, tier.name
                if ok:
                    return self._finish(RouteResult(text, tier.name, attempts, total, True), baseline_tokens, t_in, t_out)
            if is_last:
                break
        return self._finish(RouteResult(last_text, last_tier, attempts, total, False), baseline_tokens, 0, 0)

    def _finish(self, result: RouteResult, baseline_tokens, t_in: int, t_out: int) -> RouteResult:
        top = self.tiers[-1]
        b_in, b_out = baseline_tokens if baseline_tokens else (t_in, t_out)
        self.stats.tasks += 1
        self.stats.cost_usd += result.cost_usd
        self.stats.baseline_usd += top.cost(b_in, b_out)
        self.stats.served_by[result.tier] = self.stats.served_by.get(result.tier, 0) + 1
        return result
