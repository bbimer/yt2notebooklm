"""OpenRouter LLM provider implementation supporting DeepSeek and other open models."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional
from openai import OpenAI

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


def clean_json_payload(raw_text: str) -> str:
    """Clean markdown code fences from JSON output if returned by model."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class OpenRouterLLMProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek/deepseek-v4.1-flash",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouterLLMProvider")
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=timeout, max_retries=2)

    def evaluate_gatekeeper(
        self, video: VideoMetadata, transcript: VideoTranscript
    ) -> GatekeeperEvaluation:
        sample_text = sample_transcript_multi_window(transcript, max_words=4500)

        prompt = build_gatekeeper_prompt(
            title=video.title,
            channel=video.channel_title,
            topic=video.topic_id,
            transcript_sample=sample_text,
        )

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": GATEKEEPER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                raw_json = clean_json_payload(response.choices[0].message.content or "")
                raw_eval = GatekeeperEvaluation.model_validate_json(raw_json)
                return apply_gatekeeper_scoring(raw_eval)
            except Exception as e:
                backoff = min(30.0, (2 ** attempt) * 1.5)
                logger.warning(
                    "Gatekeeper OpenRouter attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    max_attempts,
                    e,
                    backoff,
                )
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Gatekeeper LLM analysis failed after {max_attempts} attempts: {e}") from e
                time.sleep(backoff)

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

        video_url = f"https://www.youtube.com/watch?v={video.video_id}"

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": METHODIST_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )
                raw_json = clean_json_payload(response.choices[0].message.content or "")
                analysis = MethodistAnalysis.model_validate_json(raw_json)
                for claim in analysis.key_claims:
                    if not claim.source_url:
                        claim.source_url = video_url
                return analysis
            except Exception as e:
                backoff = min(30.0, (2 ** attempt) * 1.5)
                logger.warning(
                    "Methodist OpenRouter attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    max_attempts,
                    e,
                    backoff,
                )
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Methodist LLM analysis failed after {max_attempts} attempts: {e}") from e
                time.sleep(backoff)

        raise RuntimeError("Unreachable")

