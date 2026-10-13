"""Cost-aware LLM routing: try the cheap model first, escalate only when the output fails validation."""
from .router import Tier, Router, RouteResult, RouterStats

__all__ = ["Tier", "Router", "RouteResult", "RouterStats"]
