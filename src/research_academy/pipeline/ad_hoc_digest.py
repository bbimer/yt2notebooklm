"""Ad-Hoc YouTube Digest & Prompt Builder Pipeline.

Fast, lightweight extractor for arbitrary YouTube videos:
- Pulls metadata and chapters via yt-dlp
- Fetches transcript via YouTube Subtitles API
- Aggregates fragments into clean 60-90s paragraphs
- Saves structured Markdown to digests/
- Copies single-task prompt + transcript to clipboard with sound chime for instant LLM paste.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyperclip
import yt_dlp

from research_academy.models import TranscriptSegment, VideoTranscript
from research_academy.pipeline.transcript_sniffer import extract_youtube_video_id
from research_academy.providers.transcripts import YouTubeApiTranscriptProvider

logger = logging.getLogger(__name__)

# Windows audio feedback
try:
    import winsound
except ImportError:
    winsound = None


def play_chime_success() -> None:
    """Plays pleasant audio chime on Windows when digest is copied."""
    if winsound:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
        try:
            winsound.Beep(1000, 100)
            winsound.Beep(1400, 150)
        except Exception:
            pass


def play_chime_error() -> None:
    """Plays error alert on Windows when error occurs."""
    if winsound:
        try:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            pass
        try:
            winsound.Beep(300, 300)
        except Exception:
            pass


def slugify(text: str, max_len: int = 50) -> str:
    """Converts title to a safe filename slug."""
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[-\s]+", "_", text)
    return text[:max_len].strip("_") or "video"


def format_duration(seconds: Optional[int]) -> str:
    """Formats duration in seconds to readable string (e.g., '14:20' or '1h 12m')."""
    if not seconds or seconds <= 0:
        return "Не указана"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    return f"{minutes:02d}:{secs:02d}"


def calculate_reading_time_minutes(word_count: int, wpm: int = 220) -> int:
    """Estimates reading time in minutes based on word count."""
    return max(1, round(word_count / wpm))


def find_latest_digest(directory: Optional[Path] = None) -> Optional[Path]:
    """
    Finds the most recently modified markdown digest file in the specified directory.
    Falls back to sorting by filename timestamp if modification times match.
    """
    dir_path = directory or (Path.cwd() / "digests")
    if not dir_path.exists():
        return None

    md_files = [p for p in dir_path.glob("*.md") if p.is_file()]
    if not md_files:
        return None

    # Sort primarily by st_mtime descending, secondarily by name descending
    md_files.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
    return md_files[0]


def aggregate_transcript_segments(
    segments: List[TranscriptSegment],
    target_duration_sec: float = 75.0,
    max_words: int = 160,
) -> List[Tuple[str, str]]:
    """
    Merges rapid 2-4s subtitle fragments into coherent, readable paragraphs
    spanning ~60-90 seconds (or ~120-160 words) with a single [MM:SS] timestamp.
    """
    if not segments:
        return []

    paragraphs: List[Tuple[str, str]] = []
    current_time_str = segments[0].timestamp_formatted
    current_start_sec = segments[0].start_seconds
    current_words: List[str] = []

    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue

        words = text.split()
        duration_span = seg.start_seconds - current_start_sec

        # If current paragraph already has words AND adding this segment crosses duration or word limit:
        # flush current paragraph first, then start a new one with this segment!
        if current_words and (duration_span >= target_duration_sec or len(current_words) >= max_words):
            combined_text = " ".join(current_words)
            if combined_text:
                combined_text = combined_text[0].upper() + combined_text[1:]
            paragraphs.append((current_time_str, combined_text))

            current_time_str = seg.timestamp_formatted
            current_start_sec = seg.start_seconds
            current_words = []

        current_words.extend(words)

    if current_words:
        combined_text = " ".join(current_words)
        if combined_text:
            combined_text = combined_text[0].upper() + combined_text[1:]
        paragraphs.append((current_time_str, combined_text))

    return paragraphs


PROMPT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "summary": {
        "title": "Глубокий конспект и ключевые инсайты (Executive Summary)",
        "prompt": (
            "Ты — высококлассный аналитик и эксперт по структурированию информации.\n"
            "Твоя задача — изучить прикрепленный(е) материал(ы) (паспорт и транскрипт видео) и составить глубокий, "
            "плотный исполнительский конспект (Executive Summary).\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. КЛЮЧЕВАЯ СУТЬ (1-2 предложения): в чем главная идея и ценность материала?\n"
            "2. СТРУКТУРИРОВАННЫЙ РАЗБОР ПО ТЕМАМ: выдели главные смысловые блоки с привязкой к главам/таймкодам.\n"
            "3. ВАЖНЫЕ ИНСАЙТЫ И ФАКТЫ: ключевые тезисы, неочевидные выводы, цифры, правила и примеры автора.\n"
            "4. ПРАКТИЧЕСКИЕ ВЫВОДЫ (Actionable Takeaways): что конкретно слушателю стоит взять и применить прямо сейчас?\n"
            "5. БЕЗ ВОДЫ: полностью убери все приветствия, самопиар, интеграции, кликбейты и повторы спикера."
        ),
    },
    "tutorial": {
        "title": "Практическое руководство / Пошаговый алгоритм (Actionable Tutorial)",
        "prompt": (
            "Ты — старший инженер и технический ментор.\n"
            "Твоя задача — извлечь из прикрепленного(ых) материала(ов) пошаговое прикладное руководство.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. ЦЕЛЬ И ПРЕДРЕКВИЗИТЫ: что создается, какой стек, библиотеки или инструменты необходимы.\n"
            "2. ПОШАГОВЫЙ АЛГОРИТМ: строгая хронологическая инструкция действий (Шаг 1, Шаг 2, Шаг 3...).\n"
            "3. КОМАНДЫ, КОД И НАСТРОЙКИ: выдели в отдельные блоки кода все упомянутые команды терминала, конфиги, функции, флаги.\n"
            "4. ПОДВОДНЫЕ КАМНИ И ОШИБКИ: где автор предупреждает о рисках, багах или тонкостях реализации.\n"
            "5. ИТОГОВЫЙ ЧЕК-ЛИСТ: краткий список проверки готовности."
        ),
    },
    "audit": {
        "title": "Критический аудит и проверка на инфоцыганство (Bullshit & Scam Filter)",
        "prompt": (
            "Ты — независимый фактчекер, скептик и технический аудитор.\n"
            "Твоя задача — провести жесткий критический аудит прикрепленного(ых) материала(ов) на предмет достоверности, "
            "практической ценности и скрытого манипулирования.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. ОЦЕНКА ПЛОТНОСТИ ПОЛЬЗЫ (от 1 до 10): процент реального технического мяса против маркетинговой воды.\n"
            "2. ПРОВЕРКА КЛЮЧЕВЫХ ТЕЗИСОВ: какие заявления автора правдивы и обоснованы, а где искажения, спекуляции или ошибки?\n"
            "3. СКРЫТЫЕ МОТИВЫ И ПРОДАЖИ: что спикер продвигает (курс, реферальную ссылку, токен, консультации, хайп)?\n"
            "4. КРАСНЫЕ ФЛАГИ: завышенные обещания, логические тупики, поверхностное понимание темы.\n"
            "5. ЧТО РЕАЛЬНО СТОИТ ЗАБРАТЬ: если в ролике есть крупицы пользы — выдели их сухо и объективно."
        ),
    },
    "compare": {
        "title": "Кросс-анализ и синтез нескольких видео (Multi-Source Comparison & Synthesis)",
        "prompt": (
            "Ты — ведущий аналитик и эксперт по комплексному синтезу информации.\n"
            "Перед тобой транскрипты нескольких видеороликов на одну тему (прикреплены файлами).\n"
            "Твоя задача — сопоставить позиции разных авторов, отфильтровать воду и выдать единый глубокий синтез.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. СВОДНАЯ СУТЬ И КОНСЕНСУС: в чем все авторы полностью согласны между собой? Какая база считается стандартом?\n"
            "2. ТОЧКИ РАСХОЖДЕНИЯ И ПРОТИВОРЕЧИЯ: где мнения спикеров кардинально расходятся, кто дает противоположные советы или разные метрики/цифры?\n"
            "3. ФАКТЧЕКИНГ И ГЛУБИНА (Кто прав?): сравни аргументацию авторов. Кто опирается на реальные цифры, код, документацию и бенчмарки, а кто занимается поверхностным пересказом и спекуляциями?\n"
            "4. УНИКАЛЬНЫЕ ИНСАЙТЫ ПО КАЖДОМУ ИСТОЧНИКУ: выдели ценные крупицы информации («мясо»), которые есть только у автора А, только у автора B и т.д.\n"
            "5. ЕДИНАЯ РЕЗУЛЬТИРУЮЩАЯ СТРАТЕГИЯ (СИНТЕЗ): сформируй итоговый алгоритм/картину на стыке всех материалов без дублирования и воды."
        ),
    },
}


def get_standalone_prompt(mode: str = "summary") -> Tuple[str, str]:
    """
    Returns (title, prompt_text) for pasting into LLM chat when files are attached via Ctrl+O.
    Does NOT include transcript text.
    """
    key = mode.lower()
    if key in ("multi", "comparison", "synthesis"):
        key = "compare"
    template = PROMPT_TEMPLATES.get(key, PROMPT_TEMPLATES["summary"])
    return template["title"], template["prompt"]



@dataclass
class VideoDetails:
    video_id: str
    title: str
    channel: str
    duration_sec: int
    url: str
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    chapters: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DigestResult:
    video_id: str
    title: str
    channel: str
    duration_str: str
    word_count: int
    reading_time_min: int
    markdown_path: Path
    clipboard_copied: bool
    mode_used: str
    chapters_count: int
    error: Optional[str] = None


class AdHocDigestGenerator:
    """Orchestrates ad-hoc extraction and synthesis of single/batch YouTube videos."""

    def __init__(
        self,
        transcript_provider: Optional[YouTubeApiTranscriptProvider] = None,
        default_output_dir: Optional[Path] = None,
    ):
        self.transcript_provider = transcript_provider or YouTubeApiTranscriptProvider()
        self.default_output_dir = default_output_dir or (Path.cwd() / "digests")
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_video_details(self, video_id: str) -> VideoDetails:
        """Fetches metadata and chapters via yt-dlp quickly without downloading."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "ignoreerrors": True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False) or {}
            except Exception as e:
                logger.warning("yt-dlp extract error for %s: %s", video_id, e)
                info = {}

        title = info.get("title") or f"YouTube Video ({video_id})"
        channel = info.get("uploader") or info.get("channel") or "YouTube Creator"
        duration = int(info.get("duration") or 0)
        upload_date = info.get("upload_date")
        view_count = info.get("view_count")

        raw_chapters = info.get("chapters") or []
        chapters: List[Dict[str, Any]] = []
        for ch in raw_chapters:
            if isinstance(ch, dict) and "title" in ch and "start_time" in ch:
                start_sec = int(ch["start_time"])
                chapters.append({
                    "title": ch["title"],
                    "start_time": start_sec,
                    "timestamp": f"{start_sec // 60:02d}:{start_sec % 60:02d}",
                })

        return VideoDetails(
            video_id=video_id,
            title=title,
            channel=channel,
            duration_sec=duration,
            url=url,
            upload_date=upload_date,
            view_count=view_count,
            chapters=chapters,
        )

    def build_markdown_file_content(
        self,
        details: VideoDetails,
        transcript: VideoTranscript,
        paragraphs: List[Tuple[str, str]],
        word_count: int,
        read_time_min: int,
    ) -> str:
        """
        Builds a crystal-clean Markdown file saved to disk as a pure knowledge base document:
        Title + Passport + Chapters + Structured Transcript.
        Zero prompt builder blocks to avoid RAG/vector contamination and instruction leakage.
        """
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        duration_formatted = format_duration(details.duration_sec)

        # Chapters section
        chapters_md = ""
        if details.chapters:
            ch_lines = [f"- `[{c['timestamp']}]` {c['title']}" for c in details.chapters]
            chapters_md = "### Оглавление автора (Chapters):\n" + "\n".join(ch_lines) + "\n\n"

        # Transcript body
        if paragraphs:
            transcript_body = "\n\n".join(f"**`[{ts}]`** {text}" for ts, text in paragraphs)
        else:
            transcript_body = transcript.full_normalized_text or transcript.full_raw_text or "Текст субтитров отсутствует."

        content = f"""# {details.title}

> **Канал:** {details.channel} | **Ссылка:** [{details.url}]({details.url})  
> **Хронометраж:** {duration_formatted} ➔ **Время на чтение конспекта:** ~{read_time_min} мин ({word_count:,} слов)  
> **Дата обработки:** {today_str}

---

## ПАСПОРТ ВИДЕО
- **ID ролика:** `{details.video_id}`
- **Автор / Канал:** {details.channel}
- **Длительность оригинала:** {duration_formatted} ({details.duration_sec} сек)
- **Объем текста субтитров:** {word_count:,} слов
- **Язык субтитров:** {transcript.language}

{chapters_md}---

## СТРУКТУРИРОВАННЫЙ ТРАНСКРИПТ РОЛИКА

{transcript_body}
"""
        return content

    def build_clipboard_payload(
        self,
        details: VideoDetails,
        paragraphs: List[Tuple[str, str]],
        mode: str = "summary",
    ) -> str:
        """
        Builds a single-task, ready-to-execute prompt + passport + chapters + transcript
        specifically engineered for pasting into Claude / ChatGPT in 1 click.
        """
        template = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["summary"])
        prompt_title = template["title"]
        prompt_instruction = template["prompt"]
        duration_formatted = format_duration(details.duration_sec)

        chapters_text = ""
        if details.chapters:
            ch_lines = [f"- [{c['timestamp']}] {c['title']}" for c in details.chapters]
            chapters_text = "ОГЛАВЛЕНИЕ АВТОРА (ТАЙМКОДЫ):\n" + "\n".join(ch_lines) + "\n\n"

        if paragraphs:
            transcript_body = "\n\n".join(f"[{ts}] {text}" for ts, text in paragraphs)
        else:
            transcript_body = "Текст субтитров отсутствует."

        payload = f"""[РЕЖИМ ОБРАБОТКИ: {prompt_title}]

{prompt_instruction}

================================================================================
МЕТАДАННЫЕ ВИДЕО:
- Название: {details.title}
- Канал: {details.channel}
- Ссылка: {details.url}
- Длительность: {duration_formatted}
================================================================================

{chapters_text}ПОЛНЫЙ ТРАНСКРИПТ РОЛИКА (РАЗБИТ ПО СМЫСЛОВЫМ АБЗАЦАМ):
{transcript_body}
"""
        return payload

    def process_url(
        self,
        url_or_id: str,
        output_dir: Optional[Path] = None,
        mode: str = "summary",
        copy_clipboard: bool = True,
    ) -> DigestResult:
        """Processes a single YouTube URL or ID into a clean markdown digest."""
        target_dir = output_dir or self.default_output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        video_id = extract_youtube_video_id(url_or_id)
        if not video_id:
            play_chime_error()
            return DigestResult(
                video_id=url_or_id,
                title="Invalid URL",
                channel="Unknown",
                duration_str="00:00",
                word_count=0,
                reading_time_min=0,
                markdown_path=Path(""),
                clipboard_copied=False,
                mode_used=mode,
                chapters_count=0,
                error=f"Не удалось распознать YouTube Video ID из ссылки: {url_or_id}",
            )

        # 1. Fetch metadata and chapters
        details = self.fetch_video_details(video_id)

        # 2. Fetch transcript
        transcript = self.transcript_provider.get_transcript(video_id)
        if not transcript.has_subtitles:
            play_chime_error()
            return DigestResult(
                video_id=video_id,
                title=details.title,
                channel=details.channel,
                duration_str=format_duration(details.duration_sec),
                word_count=0,
                reading_time_min=0,
                markdown_path=Path(""),
                clipboard_copied=False,
                mode_used=mode,
                chapters_count=len(details.chapters),
                error=f"Субтитры недоступны для видео ({details.title}): {transcript.error_message}",
            )

        # 3. Aggregate segments into coherent ~60-90s paragraphs
        paragraphs = aggregate_transcript_segments(transcript.segments)
        full_text = " ".join(p[1] for p in paragraphs) if paragraphs else (transcript.full_normalized_text or "")
        word_count = len(full_text.split())
        read_time = calculate_reading_time_minutes(word_count)

        # 4. Generate disk markdown file
        date_str = datetime.now().strftime("%Y-%m-%d")
        title_slug = slugify(details.title)
        filename = f"{date_str}_{video_id}_{title_slug}.md"
        file_path = target_dir / filename

        disk_content = self.build_markdown_file_content(
            details=details,
            transcript=transcript,
            paragraphs=paragraphs,
            word_count=word_count,
            read_time_min=read_time,
        )
        file_path.write_text(disk_content, encoding="utf-8")

        # 5. Build clipboard payload and copy
        clipboard_copied = False
        if copy_clipboard:
            payload = self.build_clipboard_payload(
                details=details,
                paragraphs=paragraphs,
                mode=mode,
            )
            try:
                pyperclip.copy(payload)
                clipboard_copied = True
                play_chime_success()
            except Exception as e:
                logger.warning("Failed to copy payload to clipboard: %s", e)

        return DigestResult(
            video_id=video_id,
            title=details.title,
            channel=details.channel,
            duration_str=format_duration(details.duration_sec),
            word_count=word_count,
            reading_time_min=read_time,
            markdown_path=file_path,
            clipboard_copied=clipboard_copied,
            mode_used=mode,
            chapters_count=len(details.chapters),
        )


def wrap_digest_with_prompt(markdown_content: str, mode: str = "summary") -> str:
    """
    Wraps existing clean digest markdown content in-memory with the selected prompt template
    without modifying the disk file.
    """
    template = PROMPT_TEMPLATES.get(mode.lower(), PROMPT_TEMPLATES["summary"])
    prompt_title = template["title"]
    prompt_instruction = template["prompt"]

    payload = f"""[РЕЖИМ ОБРАБОТКИ: {prompt_title}]

{prompt_instruction}

================================================================================
СОДЕРЖИМОЕ МАТЕРИАЛА (ИЗ БАЗЫ ЗНАНИЙ):
================================================================================

{markdown_content.strip()}
"""
    return payload

