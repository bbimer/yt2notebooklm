"""Discovery coordinator for topics, queries, and providers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from research_academy.config import AppConfig, load_yaml_file
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, TopicConfig, VideoMetadata
from research_academy.pipeline.deduplication import Deduplicator
from research_academy.pipeline.ranking import VideoRanker
from research_academy.providers.base import YouTubeProvider
from research_academy.providers.mock_provider import MockYouTubeProvider

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    def __init__(
        self,
        config: AppConfig,
        db: Database,
        provider: Optional[YouTubeProvider] = None,
    ):
        self.config = config
        self.db = db
        self.provider = provider or self._init_provider()
        self.deduplicator = Deduplicator(db)
        self.ranker = VideoRanker(config.scoring, db)
        self.topics = self._load_topics()

    def _init_provider(self) -> YouTubeProvider:
        if self.config.youtube_provider == "youtube_api" and self.config.youtube_api_key:
            try:
                from research_academy.providers.youtube_api import YouTubeApiProvider
                return YouTubeApiProvider(self.config.youtube_api_key)
            except Exception as e:
                logger.warning("Failed to initialize YouTubeApiProvider: %s. Falling back to Mock.", e)
        elif self.config.youtube_provider == "yt_dlp":
            try:
                from research_academy.providers.yt_dlp_provider import YtDlpProvider
                return YtDlpProvider()
            except Exception as e:
                logger.warning("Failed to initialize YtDlpProvider: %s. Falling back to Mock.", e)

        # Fallback to mock provider if no keys or providers configured
        return MockYouTubeProvider()

    def _load_topics(self) -> Dict[str, TopicConfig]:
        topics_file = self.config.project_root / "config" / "topics.yaml"
        data = load_yaml_file(topics_file).get("topics", [])
        return {t["id"]: TopicConfig.model_validate(t) for t in data}

    def discover_by_topic(
        self,
        topic_id: str,
        max_queries: int = 4,
        max_results_per_query: int = 15,
    ) -> Dict[str, Any]:
        """
        Runs discovery for a specific topic across its English and Russian search matrices.
        """
        topic = self.topics.get(topic_id)
        if not topic:
            raise ValueError(f"Unknown topic: {topic_id}. Available: {list(self.topics.keys())}")

        job_id = self.db.start_job("discovery", topic_id=topic_id)
        logger.info("Starting discovery job #%d for topic '%s'", job_id, topic_id)

        all_queries = topic.queries_en + topic.queries_ru
        queries_to_run = all_queries[:max_queries]

        total_discovered = 0
        new_discovered = 0
        all_new_videos: List[VideoMetadata] = []

        try:
            for query in queries_to_run:
                logger.info("Executing search for query: '%s'", query)
                candidates = self.provider.search(
                    query=query,
                    topic_id=topic_id,
                    max_results=max_results_per_query,
                )
                total_discovered += len(candidates)

                new_videos, _ = self.deduplicator.process_candidates(candidates, query_matched=query)
                new_discovered += len(new_videos)
                all_new_videos.extend(new_videos)

            # Pre-filter and rank newly discovered videos
            accepted, rejected = self.ranker.rank_and_filter(all_new_videos)

            details = {
                "queries_executed": len(queries_to_run),
                "total_found": total_discovered,
                "new_unique": new_discovered,
                "queued_for_transcript": len(accepted),
                "filtered_out": len(rejected),
            }
            self.db.finish_job(job_id, status="SUCCESS", details=details)
            return details
        except Exception as e:
            logger.exception("Discovery failed for topic %s: %s", topic_id, e)
            self.db.finish_job(job_id, status="FAILED", details={"error": str(e)})
            raise

