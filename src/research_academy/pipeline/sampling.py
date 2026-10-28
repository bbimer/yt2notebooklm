"""Multi-window transcript sampling with timestamp preservation and budget limits."""

from __future__ import annotations

import re
from typing import List, Tuple
from research_academy.models import ContentSegment, SourceContent, TranscriptSegment, VideoTranscript


def _segments_to_text(segments: List[TranscriptSegment]) -> Tuple[str, int]:
    """Formats segments as '[MM:SS] text' and returns formatted string and word count."""
    lines = []
    word_count = 0
    for s in segments:
        text = s.text.strip()
        if not text:
            continue
        line = f"[{s.timestamp_formatted}] {text}"
        lines.append(line)
        word_count += len(text.split())
    return "\n".join(lines), word_count


def sample_transcript_multi_window(
    transcript: VideoTranscript,
    max_words: int = 4000,
) -> str:
    """
    Samples transcript to fit within token budget while preserving chronological timestamps.

    If total words <= max_words: returns complete transcript with all timestamps.
    If total words > max_words: builds 3 balanced windows:
      - Window 1 (Intro/Theses): first ~25% of budget
      - Window 2 (Core/Mechanics): central ~50% of budget
      - Window 3 (Conclusion/Risks): final ~25% of budget
    """
    segments = transcript.segments

    # Fallback if no structured segments available
    if not segments:
        text = transcript.full_normalized_text or transcript.full_raw_text
        words = text.split()
        if len(words) <= max_words:
            return text
        chunk1 = " ".join(words[: int(max_words * 0.25)])
        mid = len(words) // 2
        half_mid = int(max_words * 0.50) // 2
        chunk2 = " ".join(words[max(0, mid - half_mid) : min(len(words), mid + half_mid)])
        chunk3 = " ".join(words[-int(max_words * 0.25) :])
        return (
            f"### [ОКНО 1: ВВЕДЕНИЕ]\n{chunk1}\n\n"
            f"### [ОКНО 2: ЦЕНТРАЛЬНАЯ МЕХАНИКА]\n{chunk2}\n\n"
            f"### [ОКНО 3: ВЫВОДЫ И ЗАКЛЮЧЕНИЕ]\n{chunk3}"
        )

    # If within budget, return full transcript with timestamps
    formatted_full, total_words = _segments_to_text(segments)
    if total_words <= max_words:
        return formatted_full

    budget_intro = int(max_words * 0.25)
    budget_core = int(max_words * 0.50)
    budget_concl = int(max_words * 0.25)

    # 1. Window 1: Start
    intro_segments: List[TranscriptSegment] = []
    w_count = 0
    for s in segments:
        words = len(s.text.split())
        if w_count + words > budget_intro and intro_segments:
            break
        intro_segments.append(s)
        w_count += words

    # 2. Window 3: End
    concl_segments: List[TranscriptSegment] = []
    w_count = 0
    for s in reversed(segments):
        words = len(s.text.split())
        if w_count + words > budget_concl and concl_segments:
            break
        concl_segments.insert(0, s)
        w_count += words

    # 3. Window 2: Core (around the middle)
    mid_idx = len(segments) // 2
    core_segments: List[TranscriptSegment] = []
    w_count = 0

    # Expand outward from center
    left = mid_idx
    right = mid_idx + 1
    while (left >= 0 or right < len(segments)) and w_count < budget_core:
        if left >= 0:
            s_left = segments[left]
            core_segments.insert(0, s_left)
            w_count += len(s_left.text.split())
            left -= 1
        if right < len(segments) and w_count < budget_core:
            s_right = segments[right]
            core_segments.append(s_right)
            w_count += len(s_right.text.split())
            right += 1

    # Format each window
    t_start1 = intro_segments[0].timestamp_formatted if intro_segments else "00:00"
    t_end1 = intro_segments[-1].timestamp_formatted if intro_segments else "00:00"
    txt1, _ = _segments_to_text(intro_segments)

    t_start2 = core_segments[0].timestamp_formatted if core_segments else "00:00"
    t_end2 = core_segments[-1].timestamp_formatted if core_segments else "00:00"
    txt2, _ = _segments_to_text(core_segments)

    t_start3 = concl_segments[0].timestamp_formatted if concl_segments else "00:00"
    t_end3 = concl_segments[-1].timestamp_formatted if concl_segments else "00:00"
    txt3, _ = _segments_to_text(concl_segments)

    return (
        f"### [ОКНО 1: ВВЕДЕНИЕ И ПОСТАНОВКА ПРОБЛЕМЫ · {t_start1} – {t_end1}]\n{txt1}\n\n"
        f"### [ОКНО 2: ЯДРО, МАТЕМАТИКА И МЕХАНИКА · {t_start2} – {t_end2}]\n{txt2}\n\n"
        f"### [ОКНО 3: ВЫВОДЫ, ЗАКЛЮЧЕНИЕ И ДИСКЛЕЙМЕРЫ · {t_start3} – {t_end3}]\n{txt3}"
    )


