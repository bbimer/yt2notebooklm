"""Publishing and export pipeline module (Markdown, CSV, NotebookLM bundle)."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_academy.database import Database
from research_academy.models import (
    DiscoveryStatus,
    MethodistAnalysis,
    SourceContent,
    VideoMetadata,
    VideoTranscript,
)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", text).strip("-_")[:50]


class Publisher:
    def __init__(self, db: Database, output_dir: Path):
        self.db = db
        self.output_dir = output_dir
        self.sources_dir = output_dir / "knowledge_base" / "sources"
        self.exports_dir = output_dir / "exports"
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, filename: Optional[str] = None) -> Path:
        filepath = self.exports_dir / (filename or "index.csv")
        videos = self.db.list_videos(limit=1000)

        fieldnames = [
            "video_id",
            "title",
            "topic_id",
            "channel_title",
            "duration_seconds",
            "view_count",
            "like_count",
            "like_ratio",
            "views_to_subscribers_ratio",
            "discovery_status",
            "status_reason",
            "queries_matched",
            "url",
            "created_at",
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for v in videos:
                writer.writerow({
                    "video_id": v.video_id,
                    "title": v.title,
                    "topic_id": v.topic_id,
                    "channel_title": v.channel_title,
                    "duration_seconds": v.duration_seconds,
                    "view_count": v.view_count or "",
                    "like_count": v.like_count or "",
                    "like_ratio": v.like_ratio or "",
                    "views_to_subscribers_ratio": v.views_to_subscribers_ratio or "",
                    "discovery_status": v.discovery_status.value,
                    "status_reason": v.status_reason or "",
                    "queries_matched": "; ".join(v.queries_matched),
                    "url": v.url,
                    "created_at": v.created_at.isoformat(),
                })

        return filepath

    def render_markdown_summary(
        self,
        video: Optional[VideoMetadata] = None,
        analysis: Optional[MethodistAnalysis] = None,
        transcript: Optional[VideoTranscript] = None,
        gatekeeper_score: Optional[float] = None,
        source: Optional[SourceContent] = None,
    ) -> str:
        """
        Renders a structured, verified Markdown document compliant with Section 11 of the specification.
        Isomorphic for both video and web sources.
        """
        if source is None:
            if video is None:
                raise ValueError("Either video or source must be provided")
            source = SourceContent.from_video(
                video,
                transcript or VideoTranscript(video_id=video.video_id, language="ru", full_raw_text="", full_normalized_text=""),
                domain=getattr(video, "domain", "crypto"),
            )
        if analysis is None:
            raise ValueError("analysis must be provided")

        terms_md = ""
        for item in analysis.terminology_and_slang:
            term = item.get("term", "")
            definition = item.get("definition_or_context", "")
            terms_md += f"- **{term}**: {definition}\n"

        concepts_md = "\n".join(f"- {c}" for c in analysis.key_concepts)
        examples_md = "\n".join(f"- {ex}" for ex in analysis.numerical_examples)
        mistakes_md = "\n".join(f"- {m}" for m in analysis.common_mistakes_and_myths)
        risks_md = "\n".join(f"- {r}" for r in analysis.risks_and_limitations)
        self_check_md = "\n".join(f"1. {q}" for q in analysis.self_check_questions)

        qa_md = ""
        for i, qa in enumerate(analysis.client_questions_and_answers, start=1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            qa_md += f"### Вопрос {i}: {q}\n**Ответ:** {a}\n\n"

        claims_md = ""
        for c in analysis.key_claims:
            status = c.verification_status
            if status == "market_fact":
                status_label = "РЫНОЧНЫЙ ФАКТ"
            elif status == "author_hypothesis":
                status_label = "ГИПОТЕЗА / СОВЕТ АВТОРА"
            else:
                status_label = status.upper()

            anchor_display = c.anchor_id or c.timestamp_formatted or "N/A"
            if str(anchor_display).startswith("SEC-"):
                ref_link = f"Раздел: {anchor_display}"
            elif c.timestamp_seconds is not None:
                ref_link = f"{source.url}&t={int(c.timestamp_seconds)}s ({anchor_display})"
            else:
                ref_link = f"{anchor_display}"

            claims_md += (
                f"- **[{status_label}]** {c.statement}\n"
                f"  - Ссылка/Якорь: {ref_link}\n"
                f"  - Цитата автора: *«{c.quote_text or c.statement}»*\n"
            )
            if c.allowed_sales_phrasing:
                claims_md += f"  - Формулировка для менеджера: *«{c.allowed_sales_phrasing}»*\n"

        anchors_md = ""
        if source.source_type == "web":
            for s in source.segments[:15]:
                anchors_md += f"- **{s.anchor_id}**: {s.text[:90].strip()}...\n"
        elif transcript and transcript.segments:
            step = max(1, len(transcript.segments) // 10)
            for seg in transcript.segments[::step][:12]:
                anchors_md += f"- [{seg.timestamp_formatted}]({source.url}&t={int(seg.start_seconds)}s) — {seg.text[:80]}...\n"

        md_content = f"""# {source.title}

