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


class HudSession:
    """Manages an interactive Raycast-style HUD session with live progress and completion."""

    def __init__(self, initial_progress: Optional[str] = "Обработка ссылки YouTube..."):
        self.proc = None
        hud_script = Path.home() / "Desktop" / "_customization" / "scripts" / "hud_notify.py"
        if hud_script.exists():
            try:
                import subprocess
                cmd = ["pythonw", str(hud_script), "--interactive"]
                if initial_progress:
                    cmd.extend(["--message", str(initial_progress)])
                self.proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000,  # CREATE_NO_WINDOW
                )
            except Exception as e:
                logger.debug("Failed to spawn interactive HUD: %s", e)

    def set_progress(self, msg: str) -> None:
        if self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(f"PROGRESS:{msg}\n".encode("utf-8"))
                self.proc.stdin.flush()
            except Exception:
                pass

    def set_done(self, msg: str) -> None:
        if self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(f"DONE:{msg}\n".encode("utf-8"))
                self.proc.stdin.flush()
                time.sleep(0.08)
            except Exception:
                pass

    def set_error(self, msg: str) -> None:
        if self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(f"ERROR:{msg}\n".encode("utf-8"))
                self.proc.stdin.flush()
                time.sleep(0.08)
            except Exception:
                pass

    def close(self) -> None:
        if self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(b"CLOSE\n")
                self.proc.stdin.flush()
            except Exception:
                pass


