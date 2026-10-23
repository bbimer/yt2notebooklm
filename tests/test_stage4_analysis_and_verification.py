"""Tests for Stage 4: Gatekeeper, Methodist, Claims Verification, and Publishing."""

from pathlib import Path
import pytest
from research_academy.config import AppConfig, ScoringSettings
from research_academy.database import Database
from research_academy.llm.mock_llm import MockLLMProvider
from research_academy.models import (
    ClaimModel,
    ClaimType,
    DiscoveryStatus,
    GatekeeperVerdict,
    TranscriptSegment,
    VideoMetadata,
    VideoTranscript,
)
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.pipeline.verification import ClaimVerifier


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_claim_verifier_disputes_false_guarantees(tmp_path: Path):
    verifier = ClaimVerifier()
    claim = ClaimModel(
        statement="Мы даем 100% гарантию доходности без риска",
        source_url="https://youtube.com/watch?v=scam",
    )
    res = verifier.verify_claim(claim)
    assert res.verification_status == "disputed"
    assert "ЗАПРЕЩЕНО" in res.allowed_sales_phrasing


def test_claim_verifier_verifies_delta_neutral():
    verifier = ClaimVerifier()
    claim = ClaimModel(
        statement="Дельта-нейтральная стратегия с бессрочными фьючерсами защищает от курса",
        source_url="https://youtube.com/watch?v=quant",
    )
    res = verifier.verify_claim(claim)
    assert res.verification_status == "verified"
    assert res.claim_type == ClaimType.VERIFIED_CLAIM


def test_gatekeeper_rejection_halts_methodist(temp_db: Database, tmp_path: Path):
    video = VideoMetadata(
        video_id="scam_gate_01",
        title="СКАМ СИГНАЛЫ 1000x",
        channel_id="chan_scam",
        channel_title="Scam Hub",
        url="https://youtube.com/watch?v=scam_gate_01",
        topic_id="funding-rate-arbitrage",
        duration_seconds=900,
    )
    temp_db.upsert_video(video)

    transcript = VideoTranscript(
        video_id="scam_gate_01",
        language="ru",
        full_raw_text="покупай монету переходи по ссылке сигналы",
        full_normalized_text="покупай монету переходи по ссылке сигналы",
        word_count=50,
        has_subtitles=True,
    )

    llm = MockLLMProvider(default_gatekeeper_decision=GatekeeperVerdict.REJECT, default_gatekeeper_score=3.0)
    config = AppConfig(project_root=tmp_path, database_path=temp_db.db_path)
    pipeline = AnalysisPipeline(config, temp_db, llm_provider=llm)

    gate_res, meth_res = pipeline.run_two_pass_analysis(video, transcript)
    assert gate_res.decision == GatekeeperVerdict.REJECT
    assert meth_res is None

    db_vid = temp_db.get_video("scam_gate_01")
    assert db_vid.discovery_status == DiscoveryStatus.GATEKEEPER_REJECTED


def test_gatekeeper_accept_generates_markdown(temp_db: Database, tmp_path: Path):
    video = VideoMetadata(
        video_id="quant_good_01",
        title="Institutional Delta Neutral Arbitrage Mechanics",
        channel_id="chan_wintermute",
        channel_title="Wintermute",
        url="https://youtube.com/watch?v=quant_good_01",
        topic_id="funding-rate-arbitrage",
        duration_seconds=1500,
    )
    temp_db.upsert_video(video)

    seg = TranscriptSegment(start_seconds=120.0, end_seconds=150.0, text="Funding rate arbitrage mechanics explained")
    transcript = VideoTranscript(
        video_id="quant_good_01",
        language="en",
        segments=[seg],
        full_raw_text="Funding rate arbitrage mechanics explained",
        full_normalized_text="Funding rate arbitrage mechanics explained",
        word_count=500,
        has_subtitles=True,
    )

    llm = MockLLMProvider(default_gatekeeper_decision=GatekeeperVerdict.ACCEPT, default_gatekeeper_score=9.0)
    config = AppConfig(project_root=tmp_path, database_path=temp_db.db_path)
    pipeline = AnalysisPipeline(config, temp_db, llm_provider=llm)

    gate_res, meth_res = pipeline.run_two_pass_analysis(video, transcript)
    assert gate_res.decision == GatekeeperVerdict.ACCEPT
    assert meth_res is not None

    db_vid = temp_db.get_video("quant_good_01")
    assert db_vid.discovery_status == DiscoveryStatus.PUBLISHED

    # Verify Markdown file was written to knowledge_base/sources
    sources_dir = tmp_path / "knowledge_base" / "sources"
    md_files = list(sources_dir.rglob("quant_good_01_*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert "Institutional Delta Neutral Arbitrage Mechanics" in content
    assert "Краткое содержание" in content
    assert "Вопросы клиентов и ответы" in content
    assert "Связь с NULLSPREAD" in content

