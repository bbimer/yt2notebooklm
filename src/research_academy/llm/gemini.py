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
from research_academy.pipeline.sampling import (
    sample_source_content,
    sample_transcript_multi_window,
)
from research_academy.pipeline.scoring import apply_gatekeeper_scoring
from research_academy.models import (
    GatekeeperEvaluation,
    MethodistAnalysis,
    SourceContent,
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

    def evaluate_gatekeeper_source(
        self,
        source: SourceContent,
        system_prompt: Optional[str] = None,
    ) -> GatekeeperEvaluation:
        sample_text = sample_source_content(source, max_words=4500)
        prompt = (
            f"Тема/Модуль: {source.topic_id} (Домен: {source.domain})\n"
            f"Название источника: {source.title}\n"
            f"Автор / Площадка: {source.author_or_domain}\n"
            f"URL: {source.url}\n\n"
            f"ВЫБОРКА КОНТЕНТА:\n{sample_text}\n\n"
            f"Оцени данный материал строго по критериям и верни JSON."
        )
        sys_prompt = system_prompt or GATEKEEPER_SYSTEM_PROMPT
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        response_mime_type="application/json",
                        response_schema=GatekeeperEvaluation,
                        temperature=0.2,
                    ),
                )
                raw_eval = GatekeeperEvaluation.model_validate_json(response.text)
                return apply_gatekeeper_scoring(raw_eval)
            except Exception as e:
                logger.warning("Gatekeeper Source Gemini attempt %d failed: %s", attempt + 1, e)
                if attempt == 2:
                    raise RuntimeError(f"Gatekeeper Source LLM analysis failed: {e}") from e
                time.sleep(2 ** attempt)
        raise RuntimeError("Unreachable")

    def generate_methodist_source(
        self,
        source: SourceContent,
        system_prompt: Optional[str] = None,
        claims_text: Optional[str] = None,
    ) -> MethodistAnalysis:
        if source.segments:
            formatted_text = "\n\n".join(
                f"[{s.anchor_id}]\n{s.text}" for s in source.segments if s.text.strip()
            )
        else:
            formatted_text = source.full_clean_text

        prompt = (
            f"Тема: {source.topic_id} (Домен: {source.domain})\n"
            f"Название материала: {source.title}\n"
            f"Автор / Площадка: {source.author_or_domain}\n"
            f"URL: {source.url}\n\n"
            f"ПОЛНЫЙ ТЕКСТ / СЕГМЕНТЫ:\n{formatted_text}\n\n"
            f"ФУНДАМЕНТАЛЬНЫЕ ТЕЗИСЫ ДОМЕНА:\n{claims_text or 'Не заданы.'}\n\n"
            f"Сформируй глубокий структурированный методический разбор по схеме MethodistAnalysis."
        )
        sys_prompt = system_prompt or METHODIST_SYSTEM_PROMPT
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        response_mime_type="application/json",
                        response_schema=MethodistAnalysis,
                        temperature=0.3,
                    ),
                )
                return MethodistAnalysis.model_validate_json(response.text)
            except Exception as e:
                logger.warning("Methodist Source Gemini attempt %d failed: %s", attempt + 1, e)
                if attempt == 2:
                    raise RuntimeError(f"Methodist Source LLM analysis failed: {e}") from e
                time.sleep(2 ** attempt)
        raise RuntimeError("Unreachable")

