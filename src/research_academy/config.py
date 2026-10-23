"""Configuration loader and schema validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env if present
load_dotenv()


class TrustedChannelConfig(BaseModel):
    id: str
    name: str
    specialization: str = ""
    rationale: str = ""
    verified: bool = False


DEFAULT_SUSPICIOUS_KEYWORDS = [
    "связка дня",
    "бесплатная связка",
    "гарантированный доход",
    "без вложений",
    "100% прибыль",
    "сигналы в телеграм",
    "раскрутка счета",
    "пассивный доход на автомате",
    "free money",
    "guaranteed profit",
    "100x gem",
    "telegram signals",
    "памп и дамп",
    "1000x",
    "заработок для новичка с нуля",
    "100% гарантия",
    "best signals",
    "реферальная ссылка",
    "t.me/",
]


class PreFilterConfig(BaseModel):
    min_views: int = 1000
    min_duration_seconds: int = 420
    max_duration_seconds: int = 3000
    max_duration_seconds_en: int = 4500  # 75 mins for deep institutional EN lectures/podcasts
    min_like_ratio: float = 0.015
    suspicious_keywords: List[str] = Field(default_factory=lambda: list(DEFAULT_SUSPICIOUS_KEYWORDS))


class ScoringWeights(BaseModel):
    relevance: float = 0.30
    technical_depth: float = 0.30
    practical_value: float = 0.20
    source_quality: float = 0.10
    commercial_noise_penalty: float = 0.10


class ThresholdsConfig(BaseModel):
    accept_score: float = 7.0
    review_score: float = 5.5
    max_commercial_noise: float = 6.0


class TranscriptConfig(BaseModel):
    max_words: int = 15000
    min_words: int = 250
    max_segments: int = 1200


class ScoringSettings(BaseModel):
    prefilter: PreFilterConfig = Field(default_factory=PreFilterConfig)
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    transcript: TranscriptConfig = Field(default_factory=TranscriptConfig)


class ExecutionWindow(BaseModel):
    start_hour: int = 2
    end_hour: int = 6


class ScheduleLimits(BaseModel):
    max_queries_per_run: int = 6
    max_videos_per_run: int = 15
    max_llm_cost_per_run_usd: float = 1.0


class ScheduleConfig(BaseModel):
    enabled: bool = False
    interval_hours: int = 24
    cron_expression: str = "0 3 * * *"
    timezone: str = "UTC"
    execution_window: ExecutionWindow = Field(default_factory=ExecutionWindow)
    limits: ScheduleLimits = Field(default_factory=ScheduleLimits)


class AppConfig(BaseModel):
    project_root: Path
    youtube_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "deepseek/deepseek-v4.1-flash"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: Optional[str] = None
    environment: str = "development"
    database_path: Path
    youtube_provider: str = "youtube_api"  # youtube_api or yt_dlp
    llm_provider: str = "auto"  # openrouter, gemini, or mock
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    trusted_channels: List[TrustedChannelConfig] = Field(default_factory=list)

    def mask_secret(self, secret: Optional[str]) -> str:
        if not secret:
            return "<NOT CONFIGURED>"
        if len(secret) <= 8:
            return "***"
        return f"{secret[:4]}...{secret[-4:]}"

    @property
    def status_summary(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "youtube_provider": self.youtube_provider,
            "llm_provider": self.llm_provider,
            "openrouter_api_key": self.mask_secret(self.openrouter_api_key),
            "openrouter_model": self.openrouter_model,
            "youtube_api_key": self.mask_secret(self.youtube_api_key),
            "gemini_api_key": self.mask_secret(self.gemini_api_key),
            "gemini_model": self.gemini_model,
            "database_path": str(self.database_path),
            "trusted_channels_count": len(self.trusted_channels),
            "schedule_enabled": self.schedule.enabled,
        }


def find_project_root() -> Path:
    """Resolve project root directory."""
    current = Path(__file__).resolve().parent
    for _ in range(4):
        if (current / "pyproject.toml").exists() or (current / "config").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except Exception:
            return {}


def get_config(root_dir: Optional[Path] = None) -> AppConfig:
    root = root_dir or find_project_root()
    config_dir = root / "config"

    # Load scoring
    scoring_data = load_yaml_file(config_dir / "scoring.yaml").get("scoring", {})
    scoring = ScoringSettings.model_validate(scoring_data) if scoring_data else ScoringSettings()

    # Load schedule
    schedule_data = load_yaml_file(config_dir / "schedule.yaml").get("schedule", {})
    schedule = ScheduleConfig.model_validate(schedule_data) if schedule_data else ScheduleConfig()

    # Load trusted channels
    trusted_data = load_yaml_file(config_dir / "trusted_channels.yaml").get("channels", [])
    trusted_channels = [TrustedChannelConfig.model_validate(c) for c in trusted_data]

    # Database path
    db_rel = os.getenv("DATABASE_PATH", "data/research_academy.db")
    db_path = root / db_rel
    db_path.parent.mkdir(parents=True, exist_ok=True)

    default_yt_provider = "youtube_api" if os.getenv("YOUTUBE_API_KEY") else "yt_dlp"
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    default_llm_provider = "openrouter" if openrouter_key else ("gemini" if gemini_key else "mock")

    return AppConfig(
        project_root=root,
        youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
        openrouter_api_key=openrouter_key,
        openrouter_model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
        gemini_api_key=gemini_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        environment=os.getenv("ENVIRONMENT", "development"),
        database_path=db_path,
        youtube_provider=os.getenv("YOUTUBE_PROVIDER", default_yt_provider),
        llm_provider=os.getenv("LLM_PROVIDER", default_llm_provider),
        scoring=scoring,
        schedule=schedule,
        trusted_channels=trusted_channels,
    )
