import time
from research_academy.config import get_config
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, GatekeeperVerdict
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.pipeline.publishing import Publisher

config = get_config()
db = Database(config.database_path)
pipeline = AnalysisPipeline(config, db)
publisher = Publisher(db, config.project_root)

videos = [
    v for v in db.list_videos(limit=100)
    if v.topic_id == "00_crypto_fundamentals" and v.discovery_status == DiscoveryStatus.TRANSCRIPT_FETCHED
]

print(f"Found {len(videos)} videos ready for analysis in 00_crypto_fundamentals.")

for i, video in enumerate(videos, 1):
    transcript = db.get_transcript(video.video_id)
    if not transcript:
        print(f"[{i}/{len(videos)}] No transcript for {video.video_id}, skipping.")
        continue

    print(f"\n[{i}/{len(videos)}] Processing: {video.title[:60]} ({video.video_id}) | Lang: {video.language}")
    try:
        gatekeeper, methodist = pipeline.run_two_pass_analysis(video, transcript)
        print(f"-> Gatekeeper Score: {gatekeeper.composite_score}, Verdict: {gatekeeper.decision.value}")
        if methodist:
            print(f"-> Methodist Pass OK! Key concepts: {len(methodist.key_concepts)}, Claims: {len(methodist.key_claims)}")
            pub_path = publisher.publish_video_analysis(
                video, methodist, transcript, gatekeeper.composite_score
            )
            db.update_video_status(video.video_id, DiscoveryStatus.PUBLISHED, f"Published to {pub_path.name}")
            print(f"-> Published: {pub_path.name}")
        else:
            db.update_video_status(video.video_id, DiscoveryStatus.GATEKEEPER_REJECTED, f"Rejected: {gatekeeper.decision.value}")
            print(f"-> Video not accepted for core curriculum.")
    except Exception as e:
        print(f"-> Error processing {video.video_id}: {e}")

    # Brief delay between LLM calls
    time.sleep(1)

# Re-export the 9-source NotebookLM pack
pack_path = publisher.export_notebooklm_pack()
print(f"\n[DONE] NotebookLM pack re-exported to: {pack_path}")

