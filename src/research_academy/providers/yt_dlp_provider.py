"""yt-dlp implementation of YouTubeProvider as an alternative adapter."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import yt_dlp

from research_academy.models import VideoMetadata
from research_academy.providers.base import YouTubeProvider

logger = logging.getLogger(__name__)


class YtDlpProvider(YouTubeProvider):
    def __init__(self, quiet: bool = True):
        self.ydl_opts = {
            "quiet": quiet,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "ignoreerrors": True,
        }

    def search(
        self,
        query: str,
        topic_id: str,
        max_results: int = 15,
    ) -> List[VideoMetadata]:
        search_query = f"ytsearch{max_results}:{query}"
        results: List[VideoMetadata] = []

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if not info or "entries" not in info:
                    return []

                entries = [e for e in info.get("entries", []) if e and "id" in e]
                video_ids = [e["id"] for e in entries]

            # Detailed fetch for candidates
            return self.get_video_details(video_ids, topic_id=topic_id, query_matched=query)
        except Exception as e:
            logger.warning("yt-dlp search error: %s", e)
            return []

    def get_video_details(
        self,
        video_ids: List[str],
        topic_id: str = "general",
        query_matched: Optional[str] = None,
    ) -> List[VideoMetadata]:
        detailed_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ignoreerrors": True,
        }
        results: List[VideoMetadata] = []

        with yt_dlp.YoutubeDL(detailed_opts) as ydl:
            for vid in video_ids:
                try:
                    url = f"https://www.youtube.com/watch?v={vid}"
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        continue

                    # Safe parsing of upload date
                    pub_str = info.get("upload_date")
                    published_at = None
                    if pub_str and len(pub_str) == 8:
                        try:
                            published_at = datetime.strptime(pub_str, "%Y%m%d").replace(
                                tzinfo=timezone.utc
                            )
                        except Exception:
                            published_at = None

                    sub_count = info.get("channel_follower_count")
                    if sub_count is not None and not isinstance(sub_count, int):
                        sub_count = None

                    video = VideoMetadata(
                        video_id=vid,
                        title=info.get("title") or "",
                        description=info.get("description") or "",
                        channel_id=info.get("channel_id") or "",
                        channel_title=info.get("channel") or info.get("uploader") or "",
                        published_at=published_at,
                        duration_seconds=int(info.get("duration") or 0),
                        view_count=info.get("view_count"),
                        like_count=info.get("like_count"),
                        channel_follower_count=sub_count,
                        url=url,
                        topic_id=topic_id,
                        queries_matched=[query_matched] if query_matched else [],
                        language=info.get("language"),
                    )
                    video.calculate_derived_metrics()
                    results.append(video)
                except Exception as e:
                    logger.debug("Failed to extract details for %s: %s", vid, e)
                    continue

        return results

