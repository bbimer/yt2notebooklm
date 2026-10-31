import fitz
from playwright.sync_api import sync_playwright
from pathlib import Path

repo_root = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy")
scratch = repo_root / "scratch"

# Test rendering Vstup with corrected margins and list styling
test_html = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4 portrait;
    margin: 0;
  }
  * {
    box-sizing: border-box;
  }
  body {
    font-family: "Times New Roman", Times, "Liberation Serif", serif;
    font-size: 14pt;
    line-height: 1.5;
    color: #000000;
    background: #ffffff;
    text-align: justify;
    text-justify: inter-word;
    margin: 0;
    padding: 0;
  }
  
  h1 {
    font-size: 14pt;
    font-weight: bold;
    text-transform: uppercase;
    text-align: center;
    margin: 0 0 18pt 0;
    text-indent: 0;
  }
  
  p {
    margin: 0 0 0 0;
    text-indent: 1.25cm;
    line-height: 1.5;
    text-align: justify;
  }
  
  /* Academic list styling: aligned with paragraph indent, left-aligned text (no ugly word stretching) */
  ol, ul {
    margin: 8pt 0;
    padding-left: 1.25cm; /* Exactly matching 1.25cm paragraph indent! */
    text-align: left;
  }
  
  li {
    margin-bottom: 6pt;
    line-height: 1.4;
    text-align: left; /* Eliminates huge word gaps */
  }
</style>
</head>
<body>

<h1>ВСТУП</h1>

<p><strong>Актуальність теми.</strong> Будь-який сучасний комп'ютер або мікропроцесорний пристрій працює з електричними сигналами дискретної природи. Всі дані, що зберігаються в пам'яті ЕОМ та обробляються центральним процесором (числа, тексти, команди, графічні зображення), на фізичному рівні подаються у вигляді двійкових кодів. Вибір способів кодування та систем числення визначається законами напівпровідникової схемотехніки та дискретної математики.</p>

<p>Використання десяткової системи в електронних схемах призвело б до надмірного ускладнення апаратури: для надійного розпізнавання десяти різних рівнів напруги потрібні дуже точні й дорогі компоненти, чутливі до перешкод. Натомість двійкова система використовує лише два стани («є напруга» або «немає напруги»), що забезпечує максимальну надійність і простоту логічних елементів. Для скороченого запису двійкових кодів фахівці використовують вісімкову та шістнадцяткову системи числення.</p>

<p><strong>Мета реферату</strong> — вивчити теоретичні засади систем числення, з'ясувати причини застосування двійкової, вісімкової та шістнадцяткової систем в обчислювальній техніці, опанувати правила переведення чисел і виконання двійкових арифметичних операцій, а також розглянути машинне представлення цілих чисел зі знаком у прямому, оберненому та додатковому кодах.</p>

<p><strong>Основні завдання:</strong></p>

<ol>
  <li>Розглянути відмінності між непозиційними та позиційними системами числення.</li>
  <li>Дослідити розгорнуту степеневу форму запису чисел.</li>
  <li>З'ясувати фізичні та логічні переваги двійкової системи в схемотехніці ЕОМ.</li>
  <li>Ознайомитися з призначенням вісімкової та шістнадцяткової систем.</li>
  <li>Розглянути практичні алгоритми переведення цілих і дробових чисел.</li>
  <li>Опанувати двійкове додавання, множення та принцип заміни віднімання додаванням у додатковому коді.</li>
</ol>

</body>
</html>"""

html_path = scratch / "test_vstup_clean.html"
html_path.write_text(test_html, encoding="utf-8")

# Let's test two margin setups:
# Option A: Symmetrical (Left: 20mm, Right: 20mm, Top: 20mm, Bottom: 20mm)
# Option B: Standard Academic (Left: 25mm, Right: 15mm, Top: 20mm, Bottom: 20mm)

with sync_playwright() as p:
    browser = p.chromium.launch()
    
    # Render Option A (20/20)
    page_a = browser.new_page()
    page_a.goto(html_path.resolve().as_uri())
    pdf_a = scratch / "vstup_20_20.pdf"
    page_a.pdf(
        path=str(pdf_a),
        format="A4",
        margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
        display_header_footer=True,
        header_template='<div style="font-size: 12pt; font-family: \'Times New Roman\', serif; width: 100%; text-align: right; padding-right: 20mm; padding-top: 5mm;"><span class="pageNumber"></span></div>',
        footer_template='<div></div>'
    )
    
    # Render Option B (25/15)
    page_b = browser.new_page()
    page_b.goto(html_path.resolve().as_uri())
    pdf_b = scratch / "vstup_25_15.pdf"
    page_b.pdf(
        path=str(pdf_b),
        format="A4",
        margin={"top": "20mm", "bottom": "20mm", "left": "25mm", "right": "15mm"},
        display_header_footer=True,
        header_template='<div style="font-size: 12pt; font-family: \'Times New Roman\', serif; width: 100%; text-align: right; padding-right: 15mm; padding-top: 5mm;"><span class="pageNumber"></span></div>',
        footer_template='<div></div>'
    )
    
    browser.close()

# Export images of both
doc_a = fitz.open(str(pdf_a))
doc_a[0].get_pixmap(dpi=150).save(str(scratch / "vstup_20_20.png"))
doc_a.close()

doc_b = fitz.open(str(pdf_b))
doc_b[0].get_pixmap(dpi=150).save(str(scratch / "vstup_25_15.png"))
doc_b.close()

print("Both test PDFs and PNGs generated!")

