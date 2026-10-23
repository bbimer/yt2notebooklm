"""Deduplication and query association pipeline module."""

from __future__ import annotations

from typing import List, Tuple
from research_academy.database import Database
from research_academy.models import VideoMetadata


class Deduplicator:
    def __init__(self, db: Database):
        self.db = db

    def process_candidates(
        self, candidates: List[VideoMetadata], query_matched: str
    ) -> Tuple[List[VideoMetadata], List[VideoMetadata]]:
        """
        Deduplicates incoming candidates against the database.
        Returns:
            (new_videos, existing_videos)
        """
        new_videos: List[VideoMetadata] = []
        existing_videos: List[VideoMetadata] = []

        for video in candidates:
            is_new = self.db.upsert_video(video, query_matched=query_matched)
            # Re-fetch from DB to get aggregated queries
            fresh = self.db.get_video(video.video_id) or video
            if is_new:
                new_videos.append(fresh)
            else:
                existing_videos.append(fresh)

        return new_videos, existing_videos