- **URL:** {source.url}
- **Канал / Автор:** {source.author_or_domain}
- **Домен:** {source.domain}
- **Тематический модуль:** {source.topic_id}
- **Рейтинг Gatekeeper:** {gatekeeper_score or 'N/A'}/10
- **Статус проверки:** Проверено (Methodist Verified)

---

## 🏛 СЛОЙ 1: ФУНДАМЕНТАЛЬНАЯ РЫНОЧНАЯ БАЗА (MARKET REALITY)

### Краткое содержание
{analysis.summary}

### Ключевые концепции
{concepts_md or 'Не выделены.'}

### Объяснение механизмов
{analysis.mechanisms_explanation}

### Терминология и сленг практиков
{terms_md or 'Не выделены.'}

### Числовые примеры и расчеты
{examples_md or 'Нет числовых примеров.'}

---

## 🔍 СЛОЙ 2: АУДИТ ИСТОЧНИКА И ЦИТАТЫ (SOURCE EVIDENCE)

### Проверяемые утверждения и цитаты
{claims_md or 'Нет утверждений.'}

### Риски, ограничения и технические упрощения автора
{risks_md or 'Не зафиксированы.'}

### Кликабельные таймкоды ключевых моментов
{anchors_md or 'Таймкоды отсутствуют.'}

---

## 🎯 СЛОЙ 3: СОЦИАЛЬНАЯ ИНЖЕНЕРИЯ, ПСИХОЛОГИЯ КЛИЕНТА И ЗАКРЫТИЕ (SALES PSYCHOLOGY)

### Типичные ошибки и заблуждения розничных трейдеров
{mistakes_md or 'Не зафиксированы.'}

### Вопросы клиентов и ответы (перехват авторитета и социальная инженерия)
{qa_md or 'Нет вопросов.'}

### Вопросы для самопроверки менеджера
{self_check_md or 'Нет вопросов.'}

---

