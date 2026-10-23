"""Data models for NULLSPREAD Research & Sales Academy."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DiscoveryStatus(str, Enum):
    NEW = "NEW"
    FILTERED_OUT = "FILTERED_OUT"
    QUEUED_FOR_TRANSCRIPT = "QUEUED_FOR_TRANSCRIPT"
    TRANSCRIPT_FETCHED = "TRANSCRIPT_FETCHED"
    TRANSCRIPT_FAILED = "TRANSCRIPT_FAILED"
    GATEKEEPER_REJECTED = "GATEKEEPER_REJECTED"
    GATEKEEPER_REVIEW = "GATEKEEPER_REVIEW"
    GATEKEEPER_ACCEPTED = "GATEKEEPER_ACCEPTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    PUBLISHED = "PUBLISHED"
    ERROR = "ERROR"


class GatekeeperVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    REVIEW = "REVIEW"
    REJECT = "REJECT"
    ACCEPTED_CORE = "ACCEPTED_CORE"
    REFERENCE_RETAIL_PSYCHOLOGY = "REFERENCE_RETAIL_PSYCHOLOGY"
    REVIEW_UNVERIFIED = "REVIEW_UNVERIFIED"
    REJECT_FOR_MODULE = "REJECT_FOR_MODULE"


class ClaimType(str, Enum):
    SOURCE_CLAIM = "source_claim"
    VERIFIED_CLAIM = "verified_claim"
    INTERPRETATION = "interpretation"
    UNVERIFIED = "unverified"


class QuestionCategory(str, Enum):
    BASIC = "basic"
    TECHNICAL = "technical"
    SKEPTICAL_CLIENT = "skeptical_client"
    RISK_MANAGEMENT = "risk_management"
    UNCERTAINTY = "uncertainty_acknowledgment"


class TopicConfig(BaseModel):
    id: str
    name: str
    priority: int = 1
    min_duration_seconds: int = 420
    max_duration_seconds: int = 2700
    queries_en: List[str] = Field(default_factory=list)
    queries_ru: List[str] = Field(default_factory=list)
    key_terms: List[str] = Field(default_factory=list)


class VideoMetadata(BaseModel):
    video_id: str
    title: str
    description: Optional[str] = ""
    channel_id: str
    channel_title: str
    published_at: Optional[datetime] = None
    duration_seconds: int = 0
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    channel_follower_count: Optional[int] = None
    url: str
    topic_id: str
    queries_matched: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    like_ratio: Optional[float] = None
    views_to_subscribers_ratio: Optional[float] = None
    discovery_status: DiscoveryStatus = DiscoveryStatus.NEW
    status_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("like_ratio", mode="before")
    def compute_like_ratio(cls, v: Any, info: Any) -> Optional[float]:
        if v is not None:
            return float(v)
        return None

    def calculate_derived_metrics(self) -> None:
        if self.view_count and self.view_count > 0:
            if self.like_count is not None:
                self.like_ratio = round(self.like_count / self.view_count, 4)
            if self.channel_follower_count and self.channel_follower_count > 0:
                self.views_to_subscribers_ratio = round(
                    self.view_count / self.channel_follower_count, 3
                )


class TranscriptSegment(BaseModel):
    start_seconds: float
    end_seconds: float
    text: str
    language: str = "en"
    source_type: str = "subtitles"  # subtitles_manual, subtitles_auto, audio_fallback
    quality_status: str = "raw"  # raw, normalized

    @property
    def timestamp_formatted(self) -> str:
        minutes = int(self.start_seconds // 60)
        seconds = int(self.start_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"


class VideoTranscript(BaseModel):
    video_id: str
    language: str
    segments: List[TranscriptSegment] = Field(default_factory=list)
    full_raw_text: str = ""
    full_normalized_text: str = ""
    word_count: int = 0
    has_subtitles: bool = True
    fetch_status: str = "SUCCESS"  # SUCCESS, NOT_FOUND, ERROR, BLOCKED
    error_message: Optional[str] = None


class GatekeeperEvaluation(BaseModel):
    relevance_score: float = Field(..., ge=1.0, le=10.0, description="1-10: How relevant to topic")
    technical_depth_score: float = Field(..., ge=1.0, le=10.0, description="1-10: Depth vs surface fluff")
    practical_value_score: float = Field(..., ge=1.0, le=10.0, description="1-10: Applicable trading/quant knowledge")
    source_quality_score: float = Field(..., ge=1.0, le=10.0, description="1-10: Trustworthiness and presentation")
    commercial_noise_score: float = Field(..., ge=1.0, le=10.0, description="1-10: High = referral spam, signal selling")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="0.0-1.0: Self-confidence of the model in its assessment")
    composite_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Calculated weighted score (0-10)")
    decision: GatekeeperVerdict = GatekeeperVerdict.REVIEW
    reasons: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    counter_evidence: List[str] = Field(default_factory=list, description="Accurate or useful points in the video")
    sales_translation_bridge: Optional[Dict[str, str]] = Field(
        default=None,
        description="Bridge from retail client terminology to real market mechanics and ideal sales response",
    )

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, v: Any) -> GatekeeperVerdict:
        if isinstance(v, GatekeeperVerdict):
            return v
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if v_clean in GatekeeperVerdict.__members__:
                return GatekeeperVerdict(v_clean)
            if "REJECT" in v_clean:
                return GatekeeperVerdict.REJECT_FOR_MODULE
            if "RETAIL" in v_clean or "PSYCHOLOGY" in v_clean or "REFERENCE" in v_clean:
                return GatekeeperVerdict.REFERENCE_RETAIL_PSYCHOLOGY
            if "ACCEPT" in v_clean:
                return GatekeeperVerdict.ACCEPTED_CORE
            if "UNVERIFIED" in v_clean or "REVIEW" in v_clean:
                return GatekeeperVerdict.REVIEW_UNVERIFIED
        return GatekeeperVerdict.REVIEW


class ClaimModel(BaseModel):
    claim_id: Optional[str] = None
    claim_type: ClaimType = ClaimType.SOURCE_CLAIM
    statement: str
    source_url: str = ""
    timestamp_seconds: Optional[float] = None
    timestamp_formatted: Optional[str] = None
    quote_text: Optional[str] = Field(default=None, description="Exact quote from transcript around timestamp")
    independent_evidence: Optional[str] = None
    verification_status: str = "unverified"  # verified, unverified, disputed
    allowed_sales_phrasing: Optional[str] = None
    verified_at: Optional[datetime] = None


class MethodistAnalysis(BaseModel):
    summary: str
    key_concepts: List[str] = Field(default_factory=list)
    mechanisms_explanation: str
    terminology_and_slang: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of dicts with 'term' and 'definition_or_context'",
    )
    numerical_examples: List[str] = Field(default_factory=list)
    common_mistakes_and_myths: List[str] = Field(default_factory=list)
    risks_and_limitations: List[str] = Field(default_factory=list)
    client_questions_and_answers: List[Dict[str, str]] = Field(
        default_factory=list,
        description="5 questions with 'question' and 'answer'",
    )
    self_check_questions: List[str] = Field(default_factory=list)
    key_claims: List[ClaimModel] = Field(default_factory=list)
    nullspread_connection: Optional[str] = "No confirmed product connection established."


class AcademyQuestion(BaseModel):
    id: str
    topic_id: str
    category: QuestionCategory
    question: str
    ideal_answer_key_points: List[str] = Field(default_factory=list)
    forbidden_phrasings: List[str] = Field(default_factory=list)
    source_reference: Optional[str] = None


class EvaluationResult(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    is_passing: bool
    has_critical_error: bool = False
    critical_error_details: Optional[str] = None
    factual_accuracy_score: float = Field(..., ge=0.0, le=10.0)
    mechanism_understanding_score: float = Field(..., ge=0.0, le=10.0)
    plain_language_score: float = Field(..., ge=0.0, le=10.0)
    limitations_coverage_score: float = Field(..., ge=0.0, le=10.0)
    no_false_promises_score: float = Field(..., ge=0.0, le=10.0)
    feedback: str
    knowledge_base_links: List[str] = Field(default_factory=list)
