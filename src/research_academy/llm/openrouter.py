"""OpenRouter LLM provider implementation supporting DeepSeek and other open models."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional
from openai import OpenAI

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


def normalize_methodist_payload(raw_json: str) -> Dict[str, Any]:
    """Ensures nested or slightly altered LLM outputs conform to MethodistAnalysis schema."""
    data = json.loads(raw_json)
    if not isinstance(data, dict):
        return {"summary": str(data), "mechanisms_explanation": str(data)}

    # If wrapped under top-level 'analysis' or 'content' or 'result' or 'methodist_analysis'
    for k in ("analysis", "content", "result", "payload", "methodist_analysis", "document"):
        if k in data and isinstance(data[k], dict) and ("summary" in data[k] or "mechanisms_explanation" in data[k]):
            data = data[k]
            break

    # If summary missing but present in meta, intro, overview
    if not data.get("summary"):
        for candidate in ("meta", "intro", "abstract", "overview", "title"):
            if candidate in data:
                val = data[candidate]
                if isinstance(val, dict):
                    data["summary"] = val.get("summary") or val.get("description") or val.get("title") or ""
                elif isinstance(val, str):
                    data["summary"] = val
            if data.get("summary"):
                break

    # If mechanisms_explanation missing but present in mechanisms, theory, etc.
    if not data.get("mechanisms_explanation"):
        for candidate in ("mechanisms", "explanation", "core_mechanics", "theory", "theoretical_foundation", "calculations"):
            if candidate in data:
                val = data[candidate]
                data["mechanisms_explanation"] = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                break

    # Fallback defaults for mandatory string fields
    if not data.get("summary"):
        data["summary"] = "Академический методический конспект первоисточника."
    if not data.get("mechanisms_explanation"):
        data["mechanisms_explanation"] = "Механизмы, логика и закономерности исследуемой предметной области."

    # If key_concepts is a dict, convert to list of strings
    if isinstance(data.get("key_concepts"), dict):
        data["key_concepts"] = [f"{k}: {v}" for k, v in data["key_concepts"].items()]
    elif not isinstance(data.get("key_concepts"), list):
        data["key_concepts"] = []

    return data


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
                normalized_dict = normalize_methodist_payload(raw_json)
                analysis = MethodistAnalysis.model_validate(normalized_dict)
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
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": sys_prompt},
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
                    "Gatekeeper Source OpenRouter attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    max_attempts,
                    e,
                    backoff,
                )
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Gatekeeper Source LLM analysis failed after {max_attempts} attempts: {e}") from e
                time.sleep(backoff)
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
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )
                raw_json = clean_json_payload(response.choices[0].message.content or "")
                normalized_dict = normalize_methodist_payload(raw_json)
                analysis = MethodistAnalysis.model_validate(normalized_dict)
                for claim in analysis.key_claims:
                    if not claim.source_url:
                        claim.source_url = source.url
                return analysis
            except Exception as e:
                backoff = min(30.0, (2 ** attempt) * 1.5)
                logger.warning(
                    "Methodist Source OpenRouter attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    max_attempts,
                    e,
                    backoff,
                )
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Methodist Source LLM analysis failed after {max_attempts} attempts: {e}") from e
                time.sleep(backoff)
        raise RuntimeError("Unreachable")

