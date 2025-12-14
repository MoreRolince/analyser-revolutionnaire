"""Calcul du Winner Score."""
from __future__ import annotations


def winner_score(popularity: float, growth: float, potential: float, competition: float) -> float:
    return (
        popularity * 0.30 +
        growth * 0.25 +
        potential * 0.25 +
        competition * 0.20
    )


def evaluate_winner(sig: dict, thresholds: dict | None = None) -> tuple[float, bool, list[str]]:
    t = thresholds or {"growth": 5, "popularity": 0.4, "competition": 0.3, "score": 0.55}
    score = winner_score(
        sig.get("popularity_index", 0),
        sig.get("growth_index", 0),
        sig.get("potential_index", 0),
        sig.get("competition_index", 0),
    )
    reasons: list[str] = []
    if sig.get("growth_index", 0) > t["growth"]:
        reasons.append("growth_spike")
    if sig.get("popularity_index", 0) > t["popularity"]:
        reasons.append("popular")
    if sig.get("competition_index", 0) > t["competition"]:
        reasons.append("low_competition")
    if score > t["score"]:
        reasons.append("high_score")
    return score, bool(reasons), reasons



from __future__ import annotations


def winner_score(popularity: float, growth: float, potential: float, competition: float) -> float:
    return (
        popularity * 0.30 +
        growth * 0.25 +
        potential * 0.25 +
        competition * 0.20
    )


def evaluate_winner(sig: dict, thresholds: dict | None = None) -> tuple[float, bool, list[str]]:
    t = thresholds or {"growth": 5, "popularity": 0.4, "competition": 0.3, "score": 0.55}
    score = winner_score(
        sig.get("popularity_index", 0),
        sig.get("growth_index", 0),
        sig.get("potential_index", 0),
        sig.get("competition_index", 0),
    )
    reasons: list[str] = []
    if sig.get("growth_index", 0) > t["growth"]:
        reasons.append("growth_spike")
    if sig.get("popularity_index", 0) > t["popularity"]:
        reasons.append("popular")
    if sig.get("competition_index", 0) > t["competition"]:
        reasons.append("low_competition")
    if score > t["score"]:
        reasons.append("high_score")
    return score, bool(reasons), reasons


