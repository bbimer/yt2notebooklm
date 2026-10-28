"""Unit tests for Stage 1: Domain Profiles, Isomorphic Contracts, and Database Extension."""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from research_academy.database import Database
from research_academy.domain.manager import DomainManager
from research_academy.models import (
    ClaimModel,
    ClaimType,
    ContentSegment,
    DiscoveryStatus,
    SourceContent,
    TranscriptSegment,
    VideoMetadata,
    VideoTranscript,
    WebDocumentMetadata,
)
from research_academy.pipeline.verification import ClaimVerifier


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test_stage1.db"
    return Database(db_file)


def test_domain_manager_crypto_and_computer_science():
    manager = DomainManager()
    domains = manager.list_domains()
    assert "crypto" in domains
    assert "computer_science" in domains

    # 1. Crypto domain
    crypto = manager.get_domain("crypto")
    assert crypto.id == "crypto"
    assert len(crypto.topics) >= 7
    assert "Forensic Gatekeeper" in crypto.gatekeeper_prompt
    assert "Sales Academy" in crypto.methodist_prompt

    # 2. Computer Science domain
    cs = manager.get_domain("computer_science")
    assert cs.id == "computer_science"
    topic_ids = [t.id for t in cs.topics]
    assert "01_binary_numeral_system" in topic_ids
    assert "Академический Gatekeeper" in cs.gatekeeper_prompt
    assert "IEEE 754" in cs.gatekeeper_prompt or "двоичная" in cs.gatekeeper_prompt.lower()
    assert "Computer Science" in cs.methodist_prompt


def test_claim_model_backward_compatibility():
    # A. Legacy video claim with timestamp
    claim_video = ClaimModel(
        statement="Каскадная ликвидация лонгов маркет-мейкером",
        timestamp_seconds=255.0,
        timestamp_formatted="04:15",
        quote_text="ликвидация позиций",
    )
    assert claim_video.timestamp_formatted == "04:15"
    assert claim_video.source_anchor == "04:15"

    # B. Web claim with SEC- anchor
    claim_web = ClaimModel(
        statement="Дополнительный код инвертирует биты и добавляет единицу",
        anchor_id="SEC-02 | Дополнительный код",
        quote_text="инвертирует биты",
    )
    assert claim_web.anchor_id == "SEC-02 | Дополнительный код"
    assert claim_web.source_anchor == "SEC-02 | Дополнительный код"


def test_source_content_isomorphism_from_video():
    video = VideoMetadata(
        video_id="test_vid_iso",
        title="Orderbook L2 L3 Microstructure",
        channel_id="chan_01",
        channel_title="Quant Channel",
        url="https://youtube.com/watch?v=test_vid_iso",
        topic_id="03_orderbook_mechanics",
        domain="crypto",
    )
    transcript = VideoTranscript(
        video_id="test_vid_iso",
        language="ru",
        word_count=50,
        full_normalized_text="стакан заявок и сведение ордеров",
        segments=[
            TranscriptSegment(start_seconds=10.0, end_seconds=25.0, text="введение в стакан заявок"),
            TranscriptSegment(start_seconds=30.0, end_seconds=55.0, text="сведение ордеров FIFO matching engine"),
        ],
    )

    source = SourceContent.from_video(video, transcript, domain="crypto")
    assert source.source_id == "test_vid_iso"
    assert source.source_type == "youtube"
    assert source.domain == "crypto"
    assert len(source.segments) == 2
    assert source.segments[0].anchor_id == "00:10"
    assert source.segments[1].anchor_id == "00:30"
    assert "FIFO matching engine" in source.segments[1].text


def test_claim_verifier_with_sec_anchors():
    verifier = ClaimVerifier()

    # Create dummy web document SourceContent
    doc_source = SourceContent(
        source_id="web_doc_123",
        source_type="web",
        domain="computer_science",
        topic_id="01_binary_numeral_system",
        title="Двоичная система счисления",
        url="https://ru.wikipedia.org/wiki/binary",
        segments=[
            ContentSegment(
                index=1,
                anchor_id="SEC-01 | Введение",
                title="Введение",
                text="Двоичная система счисления позиционная система счисления с основанием 2.",
            ),
            ContentSegment(
                index=2,
                anchor_id="SEC-02 | Арифметика",
                title="Арифметика",
                text="Для представления отрицательных чисел в процессоре применяется дополнительный код two's complement.",
                has_code=True,
            ),
        ],
        full_clean_text="...",
        word_count=50,
    )

    # 1. Matching quote inside SEC-02
    claim_valid = ClaimModel(
        statement="Отрицательные числа хранятся в дополнительном коде",
        anchor_id="SEC-02 | Арифметика",
        quote_text="применяется дополнительный код two's complement",
    )
    res_valid = verifier.verify_claim(claim_valid, transcript=doc_source)
    assert res_valid.verification_status != "disputed"
    # Not disputed and quote was found

    # 2. Mismatched quote (not in SEC-01)
    claim_invalid = ClaimModel(
        statement="Флаги процессора",
        anchor_id="SEC-01 | Введение",
        quote_text="флаги процессора overflow carry flag",
    )
    res_invalid = verifier.verify_claim(claim_invalid, transcript=doc_source)
    assert res_invalid.verification_status == "unverified"
    assert "не обнаружена в секции SEC-01" in res_invalid.allowed_sales_phrasing


def test_database_document_crud_and_video_domain(temp_db: Database):
    # 1. Video domain persistence
    video = VideoMetadata(
        video_id="vid_cs_01",
        title="Binary Addition",
        channel_id="chan_cs",
        channel_title="MIT OpenCourseWare",
        url="https://youtube.com/watch?v=vid_cs_01",
        topic_id="01_binary_numeral_system",
        domain="computer_science",
    )
    is_new = temp_db.upsert_video(video)
    assert is_new is True
    saved_v = temp_db.get_video("vid_cs_01")
    assert saved_v is not None
    assert saved_v.domain == "computer_science"

    # 2. Document CRUD
    doc = WebDocumentMetadata(
        document_id="web_doc_wiki_binary",
        domain="computer_science",
        topic_id="01_binary_numeral_system",
        url="https://ru.wikipedia.org/wiki/binary",
        title="Двоичная система счисления",
        author_or_domain="ru.wikipedia.org",
        clean_markdown="# Двоичная система счисления\n\nТекст статьи...",
        word_count=1200,
        discovery_status=DiscoveryStatus.EXTRACTED,
    )
    is_new_doc = temp_db.upsert_document(doc)
    assert is_new_doc is True

    fetched_doc = temp_db.get_document("web_doc_wiki_binary")
    assert fetched_doc is not None
    assert fetched_doc.title == "Двоичная система счисления"
    assert fetched_doc.domain == "computer_science"
    assert fetched_doc.word_count == 1200

    # 3. Update status
    temp_db.update_document_status(
        "web_doc_wiki_binary",
        DiscoveryStatus.ANALYSIS_COMPLETED,
        "Pass B finished successfully",
    )
    updated_doc = temp_db.get_document("web_doc_wiki_binary")
    assert updated_doc.discovery_status == DiscoveryStatus.ANALYSIS_COMPLETED
    assert updated_doc.status_reason == "Pass B finished successfully"

    # 4. List documents by domain
    cs_docs = temp_db.list_documents(domain="computer_science")
    assert len(cs_docs) == 1
    assert cs_docs[0].document_id == "web_doc_wiki_binary"

    crypto_docs = temp_db.list_documents(domain="crypto")
    assert len(crypto_docs) == 0

