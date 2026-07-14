const Tesseract = require('tesseract.js');
const path = require('path');
const fs = require('fs');

async function test() {
    const imgDir = 'D:\\openclaw-workspace\\output\\contract_analysis\\ocr_images';
    if (!fs.existsSync(imgDir)) { console.log('No image dir'); return; }
    const dirs = fs.readdirSync(imgDir);
    if (dirs.length === 0) { console.log('No image dirs'); return; }
    const testDir = path.join(imgDir, dirs[0]);
    const imgs = fs.readdirSync(testDir).filter(f => f.endsWith('.png'));
    if (imgs.length === 0) { console.log('No images in '+testDir); return; }
    const testImg = path.join(testDir, imgs[0]);
    console.log(`Testing: ${path.basename(testImg)} (${(fs.statSync(testImg).size/1024).toFixed(1)} KB)`);
    
    const start = Date.now();
    const worker = await Tesseract.createWorker('chi_sim+eng', 1, {
        logger: m => {
            if (m.status === 'loading tesseract core') console.log('  Loading core...');
            if (m.status === 'initializing tesseract') console.log('  Initializing tesseract...');
            if (m.status === 'loading language traineddata') console.log(`  Loading language: ${Math.round(m.progress*100)}%`);
            if (m.status === 'recognizing text') process.stdout.write(`\r  OCR progress: ${Math.round(m.progress*100)}%`);
        }
    });
    console.log(`\nWorker init: ${((Date.now()-start)/1000).toFixed(1)}s`);
    
    const t0 = Date.now();
    const { data } = await worker.recognize(testImg);
    console.log(`OCR time: ${((Date.now()-t0)/1000).toFixed(1)}s`);
    console.log(`Text: ${data.text.length} chars, Confidence: ${data.confidence}%`);
    console.log(`Sample: ${data.text.substring(0, 300)}`);
    
    await worker.terminate();
    console.log(`Total: ${((Date.now()-start)/1000).toFixed(1)}s`);
}

test().catch(e => { console.error(e.message); process.exit(1); });
