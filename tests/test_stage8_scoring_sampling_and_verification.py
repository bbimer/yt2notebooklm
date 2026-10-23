"""Unit tests for Stage 8: Programmatic scoring, multi-window sampling, and evidence verification."""

import pytest
from research_academy.models import (
    ClaimModel,
    ClaimType,
    GatekeeperEvaluation,
    GatekeeperVerdict,
    TranscriptSegment,
    VideoTranscript,
)
from research_academy.pipeline.sampling import sample_transcript_multi_window
from research_academy.pipeline.scoring import (
    apply_gatekeeper_scoring,
    calculate_composite_score,
    determine_verdict,
)
from research_academy.pipeline.verification import ClaimVerifier


def test_calculate_composite_score_formula_and_penalty():
    # 1. Clean high quality video: relevance=9, depth=9, practical=8, quality=8, noise=2
    # base = (9*0.35 + 9*0.35 + 8*0.15 + 8*0.15) = 3.15 + 3.15 + 1.2 + 1.2 = 8.7
    # penalty = 0 (noise <= 5)
    score = calculate_composite_score(9.0, 9.0, 8.0, 8.0, 2.0)
    assert score == 8.70

    # 2. Commercial spam video: relevance=8, depth=7, practical=6, quality=6, noise=9.0
    # base = (8*0.35 + 7*0.35 + 6*0.15 + 6*0.15) = 2.8 + 2.45 + 0.9 + 0.9 = 7.05
    # penalty = (9.0 - 5.0) * 0.5 = 2.0
    # score = 7.05 - 2.0 = 5.05
    score_spam = calculate_composite_score(8.0, 7.0, 6.0, 6.0, 9.0)
    assert score_spam == 5.05

    # 3. Clamping to [0.0, 10.0]
    assert calculate_composite_score(1.0, 1.0, 1.0, 1.0, 10.0) == 0.0
    assert calculate_composite_score(10.0, 10.0, 10.0, 10.0, 1.0) == 10.0


def test_determine_verdict():
    # ACCEPT: score >= 7.0 and noise <= 5.0
    assert determine_verdict(8.0, 2.0) == GatekeeperVerdict.ACCEPT

    # REJECT: score < 5.5
    assert determine_verdict(5.2, 3.0) == GatekeeperVerdict.REJECT

    # REJECT: excessive noise > 6.0
    assert determine_verdict(8.5, 7.0) == GatekeeperVerdict.REJECT

    # REVIEW: in-between score
    assert determine_verdict(6.2, 4.0) == GatekeeperVerdict.REVIEW

    # REFERENCE_RETAIL_PSYCHOLOGY: low technical score but useful retail reference
    assert determine_verdict(4.5, 3.0, is_retail_reference=True) == GatekeeperVerdict.REFERENCE_RETAIL_PSYCHOLOGY


def test_apply_gatekeeper_scoring():
    raw_eval = GatekeeperEvaluation(
        relevance_score=8.5,
        technical_depth_score=8.0,
        practical_value_score=8.0,
        source_quality_score=7.5,
        commercial_noise_score=2.0,
        confidence_score=0.9,
    )
    scored_eval = apply_gatekeeper_scoring(raw_eval)
    assert scored_eval.composite_score is not None
    assert scored_eval.composite_score >= 7.5
    assert scored_eval.decision == GatekeeperVerdict.ACCEPT


def test_sample_transcript_multi_window_short():
    segments = [
        TranscriptSegment(start_seconds=0.0, end_seconds=5.0, text="Intro to market microstructure", language="en"),
        TranscriptSegment(start_seconds=6.0, end_seconds=12.0, text="Order books and bids", language="en"),
    ]
    t = VideoTranscript(video_id="test1", language="en", segments=segments, word_count=8)
    sample = sample_transcript_multi_window(t, max_words=50)

    assert "[00:00] Intro to market microstructure" in sample
    assert "[00:06] Order books and bids" in sample


def test_sample_transcript_multi_window_long_preserves_three_windows():
    # Create 100 segments with timestamps
    segments = [
        TranscriptSegment(
            start_seconds=float(i * 10),
            end_seconds=float(i * 10 + 9),
            text=f"Technical trading paragraph number {i} discussing funding rate mechanics.",
            language="en",
        )
        for i in range(100)
    ]
    t = VideoTranscript(video_id="test_long", language="en", segments=segments, word_count=800)
    sample = sample_transcript_multi_window(t, max_words=100)

    assert "### [ОКНО 1: ВВЕДЕНИЕ И ПОСТАНОВКА ПРОБЛЕМЫ" in sample
    assert "### [ОКНО 2: ЯДРО, МАТЕМАТИКА И МЕХАНИКА" in sample
    assert "### [ОКНО 3: ВЫВОДЫ, ЗАКЛЮЧЕНИЕ И ДИСКЛЕЙМЕРЫ" in sample
    assert "[00:00]" in sample


def test_claim_verifier_catches_fake_timestamps_and_absent_quotes():
    verifier = ClaimVerifier()
    segments = [
        TranscriptSegment(start_seconds=10.0, end_seconds=20.0, text="Arbitrageurs capture delta neutral funding rate spreads across venues.", language="en"),
        TranscriptSegment(start_seconds=30.0, end_seconds=40.0, text="Hedging reduces spot directional risk.", language="en"),
    ]
    transcript = VideoTranscript(video_id="v1", language="en", segments=segments, word_count=20)

    # 1. Claim with non-existent timestamp beyond duration (e.g. 5000s in 60s video)
    fake_ts_claim = ClaimModel(
        statement="Funding is collected every 8 hours.",
        source_url="https://youtube.com/watch?v=v1",
        timestamp_seconds=5000.0,
        timestamp_formatted="83:20",
        quote_text="Funding is collected every 8 hours.",
    )
    res_fake_ts = verifier.verify_claim(fake_ts_claim, transcript=transcript, max_duration_seconds=60)
    assert res_fake_ts.verification_status == "unverified"
    assert "выходит за рамки видео" in res_fake_ts.allowed_sales_phrasing

    # 2. Claim with quote that does not exist in transcript
    hallucinated_quote_claim = ClaimModel(
        statement="We make millions on secret moonbot algorithm.",
        source_url="https://youtube.com/watch?v=v1",
        timestamp_seconds=12.0,
        timestamp_formatted="00:12",
        quote_text="Extremely secret moonbot algorithm that does not exist in text.",
    )
    res_hallucinated = verifier.verify_claim(hallucinated_quote_claim, transcript=transcript, max_duration_seconds=60)
    assert res_hallucinated.verification_status == "unverified"
    assert "не обнаружена в транскрипте" in res_hallucinated.allowed_sales_phrasing

    # 3. Forbidden toxic guarantee
    toxic_claim = ClaimModel(
        statement="Это 100% гарантированная прибыль без рисков.",
        source_url="https://youtube.com/watch?v=v1",
        timestamp_seconds=15.0,
        timestamp_formatted="00:15",
        quote_text="100% гарантированная прибыль",
    )
    res_toxic = verifier.verify_claim(toxic_claim, transcript=transcript, max_duration_seconds=60)
    assert res_toxic.verification_status == "disputed"
    assert "ЗАПРЕЩЕНО" in res_toxic.allowed_sales_phrasing

