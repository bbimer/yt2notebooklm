"""Two-pass AI analysis pipeline (Gatekeeper -> Methodist -> Publishing)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from research_academy.config import AppConfig
from research_academy.database import Database
from research_academy.llm.base import LLMProvider
from research_academy.llm.gemini import GeminiLLMProvider
from research_academy.llm.mock_llm import MockLLMProvider
from research_academy.models import (
    DiscoveryStatus,
    GatekeeperEvaluation,
    GatekeeperVerdict,
    MethodistAnalysis,
    VideoMetadata,
    VideoTranscript,
)
from research_academy.pipeline.publishing import Publisher
from research_academy.pipeline.scoring import apply_gatekeeper_scoring
from research_academy.pipeline.verification import ClaimVerifier

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    def __init__(
        self,
        config: AppConfig,
        db: Database,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.config = config
        self.db = db
        self.llm = llm_provider or self._init_llm()
        self.publisher = Publisher(db, config.project_root)

        product_claims_file = config.project_root / "knowledge_base" / "product" / "PRODUCT_CLAIMS.md"
        self.verifier = ClaimVerifier(product_claims_file)
        self.product_claims_text = (
            product_claims_file.read_text(encoding="utf-8")
            if product_claims_file.exists()
            else ""
        )

    def _init_llm(self) -> LLMProvider:
        if self.config.llm_provider in ("openrouter", "auto") and self.config.openrouter_api_key:
            try:
                from research_academy.llm.openrouter import OpenRouterLLMProvider
                return OpenRouterLLMProvider(
                    api_key=self.config.openrouter_api_key,
                    model_name=self.config.openrouter_model,
                )
            except Exception as e:
                logger.warning("Failed to init OpenRouterLLMProvider: %s", e)

        if self.config.llm_provider in ("gemini", "auto") and self.config.gemini_api_key:
            try:
                return GeminiLLMProvider(
                    api_key=self.config.gemini_api_key,
                    model_name=self.config.gemini_model,
                )
            except Exception as e:
                logger.warning("Failed to init GeminiLLMProvider: %s. Using MockLLMProvider.", e)
        return MockLLMProvider()

    def run_two_pass_analysis(
        self, video: VideoMetadata, transcript: VideoTranscript, force_methodist: bool = False
    ) -> Tuple[Optional[GatekeeperEvaluation], Optional[MethodistAnalysis]]:
        """
        Executes Gatekeeper (Pass A), and only if accepted (or forced), runs Methodist (Pass B).
        """
        # --- PASS A: Gatekeeper ---
        logger.info("Executing Pass A (Gatekeeper) for video %s", video.video_id)
        raw_gatekeeper_res = self.llm.evaluate_gatekeeper(video, transcript)
        # Enforce deterministic Python scoring and verdict
        gatekeeper_res = apply_gatekeeper_scoring(raw_gatekeeper_res)
        self.db.save_gatekeeper_evaluation(video.video_id, gatekeeper_res)

        if not force_methodist:
            if gatekeeper_res.decision == GatekeeperVerdict.REJECT:
                reason = f"Gatekeeper REJECT (Score: {gatekeeper_res.composite_score}/10, Noise: {gatekeeper_res.commercial_noise_score}/10)"
                self.db.update_video_status(video.video_id, DiscoveryStatus.GATEKEEPER_REJECTED, reason)
                logger.info("Video %s rejected by Gatekeeper: %s", video.video_id, reason)
                return gatekeeper_res, None

            if gatekeeper_res.decision == GatekeeperVerdict.REVIEW:
                reason = f"Gatekeeper REVIEW required (Score: {gatekeeper_res.composite_score}/10)"
                self.db.update_video_status(video.video_id, DiscoveryStatus.GATEKEEPER_REVIEW, reason)
                logger.info("Video %s flagged for manual review: %s", video.video_id, reason)
                return gatekeeper_res, None

            # Enforce Pass B quality bar: requires score >= 6.5
            if gatekeeper_res.composite_score < 6.5 and gatekeeper_res.decision != GatekeeperVerdict.ACCEPT:
                reason = f"Score {gatekeeper_res.composite_score}/10 below Pass B threshold (6.5/10)"
                self.db.update_video_status(video.video_id, DiscoveryStatus.GATEKEEPER_REJECTED, reason)
                logger.info("Video %s skipped for Pass B: %s", video.video_id, reason)
                return gatekeeper_res, None

        self.db.update_video_status(
            video.video_id,
            DiscoveryStatus.GATEKEEPER_ACCEPTED,
            f"Gatekeeper ACCEPT (Score: {gatekeeper_res.composite_score}/10)" + (" [FORCED]" if force_methodist else ""),
        )

        # --- PASS B: Methodist ---
        logger.info("Executing Pass B (Methodist) for video %s", video.video_id)
        methodist_analysis = self.llm.generate_methodist_analysis(
            video=video,
            transcript=transcript,
            product_claims_text=self.product_claims_text,
        )

        # Run claim verification against PRODUCT_CLAIMS, transcript reality and timestamps
        methodist_analysis.key_claims = self.verifier.verify_all(
            claims=methodist_analysis.key_claims,
            transcript=transcript,
            max_duration_seconds=video.duration_seconds,
        )

        # Save to database
        self.db.save_methodist_analysis(video.video_id, methodist_analysis)

        # Publish Markdown source
        markdown_path = self.publisher.publish_video_analysis(
            video=video,
            analysis=methodist_analysis,
            transcript=transcript,
            gatekeeper_score=gatekeeper_res.relevance_score,
        )
        logger.info("Published verified source markdown to: %s", markdown_path)

        self.db.update_video_status(
            video.video_id,
            DiscoveryStatus.PUBLISHED,
            f"Published to knowledge base: {markdown_path.name}",
        )

        return gatekeeper_res, methodist_analysis

