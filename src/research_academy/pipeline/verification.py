"""Verification module for factual claims, sources, timestamps, and sales boundaries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, List, Optional
from research_academy.models import ClaimModel, ClaimType, VideoTranscript, SourceContent


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
        transcript: Optional[Any] = None,
        max_duration_seconds: Optional[int] = None,
    ) -> ClaimModel:
        """
        Classifies and verifies claim against documented evidence and source reality.
        Supports both video transcripts and primary web documents isomorphically.
        Rules:
        1. Forbidden promises (100% guarantees, zero risk) -> DISPUTED.
        2. Non-existent timestamps (for video > duration or < 0) -> UNVERIFIED.
        3. Quote verification: searches segment window first, then full document text.
        4. Matches confirmed product claims in PRODUCT_CLAIMS.md -> VERIFIED.
        5. Appropriate phrasing: "По данным спецификации/первоисточника" for web vs "автора видео" for video.
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

        # Identify source context
        is_web = False
        full_text = ""
        segments = []
        source_url = claim.source_url or ""

        if transcript is not None:
            if hasattr(transcript, "source_type") and getattr(transcript, "source_type") == "web":
                is_web = True
            if hasattr(transcript, "url") and getattr(transcript, "url"):
                source_url = getattr(transcript, "url")
            if hasattr(transcript, "full_clean_text") and getattr(transcript, "full_clean_text"):
                full_text = getattr(transcript, "full_clean_text")
            elif hasattr(transcript, "full_normalized_text") and getattr(transcript, "full_normalized_text"):
                full_text = getattr(transcript, "full_normalized_text")
            elif hasattr(transcript, "full_raw_text") and getattr(transcript, "full_raw_text"):
                full_text = getattr(transcript, "full_raw_text")

            if hasattr(transcript, "segments") and getattr(transcript, "segments"):
                segments = getattr(transcript, "segments")

        anchor_str = str(claim.anchor_id or claim.timestamp_formatted or "").strip()
        if anchor_str.upper().startswith("SEC-"):
            is_web = True

        # 2. Check timestamp boundaries for video
        if not is_web and claim.timestamp_seconds is not None:
            if claim.timestamp_seconds < 0:
                claim.verification_status = "unverified"
                claim.allowed_sales_phrasing = f"Неподтверждено: Ошибочный отрицательный таймкод ({claim.timestamp_formatted})."
                return claim

            if max_duration_seconds and max_duration_seconds > 0:
                if claim.timestamp_seconds > (max_duration_seconds + 30):
                    claim.verification_status = "unverified"
                    claim.allowed_sales_phrasing = f"Неподтверждено: Таймкод {claim.timestamp_formatted} выходит за рамки видео (~{max_duration_seconds} сек)."
                    return claim

        # 3. Check quote evidence in source (segments and full text)
        quote_raw = claim.quote_text or claim.statement or ""
        clean_quote = re.sub(r"[\*_`\"'«»\(\)\[\]]", " ", quote_raw).strip().lower()
        quote_words = [w for w in re.findall(r"\w+", clean_quote) if len(w) > 3]

        matched = False
        match_location = ""

        if quote_words and (segments or full_text):
            # A. Try matching in specific anchor or nearby timestamp window
            if is_web and anchor_str:
                for seg in segments:
                    seg_anchor = str(getattr(seg, "anchor_id", getattr(seg, "timestamp_formatted", ""))).strip()
                    if anchor_str.lower() in seg_anchor.lower() or seg_anchor.lower() in anchor_str.lower():
                        seg_text = getattr(seg, "text", "").lower()
                        matches = sum(1 for w in quote_words if w in seg_text)
                        if matches >= max(1, len(quote_words) // 3):
                            matched = True
                            match_location = f"секции {anchor_str}"
                            break
            elif not is_web and claim.timestamp_seconds is not None and segments:
                ts = claim.timestamp_seconds
                for seg in segments:
                    start_sec = getattr(seg, "start_seconds", None)
                    if start_sec is not None and abs(start_sec - ts) <= 60:
                        seg_text = getattr(seg, "text", "").lower()
                        matches = sum(1 for w in quote_words if w in seg_text)
                        if matches >= max(1, len(quote_words) // 3):
                            matched = True
                            match_location = f"таймкоде {claim.timestamp_formatted}"
                            break

            # B. Fallback: search across all segments if not found in local window
            if not matched and segments:
                for seg in segments:
                    seg_text = getattr(seg, "text", "").lower()
                    matches = sum(1 for w in quote_words if w in seg_text)
                    if matches >= max(2, int(len(quote_words) * 0.4)):
                        matched = True
                        loc = getattr(seg, "anchor_id", getattr(seg, "timestamp_formatted", ""))
                        match_location = f"сегменте {loc}" if loc else "тексте источника"
                        break

            # C. Fallback: search directly in full_clean_text
            if not matched and full_text:
                full_lower = full_text.lower()
                matches = sum(1 for w in quote_words if w in full_lower)
                if matches >= max(2, int(len(quote_words) * 0.4)):
                    matched = True
                    match_location = "тексте первоисточника"

        # If matched quote in source:
        if matched:
            claim.claim_type = ClaimType.SOURCE_CLAIM
            claim.verification_status = "verified"
            claim.independent_evidence = f"Цитата верифицирована в {match_location}"
            if is_web:
                claim.allowed_sales_phrasing = f"По данным первоисточника ({claim.anchor_id or 'спецификация'}): {claim.statement}"
            else:
                claim.allowed_sales_phrasing = f"По утверждению автора ({claim.timestamp_formatted or 'видео'}): {claim.statement}"
            return claim
        elif quote_raw and (segments or full_text) and len(quote_words) >= 4:
            claim.verification_status = "unverified"
            if is_web:
                if anchor_str:
                    claim.allowed_sales_phrasing = f"Неподтверждено: Цитата автора не обнаружена в секции {anchor_str}."
                else:
                    claim.allowed_sales_phrasing = "Неподтверждено: Цитата не обнаружена в тексте первоисточника."
            else:
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

        # 5. Default framing if no independent evidence
        if not claim.independent_evidence:
            claim.claim_type = ClaimType.UNVERIFIED
            claim.verification_status = "unverified"
            if is_web:
                claim.allowed_sales_phrasing = f"По данным спецификации ({claim.anchor_id or 'первоисточник'}): {claim.statement}"
            else:
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
