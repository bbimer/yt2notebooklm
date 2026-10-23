"""LLM provider abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from research_academy.models import (
    GatekeeperEvaluation,
    MethodistAnalysis,
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

