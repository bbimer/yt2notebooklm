import pymupdf
from pathlib import Path

brain_dir = Path(r"C:\Users\root\.gemini\antigravity\brain\ad331343-413a-4ad3-88c8-02a5c5acf7c5")
exports_dir = Path("nullspread-research-academy/exports/notebooklm_pack")

# 1. Check Closer Playbook
closer_pdf = exports_dir / "Fast_Track_Closer_Playbook.pdf"
if closer_pdf.exists():
    doc = pymupdf.open(closer_pdf)
    print(f"Closer PDF pages: {len(doc)}")
    # Render page 4 & 5 to PNG
    for pno in [4, 5]:
        if pno <= len(doc):
            pix = doc[pno-1].get_pixmap(dpi=150)
            pix.save(brain_dir / f"closer_verify_p{pno}.png")
            print(f"Saved closer_verify_p{pno}.png")

# 2. Check Day 1 Sales Playbook
day1_pdf = exports_dir / "Day_1_Sales_Playbook.pdf"
if day1_pdf.exists():
    doc = pymupdf.open(day1_pdf)
    print(f"Day 1 PDF pages: {len(doc)}")
    # Render key math pages: 10, 18, 19, 21, 25
    for pno in [9, 10, 17, 18, 19, 20, 21, 25]:
        if pno <= len(doc):
            pix = doc[pno-1].get_pixmap(dpi=150)
            pix.save(brain_dir / f"day1_verify_p{pno}.png")
            print(f"Saved day1_verify_p{pno}.png")

# 3. Check Battlecard
bc_pdf = exports_dir / "Day_1_Battlecard.pdf"
if bc_pdf.exists():
    doc = pymupdf.open(bc_pdf)
    print(f"Battlecard PDF pages: {len(doc)}")

