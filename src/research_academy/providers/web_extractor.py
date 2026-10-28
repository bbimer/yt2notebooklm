"""High-fidelity Web Article Extractor and DOM Decompiler.

Decompiles raw HTML into structured Markdown, preserves mathematical formulas,
HTML sub/sup indices, tables, and code blocks, segments by H1-H3 headers ([SEC-XX]),
and enforces quality gates against anti-bot pages and empty SPAs.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup, NavigableString, Tag

from research_academy.models import ContentSegment, DiscoveryStatus

logger = logging.getLogger(__name__)

STOP_PATTERNS = [
    r"just a moment\.\.\.",
    r"enable javascript",
    r"attention required",
    r"access denied",
    r"cloudflare ray id",
    r"checking your browser",
    r"please verify you are a human",
    r"unsupported browser",
    r"ddos protection by cloudflare",
]

DEFAULT_USER_AGENT = (
    "ResearchAcademyBot/1.0 (+https://github.com/bbimer/yt2notebooklm; contact@nullspread.io)"
)


class WebExtractionResult:
    def __init__(
        self,
        clean_markdown: str,
        segments: List[ContentSegment],
        title: str,
        author_or_domain: str,
        outline: List[str],
        word_count: int,
        status: DiscoveryStatus,
        status_reason: Optional[str] = None,
        has_high_density_data: bool = False,
    ):
        self.clean_markdown = clean_markdown
        self.segments = segments
        self.title = title
        self.author_or_domain = author_or_domain
        self.outline = outline
        self.word_count = word_count
        self.status = status
        self.status_reason = status_reason
        self.has_high_density_data = has_high_density_data


class WebArticleExtractor:
    def __init__(
        self,
        min_words: int = 250,
        max_words: int = 15000,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.min_words = min_words
        self.max_words = max_words
        self.user_agent = user_agent

    def extract_from_html(self, html: str, url: str = "") -> WebExtractionResult:
        """Decompiles HTML into structured Markdown with [SEC-XX] segments and quality check."""
        domain_name = urlparse(url).netloc if url else "web_source"
        soup = BeautifulSoup(html, "html.parser")

        # 1. Pre-Extraction Quality Gate on raw HTML
        lower_html = html.lower()[:3000]
        for pat in STOP_PATTERNS:
            if re.search(pat, lower_html):
                return WebExtractionResult(
                    clean_markdown="",
                    segments=[],
                    title="Blocked / Anti-Bot Page",
                    author_or_domain=domain_name,
                    outline=[],
                    word_count=0,
                    status=DiscoveryStatus.REJECTED_EXTRACTION,
                    status_reason=f"Quality Gate rejected: Detected anti-bot / Cloudflare pattern ('{pat}')",
                )

        # 2. Extract Title
        title = self._extract_title(soup, url)

        # 3. Clean Wikipedia & Navigation Artifacts
        self._decompose_unwanted_elements(soup)

        # 4. Content Density Fallback (Find Main Container)
        container = self._find_content_container(soup)
        if not container:
            return WebExtractionResult(
                clean_markdown="",
                segments=[],
                title=title,
                author_or_domain=domain_name,
                outline=[],
                word_count=0,
                status=DiscoveryStatus.REJECTED_EXTRACTION,
                status_reason="Quality Gate rejected: No content container found",
            )

        # 5. Transform formulas, math images, sub and sup
        self._transform_math_and_indices(container)

        # 6. Parse DOM into Markdown with structural preservation
        markdown_text = self._dom_to_markdown(container).strip()
        words = markdown_text.split()
        word_count = len(words)

        # 7. Post-Extraction Quality Gate
        if word_count < self.min_words:
            return WebExtractionResult(
                clean_markdown=markdown_text,
                segments=[],
                title=title,
                author_or_domain=domain_name,
                outline=[],
                word_count=word_count,
                status=DiscoveryStatus.REJECTED_EXTRACTION,
                status_reason=f"Quality Gate rejected: word_count {word_count} < {self.min_words} words (empty SPA or stub)",
            )

        # 8. Slicing into [SEC-XX | Title] segments
        segments, outline = self._chunk_into_segments(markdown_text)
        has_density = any(s.has_table or s.has_code for s in segments)

        # 9. Truncate if exceeds max_words (prioritizing SEC-01, conclusions, and density blocks)
        if word_count > self.max_words:
            segments, markdown_text, word_count = self._truncate_with_priority(segments)

        return WebExtractionResult(
            clean_markdown=markdown_text,
            segments=segments,
            title=title,
            author_or_domain=domain_name,
            outline=outline,
            word_count=word_count,
            status=DiscoveryStatus.EXTRACTED,
            status_reason="Successfully decompiled and segmented",
            has_high_density_data=has_density,
        )

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        # Check og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return str(og_title["content"]).strip()
        # Check h1
        h1 = soup.find("h1")
        if h1 and h1.get_text().strip():
            return h1.get_text().strip()
        # Check <title>
        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            # Clean common suffixes like " - Википедия"
            title_text = re.sub(r"\s*[-—|]\s*(Википедия|Wikipedia|Habr|Хабр).*$", "", title_text, flags=re.IGNORECASE)
            return title_text
        return url or "Untitled Document"

    def _decompose_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Removes scripts, styles, popups, and wiki edit links/references."""
        # Standard garbage tags
        for tag in soup.find_all(
            ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg", "form", "button"]
        ):
            tag.decompose()

        # Wikipedia-specific artifacts (footnotes, edit section links)
        for tag in soup.find_all(["sup", "span"], class_=lambda c: c and any(x in str(c) for x in ["reference", "mw-editsection", "noprint", "navbox"])):
            tag.decompose()

        # Common ad and tracking classes/IDs
        bad_selectors = [
            "cookie", "popup", "banner", "subscribe", "related", "comments",
            "sidebar", "breadcrumb", "advertisement", "share-buttons", "social-share",
            "catlinks", "toc", "#toc"
        ]
        for tag in soup.find_all(lambda t: t.name in ["div", "section", "p", "ul", "aside"] and any(
            bad in str(t.get("class", "")) or bad in str(t.get("id", "")) for bad in bad_selectors
        )):
            tag.decompose()

    def _find_content_container(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Finds primary content container using semantic tags, common classes, or density heuristic."""
        # Priority 1: Semantic tags
        for sel in ["article", "main", '[role="main"]']:
            found = soup.select_one(sel)
            if found and len(found.get_text().split()) >= 50:
                return found

        # Priority 2: Common technical / documentation containers
        common_classes = [
            ".post-content", ".article-body", ".markdown-body", "#content",
            "#mw-content-text", ".mw-parser-output", ".entry-content", ".content"
        ]
        for sel in common_classes:
            found = soup.select_one(sel)
            if found and len(found.get_text().split()) >= 50:
                return found

        # Priority 3: Heuristic: div with highest ratio of text length to link tags
        candidates = []
        for div in soup.find_all(["div", "section"]):
            text = div.get_text()
            words = len(text.split())
            if words < 60:
                continue
            links_count = len(div.find_all("a"))
            ratio = words / (links_count + 1)
            candidates.append((ratio, words, div))

        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            return candidates[0][2]

        return soup.body or soup

    def _transform_math_and_indices(self, container: Tag) -> None:
        """Converts math elements, <sub>, and <sup> into LaTeX and formatted markdown."""
        # 1. LaTeX math tags / images
        for tag in container.find_all(["math", "span"], class_=lambda c: c and "mwe-math" in str(c)):
            alt = tag.get("alttext") or tag.get("alt")
            img = tag.find("img")
            if not alt and img and img.get("alt"):
                alt = img["alt"]
            if alt:
                tag.replace_with(f" ${alt.strip()}$ ")

        for img in container.find_all("img", class_=lambda c: c and "math" in str(c)):
            alt = img.get("alt") or img.get("alttext")
            if alt:
                img.replace_with(f" ${alt.strip()}$ ")

        # 2. Meaningful sub indices (e.g. 1011_2)
        for sub in container.find_all("sub"):
            text = sub.get_text().strip()
            if text:
                sub.replace_with(f"_{{{text}}}")

        # 3. Meaningful sup indices (e.g. 2^{16})
        for sup in container.find_all("sup"):
            text = sup.get_text().strip()
            if text:
                sup.replace_with(f"^{{{text}}}")

    def _dom_to_markdown(self, element: Tag) -> str:
        """Custom recursive DOM-walker converting tables, code, lists, and headers to Markdown."""
        chunks: List[str] = []

        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child)
                if text.strip():
                    chunks.append(text)
                continue

            if not isinstance(child, Tag):
                continue

            tag_name = child.name.lower()

            if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(tag_name[1])
                prefix = "#" * level
                header_text = child.get_text().strip()
                if header_text:
                    chunks.append(f"\n\n{prefix} {header_text}\n\n")

            elif tag_name == "p":
                p_text = self._element_inline_markdown(child).strip()
                if p_text:
                    chunks.append(f"\n\n{p_text}\n\n")

            elif tag_name == "table":
                table_md = self._table_to_markdown(child)
                if table_md.strip():
                    chunks.append(f"\n\n{table_md}\n\n")

            elif tag_name in ["pre", "code"] and child.parent.name != "pre":
                code_text = child.get_text().rstrip()
                chunks.append(f"\n\n```\n{code_text}\n```\n\n")

            elif tag_name in ["ul", "ol"]:
                list_md = self._list_to_markdown(child, is_ordered=(tag_name == "ol"))
                if list_md.strip():
                    chunks.append(f"\n\n{list_md}\n\n")

            elif tag_name == "blockquote":
                quote_text = child.get_text().strip()
                lines = [f"> {line}" for line in quote_text.splitlines() if line.strip()]
                chunks.append("\n\n" + "\n".join(lines) + "\n\n")

            else:
                # Recurse for containers (div, section, span)
                sub_md = self._dom_to_markdown(child)
                if sub_md.strip():
                    chunks.append(sub_md)

        # Normalize redundant newlines
        joined = "".join(chunks)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined

    def _element_inline_markdown(self, element: Tag) -> str:
        """Converts inline tags like <b>, <i>, <code> within a paragraph."""
        parts: List[str] = []
        for c in element.children:
            if isinstance(c, NavigableString):
                parts.append(str(c))
            elif isinstance(c, Tag):
                c_name = c.name.lower()
                c_text = c.get_text()
                if c_name in ["strong", "b"]:
                    parts.append(f"**{c_text.strip()}**")
                elif c_name in ["em", "i"]:
                    parts.append(f"*{c_text.strip()}*")
                elif c_name == "code":
                    parts.append(f"`{c_text.strip()}`")
                else:
                    parts.append(c_text)
        return "".join(parts)

    def _table_to_markdown(self, table: Tag) -> str:
        """Converts HTML table into GFM Markdown table."""
        rows = table.find_all("tr")
        if not rows:
            return ""

        table_data: List[List[str]] = []
        for r in rows:
            cells = r.find_all(["th", "td"])
            if not cells:
                continue
            row_vals = [" ".join(c.get_text().split()).replace("|", "\\|") for c in cells]
            table_data.append(row_vals)

        if not table_data:
            return ""

        # Normalize column counts
        max_cols = max(len(r) for r in table_data)
        if max_cols == 0:
            return ""

        for r in table_data:
            while len(r) < max_cols:
                r.append("")

        md_lines = []
        # Header row
        header_row = table_data[0]
        md_lines.append("| " + " | ".join(header_row) + " |")
        md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

        for row in table_data[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def _list_to_markdown(self, list_tag: Tag, is_ordered: bool = False) -> str:
        """Converts ul/ol into Markdown list."""
        items = list_tag.find_all("li", recursive=False)
        lines = []
        for i, li in enumerate(items, 1):
            text = " ".join(li.get_text().split())
            if text:
                prefix = f"{i}." if is_ordered else "-"
                lines.append(f"{prefix} {text}")
        return "\n".join(lines)

    def _chunk_into_segments(self, markdown: str) -> Tuple[List[ContentSegment], List[str]]:
        """Splits markdown by headings into [SEC-XX | Title] segments."""
        raw_sections = re.split(r"(^#{1,3}\s+[^\n]+)", markdown, flags=re.MULTILINE)
        segments: List[ContentSegment] = []
        outline: List[str] = []

        current_title = "Введение"
        current_text = ""

        def add_segment(title: str, text: str):
            clean_text = text.strip()
            if not clean_text:
                return
            idx = len(segments) + 1
            sec_id = f"SEC-{idx:02d} | {title}"
            has_table = "|" in clean_text and "---" in clean_text
            has_code = "```" in clean_text
            words = len(clean_text.split())
            seg = ContentSegment(
                index=idx,
                anchor_id=sec_id,
                title=title,
                text=clean_text,
                has_table=has_table,
                has_code=has_code,
                word_count=words,
            )
            segments.append(seg)
            outline.append(sec_id)

        i = 0
        while i < len(raw_sections):
            part = raw_sections[i].strip()
            if not part:
                i += 1
                continue

            if part.startswith("#"):
                # If we had accumulated text, flush it
                if current_text.strip():
                    add_segment(current_title, current_text)
                    current_text = ""
                # New heading
                current_title = re.sub(r"^#{1,3}\s+", "", part).strip()
                i += 1
            else:
                current_text += "\n\n" + part
                i += 1

        if current_text.strip():
            add_segment(current_title, current_text)

        # Fallback if flat text had no headings
        if not segments and markdown.strip():
            # Chunk by ~2000 characters
            chunk_size = 2000
            for start in range(0, len(markdown), chunk_size):
                chunk = markdown[start : start + chunk_size]
                add_segment(f"Раздел {len(segments) + 1}", chunk)

        return segments, outline

    def _truncate_with_priority(
        self, segments: List[ContentSegment]
    ) -> Tuple[List[ContentSegment], str, int]:
        """Truncates segments to max_words preserving SEC-01, conclusions, and density blocks."""
        if not segments:
            return segments, "", 0

        # Always keep first and last
        selected_indices = {0, len(segments) - 1}
        # Keep all segments with tables or code
        for i, s in enumerate(segments):
            if s.has_table or s.has_code:
                selected_indices.add(i)

        # Fill remaining budget from beginning
        sorted_indices = sorted(list(selected_indices))
        current_words = sum(segments[i].word_count for i in sorted_indices)

        for i in range(len(segments)):
            if i not in selected_indices:
                w = segments[i].word_count
                if current_words + w <= self.max_words:
                    selected_indices.add(i)
                    current_words += w

        final_indices = sorted(list(selected_indices))
        final_segments = [segments[i] for i in final_indices]
        # Re-index
        for new_idx, s in enumerate(final_segments, 1):
            s.index = new_idx

        new_md = "\n\n".join(s.text for s in final_segments)
        return final_segments, new_md, sum(s.word_count for s in final_segments)

