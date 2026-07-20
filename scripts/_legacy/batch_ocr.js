const Tesseract = require('tesseract.js');
const fs = require('fs');
const path = require('path');

// OCR一个目录中的所有PNG
async function ocrDirectory(imgDir, outputFile) {
    const imgs = fs.readdirSync(imgDir)
        .filter(f => f.endsWith('.png'))
        .sort()
        .map(f => path.join(imgDir, f));
    
    if (imgs.length === 0) {
        fs.writeFileSync(outputFile, JSON.stringify({error:'no images', dir: imgDir}));
        return;
    }
    
    const startAll = Date.now();
    const worker = await Tesseract.createWorker('chi_sim+eng', 1, {
        logger: m => {
            if (m.status === 'loading language traineddata') process.stderr.write(`\r${path.basename(imgDir)} init: ${Math.round(m.progress*100)}%`);
        }
    });
    
    const results = [];
    for (let i = 0; i < imgs.length; i++) {
        const t0 = Date.now();
        const { data } = await worker.recognize(imgs[i]);
        results.push({
            page: i + 1,
            file: path.basename(imgs[i]),
            text: data.text,
            confidence: Math.round(data.confidence),
            time_s: Math.round((Date.now()-t0)/10)/100
        });
        process.stderr.write(`\r${path.basename(imgDir)}: ${i+1}/${imgs.length} (${Math.round(data.confidence)}%)`);
    }
    
    await worker.terminate();
    
    const output = {
        dir: imgDir,
        total_pages: imgs.length,
        total_time_s: Math.round((Date.now()-startAll)/100)/10,
        avg_confidence: Math.round(results.reduce((s,r)=>s+r.confidence,0)/results.length),
        total_chars: results.reduce((s,r)=>s+r.text.length,0),
        results
    };
    
    fs.writeFileSync(outputFile, JSON.stringify(output, null, 2));
    process.stderr.write(`\r${path.basename(imgDir)}: DONE ${output.total_chars} chars\n`);
}

const imgDir = process.argv[2];
const outFile = process.argv[3];
if (!imgDir || !outFile) {
    console.log(JSON.stringify({error:'Usage: node batch_ocr.js <imgdir> <output.json>'}));
    process.exit(1);
}

ocrDirectory(imgDir, outFile).catch(e => {
    fs.writeFileSync(outFile, JSON.stringify({error: e.message}));
    process.exit(1);
});
