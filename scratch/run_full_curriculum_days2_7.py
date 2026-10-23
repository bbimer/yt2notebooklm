"""Full curriculum pipeline for Days 2-7 (Modules 01 to 06).
Orchestrates:
1. Matrix harvesting (discovery, duration checks, subtitle validation)
2. Pass A (Gatekeeper) with deepseek-v4.1-flash & programmatic scoring
3. Pass B (Methodist) with >= 6.5 threshold & landing block anchors
4. Discrete NotebookLM pack re-export (Day_2 to Day_7)
"""

import sys
import time
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

TARGET_MODULES = [
    "01_market_structure",
    "02_arbitrage_and_derivatives",
    "03_orderbook_mechanics",
    "04_onchain_logistics",
    "05_risk_and_hedging",
    "06_quant_stack_and_mindset",
]

config = get_config()
db = Database(config.database_path)
harvester = MatrixHarvester(config=config, db=db)
pipeline = AnalysisPipeline(config=config, db=db)
publisher = Publisher(db, config.project_root)

print(f"=== NULLSPREAD RESEARCH ACADEMY: DAYS 2-7 PIPELINE ===", flush=True)
print(f"Target Modules: {len(TARGET_MODULES)}", flush=True)
print(f"LLM Provider: {config.llm_provider} (Model: {config.openrouter_model})", flush=True)
print(f"Quality Bar: Pass B threshold >= 6.5 / 10\n", flush=True)

for mod_idx, mod_id in enumerate(TARGET_MODULES, 2):
    mod_info = SEARCH_MATRIX.get(mod_id, {})
    mod_title = mod_info.get("title", mod_id)
    print(f"\n{'='*70}", flush=True)
    print(f"DAY {mod_idx}: {mod_title} [{mod_id}]", flush=True)
    print(f"{'='*70}", flush=True)

    # 1. Harvest Phase
    print(f"\n[PHASE 1] Harvesting YouTube candidates with subtitles...", flush=True)
    try:
        harvested = harvester.harvest_module(mod_id)
        print(f"-> Harvested {len(harvested)} videos with transcripts for {mod_id}.", flush=True)
    except Exception as e:
        print(f"-> Harvesting error for {mod_id}: {e}", flush=True)

    # 2. Analysis Phase (Two-Pass LLM)
    pending_videos = [
        v for v in db.list_videos(limit=200)
        if v.topic_id == mod_id and v.discovery_status == DiscoveryStatus.TRANSCRIPT_FETCHED
    ]
    print(f"\n[PHASE 2] Two-Pass LLM Analysis on {len(pending_videos)} videos...", flush=True)

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
                print(f"    -> SKIPPED Pass B (Score {score} < 6.5 or Rejected)", flush=True)
                rejected_count += 1
        except Exception as e:
            print(f"    -> ERROR analyzing {video.video_id}: {e}", flush=True)

        # Brief delay to respect rate limits
        time.sleep(1.0)

    print(f"\n[SUMMARY DAY {mod_idx}] Published: {published_count} | Filtered Out: {rejected_count}", flush=True)

    # 3. Intermediate Pack Re-export
    pack_dir = publisher.export_notebooklm_pack()
    print(f"[NOTEBOOKLM PACK UPDATED] -> {pack_dir}", flush=True)

print(f"\n{'='*70}", flush=True)
print(f"🎉 ALL MODULES (DAYS 2-7) COMPLETE! Full NotebookLM pack ready.", flush=True)
print(f"{'='*70}\n", flush=True)
