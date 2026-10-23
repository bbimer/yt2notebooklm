"""Matrix Harvester: automated discovery, negative keyword filtering, transcript extraction,
and audit file generation across all 7 modules of the SEARCH_MATRIX."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yt_dlp
from rich.console import Console

from research_academy.config import AppConfig, get_config
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, VideoMetadata
from research_academy.pipeline.transcript_sniffer import (
    build_semi_manual_audit_prompt,
    calculate_transcript_telemetry,
)
from research_academy.providers.transcripts import YouTubeApiTranscriptProvider
from research_academy.queries_config import NEGATIVE_KEYWORDS, SEARCH_MATRIX

logger = logging.getLogger(__name__)
console = Console()


def contains_negative_keywords(title: str, negative_keywords: List[str]) -> Optional[str]:
    title_lower = title.lower()
    for kw in negative_keywords:
        if kw.lower() in title_lower:
            return kw
    return None


class MatrixHarvester:
    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db: Optional[Database] = None,
        output_dir: Optional[Path] = None,
    ):
        self.config = config or get_config()
        self.db = db or Database(self.config.database_path)
        self.transcript_provider = YouTubeApiTranscriptProvider()
        self.output_dir = Path(output_dir or (self.config.project_root / "transcripts_sniffer"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        existing = list(self.output_dir.glob("audit_*.txt"))
        self.counter = len(existing) + 1

        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "ignoreerrors": True,
        }

    def harvest_query(
        self,
        query: str,
        module_id: str,
        module_title: str,
        max_search_candidates: int = 4,
    ) -> Optional[Dict[str, Any]]:
        """
        Searches candidates for a single query, verifies subtitles,
        filters negative keywords, and persists file + DB.
        """
        search_query = f"ytsearch{max_search_candidates}:{query}"

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if not info or "entries" not in info:
                    return None
                entries = [e for e in info.get("entries", []) if e and "id" in e]
        except Exception as e:
            logger.warning("Search failed for '%s': %s", query, e)
            return None

        for entry in entries:
            vid = entry.get("id")
            title = entry.get("title", f"Video {vid}")
            channel = entry.get("uploader", "YouTube Creator")
            channel_id = entry.get("channel_id", "unknown_channel")
            duration = int(entry.get("duration") or 0)
            url = f"https://www.youtube.com/watch?v={vid}"

            # 1. Negative keywords filter
            scam_kw = contains_negative_keywords(title, NEGATIVE_KEYWORDS)
            if scam_kw:
                logger.info("Skipping '%s' (negative keyword: %s)", title, scam_kw)
                continue

            # 2. Duration filter (Shorts < 420s, RU max 3000s, EN max 4500s for deep quant lectures)
            is_en_query = not any("а" <= ch <= "я" or "А" <= ch <= "Я" for ch in query)
            max_dur = 4500 if is_en_query else 3000
            if duration > 0:
                if duration < 420:
                    logger.info("Skipping '%s' (too short: %ds < 420s)", title, duration)
                    continue
                if duration > max_dur:
                    logger.info("Skipping '%s' (too long: %ds > %ds)", title, duration, max_dur)
                    continue

            # 3. Check transcript
            transcript = self.transcript_provider.get_transcript(vid)
            if not transcript.has_subtitles or transcript.word_count < 150:
                continue

            # Found a valid candidate with subtitles!
            telemetry = calculate_transcript_telemetry(transcript)
            current_counter = self.counter
            filename = f"audit_{current_counter:03d}_{module_id}_{vid}.txt"
            filepath = self.output_dir / filename

            # Save full transcript file
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if transcript.segments:
                body_lines = [
                    f"[{s.timestamp_formatted}] {s.text}"
                    for s in transcript.segments
                    if s.text.strip()
                ]
                formatted_body = "\n".join(body_lines)
            else:
                formatted_body = transcript.full_normalized_text or transcript.full_raw_text

            file_content = (
                f"================================================================================\n"
                f"NULLSPREAD RESEARCH · СУБТИТРЫ ВИДЕО ДЛЯ АУДИТА #{current_counter}\n"
                f"Модуль: {module_title} ({module_id})\n"
                f"Поисковый запрос: {query}\n"
                f"================================================================================\n"
                f"ID видео: {vid}\n"
                f"Название: {title}\n"
                f"Канал: {channel}\n"
                f"Ссылка: {url}\n"
                f"Объем: {telemetry['word_count']} слов (~{telemetry['est_duration_minutes']} мин)\n"
                f"Язык: {transcript.language}\n"
                f"Файл: {filename}\n"
                f"Создан: {now_str}\n"
                f"================================================================================\n\n"
                f"{formatted_body}\n"
            )
            filepath.write_text(file_content, encoding="utf-8")

            # Save to SQLite database
            v_meta = VideoMetadata(
                video_id=vid,
                title=title,
                channel_id=channel_id,
                channel_title=channel,
                duration_seconds=duration or int(telemetry["est_duration_minutes"] * 60),
                url=url,
                topic_id=module_id,
                queries_matched=[query],
                language=transcript.language,
                discovery_status=DiscoveryStatus.TRANSCRIPT_FETCHED,
            )
            self.db.upsert_video(v_meta)
            self.db.save_transcript(transcript)

            prompt = build_semi_manual_audit_prompt(
                video_title=title,
                video_url=url,
                channel_title=channel,
                transcript=transcript,
                telemetry=telemetry,
                audit_counter=current_counter,
                transcript_filename=filename,
            )

            prompt_path = self.output_dir / f"audit_{current_counter:03d}_{module_id}_{vid}_PROMPT.md"
            prompt_path.write_text(prompt, encoding="utf-8")

            self.counter += 1

            return {
                "counter": current_counter,
                "video_id": vid,
                "title": title,
                "channel": channel,
                "url": url,
                "words": telemetry["word_count"],
                "duration_min": telemetry["est_duration_minutes"],
                "file": str(filepath),
                "prompt_file": str(prompt_path),
                "trader_markers": telemetry["trader_markers"],
                "scam_markers": telemetry["scam_markers"],
            }

        return None

    def harvest_module(
        self,
        module_id: str,
        max_videos_per_query: int = 1,
    ) -> List[Dict[str, Any]]:
        mod = SEARCH_MATRIX.get(module_id)
        if not mod:
            raise ValueError(f"Unknown module: {module_id}")

        mod_title = mod["title"]
        queries = mod.get("queries_ru", []) + mod.get("queries_en", [])
        harvested = []

        console.print(f"\n[bold cyan]▶ Запуск сбора для: {mod_title}[/bold cyan] ({len(queries)} запросов)")

        for i, q in enumerate(queries, 1):
            console.print(f"  [dim][{i}/{len(queries)}][/dim] Поиск: [yellow]'{q}'[/yellow]...", end=" ")
            res = self.harvest_query(
                query=q,
                module_id=module_id,
                module_title=mod_title,
            )
            if res:
                console.print(f"[bold green]✔ Найдено:[/bold green] {res['title'][:45]}... ([cyan]{res['words']} слов[/cyan])")
                harvested.append(res)
            else:
                console.print("[dim yellow]⚠ Роликов с субтитрами не найдено[/dim yellow]")
            time.sleep(0.3)

        return harvested

    def harvest_all_matrix(self) -> Dict[str, List[Dict[str, Any]]]:
        all_results = {}
        for mod_id in SEARCH_MATRIX.keys():
            if mod_id == "02_arbitrage_types":  # alias
                continue
            res = self.harvest_module(mod_id)
            all_results[mod_id] = res
        return all_results