def trigger_hud(
    message: str = "Готово",
    hud_type: str = "done",
    duration_ms: int = 850,
    **kwargs,
) -> None:
    """Fast non-blocking single-shot HUD trigger."""
    try:
        import subprocess
        hud_script = Path.home() / "Desktop" / "_customization" / "scripts" / "hud_notify.py"
        if hud_script.exists():
            cmd = [
                "pythonw",
                str(hud_script),
                "--type", str(hud_type),
                "--message", str(message),
                "--duration", str(duration_ms),
            ]
            subprocess.Popen(cmd, creationflags=0x08000000)  # CREATE_NO_WINDOW
    except Exception as e:
        logger.debug("Failed to spawn HUD notification: %s", e)




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
        "title": "Глубокий конспект и ключевые инсайты (Executive Summary v2.0)",
        "prompt": (
            "Ты - ведущий аналитик и эксперт по структурированию информации.\n"
            "Твоя задача - изучить прикрепленный(е) материал(ы) (паспорт и транскрипт видео) и составить глубокий, плотный исполнительский конспект (Executive Summary).\n\n"
            "ПРИНЦИПЫ ТОЧНОСТИ:\n"
            "- Source Fidelity: опирайся строго на содержание первоисточника, не сглаживай технические нюансы.\n"
            "- Uncertainty Handling: если автор высказывает гипотезу или личное мнение, помечай это как мнение автора, а не как доказанный факт.\n"
            "- Traceability: привязывай ключевые тезисы и разделы к таймкодам или главам источника.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. КЛЮЧЕВАЯ СУТЬ (1-2 предложения): в чем главная идея, проблема и ценность материала?\n"
            "2. СТРУКТУРИРОВАННЫЙ РАЗБОР ПО ТЕМАМ (с таймкодами): разбей материал на смысловые блоки. Сохраняй причинно-следственные связи («А ведет к Б, потому что В») и конкретные технические детали, избегая чрезмерного сжатия до поверхностных тезисов.\n"
            "3. ИНСАЙТЫ, ЦИФРЫ И АРГУМЕНТАЦИЯ: точные метрики, бенчмарки, неочевидные выводы, правила и формулы автора с кратким контекстом их применения.\n"
            "4. ПРАКТИЧЕСКИЕ ВЫВОДЫ (Actionable Takeaways):\n"
            "   - [Рекомендации автора]: конкретные шаги, решения и советы, прямо озвученные спикером.\n"
            "   - [Выводы аналитика]: прикладные следствия и инструменты, логически вытекающие из разобранной фактуры.\n"
            "5. ФИЛЬТР ВОДЫ: полностью убери самопиар, приветствия, спонсорские интеграции и повторы, но строго сохрани всю глубину и контекст авторской аргументации."
        ),
    },
    "tutorial": {
        "title": "Практическое руководство / Пошаговый алгоритм (Actionable Tutorial v2.0)",
        "prompt": (
            "Ты - старший инженер и технический ментор.\n"
            "Твоя задача - извлечь из прикрепленного(ых) материала(ов) пошаговое прикладное руководство, проверив логическую полноту и совместимость каждого шага.\n\n"
            "ПРИНЦИПЫ ТОЧНОСТИ:\n"
            "- Source Fidelity: строго разделяй то, что автор показал на экране, и шаги, достроенные моделью для работоспособности.\n"
            "- Uncertainty Handling & Compatibility: для каждого достроенного шага проверяй синтаксическую корректность, совместимость версий библиотек, флагов и параметров окружения.\n"
            "- Traceability: привязывай этапы и ключевые действия к таймкодам видео.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. ЦЕЛЬ, СТЕК И ПРЕДРЕКВИЗИТЫ: что конкретно создается, минимальные требования к окружению, проверенные версии зависимостей и доступы.\n"
            "2. ПОШАГОВЫЙ АЛГОРИТМ: строгая хронологическая последовательность действий. Каждый шаг маркируй тегом:\n"
            "   - [В видео]: действие, команда или настройка прямо продемонстрированы автором в источнике.\n"
            "   - [Достроено ИИ]: связующий шаг или конфиг, пропущенный автором, но проверенный моделью на совместимость со стеком.\n"
            "3. КОМАНДЫ, КОД И КОНФИГУРАЦИИ: готовые блоки кода/конфигов с комментариями к флагам и переменным окружения.\n"
            "4. ПОДВОДНЫЕ КАМНИ И ОШИБКИ: критические точки отказа, скрытые баги версий и предупреждения автора.\n"
            "5. ЧЕК-ЛИСТ ГОТОВНОСТИ: краткий список критериев для проверки, что результат воспроизведен корректно."
        ),
    },
    "audit": {
        "title": "Критический аудит и проверка на инфоцыганство (Bullshit & Scam Filter v2.0)",
        "prompt": (
            "Ты - независимый фактчекер, скептик и технический аудитор.\n"
            "Твоя задача - провести объективный критический аудит прикрепленного(ых) материала(ов) на предмет достоверности, практической ценности и скрытого манипулирования.\n\n"
            "ПРИНЦИПЫ ТОЧНОСТИ:\n"
            "- Source Fidelity: цитируй и оценивай только то, что автор реально озвучил; не приписывай ему тезисов, которых нет в источнике.\n"
            "- Uncertainty Handling: отделяй проверяемые факты от субъективных оценок. Не делай обвинений без опоры на конкретные цитаты.\n"
            "- Traceability: указывай точные таймкоды для каждого разобранного заявления и обнаруженной уловки.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. ОЦЕНКА ПЛОТНОСТИ ПОЛЬЗЫ (от 1 до 10): объективное соотношение проверяемой технической фактуры к общему хронометражу и воде.\n"
            "2. КЛАССИФИКАЦИЯ ТЕЗИСОВ И ФАКТЧЕКИНГ:\n"
            "   - [Обосновано в материале / Подтверждено]: тезисы, строго подкрепленные данными, расчетами, кодом или проверяемыми первоисточниками из видео.\n"
            "   - [Не подтверждено / Субъективно]: личные мнения, гипотезы и прогнозы автора без проверяемой доказательной базы.\n"
            "   - [Опровергнуто / Ошибка]: утверждения, прямо противоречащие техническим фактам, спецификациям или задокументированным стандартам.\n"
            "3. СКРЫТЫЕ МОТИВЫ И АНАЛИЗ МАНИПУЛЯЦИЙ: беспристрастный разбор мотивов спикера (продвижение инфопродукта, рефералки, токена, кликбейт, нагнетание FOMO/FUD) со ссылкой на конкретные речевые конструкции без необоснованных ярлыков.\n"
            "4. ГРАНИЦЫ ПРИМЕНИМОСТИ И РИСКИ: для кого рекомендации автора опасны, где они гарантированно сломаются и о каких скрытых издержках/рисках спикер умолчал.\n"
            "5. СУХОЙ ОСТАТОК: объективно доказанные крупицы пользы (с таймкодами), которые действительно имеют прикладную ценность."
        ),
    },
    "compare": {
        "title": "Кросс-анализ и синтез нескольких видео (Multi-Source Comparison & Synthesis v2.0)",
        "prompt": (
            "Ты - ведущий аналитик и эксперт по комплексному синтезу информации.\n"
            "Перед тобой транскрипты нескольких видеороликов на одну тему (прикреплены файлами).\n"
            "Твоя задача - сопоставить позиции авторов, взвесить доказательную базу и сформировать объективный синтез.\n\n"
            "ПРИНЦИПЫ ТОЧНОСТИ:\n"
            "- Source Fidelity: не искажай аргументы отдельных спикеров ради создания искусственного компромисса.\n"
            "- Uncertainty Handling: отделяй общепринятый консенсус спикеров от объективно доказанной истины (если все авторы повторяют популярный миф - прямо укажи это).\n"
            "- Traceability: атрибутируй каждый тезис, расхождение и инсайт к конкретному автору/видео с указанием таймкодов.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "1. СВОДНАЯ СУТЬ И КОНСЕНСУС (ПРОВЕРКА ИСТИНОЙ): в чем все авторы сходятся между собой? Является ли это согласие объективным фактом или общим некритичным допущением?\n"
            "2. ОЦЕНКА ДОКАЗАТЕЛЬНОЙ БАЗЫ: сравни глубину каждого источника. Кто опирается на бенчмарки, код, цифры и документацию, а кто - на субъективный опыт и поверхностный пересказ?\n"
            "3. ТОЧКИ РАСХОЖДЕНИЯ И ПРОТИВОРЕЧИЯ (НЕРАЗРЕШЕННЫЕ КОНФЛИКТЫ): где позиции авторов кардинально расходятся? Не сглаживай углы: зафиксируй противоположные мнения и укажи причину расхождения (разные граничные условия, конфликт интересов, чья-то ошибка) либо прямо напиши [Причина не установлена], если данных в видео недостаточно.\n"
            "4. УНИКАЛЬНЫЕ ИНСАЙТЫ ПО КАЖДОМУ ИСТОЧНИКУ: ценные прикладные крупицы информации («мясо»), озвученные только автором А, автором B и т.д.\n"
            "5. ЕДИНАЯ РЕЗУЛЬТИРУЮЩАЯ СТРАТЕГИЯ: итоговая синтезированная модель/алгоритм, берущая лучшие верифицированные элементы из каждого видео без дублирования воды."
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
        hud_session: Optional[HudSession] = None,
    ) -> DigestResult:
        """Processes a single YouTube URL or ID into a clean markdown digest."""
        target_dir = output_dir or self.default_output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        video_id = extract_youtube_video_id(url_or_id)
        if not video_id:
            play_chime_error()
            if hud_session:
                hud_session.set_error("Некорректная ссылка на видео")
            else:
                trigger_hud(
                    message="Некорректная ссылка на видео",
                    hud_type="error",
                )
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

        if hud_session:
            hud_session.set_progress("Извлечение субтитров YouTube...")

        # 1. Fetch metadata and chapters
        details = self.fetch_video_details(video_id)

        # 2. Fetch transcript
        transcript = self.transcript_provider.get_transcript(video_id)
        if not transcript.has_subtitles:
            play_chime_error()
            if hud_session:
                hud_session.set_error("Субтитры недоступны для видео")
            else:
                trigger_hud(
                    message="Субтитры недоступны для видео",
                    hud_type="error",
                )
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

        if hud_session:
            hud_session.set_progress("Формирование дайджеста...")

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
                done_msg = "Аудит скопирован в буфер" if mode == "audit" else "Саммари скопировано в буфер"
                if hud_session:
                    hud_session.set_done(done_msg)
                else:
                    trigger_hud(
                        message=done_msg,
                        hud_type="done",
                    )
            except Exception as e:
                logger.warning("Failed to copy payload to clipboard: %s", e)
                if hud_session:
                    hud_session.set_error("Ошибка копирования в буфер")
        else:
            if hud_session:
                hud_session.set_done("Дайджест сохранен")
            else:
                trigger_hud(
                    message="Дайджест сохранен",
                    hud_type="done",
                )

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

