const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const slidesDir = 'C:\\Users\\scrccpa\\.openclaw\\workspace\\huashu-demo\\slides';
const outputDir = 'C:\\Users\\scrccpa\\.openclaw\\workspace\\huashu-demo\\output';

// A4 at 96 DPI (Chromium's default CSS-pixel-to-physical mapping):
// 297mm = 11.69in → 11.69 × 96 = 1122.5 CSS pixels (round to 1122)
// 210mm = 8.27in  → 8.27 × 96 = 793.7 CSS pixels (round to 794)
// 
// BUT our design is 1920×1358. We scale it UP with CSS transform.
const DESIGN_W = 1920;
const DESIGN_H = 1358;
const VP_W = 1122;  // Exact A4 CSS pixels at 96 DPI
const VP_H = 794;
const SCALE_FACTOR = VP_W / DESIGN_W;  // Fit design into A4 viewport

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

const slides = [
  '01-cover.html', '02-about.html', '03-services.html',
  '04-jingze.html', '05-performance.html', '06-special-fund.html',
  '07-procurement.html', '08-engineering.html', '09-subsidy.html',
  '10-methodology.html', '11d-party.html', '11-experience.html', '12-contact.html'
];

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: VP_W, height: VP_H },
    deviceScaleFactor: 4,
  });

  for (const slide of slides) {
    const page = await context.newPage();
    await page.goto('file://' + path.join(slidesDir, slide), { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForFunction(() => document.fonts.ready, { timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(1500);

    // Scale 1920×1358 design to fit within 1122×794 viewport
    // Also adjust body to use viewport dimensions for proper scaling
    await page.addStyleTag({
      content: `
        body {
          width: ${DESIGN_W}px !important;
          height: ${DESIGN_H}px !important;
          transform: scale(${SCALE_FACTOR});
          transform-origin: 0 0;
        }
      `
    });

    // 1122×794 CSS pixels → A4 exact. deviceScaleFactor:4 → 4488×3176 raster
    // Text stays vector in PDF
    const pdfBuffer = await page.pdf({
      width: '297mm',
      height: '210mm',
      printBackground: true,
    });

    const outPath = path.join(outputDir, `page-${String(slides.indexOf(slide)+1).padStart(2,'0')}.pdf`);
    fs.writeFileSync(outPath, pdfBuffer);
    const kb = (pdfBuffer.length / 1024).toFixed(0);
    console.log(`  OK ${slide} (${kb} KB)`);
    await page.close();
  }

  console.log(`\nDone: ${slides.length} PDFs → merge_pdfs.py`);
  await browser.close();
})();
