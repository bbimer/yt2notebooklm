"""Tests for the Fast-Track Closer module and exam simulator."""

from pathlib import Path
import pytest

from research_academy.pipeline.closer_fast_track import (
    get_fast_track_closer_playbook_markdown,
    get_fast_track_exam_simulator_markdown,
)
from research_academy.pipeline.synthesizer import CurriculumSynthesizer


def test_fast_track_closer_markdown_contents():
    md = get_fast_track_closer_playbook_markdown()
    assert "# БОЕВОЙ ПЛЕЙБУК КЛОУЗЕРА: ОТ $20 ДО $2,000+" in md
    assert "TRIPWIRE" in md
    assert "Gotbit" in md
    assert "Delphi Digital" in md
    assert "Performance Fee" in md
    # Ensure zero emojis
    assert "🎯" not in md
    assert "🔥" not in md
    assert "🚀" not in md
    assert "💰" not in md
    assert "👉" not in md
    # Ensure 10 objection cards
    for i in range(1, 11):
        assert f"### Карточка {i}:" in md


def test_fast_track_exam_simulator_contents():
    exam = get_fast_track_exam_simulator_markdown()
    assert "TELEGRAM CLOSER SIMULATOR" in exam
    assert "Артём" in exam
    assert "ДИСКВАЛИФИКАЦИЯ!" in exam
    assert "0.8 балла" in exam
    assert "0.6 балла" in exam


def test_synthesizer_fast_track_pack(tmp_path: Path):
    synthesizer = CurriculumSynthesizer(tmp_path)
    res = synthesizer.synthesize_fast_track_closer_pack()

    assert "closer_playbook_md" in res
    assert "closer_playbook_pdf" in res
    assert "exam_simulator_md" in res

    assert res["closer_playbook_md"].exists()
    assert res["closer_playbook_pdf"].exists()
    assert res["exam_simulator_md"].exists()

    assert res["closer_playbook_pdf"].stat().st_size > 50_000
    assert res["closer_playbook_md"].stat().st_size > 10_000

