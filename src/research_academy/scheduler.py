"""Periodic scheduler and continuous research pipeline coordinator."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from research_academy.config import AppConfig
from research_academy.database import Database
from research_academy.models import DiscoveryStatus
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.pipeline.discovery import DiscoveryEngine
from research_academy.pipeline.transcription import TranscriptionPipeline

logger = logging.getLogger(__name__)


class ContinuousResearchCoordinator:
    def __init__(self, config: AppConfig, db: Database):
        self.config = config
        self.db = db
        self.discovery = DiscoveryEngine(config, db)
        self.transcription = TranscriptionPipeline(config, db)
        self.analysis = AnalysisPipeline(config, db)

    def run_update_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Executes an end-to-end continuous research update:
        1. Discovers new videos across configured topics (respecting query limits).
        2. Transcribes queued candidate videos.
        3. Runs Gatekeeper and Methodist passes.
        """
        limits = self.config.schedule.limits
        logger.info("Starting continuous research update (dry_run=%s)", dry_run)

        if dry_run:
            queued = self.db.list_videos(status=DiscoveryStatus.QUEUED_FOR_TRANSCRIPT, limit=limits.max_videos_per_run)
            transcribed = self.db.list_videos(status=DiscoveryStatus.TRANSCRIPT_FETCHED, limit=limits.max_videos_per_run)
            return {
                "dry_run": True,
                "planned_queries_per_topic": limits.max_queries_per_run,
                "queued_for_transcript": len(queued),
                "ready_for_analysis": len(transcribed),
                "estimated_max_cost_usd": limits.max_llm_cost_per_run_usd,
            }

        job_id = self.db.start_job("continuous_update")
        stats = {
            "topics_processed": 0,
            "transcripts_fetched": 0,
            "videos_published": 0,
            "videos_rejected": 0,
        }

        try:
            # 1. Discovery for top priority topics
            for topic_id in self.discovery.topics.keys():
                self.discovery.discover_by_topic(
                    topic_id=topic_id,
                    max_queries=min(2, limits.max_queries_per_run),
                )
                stats["topics_processed"] += 1

            # 2. Transcription
            queued_videos = self.db.list_videos(
                status=DiscoveryStatus.QUEUED_FOR_TRANSCRIPT,
                limit=limits.max_videos_per_run,
            )
            for v in queued_videos:
                t = self.transcription.process_video_transcript(v)
                if t:
                    stats["transcripts_fetched"] += 1

            # 3. Analysis (Gatekeeper + Methodist)
            ready_videos = self.db.list_videos(
                status=DiscoveryStatus.TRANSCRIPT_FETCHED,
                limit=limits.max_videos_per_run,
            )
            for v in ready_videos:
                transcript = self.db.get_transcript(v.video_id)
                if not transcript:
                    continue
                gate, meth = self.analysis.run_two_pass_analysis(v, transcript)
                if meth:
                    stats["videos_published"] += 1
                else:
                    stats["videos_rejected"] += 1

            self.db.finish_job(job_id, status="SUCCESS", details=stats)
            return stats
        except Exception as e:
            logger.exception("Continuous update cycle failed: %s", e)
            self.db.finish_job(job_id, status="FAILED", details={"error": str(e)})
            raise

    def retry_failed_transcripts(self) -> int:
        """Retries videos marked as TRANSCRIPT_FAILED."""
        failed = self.db.list_videos(status=DiscoveryStatus.TRANSCRIPT_FAILED, limit=20)
        retried_count = 0
        for v in failed:
            logger.info("Retrying transcript for video: %s", v.video_id)
            res = self.transcription.process_video_transcript(v)
            if res:
                retried_count += 1
        return retried_count


class ResearchScheduler:
    def __init__(self, coordinator: ContinuousResearchCoordinator):
        self.coordinator = coordinator
        self.scheduler = BackgroundScheduler(
            timezone=coordinator.config.schedule.timezone
        )

    def start(self) -> None:
        cron_expr = self.coordinator.config.schedule.cron_expression
        logger.info("Starting ResearchScheduler with cron: %s", cron_expr)
        self.scheduler.add_job(
            self.coordinator.run_update_cycle,
            CronTrigger.from_crontab(cron_expr),
            id="nullspread_research_update",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)

