from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content("""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
            <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
        </head>
        <body>
            <div id="test"></div>
        </body>
        </html>
    """)

    tests = [
        r"""\begin{array}{r@{\quad}l}
  11011_2 & : 101_2 = 101_2 \quad (\text{частка } 5_{10}) \\
- 101\phantom{00} & \\
\hline
  00111_2 & \\
- \phantom{0}101\phantom{0} & \\
\hline
  00010_2 & (\text{залишок } 2_{10})
\end{array}""",
        r"""\begin{array}{r|l}
  11011_2 & 101_2 \\
  \hline
  - 101\phantom{00} & 101_2 \quad (\text{частка } 5_{10}) \\
  \hline
  00111_2 & \\
  - 101\phantom{0} & \\
  \hline
  00010_2 & (\text{залишок } 2_{10})
\end{array}"""
    ]

    for i, t in enumerate(tests):
        res = page.evaluate("""(tex) => {
            try {
                katex.render(tex, document.getElementById('test'), { displayMode: true, throwOnError: true });
                return 'SUCCESS';
            } catch (e) {
                return 'ERROR: ' + e.message;
            }
        }""", t)
        print(f"Test {i+1}: {res}")

    browser.close()

