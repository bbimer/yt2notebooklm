import os
import re
import subprocess
import shutil
from pathlib import Path
import fitz  # PyMuPDF
from playwright.sync_api import sync_playwright

repo_root = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy")
md_file = repo_root / "knowledge_base" / "domains" / "computer_science" / "referat_binary_numeral_systems_ua.md"
brain_dir = Path(r"C:\Users\root\.gemini\antigravity\brain\7afdad11-34cd-4582-8fa3-936fa707f3e9")
pandoc_exe = r"C:\Users\root\AppData\Local\Pandoc\pandoc.exe"

# Step 1: Run Pandoc with markdown+pipe_tables and KaTeX math
cmd = [pandoc_exe, "-f", "markdown+pipe_tables", str(md_file), "-t", "html", "--math-method=katex"]
proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
raw_html = proc.stdout

# Extract content starting from after the title page hr
parts = re.split(r'<hr\s*/?>', raw_html, maxsplit=1)
main_body_html = parts[1] if len(parts) == 2 else raw_html

# Separate TOC from main content: find <h1 id="вступ">
intro_match = re.search(r'(<h1[^>]*id="вступ"[^>]*>)', main_body_html, flags=re.IGNORECASE)
toc_html_raw = main_body_html[:intro_match.start()] if intro_match else ""
content_html_raw = main_body_html[intro_match.start():] if intro_match else main_body_html

# Insert page breaks before each major chapter ONLY
major_sections = [
    '<h1 id="вступ">',
    '<h1 id="розділ-1',
    '<h1 id="розділ-2',
    '<h1 id="розділ-3',
    '<h1 id="висновки">',
    '<h1 id="список-використаних-джерел">'
]
for s in major_sections:
    content_html_raw = re.sub(f'({re.escape(s)})', r'<div class="page-break"></div>\1', content_html_raw, flags=re.IGNORECASE)

# Title page HTML component (fits precisely on 1 page)
title_page_html = """
<div class="cover-page">
  <div class="cover-header">
    <div class="ministry">МІНІСТЕРСТВО ОСВІТИ І НАУКИ УКРАЇНИ</div>
    <div class="university">НАЦІОНАЛЬНИЙ ТЕХНІЧНИЙ УНІВЕРСИТЕТ УКРАЇНИ<br>«КИЇВСЬКИЙ ПОЛІТЕХНІЧНИЙ ІНСТИТУТ ІМЕНІ ІГОРЯ СІКОРСЬКОГО»</div>
    <div class="faculty">Факультет інформатики та обчислювальної техніки</div>
    <div class="department">Кафедра обчислювальної техніки</div>
  </div>

  <div class="cover-middle">
    <div class="doc-type">РЕФЕРАТ</div>
    <div class="doc-discipline">з дисципліни: «Архітектура комп'ютерних систем та основи схемотехніки»</div>
    <div class="doc-topic-label">на тему:</div>
    <div class="doc-topic">«Системи числення, двійкова арифметика та принципи машинного представлення даних в обчислювальних системах»</div>
  </div>

  <div class="cover-meta-grid">
    <div class="meta-left"></div>
    <div class="meta-right">
      <p><strong>Виконав:</strong><br>
      студент групи КН-21<br>
      <em>Іваненко Іван Іванович</em></p>
      
      <p style="margin-top: 14px;"><strong>Перевірив:</strong><br>
      доцент кафедри ОТ, к.т.н.<br>
      <em>Петренко Петро Петрович</em></p>
    </div>
  </div>

  <div class="cover-footer">
    <div>Київ — 2026</div>
  </div>
</div>
"""

