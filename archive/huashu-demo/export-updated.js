const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const root = __dirname;
const slidesDir = path.join(root, 'slides');
const outputDir = path.join(root, 'output');
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

const DESIGN_W = 1920;
const DESIGN_H = 1080;
const slides = [
  '01-cover.html', '02-about.html', '03-services.html',
  '03a-transition.html',
  '04-jingze.html', '05-performance.html', '06-special-fund.html',
  '07-procurement.html', '08b-subsidy.html', '08c-costbenefit.html',
  '08-engineering.html', '09-subsidy.html', '09a-transition.html',
  '10-methodology.html', '11d-party.html', '11-experience.html', '12-contact.html'
];

(async () => {
  const browser = await chromium.launch({ channel: 'msedge' }).catch(() => chromium.launch());
  const context = await browser.newContext({
    viewport: { width: DESIGN_W, height: DESIGN_H },
    deviceScaleFactor: 2,
  });

  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i];
    const page = await context.newPage();
    await page.goto('file://' + path.join(slidesDir, slide), { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(800);
    const n = String(i + 1).padStart(2, '0');
    await page.screenshot({ path: path.join(outputDir, `page-${n}.png`), fullPage: false });
    const pdfBuffer = await page.pdf({ width: '297mm', height: '167mm', printBackground: true });
    fs.writeFileSync(path.join(outputDir, `page-${n}.pdf`), pdfBuffer);
    console.log(`OK ${n} ${slide}`);
    await page.close();
  }
  await browser.close();
})();
