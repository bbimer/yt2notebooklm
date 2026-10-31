from pathlib import Path
repo_dir = Path("nullspread-research-academy").resolve()
import fitz

closer_pdf = repo_dir / "exports" / "notebooklm_pack" / "Fast_Track_Closer_Playbook.pdf"
day1_pdf = repo_dir / "exports" / "notebooklm_pack" / "Day_1_Sales_Playbook.pdf"
bc_pdf = repo_dir / "exports" / "notebooklm_pack" / "Day_1_Battlecard.pdf"

print("Closer PDF exists:", closer_pdf.exists(), "pages:", len(fitz.open(closer_pdf)))
print("Day 1 PDF exists:", day1_pdf.exists(), "pages:", len(fitz.open(day1_pdf)))
print("Battlecard PDF exists:", bc_pdf.exists(), "pages:", len(fitz.open(bc_pdf)))