def sample_web_document_structural(
    source: SourceContent,
    max_words: int = 2000,
) -> str:
    """
    Structural Outline Sampling for Web Documents:
    1. Document Outline (all H1-H3 sections).
    2. Lead/Intro (SEC-01).
    3. Payload Core (2-3 segments from middle with tables, code, or high numbers density).
    4. Conclusion (last segment).
    Total size ~1.5k-2k words, giving Gatekeeper 100% clarity on depth vs fluff.
    """
    segments = source.segments
    if not segments:
        text = source.full_clean_text
        words = text.split()
        return " ".join(words[:max_words]) if len(words) > max_words else text

    total_words = source.word_count or sum(s.word_count for s in segments)
    if total_words <= max_words:
        lines = [f"[{s.anchor_id}]\n{s.text}" for s in segments]
        return "\n\n".join(lines)

    # 1. Outline
    outline_lines = [f"- {s.anchor_id}" for s in segments]
    outline_str = "### [ОГЛАВЛЕНИЕ ДОКУМЕНТА]\n" + "\n".join(outline_lines)

    # 2. Lead (SEC-01)
    lead_seg = segments[0]
    lead_str = f"### [ЛИД / АБСТРАКТ: {lead_seg.anchor_id}]\n{lead_seg.text}"

    # 3. Conclusions (Final segment)
    concl_seg = segments[-1]
    concl_str = f"### [ВЫВОДЫ И ЗАКЛЮЧЕНИЕ: {concl_seg.anchor_id}]\n{concl_seg.text}"

    # 4. Core Payload (2-3 middle segments with max data density)
    middle_candidates = segments[1:-1]
    core_selected = []
    if middle_candidates:
        def density_score(seg: ContentSegment) -> float:
            score = 0.0
            if seg.has_table:
                score += 10.0
            if seg.has_code:
                score += 8.0
            digits_count = len(re.findall(r"\d+", seg.text))
            math_count = len(re.findall(r"\$|\^|_|\{", seg.text))
            score += min(5.0, (digits_count + math_count) / 10.0)
            return score

        middle_sorted = sorted(middle_candidates, key=density_score, reverse=True)
        core_selected = sorted(middle_sorted[:3], key=lambda s: s.index)

    core_blocks = []
    for s in core_selected:
        core_blocks.append(f"### [ЯДРО ПЛОТНОСТИ ФАКТУРЫ: {s.anchor_id}]\n{s.text}")

    core_str = "\n\n".join(core_blocks)
    return f"{outline_str}\n\n{lead_str}\n\n{core_str}\n\n{concl_str}"


def sample_source_content(source: SourceContent, max_words: int = 2000) -> str:
    """Unified sampling entry point for any SourceContent (video or web)."""
    if source.source_type == "web":
        return sample_web_document_structural(source, max_words=max_words)
    lines = [f"[{s.anchor_id}] {s.text}" for s in source.segments]
    return "\n".join(lines)

