"""Audio extraction and external Whisper fallback transcription provider."""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
import requests
import yt_dlp

from research_academy.models import TranscriptSegment, VideoTranscript
from research_academy.pipeline.normalization import normalize_caption_text

logger = logging.getLogger(__name__)


class AudioFallbackProvider(ABC):
    @abstractmethod
    def transcribe_audio_fallback(self, video_id: str, video_url: str) -> VideoTranscript:
        pass


class GroqWhisperAudioFallback(AudioFallbackProvider):
    def __init__(self, api_key: Optional[str] = None, temp_dir: Optional[Path] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.temp_dir = temp_dir or Path("temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio(self, video_url: str, output_path: Path) -> bool:
        """Downloads audio stream only (low bitrate mp3/m4a) to save bandwidth."""
        ydl_opts = {
            "format": "ba[ext=m4a]/ba/b",
            "outtmpl": str(output_path.with_suffix("")),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "64",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return output_path.exists()
        except Exception as e:
            logger.warning("Audio extraction failed for %s: %s", video_url, e)
            return False

    def transcribe_audio_fallback(self, video_id: str, video_url: str) -> VideoTranscript:
        if not self.api_key:
            return VideoTranscript(
                video_id=video_id,
                language="unknown",
                has_subtitles=False,
                fetch_status="FALLBACK_SKIPPED",
                error_message="Groq API key not configured for audio fallback",
            )

        audio_file = self.temp_dir / f"{video_id}.mp3"
        try:
            # 1. Download audio stream only
            success = self.extract_audio(video_url, audio_file)
            if not success or not audio_file.exists():
                return VideoTranscript(
                    video_id=video_id,
                    language="unknown",
                    has_subtitles=False,
                    fetch_status="FALLBACK_FAILED",
                    error_message="Failed to download audio track",
                )

            # Check file size (Groq limit is 25 MB)
            file_size_mb = audio_file.stat().st_size / (1024 * 1024)
            if file_size_mb > 25.0:
                return VideoTranscript(
                    video_id=video_id,
                    language="unknown",
                    has_subtitles=False,
                    fetch_status="FALLBACK_FAILED",
                    error_message=f"Audio file size ({file_size_mb:.1f} MB) exceeds limit of 25MB",
                )

            # 2. Call Groq Whisper API
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with open(audio_file, "rb") as f:
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files={"file": (audio_file.name, f, "audio/mpeg")},
                    data={"model": "whisper-large-v3", "response_format": "verbose_json"},
                    timeout=120.0,
                )

            if response.status_code != 200:
                return VideoTranscript(
                    video_id=video_id,
                    language="unknown",
                    has_subtitles=False,
                    fetch_status="FALLBACK_FAILED",
                    error_message=f"Groq API error ({response.status_code}): {response.text}",
                )

            res_data = response.json()
            raw_segments = res_data.get("segments", [])
            segments: List[TranscriptSegment] = []
            raw_texts: List[str] = []
            normalized_texts: List[str] = []

            for seg in raw_segments:
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
                text = str(seg.get("text", "")).strip()
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
                        language=res_data.get("language", "en"),
                        source_type="audio_fallback_whisper",
                        quality_status="normalized",
                    )
                )

            full_raw = " ".join(raw_texts)
            full_norm = " ".join(normalized_texts)

            return VideoTranscript(
                video_id=video_id,
                language=res_data.get("language", "en"),
                segments=segments,
                full_raw_text=full_raw,
                full_normalized_text=full_norm,
                word_count=len(full_norm.split()),
                has_subtitles=True,
                fetch_status="SUCCESS",
            )
        finally:
            # Enforce security/privacy rule: Do not store audio files indefinitely!
            if audio_file.exists():
                try:
                    audio_file.unlink()
                except Exception:
                    pass

