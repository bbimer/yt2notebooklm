"""Web Search Provider and URL Normalizer with Cyrillic & Wikipedia fallback support."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    score: float = 7.0

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


def is_cf_blocked_or_empty(status_code: int, html: str) -> bool:
    """
    Evaluates whether the HTTP response is blocked by Cloudflare / anti-bot
    or contains an empty SPA / JavaScript shell with no prose content.
    """
    if status_code in (403, 429, 503):
        return True

    if not html or not html.strip():
        return True

    lower = html.lower()
    block_markers = [
        "just a moment...",
        "cf-browser-verification",
        "attention required! | cloudflare",
        "cloudflare ray id",
        "please verify you are a human",
        "enable javascript",
        "access denied",
        "ddos protection by cloudflare",
        "checking your browser before accessing",
    ]
    if any(m in lower for m in block_markers):
        return True

    # Strip script, style, noscript, svg to measure actual text payload
    clean_text = re.sub(r"<(script|style|svg|noscript)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<[^>]+>", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # If clean prose is less than 500 characters, it is an empty SPA or stub
    return len(clean_text) < 500


class WebSearchProvider:
    def __init__(
        self,
        user_agent: str = WIKIPEDIA_BOT_USER_AGENT,
        timeout: float = 15.0,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def smart_fetch_html(self, url: str) -> Tuple[int, str]:
        """
        Two-tier cascade fetcher:
        Tier 1 (Scalpel): curl_cffi with Chrome 124 TLS/JA3 impersonation (~0.3s).
        Tier 2 (Sledgehammer): AdsPower Local API (if running) or local Playwright Chromium.
        """
        canon_url = canonicalize_url(url)

        # Tier 1: curl_cffi
        try:
            from curl_cffi import requests as cffi_requests
            r = cffi_requests.get(
                canon_url,
                impersonate="chrome124",
                timeout=self.timeout,
                headers={"Accept-Language": "en-US,en;q=0.9,ru;q=0.8"}
            )
            if not is_cf_blocked_or_empty(r.status_code, r.text):
                logger.info("Tier 1 (curl_cffi) succeeded for %s (status=%d, len=%d)", canon_url, r.status_code, len(r.text))
                return r.status_code, r.text
            else:
                logger.warning("Tier 1 flagged CF block/empty SPA for %s (status=%d), triggering Tier 2 fallback", canon_url, r.status_code)
        except Exception as e:
            logger.warning("Tier 1 curl_cffi exception for %s: %s, triggering Tier 2 fallback", canon_url, e)

        # Tier 2: Sledgehammer Fallback (AdsPower or Playwright)
        return self._fetch_via_headless(canon_url)

    def _fetch_via_headless(self, url: str) -> Tuple[int, str]:
        """
        Fallback renderer: checks AdsPower Local API, then defaults to local Playwright Chromium.
        """
        import json
        import os
        adspower_api = os.getenv("ADSPOWER_API", "http://local.adspower.net:50325")
        profile_id = os.getenv("ADSPOWER_PROFILE_ID", "")

        # 1. Check if AdsPower Local API is listening and configured
        if profile_id and profile_id != "k123456":
            try:
                import urllib.request
                resp = urllib.request.urlopen(f"{adspower_api}/status", timeout=1.5)
                if resp.status == 200:
                    logger.info("AdsPower is active, attempting launch with profile %s", profile_id)
                    start_resp = urllib.request.urlopen(f"{adspower_api}/api/v1/browser/start?user_id={profile_id}", timeout=10)
                    start_data = json.loads(start_resp.read().decode())
                    if start_data.get("code") == 0:
                        ws_endpoint = start_data["data"]["ws"]["puppeteer"]
                        from playwright.sync_api import sync_playwright
                        with sync_playwright() as p:
                            browser = p.chromium.connect_over_cdp(ws_endpoint)
                            context = browser.contexts[0]
                            page = context.new_page()
                            try:
                                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                                page.wait_for_timeout(2000)
                                content = page.content()
                                return 200, content
                            finally:
                                page.close()
            except Exception as e:
                logger.warning("AdsPower fallback error for %s: %s, falling back to local Playwright", url, e)

        # 2. Local Playwright Chromium Fallback
        try:
            logger.info("Executing Tier 2 local Playwright Chromium for %s", url)
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2000)
                    content = page.content()
                    return 200, content
                finally:
                    browser.close()
        except Exception as e:
            logger.error("Tier 2 Playwright failed for %s: %s", url, e)
            return 0, f"FETCH_ERROR: {e}"

    def fetch_html(self, url: str) -> Tuple[int, str]:
        """Downloads HTML content using smart two-tier cascade."""
        return self.smart_fetch_html(url)

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
            try:
                from ddgs import DDGS
            except ImportError:
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

    def search_for_topic(
        self,
        topic: Any,
        domain_config: Any,
        max_results: int = 5,
    ) -> List[WebSearchResult]:
        """
        Discovers candidate URLs for a given topic across its web_queries.
        """
        queries = getattr(topic, "web_queries", None) or getattr(topic, "queries_en", []) or getattr(topic, "queries_ru", [])
        trusted = getattr(domain_config, "trusted_sources", [])
        blacklist = getattr(domain_config, "blacklisted_domains", [])

        seen_urls = set()
        out: List[WebSearchResult] = []

        for q in queries:
            raw_hits = self.search(
                query=q,
                max_results=max_results,
                blacklisted_domains=blacklist,
                trusted_sources=trusted,
            )
            for hit in raw_hits:
                u = hit["url"]
                if u not in seen_urls:
                    seen_urls.add(u)
                    is_trusted = any(ts.lower() in u.lower() for ts in trusted)
                    score = 9.0 if is_trusted else 7.5
                    out.append(WebSearchResult(
                        title=hit["title"],
                        url=u,
                        snippet=hit.get("snippet", ""),
                        source=hit.get("source", ""),
                        score=score,
                    ))
                    if len(out) >= max_results:
                        break
            if len(out) >= max_results:
                break
        return out

