"""Transcript Sniffer & Prompt Builder for Semi-Manual LLM Evaluation.

Inspired by NullSpread Telegram Clipboard Intelligence, adapted for YouTube transcripts.
Pulls subtitles, calculates technical density vs scam flags, builds a specialized
5-point evaluation prompt, and copies it to clipboard with a chime!
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pyperclip

from research_academy.models import VideoMetadata, VideoTranscript
from research_academy.pipeline.normalization import normalize_caption_text
from research_academy.providers.transcripts import YouTubeApiTranscriptProvider

# Windows audio feedback
try:
    import winsound
except ImportError:
    winsound = None

# Technical quant & trader patterns (Positive signals)
TRADER_TECHNICAL_PATTERNS = [
    (re.compile(r"\b(?:стакан\w*|ордербук\w*|order\s*book)\b", re.IGNORECASE), "стакан ордеров"),
    (re.compile(r"\b(?:проскальзывани\w*|slippage)\b", re.IGNORECASE), "проскальзывание (slippage)"),
    (re.compile(r"\b(?:сведени\w*\s+ордер\w*|matching\s+engine)\b", re.IGNORECASE), "сведение ордеров"),
    (re.compile(r"\b(?:maker|taker|мейкер|тейкер)\b", re.IGNORECASE), "maker/taker комиссии"),
    (re.compile(r"\b(?:funding\s*rate|ставк\w*\s+финансирования|фандинг\w*)\b", re.IGNORECASE), "фандинг"),
    (re.compile(r"\b(?:дельта[\s-]нейтральн\w*|delta[\s-]neutral)\b", re.IGNORECASE), "дельта-нейтральность"),
    (re.compile(r"\b(?:спот[\s-]перп|spot[\s-]perp|cash[\s-]and[\s-]carry)\b", re.IGNORECASE), "спот-перп базис"),
    (re.compile(r"\b(?:ликвидност\w*|пул\w*\s+ликвидности|liquidity\s+pool)\b", re.IGNORECASE), "ликвидность / AMM"),
    (re.compile(r"\b(?:маркет[\s-]?мейкер\w*|market[\s-]?maker|зима|wintermute)\b", re.IGNORECASE), "маркет-мейкинг"),
    (re.compile(r"\b(?:лимитн\w*\s+ордер\w*|limit\s*order)\b", re.IGNORECASE), "лимитные ордера"),
    (re.compile(r"\b(?:глубин\w*\s+рынка|market\s+depth)\b", re.IGNORECASE), "глубина рынка (depth)"),
    (re.compile(r"\b(?:ликвидац\w*|liquidation|шорт[\s-]сквиз)\b", re.IGNORECASE), "ликвидации/сквиз"),
    (re.compile(r"\b(?:hft|арбитраж\w*\s+задержк\w*|latency)\b", re.IGNORECASE), "latency/HFT"),
    (re.compile(r"\b(?:китайск\w*\s+преми\w*|кимчхи|kimchi\s+premium)\b", re.IGNORECASE), "Kimchi Premium"),
    (re.compile(r"\b(?:финальност\w*|finality|подтверждени\w*\s+сети)\b", re.IGNORECASE), "финальность/конфирмы"),
]

# Infocigan & scam patterns (Red flags)
SCAM_COMMERCIAL_PATTERNS = [
    (re.compile(r"\b(?:связка\s+дня|бесплатная\s+связка|рабочая\s+связка)\b", re.IGNORECASE), "«связка» (инфоцыганство)"),
    (re.compile(r"\b(?:100%\s+прибыль|гарантированн\w*\s+доход|без\s+риск\w*)\b", re.IGNORECASE), "гарантии прибыли / безрисковость"),
    (re.compile(r"\b(?:пассивный\s+доход\s+на\s+автомате|кнопка\s+бабло)\b", re.IGNORECASE), "пассивный доход на автомате"),
    (re.compile(r"\b(?:сигнал\w*\s+в\s+тг|сигнал\w*\s+в\s+телеграм|t\.me\/)\b", re.IGNORECASE), "продажа сигналов в Telegram"),
    (re.compile(r"\b(?:реферальн\w*\s+ссылк\w*|рефк\w*|бонус\s+при\s+регистрации)\b", re.IGNORECASE), "реферальные ссылки"),
    (re.compile(r"\b(?:раскрутк\w*\s+счет\w*|доверительн\w*\s+управлени\w*)\b", re.IGNORECASE), "раскрутка депозита"),
    (re.compile(r"\b(?:1000x|100x|иксы|ракета|туземун)\b", re.IGNORECASE), "хайп / иксы (1000x)"),
    (re.compile(r"\b(?:заработок\s+для\s+новичка\s+с\s+нуля)\b", re.IGNORECASE), "«с нуля для новичка»"),
]


def play_chime_success():
    """Audio cue when prompt is copied to clipboard."""
    if winsound:
        try:
            winsound.Beep(880, 100)
            winsound.Beep(1320, 180)
        except Exception:
            pass


def play_chime_error():
    if winsound:
        try:
            winsound.Beep(440, 250)
        except Exception:
            pass


def extract_youtube_video_id(url_or_id: str) -> Optional[str]:
    """Extracts 11-char YouTube video ID from various link formats."""
    text = url_or_id.strip()
    if re.match(r"^[a-zA-Z0-9_-]{11}$", text):
        return text

    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|embed\/|\/watch\?v=|\&v=)([a-zA-Z0-9_-]{11})",
        r"(?:shorts\/)([a-zA-Z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def calculate_transcript_telemetry(transcript: VideoTranscript) -> Dict[str, Any]:
    text = transcript.full_normalized_text

    trader_hits: List[str] = []
    for pat, label in TRADER_TECHNICAL_PATTERNS:
        if pat.search(text) and label not in trader_hits:
            trader_hits.append(label)

    scam_hits: List[str] = []
    for pat, label in SCAM_COMMERCIAL_PATTERNS:
        if pat.search(text) and label not in scam_hits:
            scam_hits.append(label)

    # Estimate reading time & word count
    words = text.split()
    total_words = len(words)
    est_duration_minutes = round(total_words / 140, 1)  # average speaking rate ~140 wpm

    # Density metric: technical markers per 1000 words
    density = round((len(trader_hits) / max(1, total_words)) * 1000, 2)

    return {
        "word_count": total_words,
        "est_duration_minutes": est_duration_minutes,
        "trader_markers": trader_hits,
        "scam_markers": scam_hits,
        "technical_density": density,
    }


def build_semi_manual_audit_prompt(
    video_title: str,
    video_url: str,
    channel_title: str,
    transcript: VideoTranscript,
    telemetry: Dict[str, Any],
    audit_counter: int = 1,
    transcript_filename: Optional[str] = None,
) -> str:
    """
    Constructs the 5-point evaluation prompt for ChatGPT, Claude, DeepSeek, or Gemini.
    Specifically designed to filter out garbage and extract genuine market mechanics.
    """
    now_ts = datetime.now().strftime("%H:%M:%S")

    trader_markers_str = ", ".join(telemetry["trader_markers"]) if telemetry["trader_markers"] else "Явных технических маркеров не обнаружено"
    scam_markers_str = f"⚠️ ОБНАРУЖЕНЫ: {', '.join(telemetry['scam_markers'])}" if telemetry["scam_markers"] else "🟢 Чисто (маркеров инфоцыганства не найдено)"

    if transcript_filename:
        # File attachment mode (lightweight, zero browser DOM lag)
        subtitles_section = f"""## 3. СУБТИТРЫ ВИДЕО:
