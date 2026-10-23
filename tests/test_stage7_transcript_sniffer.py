"""Tests for Transcript Sniffer & Semi-Manual Audit Prompt Builder."""

import pytest
from research_academy.models import TranscriptSegment, VideoTranscript
from research_academy.pipeline.transcript_sniffer import (
    TranscriptSniffer,
    build_semi_manual_audit_prompt,
    calculate_transcript_telemetry,
    extract_youtube_video_id,
)
from research_academy.providers.base import TranscriptProvider


class MockSnifferTranscriptProvider(TranscriptProvider):
    def __init__(self, transcripts_map=None):
        self.transcripts_map = transcripts_map or {}

    def get_transcript(self, video_id: str, languages=None) -> VideoTranscript:
        if video_id in self.transcripts_map:
            return self.transcripts_map[video_id]
        return VideoTranscript(
            video_id=video_id,
            language="ru",
            has_subtitles=False,
            fetch_status="NOT_FOUND",
            error_message="Subtitles not available",
        )


def test_extract_youtube_video_id():
    assert extract_youtube_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ?t=42") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://example.com/not-youtube") is None


def test_calculate_transcript_telemetry():
    sample_text = (
        "Сегодня мы разберем стакан ордеров и сведение ордеров на бирже. "
        "Проскальзывание и комиссии maker taker играют ключевую роль в арбитраже фандинга. "
        "Также мы предупреждаем: не ведитесь на связка дня и сигналы в тг с обещанием 100% прибыль."
    )
    seg = TranscriptSegment(start_seconds=0.0, end_seconds=30.0, text=sample_text)
    transcript = VideoTranscript(
        video_id="test_vid_telemetry",
        language="ru",
        segments=[seg],
        full_raw_text=sample_text,
        full_normalized_text=sample_text,
        word_count=len(sample_text.split()),
        has_subtitles=True,
    )

    telemetry = calculate_transcript_telemetry(transcript)
    assert "стакан ордеров" in telemetry["trader_markers"]
    assert "maker/taker комиссии" in telemetry["trader_markers"]
    assert "проскальзывание (slippage)" in telemetry["trader_markers"]
    assert "«связка» (инфоцыганство)" in telemetry["scam_markers"]
    assert "гарантии прибыли / безрисковость" in telemetry["scam_markers"]
    assert telemetry["word_count"] > 0


def test_build_semi_manual_audit_prompt():
    sample_text = "Разбор механики фандинга и дельта-нейтрального хеджа спот-перп."
    seg = TranscriptSegment(start_seconds=0.0, end_seconds=20.0, text=sample_text)
    transcript = VideoTranscript(
        video_id="test_vid_prompt",
        language="ru",
        segments=[seg],
        full_raw_text=sample_text,
        full_normalized_text=sample_text,
        word_count=10,
        has_subtitles=True,
    )
    telemetry = {
        "word_count": 10,
        "est_duration_minutes": 0.1,
        "trader_markers": ["фандинг", "дельта-нейтральность"],
        "scam_markers": [],
        "technical_density": 200.0,
    }

    prompt = build_semi_manual_audit_prompt(
        video_title="Funding Rate Masterclass",
        video_url="https://youtube.com/watch?v=test_vid_prompt",
        channel_title="Quant Desk",
        transcript=transcript,
        telemetry=telemetry,
    )

    assert "Funding Rate Masterclass" in prompt
    assert "ЭТАП 1 — ОЦЕНКА ПО КРИТЕРИЯМ (Шкала 1.0 – 5.0)" in prompt
    assert "Техническая глубина" in prompt
    assert "ИТОГОВЫЙ БАЛЛ:" in prompt
    assert "ACCEPTED_CORE" in prompt
    assert "REJECT_FOR_MODULE" in prompt
    assert "МОСТ ДЛЯ СЕЙЛЗ-КОМАНДЫ" in prompt


def test_transcript_sniffer_success(tmp_path):
    sample_text = "Технический разбор пулов ликвидности AMM и стакана ордеров."
    seg = TranscriptSegment(start_seconds=0.0, end_seconds=30.0, text=sample_text)
    transcript = VideoTranscript(
        video_id="abc123xyz89",
        language="ru",
        segments=[seg],
        full_raw_text=sample_text,
        full_normalized_text=sample_text,
        word_count=10,
        has_subtitles=True,
    )

    mock_provider = MockSnifferTranscriptProvider({"abc123xyz89": transcript})
    sniffer = TranscriptSniffer(transcript_provider=mock_provider, output_dir=tmp_path)

    ok, prompt = sniffer.inspect_and_build_prompt("https://youtu.be/abc123xyz89", copy_to_clipboard=False)
    assert ok is True
    assert "abc123xyz89" in prompt
    assert "ЭТАП 2 — ИТОГОВЫЙ ВЕРДИКТ" in prompt
    assert "[AUDIT #1" in prompt
    # Check that file was created in tmp_path
    saved_file = tmp_path / "audit_001_abc123xyz89.txt"
    assert saved_file.exists()
    assert "Технический разбор" in saved_file.read_text(encoding="utf-8")
