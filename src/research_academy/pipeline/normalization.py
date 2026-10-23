"""Crypto terminology normalization for auto-generated captions."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple
from research_academy.models import TranscriptSegment

# Common misheard crypto/trading phrases in auto-generated captions
TERM_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\ba mm\b", re.IGNORECASE), "AMM"),
    (re.compile(r"\bsleep\s+page\b", re.IGNORECASE), "slippage"),
    (re.compile(r"\bfound(?:ing)?\s+rate\b", re.IGNORECASE), "funding rate"),
    (re.compile(r"\bfound(?:ing)?\s+right\b", re.IGNORECASE), "funding rate"),
    (re.compile(r"\bbuy\s+bit\b", re.IGNORECASE), "Bybit"),
    (re.compile(r"\bby bit\b", re.IGNORECASE), "Bybit"),
    (re.compile(r"\bdelta\s+natural\b", re.IGNORECASE), "delta neutral"),
    (re.compile(r"\bliquidity\s+pull\b", re.IGNORECASE), "liquidity pool"),
    (re.compile(r"\bspot\s+part\b", re.IGNORECASE), "spot perp"),
    (re.compile(r"\bperp(?:etual)?\s+feature\b", re.IGNORECASE), "perpetual future"),
    (re.compile(r"\bбайненс\b", re.IGNORECASE), "Binance"),
    (re.compile(r"\bбайбит\b", re.IGNORECASE), "Bybit"),
    (re.compile(r"\bдельта\s+натуральн\w*\b", re.IGNORECASE), "дельта-нейтральн"),
    (re.compile(r"\bслиппейдж\b", re.IGNORECASE), "проскальзывание (slippage)"),
]


def normalize_caption_text(text: str) -> str:
    """Applies contextual corrections for common caption transcription artifacts."""
    normalized = text
    for pattern, replacement in TERM_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def normalize_segments(segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
    """
    Returns normalized copies of transcript segments, labeled as quality_status='normalized'.
    """
    normalized_list = []
    for s in segments:
        norm_text = normalize_caption_text(s.text)
        normalized_list.append(
            TranscriptSegment(
                start_seconds=s.start_seconds,
                end_seconds=s.end_seconds,
                text=norm_text,
                language=s.language,
                source_type=s.source_type,
                quality_status="normalized",
            )
        )
    return normalized_list

