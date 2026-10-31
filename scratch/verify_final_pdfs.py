import os, sys, re
from pathlib import Path
import pypdf

root = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy")
exports = root / "exports" / "notebooklm_pack"

pb_pdf = exports / "Day_1_Sales_Playbook.pdf"
bc_pdf = exports / "Day_1_Battlecard.pdf"
pb_md = exports / "Day_1_Sales_Playbook.md"
bc_md = exports / "Day_1_BATTLECARD.md"

emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]")

print("=== AUDIT REPORT ===")

# 1. Battlecard MD
with open(bc_md, "r", encoding="utf-8") as f:
    bc_md_text = f.read()
bc_md_emojis = emoji_pattern.findall(bc_md_text)
print(f"Battlecard MD: {len(bc_md_text.splitlines())} lines, {len(bc_md_text)} bytes, Emojis: {len(bc_md_emojis)}")

# 2. Battlecard PDF
with open(bc_pdf, "rb") as f:
    bc_reader = pypdf.PdfReader(f)
    bc_pages = len(bc_reader.pages)
    bc_pdf_text = "".join([page.extract_text() or "" for page in bc_reader.pages])
bc_pdf_emojis = emoji_pattern.findall(bc_pdf_text)
print(f"Battlecard PDF: {bc_pages} pages, Emojis: {len(bc_pdf_emojis)}")

# 3. Playbook MD
with open(pb_md, "r", encoding="utf-8") as f:
    pb_md_text = f.read()
pb_md_lines = len(pb_md_text.splitlines())
pb_md_emojis = emoji_pattern.findall(pb_md_text)
print(f"Playbook MD: {pb_md_lines} lines, {len(pb_md_text)} bytes, Emojis: {len(pb_md_emojis)}")

# 4. Playbook PDF
with open(pb_pdf, "rb") as f:
    pb_reader = pypdf.PdfReader(f)
    pb_pages = len(pb_reader.pages)
    pb_pdf_text = "".join([page.extract_text() or "" for page in pb_reader.pages])
pb_pdf_emojis = emoji_pattern.findall(pb_pdf_text)
print(f"Playbook PDF: {pb_pages} pages, Emojis: {len(pb_pdf_emojis)}")

# Check key figures in Playbook MD
checks = [
    ("LOG3", "LOG3" in pb_md_text),
    ("375", "375" in pb_md_text),
    ("-$10.00", "-$10.00" in pb_md_text),
    ("-$200.00", "-$200.00" in pb_md_text),
    ("-$320.00", "-$320.00" in pb_md_text),
    ("-$5,500.00", "-$5,500.00" in pb_md_text),
    ("$183.3 млрд", "$183.3 млрд" in pb_md_text),
    ("$73.4 млрд", "$73.4 млрд" in pb_md_text),
    ("От $100,000", "От $100,000" in pb_md_text),
    ("21,000", "21,000" in pb_md_text),
    ("45,000–65,000", "45,000–65,000" in pb_md_text),
    ("20,000", "20,000" in pb_md_text),
    ("2,900", "2,900" in pb_md_text),
    ("2,100", "2,100" in pb_md_text),
    ("2,600", "2,600" in pb_md_text),
    ("NULLSPREAD check (brand-neutral)", "NULLSPREAD" not in pb_md_text),
    ("NULLSPREAD in battlecard", "NULLSPREAD" not in bc_md_text),
]

print("\n=== KEY FIGURES & INTEGRITY CHECKS ===")
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")

# Check 375 corruptions: should ONLY appear around LOG3
occ_375 = [m.start() for m in re.finditer(r"\b375\b", pb_md_text)]
print(f"\nOccurrences of '375': {len(occ_375)}")
for idx in occ_375:
    context = pb_md_text[max(0, idx-40):min(len(pb_md_text), idx+40)].replace("\n", " ")
    print(f"  375 context: ...{context}...")
