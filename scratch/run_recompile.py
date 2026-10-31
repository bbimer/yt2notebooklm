import sys
from pathlib import Path
repo_dir = Path("nullspread-research-academy").resolve()
sys.path.insert(0, str(repo_dir))

from src.research_academy.pipeline.synthesizer import CurriculumSynthesizer
import fitz  # PyMuPDF

print("Initializing CurriculumSynthesizer...")
synthesizer = CurriculumSynthesizer(project_root=repo_dir)

print("\n--- 1. Synthesizing Fast-Track Closer Pack ---")
closer_artifacts = synthesizer.synthesize_fast_track_closer_pack()
for k, v in closer_artifacts.items():
    print(f"  {k}: {v}")
closer_doc = fitz.open(closer_artifacts["closer_playbook_pdf"])
print(f"Fast_Track_Closer_Playbook.pdf page count: {len(closer_doc)}")

print("\n--- 2. Synthesizing Day 1 Institutional Pack ---")
day1_artifacts = synthesizer.synthesize_day_1_pack()
for k, v in day1_artifacts.items():
    print(f"  {k}: {v}")
day1_doc = fitz.open(day1_artifacts["sales_playbook_pdf"])
print(f"Day_1_Sales_Playbook.pdf page count: {len(day1_doc)}")
bc_doc = fitz.open(day1_artifacts["battlecard_pdf"])
print(f"Day_1_Battlecard.pdf page count: {len(bc_doc)}")