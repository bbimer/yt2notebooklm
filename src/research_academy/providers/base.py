"""Base interfaces for YouTube and Transcript providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from research_academy.models import VideoMetadata, VideoTranscript


class YouTubeProvider(ABC):
    """Abstract interface for YouTube discovery and metadata collection."""

    @abstractmethod
    def search(
        self,
        query: str,
        topic_id: str,
        max_results: int = 20,
    ) -> List[VideoMetadata]:
        """Search videos by query and return metadata list."""
        pass

    @abstractmethod
    def get_video_details(self, video_ids: List[str]) -> List[VideoMetadata]:
        """Fetch detailed metadata (views, likes, duration, channel info) for a batch of video IDs."""
        pass


class TranscriptProvider(ABC):
    """Abstract interface for retrieving video transcripts."""

    @abstractmethod
    def get_transcript(self, video_id: str, languages: Optional[List[str]] = None) -> VideoTranscript:
        """Fetch transcripts (captions) for a video."""
        pass

