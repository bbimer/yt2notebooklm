"""CLI interface for NULLSPREAD Research & Sales Academy."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from research_academy.academy.evaluation import AnswerEvaluator
from research_academy.academy.question_generator import QuestionGenerator
from research_academy.academy.roleplay import InvestorPersona, RoleplaySession
from research_academy.config import get_config
from research_academy.database import Database
from research_academy.domain.manager import DomainManager
from research_academy.models import DiscoveryStatus
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.pipeline.discovery import DiscoveryEngine
from research_academy.pipeline.publishing import Publisher
from research_academy.pipeline.transcription import TranscriptionPipeline
from research_academy.pipeline.web_harvester import WebHarvester
from research_academy.scheduler import ContinuousResearchCoordinator

console = Console()


@click.group()
def cli() -> None:
    """NULLSPREAD Research & Sales Academy CLI."""
    pass


@cli.command("doctor")
def doctor_cmd() -> None:
    """Inspect environment, API keys, database, and dependencies without leaking secrets."""
    config = get_config()
    db = Database(config.database_path)

    table = Table(title="System Diagnostic (Doctor)", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="dim", width=25)
    table.add_column("Status / Value", style="bold")
    table.add_column("Details")

    # Python Version
    table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "OK")

    # SQLite
    try:
        with db.get_connection() as conn:
            cur = conn.execute("SELECT count(*) FROM videos")
            count = cur.fetchone()[0]
        table.add_row("Database (SQLite)", "CONNECTED", f"{config.database_path} ({count} videos)")
    except Exception as e:
        table.add_row("Database (SQLite)", "[red]ERROR[/red]", str(e))

    # YouTube API
    yt_status = "[green]CONFIGURED[/green]" if config.youtube_api_key else "[yellow]MOCK / MISSING[/yellow]"
    table.add_row("YouTube API Key", yt_status, config.mask_secret(config.youtube_api_key))

    # LLM Providers
    or_status = "[green]CONFIGURED (Active)[/green]" if config.openrouter_api_key else "[yellow]NOT CONFIGURED[/yellow]"
    table.add_row("OpenRouter API Key", or_status, f"{config.mask_secret(config.openrouter_api_key)} (Model: {config.openrouter_model})")

    gemini_status = "[green]CONFIGURED[/green]" if config.gemini_api_key else "[yellow]NOT CONFIGURED[/yellow]"
    table.add_row("Gemini API Key", gemini_status, f"{config.mask_secret(config.gemini_api_key)} (Model: {config.gemini_model})")

    table.add_row("Active LLM Provider", f"[bold cyan]{config.llm_provider}[/bold cyan]", "Auto-resolves to openrouter if key present")

    # YouTube Provider Selection
    table.add_row("YouTube Provider", config.youtube_provider, "youtube_api or yt_dlp")

    # Trusted Channels
    table.add_row("Trusted Channels", f"{len(config.trusted_channels)} channels", "Loaded from config/trusted_channels.yaml")

    console.print(table)


@cli.command("status")
def status_cmd() -> None:
    """Show database summary, video and web processing stages, and knowledge base stats."""
    config = get_config()
    db = Database(config.database_path)
    manager = DomainManager(config.project_root)

    videos = db.list_videos(limit=1000)
    docs = db.list_documents(limit=1000)
    status_counts = {}
    for v in videos:
        status_counts[v.discovery_status.value] = status_counts.get(v.discovery_status.value, 0) + 1
    for d in docs:
        key = f"Doc: {d.discovery_status.value}"
        status_counts[key] = status_counts.get(key, 0) + 1

    table = Table(title="Research Academy Status", show_header=True, header_style="bold magenta")
    table.add_column("Metric / Status", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Total Videos in DB", str(len(videos)))
    table.add_row("Total Web Documents in DB", str(len(docs)))
    table.add_row("Active Domains", ", ".join(manager.list_domains()))
    for status, count in status_counts.items():
        table.add_row(f"Status: {status}", str(count))

    # Knowledge base markdown files
    sources_dir = config.project_root / "knowledge_base" / "sources"
    md_sources = list(sources_dir.rglob("*.md")) if sources_dir.exists() else []
    domain_sources_dir = config.project_root / "knowledge_base" / "domains"
    if domain_sources_dir.exists():
        md_sources += list(domain_sources_dir.rglob("*.md"))
    table.add_row("Published Verified Sources", str(len(md_sources)))

    console.print(table)


@cli.command("search")
@click.option("--topic", required=True, help="Topic identifier (e.g. funding-rate-arbitrage, market-microstructure)")
@click.option("--max-queries", default=2, help="Max queries to execute to conserve API quota")
def search_cmd(topic: str, max_queries: int) -> None:
    """Discover candidate videos on YouTube for a specific topic."""
    config = get_config()
    db = Database(config.database_path)
    engine = DiscoveryEngine(config, db)

    console.print(f"[bold green]Starting discovery for topic:[/bold green] [cyan]{topic}[/cyan]")
    try:
        results = engine.discover_by_topic(topic_id=topic, max_queries=max_queries)
        console.print("[bold green]Discovery completed successfully![/bold green]")
        console.print(f"- Queries executed: [yellow]{results['queries_executed']}[/yellow]")
        console.print(f"- Total candidates found: [yellow]{results['total_found']}[/yellow]")
        console.print(f"- New unique videos: [yellow]{results['new_unique']}[/yellow]")
        console.print(f"- Queued for transcript: [green]{results['queued_for_transcript']}[/green]")
        console.print(f"- Filtered out (pre-filter): [red]{results['filtered_out']}[/red]")
    except Exception as e:
        console.print(f"[bold red]Discovery failed:[/bold red] {e}")
        sys.exit(1)


@cli.command("process")
@click.argument("target", required=False)
@click.option("--video-id", help="YouTube video ID or URL to process")
@click.option("--module", default="02_arbitrage_types", help="Target module (01_market_structure, 02_arbitrage_types, etc.)")
@click.option("--force", is_flag=True, help="Force Methodist pass even if Gatekeeper flagged review/borderline")
def process_cmd(target: Optional[str], video_id: Optional[str], module: str, force: bool) -> None:
    """Run transcription, Gatekeeper, and Methodist pass for a video (accepts link or ID)."""
    from research_academy.pipeline.transcript_sniffer import extract_youtube_video_id

    raw_input = target or video_id
    if not raw_input:
        console.print("[bold red]Укажите ссылку на YouTube или video-id:[/bold red] `research process https://youtu.be/... --module 01_market_structure`")
        sys.exit(1)

    vid = extract_youtube_video_id(raw_input)
    if not vid:
        console.print(f"[bold red]Не удалось распознать YouTube Video ID:[/bold red] {raw_input}")
        sys.exit(1)

    config = get_config()
    db = Database(config.database_path)
    video = db.get_video(vid)

    # If video isn't in DB yet, create metadata entry on the fly
    if not video:
        video = VideoMetadata(
            video_id=vid,
            title=f"Curated Video ({vid})",
            channel_id="manual_import",
            channel_title="YouTube Creator",
            url=f"https://www.youtube.com/watch?v={vid}",
            topic_id=module,
            discovery_status=DiscoveryStatus.QUEUED_FOR_TRANSCRIPT,
        )
        db.upsert_video(video, query_matched="manual_curation")

    console.print(f"[bold cyan]Processing video:[/bold cyan] {video.title} ({vid}) [Модуль: [yellow]{video.topic_id}[/yellow]]")

    # Step 1: Transcribe
    transcription = TranscriptionPipeline(config, db)
    transcript = transcription.process_video_transcript(video)
    if not transcript:
        console.print(f"[bold red]Transcription failed or video filtered out.[/bold red] Reason: {video.status_reason}")
        sys.exit(1)

    console.print(f"[bold green]Transcript fetched:[/bold green] {transcript.word_count} words.")

    # Step 2: Two-pass analysis (with optional force)
    analysis = AnalysisPipeline(config, db)
    gate_res, meth_res = analysis.run_two_pass_analysis(video, transcript, force_methodist=force)

    if gate_res:
        console.print(f"Gatekeeper Decision: [bold]{gate_res.decision.value}[/bold] (Score: {gate_res.relevance_score}/10)")
    if meth_res:
        console.print(f"[bold green]Methodist pass completed! Verified source published to knowledge base under:[/bold green] [cyan]knowledge_base/sources/{video.topic_id}/[/cyan]")
    else:
        console.print("[yellow]Video did not pass Gatekeeper threshold. Methodist pass skipped. (Use --force to override)[/yellow]")


@cli.command("update")
@click.option("--dry-run", is_flag=True, help="Preview update plan without running API queries or spending tokens")
def update_cmd(dry_run: bool) -> None:
    """Execute end-to-end continuous research update cycle."""
    config = get_config()
    db = Database(config.database_path)
    coordinator = ContinuousResearchCoordinator(config, db)

    if dry_run:
        plan = coordinator.run_update_cycle(dry_run=True)
        console.print(Panel.fit("[bold yellow]Continuous Research Update (DRY-RUN)[/bold yellow]"))
        console.print(f"- Planned queries per topic: {plan['planned_queries_per_topic']}")
        console.print(f"- Videos queued for transcript: {plan['queued_for_transcript']}")
        console.print(f"- Transcribed videos ready for LLM: {plan['ready_for_analysis']}")
        console.print(f"- Max estimated LLM budget: ${plan['estimated_max_cost_usd']:.2f}")
    else:
        console.print("[bold green]Starting continuous research update cycle...[/bold green]")
        stats = coordinator.run_update_cycle(dry_run=False)
        console.print("[bold green]Update cycle finished successfully:[/bold green]")
        for k, v in stats.items():
            console.print(f"- {k}: [cyan]{v}[/cyan]")


@cli.command("retry-failed")
def retry_failed_cmd() -> None:
    """Retry transcription for videos that previously failed."""
    config = get_config()
    db = Database(config.database_path)
    coordinator = ContinuousResearchCoordinator(config, db)

    console.print("[bold cyan]Retrying failed transcripts...[/bold cyan]")
    retried = coordinator.retry_failed_transcripts()
    console.print(f"[bold green]Retried {retried} failed videos.[/bold green]")


@cli.command("export")
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["pack", "bundle", "csv", "markdown"]),
    default="pack",
    help="Export format: pack (NotebookLM files), bundle (single file), csv (index), markdown (sources directory)",
)
@click.option("--domain", default="crypto", help="Domain to export (crypto, computer_science, english_learning)")
def export_cmd(export_format: str, domain: str) -> None:
    """Export collected intelligence to NotebookLM pack, bundle, CSV index, or Markdown files."""
    config = get_config()
    db = Database(config.database_path)
    publisher = Publisher(db, config.project_root)

    if export_format == "pack":
        path = publisher.export_notebooklm_pack(domain=domain)
        console.print(f"[bold green]NotebookLM pack for '{domain}' generated successfully in:[/bold green] [cyan]{path}[/cyan]")
        if domain == "crypto":
            console.print("[dim]Включает: 00_PRODUCT_CLAIMS, 00_SALES_OBJECTIONS, 7 файлов модулей по дням и README с промптом для подкаста.[/dim]")
        else:
            console.print(f"[dim]Включает: 00_DOMAIN_FOUNDATIONS, тематические модули домена '{domain}' и README с промптом для подкаста.[/dim]")
    elif export_format == "bundle":
        path = publisher.build_notebooklm_bundle()
        console.print(f"[bold green]NotebookLM single bundle generated:[/bold green] [cyan]{path}[/cyan]")
    elif export_format == "csv":
        path = publisher.export_csv()
        console.print(f"[bold green]CSV index exported successfully:[/bold green] [cyan]{path}[/cyan]")
    elif export_format == "markdown":
        console.print(f"[bold green]Markdown sources stored in:[/bold green] [cyan]{publisher.sources_dir}[/cyan]")


# --- Domain Management Group ---

@cli.group("domain")
def domain_group() -> None:
    """Manage domain profiles (crypto, computer_science, english_learning, etc.)."""
    pass


@domain_group.command("list")
def domain_list_cmd() -> None:
    """List all registered knowledge domains."""
    config = get_config()
    manager = DomainManager(config.project_root)
    domains = manager.list_domains()

    table = Table(title="Knowledge Domains", show_header=True, header_style="bold cyan")
    table.add_column("Domain ID", style="bold green")
    table.add_column("Domain Name", style="white")
    table.add_column("Topics Count", style="yellow")
    table.add_column("Trusted Sources")

    for d_id in domains:
        profile = manager.get_domain(d_id)
        table.add_row(
            profile.id,
            profile.name,
            str(len(profile.topics)),
            ", ".join(profile.config.trusted_sources[:3]) or "None",
        )

    console.print(table)


@domain_group.command("info")
@click.argument("domain_id")
def domain_info_cmd(domain_id: str) -> None:
    """Show details, topics, and configuration for a domain."""
    config = get_config()
    manager = DomainManager(config.project_root)
    try:
        profile = manager.get_domain(domain_id)
    except Exception as e:
        console.print(f"[bold red]Domain not found:[/bold red] {e}")
        return

    console.print(Panel.fit(
        f"[bold cyan]{profile.name}[/bold cyan] ([green]{profile.id}[/green])\n"
        f"[dim]{profile.description}[/dim]\n\n"
        f"Trusted Sources: {', '.join(profile.config.trusted_sources)}\n"
        f"Blacklisted Domains: {', '.join(profile.config.blacklisted_domains)}\n"
        f"Topics: {len(profile.topics)}",
        title=f"Domain Info: {profile.id}"
    ))

    if profile.topics:
        t_table = Table(title=f"Topics in {profile.id}", show_header=True)
        t_table.add_column("ID", style="cyan", no_wrap=True)
        t_table.add_column("Title", style="bold")
        t_table.add_column("Queries (RU/EN)")
        for t in profile.topics:
            all_q = t.queries_ru + t.queries_en
            t_table.add_row(t.id, t.title, f"{len(all_q)} queries ({', '.join(all_q[:2])}...)")
        console.print(t_table)


# --- Web Ingestion & Harvesting Group ---

@cli.group("web")
def web_group() -> None:
    """Primary web source discovery, decompilation, and ingestion."""
    pass


@web_group.command("search")
@click.option("--domain", default="computer_science", help="Target domain")
@click.option("--topic", required=True, help="Topic identifier")
@click.option("--max-results", default=5, help="Max web search results")
def web_search_cmd(domain: str, topic: str, max_results: int) -> None:
    """Search for primary web articles, documentation, and papers for a topic."""
    config = get_config()
    db = Database(config.database_path)
    manager = DomainManager(config.project_root)
    harvester = WebHarvester(config, db, domain_manager=manager)

    console.print(f"[bold cyan]Searching web for topic:[/bold cyan] {topic} [Домен: [yellow]{domain}[/yellow]]")
    profile = manager.get_domain(domain)
    topic_obj = profile.get_topic(topic)
    if not topic_obj:
        console.print(f"[bold red]Topic '{topic}' not found in domain '{domain}'.[/bold red]")
        return

    results = harvester.search_provider.search_for_topic(
        topic=topic_obj, domain_config=profile.config, max_results=max_results
    )
    if not results:
        console.print("[yellow]No search results found.[/yellow]")
        return

    table = Table(title=f"Web Search Results ({topic})", show_header=True)
    table.add_column("#", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("URL", style="cyan")
    table.add_column("Score", style="green")

    for i, res in enumerate(results, 1):
        table.add_row(str(i), res.title[:60], res.url, f"{res.score:.1f}")

    console.print(table)


@web_group.command("ingest")
@click.argument("url")
@click.option("--domain", default="computer_science", help="Target domain (computer_science, english_learning, etc.)")
@click.option("--topic", default="general", help="Target topic identifier")
@click.option("--analyze/--no-analyze", default=True, help="Run two-pass AI analysis after extraction")
@click.option("--force", is_flag=True, help="Force Methodist pass even if Gatekeeper flagged review/borderline")
def web_ingest_cmd(url: str, domain: str, topic: str, analyze: bool, force: bool) -> None:
    """Fetch, decompile, and optionally run two-pass analysis on a primary web article."""
    config = get_config()
    db = Database(config.database_path)
    manager = DomainManager(config.project_root)
    harvester = WebHarvester(config, db, domain_manager=manager)

    console.print(f"[bold cyan]Ingesting primary web source:[/bold cyan] {url}")
    console.print(f"Domain: [yellow]{domain}[/yellow] | Topic: [yellow]{topic}[/yellow]")

    try:
        source = harvester.ingest_url(url=url, topic_id=topic, domain=domain)
    except Exception as e:
        console.print(f"[bold red]Extraction failed:[/bold red] {e}")
        return

    console.print(f"[bold green]Successfully extracted & decompiled:[/bold green] {source.title}")
    console.print(f"- Words: [yellow]{source.word_count}[/yellow] | Segments: [yellow]{len(source.segments)}[/yellow] [SEC-XX]")

    if not analyze:
        console.print("[dim]Analysis skipped (--no-analyze).[/dim]")
        return

    console.print("[bold cyan]Executing Isomorphic Two-Pass AI Analysis...[/bold cyan]")
    analysis = AnalysisPipeline(config, db, domain_manager=manager)
    gate_res, meth_res = analysis.run_two_pass_analysis(source=source, force_methodist=force)

    if gate_res:
        console.print(f"Gatekeeper Decision: [bold]{gate_res.decision.value}[/bold] (Score: {gate_res.relevance_score}/10, Noise: {gate_res.commercial_noise_score}/10)")
    if meth_res:
        dest_dir = (
            f"knowledge_base/sources/{source.topic_id}/"
            if source.domain == "crypto"
            else f"knowledge_base/domains/{source.domain}/sources/{source.topic_id}/"
        )
        console.print(f"[bold green]Methodist pass completed! Verified source published under:[/bold green] [cyan]{dest_dir}[/cyan]")
    else:
        console.print("[yellow]Document did not pass Gatekeeper threshold. Methodist pass skipped. (Use --force to override)[/yellow]")


# --- Sales Academy Subgroup ---

@cli.group("academy")
def academy_group() -> None:
    """Sales Academy training and evaluation tools."""
    pass


@academy_group.command("quiz")
@click.option("--topic", default="funding-rate-arbitrage", help="Topic to quiz manager on")
def quiz_cmd(topic: str) -> None:
    """Run an interactive technical quiz for managers."""
    config = get_config()
    db = Database(config.database_path)
    q_gen = QuestionGenerator(db)
    evaluator = AnswerEvaluator()

    questions = q_gen.get_questions_by_topic(topic, count=2)
    if not questions:
        console.print("[yellow]No questions found for this topic.[/yellow]")
        return

    console.print(Panel.fit(f"[bold green]NULLSPREAD Sales Academy Quiz[/bold green]\nТема: [cyan]{topic}[/cyan]"))

    for i, q in enumerate(questions, start=1):
        console.print(f"\n[bold yellow]Вопрос {i} ({q.category.value}):[/bold yellow] {q.question}")
        answer = Prompt.ask("[bold cyan]Ваш ответ[/bold cyan]")

        res = evaluator.evaluate_response(q, answer)
        if res.has_critical_error:
            console.print(f"[bold red]❌ КРИТИЧЕСКАЯ ОШИБКА:[/bold red] {res.critical_error_details}")
        elif res.is_passing:
            console.print(f"[bold green]✅ СДАНО ({res.score}/10):[/bold green]\n{res.feedback}")
        else:
            console.print(f"[bold yellow]⚠️ ТРЕБУЕТ ДОРАБОТКИ ({res.score}/10):[/bold yellow]\n{res.feedback}")


@academy_group.command("roleplay")
@click.option("--difficulty", type=click.Choice(["easy", "medium", "hard"]), default="hard")
def roleplay_cmd(difficulty: str) -> None:
    """Start interactive roleplay sparring session with a skeptical crypto investor."""
    config = get_config()
    db = Database(config.database_path)
    persona = InvestorPersona(difficulty=difficulty)
    session = RoleplaySession(db, difficulty=difficulty, persona=persona)

    console.print(Panel(persona.intro_prompt(), title="[bold red]Клиентский тренажер (Sparring Session)[/bold red]"))

    challenge = session.get_challenge(0)
    console.print(f"\n[bold yellow]Скептичный инвестор:[/bold yellow] «{challenge.question}»")
    answer = Prompt.ask("[bold cyan]Ответ менеджера NULLSPREAD[/bold cyan]")

    res = session.submit_response(challenge, answer)

    console.print("\n[bold]=== Результат аттестации ===[/bold]")
    if res.has_critical_error:
        console.print(f"[bold red]❌ СЦЕНАРИЙ ЗАБЛОКИРОВАН:[/bold red] {res.critical_error_details}")
        console.print("[red]Вы допустили критическую ошибку в аргументации или пообещали гарантии.[/red]")
    elif res.is_passing:
        console.print(f"[bold green]✅ УСПЕШНО ({res.score}/10):[/bold green] Клиент удовлетворен ответом и готов обсуждать детали.")
    else:
        console.print(f"[bold yellow]⚠️ НЕ СДАНО ({res.score}/10):[/bold yellow] Ответ поверхностный, клиент ушел к конкурентам.")

    console.print(f"\n[dim]{res.feedback}[/dim]")


# --- Transcript Sniffer & Semi-Manual Audit ---

@cli.command("audit")
@click.argument("target", required=False)
@click.option("--clipboard/--no-clipboard", default=True, help="Copy generated audit prompt to clipboard")
def audit_cmd(target: Optional[str], clipboard: bool) -> None:
    """Generate a 5-point 'Gem vs Trash' audit prompt from subtitles for ChatGPT/Claude."""
    from research_academy.pipeline.transcript_sniffer import (
        TranscriptSniffer,
        extract_youtube_video_id,
    )

    sniffer = TranscriptSniffer()

    if not target:
        config = get_config()
        db = Database(config.database_path)
        videos = db.list_videos(limit=1)
        if not videos:
            console.print("[yellow]Укажите ссылку на YouTube или video_id: `research audit https://youtu.be/...`[/yellow]")
            return
        target = videos[0].video_id
        console.print(f"[cyan]Взят последний ролик из базы данных: {videos[0].title} ({target})[/cyan]")

    ok, prompt_or_err = sniffer.inspect_and_build_prompt(target, copy_to_clipboard=clipboard)
    if not ok:
        console.print(f"[bold red]Ошибка аудита:[/bold red] {prompt_or_err}")
    elif not clipboard:
        console.print(prompt_or_err)


@cli.command("sniffer")
def sniffer_cmd() -> None:
    """Run clipboard watcher: copy any YouTube link in browser -> get ready-to-paste LLM audit prompt in clipboard!"""
    import time
    import pyperclip
    from research_academy.pipeline.transcript_sniffer import (
        TranscriptSniffer,
        extract_youtube_video_id,
    )

    sniffer = TranscriptSniffer()
    console.print(Panel.fit(
        f"[bold green]NULLSPREAD YOUTUBE CLIPBOARD SNIFFER ЗАПУЩЕН[/bold green]\n\n"
        "1. Листай YouTube в браузере по матрице запросов.\n"
        "2. Нажимай 'Копировать ссылку на видео' ([bold cyan]Ctrl + C[/bold cyan]).\n"
        "3. Полные субтитры мгновенно сохраняются файлом в [cyan]transcripts_sniffer/[/cyan].\n"
        "4. В буфер обмена падает [bold yellow]легкий промпт (~1.5 КБ)[/bold yellow] со счетчиком аудита.\n"
        "5. В браузере (ChatGPT/Claude/DeepSeek) прикрепи файл и жми [bold yellow]Ctrl + V[/bold yellow]!\n"
        "   [dim](Браузерная страница больше никогда не зависает от гигантского текста!)[/dim]\n\n"
        f"[dim]Текущий счетчик: аудит #{sniffer.counter} | Для выхода нажми Ctrl + C[/dim]"
    ))

    last_clipboard = ""
    try:
        last_clipboard = pyperclip.paste().strip()
    except Exception:
        pass

    while True:
        try:
            time.sleep(0.5)
            current = pyperclip.paste().strip()
            if current and current != last_clipboard:
                last_clipboard = current
                # Check if it's a YouTube link
                vid = extract_youtube_video_id(current)
                if vid and not current.startswith("# 🎬 [AUDIT"):
                    console.print(f"\n[cyan]🔍 Обнаружена ссылка YouTube: {current} (ID: {vid})[/cyan]")
                    ok, prompt_or_err = sniffer.inspect_and_build_prompt(vid, copy_to_clipboard=True)
                    if ok:
                        try:
                            last_clipboard = pyperclip.paste().strip()
                        except Exception:
                            pass
        except KeyboardInterrupt:
            console.print("\n[yellow]Остановка слушателя буфера обмена.[/yellow]")
            break
        except Exception as e:
            time.sleep(1)


@cli.command("harvest")
@click.option("--module", default=None, help="ID конкретного модуля (например 00_crypto_fundamentals) или пропустите для всех 7 модулей")
def harvest_cmd(module: Optional[str]) -> None:
    """Automated matrix harvester: finds 1 solid video per query with subtitles, filters negative keywords, and saves files + prompts."""
    from research_academy.pipeline.matrix_harvester import MatrixHarvester
    from research_academy.queries_config import SEARCH_MATRIX

    harvester = MatrixHarvester()
    if module:
        if module not in SEARCH_MATRIX:
            console.print(f"[bold red]Неизвестный модуль:[/bold red] {module}. Доступные: {list(SEARCH_MATRIX.keys())}")
            sys.exit(1)
        results = harvester.harvest_module(module)
        console.print(f"\n[bold green]Сбор по модулю {module} завершен![/bold green] Найдено и сохранено: [yellow]{len(results)}[/yellow] роликов.")
    else:
        console.print("[bold green]🚀 Запуск сбора по всей матрице (7 Дней / 7 Модулей)...[/bold green]")
        all_res = harvester.harvest_all_matrix()
        total = sum(len(v) for v in all_res.values())
        console.print(f"\n[bold green]🎉 Полный сбор завершен![/bold green] Всего обработано и сохранено: [yellow]{total}[/yellow] роликов с субтитрами.")


@cli.command("digest")
@click.argument("urls", nargs=-1, required=False)
@click.option("--from-clipboard", "-c", is_flag=True, default=False, help="Прочитать URL видео прямо из текущего буфера обмена Windows")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Файл со списком ссылок (по одной на строку)")
@click.option("--mode", "-m", type=click.Choice(["summary", "tutorial", "audit"]), default="summary", show_default=True, help="Режим промпта для буфера обмена (summary | tutorial | audit)")
@click.option("--output-dir", "-o", default="digests", show_default=True, help="Папка для сохранения Markdown дайджестов")
@click.option("--clipboard/--no-clipboard", default=True, show_default=True, help="Копировать готовый монолитный запрос (промпт + транскрипт) в буфер обмена")
@click.option("--open", "open_file", is_flag=True, default=False, help="Автоматически открыть созданный Markdown файл в редакторе")
def digest_cmd(
    urls: tuple[str, ...],
    from_clipboard: bool,
    input_file: Optional[str],
    mode: str,
    output_dir: str,
    clipboard: bool,
    open_file: bool,
) -> None:
    """Extract structured Markdown transcript & prompt from YouTube URL(s) without watching."""
    import pyperclip
    from research_academy.pipeline.ad_hoc_digest import (
        AdHocDigestGenerator,
        play_chime_error,
        play_chime_success,
    )
    from research_academy.pipeline.transcript_sniffer import extract_youtube_video_id

    target_urls: List[str] = list(urls)

    if from_clipboard:
        try:
            cb_content = pyperclip.paste().strip()
            if cb_content:
                # Find all YouTube URLs in clipboard
                found_vids = []
                for token in cb_content.split():
                    vid = extract_youtube_video_id(token)
                    if vid and vid not in found_vids:
                        found_vids.append(token)
                if found_vids:
                    target_urls.extend(found_vids)
                else:
                    vid = extract_youtube_video_id(cb_content)
                    if vid:
                        target_urls.append(cb_content)
        except Exception as e:
            logger.warning("Error reading clipboard: %s", e)

    if input_file:
        try:
            with open(input_file, "r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        target_urls.append(line)
        except Exception as e:
            console.print(f"[bold red]Ошибка чтения файла ссылок:[/bold red] {e}")

    if not target_urls:
        play_chime_error()
        console.print(
            Panel.fit(
                "[bold red]Не указано ни одной ссылки на YouTube![/bold red]\n\n"
                "Примеры использования:\n"
                "  [cyan]python -m research_academy.cli digest \"https://youtu.be/...\"[/cyan]\n"
                "  [cyan]python -m research_academy.cli digest --from-clipboard --mode summary[/cyan]\n"
                "  [cyan]python -m research_academy.cli digest --from-clipboard --mode audit[/cyan]\n"
                "  [cyan]python -m research_academy.cli digest url1 url2 url3 -o my_digests[/cyan]",
                title="YouTube Digest CLI",
            )
        )
        sys.exit(1)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    generator = AdHocDigestGenerator(default_output_dir=out_path)

    console.print(f"[bold cyan]🔍 Запуск обработки {len(target_urls)} видео (Режим промпта: [yellow]{mode}[/yellow])...[/bold cyan]\n")

    results = []
    # If single URL, copy_clipboard is respected. If multiple, copy the first or don't spam.
    for idx, u in enumerate(target_urls, 1):
        should_copy = clipboard and (len(target_urls) == 1 or idx == 1)
        console.print(f"[{idx}/{len(target_urls)}] Извлекаю данные: [dim]{u}[/dim]...")
        res = generator.process_url(
            url_or_id=u,
            output_dir=out_path,
            mode=mode,
            copy_clipboard=should_copy,
        )
        results.append(res)
        if res.error:
            console.print(f"  [bold red]ОШИБКА:[/bold red] {res.error}")
        else:
            console.print(
                f"  [bold green]УСПЕХ:[/bold green] [bold]{res.title}[/bold] ({res.channel}) "
                f"| Хронометраж: {res.duration_str} ➔ Чтение: ~{res.reading_time_min} мин ({res.word_count:,} слов)"
            )
            if res.chapters_count > 0:
                console.print(f"  [cyan]Главы автора:[/cyan] Найдено {res.chapters_count} глав с таймкодами")

    # Final summary display
    successful = [r for r in results if not r.error]
    if successful:
        table = Table(title="Результаты экстракции (YouTube Digest)", show_header=True, header_style="bold cyan")
        table.add_column("Видео", style="bold")
        table.add_column("Канал")
        table.add_column("Хронометраж")
        table.add_column("Чтение (~мин)")
        table.add_column("Файл конспекта")

        total_words = 0
        for r in successful:
            total_words += r.word_count
            table.add_row(
                r.title[:45] + "..." if len(r.title) > 45 else r.title,
                r.channel,
                r.duration_str,
                f"~{r.reading_time_min} мин",
                f"[link=file:///{r.markdown_path.resolve()}]{r.markdown_path.name}[/link]",
            )
        console.print(table)

        if clipboard and any(r.clipboard_copied for r in successful):
            console.print(
                "\n[bold green]Готовый запрос скопирован в буфер обмена![/bold green] "
                "[bold yellow]Открывай Claude / ChatGPT / DeepSeek и жми Ctrl + V[/bold yellow]"
            )

        if open_file and successful:
            try:
                click.launch(str(successful[0].markdown_path))
            except Exception as e:
                logger.warning("Could not open file: %s", e)
    else:
        console.print("[bold red]Ни одно видео не удалось обработать.[/bold red]")
        sys.exit(1)


@cli.command("prompt")
@click.argument(
    "mode",
    type=click.Choice(["summary", "audit", "tutorial", "compare", "multi"], case_sensitive=False),
    default="summary",
    required=False,
)
@click.option(
    "-m",
    "--mode",
    "mode_opt",
    type=click.Choice(["summary", "audit", "tutorial", "compare", "multi"], case_sensitive=False),
    default=None,
    help="Режим промпта (summary | audit | tutorial | compare)",
)
def prompt_cmd(mode: str, mode_opt: Optional[str]) -> None:
    """Скопировать чистый промпт для прикрепленных файлов в буфер обмена."""
    import pyperclip
    from research_academy.pipeline.ad_hoc_digest import (
        get_standalone_prompt,
        play_chime_success,
    )

    chosen_mode = mode_opt or mode or "summary"
    title, prompt_text = get_standalone_prompt(chosen_mode)

    try:
        pyperclip.copy(prompt_text.strip())
        play_chime_success()
    except Exception as e:
        logger.warning("Failed to copy prompt to clipboard: %s", e)

    console.print(
        Panel.fit(
            f"[bold green]Промпт скопирован в буфер обмена![/bold green]\n\n"
            f"[bold cyan]Название:[/bold cyan] {title}\n"
            f"[bold yellow]Режим:[/bold yellow] {chosen_mode}\n\n"
            f"[dim]Вставь через Ctrl + V в окно чата после прикрепления файлов (Ctrl + O).[/dim]",
            border_style="green",
        )
    )


@cli.command("latest-digest")
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["summary", "tutorial", "audit", "compare", "multi"], case_sensitive=False),
    default=None,
    help="Режим промпта для оборачивания дайджеста на лету в буфер (summary | tutorial | audit | compare)",
)
@click.option(
    "-f",
    "--file",
    "target_file_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Конкретный файл дайджеста (по умолчанию берется самый свежий)",
)
@click.option(
    "-c/-nc",
    "--copy/--no-copy",
    "copy_clipboard",
    default=True,
    help="Скопировать в буфер обмена Windows (путь, либо готовый payload при указании -m)",
)
@click.option(
    "-o",
    "--open",
    "open_file",
    is_flag=True,
    help="Открыть последний файл в редакторе по умолчанию / VS Code",
)
@click.option(
    "-r",
    "--reveal",
    "reveal_file",
    is_flag=True,
    help="Показать последний файл в Проводнике Windows",
)
@click.option(
    "--relative",
    is_flag=True,
    help="Использовать путь относительно корня проекта",
)
@click.option(
    "-d",
    "--dir",
    "digest_dir",
    default="digests",
    help="Папка с дайджестами (по умолчанию digests)",
)
def latest_digest_cmd(
    mode: Optional[str],
    target_file_path: Optional[Path],
    copy_clipboard: bool,
    open_file: bool,
    reveal_file: bool,
    relative: bool,
    digest_dir: str,
) -> None:
    """Найти дайджест, скопировать его путь или обернуть в промпт на лету."""
    import subprocess
    from research_academy.pipeline.ad_hoc_digest import (
        find_latest_digest,
        play_chime_error,
        play_chime_success,
        wrap_digest_with_prompt,
    )

    if target_file_path:
        target_file = target_file_path
    else:
        target_dir = Path(digest_dir)
        target_file = find_latest_digest(target_dir)

    if not target_file or not target_file.exists():
        play_chime_error()
        console.print(f"[bold red]Файлы дайджестов не найдены![/bold red]")
        sys.exit(1)

    resolved_path = target_file.resolve()
    if relative:
        try:
            path_to_use = str(resolved_path.relative_to(Path.cwd()))
        except ValueError:
            path_to_use = str(resolved_path)
    else:
        path_to_use = str(resolved_path)

    # If mode is specified: in-memory wrap content with prompt template without touching disk file!
    payload_to_copy = None
    if mode:
        content = target_file.read_text(encoding="utf-8")
        payload_to_copy = wrap_digest_with_prompt(content, mode=mode.lower())
    else:
        payload_to_copy = path_to_use.strip()

    # 1. Copy to clipboard
    if copy_clipboard and payload_to_copy:
        try:
            import pyperclip
            pyperclip.copy(payload_to_copy)
            play_chime_success()
        except Exception as e:
            logger.warning("Failed to copy to clipboard: %s", e)

    # 2. Display summary
    stat = target_file.stat()
    size_kb = round(stat.st_size / 1024, 1)
    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    table = Table(title="YouTube дайджест (Локальный доступ)", show_header=True, header_style="bold cyan")
    table.add_column("Параметр", style="cyan", no_wrap=True)
    table.add_column("Значение", style="white")

    table.add_row("Файл", target_file.name)
    table.add_row("Путь", path_to_use)
    table.add_row("Размер", f"{size_kb} КБ")
    table.add_row("Изменен", mod_time)
    if mode:
        table.add_row("Режим промпта", f"[bold yellow]{mode}[/bold yellow] (обернут на лету в буфер)")

    console.print(table)
    if copy_clipboard:
        if mode:
            console.print(
                f"[bold green]Дайджест обернут в промпт ([yellow]{mode}[/yellow]) и скопирован в буфер обмена![/bold green]\n"
                "[bold cyan]Жми Ctrl + V в чат Claude / ChatGPT / DeepSeek[/bold cyan]"
            )
        else:
            console.print("[bold green]Путь скопирован в буфер обмена![/bold green] (чистая строка без \\r\\n)")

    # 3. Handle actions
    if reveal_file:
        try:
            subprocess.run(["explorer.exe", f"/select,{resolved_path}"], check=False)
        except Exception as e:
            logger.warning("Failed to reveal file in explorer: %s", e)

    if open_file:
        try:
            click.launch(str(resolved_path))
        except Exception as e:
            logger.warning("Failed to open file: %s", e)


if __name__ == "__main__":
    cli()


