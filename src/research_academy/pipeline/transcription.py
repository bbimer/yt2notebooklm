"""Transcription pipeline orchestrator."""

from __future__ import annotations

import logging
from typing import Optional

from research_academy.config import AppConfig
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, VideoMetadata, VideoTranscript
from research_academy.providers.audio_fallback import AudioFallbackProvider, GroqWhisperAudioFallback
from research_academy.providers.base import TranscriptProvider
from research_academy.providers.transcripts import YouTubeApiTranscriptProvider

logger = logging.getLogger(__name__)


class TranscriptionPipeline:
    def __init__(
        self,
        config: AppConfig,
        db: Database,
        transcript_provider: Optional[TranscriptProvider] = None,
        fallback_provider: Optional[AudioFallbackProvider] = None,
    ):
        self.config = config
        self.db = db
        self.provider = transcript_provider or YouTubeApiTranscriptProvider()
        self.fallback = fallback_provider or (
            GroqWhisperAudioFallback(api_key=config.groq_api_key)
            if config.groq_api_key
            else None
        )

    def process_video_transcript(self, video: VideoMetadata) -> Optional[VideoTranscript]:
        """
        Fetches transcript for a video, validates length, and updates status.
        """
        logger.info("Fetching transcript for video: %s (%s)", video.video_id, video.title)

        # 1. Try subtitles extraction
        transcript = self.provider.get_transcript(video.video_id)

        # 2. Try audio fallback if no subtitles and fallback configured
        if not transcript.has_subtitles and self.fallback:
            logger.info("Subtitles unavailable for %s. Attempting audio fallback...", video.video_id)
            fallback_transcript = self.fallback.transcribe_audio_fallback(
                video.video_id, video.url
            )
            if fallback_transcript.has_subtitles:
                transcript = fallback_transcript

        # 3. Handle failure
        if not transcript.has_subtitles:
            reason = transcript.error_message or "Subtitles unavailable"
            self.db.update_video_status(video.video_id, DiscoveryStatus.TRANSCRIPT_FAILED, reason)
            return None

        # 4. Check word count limits
        cfg = self.config.scoring.transcript
        if transcript.word_count < cfg.min_words:
            reason = f"Transcript too short ({transcript.word_count} words < {cfg.min_words})"
            self.db.update_video_status(video.video_id, DiscoveryStatus.FILTERED_OUT, reason)
            return None

        # 5. Persist transcript
        self.db.save_transcript(transcript)
        self.db.update_video_status(
            video.video_id,
            DiscoveryStatus.TRANSCRIPT_FETCHED,
            f"Transcript fetched ({transcript.word_count} words)",
        )
        return transcript

