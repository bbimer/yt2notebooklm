"""Full curriculum pipeline for Days 1-7 (Modules 00 to 06).
Option A: Complete Fresh Harvest & Analysis with Hardcore Institutional Matrix.

Orchestrates:
1. Matrix harvesting (discovery, duration checks, subtitle validation) across all 7 days
2. Pass A (Gatekeeper) with deepseek-v4.1-flash & programmatic scoring
3. Pass B (Methodist) with >= 6.5 threshold & 4-layer social engineering format
4. Discrete NotebookLM pack incremental re-export (Day_1 to Day_7)
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))
load_dotenv(project_root / ".env")

from research_academy.config import get_config
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, GatekeeperVerdict
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.pipeline.matrix_harvester import MatrixHarvester
from research_academy.pipeline.publishing import Publisher
from research_academy.queries_config import SEARCH_MATRIX

ALL_MODULES = [
    "00_crypto_fundamentals",       # Day 1: Хищная токеномика, VC-дампы и механика стейблкоинов
    "01_market_structure",           # Day 2: Анатомия маркет-мейкеров, охота за стопами и токсичный поток
    "02_arbitrage_and_derivatives",  # Day 3: Деривативы, базис-трейдинг и почему ручной арбитраж мертв
    "03_orderbook_mechanics",        # Day 4: Манипуляции стаканом, спуфинг, айсберги и фейковые объемы
    "04_onchain_logistics",          # Day 5: Темный лес ончейна, MEV-боты, сэндвич-атаки и инфраструктура
    "05_risk_and_hedging",           # Day 6: Анатомия краха бирж, ловушки выводов, Leg Risk и AML
    "06_quant_stack_and_mindset",    # Day 7: Квант-стек, алгоритмическое преимущество и смерть теханализа
]

config = get_config(project_root)
db = Database(config.database_path)
harvester = MatrixHarvester(config=config, db=db)
pipeline = AnalysisPipeline(config=config, db=db)
publisher = Publisher(db, config.project_root)

start_time = datetime.now()
print(f"======================================================================", flush=True)
print(f"🚀 NULLSPREAD RESEARCH & SALES ACADEMY: FULL 7-DAY HARVEST & CURRICULUM", flush=True)
print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
print(f"Target Modules: {len(ALL_MODULES)} (Days 1 to 7)", flush=True)
print(f"LLM Provider: {config.llm_provider} (Model: {config.openrouter_model})", flush=True)
print(f"Quality Bar: Pass B threshold >= 6.5 / 10", flush=True)
print(f"Architecture: 4 Layers (Market Reality -> Evidence -> Sales Psych -> Applied)", flush=True)
print(f"======================================================================\n", flush=True)

total_published_all = 0
total_rejected_all = 0

for mod_idx, mod_id in enumerate(ALL_MODULES, 1):
    mod_info = SEARCH_MATRIX.get(mod_id, {})
    mod_title = mod_info.get("title", mod_id)
    day_start = datetime.now()
    print(f"\n{'='*75}", flush=True)
    print(f"📅 DAY {mod_idx}/7: {mod_title} [{mod_id}]", flush=True)
    print(f"{'='*75}", flush=True)

    # 1. Harvest Phase
    print(f"\n[PHASE 1] Harvesting YouTube candidates with subtitles for {mod_id}...", flush=True)
    try:
        harvested = harvester.harvest_module(mod_id)
        print(f"-> Harvested {len(harvested)} videos with transcripts for {mod_id}.", flush=True)
    except Exception as e:
        print(f"-> Harvesting error for {mod_id}: {e}", flush=True)

    # 2. Analysis Phase (Two-Pass LLM)
    pending_videos = [
        v for v in db.list_videos(limit=300)
        if v.topic_id == mod_id and v.discovery_status == DiscoveryStatus.TRANSCRIPT_FETCHED
    ]
    print(f"\n[PHASE 2] Two-Pass LLM Analysis on {len(pending_videos)} videos in {mod_id}...", flush=True)

    published_count = 0
    rejected_count = 0

    for i, video in enumerate(pending_videos, 1):
        transcript = db.get_transcript(video.video_id)
        if not transcript:
            print(f"[{i}/{len(pending_videos)}] No transcript for {video.video_id}, skipping.", flush=True)
            continue

        print(f"\n--- [{i}/{len(pending_videos)}] Analyzing: {video.title[:65]} ---", flush=True)
        print(f"    ID: {video.video_id} | Lang: {video.language} | Duration: {video.duration_seconds}s", flush=True)

        try:
            gatekeeper, methodist = pipeline.run_two_pass_analysis(video, transcript)
            score = gatekeeper.composite_score if gatekeeper else 0.0
            verdict = gatekeeper.decision.value if gatekeeper else "UNKNOWN"
            print(f"    -> Pass A (Gatekeeper): Score = {score}/10, Verdict = {verdict}", flush=True)

            if methodist:
                pub_path = publisher.publish_video_analysis(
                    video, methodist, transcript, score
                )
                db.update_video_status(video.video_id, DiscoveryStatus.PUBLISHED, f"Published to {pub_path.name}")
                print(f"    -> Pass B (Methodist) OK! Concepts: {len(methodist.key_concepts)}, Claims: {len(methodist.key_claims)}", flush=True)
                print(f"    -> PUBLISHED: {pub_path.name} ({pub_path.stat().st_size // 1024} KB)", flush=True)
                published_count += 1
            else:
                db.update_video_status(
                    video.video_id,
                    DiscoveryStatus.GATEKEEPER_REJECTED,
                    f"Rejected by Gatekeeper: {verdict} (Score {score} < 6.5)"
                )
                print(f"    -> SKIPPED Pass B (Score {score} < 6.5 or Rejected)", flush=True)
                rejected_count += 1
        except Exception as e:
            print(f"    -> ERROR analyzing {video.video_id}: {e}", flush=True)

        # Rate-limiting delay
        time.sleep(1.0)

    total_published_all += published_count
    total_rejected_all += rejected_count

    elapsed_day = (datetime.now() - day_start).total_seconds()
    print(f"\n[SUMMARY DAY {mod_idx}] Published: {published_count} | Filtered Out: {rejected_count} (Took {elapsed_day:.1f}s)", flush=True)

    # 3. Intermediate Pack Re-export
    pack_dir = publisher.export_notebooklm_pack()
    print(f"[NOTEBOOKLM PACK UPDATED] -> {pack_dir}", flush=True)

total_elapsed = (datetime.now() - start_time).total_seconds()
print(f"\n{'='*75}", flush=True)
print(f"🎉 ALL 7 DAYS COMPLETED SUCCESSFULLY!", flush=True)
print(f"Total Published: {total_published_all} verified guides", flush=True)
print(f"Total Filtered Out: {total_rejected_all} low-signal candidates", flush=True)
print(f"Total Pipeline Runtime: {total_elapsed / 60:.1f} minutes", flush=True)
print(f"Final NotebookLM pack ready in: exports/notebooklm_pack/", flush=True)
print(f"{'='*75}\n", flush=True)

