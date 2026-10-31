const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setContent(`
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
    `);

    const tests = [
        `\\begin{array}{r@{\\quad}l}
  11011_2 & : 101_2 = 101_2 \\quad (\\text{частка } 5_{10}) \\\\
- 101\\phantom{00} & \\\\
\\hline
  00111_2 & \\\\
- \\phantom{0}101\\phantom{0} & \\\\
\\hline
  00010_2 & (\\text{залишок } 2_{10})
\\end{array}`,
        `\\begin{array}{r|l}
  11011_2 & 101_2 \\\\
  \\hline
  - 101\\phantom{00} & 101_2 \\quad (\\text{частка } 5_{10}) \\\\
  \\hline
  00111_2 & \\\\
  - 101\\phantom{0} & \\\\
  \\hline
  00010_2 & (\\text{залишок } 2_{10})
\\end{array}`
    ];

    for (let i = 0; i < tests.length; i++) {
        const res = await page.evaluate((tex) => {
            try {
                katex.render(tex, document.getElementById('test'), { displayMode: true, throwOnError: true });
                return 'SUCCESS';
            } catch (e) {
                return 'ERROR: ' + e.message;
            }
        }, tests[i]);
        console.log(`Test ${i + 1}:`, res);
    }

    await browser.close();
})();

