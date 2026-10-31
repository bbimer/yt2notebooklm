from playwright.sync_api import sync_playwright
import fitz

html = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4 portrait;
    margin-top: 20mm;
    margin-bottom: 20mm;
    margin-left: 25mm;
    margin-right: 15mm;
  }
  body {
    font-family: 'Times New Roman', serif;
    font-size: 14pt;
    line-height: 1.5;
    text-align: justify;
    margin: 0;
    padding: 0;
  }
  p { text-indent: 1.25cm; margin: 0; }
  h1 { text-align: center; font-size: 14pt; margin: 0 0 18pt 0; }
</style>
</head>
<body>
<h1>ВСТУП</h1>
<p>Тестовий текст для перевірки полів сторінки в хроміум пдф.</p>
</body>
</html>"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    page.pdf(path='nullspread-research-academy/scratch/test_css_margin.pdf', format='A4', prefer_css_page_size=True)
    browser.close()

doc = fitz.open('nullspread-research-academy/scratch/test_css_margin.pdf')
p = doc[0]
for b in p.get_text('blocks'):
    print(f"x0={b[0]:.1f}, x1={b[2]:.1f}, y0={b[1]:.1f}, y1={b[3]:.1f} | text={b[4]!r}")