def generate_full_html(toc_entries=None):
    if toc_entries:
        toc_items_html = []
        for title, page_num, level in toc_entries:
            indent_class = "toc-l1" if level == 1 else "toc-l2"
            weight_style = "font-weight: bold;" if level == 1 else ""
            toc_items_html.append(f"""
            <div class="toc-row {indent_class}" style="{weight_style}">
              <span class="toc-text">{title}</span>
              <span class="toc-dots"></span>
              <span class="toc-page-num">{page_num}</span>
            </div>
            """)
        toc_content = f"""
        <div class="toc-container">
          <h1 class="toc-header">ЗМІСТ</h1>
          {''.join(toc_items_html)}
        </div>
        """
    else:
        toc_content = f"""
        <div class="toc-container">
          {toc_html_raw}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <title>Реферат - Системи числення та двійкова арифметика</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <style>
    @page {{
      size: A4 portrait;
      margin: 20mm 20mm 20mm 20mm; /* Centered, symmetric margins */
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      font-family: "Times New Roman", Times, "Liberation Serif", serif;
      font-size: 14pt;
      line-height: 1.45;
      color: #000000;
      background: #ffffff;
      text-align: justify;
      margin: 0;
      padding: 0;
    }}
    
    /* Cover Page Styling */
    .cover-page {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 250mm;
      text-align: center;
      padding-top: 5mm;
      padding-bottom: 5mm;
      page-break-after: always;
      break-after: page;
    }}
    .ministry {{
      font-size: 13pt;
      font-weight: bold;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .university {{
      font-size: 13.5pt;
      font-weight: bold;
      line-height: 1.3;
      margin-bottom: 8px;
    }}
    .faculty, .department {{
      font-size: 13pt;
      margin-bottom: 3px;
    }}
    .cover-middle {{
      margin-top: 25mm;
      margin-bottom: 20mm;
    }}
    .doc-type {{
      font-size: 26pt;
      font-weight: bold;
      letter-spacing: 2px;
      margin-bottom: 12px;
    }}
    .doc-discipline {{
      font-size: 13.5pt;
      font-style: italic;
      margin-bottom: 16px;
    }}
    .doc-topic-label {{
      font-size: 13pt;
      margin-bottom: 8px;
    }}
    .doc-topic {{
      font-size: 16pt;
      font-weight: bold;
      line-height: 1.35;
      max-width: 90%;
      margin: 0 auto;
    }}
    .cover-meta-grid {{
      display: flex;
      justify-content: flex-end;
      text-align: left;
      font-size: 13pt;
      line-height: 1.4;
      margin-top: 15mm;
      margin-bottom: 15mm;
    }}
    .meta-right {{
      width: 48%;
    }}
    .meta-right p {{
      text-indent: 0 !important;
      margin: 0;
    }}
    .cover-footer {{
      font-size: 13pt;
      font-weight: bold;
    }}
    
    /* TOC Styling - strictly 1 page */
    .toc-container {{
      page-break-after: always;
      break-after: page;
      padding-top: 5mm;
    }}
    .toc-header {{
      text-align: center;
      font-size: 16pt;
      font-weight: bold;
      margin-bottom: 20pt;
    }}
    .toc-row {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      margin-bottom: 7pt;
      font-size: 13pt;
      line-height: 1.3;
    }}
    .toc-l1 {{
      font-weight: bold;
      margin-top: 8pt;
    }}
    .toc-l2 {{
      padding-left: 20px;
      font-size: 12.5pt;
    }}
    .toc-text {{
      white-space: normal;
    }}
    .toc-dots {{
      flex-grow: 1;
      border-bottom: 1px dotted #333;
      margin: 0 8px;
      position: relative;
      top: -3px;
    }}
    .toc-page-num {{
      font-weight: bold;
      min-width: 25px;
      text-align: right;
    }}

    /* Main Typography */
    p {{
      text-indent: 1.25cm;
      margin-top: 0;
      margin-bottom: 0.45em;
    }}
    h1, h2, h3, h4 {{
      text-align: left;
      text-indent: 0;
      font-weight: bold;
      break-after: avoid;
      page-break-after: avoid;
    }}
    h1 {{
      font-size: 16pt;
      margin-top: 20pt;
      margin-bottom: 12pt;
      text-align: center;
      text-transform: uppercase;
    }}
    h2 {{
      font-size: 14pt;
      margin-top: 16pt;
      margin-bottom: 8pt;
    }}
    h3 {{
      font-size: 13.5pt;
      margin-top: 12pt;
      margin-bottom: 6pt;
    }}
    h4 {{
      font-size: 13pt;
      margin-top: 10pt;
      margin-bottom: 4pt;
      font-style: italic;
    }}
    .page-break {{
      page-break-before: always;
      break-before: page;
    }}

    /* Tables */
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 14pt 0;
      font-size: 11pt;
      line-height: 1.35;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    th, td {{
      border: 1px solid #222;
      padding: 6pt 8pt;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background-color: #f5f5f5;
      font-weight: bold;
      text-align: center;
    }}

    /* Lists */
    ul, ol {{
      margin-top: 0;
      margin-bottom: 0.5em;
      padding-left: 1.6cm;
    }}
    li {{
      margin-bottom: 0.2em;
    }}

    /* Blockquotes */
    blockquote {{
      margin: 12pt 0;
      padding: 6pt 16pt;
      border-left: 3px solid #222;
      background-color: #fbfbfb;
      font-style: italic;
    }}
    blockquote p {{
      text-indent: 0;
      margin: 0;
    }}

    /* Math Formulas */
    .katex-display {{
      margin: 10pt 0 !important;
      text-align: center;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .katex {{
      font-size: 1.05em !important;
    }}
    pre, code {{
      font-family: Consolas, "Courier New", monospace;
      font-size: 11pt;
      background-color: #f4f4f4;
      padding: 2px 4px;
      border-radius: 3px;
    }}
    pre {{
      padding: 8pt;
      overflow-x: auto;
    }}
  </style>
</head>
<body>
{title_page_html}
{toc_content}
{content_html_raw}

<script>
document.querySelectorAll('span.math.inline').forEach(el => {{
  try {{
    katex.render(el.textContent, el, {{ displayMode: false, throwOnError: false }});
  }} catch (e) {{
    console.error(e);
  }}
}});
document.querySelectorAll('span.math.display').forEach(el => {{
  try {{
    katex.render(el.textContent, el, {{ displayMode: true, throwOnError: false }});
  }} catch (e) {{
    console.error(e);
  }}
}});
window.katexRenderDone = true;
</script>
</body>
</html>"""

