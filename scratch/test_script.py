from playwright.sync_api import sync_playwright
import fitz

html = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: 0; }
  body {
    font-family: 'Times New Roman', serif;
    font-size: 14pt;
    line-height: 1.5;
    text-align: justify;
    text-justify: inter-word;
    margin: 0;
    padding: 0;
  }
  p {
    text-indent: 1.25cm;
    margin: 0;
  }
  ol, ul {
    margin: 6pt 0;
    padding-left: 1.25cm;
    text-align: left;
  }
  li {
    margin-bottom: 4pt;
    text-align: left;
  }
</style>
</head>
<body>
<h1 style="text-align: center; text-transform: uppercase; font-size: 14pt; margin: 0 0 18pt 0;">ВСТУП</h1>
<p><strong>Актуальність теми.</strong> Будь-який сучасний комп'ютер або мікропроцесорний пристрій працює з електричними сигналами дискретної природи. Всі дані, що зберігаються в пам'яті ЕОМ та обробляються центральним процесором (числа, тексти, команди, графічні зображення), на фізичному рівні подаються у вигляді двійкових кодів.</p>
<p><strong>Основні завдання:</strong></p>
<ol>
  <li>Розглянути відмінності між непозиційними та позиційними системами числення.</li>
  <li>Дослідити розгорнуту степеневу форму запису чисел.</li>
  <li>З'ясувати фізичні та логічні переваги двійкової системи в схемотехніці ЕОМ.</li>
</ol>
</body>
</html>"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    page.pdf(
        path='nullspread-research-academy/scratch/test_margins.pdf',
        format='A4',
        margin={'top': '20mm', 'bottom': '20mm', 'left': '25mm', 'right': '15mm'},
        display_header_footer=True,
        header_template='<div style="font-size: 12pt; font-family: \'Times New Roman\', serif; width: 100%; text-align: right; padding-right: 15mm; padding-top: 5mm;"><span class="pageNumber"></span></div>',
        footer_template='<div></div>'
    )
    browser.close()

doc = fitz.open('nullspread-research-academy/scratch/test_margins.pdf')
p = doc[0]
for b in p.get_text('blocks'):
    print(f"x0={b[0]:.1f}, y0={b[1]:.1f}, x1={b[2]:.1f}, y1={b[3]:.1f} | text={b[4][:40]!r}")

