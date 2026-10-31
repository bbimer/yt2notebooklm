"""Tests for Stage 3: End-to-end Isomorphic Pipeline, Web Harvester, Domain Analysis & Publishing."""

from pathlib import Path
import pytest
from click.testing import CliRunner

from research_academy.cli import cli
from research_academy.config import AppConfig
from research_academy.database import Database
from research_academy.domain.manager import DomainManager
from research_academy.llm.mock_llm import MockLLMProvider
from research_academy.models import (
    ClaimType,
    ContentSegment,
    DiscoveryStatus,
    GatekeeperVerdict,
    SourceContent,
    WebDocumentMetadata,
)
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.pipeline.publishing import Publisher
from research_academy.pipeline.web_harvester import WebHarvester
from research_academy.providers.web_extractor import WebArticleExtractor


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_web_harvester_ingest_and_persistence(temp_db: Database, tmp_path: Path):
    extractor = WebArticleExtractor(min_words=50)
    config = AppConfig(project_root=tmp_path, database_path=temp_db.db_path)
    harvester = WebHarvester(config, temp_db, extractor=extractor)

    html = """
    <html>
      <head><title>Binary Numeral System — Academic Overview</title></head>
      <body>
        <article>
          <h1>Binary Numeral System</h1>
          <p>The binary numeral system is a positional base-2 system that uses digits 0 and 1.</p>
          <h2>Mathematical Definition</h2>
          <p>Each bit position represents an increasing power of two from right to left.</p>
          <table>
            <tr><th>Binary</th><th>Decimal</th></tr>
            <tr><td>0001</td><td>1</td></tr>
            <tr><td>0010</td><td>2</td></tr>
          </table>
          <p>Conclusion: Modern ALU circuitry operates purely in binary logic for maximum physical switching reliability.</p>
        </article>
      </body>
    </html>
    """

    # Mock extraction from HTML directly via extractor and store in DB
    result = extractor.extract_from_html(html, "https://en.wikipedia.org/wiki/Binary_number")
    assert result.status == DiscoveryStatus.EXTRACTED
    assert len(result.segments) >= 2

    source = harvester.ingest_url(
        url="https://en.wikipedia.org/wiki/Binary_number",
        topic_id="01_binary_numeral_system",
        domain="computer_science",
        force_fetch=False,
    )
    # The first call will attempt fetch or we verify DB upsert logic
    doc = temp_db.get_document(source.source_id)
    assert doc is not None
    assert doc.domain == "computer_science"
    assert doc.topic_id == "01_binary_numeral_system"


def test_isomorphic_analysis_on_web_source(temp_db: Database, tmp_path: Path):
    config = AppConfig(project_root=tmp_path, database_path=temp_db.db_path)
    llm = MockLLMProvider(default_gatekeeper_decision=GatekeeperVerdict.ACCEPT, default_gatekeeper_score=9.0)
    pipeline = AnalysisPipeline(config, temp_db, llm_provider=llm)

    seg1 = ContentSegment(
        index=1,
        anchor_id="SEC-01 | Введение",
        title="Введение",
        text="Двоичная система счисления является позиционной системой счисления с основанием 2.",
        word_count=10,
    )
    seg2 = ContentSegment(
        index=2,
        anchor_id="SEC-02 | Арифметика",
        title="Арифметика",
        text="Сложение двоичных чисел выполняется поразрядно с переносом единицы в старший разряд.",
        word_count=10,
    )

    source = SourceContent(
        source_id="web_binary_test_01",
        source_type="web",
        domain="computer_science",
        topic_id="01_binary_numeral_system",
        title="Двоичная система счисления и машинная арифметика",
        url="https://ru.wikipedia.org/wiki/Двоичная_система_счисления",
        author_or_domain="ru.wikipedia.org",
        segments=[seg1, seg2],
        full_clean_text=f"{seg1.text}\n\n{seg2.text}",
        word_count=20,
    )

    # Register document in DB
    doc_meta = WebDocumentMetadata(
        document_id=source.source_id,
        domain=source.domain,
        topic_id=source.topic_id,
        url=source.url,
        title=source.title,
        author_or_domain=source.author_or_domain,
        clean_markdown=source.full_clean_text,
        word_count=source.word_count,
        discovery_status=DiscoveryStatus.EXTRACTED,
    )
    temp_db.upsert_document(doc_meta)

    # Execute isomorphic two-pass analysis
    gate_res, meth_res = pipeline.run_two_pass_analysis(source=source)

    assert gate_res is not None
    assert gate_res.decision == GatekeeperVerdict.ACCEPT
    assert meth_res is not None
    assert len(meth_res.key_concepts) > 0
    assert len(meth_res.key_claims) > 0

    # Verify claim anchors match SEC-01
    claim = meth_res.key_claims[0]
    assert claim.anchor_id == "SEC-01 | Введение"
    assert claim.verification_status == "verified"

    # Verify document status updated in DB
    updated_doc = temp_db.get_document(source.source_id)
    assert updated_doc.discovery_status == DiscoveryStatus.PUBLISHED

    # Verify published markdown file in domain-isolated folder
    domain_file = (
        tmp_path
        / "knowledge_base"
        / "domains"
        / "computer_science"
        / "sources"
        / "01_binary_numeral_system"
    )
    published_files = list(domain_file.glob("*.md"))
    assert len(published_files) == 1
    content = published_files[0].read_text(encoding="utf-8")
    assert "SEC-01" in content
    assert "computer_science" in content


def test_publisher_notebooklm_pack_for_custom_domain(temp_db: Database, tmp_path: Path):
    publisher = Publisher(temp_db, tmp_path)

    # Create a mock source in computer_science
    src_dir = tmp_path / "knowledge_base" / "domains" / "computer_science" / "sources" / "01_binary_numeral_system"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "web_01_binary.md").write_text("# Двоичная система\nКонтент модуля.", encoding="utf-8")

    # Export NotebookLM pack for computer_science
    pack_dir = publisher.export_notebooklm_pack(domain="computer_science")
    assert pack_dir.exists()
    assert (pack_dir / "README_NOTEBOOKLM_GUIDE.md").exists()
    assert (pack_dir / "Topic_01_binary_numeral_system.md").exists()

    guide_text = (pack_dir / "README_NOTEBOOKLM_GUIDE.md").read_text(encoding="utf-8")
    assert "Computer Science" in guide_text

    topic_text = (pack_dir / "Topic_01_binary_numeral_system.md").read_text(encoding="utf-8")
    assert "Двоичная система" in topic_text


def test_cli_domain_and_web_commands(tmp_path: Path):
    runner = CliRunner()

    # 1. domain list
    res_list = runner.invoke(cli, ["domain", "list"])
    assert res_list.exit_code == 0
    assert "computer_science" in res_list.output
    assert "crypto" in res_list.output
    assert "english_learning" in res_list.output

    # 2. domain info
    res_info = runner.invoke(cli, ["domain", "info", "computer_science"])
    assert res_info.exit_code == 0
    assert "01_binary_numeral" in res_info.output

    # 3. export for custom domain
    res_export = runner.invoke(cli, ["export", "--format", "pack", "--domain", "computer_science"])
    assert res_export.exit_code == 0
    assert "computer_science" in res_export.output
    import shutil
    shutil.rmtree(Path("exports/notebooklm_pack/computer_science"), ignore_errors=True)
