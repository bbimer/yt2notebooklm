"""Unit tests for Stage 2: WebArticleExtractor, URL Canonicalization, and Structural Outline Sampling."""

import pytest
from bs4 import BeautifulSoup

from research_academy.models import ContentSegment, DiscoveryStatus, SourceContent
from research_academy.pipeline.sampling import (
    sample_source_content,
    sample_web_document_structural,
)
from research_academy.providers.web_extractor import WebArticleExtractor
from research_academy.providers.web_provider import (
    canonicalize_url,
    generate_document_id,
)


def test_canonicalize_url_and_cyrillic():
    # 1. Percent-encoded Cyrillic vs unquoted Cyrillic
    url_percent = "https://ru.wikipedia.org/wiki/%D0%94%D0%B2%D0%BE%D0%B8%D1%87%D0%BD%D0%B0%D1%8F_%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0_%D1%81%D1%87%D0%B8%D1%81%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F"
    url_cyrillic = "https://ru.wikipedia.org/wiki/Двоичная_система_счисления"
    assert canonicalize_url(url_percent) == canonicalize_url(url_cyrillic)
    assert generate_document_id(url_percent) == generate_document_id(url_cyrillic)

    # 2. Strips UTM, tracking, anchors, and trailing slash
    url_dirty = "https://example.com/docs/binary/?utm_source=twitter&ref=reddit&fbclid=xyz#section-2"
    url_clean = canonicalize_url(url_dirty)
    assert url_clean == "https://example.com/docs/binary"
    assert "utm_source" not in url_clean
    assert "#section-2" not in url_clean


def test_web_article_extractor_table_code_and_indices():
    extractor = WebArticleExtractor(min_words=20)  # low threshold for testing snippet

    html = """
    <html>
    <head><title>Двоичная система счисления - Википедия</title></head>
    <body>
    <article>
        <h1>Двоичная система счисления</h1>
        <p>Двоичная система счисления — это позиционная система счисления с основанием 2. Число 1011<sub>2</sub> в десятичной системе равно 11<sub>10</sub>, а диапазон 16 бит составляет 2<sup>16</sup> = 65536 различных значений. <sup class="reference"><a href="#cite">[1]</a></sup> <span class="mw-editsection">[править | править код]</span></p>

        <span class="mwe-math-element">
            <img class="mwe-math-fallback-image-inline" alt="N = \\sum_{i=0}^{n} d_i \\cdot 2^i" src="math.png" />
        </span>

        <h2>Сравнительная таблица систем</h2>
        <table>
            <tr><th>Основание</th><th>Название</th><th>Символы</th></tr>
            <tr><td>2</td><td>Двоичная</td><td>0, 1</td></tr>
            <tr><td>16</td><td>Шестнадцатеричная</td><td>0-9, A-F</td></tr>
        </table>

        <h2>Пример кода на Python</h2>
        <pre><code class="language-python">def to_binary(n: int) -> str:
    return bin(n)[2:]</code></pre>

        <h2>Заключение</h2>
        <p>Таким образом, двоичная арифметика лежит в основе всех современных процессорных архитектур и АЛУ.</p>
    </article>
    </body>
    </html>
    """

    res = extractor.extract_from_html(html, "https://ru.wikipedia.org/wiki/binary")
    assert res.status == DiscoveryStatus.EXTRACTED
    assert res.title == "Двоичная система счисления"
    assert res.has_high_density_data is True

    # 1. Check math and sub/sup indices
    assert "1011_{2}" in res.clean_markdown
    assert "2^{16}" in res.clean_markdown
    assert "$N = \\sum_{i=0}^{n} d_i \\cdot 2^i$" in res.clean_markdown

    # 2. Check footnotes removal
    assert "[1]" not in res.clean_markdown
    assert "[править" not in res.clean_markdown

    # 3. Check table parsing
    assert "| Основание | Название | Символы |" in res.clean_markdown
    assert "| 2 | Двоичная | 0, 1 |" in res.clean_markdown
    assert "| --- |" in res.clean_markdown

    # 4. Check code block
    assert "```" in res.clean_markdown
    assert "def to_binary" in res.clean_markdown

    # 5. Check structural segments
    assert len(res.segments) >= 3
    assert res.segments[0].anchor_id.startswith("SEC-01")
    assert any("Сравнительная таблица" in s.anchor_id and s.has_table for s in res.segments)
    assert any("Пример кода" in s.anchor_id and s.has_code for s in res.segments)


