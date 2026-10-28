"""Web Search Provider and URL Normalizer with Cyrillic & Wikipedia fallback support."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse
import httpx

logger = logging.getLogger(__name__)

TRACKING_QUERY_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "yclid", "ysclid", "from", "source", "_openstat"
}

WIKIPEDIA_BOT_USER_AGENT = (
    "ResearchAcademyBot/1.0 (+https://github.com/bbimer/yt2notebooklm; contact@nullspread.io)"
)


def canonicalize_url(url: str) -> str:
    """
    Normalizes URLs into a canonical format:
    1. Unquotes percent-encoded UTF-8 / Cyrillic characters (so %D0%94... and readable match)
    2. Strips tracking query parameters (utm_*, ref, fbclid, etc.)
    3. Strips anchor fragments (#section)
    4. Strips trailing slashes
    """
    if not url:
        return ""

    parsed = urlparse(url.strip())
    # 1. Unquote path to handle Cyrillic consistently
    path = unquote(parsed.path)
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # 2. Filter out tracking params from query
    query_items = parse_qsl(parsed.query)
    clean_query_items = [(k, v) for k, v in query_items if k.lower() not in TRACKING_QUERY_PARAMS]
    clean_query = urlencode(clean_query_items)

    # 3. Assemble canonical URL without fragment
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()

    canonical = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
    return canonical


def generate_document_id(url: str) -> str:
    """Generates deterministic document_id hash from canonical URL."""
    canon = canonicalize_url(url)
    h = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]
    return f"web_{h}"


class WebSearchProvider:
    def __init__(
        self,
        user_agent: str = WIKIPEDIA_BOT_USER_AGENT,
        timeout: float = 12.0,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def fetch_html(self, url: str) -> Tuple[int, str]:
        """Downloads HTML content using httpx with custom headers and redirects."""
        canon_url = canonicalize_url(url)
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(canon_url, headers=self.headers)
                return resp.status_code, resp.text
        except Exception as e:
            logger.warning("Error fetching URL %s: %s", canon_url, e)
            return 0, f"FETCH_ERROR: {e}"

    def search(
        self,
        query: str,
        max_results: int = 5,
        blacklisted_domains: Optional[List[str]] = None,
        trusted_sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discovers candidate URLs via DuckDuckGo with Wikipedia OpenSearch API fallback.
        Filters blacklisted domains and prioritizes trusted sources.
        """
        results: List[Dict[str, Any]] = []
        blacklist = set(blacklisted_domains or [])

        # 1. Try DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            ddg_raw = list(ddgs.text(query, max_results=max_results * 2))
            for item in ddg_raw:
                href = item.get("href") or item.get("url") or ""
                if not href:
                    continue
                canon = canonicalize_url(href)
                domain = urlparse(canon).netloc
                if any(bad in domain for bad in blacklist):
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "url": canon,
                    "snippet": item.get("body", ""),
                    "source": "duckduckgo",
                })
        except Exception as e:
            logger.info("DuckDuckGo search unavailable or blocked (%s), using Wikipedia OpenSearch", e)

        # 2. Augment / Fallback via Wikipedia OpenSearch API
        if len(results) < max_results:
            wiki_results = self._search_wikipedia(query, max_results=max_results)
            for w in wiki_results:
                canon = canonicalize_url(w["url"])
                if not any(r["url"] == canon for r in results):
                    results.append(w)

        # 3. Boost trusted sources to top
        if trusted_sources:
            def trusted_key(item: Dict[str, Any]) -> int:
                u = item["url"].lower()
                return 0 if any(ts.lower() in u for ts in trusted_sources) else 1

            results.sort(key=trusted_key)

        return results[:max_results]

    def _search_wikipedia(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Queries Wikipedia OpenSearch API (RU or EN depending on script)."""
        is_cyrillic = bool(re.search(r"[\u0400-\u04FF]", query))
        wiki_lang = "ru" if is_cyrillic else "en"
        api_url = f"https://{wiki_lang}.wikipedia.org/w/api.php"

        params = {
            "action": "opensearch",
            "search": query,
            "limit": max_results,
            "format": "json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(api_url, params=params, headers=self.headers)
                if r.status_code == 200:
                    data = r.json()
                    # data format: [query, [titles], [descriptions], [urls]]
                    if len(data) >= 4:
                        titles = data[1]
                        snippets = data[2]
                        urls = data[3]
                        out = []
                        for t, s, u in zip(titles, snippets, urls):
                            out.append({
                                "title": t,
                                "url": canonicalize_url(u),
                                "snippet": s or t,
                                "source": "wikipedia_opensearch",
                            })
                        return out
        except Exception as e:
            logger.warning("Wikipedia OpenSearch error for query '%s': %s", query, e)

        return []