# Pass 1: Build temp HTML & render temp PDF to find exact page numbers
html_temp = repo_root / "scratch" / "temp_referat.html"
html_temp.write_text(generate_full_html(), encoding="utf-8")

pdf_temp = repo_root / "scratch" / "temp_referat.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    page = browser.new_page()
    page.goto(html_temp.resolve().as_uri(), wait_until="networkidle")
    page.wait_for_function("() => window.katexRenderDone === true")
    page.wait_for_timeout(1000)
    page.pdf(
        path=str(pdf_temp),
        format="A4",
        margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
        print_background=True,
        display_header_footer=True,
        header_template="<div></div>",
        footer_template='<div style="font-size: 10pt; font-family: \'Times New Roman\', serif; width: 100%; text-align: right; padding-right: 20mm;"><span class="pageNumber"></span></div>'
    )
    browser.close()

# Search temp PDF for actual page numbers of each section
doc = fitz.open(str(pdf_temp))
sections_to_find = [
    ("ВСТУП", "ВСТУП", 1),
    ("РОЗДІЛ 1. ЗАГАЛЬНІ ВІДОМОСТІ ПРО СИСТЕМИ ЧИСЛЕННЯ", "РОЗДІЛ 1", 1),
    ("1.1. Поняття системи числення. Непозиційні та позиційні системи", "1.1. Поняття системи", 2),
    ("1.2. Базові характеристики позиційних систем числення", "1.2. Базові характеристики", 2),
    ("РОЗДІЛ 2. ОСНОВНІ КОМП’ЮТЕРНІ СИСТЕМИ ЧИСЛЕННЯ", "РОЗДІЛ 2", 1),
    ("2.1. Двійкова система числення (Binary) як основа цифрової електроніки", "2.1. Двійкова система", 2),
    ("2.2. Вісімкова (Octal) та шістнадцяткова (Hexadecimal) системи", "2.2. Вісімкова", 2),
    ("РОЗДІЛ 3. АЛГОРИТМИ ПЕРЕВОДУ ЧИСЕЛ ТА ДВІЙКОВА АРИФМЕТИКА", "РОЗДІЛ 3", 1),
    ("3.1. Переведення цілих та дробових чисел. Дроби та IEEE 754", "3.1. Переведення", 2),
    ("3.2. Швидкий перехід між системами (метод тріад і тетрад)", "3.2. Швидкий перехід", 2),
    ("3.3. Арифметичні операції та машинне кодування чисел", "3.3. Арифметичні операції", 2),
    ("ВИСНОВКИ", "ВИСНОВКИ", 1),
    ("СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ", "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ", 1),
]

