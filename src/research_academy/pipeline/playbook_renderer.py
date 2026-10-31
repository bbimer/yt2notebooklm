"""Playwright and Pandoc based document renderer for Sales Playbooks and Battlecards."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright

PANDOC_PATH = r"C:\Users\root\AppData\Local\Pandoc\pandoc.exe"


class PlaybookRenderer:
    def __init__(self, pandoc_path: str = PANDOC_PATH):
        self.pandoc_path = pandoc_path if os.path.exists(pandoc_path) else "pandoc"

    @classmethod
    def preprocess_markdown(cls, text: str) -> str:
        r"""
        Robust preprocessor for Sales Playbook and Battlecard documents:
        1. Normalizes accidental double-dollar signs before digits ($$3,000 -> $3,000).
        2. Protects code blocks (```...``` and `...`).
        3. Converts block formulas $$...$$ to \[...\] with isolated paragraph spacing.
        4. Normalizes pseudo-math ranges, multiples, percentages, and tickers.
        5. Converts legitimate inline LaTeX math $...$ into \(...\) for Pandoc/KaTeX.
        6. Injects blank lines before markdown lists to prevent paragraph-list merging.
        7. Converts GitHub callouts (> [!WARNING], > [!CAUTION]) to standard bold alerts.
        8. Cleans up dangling bold asterisks (*** -> **).
        9. Restores protected blocks.
        """

        placeholders = []

        def save_block(m):
            placeholders.append(m.group(0))
            return f"___BLOCK_PLACEHOLDER_{len(placeholders)-1}___"

        # 1. Protect code blocks
        text = re.sub(r"```[\s\S]*?```", save_block, text)
        text = re.sub(r"`[^`\n]+`", save_block, text)

        # 2. Convert block formulas $$...$$ to \[...\]
        def clean_display_math(m):
            math_content = m.group(1).strip()
            # Strip blockquote '>' prefixes inside math lines
            math_content = re.sub(r"(?m)^\s*>\s*", "", math_content)
            # Remove currency dollar signs inside math mode so KaTeX does not crash
            math_content = re.sub(r"\$(\d+(?:\.\d+)?)", r"\1", math_content)
            return f"\n\n\\[\n{math_content}\n\\]\n\n"

        text = re.sub(r"\$\$([\s\S]*?)\$\$", clean_display_math, text)

        # 3. Clean pseudo-math ranges, percentages, multipliers, tickers
        # Currency ranges: $10--$50 or $10\text{--}$50
        text = re.sub(r"\$([0-9.]+)\s*(?:\\text\{--\}|--)\s*\$([0-9.]+)\$", r"$\1–$\2", text)
        # Percentage ranges: $20--40\%$ or $75.0\text{--}80.0\%$
        text = re.sub(r"\$([0-9.]+)(?:\\\%|\%)?\s*(?:\\text\{--\}|--)\s*([0-9.]+)(?:\\\%|\%)\$", r"\1–\2%", text)
        # Number ranges: $10\text{--}50$ or $10--50$
        text = re.sub(r"\$([0-9.]+)\s*(?:\\text\{--\}|--)\s*([0-9.]+)\$", r"\1–\2", text)
        # Parenthesized percentage ranges: ($85\%--95\%$)
        text = re.sub(r"\(([0-9.]+)(?:\\\%|\%)?\s*(?:\\text\{--\}|--)\s*([0-9.]+)(?:\\\%|\%)\)", r"(\1–\2%)", text)
        # Tickers inside dollar signs
        text = re.sub(r"\$(USDC|USDT|ETH|stETH|WETH|ETH-PERP|ETH/USDT|BTC|SOL|DAI|TIA|WLFI|crvUSD|STRK|JTO|PYTH|ICP|OXY|AXS|APE|MNGO|MNGO-PERP)\$", r"\1", text)
        # Multipliers: $120\times$ or $120x$
        text = re.sub(r"\$([0-9,.]+)(?:\\times|x)\$", r"\1x", text)
        # Pure signed/unsigned percentages: $+145\%$ or $-164.25\%$
        text = re.sub(r"\$([+-]?[0-9.]+(?:\\\%|\%))\$", lambda m: m.group(1).replace(r"\%", "%"), text)
        # Isolated \times
        text = re.sub(r"\$\\times\$", "×", text)
        # Pure signed numbers: $+250$
        text = re.sub(r"\$([+-]\d+)\$", r"\1", text)

        # 4. Convert legitimate inline LaTeX math $...$ into \(...\)
        def convert_inline_math(m):
            inner = m.group(1).strip()
            # If it looks like currency or plain numbers, don't convert
            if re.match(r'^[0-9,.]+(?:\s*(?:млн|млрд|k|M|USD|USDT|USDC))?$', inner):
                return m.group(0)
            # LaTeX indicators
            if any(tok in inner for tok in ['\\', '_', '^', '{', '}', '∑', '∏', 'Δ', 'σ', '∝', '≈', '≤', '≥', '→', '±', '×']):
                return f"\\({inner}\\)"
            # Function notation: P(t), S(t), M(t)
            if re.match(r'^[A-Za-z]\([a-z]\)$', inner):
                return f"\\({inner}\\)"
            return m.group(0)

        text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', convert_inline_math, text)

        # 5. Inject missing blank lines before lists
        lines = text.split("\n")
        new_lines = []
        list_re = re.compile(r"^(\s*)([*+-]|\d+\.)\s+")
        for i, line in enumerate(lines):
            if list_re.match(line) and i > 0:
                prev = lines[i - 1].strip()
                if prev and not list_re.match(prev) and not prev.startswith("#") and not prev.startswith(">") and not prev.startswith("|"):
                    new_lines.append("")
            new_lines.append(line)
        text = "\n".join(new_lines)

        # 6. Replace GitHub callout syntax
        text = re.sub(r">\s*\[!(?:WARNING|CAUTION)\]\s*", "> **ВНИМАНИЕ:** ", text)
        text = re.sub(r">\s*\[!NOTE\]\s*", "> **ПРИМЕЧАНИЕ:** ", text)
        text = re.sub(r">\s*\[!IMPORTANT\]\s*", "> **ВАЖНО:** ", text)
        text = re.sub(r">\s*\[!TIP\]\s*", "> **СОВЕТ:** ", text)

        # 7. Fix dangling asterisks
        text = re.sub(r"\*{3,}", "**", text)

        # 8. Restore protected blocks
        for idx, block in enumerate(placeholders):
            text = text.replace(f"___BLOCK_PLACEHOLDER_{idx}___", block)

        return text

    def render_docx(self, markdown_path: Path, output_docx_path: Path) -> Path:
        """Converts Markdown to a formatted Word .docx document using Pandoc."""
        output_docx_path.parent.mkdir(parents=True, exist_ok=True)
        raw_md = markdown_path.read_text(encoding="utf-8")
        clean_md = self.preprocess_markdown(raw_md)
        temp_md_path = output_docx_path.with_suffix(".tmp.md")
        temp_md_path.write_text(clean_md, encoding="utf-8")

        try:
            cmd = [
                self.pandoc_path,
                "-f", "markdown-tex_math_dollars+tex_math_single_backslash+pipe_tables",
                str(temp_md_path),
                "-t", "docx",
                "-o", str(output_docx_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
        finally:
            if temp_md_path.exists():
                temp_md_path.unlink()

        return output_docx_path

    def render_pdf(
        self,
        markdown_path: Path,
        output_pdf_path: Path,
        title: str = "Institutional Sales Playbook",
        subtitle: str = "Research & Sales Academy",
        is_battlecard: bool = False,
    ) -> Path:
        """
        Converts Markdown to a styled corporate PDF using Pandoc + KaTeX + Playwright Chromium.
        Supports custom callout styling for:
        - МЕТАФОРА / ВЕКТОР А
        - КЕЙС / Криминалистика
        - UNIT-ЭКОНОМИКА / ВЕКТОР Б
        - ТЕХНИЧЕСКИЙ ПРУФ / Под капотом
        - СКРИПТ ЗАКРЫТИЯ / Скрипт
        """
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        raw_md = markdown_path.read_text(encoding="utf-8")
        clean_md = self.preprocess_markdown(raw_md)
        temp_md_path = output_pdf_path.with_suffix(".tmp.md")
        temp_md_path.write_text(clean_md, encoding="utf-8")

        # 1. Convert markdown to HTML body via Pandoc with KaTeX and disabled dollar math
        try:
            cmd = [
                self.pandoc_path,
                "-f", "markdown-tex_math_dollars+tex_math_single_backslash+pipe_tables",
                str(temp_md_path),
                "-t", "html",
                "--katex",
            ]
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
            body_html = proc.stdout
        finally:
            if temp_md_path.exists():
                temp_md_path.unlink()

        # 2. Enrich HTML with specialized callout styling
        body_html = self._apply_callout_containers(body_html)

        # 3. Build complete standalone HTML with KaTeX and corporate styling
        full_html = self._build_html_template(
            body_html=body_html,
            title=title,
            subtitle=subtitle,
            is_battlecard=is_battlecard,
        )

        temp_html_path = output_pdf_path.resolve().with_suffix(".html")
        temp_html_path.write_text(full_html, encoding="utf-8")

        # 4. Render to PDF via Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(temp_html_path.as_uri(), wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            margin = {"top": "12mm", "bottom": "12mm", "left": "14mm", "right": "14mm"}
            if is_battlecard:
                margin = {"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}

            page.pdf(
                path=str(output_pdf_path),
                format="A4",
                print_background=True,
                margin=margin,
            )
            browser.close()

        # Clean up temporary HTML
        if temp_html_path.exists():
            temp_html_path.unlink()

        return output_pdf_path

    def _apply_callout_containers(self, html: str) -> str:
        """Transforms markdown blockquotes into styled executive callout cards based on uppercase prefix."""
        def replace_blockquote(match):
            bq_content = match.group(1)
            if "МЕТАФОРА" in bq_content or "ВЕКТОР А" in bq_content or "Переводчик" in bq_content or "💡" in bq_content:
                return f'<div class="callout callout-metaphor">{bq_content}</div>'
            elif "КЕЙС" in bq_content or "Криминалистика" in bq_content or "Живой кейс" in bq_content or "💥" in bq_content:
                return f'<div class="callout callout-case">{bq_content}</div>'
            elif "UNIT-ЭКОНОМИКА" in bq_content or "ВЕКТОР Б" in bq_content or "Числовой расчет" in bq_content or "Пошаговый долларовый разбор" in bq_content or "📊" in bq_content:
                return f'<div class="callout callout-calc">{bq_content}</div>'
            elif "ТЕХНИЧЕСКИЙ ПРУФ" in bq_content or "Под капотом" in bq_content or "Железный пруф" in bq_content or "🔬" in bq_content:
                return f'<div class="callout callout-proof">{bq_content}</div>'
            elif "СКРИПТ ЗАКРЫТИЯ" in bq_content or "Скрипт" in bq_content or "Ответ" in bq_content or "🎯" in bq_content:
                return f'<div class="callout callout-sales">{bq_content}</div>'
            elif "ВНИМАНИЕ" in bq_content or "Внимание" in bq_content or "Стоп" in bq_content or "⚠️" in bq_content or "Главное правило" in bq_content:
                return f'<div class="callout callout-warning">{bq_content}</div>'
            return f'<blockquote>{bq_content}</blockquote>'

        html = re.sub(r'<blockquote>(.*?)</blockquote>', replace_blockquote, html, flags=re.DOTALL)
        return html

    def _build_html_template(
        self, body_html: str, title: str, subtitle: str, is_battlecard: bool = False
    ) -> str:
        css = """
        @page {
            size: A4 portrait;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 9.6pt;
            line-height: 1.48;
            color: #1a1a24;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }
        h1 {
            color: #0b192c;
            font-size: 20pt;
            border-bottom: 2px solid #0056b3;
            padding-bottom: 6px;
            margin-top: 24px;
            margin-bottom: 14px;
            page-break-after: avoid;
        }
        h2 {
            color: #1e3e62;
            font-size: 14pt;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
            margin-top: 20px;
            margin-bottom: 10px;
            page-break-after: avoid;
        }
        h3 {
            color: #2b3a4a;
            font-size: 12pt;
            margin-top: 14px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }
        p {
            margin-top: 0;
            margin-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0;
            font-size: 9.5pt;
            page-break-inside: avoid;
        }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 7px 10px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background-color: #f1f5f9;
            color: #0f172a;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f8fafc;
        }
        code {
            background: #f1f5f9;
            color: #b91c1c;
            padding: 2px 5px;
            border-radius: 4px;
            font-size: 9pt;
            font-family: Consolas, "Courier New", monospace;
        }
        pre {
            background-color: #0f172a !important;
            color: #f8fafc !important;
            padding: 14px 18px;
            border-radius: 8px;
            overflow-x: auto;
            page-break-inside: avoid;
            margin: 12px 0;
        }
        pre code {
            background-color: transparent !important;
            color: #f8fafc !important;
            padding: 0 !important;
            border: none !important;
            font-size: 0.88em !important;
            line-height: 1.45 !important;
            font-family: Consolas, "Courier New", monospace;
        }
        /* Callouts */
        .callout {
            border-left: 4px solid #0056b3;
            background: #f8fafc;
            padding: 10px 14px;
            margin: 12px 0;
            border-radius: 0 6px 6px 0;
            page-break-inside: avoid;
        }
        .callout-metaphor {
            border-left-color: #f59e0b;
            background: #fffbeb;
        }
        .callout-case {
            border-left-color: #ef4444;
            background: #fef2f2;
        }
        .callout-calc {
            border-left-color: #10b981;
            background: #f0fdf4;
        }
        .callout-proof {
            border-left-color: #8b5cf6;
            background: #f5f3ff;
        }
        .callout-sales {
            border-left-color: #0056b3;
            background: #eff6ff;
        }
        .callout-warning {
            border-left-color: #dc2626;
            background: #fff1f2;
        }
        /* Header and Tags */
        .doc-header {
            margin-bottom: 24px;
            border-bottom: 2px solid #0056b3;
            padding-bottom: 12px;
        }
        .doc-tag {
            font-size: 8pt;
            font-weight: 700;
            color: #0056b3;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 4px;
        }
        .doc-title {
            font-size: 18pt;
            font-weight: 800;
            color: #0b192c;
            line-height: 1.2;
        }
        .doc-subtitle {
            font-size: 10.5pt;
            color: #64748b;
            margin-top: 4px;
        }
        /* Lists */
        ul, ol {
            margin-top: 4px;
            margin-bottom: 12px;
            padding-left: 24px;
        }
        li {
            margin-bottom: 4px;
        }
        """

        if is_battlecard:
            css += """
            body {
                font-size: 8.5pt;
                line-height: 1.35;
            }
            h1 { font-size: 14pt; margin-top: 10px; margin-bottom: 6px; }
            h2 { font-size: 11pt; margin-top: 8px; margin-bottom: 4px; }
            h3 { font-size: 9.5pt; margin-top: 6px; margin-bottom: 2px; }
            table { font-size: 8pt; margin: 6px 0; }
            th, td { padding: 4px 6px; }
            .callout { padding: 6px 8px; margin: 6px 0; font-size: 8pt; }
            p { margin-bottom: 6px; }
            pre { padding: 8px 10px; font-size: 7.5pt; }
            """

        header_html = ""
        if is_battlecard:
            header_html = f"""
    <div class="doc-header">
        <div class="doc-tag">Institutional Research & Sales Academy</div>
        <div class="doc-title">{title}</div>
        <div class="doc-subtitle">{subtitle}</div>
    </div>
"""

        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script>
    function renderPandocKatex() {{
        if (typeof katex !== 'undefined') {{
            document.querySelectorAll('.math.inline').forEach(function(el) {{
                katex.render(el.textContent, el, {{displayMode: false, throwOnError: false}});
            }});
            document.querySelectorAll('.math.display').forEach(function(el) {{
                katex.render(el.textContent, el, {{displayMode: true, throwOnError: false}});
            }});
        }} else {{
            setTimeout(renderPandocKatex, 50);
        }}
    }}
    window.addEventListener('DOMContentLoaded', renderPandocKatex);
    </script>
    <style>{css}</style>
</head>
<body>
    {header_html}
    {body_html}
</body>
</html>
"""
