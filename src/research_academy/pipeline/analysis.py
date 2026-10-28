"""Two-pass AI analysis pipeline (Gatekeeper -> Methodist -> Publishing)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from research_academy.config import AppConfig
from research_academy.database import Database
from research_academy.domain.manager import DomainManager
from research_academy.llm.base import LLMProvider
from research_academy.llm.gemini import GeminiLLMProvider
from research_academy.llm.mock_llm import MockLLMProvider
from research_academy.models import (
    DiscoveryStatus,
    GatekeeperEvaluation,
    GatekeeperVerdict,
    MethodistAnalysis,
    SourceContent,
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
        domain_manager: Optional[DomainManager] = None,
    ):
        self.config = config
        self.db = db
        self.domain_manager = domain_manager or DomainManager(config.project_root)
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

    def _update_status(
        self, source: SourceContent, status: DiscoveryStatus, reason: Optional[str] = None
    ) -> None:
        if source.source_type == "web" or self.db.get_document(source.source_id) is not None:
            self.db.update_document_status(source.source_id, status, reason)
        else:
            self.db.update_video_status(source.source_id, status, reason)

    def analyze_source(
        self,
        source: SourceContent,
        force_methodist: bool = False,
    ) -> Tuple[Optional[GatekeeperEvaluation], Optional[MethodistAnalysis]]:
        """
        Executes unified two-pass analysis (Gatekeeper -> Methodist -> Publishing) on any SourceContent.
        """
        domain_profile = self.domain_manager.get_domain(source.domain)
        claims_text = domain_profile.claims_text or self.product_claims_text

        # --- PASS A: Gatekeeper ---
        logger.info("Executing Pass A (Gatekeeper) for %s (%s)", source.source_id, source.title)
        raw_gatekeeper_res = self.llm.evaluate_gatekeeper_source(
            source, system_prompt=domain_profile.gatekeeper_prompt
        )
        gatekeeper_res = apply_gatekeeper_scoring(raw_gatekeeper_res)
        self.db.save_gatekeeper_evaluation(source.source_id, gatekeeper_res)

        if not force_methodist:
            if gatekeeper_res.decision == GatekeeperVerdict.REJECT:
                reason = f"Gatekeeper REJECT (Score: {gatekeeper_res.composite_score}/10, Noise: {gatekeeper_res.commercial_noise_score}/10)"
                self._update_status(source, DiscoveryStatus.GATEKEEPER_REJECTED, reason)
                logger.info("Source %s rejected by Gatekeeper: %s", source.source_id, reason)
                return gatekeeper_res, None

            if gatekeeper_res.decision == GatekeeperVerdict.REVIEW:
                reason = f"Gatekeeper REVIEW required (Score: {gatekeeper_res.composite_score}/10)"
                self._update_status(source, DiscoveryStatus.GATEKEEPER_REVIEW, reason)
                logger.info("Source %s flagged for manual review: %s", source.source_id, reason)
                return gatekeeper_res, None

            # Enforce Pass B quality bar: requires score >= 6.5
            if gatekeeper_res.composite_score < 6.5 and gatekeeper_res.decision != GatekeeperVerdict.ACCEPT:
                reason = f"Score {gatekeeper_res.composite_score}/10 below Pass B threshold (6.5/10)"
                self._update_status(source, DiscoveryStatus.GATEKEEPER_REJECTED, reason)
                logger.info("Source %s skipped for Pass B: %s", source.source_id, reason)
                return gatekeeper_res, None

        self._update_status(
            source,
            DiscoveryStatus.GATEKEEPER_ACCEPTED,
            f"Gatekeeper ACCEPT (Score: {gatekeeper_res.composite_score}/10)" + (" [FORCED]" if force_methodist else ""),
        )

        # --- PASS B: Methodist ---
        logger.info("Executing Pass B (Methodist) for %s (%s)", source.source_id, source.title)
        methodist_analysis = self.llm.generate_methodist_source(
            source=source,
            system_prompt=domain_profile.methodist_prompt,
            claims_text=claims_text,
        )

        # Run claim verification against claims reality and anchors
        max_duration = None
        if hasattr(source, "metadata") and source.metadata:
            max_duration = source.metadata.get("duration_seconds")
        methodist_analysis.key_claims = self.verifier.verify_all(
            claims=methodist_analysis.key_claims,
            transcript=source,
            max_duration_seconds=max_duration,
        )

        # Save to database
        self.db.save_methodist_analysis(source.source_id, methodist_analysis)

        # Publish Markdown source
        markdown_path = self.publisher.publish_source_analysis(
            source=source,
            analysis=methodist_analysis,
            gatekeeper_score=gatekeeper_res.relevance_score,
        )
        logger.info("Published verified source markdown to: %s", markdown_path)

        self._update_status(
            source,
            DiscoveryStatus.PUBLISHED,
            f"Published to knowledge base: {markdown_path.name}",
        )

        return gatekeeper_res, methodist_analysis

    def run_two_pass_analysis(
        self,
        video: Optional[VideoMetadata] = None,
        transcript: Optional[VideoTranscript] = None,
        force_methodist: bool = False,
        source: Optional[SourceContent] = None,
    ) -> Tuple[Optional[GatekeeperEvaluation], Optional[MethodistAnalysis]]:
        """
        Executes Gatekeeper (Pass A), and only if accepted (or forced), runs Methodist (Pass B).
        Backward-compatible with (video, transcript) and supports unified SourceContent.
        """
        if source is None:
            if video is None or transcript is None:
                raise ValueError("Either source or both (video and transcript) must be provided")
            source = SourceContent.from_video(
                video, transcript, domain=getattr(video, "domain", "crypto")
            )
        return self.analyze_source(source, force_methodist=force_methodist)