Субтитры прикреплены отдельным файлом: `{transcript_filename}`
Изучи полный текст из прикрепленного файла перед выставлением оценок и формированием вердикта."""
        file_passport_line = f"- **Файл транскрипта:** `{transcript_filename}` (прикреплен к этому запросу)\n"
    else:
        # Inline fallback mode
        text = transcript.full_normalized_text
        words = text.split()
        if len(words) > 3500:
            chunk_start = " ".join(words[:1200])
            mid_idx = len(words) // 2
            chunk_mid = " ".join(words[mid_idx - 600 : mid_idx + 600])
            chunk_end = " ".join(words[-1000:])
            transcript_sample = (
                f"[ФРАГМЕНТ 1: НАЧАЛО]\n{chunk_start}\n\n"
                f"[...]\n\n"
                f"[ФРАГМЕНТ 2: СЕРЕДИНА]\n{chunk_mid}\n\n"
                f"[...]\n\n"
                f"[ФРАГМЕНТ 3: ЗАКЛЮЧЕНИЕ И ВЫВОДЫ]\n{chunk_end}"
            )
        else:
            transcript_sample = text
        subtitles_section = f"""## 3. ВЫБОРКА СУБТИТРОВ ВИДЕО:\n\"\"\"\n{transcript_sample}\n\"\"\""""
        file_passport_line = ""

    prompt = f"""# 🎬 [AUDIT #{audit_counter} · {now_ts}] ОБЪЕКТИВНЫЙ ТЕХНИЧЕСКИЙ АУДИТ ВИДЕО-МАТЕРИАЛА

## 1. ПАСПОРТ ВИДЕО:
- **Номер аудита:** #{audit_counter}
- **Название:** {video_title}
- **Канал:** {channel_title}
- **Ссылка:** {video_url}
- **Объем субтитров:** {telemetry['word_count']} слов (~{telemetry['est_duration_minutes']} мин речи)
- **Язык субтитров:** {transcript.language}
{file_passport_line}
### ПРЕДВАРИТЕЛЬНАЯ АЛГОРИТМИЧЕСКАЯ ТЕЛЕМЕТРИЯ:
- **Технические маркеры практиков:** {trader_markers_str}
- **Флаги коммерческого шума/скама:** {scam_markers_str}
- **Плотность терминологии:** {telemetry['technical_density']} маркеров / 1000 слов

---

## 2. ТВОЯ РОЛЬ И ПРИНЦИПЫ:
Ты — беспристрастный Forensic Quant-Аудитор. Твоя задача — провести доказательную (evidence-based) экспертизу видеоматериала.

ПРАВИЛА БЕСПРИСТРАСТНОГО АУДИТА:
1. **СТРОГИЙ ЗАПРЕТ НА ЭМОЦИОНАЛЬНЫЙ СНОБИЗМ.** Запрещены слова-паразиты вроде «эзотерика», «катастрофические издержки», «полный бред». Каждая претензия обязана опираться на конкретный таймкод и цитату.
2. **ОТСУТСТВИЕ БЭКТЕСТОВ/СТАТИСТИКИ** трактуй как «эффективность не подтверждена представленными данными», а не как «доказанную убыточность».
3. **НАЛИЧИЕ ССЫЛКИ НА TELEGRAM/БИРЖУ** оценивай беспристрастно: вытесняет ли реклама суть? Даются ли обещания нереалистичной доходности, либо это авторский дневник?
4. **РАЗДЕЛЯЙ КАТЕГОРИИ МАТЕРИАЛА:** Если ролик слаб для модуля квантовой микроструктуры, определи, ценен ли он как «Словарь ментальности розничного клиента (SMC/ICT/уровни)» для подготовки сейлз-команды к реальным звонкам.

---

{subtitles_section}

---

## 4. СТРУКТУРА ОТВЕТА (ОТВЕТЬ СТРОГО ПО ЭТОМУ ШАБЛОНУ):

### 📊 ЭТАП 1 — ОЦЕНКА ПО КРИТЕРИЯМ (Шкала 1.0 – 5.0)

1. **Техническая глубина и соответствие биржевой микроструктуре (1–5):**
   - *Критерий:* Книга заявок (CLOB), Matching Engine, очереди ордеров, спреды, задержки, модели маркет-мейкинга против субъективных графических концепций.
   - *Если автор подменяет понятия (например, FVG вместо slippage):* Обязательно приведи таймкод и цитату.
   - **Оценка:** [X / 5.0] — *обоснование с таймкодом [MM:SS]*

2. **Обоснованность утверждений и учет издержек (1–5):**
   - *Критерий:* Учтены ли комиссии мейкер/тейкер, влияние спреда на матожидание и риски исполнения на мелких таймфреймах? Приведена ли статистика или единичные подобранные примеры?
   - **Оценка:** [X / 5.0] — *обоснование*

3. **Характер коммерческого шума (1–5):**
   - *5.0:* Чистый образовательный контент без ссылок и прогревов.
   - *3.0:* Есть ссылки на личный канал/биржу, но контент самодостаточен и не обещает «кнопку бабло».
   - *1.0:* Агрессивный кликбейт, обещания превзойти 99% трейдеров, воронка в приватные сигналы.
   - **Оценка:** [X / 5.0] — *обоснование*

4. **Интеллектуальная плотность и воспроизводимость (1–5):**
   - *Критерий:* Отношение проверяемых фактов к хронометражу без риторических преувеличений.
   - **Оценка:** [X / 5.0] — *обоснование*

---

### ⚖️ ЭТАП 2 — ИТОГОВЫЙ ВЕРДИКТ

- **ИТОГОВЫЙ БАЛЛ:** [Среднее 1.0 - 5.0]
- **СТАТУС:** 
  • 🟢 **ACCEPTED_CORE (Принять в основной модуль)** — балл >= 4.0, шум <= 2.5, подтвержденные расчеты и строгая микроструктура.
  • 🟡 **REFERENCE_RETAIL_PSYCHOLOGY (Взять как профиль ритейл-клиента)** — для квантового модуля слабо, но ценно как карта розничного сленга и возражений для сейлз-команды.
  • ⚪ **REVIEW_UNVERIFIED (Требует проверки / взять фрагменты)** — балл 3.0 - 3.9, есть дельные гипотезы без строгой доказательной базы.
  • 🔴 **REJECT_FOR_MODULE (Отклонить для модуля)** — балл < 3.0, грубая подмена понятий или реклама скама.
- **Главный аргумент вердикта (без эмоциональных эпитетов):** (2-3 емких предложения на основе фактов).
- **Смягчающие факторы / Что полезного сказал автор (Counter-evidence):** (1-2 объективных пункта).

---

### 🌉 ЭТАП 3 — МОСТ ДЛЯ СЕЙЛЗ-КОМАНДЫ (SALES TRANSLATION BRIDGE)
*(Заполняется для всех статусов, включая REJECT, если видео затрагивает рыночные термины)*

1. **С какими понятиями/заблуждениями придет клиент после этого видео?**
   *(Что клиент будет называть «ликвидностью», «проскальзыванием» или «ордер-блоком»)*
2. **Как эта механика РЕАЛЬНО работает на уровне биржевого стакана и арбитража?**
   *(Перевод на язык реального Matching Engine, каскада стоп-маркет ордеров, спреда и задержек)*
3. **Образцовый профессиональный ответ менеджера клиенту:**
   *(Без снобизма и без насмешек над розничным трейдером, уважительно раскрывая технологические преимущества платформы)*
"""
    return prompt.strip()


