"""CLI interface for NULLSPREAD Research & Sales Academy."""

from __future__ import annotations

import sys
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


if __name__ == "__main__":
    cli()

