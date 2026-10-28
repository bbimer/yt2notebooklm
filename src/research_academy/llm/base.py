"""LLM provider abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from research_academy.models import (
    GatekeeperEvaluation,
    MethodistAnalysis,
    SourceContent,
    TranscriptSegment,
    VideoMetadata,
    VideoTranscript,
)


class LLMProvider(ABC):
    @abstractmethod
    def evaluate_gatekeeper(
        self, video: VideoMetadata, transcript: VideoTranscript
    ) -> GatekeeperEvaluation:
        """Pass A: Fast, low-token evaluation of relevance, depth, and noise."""
        pass

    @abstractmethod
    def generate_methodist_analysis(
        self,
        video: VideoMetadata,
        transcript: VideoTranscript,
        product_claims_text: Optional[str] = None,
    ) -> MethodistAnalysis:
        """Pass B: Deep structured methodology, concepts, 5 questions, and real timestamped claims."""
        pass

    def evaluate_gatekeeper_source(
        self,
        source: SourceContent,
        system_prompt: Optional[str] = None,
    ) -> GatekeeperEvaluation:
        """Unified Pass A Gatekeeper evaluation on any SourceContent."""
        video = VideoMetadata(
            video_id=source.source_id,
            title=source.title,
            channel_id=source.author_or_domain or "source",
            channel_title=source.author_or_domain or "source",
            url=source.url,
            topic_id=source.topic_id,
            domain=source.domain,
            duration_seconds=int(source.word_count * 0.4),
        )
        segments = [
            TranscriptSegment(
                start_seconds=float(s.index * 60),
                end_seconds=float((s.index + 1) * 60),
                text=s.text,
            )
            for s in source.segments
        ]
        transcript = VideoTranscript(
            video_id=source.source_id,
            language="ru",
            segments=segments,
            full_raw_text=source.full_clean_text,
            full_normalized_text=source.full_clean_text,
            word_count=source.word_count,
        )
        return self.evaluate_gatekeeper(video, transcript)

    def generate_methodist_source(
        self,
        source: SourceContent,
        system_prompt: Optional[str] = None,
        claims_text: Optional[str] = None,
    ) -> MethodistAnalysis:
        """Unified Pass B Methodist analysis on any SourceContent."""
        video = VideoMetadata(
            video_id=source.source_id,
            title=source.title,
            channel_id=source.author_or_domain or "source",
            channel_title=source.author_or_domain or "source",
            url=source.url,
            topic_id=source.topic_id,
            domain=source.domain,
            duration_seconds=int(source.word_count * 0.4),
        )
        segments = [
            TranscriptSegment(
                start_seconds=float(s.index * 60),
                end_seconds=float((s.index + 1) * 60),
                text=s.text,
            )
            for s in source.segments
        ]
        transcript = VideoTranscript(
            video_id=source.source_id,
            language="ru",
            segments=segments,
            full_raw_text=source.full_clean_text,
            full_normalized_text=source.full_clean_text,
            word_count=source.word_count,
        )
        return self.generate_methodist_analysis(
            video=video,
            transcript=transcript,
            product_claims_text=claims_text,
        )

