import sys
import re
from pathlib import Path
repo_dir = Path("nullspread-research-academy").resolve()
sys.path.insert(0, str(repo_dir))

from src.research_academy.pipeline.playbook_renderer import PlaybookRenderer

p = repo_dir / "src" / "research_academy" / "pipeline" / "playbook_content.py"
text = p.read_text(encoding="utf-8")
processed = PlaybookRenderer.preprocess_markdown(text)

opens = [m.start() for m in re.finditer(r"\\\[", processed)]
closes = [m.start() for m in re.finditer(r"\\\]", processed)]

print(f"\\[ count: {len(opens)}, \\] count: {len(closes)}")
for i, (op, cl) in enumerate(zip(opens, closes), 1):
    print(f"Block {i} (len {cl-op}):\n{repr(processed[op:min(op+80, cl+2)])}")
