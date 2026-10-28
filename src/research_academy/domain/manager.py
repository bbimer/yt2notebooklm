"""DomainManager: Discovers, loads, and manages domain profiles with backward compatibility."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from research_academy.domain.profile import DomainConfig, DomainProfile
from research_academy.models import TopicConfig

logger = logging.getLogger(__name__)


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Error reading YAML %s: %s", path, e)
        return {}


def _import_prompts_from_file(path: Path) -> Tuple[str, str]:
    """Dynamically imports GATEKEEPER_SYSTEM_PROMPT and METHODIST_SYSTEM_PROMPT from a python file."""
    if not path.exists():
        return "", ""
    try:
        spec = importlib.util.spec_from_file_location("domain_prompts", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            gk = getattr(module, "GATEKEEPER_SYSTEM_PROMPT", "")
            met = getattr(module, "METHODIST_SYSTEM_PROMPT", "")
            return gk, met
    except Exception as e:
        logger.warning("Could not load prompts from %s: %s", path, e)
    return "", ""


class DomainManager:
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            from research_academy.config import find_project_root
            self.project_root = find_project_root()
        else:
            self.project_root = project_root
        self.domains_dir = self.project_root / "domains"
        self._cache: Dict[str, DomainProfile] = {}

    def list_domains(self) -> List[str]:
        """Lists available domain identifiers."""
        domains = []
        if self.domains_dir.exists():
            for d in self.domains_dir.iterdir():
                if d.is_dir() and not d.name.startswith((".", "_")):
                    domains.append(d.name)

        # Fallback to repository root domains if self.project_root is a temp dir
        from research_academy.config import find_project_root
        repo_root = find_project_root()
        if repo_root != self.project_root and (repo_root / "domains").exists():
            for d in (repo_root / "domains").iterdir():
                if d.is_dir() and not d.name.startswith((".", "_")):
                    domains.append(d.name)

        if "crypto" not in domains:
            domains.append("crypto")
        return sorted(list(set(domains)))

    def get_domain(self, domain_id: str = "crypto") -> DomainProfile:
        """Retrieves and caches domain profile by id. Defaults to crypto with fallback."""
        if domain_id in self._cache:
            return self._cache[domain_id]

        domain_dir = self.domains_dir / domain_id
        if domain_dir.exists():
            profile = self._load_from_directory(domain_dir, domain_id)
            self._cache[domain_id] = profile
            return profile

        # Check repository root fallback if self.project_root was a custom directory
        from research_academy.config import find_project_root
        repo_root = find_project_root()
        if repo_root != self.project_root:
            repo_domain_dir = repo_root / "domains" / domain_id
            if repo_domain_dir.exists():
                profile = self._load_from_directory(repo_domain_dir, domain_id)
                self._cache[domain_id] = profile
                return profile

        # Fallback for default crypto domain if custom directory not found
        if domain_id == "crypto":
            profile = self._create_crypto_fallback()
            self._cache[domain_id] = profile
            return profile

        raise ValueError(f"Domain '{domain_id}' not found in {self.domains_dir}")

    def _load_from_directory(self, domain_dir: Path, domain_id: str) -> DomainProfile:
        domain_yaml_path = domain_dir / "domain.yaml"
        domain_data = _load_yaml(domain_yaml_path)

        config = DomainConfig(
            id=domain_data.get("id", domain_id),
            name=domain_data.get("name", domain_id.replace("_", " ").title()),
            description=domain_data.get("description", ""),
            trusted_sources=domain_data.get("trusted_sources", []),
            blacklisted_domains=domain_data.get("blacklisted_domains", []),
            default_prefilter_min_words=domain_data.get("default_prefilter_min_words", 250),
            default_max_words=domain_data.get("default_max_words", 15000),
            claims_file=domain_data.get("claims_file"),
        )

        # Load topics
        topics_yaml_path = domain_dir / "topics.yaml"
        topics_data = _load_yaml(topics_yaml_path).get("topics", [])
        topics = [TopicConfig.model_validate(t) for t in topics_data]

        # Load prompts
        prompts_py_path = domain_dir / "prompts.py"
        gk_prompt, met_prompt = _import_prompts_from_file(prompts_py_path)
        if not gk_prompt or not met_prompt:
            # Fallback to default prompts if not in directory
            from research_academy.llm.prompts import (
                GATEKEEPER_SYSTEM_PROMPT,
                METHODIST_SYSTEM_PROMPT,
            )
            gk_prompt = gk_prompt or GATEKEEPER_SYSTEM_PROMPT
            met_prompt = met_prompt or METHODIST_SYSTEM_PROMPT

        # Load claims
        claims_text = ""
        claims_file = domain_dir / (config.claims_file or "claims/PRODUCT_CLAIMS.md")
        if claims_file.exists():
            claims_text = claims_file.read_text(encoding="utf-8")
        elif (self.project_root / "knowledge_base" / "product" / "PRODUCT_CLAIMS.md").exists():
            claims_text = (self.project_root / "knowledge_base" / "product" / "PRODUCT_CLAIMS.md").read_text(encoding="utf-8")

        return DomainProfile(
            id=config.id,
            name=config.name,
            description=config.description,
            config=config,
            topics=topics,
            gatekeeper_prompt=gk_prompt,
            methodist_prompt=met_prompt,
            claims_text=claims_text,
            root_path=domain_dir,
        )

    def _create_crypto_fallback(self) -> DomainProfile:
        from research_academy.llm.prompts import (
            GATEKEEPER_SYSTEM_PROMPT,
            METHODIST_SYSTEM_PROMPT,
        )

        topics_path = self.project_root / "config" / "topics.yaml"
        topics_data = _load_yaml(topics_path).get("topics", [])
        topics = [TopicConfig.model_validate(t) for t in topics_data]

        claims_path = self.project_root / "knowledge_base" / "product" / "PRODUCT_CLAIMS.md"
        claims_text = claims_path.read_text(encoding="utf-8") if claims_path.exists() else ""

        config = DomainConfig(
            id="crypto",
            name="Syndicate Intelligence: Криптовалюты и микроструктура деска",
            description="Институциональная микроструктура рынка, дельта-нейтральный арбитраж, деривативы и анатомия манипуляций.",
            trusted_sources=["Wintermute", "Jump Trading"],
            blacklisted_domains=["tiktok.com", "instagram.com", "t.me"],
            default_prefilter_min_words=250,
            default_max_words=15000,
        )

        return DomainProfile(
            id="crypto",
            name=config.name,
            description=config.description,
            config=config,
            topics=topics,
            gatekeeper_prompt=GATEKEEPER_SYSTEM_PROMPT,
            methodist_prompt=METHODIST_SYSTEM_PROMPT,
            claims_text=claims_text,
            root_path=self.project_root / "domains" / "crypto",
        )
