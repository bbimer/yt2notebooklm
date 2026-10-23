"""YouTube Data API v3 implementation of YouTubeProvider."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from research_academy.models import VideoMetadata
from research_academy.providers.base import YouTubeProvider


def parse_iso8601_duration(duration_str: str) -> int:
    """
    Parses ISO 8601 duration strings like 'PT15M33S', 'PT1H2M10S', 'PT45S' into total seconds.
    """
    pattern = re.compile(
        r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
    )
    match = pattern.match(duration_str or "")
    if not match:
        return 0
    parts = match.groupdict()
    hours = int(parts.get("hours") or 0)
    minutes = int(parts.get("minutes") or 0)
    seconds = int(parts.get("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


class YouTubeApiProvider(YouTubeProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("YouTube API key is required for YouTubeApiProvider")
        self.api_key = api_key
        self._service = build("youtube", "v3", developerKey=api_key)
        self.quota_units_used = 0

    def search(
        self,
        query: str,
        topic_id: str,
        max_results: int = 20,
    ) -> List[VideoMetadata]:
        try:
            # 1. Search for video IDs (costs ~100 units)
            request = self._service.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=min(max_results, 50),
            )
            response = request.execute()
            self.quota_units_used += 100

            items = response.get("items", [])
            video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]
            if not video_ids:
                return []

            # 2. Batch fetch full video details (costs ~1 unit)
            videos = self.get_video_details(video_ids, topic_id=topic_id, query_matched=query)
            return videos
        except HttpError as e:
            if e.resp.status in (400, 403):
                raise RuntimeError(f"YouTube Data API error (Quota or Authentication): {e}") from e
            raise RuntimeError(f"YouTube Data API error: {e}") from e

    def get_video_details(
        self,
        video_ids: List[str],
        topic_id: str = "general",
        query_matched: Optional[str] = None,
    ) -> List[VideoMetadata]:
        if not video_ids:
            return []

        results: List[VideoMetadata] = []
        # Chunk into batches of 50
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            request = self._service.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(batch),
            )
            response = request.execute()
            self.quota_units_used += 1

            for item in response.get("items", []):
                vid = item["id"]
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})
                statistics = item.get("statistics", {})

                duration_sec = parse_iso8601_duration(content_details.get("duration", ""))
                published_at_str = snippet.get("publishedAt")
                published_at = (
                    datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                    if published_at_str
                    else None
                )

                views = int(statistics.get("viewCount")) if statistics.get("viewCount") else None
                likes = int(statistics.get("likeCount")) if statistics.get("likeCount") else None

                video = VideoMetadata(
                    video_id=vid,
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    channel_id=snippet.get("channelId", ""),
                    channel_title=snippet.get("channelTitle", ""),
                    published_at=published_at,
                    duration_seconds=duration_sec,
                    view_count=views,
                    like_count=likes,
                    channel_follower_count=None,  # Not in videos.list, kept as null
                    url=f"https://www.youtube.com/watch?v={vid}",
                    topic_id=topic_id,
                    queries_matched=[query_matched] if query_matched else [],
                    language=snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage"),
                )
                video.calculate_derived_metrics()
                results.append(video)

        return results

