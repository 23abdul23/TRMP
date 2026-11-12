// usage: node scripts/html_to_pdf.js <input.html> <output.pdf>   (Playwright's bundled Chromium)
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [inp, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + path.resolve(inp), { waitUntil: 'networkidle' });
  await p.pdf({ path: out, format: 'A4', printBackground: true, displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8px;color:#667;width:100%;text-align:center;font-family:Arial">TRMP: contiguous destroy vs RL — project report &nbsp;|&nbsp; page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    margin: { top: '17mm', bottom: '18mm', left: '16mm', right: '16mm' } });
  await b.close();
})();
