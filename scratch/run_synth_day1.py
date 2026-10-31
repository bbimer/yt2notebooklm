import sys, os
from pathlib import Path

root = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy")
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))
os.chdir(str(root))

from research_academy.pipeline.synthesizer import CurriculumSynthesizer

synth = CurriculumSynthesizer(project_root=root)
res = synth.synthesize_day_1_pack()
for k, v in res.items():
    print(f"{k}: {v} (size={os.path.getsize(v)})")
