"""Transcript provider using youtube-transcript-api with language fallback."""

from __future__ import annotations

import logging
from typing import List, Optional
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from research_academy.models import TranscriptSegment, VideoTranscript
from research_academy.pipeline.normalization import normalize_caption_text
from research_academy.providers.base import TranscriptProvider

logger = logging.getLogger(__name__)


class YouTubeApiTranscriptProvider(TranscriptProvider):
    def __init__(self, preferred_languages: Optional[List[str]] = None):
        self.preferred_languages = preferred_languages or ["ru", "en"]

    def _get_transcript_list(self, video_id: str):
        # Support both youtube-transcript-api >=1.2 (instance methods) and legacy static methods
        if hasattr(YouTubeTranscriptApi, "list_transcripts"):
            try:
                return YouTubeTranscriptApi.list_transcripts(video_id)
            except TypeError:
                pass

        api = YouTubeTranscriptApi() if isinstance(YouTubeTranscriptApi, type) else YouTubeTranscriptApi
        if hasattr(api, "list") and callable(getattr(api, "list")):
            return api.list(video_id)
        if hasattr(api, "list_transcripts") and callable(getattr(api, "list_transcripts")):
            return api.list_transcripts(video_id)
        raise AttributeError("YouTubeTranscriptApi has neither 'list' nor 'list_transcripts' method")

    def get_transcript(
        self, video_id: str, languages: Optional[List[str]] = None
    ) -> VideoTranscript:
        langs = languages or self.preferred_languages

        try:
            # 1. Fetch transcript list
            transcript_list = self._get_transcript_list(video_id)

            chosen_transcript = None
            source_type = "subtitles_manual"

            # Try manual first in preferred languages
            for lang in langs:
                try:
                    chosen_transcript = transcript_list.find_manually_created_transcript([lang])
                    source_type = "subtitles_manual"
                    break
                except Exception:
                    continue

            # If no manual, try auto-generated
            if not chosen_transcript:
                for lang in langs:
                    try:
                        chosen_transcript = transcript_list.find_generated_transcript([lang])
                        source_type = "subtitles_auto"
                        break
                    except Exception:
                        continue

            # Fallback to whatever is available
            if not chosen_transcript:
                try:
                    for t in transcript_list:
                        chosen_transcript = t
                        source_type = "subtitles_auto" if t.is_generated else "subtitles_manual"
                        break
                except Exception:
                    pass

            if not chosen_transcript:
                return VideoTranscript(
                    video_id=video_id,
                    language="unknown",
                    has_subtitles=False,
                    fetch_status="NOT_FOUND",
                    error_message="No suitable transcript found in requested languages",
                )

            # Fetch the actual transcript segments
            raw_res = chosen_transcript.fetch()
            if hasattr(raw_res, "to_raw_data") and callable(getattr(raw_res, "to_raw_data")):
                raw_data = raw_res.to_raw_data()
            elif isinstance(raw_res, list):
                raw_data = raw_res
            else:
                raw_data = list(raw_res)

            segments: List[TranscriptSegment] = []
            raw_texts: List[str] = []
            normalized_texts: List[str] = []

            for item in raw_data:
                if isinstance(item, dict):
                    start = float(item.get("start", 0.0))
                    duration = float(item.get("duration", 0.0))
                    text = str(item.get("text", "")).strip().replace("\n", " ")
                else:
                    start = float(getattr(item, "start", 0.0))
                    duration = float(getattr(item, "duration", 0.0))
                    text = str(getattr(item, "text", "")).strip().replace("\n", " ")

                end = start + duration
                if not text:
                    continue

                raw_texts.append(text)
                norm_text = normalize_caption_text(text)
                normalized_texts.append(norm_text)

                segments.append(
                    TranscriptSegment(
                        start_seconds=start,
                        end_seconds=end,
                        text=norm_text,
                        language=chosen_transcript.language_code,
                        source_type=source_type,
                        quality_status="normalized",
                    )
                )

            full_raw = " ".join(raw_texts)
            full_norm = " ".join(normalized_texts)
            word_count = len(full_norm.split())

            return VideoTranscript(
                video_id=video_id,
                language=chosen_transcript.language_code,
                segments=segments,
                full_raw_text=full_raw,
                full_normalized_text=full_norm,
                word_count=word_count,
                has_subtitles=True,
                fetch_status="SUCCESS",
            )

        except TranscriptsDisabled:
            return VideoTranscript(
                video_id=video_id,
                language="unknown",
                has_subtitles=False,
                fetch_status="DISABLED",
                error_message="Subtitles are disabled by author for this video",
            )
        except NoTranscriptFound:
            return VideoTranscript(
                video_id=video_id,
                language="unknown",
                has_subtitles=False,
                fetch_status="NOT_FOUND",
                error_message="No transcript found on YouTube",
            )
        except CouldNotRetrieveTranscript as e:
            return VideoTranscript(
                video_id=video_id,
                language="unknown",
                has_subtitles=False,
                fetch_status="BLOCKED",
                error_message=f"YouTube blocked or throttled transcript retrieval: {e}",
            )
        except Exception as e:
            logger.warning("Unexpected transcript error for %s: %s", video_id, e)
            return VideoTranscript(
                video_id=video_id,
                language="unknown",
                has_subtitles=False,
                fetch_status="ERROR",
                error_message=str(e),
            )