def test_web_article_extractor_quality_gate_antibot_and_spa():
    extractor = WebArticleExtractor(min_words=250)

    # 1. Anti-bot Cloudflare challenge
    cf_html = """
    <html>
    <head><title>Attention Required! | Cloudflare</title></head>
    <body>
        <h1>Just a moment...</h1>
        <p>Please enable JavaScript and cookies to continue. Cloudflare Ray ID: 87654321</p>
    </body>
    </html>
    """
    res_cf = extractor.extract_from_html(cf_html, "https://protected-site.com")
    assert res_cf.status == DiscoveryStatus.REJECTED_EXTRACTION
    assert "Cloudflare" in res_cf.status_reason or "anti-bot" in res_cf.status_reason
    assert res_cf.word_count == 0

    # 2. Empty React/Vue SPA stub
    spa_html = """
    <html>
    <head><title>My Modern Web App</title></head>
    <body>
        <div id="root">Loading application... Please wait.</div>
    </body>
    </html>
    """
    res_spa = extractor.extract_from_html(spa_html, "https://spa-app.com")
    assert res_spa.status == DiscoveryStatus.REJECTED_EXTRACTION
    assert "word_count" in res_spa.status_reason


def test_structural_outline_sampling():
    # Build document with 5 sections
    segments = [
        ContentSegment(index=1, anchor_id="SEC-01 | Введение", title="Введение", text="Позиционные системы счисления начало...", word_count=50),
        ContentSegment(index=2, anchor_id="SEC-02 | История", title="История", text="Лейбниц и двоичная система счисления...", word_count=40),
        ContentSegment(index=3, anchor_id="SEC-03 | Таблица степеней", title="Таблица степеней", text="| Степень | Значение |\n| 2^8 | 256 |", has_table=True, word_count=80),
        ContentSegment(index=4, anchor_id="SEC-04 | Код на Си", title="Код на Си", text="```c\nint x = 1 << 4;\n```", has_code=True, word_count=60),
        ContentSegment(index=5, anchor_id="SEC-05 | Заключение", title="Заключение", text="Резюме и практические выводы работы.", word_count=30),
    ]

    source = SourceContent(
        source_id="web_test_sampling",
        source_type="web",
        domain="computer_science",
        topic_id="01_binary_numeral_system",
        title="Двоичные вычисления",
        url="https://example.com/binary",
        segments=segments,
        full_clean_text="...",
        word_count=5000,  # Simulated long document exceeding budget
    )

    sample = sample_web_document_structural(source, max_words=200)

    # 1. Must contain outline
    assert "### [ОГЛАВЛЕНИЕ ДОКУМЕНТА]" in sample
    assert "SEC-01 | Введение" in sample
    assert "SEC-05 | Заключение" in sample

    # 2. Must contain lead (SEC-01)
    assert "### [ЛИД / АБСТРАКТ: SEC-01 | Введение]" in sample
    assert "Позиционные системы счисления начало" in sample

    # 3. Must contain density core (table and code segments)
    assert "### [ЯДРО ПЛОТНОСТИ ФАКТУРЫ: SEC-03 | Таблица степеней]" in sample
    assert "### [ЯДРО ПЛОТНОСТИ ФАКТУРЫ: SEC-04 | Код на Си]" in sample

    # 4. Must contain conclusions (SEC-05)
    assert "### [ВЫВОДЫ И ЗАКЛЮЧЕНИЕ: SEC-05 | Заключение]" in sample
    assert "Резюме и практические выводы" in sample

