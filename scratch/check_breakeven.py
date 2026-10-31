import sys
from pathlib import Path
repo_dir = Path("nullspread-research-academy").resolve()
sys.path.insert(0, str(repo_dir))

from src.research_academy.pipeline.playbook_renderer import PlaybookRenderer

p = repo_dir / "src" / "research_academy" / "pipeline" / "playbook_content.py"
text = p.read_text(encoding="utf-8")
processed = PlaybookRenderer.preprocess_markdown(text)

idx = processed.find("breakeven")
print(repr(processed[idx-60:idx+160]))

