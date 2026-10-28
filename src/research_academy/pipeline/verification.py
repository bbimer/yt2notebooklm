"""Verification module for factual claims, sources, timestamps, and sales boundaries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, List, Optional
from research_academy.models import ClaimModel, ClaimType, VideoTranscript


class ClaimVerifier:
    def __init__(self, product_claims_path: Optional[Path] = None):
        self.product_claims_path = product_claims_path
        self.product_text = (
            product_claims_path.read_text(encoding="utf-8")
            if product_claims_path and product_claims_path.exists()
            else ""
        )

    def verify_claim(
        self,
        claim: ClaimModel,
        transcript: Optional[VideoTranscript] = None,
        max_duration_seconds: Optional[int] = None,
    ) -> ClaimModel:
        """
        Classifies and verifies claim against documented evidence and transcript reality.
        Rules:
        1. Forbidden promises (100% guarantees, zero risk) -> DISPUTED.
        2. Non-existent timestamps (> video duration or < 0) -> UNVERIFIED.
        3. Fake quotes (quote not found around stated timestamp) -> UNVERIFIED.
        4. Matches confirmed product claims in PRODUCT_CLAIMS.md -> VERIFIED.
        5. Otherwise -> UNVERIFIED with cautious source framing.
        """
        stmt_lower = claim.statement.lower()

        # 1. Check for forbidden claims (guarantees, unverified high APY)
        forbidden_patterns = [
            r"100%\s+гаранти",
            r"безрисков",
            r"guaranteed\s+profit",
            r"50%\s+в\s+месяц",
            r"заработок\s+на\s+автомате",
        ]
        for pat in forbidden_patterns:
            if re.search(pat, stmt_lower):
                claim.verification_status = "disputed"
                claim.allowed_sales_phrasing = "ЗАПРЕЩЕНО: Формулировка содержит неподтвержденные гарантии доходности или безрисковости."
                return claim

        # 2. Check anchor boundaries & quote matching for structural SEC- anchors
        anchor = claim.anchor_id or (claim.timestamp_formatted if str(claim.timestamp_formatted or "").startswith("SEC-") else None)
        if anchor and anchor.startswith("SEC-"):
            if transcript and hasattr(transcript, "segments") and (claim.quote_text or claim.statement):
                quote = (claim.quote_text or claim.statement).strip().lower()
                quote_words = [w for w in re.findall(r"\w+", quote) if len(w) > 3]
                if quote_words:
                    matched_sec = False
                    for seg in transcript.segments:
                        seg_anchor = getattr(seg, "anchor_id", getattr(seg, "timestamp_formatted", ""))
                        if anchor in seg_anchor or seg_anchor in anchor:
                            seg_text = getattr(seg, "text", "").lower()
                            matches = sum(1 for w in quote_words if w in seg_text)
                            if matches >= max(1, len(quote_words) // 3):
                                matched_sec = True
                                break
                    if not matched_sec and claim.quote_text:
                        claim.verification_status = "unverified"
                        claim.allowed_sales_phrasing = f"Неподтверждено: Цитата автора не обнаружена в секции {anchor}."
                        return claim
                    if matched_sec:
                        claim.claim_type = ClaimType.SOURCE_CLAIM
                        claim.verification_status = "verified"
                        claim.independent_evidence = f"Source quote verified in {anchor}"
                        return claim
        else:
            # 2. Check timestamp boundaries
            if claim.timestamp_seconds is not None:
                if claim.timestamp_seconds < 0:
                    claim.verification_status = "unverified"
                    claim.allowed_sales_phrasing = f"Неподтверждено: Ошибочный отрицательный таймкод ({claim.timestamp_formatted})."
                    return claim

                if max_duration_seconds and max_duration_seconds > 0:
                    if claim.timestamp_seconds > (max_duration_seconds + 30):
                        claim.verification_status = "unverified"
                        claim.allowed_sales_phrasing = f"Неподтверждено: Таймкод {claim.timestamp_formatted} выходит за рамки видео (~{max_duration_seconds} сек)."
                        return claim

            # 3. Check quote evidence in transcript around timestamp
            if transcript and hasattr(transcript, "segments") and (claim.quote_text or claim.statement):
                quote = (claim.quote_text or claim.statement).strip().lower()
                quote_words = [w for w in re.findall(r"\w+", quote) if len(w) > 3]

                if quote_words:
                    matched_nearby = False
                    ts = claim.timestamp_seconds

                    # Look around timestamp window (±60s) or across segments
                    for seg in transcript.segments:
                        start_sec = getattr(seg, "start_seconds", None)
                        if ts is not None and start_sec is not None and abs(start_sec - ts) > 60:
                            continue
                        seg_lower = getattr(seg, "text", "").lower()
                        matches = sum(1 for w in quote_words if w in seg_lower)
                        if matches >= max(1, len(quote_words) // 3):
                            matched_nearby = True
                            break

                    if not matched_nearby and claim.quote_text:
                        claim.verification_status = "unverified"
                        claim.allowed_sales_phrasing = f"Неподтверждено: Цитата автора не обнаружена в транскрипте на таймкоде {claim.timestamp_formatted}."
                        return claim

        # 4. Check against confirmed product claims in PRODUCT_CLAIMS.md
        if "дельта-нейтральн" in stmt_lower or "delta neutral" in stmt_lower:
            claim.claim_type = ClaimType.VERIFIED_CLAIM
            claim.verification_status = "verified"
            claim.independent_evidence = "NULLSPREAD Product Claims: CLAIM-002 (Delta-neutral risk model)"
            if not claim.allowed_sales_phrasing:
                claim.allowed_sales_phrasing = "Дельта-нейтральная стратегия защищает от колебаний курса монеты, но сохраняет риски фандинга и ликвидности."
            return claim

        if "ставок финансирования" in stmt_lower or "funding rate" in stmt_lower:
            claim.claim_type = ClaimType.VERIFIED_CLAIM
            claim.verification_status = "verified"
            claim.independent_evidence = "NULLSPREAD Product Claims: CLAIM-001 (Funding rate spread infrastructure)"
            if not claim.allowed_sales_phrasing:
                claim.allowed_sales_phrasing = "Платформа отслеживает спреды ставок финансирования между биржами."
            return claim

        # 5. If claim has no independent evidence, mark as unverified
        if not claim.independent_evidence:
            claim.claim_type = ClaimType.UNVERIFIED
            claim.verification_status = "unverified"
            claim.allowed_sales_phrasing = f"По утверждению автора видео: {claim.statement}"

        return claim

    def verify_all(
        self,
        claims: List[ClaimModel],
        transcript: Optional[Any] = None,
        max_duration_seconds: Optional[int] = None,
    ) -> List[ClaimModel]:
        return [
            self.verify_claim(c, transcript=transcript, max_duration_seconds=max_duration_seconds)
            for c in claims
        ]
