import os
import shutil
import subprocess
from pathlib import Path

SRC_MD = Path(r"C:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_Sales_Playbook.md")
OUT_DIR = Path(r"C:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack")
VAULT_MAT = Path(r"D:\Obsidian\Syndicate Intelligence\Syndicate Intelligence\30_Материалы")
VAULT_ROOT = Path(r"D:\Obsidian\Syndicate Intelligence\Syndicate Intelligence")

CSS_FILE = Path(r"C:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\ebook_style.css")
META_FILE = Path(r"C:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\metadata.yaml")

# 1. Custom CSS for PocketBook E-ink Carta screen
css_content = """/* Typography for E-ink PocketBook 740 */
@charset "utf-8";

body {
    font-family: "PT Serif", "Georgia", "Times New Roman", serif;
    font-size: 1.05em;
    line-height: 1.5;
    text-align: justify;
    text-justify: inter-word;
    hyphens: auto;
    margin: 0;
    padding: 0;
    color: #111111;
    background-color: #ffffff;
}

h1, h2, h3, h4, h5, h6 {
    font-family: "PT Sans", "Helvetica Neue", "Arial", sans-serif;
    font-weight: bold;
    line-height: 1.25;
    color: #000000;
}

h1 {
    font-size: 1.7em;
    text-align: center;
    margin-top: 1.8em;
    margin-bottom: 0.8em;
    page-break-before: always;
    border-bottom: 2px solid #222222;
    padding-bottom: 0.3em;
}

h2 {
    font-size: 1.35em;
    margin-top: 1.5em;
    margin-bottom: 0.6em;
    page-break-before: always;
    border-bottom: 1px solid #666666;
    padding-bottom: 0.2em;
}

h3 {
    font-size: 1.15em;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
}

h4 {
    font-size: 1.05em;
    margin-top: 1.0em;
    margin-bottom: 0.3em;
}

p {
    margin-top: 0;
    margin-bottom: 0.7em;
    text-indent: 1.2em;
}

/* Remove indent for first paragraph after headings or blockquotes */
h1 + p, h2 + p, h3 + p, h4 + p, blockquote + p, ul + p, ol + p, table + p {
    text-indent: 0;
}

blockquote {
    margin: 1.0em 0;
    padding: 0.6em 1.0em;
    border-left: 4px solid #333333;
    background-color: #f3f3f3;
    font-style: normal;
}

blockquote p {
    text-indent: 0;
    margin-bottom: 0.4em;
}

blockquote p:last-child {
    margin-bottom: 0;
}

hr {
    border: none;
    border-top: 1px dashed #888888;
    margin: 1.5em 0;
}

ul, ol {
    margin-top: 0.4em;
    margin-bottom: 0.8em;
    padding-left: 1.8em;
}

li {
    margin-bottom: 0.3em;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 0.9em;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #444444;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
}

th {
    background-color: #e8e8e8;
    font-weight: bold;
}

code {
    font-family: "PT Mono", "Courier New", monospace;
    font-size: 0.9em;
    background-color: #efefef;
    padding: 1px 4px;
    border-radius: 2px;
}

pre {
    font-family: "PT Mono", "Courier New", monospace;
    font-size: 0.85em;
    background-color: #f5f5f5;
    border: 1px solid #cccccc;
    padding: 8px;
    margin: 1.0em 0;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

pre code {
    background-color: transparent;
    padding: 0;
}

strong {
    font-weight: bold;
}

em {
    font-style: italic;
}
"""

CSS_FILE.write_text(css_content, encoding="utf-8")

# 2. Metadata YAML
metadata_content = """---
title: "Корпоративный учебник по крипторынку и продажам (Sales Playbook)"
subtitle: "Модуль M/01: Хищная токеномика, физика депега и судебная хроника манипуляций"
author: "Nullspread Research Academy"
language: "ru"
rights: "Syndicate Intelligence Internal Use Only"
publisher: "Nullspread Academy"
...
"""

