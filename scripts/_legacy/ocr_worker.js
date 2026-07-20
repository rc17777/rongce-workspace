/**
 * Tesseract.js OCR Worker
 * 接收图片路径列表，批量OCR，输出JSON
 * 用法: node ocr_worker.js <image1> <image2> ...
 */
const Tesseract = require('tesseract.js');
const fs = require('fs');
const path = require('path');

async function ocrImage(imagePath) {
    try {
        const { data } = await Tesseract.recognize(imagePath, 'chi_sim+eng', {
            logger: m => {
                if (m.status === 'recognizing text') {
                    process.stderr.write(`\r  OCR ${path.basename(imagePath)}: ${Math.round(m.progress*100)}%`);
                }
            }
        });
        process.stderr.write('\n');
        return { path: imagePath, text: data.text, confidence: data.confidence };
    } catch (err) {
        return { path: imagePath, text: '', error: err.message };
    }
}

async function main() {
    const images = process.argv.slice(2);
    if (images.length === 0) {
        console.log(JSON.stringify({ error: 'No images provided' }));
        process.exit(1);
    }

    const results = [];
    for (const img of images) {
        if (!fs.existsSync(img)) {
            results.push({ path: img, text: '', error: 'File not found' });
            continue;
        }
        const result = await ocrImage(img);
        results.push(result);
        // Clean up image after OCR
        try { fs.unlinkSync(img); } catch(e) {}
    }
    console.log(JSON.stringify(results));
}

main().catch(e => {
    console.log(JSON.stringify({ error: e.message }));
    process.exit(1);
});
