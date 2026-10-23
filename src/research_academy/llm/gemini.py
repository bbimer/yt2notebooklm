"""Google Gemini LLM provider implementation via google-genai SDK."""

from __future__ import annotations

import logging
import time
from typing import Optional
from google import genai
from google.genai import types

from research_academy.llm.base import LLMProvider
from research_academy.llm.prompts import (
    GATEKEEPER_SYSTEM_PROMPT,
    METHODIST_SYSTEM_PROMPT,
    build_gatekeeper_prompt,
    build_methodist_prompt,
)
from research_academy.pipeline.sampling import sample_transcript_multi_window
from research_academy.pipeline.scoring import apply_gatekeeper_scoring
from research_academy.models import (
    GatekeeperEvaluation,
    MethodistAnalysis,
    VideoMetadata,
    VideoTranscript,
)

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiLLMProvider")
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def evaluate_gatekeeper(
        self, video: VideoMetadata, transcript: VideoTranscript
    ) -> GatekeeperEvaluation:
        # Multi-window sampling with budget and chronological timestamps
        sample_text = sample_transcript_multi_window(transcript, max_words=4500)

        prompt = build_gatekeeper_prompt(
            title=video.title,
            channel=video.channel_title,
            topic=video.topic_id,
            transcript_sample=sample_text,
        )

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GATEKEEPER_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=GatekeeperEvaluation,
                        temperature=0.2,
                    ),
                )
                raw_eval = GatekeeperEvaluation.model_validate_json(response.text)
                # Compute composite score and verdict deterministically in Python
                return apply_gatekeeper_scoring(raw_eval)
            except Exception as e:
                logger.warning("Gatekeeper Gemini attempt %d failed: %s", attempt + 1, e)
                if attempt == 2:
                    raise RuntimeError(f"Gatekeeper LLM analysis failed after 3 attempts: {e}") from e
                time.sleep(2 ** attempt)

        raise RuntimeError("Unreachable")

    def generate_methodist_analysis(
        self,
        video: VideoMetadata,
        transcript: VideoTranscript,
        product_claims_text: Optional[str] = None,
    ) -> MethodistAnalysis:
        if transcript.segments:
            formatted_transcript = "\n".join(
                f"[{s.timestamp_formatted}] {s.text}" for s in transcript.segments if s.text.strip()
            )
        else:
            formatted_transcript = transcript.full_normalized_text

        prompt = build_methodist_prompt(
            title=video.title,
            channel=video.channel_title,
            topic=video.topic_id,
            full_transcript=formatted_transcript,
            product_claims=product_claims_text or "No specific product claims provided.",
        )

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=METHODIST_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=MethodistAnalysis,
                        temperature=0.3,
                    ),
                )
                return MethodistAnalysis.model_validate_json(response.text)
            except Exception as e:
                logger.warning("Methodist Gemini attempt %d failed: %s", attempt + 1, e)
                if attempt == 2:
                    raise RuntimeError(f"Methodist LLM analysis failed after 3 attempts: {e}") from e
                time.sleep(2 ** attempt)

        raise RuntimeError("Unreachable")