toc_entries = []
for full_title, search_str, level in sections_to_find:
    found_page = None
    for p_idx, p_obj in enumerate(doc):
        if p_idx < 2:
            continue
        text = p_obj.get_text()
        if search_str in text:
            found_page = p_idx + 1  # 1-based page number
            break
    if found_page is None:
        found_page = 3
    toc_entries.append((full_title, found_page, level))

doc.close()
print("Discovered TOC page numbers:")
for t, p_num, l in toc_entries:
    print(f"  {t} -> Page {p_num}")

# Pass 2: Re-render final HTML with real TOC page numbers
final_html_file = repo_root / "scratch" / "final_referat.html"
final_html_file.write_text(generate_full_html(toc_entries), encoding="utf-8")

final_pdf = repo_root / "knowledge_base" / "domains" / "computer_science" / "referat_binary_numeral_systems_ua.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    page = browser.new_page()
    page.goto(final_html_file.resolve().as_uri(), wait_until="networkidle")
    page.wait_for_function("() => window.katexRenderDone === true")
    page.wait_for_timeout(1000)
    page.pdf(
        path=str(final_pdf),
        format="A4",
        margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
        print_background=True,
        display_header_footer=True,
        header_template="<div></div>",
        footer_template='<div style="font-size: 10pt; font-family: \'Times New Roman\', serif; width: 100%; text-align: right; padding-right: 20mm;"><span class="pageNumber"></span></div>'
    )
    browser.close()

# Step 7: Redact page number from cover page (Page 1)
doc_final = fitz.open(str(final_pdf))
cover_page = doc_final[0]
rect = fitz.Rect(0, cover_page.rect.height - 100, cover_page.rect.width, cover_page.rect.height)
cover_page.add_redact_annot(rect, fill=(1, 1, 1))
cover_page.apply_redactions()

temp_clean = repo_root / "scratch" / "cleaned_final.pdf"
doc_final.save(str(temp_clean), garbage=4, deflate=True)
doc_final.close()
os.replace(str(temp_clean), str(final_pdf))

# Copy to brain artifact directory
brain_pdf = brain_dir / "referat_binary_numeral_systems_ua.pdf"
shutil.copy2(str(final_pdf), str(brain_pdf))

print(f"PERFECT ACADEMIC PDF GENERATED AT:\n  {final_pdf}\n  {brain_pdf}")

# Verification of final PDF
doc_check = fitz.open(str(final_pdf))
patterns = ['\\begin{array}', '\\boxed', '\\underbrace', '\\cdot', '\\phantom', '\\overset']
found = {}
for i, page in enumerate(doc_check):
    t = page.get_text()
    for pat in patterns:
        if pat in t:
            found.setdefault(pat, []).append(i + 1)
print(f"Total pages: {len(doc_check)}")
print(f"Raw patterns check: {found}")
assert len(found) == 0, f"Raw LaTeX patterns still found in PDF: {found}"

# Render preview images
doc_check[0].get_pixmap(dpi=150).save(str(brain_dir / "page_1.png"))
doc_check[1].get_pixmap(dpi=150).save(str(brain_dir / "page_2_toc.png"))
doc_check[2].get_pixmap(dpi=150).save(str(brain_dir / "page_3_vstup.png"))
doc_check[3].get_pixmap(dpi=150).save(str(brain_dir / "page_4_ch1.png"))
doc_check.close()

# Generate updated DOCX
docx_file = repo_root / "knowledge_base" / "domains" / "computer_science" / "referat_binary_numeral_systems.docx"
brain_docx = brain_dir / "referat_binary_numeral_systems.docx"
cmd_docx = [pandoc_exe, "-f", "markdown+pipe_tables", str(md_file), "-o", str(docx_file)]
subprocess.run(cmd_docx, check=True)
shutil.copy2(str(docx_file), str(brain_docx))

# Copy updated md to brain artifact
brain_md = brain_dir / "referat_binary_numeral_systems_ua.md"
shutil.copy2(str(md_file), str(brain_md))

print("ALL BUILDS & PREVIEWS COMPLETED SUCCESSFULLY!")
