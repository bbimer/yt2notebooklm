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

        status_code, html = self.search_provider.smart_fetch_html(canon_url)
        if status_code != 200 or not html or html.startswith("FETCH_ERROR:"):
            logger.error("Failed to fetch %s: status=%d", canon_url, status_code)
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
                status_reason=f"HTTP fetch failed: status={status_code}",
            )
            self.db.upsert_document(doc_meta)
            raise RuntimeError(f"Could not fetch {canon_url}: status={status_code}")

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
        domain: str = "crypto",
        max_results: int = 8,
    ) -> List[SourceContent]:
        """
        Discovers relevant primary web sources for a topic across its configured web_queries,
        selecting the top 1 unique valid result per query to build a comprehensive ground truth.
        """
        domain_profile = self.domain_manager.get_domain(domain)
        topic = domain_profile.get_topic(topic_id)
        if not topic:
            logger.warning("Topic %s not found in domain %s", topic_id, domain)
            return []

        queries = getattr(topic, "web_queries", None) or (topic.queries_en + topic.queries_ru)
        trusted = getattr(domain_profile.config, "trusted_sources", [])
        blacklist = getattr(domain_profile.config, "blacklisted_domains", [])

        sources: List[SourceContent] = []
        seen_urls = set()

        for q in queries:
            if len(sources) >= max_results:
                break
            hits = self.search_provider.search(
                query=q,
                max_results=3,
                blacklisted_domains=blacklist,
                trusted_sources=trusted,
            )
            for h in hits:
                canon_u = canonicalize_url(h["url"])
                if canon_u in seen_urls:
                    continue
                try:
                    logger.info("Harvesting query '%s' -> %s", q, canon_u)
                    source = self.ingest_url(url=canon_u, topic_id=topic_id, domain=domain)
                    if source.word_count >= self.extractor.min_words:
                        seen_urls.add(canon_u)
                        sources.append(source)
                        break  # Take top 1 unique successful document per query
                except Exception as e:
                    logger.warning("Could not ingest %s: %s", canon_u, e)

        return sources

