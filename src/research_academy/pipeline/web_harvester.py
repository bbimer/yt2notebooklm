"""Web Harvester: Ingests primary web sources and coordinates discovery and extraction."""

from __future__ import annotations

import json
import logging
from typing import List, Optional
import httpx

from research_academy.config import AppConfig
from research_academy.database import Database
from research_academy.domain.manager import DomainManager
from research_academy.models import (
    DiscoveryStatus,
    SourceContent,
    WebDocumentMetadata,
)
from research_academy.providers.web_extractor import DEFAULT_USER_AGENT, WebArticleExtractor
from research_academy.providers.web_provider import (
    WebSearchProvider,
    canonicalize_url,
    generate_document_id,
)

logger = logging.getLogger(__name__)


class WebHarvester:
    def __init__(
        self,
        config: AppConfig,
        db: Database,
        domain_manager: Optional[DomainManager] = None,
        extractor: Optional[WebArticleExtractor] = None,
        search_provider: Optional[WebSearchProvider] = None,
    ):
        self.config = config
        self.db = db
        self.domain_manager = domain_manager or DomainManager(config.project_root)
        self.extractor = extractor or WebArticleExtractor()
        self.search_provider = search_provider or WebSearchProvider()

    def ingest_url(
        self,
        url: str,
        topic_id: str = "general",
        domain: str = "computer_science",
        force_fetch: bool = False,
    ) -> SourceContent:
        """
        Fetches, decompiles and registers a primary web source into SQLite and SourceContent.
        """
        canon_url = canonicalize_url(url)
        doc_id = generate_document_id(canon_url)

        # Check existing in DB unless force_fetch
        if not force_fetch:
            existing = self.db.get_document(doc_id)
            if existing and existing.discovery_status in (
                DiscoveryStatus.EXTRACTED,
                DiscoveryStatus.PUBLISHED,
                DiscoveryStatus.GATEKEEPER_ACCEPTED,
            ):
                logger.info("Document %s already extracted in DB", doc_id)
                outline = json.loads(existing.outline_json) if existing.outline_json else []
                segments, _ = self.extractor._chunk_into_segments(existing.clean_markdown)
                return SourceContent(
                    source_id=existing.document_id,
                    source_type="web",
                    domain=existing.domain,
                    topic_id=existing.topic_id,
                    title=existing.title,
                    url=existing.url,
                    author_or_domain=existing.author_or_domain,
                    segments=segments,
                    full_clean_text=existing.clean_markdown,
                    word_count=existing.word_count,
                    has_high_density_data=any(s.has_table or s.has_code for s in segments),
                    outline=outline,
                )

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            with httpx.Client(timeout=30.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(canon_url)
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            logger.error("Failed to fetch %s: %s", canon_url, e)
            doc_meta = WebDocumentMetadata(
                document_id=doc_id,
                domain=domain,
                topic_id=topic_id,
                url=canon_url,
                title="Fetch Error",
                author_or_domain=canon_url,
                clean_markdown="",
                word_count=0,
                discovery_status=DiscoveryStatus.REJECTED_EXTRACTION,
                status_reason=f"HTTP fetch failed: {e}",
            )
            self.db.upsert_document(doc_meta)
            raise RuntimeError(f"Could not fetch {canon_url}: {e}") from e

        # Extract
        extraction = self.extractor.extract_from_html(html, canon_url)

        # Save to DB
        doc_meta = WebDocumentMetadata(
            document_id=doc_id,
            domain=domain,
            topic_id=topic_id,
            url=canon_url,
            title=extraction.title,
            author_or_domain=extraction.author_or_domain,
            clean_markdown=extraction.clean_markdown,
            outline_json=json.dumps(extraction.outline, ensure_ascii=False),
            word_count=extraction.word_count,
            discovery_status=extraction.status,
            status_reason=extraction.status_reason,
        )
        self.db.upsert_document(doc_meta)

        source = SourceContent(
            source_id=doc_id,
            source_type="web",
            domain=domain,
            topic_id=topic_id,
            title=extraction.title,
            url=canon_url,
            author_or_domain=extraction.author_or_domain,
            segments=extraction.segments,
            full_clean_text=extraction.clean_markdown,
            word_count=extraction.word_count,
            has_high_density_data=extraction.has_high_density_data,
            outline=extraction.outline,
        )

        return source

    def harvest_topic(
        self,
        topic_id: str,
        domain: str = "computer_science",
        max_results: int = 5,
    ) -> List[SourceContent]:
        """
        Discovers relevant primary web sources for topic and extracts them into SourceContent.
        """
        domain_profile = self.domain_manager.get_domain(domain)
        topic = domain_profile.get_topic(topic_id)
        if not topic:
            logger.warning("Topic %s not found in domain %s", topic_id, domain)
            return []

        search_results = self.search_provider.search_for_topic(
            topic=topic,
            domain_config=domain_profile.config,
            max_results=max_results,
        )

        sources: List[SourceContent] = []
        for res in search_results:
            try:
                source = self.ingest_url(
                    url=res.url,
                    topic_id=topic_id,
                    domain=domain,
                )
                if source.word_count >= self.extractor.min_words:
                    sources.append(source)
            except Exception as e:
                logger.warning("Could not ingest %s: %s", res.url, e)

        return sources