## ⚙️ СЛОЙ 4: ПРИКЛАДНОЙ СЛОЙ (Связь с NULLSPREAD & Product Application)
{analysis.nullspread_connection or 'Продуктовая связь не установлена (общетехнический фундамент).'}
"""
        return md_content

    def publish_source_analysis(
        self,
        source: SourceContent,
        analysis: MethodistAnalysis,
        gatekeeper_score: Optional[float] = None,
    ) -> Path:
        slug = slugify(source.title)
        filename = f"{source.source_id}_{slug}.md"
        if source.domain == "crypto":
            module_dir = self.sources_dir / (source.topic_id or "general")
        else:
            module_dir = (
                self.output_dir
                / "knowledge_base"
                / "domains"
                / source.domain
                / "sources"
                / (source.topic_id or "general")
            )
        module_dir.mkdir(parents=True, exist_ok=True)
        filepath = module_dir / filename

        content = self.render_markdown_summary(
            analysis=analysis,
            gatekeeper_score=gatekeeper_score,
            source=source,
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def publish_video_analysis(
        self,
        video: VideoMetadata,
        analysis: MethodistAnalysis,
        transcript: Optional[VideoTranscript] = None,
        gatekeeper_score: Optional[float] = None,
    ) -> Path:
        source = SourceContent.from_video(
            video,
            transcript or VideoTranscript(video_id=video.video_id, language="ru", full_raw_text="", full_normalized_text=""),
            domain=getattr(video, "domain", "crypto"),
        )
        return self.publish_source_analysis(source, analysis, gatekeeper_score)

    def build_notebooklm_bundle(self) -> Path:
        """
        Combines product claims and all verified markdown sources into a curated bundle
        ready for upload into Google NotebookLM.
        """
        bundle_path = self.exports_dir / "notebooklm_knowledge_bundle.md"
        product_claims_path = self.output_dir / "knowledge_base" / "product" / "PRODUCT_CLAIMS.md"
        sales_objections_path = self.output_dir / "knowledge_base" / "product" / "SALES_OBJECTIONS.md"

        with open(bundle_path, "w", encoding="utf-8") as out:
            out.write("# NULLSPREAD UNIFIED KNOWLEDGE BASE (NOTEBOOKLM BUNDLE)\n\n")
            if product_claims_path.exists():
                out.write(product_claims_path.read_text(encoding="utf-8"))
                out.write("\n\n---\n\n")
            if sales_objections_path.exists():
                out.write(sales_objections_path.read_text(encoding="utf-8"))
                out.write("\n\n---\n\n")

            # Recursively collect all markdown sources across all module folders
            for src in sorted(self.sources_dir.rglob("*.md")):
                out.write(f"\n\n<!-- SOURCE: {src.parent.name}/{src.name} -->\n\n")
                out.write(src.read_text(encoding="utf-8"))
                out.write("\n\n---\n\n")

        return bundle_path

    def export_notebooklm_pack(self, domain: str = "crypto") -> Path:
        """
        Exports discrete package optimized for NotebookLM multi-source checkboxes.
        Supports 'crypto' (default 9-file pack) and custom domains (Topic_*.md files).
        """
        if domain != "crypto":
            from research_academy.domain.manager import DomainManager

            manager = DomainManager(self.output_dir)
            profile = manager.get_domain(domain)
            domain_pack_dir = self.exports_dir / "notebooklm_pack" / domain
            domain_pack_dir.mkdir(parents=True, exist_ok=True)

            # 1. 00_DOMAIN_FOUNDATIONS.md
            if profile.claims_text:
                (domain_pack_dir / "00_DOMAIN_FOUNDATIONS.md").write_text(
                    f"# {profile.name} — Фундаментальный базис\n\n{profile.claims_text}",
                    encoding="utf-8",
                )

            # 2. Topic modules
            domain_sources_dir = self.output_dir / "knowledge_base" / "domains" / domain / "sources"
            for topic in profile.topics:
                filename = f"Topic_{topic.id}.md"
                topic_dir = domain_sources_dir / topic.id
                verified_files = sorted(topic_dir.glob("*.md")) if topic_dir.exists() else []

                content = [
                    f"# {topic.title}\n",
                    f"**Описание:** {topic.description}\n",
                    f"**Ключевые концепции:** {', '.join(topic.key_terms)}\n",
                    "---\n",
                ]

                if verified_files:
                    content.append(f"## Проверенные первоисточники ({len(verified_files)} документов/статей)\n")
                    for vf in verified_files:
                        content.append(f"### Источник: {vf.stem}\n")
                        content.append(vf.read_text(encoding="utf-8"))
                        content.append("\n\n---\n")
                else:
                    content.append("## Статус сбора материала\n")
                    content.append("*Материалы для данной темы находятся в очереди сбора и верификации.*\n")

                (domain_pack_dir / filename).write_text("\n".join(content), encoding="utf-8")

            # 3. Domain NotebookLM Guide
            guide_text = f"""# Руководство по работе с Google NotebookLM — {profile.name}

## 1. Загрузка в NotebookLM
Загрузите все сгенерированные файлы из папки `{domain_pack_dir.name}` в новый блокнот NotebookLM.