META_FILE.write_text(metadata_content, encoding="utf-8")

# 3. Compile EPUB
epub_out = OUT_DIR / "Day_1_Sales_Playbook.epub"
cmd_epub = [
    "pandoc",
    str(SRC_MD),
    "-o", str(epub_out),
    "--metadata-file", str(META_FILE),
    "--css", str(CSS_FILE),
    "--toc",
    "--toc-depth=3",
    "--math-method=mathml",
    "--split-level=2",
]

print("Compiling EPUB...")
res_epub = subprocess.run(cmd_epub, capture_output=True, text=True)
if res_epub.returncode != 0:
    print(f"Error compiling EPUB: {res_epub.stderr}")
else:
    print(f"[OK] EPUB created: {epub_out} ({epub_out.stat().st_size} bytes)")

# 4. Compile FB2
fb2_out = OUT_DIR / "Day_1_Sales_Playbook.fb2"
cmd_fb2 = [
    "pandoc",
    str(SRC_MD),
    "-o", str(fb2_out),
    "--metadata-file", str(META_FILE),
    "--toc",
    "--toc-depth=3",
]

print("Compiling FB2...")
res_fb2 = subprocess.run(cmd_fb2, capture_output=True, text=True)
if res_fb2.returncode != 0:
    print(f"Error compiling FB2: {res_fb2.stderr}")
else:
    print(f"[OK] FB2 created: {fb2_out} ({fb2_out.stat().st_size} bytes)")

# 5. Copy to Obsidian Vault 30_Материалы
if epub_out.exists():
    vault_epub = VAULT_MAT / epub_out.name
    shutil.copy2(epub_out, vault_epub)
    print(f"[VAULT] Copied to {vault_epub} ({vault_epub.stat().st_size} bytes)")

if fb2_out.exists():
    vault_fb2 = VAULT_MAT / fb2_out.name
    shutil.copy2(fb2_out, vault_fb2)
    print(f"[VAULT] Copied to {vault_fb2} ({vault_fb2.stat().st_size} bytes)")

# 6. Update 🧭 Syndicate Intelligence - Главный пульт.md with EPUB and FB2 links
dashboard_file = VAULT_ROOT / "🧭 Syndicate Intelligence - Главный пульт.md"
if dashboard_file.exists():
    db_text = dashboard_file.read_text(encoding="utf-8")
    
    old_block = "## 📱 Быстрый доступ для PocketBook / Mobile (PDF для ридера)"
    new_block = """## 📱 Книжный формат для PocketBook 740 / Мобильного
- [[30_Материалы/Day_1_Sales_Playbook.epub|📖 Day 1 Sales Playbook (EPUB3 - масштабируемый шрифт, оглавление)]]
- [[30_Материалы/Day_1_Sales_Playbook.fb2|📖 Day 1 Sales Playbook (FB2 - нативный формат PocketBook)]]
- [[30_Материалы/Day_1_Sales_Playbook.pdf|📄 Day 1 Sales Playbook (PDF, 5 слоев)]]
- [[30_Материалы/Fast_Track_Closer_Playbook.pdf|📄 Fast Track Closer Playbook (PDF)]]
- [[30_Материалы/Day_1_Battlecard.pdf|📄 Day 1 Battlecard (PDF)]]"""

    if old_block in db_text:
        # replace the lines under it until the next section
        import re
        pattern = r"## 📱 Быстрый доступ для PocketBook / Mobile \(PDF для ридера\)[\s\S]*?(?=## ⚡ 1\. Трекер)"
        updated_db = re.sub(pattern, new_block + "\n\n---\n\n", db_text)
        dashboard_file.write_text(updated_db, encoding="utf-8")
        print("[VAULT] Updated dashboard with EPUB/FB2 book links!")

print("\n--- EBOOK GENERATION FINISHED ---")

