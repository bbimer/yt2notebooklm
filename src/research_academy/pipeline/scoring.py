"""Deterministic Python scoring and decision logic for Gatekeeper evaluations."""

from __future__ import annotations

from research_academy.models import GatekeeperEvaluation, GatekeeperVerdict


def calculate_composite_score(
    relevance: float,
    technical_depth: float,
    practical_value: float,
    source_quality: float,
    commercial_noise: float,
) -> float:
    """
    Computes weighted composite score (0.0 - 10.0):
    - Relevance (35%): Focus on microstructure, funding, latency, orderbook.
    - Technical Depth (35%): Real formulas, order matching mechanics vs surface talk.
    - Practical Value (15%): Real-world risk understanding and execution clarity.
    - Source Quality (15%): Speaker credibility, accuracy, clean presentation.
    - Penalty: If commercial_noise > 5.0, penalizes 0.5 points per excess point.
    Clamped strictly to [0.0, 10.0].
    """
    base = (
        (relevance * 0.35)
        + (technical_depth * 0.35)
        + (practical_value * 0.15)
        + (source_quality * 0.15)
    )
    penalty = max(0.0, (commercial_noise - 5.0) * 0.5) if commercial_noise > 5.0 else 0.0
    final_score = base - penalty
    return max(0.0, min(10.0, round(final_score, 2)))


def determine_verdict(
    composite_score: float,
    commercial_noise: float,
    accept_threshold: float = 7.0,
    review_threshold: float = 5.5,
    max_commercial_noise: float = 5.0,
    is_retail_reference: bool = False,
) -> GatekeeperVerdict:
    """
    Determines Gatekeeper verdict based on calculated composite score and noise limits.
    """
    if commercial_noise > (max_commercial_noise + 1.0):
        return GatekeeperVerdict.REJECT

    if composite_score >= accept_threshold and commercial_noise <= max_commercial_noise:
        return GatekeeperVerdict.ACCEPT

    if is_retail_reference and commercial_noise <= (max_commercial_noise + 1.0):
        return GatekeeperVerdict.REFERENCE_RETAIL_PSYCHOLOGY

    if composite_score < review_threshold:
        return GatekeeperVerdict.REJECT

    return GatekeeperVerdict.REVIEW


def apply_gatekeeper_scoring(evaluation: GatekeeperEvaluation) -> GatekeeperEvaluation:
    """
    Applies programmatic calculation to an evaluation object to ensure math
    is not dependent on LLM hallucination.
    """
    score = calculate_composite_score(
        relevance=evaluation.relevance_score,
        technical_depth=evaluation.technical_depth_score,
        practical_value=evaluation.practical_value_score,
        source_quality=evaluation.source_quality_score,
        commercial_noise=evaluation.commercial_noise_score,
    )
    is_retail = (
        evaluation.decision == GatekeeperVerdict.REFERENCE_RETAIL_PSYCHOLOGY
        or bool(evaluation.sales_translation_bridge and evaluation.sales_translation_bridge.get("client_belief"))
    )
    verdict = determine_verdict(
        composite_score=score,
        commercial_noise=evaluation.commercial_noise_score,
        is_retail_reference=is_retail,
    )
    evaluation.composite_score = score
    evaluation.decision = verdict
    return evaluation

