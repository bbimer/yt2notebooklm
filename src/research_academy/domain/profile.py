"""Domain profile schema and configuration for Multi-Domain Knowledge Architecture."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from research_academy.models import TopicConfig


class DomainConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    trusted_sources: List[str] = Field(default_factory=list)
    blacklisted_domains: List[str] = Field(default_factory=list)
    default_prefilter_min_words: int = 250
    default_max_words: int = 15000
    claims_file: Optional[str] = None


class DomainProfile(BaseModel):
    id: str
    name: str
    description: str = ""
    config: DomainConfig
    topics: List[TopicConfig] = Field(default_factory=list)
    gatekeeper_prompt: str = ""
    methodist_prompt: str = ""
    claims_text: str = ""
    root_path: Optional[Path] = None

    def get_topic(self, topic_id: str) -> Optional[TopicConfig]:
        for t in self.topics:
            if t.id == topic_id:
                return t
        return None

