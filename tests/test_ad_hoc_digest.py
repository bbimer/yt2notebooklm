"""Unit tests for Ad-Hoc YouTube Digest and Prompt Builder."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from research_academy.cli import cli
from research_academy.models import TranscriptSegment, VideoTranscript
from research_academy.pipeline.ad_hoc_digest import (
    AdHocDigestGenerator,
    VideoDetails,
    aggregate_transcript_segments,
    find_latest_digest,
    format_duration,
    get_standalone_prompt,
    slugify,
    wrap_digest_with_prompt,
)
from research_academy.providers.base import TranscriptProvider


class MockDigestTranscriptProvider(TranscriptProvider):
    def __init__(self, segments=None, has_subtitles=True):
        self.segments = segments or [
            TranscriptSegment(text="Hello world,", start_seconds=0.0, end_seconds=2.5),
            TranscriptSegment(text="welcome to this deep dive.", start_seconds=2.5, end_seconds=5.5),
            TranscriptSegment(text="We are discussing decentralized systems.", start_seconds=5.5, end_seconds=9.5),
            TranscriptSegment(text="Let us jump into chapter one.", start_seconds=85.0, end_seconds=90.0),
            TranscriptSegment(text="Here are the architecture specifics.", start_seconds=90.0, end_seconds=94.0),
        ]
        self.has_subtitles = has_subtitles

    def get_transcript(self, video_id: str, languages=None) -> VideoTranscript:
        if not self.has_subtitles:
            return VideoTranscript(
                video_id=video_id,
                language="ru",
                has_subtitles=False,
                fetch_status="ERROR",
                error_message="No subtitles",
            )
        return VideoTranscript(
            video_id=video_id,
            language="ru",
            has_subtitles=True,
            fetch_status="OK",
            segments=self.segments,
            full_normalized_text=" ".join(s.text for s in self.segments),
        )


def test_slugify():
    assert slugify("Coins VS Tokens: What's the Difference?") == "coins_vs_tokens_whats_the_difference"
    assert slugify("Тест русских символов и знаков!!!") == "тест_русских_символов_и_знаков"


def test_format_duration():
    assert format_duration(45) == "00:45"
    assert format_duration(185) == "03:05"
    assert format_duration(3665) == "1ч 1м 5с"
    assert format_duration(0) == "Не указана"


def test_aggregate_transcript_segments():
    segments = [
        TranscriptSegment(text="phrase one", start_seconds=0.0, end_seconds=2.0),
        TranscriptSegment(text="phrase two", start_seconds=2.0, end_seconds=4.0),
        TranscriptSegment(text="phrase three", start_seconds=4.0, end_seconds=6.0),
        TranscriptSegment(text="phrase next block", start_seconds=80.0, end_seconds=82.0),
    ]
    # Target duration 75s -> first 3 should merge into [00:00], 4th into [01:20]
    paragraphs = aggregate_transcript_segments(segments, target_duration_sec=75.0, max_words=100)
    assert len(paragraphs) == 2
    assert paragraphs[0][0] == "00:00"
    assert "Phrase one phrase two phrase three" in paragraphs[0][1]
    assert paragraphs[1][0] == "01:20"
    assert "Phrase next block" in paragraphs[1][1]


def test_build_markdown_disk_and_clipboard_payload(tmp_path: Path):
    mock_provider = MockDigestTranscriptProvider()
    generator = AdHocDigestGenerator(transcript_provider=mock_provider, default_output_dir=tmp_path)

    details = VideoDetails(
        video_id="test1234567",
        title="Test Architecture Video",
        channel="Quant Tech",
        duration_sec=300,
        url="https://www.youtube.com/watch?v=test1234567",
        chapters=[
            {"title": "Introduction", "start_time": 0, "timestamp": "00:00"},
            {"title": "Deep Dive", "start_time": 120, "timestamp": "02:00"},
        ],
    )
    transcript = mock_provider.get_transcript("test1234567")
    paragraphs = aggregate_transcript_segments(transcript.segments)

    # 1. Test disk file content: MUST be clean knowledge-base Markdown (Option A)
    # Zero prompt-builder blocks to prevent RAG/NotebookLM vector contamination
    disk_content = generator.build_markdown_file_content(
        details=details,
        transcript=transcript,
        paragraphs=paragraphs,
        word_count=50,
        read_time_min=1,
    )
    assert "# Test Architecture Video" in disk_content
    assert "Quant Tech" in disk_content
    assert "Introduction" in disk_content
    assert "Deep Dive" in disk_content
    assert "ПАСПОРТ ВИДЕО" in disk_content
    assert "СТРУКТУРИРОВАННЫЙ ТРАНСКРИПТ РОЛИКА" in disk_content
    assert "[00:00]" in disk_content
    # MUST NOT contain prompt builder templates on disk:
    assert "Executive Summary" not in disk_content
    assert "Actionable Tutorial" not in disk_content
    assert "Bullshit & Scam Filter" not in disk_content
    assert "ПРОМПТ-БИЛДЕР" not in disk_content

    # 2. Test in-memory prompt wrapping via wrap_digest_with_prompt
    wrapped_summary = wrap_digest_with_prompt(disk_content, mode="summary")
    assert "Executive Summary" in wrapped_summary
    assert "СОДЕРЖИМОЕ МАТЕРИАЛА" in wrapped_summary
    assert "# Test Architecture Video" in wrapped_summary

    wrapped_audit = wrap_digest_with_prompt(disk_content, mode="audit")
    assert "Bullshit & Scam Filter" in wrapped_audit
    assert "СОДЕРЖИМОЕ МАТЕРИАЛА" in wrapped_audit
    assert "Executive Summary" not in wrapped_audit

    wrapped_tutorial = wrap_digest_with_prompt(disk_content, mode="tutorial")
    assert "Actionable Tutorial" in wrapped_tutorial
    assert "СОДЕРЖИМОЕ МАТЕРИАЛА" in wrapped_tutorial

    # 3. Test clipboard payload: MUST contain ONLY the 1 active prompt, passport, and transcript
    clip_summary = generator.build_clipboard_payload(details, paragraphs, mode="summary")
    assert "Executive Summary" in clip_summary
    assert "Actionable Tutorial" not in clip_summary  # Should not be in summary clipboard
    assert "Bullshit & Scam Filter" not in clip_summary
    assert "Test Architecture Video" in clip_summary
    assert "Quant Tech" in clip_summary
    assert "Introduction" in clip_summary
    assert "[00:00]" in clip_summary

    clip_audit = generator.build_clipboard_payload(details, paragraphs, mode="audit")
    assert "Bullshit & Scam Filter" in clip_audit
    assert "Executive Summary" not in clip_audit


def test_process_url_success(tmp_path: Path):
    mock_provider = MockDigestTranscriptProvider()
    generator = AdHocDigestGenerator(transcript_provider=mock_provider, default_output_dir=tmp_path)

    with patch.object(
        generator,
        "fetch_video_details",
        return_value=VideoDetails(
            video_id="abc12345678",
            title="Crypto Economics 101",
            channel="DeFi Research",
            duration_sec=600,
            url="https://www.youtube.com/watch?v=abc12345678",
            chapters=[{"title": "Basics", "start_time": 0, "timestamp": "00:00"}],
        ),
    ), patch("pyperclip.copy") as mock_copy, patch(
        "research_academy.pipeline.ad_hoc_digest.play_chime_success"
    ) as mock_chime:
        res = generator.process_url("https://www.youtube.com/watch?v=abc12345678", output_dir=tmp_path, mode="summary")

        assert res.error is None
        assert res.video_id == "abc12345678"
        assert res.title == "Crypto Economics 101"
        assert res.channel == "DeFi Research"
        assert res.markdown_path.exists()
        assert res.clipboard_copied is True
        mock_copy.assert_called_once()
        mock_chime.assert_called_once()


def test_process_url_no_subtitles(tmp_path: Path):
    mock_provider = MockDigestTranscriptProvider(has_subtitles=False)
    generator = AdHocDigestGenerator(transcript_provider=mock_provider, default_output_dir=tmp_path)

    with patch.object(
        generator,
        "fetch_video_details",
        return_value=VideoDetails(
            video_id="no_subs_vid",
            title="No Subtitles Video",
            channel="Unknown",
            duration_sec=100,
            url="https://www.youtube.com/watch?v=no_subs_vid",
        ),
    ), patch("research_academy.pipeline.ad_hoc_digest.play_chime_error") as mock_err_chime:
        res = generator.process_url("https://www.youtube.com/watch?v=no_subs_vid", output_dir=tmp_path)
        assert res.error is not None
        assert "Субтитры недоступны" in res.error
        mock_err_chime.assert_called_once()


def test_cli_digest_command(tmp_path: Path):
    runner = CliRunner()

    with patch(
        "research_academy.pipeline.ad_hoc_digest.AdHocDigestGenerator.process_url"
    ) as mock_proc:
        from research_academy.pipeline.ad_hoc_digest import DigestResult
        mock_proc.return_value = DigestResult(
            video_id="sample_vid_1",
            title="Sample Title",
            channel="Test Channel",
            duration_str="10:00",
            word_count=500,
            reading_time_min=2,
            markdown_path=tmp_path / "sample.md",
            clipboard_copied=True,
            mode_used="summary",
            chapters_count=2,
        )

        res = runner.invoke(cli, ["digest", "https://youtu.be/sample_vid_1", "-o", str(tmp_path)])
        assert res.exit_code == 0
        assert "Sample Title" in res.output
        assert "Test Channel" in res.output
        assert "Готовый запрос скопирован в буфер обмена" in res.output


def test_cli_digest_from_clipboard(tmp_path: Path):
    runner = CliRunner()

    with patch("pyperclip.paste", return_value="https://www.youtube.com/watch?v=sample_clip_vid"), patch(
        "research_academy.pipeline.ad_hoc_digest.AdHocDigestGenerator.process_url"
    ) as mock_proc:
        from research_academy.pipeline.ad_hoc_digest import DigestResult
        mock_proc.return_value = DigestResult(
            video_id="sample_clip_vid",
            title="Clip Title",
            channel="Clip Channel",
            duration_str="05:00",
            word_count=300,
            reading_time_min=1,
            markdown_path=tmp_path / "clip.md",
            clipboard_copied=True,
            mode_used="audit",
            chapters_count=0,
        )

        res = runner.invoke(cli, ["digest", "--from-clipboard", "--mode", "audit", "-o", str(tmp_path)])
        assert res.exit_code == 0
        assert "Clip Title" in res.output


def test_find_latest_digest(tmp_path: Path):
    assert find_latest_digest(tmp_path) is None

    # Create older file
    f1 = tmp_path / "2026-10-30_vid1_older.md"
    f1.write_text("older content", encoding="utf-8")

    # Create newer file
    f2 = tmp_path / "2026-10-31_vid2_newer.md"
    f2.write_text("newer content", encoding="utf-8")

    latest = find_latest_digest(tmp_path)
    assert latest is not None
    assert latest.name == "2026-10-31_vid2_newer.md"


def test_cli_latest_digest_command(tmp_path: Path):
    runner = CliRunner()

    # Empty directory
    res_empty = runner.invoke(cli, ["latest-digest", "-d", str(tmp_path)])
    assert res_empty.exit_code != 0
    assert "не найдены" in res_empty.output

    # With file: default call copies path (no \r\n)
    sample = tmp_path / "2026-10-31_vid_sample.md"
    sample.write_text("# Clean Digest\n\nVideo transcript content here.", encoding="utf-8")

    with patch("pyperclip.copy") as mock_copy, patch(
        "research_academy.pipeline.ad_hoc_digest.play_chime_success"
    ) as mock_chime:
        res = runner.invoke(cli, ["latest-digest", "-d", str(tmp_path)])
        assert res.exit_code == 0
        assert "2026-10-31_vid_sample.md" in res.output
        assert "Путь скопирован в буфер обмена" in res.output
        mock_copy.assert_called_once_with(str(sample.resolve()))
        # Verify no trailing newline in copied path
        copied_path = mock_copy.call_args[0][0]
        assert not copied_path.endswith("\n")
        assert not copied_path.endswith("\r")
        mock_chime.assert_called_once()

    # With -m audit: in-memory prompt wrapping without touching disk file!
    with patch("pyperclip.copy") as mock_copy, patch(
        "research_academy.pipeline.ad_hoc_digest.play_chime_success"
    ) as mock_chime:
        res_audit = runner.invoke(cli, ["latest-digest", "-d", str(tmp_path), "-m", "audit"])
        assert res_audit.exit_code == 0
        assert "Дайджест обернут в промпт (audit) и скопирован в буфер обмена" in res_audit.output
        mock_copy.assert_called_once()
        copied_payload = mock_copy.call_args[0][0]
        assert "Bullshit & Scam Filter" in copied_payload
        assert "Video transcript content here." in copied_payload
        assert "[РЕЖИМ ОБРАБОТКИ:" in copied_payload
        mock_chime.assert_called_once()
        # Verify disk file remained 100% clean and was NOT modified
        disk_text = sample.read_text(encoding="utf-8")
        assert "Bullshit & Scam Filter" not in disk_text
        assert disk_text == "# Clean Digest\n\nVideo transcript content here."

    # With -f custom file and -m tutorial
    custom_file = tmp_path / "custom_digest.md"
    custom_file.write_text("# Custom Tutorial Digest\n\nSteps to run.", encoding="utf-8")
    with patch("pyperclip.copy") as mock_copy, patch(
        "research_academy.pipeline.ad_hoc_digest.play_chime_success"
    ) as mock_chime:
        res_custom = runner.invoke(cli, ["latest-digest", "-f", str(custom_file), "-m", "tutorial"])
        assert res_custom.exit_code == 0
        assert "tutorial" in res_custom.output
        copied_payload = mock_copy.call_args[0][0]
        assert "Actionable Tutorial" in copied_payload
        assert "Steps to run." in copied_payload
        assert custom_file.read_text(encoding="utf-8") == "# Custom Tutorial Digest\n\nSteps to run."


def test_get_standalone_prompt():
    title_sum, prompt_sum = get_standalone_prompt("summary")
    assert "Executive Summary" in title_sum
    assert "прикрепленный(е) материал(ы)" in prompt_sum

    title_audit, prompt_audit = get_standalone_prompt("audit")
    assert "Bullshit & Scam" in title_audit
    assert "ОЦЕНКА ПЛОТНОСТИ ПОЛЬЗЫ" in prompt_audit

    title_comp, prompt_comp = get_standalone_prompt("compare")
    assert "Кросс-анализ" in title_comp
    assert "СВОДНАЯ СУТЬ И КОНСЕНСУС" in prompt_comp

    # Alias multi -> compare
    title_multi, prompt_multi = get_standalone_prompt("multi")
    assert title_multi == title_comp
    assert prompt_multi == prompt_comp


def test_cli_prompt_command():
    runner = CliRunner()

    # 1. Default (summary)
    with patch("pyperclip.copy") as mock_copy, patch(
        "research_academy.pipeline.ad_hoc_digest.play_chime_success"
    ) as mock_chime:
        res = runner.invoke(cli, ["prompt"])
        assert res.exit_code == 0
        assert "Промпт скопирован в буфер обмена" in res.output
        assert "Executive Summary" in res.output
        mock_copy.assert_called_once()
        copied = mock_copy.call_args[0][0]
        assert "Executive Summary" in copied or "исполнительский конспект" in copied
        mock_chime.assert_called_once()

    # 2. compare / multi
    with patch("pyperclip.copy") as mock_copy, patch(
        "research_academy.pipeline.ad_hoc_digest.play_chime_success"
    ) as mock_chime:
        res_comp = runner.invoke(cli, ["prompt", "compare"])
        assert res_comp.exit_code == 0
        assert "compare" in res_comp.output
        copied_comp = mock_copy.call_args[0][0]
        assert "СВОДНАЯ СУТЬ И КОНСЕНСУС" in copied_comp
        assert "ТОЧКИ РАСХОЖДЕНИЯ И ПРОТИВОРЕЧИЯ" in copied_comp
        mock_chime.assert_called_once()



