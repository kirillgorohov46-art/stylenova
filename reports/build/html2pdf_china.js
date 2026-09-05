// Usage: node html2pdf.js input.html output.pdf [screenshot.png]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [, , input, output, shot] = process.argv;
  const exe = fs.existsSync('/opt/pw-browsers/chromium/chrome-linux/chrome')
    ? '/opt/pw-browsers/chromium/chrome-linux/chrome'
    : '/opt/pw-browsers/chromium';
  const browser = await chromium.launch({ executablePath: exe });
  const page = await browser.newPage({ viewport: { width: 1000, height: 1400 } });
  await page.goto('file://' + path.resolve(input), { waitUntil: 'load' });
  await page.emulateMedia({ media: 'print' });
  if (shot) {
    await page.emulateMedia({ media: 'screen' });
    await page.screenshot({ path: shot, fullPage: true });
    await page.emulateMedia({ media: 'print' });
  }
  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: false,
    margin: { top: '18mm', bottom: '16mm', left: '14mm', right: '14mm' },
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size:8px;color:#898781;width:100%;padding:0 14mm;font-family:\'DejaVu Sans\',sans-serif;display:flex;justify-content:space-between;"><span>StyleNova · Закупка из Китая · маржа и себестоимость · сентябрь 2026</span><span></span></div>',
    footerTemplate: '<div style="font-size:8px;color:#898781;width:100%;padding:0 14mm;font-family:\'DejaVu Sans\',sans-serif;display:flex;justify-content:space-between;"><span>Оптовые цены Alibaba/1688 и правила ввоза в РФ, 5 сентября 2026</span><span>стр. <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
  });
  await browser.close();
  console.log('PDF written:', output);
})().catch((e) => { console.error('ERR', e); process.exit(1); });