class TranscriptSniffer:
    def __init__(
        self,
        transcript_provider: Optional[YouTubeApiTranscriptProvider] = None,
        output_dir: Optional[Path] = None,
    ):
        self.provider = transcript_provider or YouTubeApiTranscriptProvider()
        self.output_dir = Path(output_dir or (Path.cwd() / "transcripts_sniffer"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        existing = list(self.output_dir.glob("audit_*.txt"))
        self.counter = len(existing) + 1

    def inspect_and_build_prompt(
        self,
        url_or_id: str,
        title: Optional[str] = None,
        channel: Optional[str] = None,
        copy_to_clipboard: bool = True,
        save_file: bool = True,
    ) -> Tuple[bool, str]:
        """
        Fetches transcript, saves to clean dedicated file, builds compact lightweight prompt,
        copies to clipboard, and plays chime.
        """
        video_id = extract_youtube_video_id(url_or_id)
        if not video_id:
            return False, f"Не удалось распознать YouTube Video ID из ссылки: {url_or_id}"

        current_counter = self.counter
        print(f"\n🔍 [Sniffer #{current_counter}] Получаю субтитры для видео {video_id}...")
        transcript = self.provider.get_transcript(video_id)

        if not transcript.has_subtitles:
            play_chime_error()
            return False, f"Субтитры недоступны для видео {video_id}: {transcript.error_message}"

        telemetry = calculate_transcript_telemetry(transcript)
        v_title = title or f"YouTube Video ({video_id})"
        v_channel = channel or "YouTube Creator"
        v_url = f"https://www.youtube.com/watch?v={video_id}"

        filename = f"audit_{current_counter:03d}_{video_id}.txt"
        filepath = self.output_dir / filename

        if save_file:
            # Build full structured file with timestamps
            if transcript.segments:
                body_lines = [
                    f"[{s.timestamp_formatted}] {s.text}"
                    for s in transcript.segments
                    if s.text.strip()
                ]
                formatted_body = "\n".join(body_lines)
            else:
                formatted_body = transcript.full_normalized_text or transcript.full_raw_text

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_content = (
                f"================================================================================\n"
                f"NULLSPREAD RESEARCH · СУБТИТРЫ ВИДЕО ДЛЯ АУДИТА #{current_counter}\n"
                f"================================================================================\n"
                f"ID видео: {video_id}\n"
                f"Название: {v_title}\n"
                f"Канал: {v_channel}\n"
                f"Ссылка: {v_url}\n"
                f"Объем: {telemetry['word_count']} слов (~{telemetry['est_duration_minutes']} мин)\n"
                f"Язык: {transcript.language}\n"
                f"Файл: {filename}\n"
                f"Создан: {now_str}\n"
                f"================================================================================\n\n"
                f"{formatted_body}\n"
            )
            filepath.write_text(file_content, encoding="utf-8")

        prompt = build_semi_manual_audit_prompt(
            video_title=v_title,
            video_url=v_url,
            channel_title=v_channel,
            transcript=transcript,
            telemetry=telemetry,
            audit_counter=current_counter,
            transcript_filename=filename if save_file else None,
        )

        self.counter += 1

        if copy_to_clipboard:
            try:
                pyperclip.copy(prompt)
                play_chime_success()
                print("=" * 72)
                print(f"🎉 [ВСТАВКА #{current_counter}] ПРОМПТ СКОПИРОВАН В БУФЕР ОБМЕНА!")
                print(f"📄 Файл с субтитрами сохранен:")
                print(f"   👉 {filepath.resolve()}")
                print(f"📊 Слов: {telemetry['word_count']} (~{telemetry['est_duration_minutes']} мин речи) | Тех. маркеры: {len(telemetry['trader_markers'])} | Шум: {len(telemetry['scam_markers'])}")
                print("=" * 72)
                print(f"👉 В ChatGPT / Claude / DeepSeek:")
                print(f"   1. Прикрепи сохраненный файл '{filename}' (или перетащи в чат)")
                print(f"   2. Нажми Ctrl + V (браузер НЕ зависнет, размер промпта всего ~1.5 КБ) и отправь!\n")
            except Exception as e:
                print(f"[WARN] Не удалось скопировать в буфер обмена: {e}")

        return True, prompt

