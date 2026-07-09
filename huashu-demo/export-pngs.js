const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const slidesDir = 'C:\\Users\\scrccpa\\.openclaw\\workspace\\huashu-demo\\slides';
const outputDir = 'C:\\Users\\scrccpa\\.openclaw\\workspace\\huashu-demo\\output';

// A4 ratio canvas. Content fills entire page via flex stretching.
const W = 1920;
const H = Math.round(W * 210 / 297); // 1358

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

const slides = [
  '01-cover.html', '02-about.html', '03-services.html',
  '04-jingze.html', '05-performance.html', '06-special-fund.html',
  '07-procurement.html', '08b-subsidy.html', '08c-costbenefit.html',
  '08-engineering.html', '09-subsidy.html', '10-methodology.html',
  '11d-party.html', '11-experience.html', '12-contact.html'
];

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: W, height: H },
    deviceScaleFactor: 4,  // 7680×5432 → 657 DPI on A4
  });

  for (const slide of slides) {
    const page = await context.newPage();
    await page.goto('file://' + path.join(slidesDir, slide), { waitUntil: 'load', timeout: 60000 });
    await page.waitForFunction(() => document.fonts.ready, { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(2000);

    // Stretch body to fill the full A4 viewport
    await page.addStyleTag({
      content: `body { height: ${H}px !important; width: ${W}px !important; overflow: hidden !important; }`
    });

    // Screenshot at full viewport resolution → guaranteed pixel-perfect
    const screenshot = await page.screenshot({ clip: { x: 0, y: 0, width: W, height: H } });
    const outPath = path.join(outputDir, `page-${String(slides.indexOf(slide)+1).padStart(2,'0')}.png`);
    fs.writeFileSync(outPath, screenshot);
    const kb = (screenshot.length / 1024).toFixed(0);
    console.log(`  OK ${slide} (${kb} KB)`);
    await page.close();
  }

  console.log(`\nDone: ${slides.length} PNGs. Run: python make_pdf.py`);
  await browser.close();
})();
