"""Tests for Stage 6: Scheduler, Coordinator, Dry-run, and CLI commands."""

from pathlib import Path
import pytest
from click.testing import CliRunner
from research_academy.cli import cli
from research_academy.config import AppConfig, ScoringSettings
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, VideoMetadata
from research_academy.scheduler import ContinuousResearchCoordinator


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_coordinator_dry_run(temp_db: Database, tmp_path: Path):
    config = AppConfig(
        project_root=tmp_path,
        database_path=temp_db.db_path,
        scoring=ScoringSettings(),
    )
    coordinator = ContinuousResearchCoordinator(config, temp_db)
    res = coordinator.run_update_cycle(dry_run=True)

    assert res["dry_run"] is True
    assert "planned_queries_per_topic" in res
    assert "queued_for_transcript" in res


def test_coordinator_retry_failed_transcripts(temp_db: Database, tmp_path: Path):
    v = VideoMetadata(
        video_id="failed_vid_01",
        title="Failed Video",
        channel_id="chan_fail",
        channel_title="Fail Hub",
        url="https://youtube.com/watch?v=failed_vid_01",
        topic_id="funding-rate-arbitrage",
        discovery_status=DiscoveryStatus.TRANSCRIPT_FAILED,
        status_reason="Network error",
    )
    temp_db.upsert_video(v)

    config = AppConfig(project_root=tmp_path, database_path=temp_db.db_path)
    coordinator = ContinuousResearchCoordinator(config, temp_db)

    # Will attempt retry
    retried = coordinator.retry_failed_transcripts()
    assert isinstance(retried, int)


def test_cli_doctor():
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "System Diagnostic" in result.output
    assert "Python" in result.output
    assert "Database" in result.output


def test_cli_status():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Research Academy Status" in result.output


def test_cli_update_dry_run():
    runner = CliRunner()
    result = runner.invoke(cli, ["update", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY-RUN" in result.output


def test_cli_export():
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--format", "csv"])
    assert result.exit_code == 0
    assert "CSV index exported successfully" in result.output

