from playwright.sync_api import sync_playwright
import fitz
from pathlib import Path

repo_root = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy")
scratch = repo_root / "scratch"

test_html = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4 portrait;
    margin-top: 20mm;
    margin-bottom: 20mm;
    margin-left: 25mm;
    margin-right: 20mm;
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
  
  /* Academic list: aligned with paragraph indent, left-aligned to avoid gaping word spacing */
  ol, ul {
    margin: 8pt 0;
    padding-left: 1.25cm;
    text-align: left;
  }
  
  li {
    margin-bottom: 5pt;
    line-height: 1.45;
    text-align: left;
  }
</style>
</head>
<body>

<h1>ВСТУП</h1>

<p><strong>Актуальність теми.</strong> Сучасна цифрова техніка та мікропроцесорні пристрої працюють з електричними сигналами дискретної природи. Всі дані, що зберігаються в пам'яті ЕОМ та обробляються центральним процесором (числа, тексти, команди, графічні зображення), на фізичному рівні подаються у вигляді двійкових кодів. Вибір способів кодування та систем числення визначається законами напівпровідникової схемотехніки та дискретної математики.</p>

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

html_file = scratch / "vstup_balanced.html"
html_file.write_text(test_html, encoding="utf-8")

pdf_file = scratch / "vstup_balanced.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(html_file.resolve().as_uri())
    page.pdf(
        path=str(pdf_file),
        format="A4",
        prefer_css_page_size=True,
        display_header_footer=True,
        header_template='<div style="font-size: 12pt; font-family: \'Times New Roman\', serif; width: 100%; text-align: right; padding-right: 20mm; padding-top: 5mm;"><span class="pageNumber"></span></div>',
        footer_template='<div></div>'
    )
    browser.close()

doc = fitz.open(str(pdf_file))
png_file = scratch / "vstup_balanced.png"
doc[0].get_pixmap(dpi=150).save(str(png_file))

# Also copy to brain directory
brain_dir = Path(r"C:\Users\root\.gemini\antigravity\brain\2af54222-aa64-4815-b67b-8de6182563f5")
shutil_copy = brain_dir / "vstup_balanced.png"
import shutil
shutil.copy2(str(png_file), str(shutil_copy))

print("Rendered vstup_balanced successfully!")
for b in doc[0].get_text('blocks'):
    print(f"x0={b[0]:.1f}, x1={b[2]:.1f} | {b[4][:35]!r}")
doc.close()