## 2. Генерация Audio Overview (Подкаста)
В левой панели NotebookLM отметьте галочками изучаемую тему и нажмите «Customize»:
> «Обсуждайте материал на русском языке в формате академического диалога двух ведущих экспертов. Делайте акцент на глубине, доказательствах и практических кейсах по теме {profile.name}. Без поверхностных упрощений и клише».
"""
            (domain_pack_dir / "README_NOTEBOOKLM_GUIDE.md").write_text(guide_text, encoding="utf-8")
            return domain_pack_dir

        from research_academy.queries_config import SEARCH_MATRIX

        pack_dir = self.exports_dir / "notebooklm_pack"
        pack_dir.mkdir(parents=True, exist_ok=True)

        product_claims_path = self.output_dir / "knowledge_base" / "product" / "PRODUCT_CLAIMS.md"
        sales_objections_path = self.output_dir / "knowledge_base" / "product" / "SALES_OBJECTIONS.md"

        # 1. 00_PRODUCT_CLAIMS_AND_LANDING.md
        if product_claims_path.exists():
            (pack_dir / "00_PRODUCT_CLAIMS_AND_LANDING.md").write_text(
                product_claims_path.read_text(encoding="utf-8"), encoding="utf-8"
            )

        # 2. 00_SALES_OBJECTIONS.md
        if sales_objections_path.exists():
            (pack_dir / "00_SALES_OBJECTIONS.md").write_text(
                sales_objections_path.read_text(encoding="utf-8"), encoding="utf-8"
            )

        # 3. 7 Days Modules (1 Module = 1 NotebookLM Source)
        day_mapping = [
            ("00_crypto_fundamentals", "Day_1_00_Fundamentals.md", "День 1. Модуль 0: Фундамент крипты, блокчейн и токеномика"),
            ("01_market_structure", "Day_2_01_Market_Structure.md", "День 2. Модуль 1: Архитектура рынка, биржи и маркет-мейкеры"),
            ("02_arbitrage_and_derivatives", "Day_3_02_Arbitrage_and_Derivatives.md", "День 3. Модуль 2: Деривативы, фьючерсы и виды криптоарбитража"),
            ("03_orderbook_mechanics", "Day_4_03_Orderbook_and_Execution.md", "День 4. Модуль 3: Биржевой стакан, сведение ордеров и HFT"),
            ("04_onchain_logistics", "Day_5_04_DEX_and_Onchain.md", "День 5. Модуль 4: DEX, пулы ликвидности и ончейн-клиринг"),
            ("05_risk_and_hedging", "Day_6_05_Risks_and_Security.md", "День 6. Модуль 5: Реальные риски, ликвидации и безопасность"),
            ("06_quant_stack_and_mindset", "Day_7_06_Quant_Stack.md", "День 7. Модуль 6: Квант-стек, психология рынка и скрипты продаж"),
        ]

        for topic_id, filename, default_title in day_mapping:
            topic_info = SEARCH_MATRIX.get(topic_id, {})
            title = topic_info.get("title", default_title)
            topic_sources_dir = self.sources_dir / topic_id
            verified_files = sorted(topic_sources_dir.glob("*.md")) if topic_sources_dir.exists() else []

            content = [
                f"# {title}\n",
                f"**Ключевые термины модуля:** {', '.join(topic_info.get('key_terms', []))}\n",
                "---\n",
            ]

            if verified_files:
                content.append(f"## Проверенные материалы дня ({len(verified_files)} видео-исследований)\n")
                for vf in verified_files:
                    content.append(f"### Источник: {vf.stem}\n")
                    content.append(vf.read_text(encoding="utf-8"))
                    content.append("\n\n---\n")
            else:
                content.append("## Статус сбора материала\n")
                content.append("*Материалы для данного дня находятся в очереди сбора и верификации.*\n")
                content.append("\n### Целевые поисковые запросы модуля:")
                content.append("\n**Русскоязычные запросы:**")
                for q in topic_info.get("queries_ru", []):
                    content.append(f"- `{q}`")
                content.append("\n**Англоязычные запросы:**")
                for q in topic_info.get("queries_en", []):
                    content.append(f"- `{q}`")
                content.append("\n")

            (pack_dir / filename).write_text("\n".join(content), encoding="utf-8")

        # 4. README_NOTEBOOKLM_GUIDE.md
        guide_text = """# Руководство по работе с Google NotebookLM (NULLSPREAD Research Academy)

## 1. Структура источников (9 файлов)
В этой папке сгенерировано 9 отдельных источников для загрузки в один блокнот NotebookLM:
1. `00_PRODUCT_CLAIMS_AND_LANDING.md` — Фундамент и официальные продуктовые рамки платформы NULLSPREAD.
2. `00_SALES_OBJECTIONS.md` — Матрица клиентских возражений и контраргументов.
3. `Day_1_00_Fundamentals.md` ... `Day_7_06_Quant_Stack.md` — 7 модулей по дням курса.

## 2. Как генерировать сфокусированные подкасты (Audio Overview)
В левой панели NotebookLM отметьте галочками:
- `[x] 00_PRODUCT_CLAIMS_AND_LANDING.md`
- `[x] Day_X_...` (только изучаемый модуль текущего дня!)

Нажмите кнопку **«Customize» (Настроить)** перед генерацией Audio Overview и вставьте следующий проверенный промпт:

> «Обсуждайте материал на русском языке. Вы — два опытных крипто-практика. Сделайте жесткий фокус на том, как применять эти механики при общении со скептично настроенным инвестором с крупным капиталом. Разберите мифы розничных трейдеров и покажите, как аргументировать позицию через аналитику деска NULLSPREAD (глубина стакана, фрикции фиата, задержка ончейн-клиринга). Без воды и детских метафор».

## 3. Дневной воркфлоу менеджера
1. **Утро (Автоматика):** Скрипт `research_academy` собирает аналитику дня и обновляет файлы в `notebooklm_pack/`.
2. **День (Погружение):**
   - Слушаем 15-минутный кастомный подкаст от NotebookLM по модулю дня (задает контекст).
   - Вычитываем синтезированный конспект от DeepSeek (особенно Bilingual Glossary и Sales Translation Bridge).
   - Открываем 2-3 ключевых видео по таймкодам вида `[MM:SS]` для визуального просмотра стаканов и графиков.
3. **Вечер (Спарринг в чате NotebookLM):**
   - Пишем в чат NotebookLM: *«Задай мне 5 самых каверзных вопросов от лица взрослого криптоинвестора строго по сегодняшнему модулю, по одному за раз, и оценивай мои ответы по базе знаний»*.
"""
        (pack_dir / "README_NOTEBOOKLM_GUIDE.md").write_text(guide_text, encoding="utf-8")
        return pack_dir

