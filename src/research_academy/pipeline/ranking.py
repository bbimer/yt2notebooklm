"""Pre-filtering, suspicious signal detection, and candidate ranking."""

from __future__ import annotations

from typing import List, Tuple
from research_academy.config import ScoringSettings
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, VideoMetadata


class VideoRanker:
    def __init__(self, settings: ScoringSettings, db: Database):
        self.settings = settings
        self.db = db

    def evaluate_prefilter(self, video: VideoMetadata) -> Tuple[bool, str]:
        """
        Evaluates mechanical criteria before spending resources on transcripts or LLMs.
        Returns:
            (passes_prefilter, reason)
        """
        cfg = self.settings.prefilter

        # 1. Duration check
        max_dur = cfg.max_duration_seconds_en if (video.language and video.language.lower() == "en") else cfg.max_duration_seconds
        if video.duration_seconds < cfg.min_duration_seconds:
            return False, f"Duration {video.duration_seconds}s is below minimum {cfg.min_duration_seconds}s (Short/Teaser)"
        if video.duration_seconds > max_dur:
            return False, f"Duration {video.duration_seconds}s exceeds maximum {max_dur}s"

        # 2. Minimum views check
        if video.view_count is not None and video.view_count < cfg.min_views:
            return False, f"View count {video.view_count} is below threshold {cfg.min_views}"

        # 3. Suspicious commercial / scam phrases
        combined_text = f"{video.title} {video.description}".lower()
        for phrase in cfg.suspicious_keywords:
            if phrase.lower() in combined_text:
                return False, f"Flagged suspicious commercial phrase: '{phrase}'"

        return True, "Passed pre-filter criteria"

    def rank_and_filter(self, videos: List[VideoMetadata]) -> Tuple[List[VideoMetadata], List[VideoMetadata]]:
        """
        Filters a list of candidate videos and updates their status in the database.
        Returns:
            (accepted_candidates, rejected_candidates)
        """
        accepted = []
        rejected = []

        for video in videos:
            passes, reason = self.evaluate_prefilter(video)
            if passes:
                self.db.update_video_status(video.video_id, DiscoveryStatus.QUEUED_FOR_TRANSCRIPT, reason)
                video.discovery_status = DiscoveryStatus.QUEUED_FOR_TRANSCRIPT
                video.status_reason = reason
                accepted.append(video)
            else:
                self.db.update_video_status(video.video_id, DiscoveryStatus.FILTERED_OUT, reason)
                video.discovery_status = DiscoveryStatus.FILTERED_OUT
                video.status_reason = reason
                rejected.append(video)

        # Sort accepted candidates by derived engagement metrics if present
        accepted.sort(
            key=lambda v: (
                v.views_to_subscribers_ratio or 0.0,
                v.like_ratio or 0.0,
                v.view_count or 0,
            ),
            reverse=True,
        )

        return accepted, rejected

