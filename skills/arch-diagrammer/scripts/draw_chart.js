#!/usr/bin/env node
/**
 * Chart Drawer - Node.js version
 * Generates production-quality charts for audit reports via @napi-rs/canvas
 *
 * Usage:
 *   node draw_chart.js --type heatmap --data data.json --output out.png
 *   node draw_chart.js --type heatmap --data '{"rows":[...]}' --output out.png
 *
 * Types: heatmap, bar, pie, line, colored_table
 */

const { createCanvas, loadImage, GlobalFonts } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');

// Try to register Chinese fonts
try {
  const fontDirs = [
    'C:\\Windows\\Fonts\\msyh.ttc',
    'C:\\Windows\\Fonts\\simhei.ttf',
    'C:\\Windows\\Fonts\\simsun.ttc',
  ];
  for (const f of fontDirs) {
    if (fs.existsSync(f)) {
      GlobalFonts.registerFromPath(f, path.basename(f, path.extname(f)));
    }
  }
} catch(e) { /* font registration is best-effort */ }

// Available font families
const FONT_TITLE = 'msyh';
const FONT_BODY = 'msyh';
const FONT_FALLBACK = 'sans-serif';

// ============ Color Scheme ============
const C = {
  deepBlue:  '#1A237E',
  mediumBlue:'1565C0',
  lightBlue: '#42A5F5',
  teal:      '#26A69A',
  orange:    '#E65100',
  red:       '#D32F2F',
  yellow:    '#FBC02D',
  green:     '#388E3C',
  grey:      '#757575',
  lightGrey: '#BDBDBD',
  lightBg:   '#E8EAF6',
};

const BAR_COLORS    = ['#1A237E','#1565C0','#42A5F5','#90CAF9'];
const CONTRAST      = ['#1A237E','#E65100'];
const PIE_COLORS    = ['#1A237E','#1565C0','#42A5F5','#26A69A','#E65100','#D32F2F'];
const HEAT_GREEN    = '#388E3C';
const HEAT_YELLOW   = '#FBC02D';
const HEAT_RED      = '#D32F2F';

// ============ Utility ============
function colorToRGBA(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return alpha !== undefined ? `rgba(${r},${g},${b},${alpha})` : hex;
}

function drawRoundedRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function heatColor(ratio) {
  // 0..1 -> green..yellow..red
  const r = Math.round(Math.min(1, ratio * 2) * 211 + 44 * (1 - Math.min(1, ratio * 2)));
  const g = Math.round(Math.max(0, 1 - ratio) * 188 + 56 * ratio);
  const b = Math.round(Math.max(0, 1 - ratio * 2) * 140);
  return `rgb(${r},${g},${b})`;
}

// ============ Chart Renderers ============

function drawHeatmap(data) {
  const rows = data.rows || ['A','B','C','D'];
  const cols = data.columns || ['X','Y'];
  const values = data.values || rows.map(() => cols.map(() => 1));
  const title = data.title || '风险评估热力图';
  const vmin = data.min !== undefined ? data.min : 1;
  const vmax = data.max !== undefined ? data.max : 5;

  const h = Math.max(400, rows.length * 60 + 120);
  const w = Math.max(600, cols.length * 100 + 180);
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  const margin = { top: 60, right: 60, bottom: 60, left: 120 };
  const plotW = w - margin.left - margin.right;
  const plotH = h - margin.top - margin.bottom;
  const cellW = plotW / cols.length;
  const cellH = plotH / rows.length;

  // Background
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  // Title
  ctx.fillStyle = C.deepBlue;
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 35);

  // Draw heatmap cells
  for (let i = 0; i < rows.length; i++) {
    for (let j = 0; j < cols.length; j++) {
      const val = values[i][j];
      const ratio = (val - vmin) / (vmax - vmin);
      const x = margin.left + j * cellW;
      const y = margin.top + i * cellH;

      ctx.fillStyle = heatColor(ratio);
      drawRoundedRect(ctx, x + 2, y + 2, cellW - 4, cellH - 4, 4);
      ctx.fill();

      // Text
      ctx.fillStyle = ratio > 0.5 ? '#FFFFFF' : '#333333';
      ctx.font = `bold 14px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(val), x + cellW / 2, y + cellH / 2);
    }
  }

  // Row labels
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  ctx.font = `13px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.fillStyle = '#333';
  for (let i = 0; i < rows.length; i++) {
    ctx.fillText(rows[i], margin.left - 10, margin.top + i * cellH + cellH / 2);
  }

  // Column labels
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.font = `bold 14px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.fillStyle = '#333';
  for (let j = 0; j < cols.length; j++) {
    ctx.fillText(cols[j], margin.left + j * cellW + cellW / 2, margin.top - 8);
  }

  // Color bar (legend)
  const cbarX = w - 40;
  const cbarY = margin.top;
  const cbarH = plotH;
  const cbarW = 20;
  const cbarGrad = ctx.createLinearGradient(cbarX, cbarY + cbarH, cbarX, cbarY);
  cbarGrad.addColorStop(0, HEAT_GREEN);
  cbarGrad.addColorStop(0.5, HEAT_YELLOW);
  cbarGrad.addColorStop(1, HEAT_RED);
  ctx.fillStyle = cbarGrad;
  drawRoundedRect(ctx, cbarX, cbarY, cbarW, cbarH, 3);
  ctx.fill();

  ctx.strokeStyle = C.grey;
  ctx.lineWidth = 1;
  ctx.strokeRect(cbarX, cbarY, cbarW, cbarH);

  // Color bar labels
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.font = `11px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.fillStyle = HEAT_GREEN;
  ctx.fillText('低', cbarX + cbarW + 8, cbarY + cbarH);
  ctx.fillStyle = HEAT_YELLOW;
  ctx.fillText('中', cbarX + cbarW + 8, cbarY + cbarH / 2);
  ctx.fillStyle = HEAT_RED;
  ctx.fillText('高', cbarX + cbarW + 8, cbarY);

  return canvas.toBuffer('image/png');
}


function drawBarChart(data) {
  const labels = data.labels || ['A','B','C','D'];
  const values = data.values;
  const title = data.title || '柱状图';
  const xlabel = data.xlabel || '';
  const ylabel = data.ylabel || '';

  const isGrouped = Array.isArray(values[0]);
  const nGroups = isGrouped ? values.length : 1;
  const nItems = isGrouped ? values[0].length : values.length;

  const w = Math.max(800, nItems * 100 + 200);
  const h = 500;
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  const margin = { top: 60, right: 40, bottom: 80, left: 80 };
  const plotW = w - margin.left - margin.right;
  const plotH = h - margin.top - margin.bottom;

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = C.deepBlue;
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 35);

  // Find max value
  const allVals = isGrouped ? values.flat() : values;
  const maxVal = Math.max(...allVals, 1);
  const yMax = Math.ceil(maxVal * 1.2 / 10) * 10 || 10;

  // Draw Y axis
  ctx.strokeStyle = C.lightGrey;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin.left, margin.top);
  ctx.lineTo(margin.left, margin.top + plotH);
  ctx.lineTo(margin.left + plotW, margin.top + plotH);
  ctx.stroke();

  // Y labels
  const ySteps = 5;
  for (let i = 0; i <= ySteps; i++) {
    const val = (yMax / ySteps) * i;
    const y = margin.top + plotH - (plotH / ySteps) * i;
    ctx.fillStyle = C.grey;
    ctx.font = `11px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(val), margin.left - 10, y);

    ctx.strokeStyle = '#EEEEEE';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(margin.left + plotW, y);
    ctx.stroke();
  }

  if (ylabel) {
    ctx.fillStyle = C.grey;
    ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.save();
    ctx.translate(20, margin.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(ylabel, 0, 0);
    ctx.restore();
  }

  // Bars
  const groupW = plotW / nItems;
  const barCount = isGrouped ? nGroups : 1;
  const barW = (groupW * 0.7) / barCount;

  for (let i = 0; i < nItems; i++) {
    for (let g = 0; g < barCount; g++) {
      const val = isGrouped ? values[g][i] : values[i];
      const barH = (val / yMax) * plotH;
      const x = margin.left + i * groupW + groupW * 0.15 + g * barW;
      const y = margin.top + plotH - barH;

      const color = isGrouped ? CONTRAST[g % CONTRAST.length] : BAR_COLORS[i % BAR_COLORS.length];
      ctx.fillStyle = colorToRGBA(color, 0.85);
      drawRoundedRect(ctx, x, y, barW - 2, barH, 3);
      ctx.fill();

      // Value label
      if (val > 0) {
        ctx.fillStyle = color;
        ctx.font = `bold 11px ${FONT_BODY}, ${FONT_FALLBACK}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText(String(val), x + (barW - 2) / 2, y - 4);
      }
    }
  }

  // X labels
  ctx.fillStyle = '#333';
  ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let i = 0; i < nItems; i++) {
    ctx.fillText(labels[i], margin.left + i * groupW + groupW / 2, margin.top + plotH + 8);
  }

  if (xlabel) {
    ctx.fillStyle = C.grey;
    ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.fillText(xlabel, margin.left + plotW / 2, h - 10);
  }

  // Legend for grouped
  if (isGrouped && data.group_names) {
    const legendY = 10;
    let lx = w - 300;
    for (let g = 0; g < barCount; g++) {
      ctx.fillStyle = CONTRAST[g % CONTRAST.length];
      ctx.fillRect(lx, legendY, 16, 16);
      ctx.fillStyle = '#333';
      ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(data.group_names[g], lx + 22, legendY + 8);
      lx += 120;
    }
  }

  return canvas.toBuffer('image/png');
}


function drawPieChart(data) {
  const labels = data.labels || ['A','B','C'];
  const values = data.values || [30, 50, 20];
  const title = data.title || '结构分析';
  const isDonut = data.donut !== false;

  const w = 700, h = 500;
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = C.deepBlue;
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 30);

  const total = values.reduce((a, b) => a + b, 0);
  const cx = w / 2 - 50, cy = h / 2 + 20, radius = Math.min(cx - 60, cy - 40);

  let startAngle = -Math.PI / 2;
  for (let i = 0; i < values.length; i++) {
    const sliceAngle = (values[i] / total) * Math.PI * 2;
    const color = PIE_COLORS[i % PIE_COLORS.length];

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Label
    const midAngle = startAngle + sliceAngle / 2;
    const labelR = radius * 0.7;
    const lx = cx + Math.cos(midAngle) * labelR;
    const ly = cy + Math.sin(midAngle) * labelR;
    const pct = ((values[i] / total) * 100).toFixed(1);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = `bold 13px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${pct}%`, lx, ly);

    startAngle += sliceAngle;
  }

  if (isDonut) {
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 0.45, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();
  }

  // Legend
  const legendX = w - 180;
  let legendY = 100;
  for (let i = 0; i < labels.length; i++) {
    ctx.fillStyle = PIE_COLORS[i % PIE_COLORS.length];
    ctx.fillRect(legendX, legendY, 14, 14);
    ctx.fillStyle = '#333';
    ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${labels[i]} (${values[i]})`, legendX + 20, legendY + 7);
    legendY += 24;
  }

  return canvas.toBuffer('image/png');
}


function drawLineChart(data) {
  const labels = data.labels || ['1月','2月','3月','4月'];
  const values = data.values;
  const title = data.title || '趋势分析';
  const ylabel = data.ylabel || '';
  const seriesNames = data.series_names || ['主趋势'];

  const multiSeries = values.length > 1 && Array.isArray(values[0]);
  const series = multiSeries ? values : [values];
  const nPoints = labels.length;
  const lineColors = ['#1A237E','#E65100','#26A69A','#757575'];

  const w = Math.max(800, nPoints * 80 + 200), h = 450;
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = C.deepBlue;
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 30);

  const margin = { top: 50, right: 40, bottom: 60, left: 80 };
  const plotW = w - margin.left - margin.right;
  const plotH = h - margin.top - margin.bottom;

  const allVals = series.flat();
  const maxVal = Math.max(...allVals, 1);
  const yMax = Math.ceil(maxVal * 1.2 / 10) * 10 || 10;

  // Grid
  const ySteps = 5;
  ctx.strokeStyle = '#EEEEEE';
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= ySteps; i++) {
    const y = margin.top + plotH - (plotH / ySteps) * i;
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(margin.left + plotW, y);
    ctx.stroke();
    ctx.fillStyle = C.grey;
    ctx.font = `11px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(String((yMax / ySteps) * i), margin.left - 8, y);
  }

  if (ylabel) {
    ctx.fillStyle = C.grey;
    ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.save();
    ctx.translate(18, margin.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(ylabel, 0, 0);
    ctx.restore();
  }

  // X labels
  ctx.fillStyle = '#333';
  ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  const xStep = plotW / (nPoints - 1 || 1);
  for (let i = 0; i < nPoints; i++) {
    ctx.fillText(labels[i], margin.left + i * xStep, margin.top + plotH + 5);
  }

  // Axes
  ctx.strokeStyle = C.lightGrey;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin.left, margin.top);
  ctx.lineTo(margin.left, margin.top + plotH);
  ctx.lineTo(margin.left + plotW, margin.top + plotH);
  ctx.stroke();

  // Data lines
  for (let s = 0; s < series.length; s++) {
    const vals = series[s];
    const color = lineColors[s % lineColors.length];

    // Line
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let i = 0; i < nPoints; i++) {
      const x = margin.left + i * xStep;
      const y = margin.top + plotH - (vals[i] / yMax) * plotH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Points
    for (let i = 0; i < nPoints; i++) {
      const x = margin.left + i * xStep;
      const y = margin.top + plotH - (vals[i] / yMax) * plotH;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Value label
      ctx.fillStyle = color;
      ctx.font = `bold 11px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(String(vals[i]), x, y - 8);
    }
  }

  // Legend for multi-series
  if (multiSeries) {
    const legendY = 8;
    let lx = w - 300;
    for (let s = 0; s < series.length; s++) {
      ctx.strokeStyle = lineColors[s % lineColors.length];
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(lx, legendY + 8);
      ctx.lineTo(lx + 20, legendY + 8);
      ctx.stroke();
      ctx.fillStyle = '#333';
      ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(seriesNames[s] || `系列${s+1}`, lx + 26, legendY + 8);
      lx += 120;
    }
  }

  return canvas.toBuffer('image/png');
}


function drawColoredTable(data) {
  const headers = data.headers || ['项目','金额','状态'];
  const rows = data.rows || [['A','100','完成'],['B','200','进行中']];
  const title = data.title || '表格';
  const statusCol = data.status_column;

  const nCols = headers.length;
  const nRows = rows.length + 1;
  const colW = 140;
  const rowH = 38;
  const pad = 15;

  const w = nCols * colW + pad * 2;
  const h = nRows * rowH + 60;
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = C.deepBlue;
  ctx.font = `bold 16px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 30);

  const startX = pad;
  const startY = 50;

  // Header
  ctx.fillStyle = C.deepBlue;
  ctx.fillRect(startX, startY, nCols * colW, rowH);
  ctx.fillStyle = '#FFFFFF';
  ctx.font = `bold 13px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let j = 0; j < nCols; j++) {
    ctx.fillText(headers[j], startX + j * colW + colW / 2, startY + rowH / 2);
  }

  // Data rows
  for (let i = 0; i < rows.length; i++) {
    const y = startY + (i + 1) * rowH;
    ctx.fillStyle = i % 2 === 0 ? '#E8EAF6' : '#FFFFFF';
    ctx.fillRect(startX, y, nCols * colW, rowH);

    ctx.strokeStyle = C.lightGrey;
    ctx.lineWidth = 0.5;
    ctx.strokeRect(startX, y, nCols * colW, rowH);

    for (let j = 0; j < nCols; j++) {
      const val = String(rows[i][j]);

      // Color status column
      if (statusCol !== undefined && j === statusCol) {
        if (/高/.test(val)) {
          ctx.fillStyle = '#FFCDD2';
          ctx.fillRect(startX + j * colW, y, colW, rowH);
          ctx.fillStyle = '#D32F2F';
        } else if (/中|进行/.test(val)) {
          ctx.fillStyle = '#FFF9C4';
          ctx.fillRect(startX + j * colW, y, colW, rowH);
          ctx.fillStyle = '#F57F17';
        } else if (/低|完成|正常/.test(val)) {
          ctx.fillStyle = '#C8E6C9';
          ctx.fillRect(startX + j * colW, y, colW, rowH);
          ctx.fillStyle = '#388E3C';
        } else {
          ctx.fillStyle = '#333';
        }
        ctx.font = `bold 12px ${FONT_BODY}, ${FONT_FALLBACK}`;
      } else {
        ctx.fillStyle = '#333';
        ctx.font = `12px ${FONT_BODY}, ${FONT_FALLBACK}`;
      }

      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(val, startX + j * colW + colW / 2, y + rowH / 2);
    }
  }

  // Grid lines
  ctx.strokeStyle = C.lightGrey;
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= rows.length; i++) {
    const y = startY + (i + 1) * rowH;
    ctx.beginPath();
    ctx.moveTo(startX, y);
    ctx.lineTo(startX + nCols * colW, y);
    ctx.stroke();
  }

  return canvas.toBuffer('image/png');
}


// ============ Flowchart Renderer ============

function drawFlowchart(data) {
  const title = data.title || '流程图';
  const steps = data.steps || [
    { name: '步骤1', desc: '开始', color: '#388E3C' },
    { name: '步骤2', desc: '处理', color: '#1565C0' },
    { name: '步骤3', desc: '判断', color: '#FBC02D' },
    { name: '步骤4', desc: '结束', color: '#D32F2F' },
  ];
  const actors = data.actors || [];  // 泳道角色
  const stages = data.stages || [];   // 阶段分组
  const orientation = data.orientation || 'vertical'; // horizontal/vertical

  const n = steps.length;
  const isVertical = orientation === 'vertical';
  
  const boxW = 220;
  const boxH = 56;
  const gap = 40;
  const vGap = 50;
  const margin = 60;

  const w = isVertical ? 700 : n * (boxW + gap) + margin * 2;
  const h = isVertical ? n * (boxH + vGap) + margin * 2 : 500;
  
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  // Title
  ctx.fillStyle = '#1A237E';
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 35);

  // Draw steps
  for (let i = 0; i < n; i++) {
    const step = steps[i];
    const x = isVertical ? (w - boxW) / 2 : margin + i * (boxW + gap);
    const y = isVertical ? margin + i * (boxH + vGap) : h / 2 - boxH / 2;

    const color = step.color || '#1565C0';
    const isDiamond = step.shape === 'diamond';

    // Draw box or diamond
    ctx.save();
    if (isDiamond) {
      ctx.translate(x + boxW / 2, y + boxH / 2);
      ctx.beginPath();
      ctx.moveTo(0, -boxH / 2);
      ctx.lineTo(boxW / 2, 0);
      ctx.lineTo(0, boxH / 2);
      ctx.lineTo(-boxW / 2, 0);
      ctx.closePath();
      ctx.fillStyle = colorToRGBA(color, 0.15);
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    } else {
      drawRoundedRect(ctx, x, y, boxW, boxH, 6);
      ctx.fillStyle = colorToRGBA(color, 0.1);
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Left color bar
      ctx.fillStyle = color;
      drawRoundedRect(ctx, x, y, 6, boxH, 3);
      ctx.fill();
    }

    // Step number badge
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x + 24, y + boxH / 2, 12, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `bold 11px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(i + 1), x + 24, y + boxH / 2);

    // Step name
    ctx.fillStyle = '#333';
    ctx.font = `bold 14px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(step.name, x + 40, y + boxH / 2 - 6);

    // Step description
    if (step.desc) {
      ctx.fillStyle = C.grey;
      ctx.font = `11px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.fillText(step.desc, x + 40, y + boxH / 2 + 14);
    }

    // Arrow between boxes
    if (i < n - 1) {
      const fromX = isVertical ? x + boxW / 2 : x + boxW;
      const fromY = isVertical ? y + boxH : y + boxH / 2;
      const toX = isVertical ? x + boxW / 2 : fromX + gap;
      const toY = isVertical ? fromY + vGap : fromY;

      ctx.strokeStyle = C.grey;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(fromX, fromY);
      ctx.lineTo(toX, toY - (isVertical ? 10 : 0));
      ctx.stroke();

      // Arrowhead
      if (isVertical) {
        ctx.fillStyle = C.grey;
        ctx.beginPath();
        ctx.moveTo(toX - 5, toY - 10);
        ctx.lineTo(toX, toY);
        ctx.lineTo(toX + 5, toY - 10);
        ctx.closePath();
        ctx.fill();
      }

      // Arrow label
      if (step.arrowLabel) {
        ctx.fillStyle = C.grey;
        ctx.font = `10px ${FONT_BODY}, ${FONT_FALLBACK}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText(step.arrowLabel, fromX, isVertical ? fromY + vGap / 2 - 3 : fromY - 8);
      }
    }
  }

  // Draw stage grouping (vertical only)
  if (stages && stages.length > 0 && isVertical) {
    let stageY = margin;
    for (const stage of stages) {
      const startIdx = stage.start || 0;
      const endIdx = stage.end || 0;
      const sY = margin + startIdx * (boxH + vGap);
      const eY = margin + endIdx * (boxH + vGap) + boxH;
      
      // Stage bracket
      ctx.strokeStyle = C.mediumBlue;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      ctx.beginPath();
      ctx.moveTo(45, sY);
      ctx.lineTo(45, eY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Stage label
      ctx.fillStyle = C.mediumBlue;
      ctx.font = `bold 11px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(stage.name, 40, (sY + eY) / 2);
    }
  }

  // Draw swimlanes
  if (actors && actors.length > 0) {
    const laneH = h - margin - 20;
    const laneW = (w - margin * 2) / actors.length;
    ctx.strokeStyle = '#E0E0E0';
    ctx.lineWidth = 0.5;
    ctx.setLineDash([4, 4]);
    for (let i = 1; i < actors.length; i++) {
      ctx.beginPath();
      ctx.moveTo(margin + i * laneW, margin);
      ctx.lineTo(margin + i * laneW, margin + laneH);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Actor labels at top
    ctx.fillStyle = C.deepBlue;
    ctx.font = `bold 12px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    for (let i = 0; i < actors.length; i++) {
      ctx.fillText(actors[i], margin + i * laneW + laneW / 2, margin - 5);
    }
  }

  return canvas.toBuffer('image/png');
}


// ============ Timeline Renderer ============

function drawTimeline(data) {
  const title = data.title || '项目时间轴';
  const milestones = data.milestones || [
    { date: '2026.01', label: '项目启动', desc: '成立工作组' },
    { date: '2026.02', label: '现场审计', desc: '资料收集' },
    { date: '2026.03', label: '报告出具', desc: '征求意见' },
    { date: '2026.04', label: '归档结案', desc: '完成' },
  ];
  const orientation = data.orientation || 'horizontal';

  const n = milestones.length;
  const isHorizontal = orientation === 'horizontal';
  const margin = 60;

  const nodeR = 16;
  const spacing = isHorizontal ? 140 : 100;

  const w = isHorizontal ? n * spacing + margin * 2 : 600;
  const h = isHorizontal ? 350 : n * spacing + margin * 2;
  const midLine = isHorizontal ? h / 2 : w / 2;

  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  // Title
  ctx.fillStyle = '#1A237E';
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 30);

  // Timeline line
  ctx.strokeStyle = C.deepBlue;
  ctx.lineWidth = 2;
  ctx.beginPath();
  if (isHorizontal) {
    ctx.moveTo(margin, midLine);
    ctx.lineTo(w - margin, midLine);
  } else {
    ctx.moveTo(midLine, margin);
    ctx.lineTo(midLine, h - margin);
  }
  ctx.stroke();

  // Draw milestones
  for (let i = 0; i < n; i++) {
    const m = milestones[i];
    const isOdd = i % 2 === 0;

    let cx, cy;
    if (isHorizontal) {
      cx = margin + i * spacing + spacing / 2;
      cy = midLine;
    } else {
      cx = midLine;
      cy = margin + i * spacing + spacing / 2;
    }

    // Node circle
    const color = m.color || (i === 0 ? '#388E3C' : i === n - 1 ? '#1A237E' : '#1565C0');
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(cx, cy, nodeR, 0, Math.PI * 2);
    ctx.fill();
    
    // White inner circle
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(cx, cy, nodeR * 0.5, 0, Math.PI * 2);
    ctx.fill();

    // Number
    ctx.fillStyle = color;
    ctx.font = `bold 10px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(i + 1), cx, cy);

    // Connector line
    const offset = nodeR + 12;
    ctx.strokeStyle = '#BDBDBD';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    if (isHorizontal) {
      const dir = isOdd ? -1 : 1;
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx, cy + dir * offset);
    } else {
      const dir = isOdd ? -1 : 1;
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + dir * offset, cy);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Label box
    const labelW = 120;
    const labelH = 50;
    if (isHorizontal) {
      const lx = cx - labelW / 2;
      const ly = isOdd ? cy - offset - labelH - 5 : cy + offset + 5;

      ctx.fillStyle = '#F5F5F5';
      drawRoundedRect(ctx, lx, ly, labelW, labelH, 6);
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Date
      ctx.fillStyle = color;
      ctx.font = `bold 11px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(m.date || '', cx, ly + labelH / 2 - 4);

      // Label
      ctx.fillStyle = '#333';
      ctx.font = `bold 12px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(m.label, cx, ly + labelH / 2);

      // Description
      if (m.desc) {
        ctx.fillStyle = C.grey;
        ctx.font = `10px ${FONT_BODY}, ${FONT_FALLBACK}`;
        ctx.textBaseline = 'top';
        ctx.fillText(m.desc, cx, ly + labelH / 2 + 14);
      }
    } else {
      const dir = isOdd ? -1 : 1;
      const lx = dir === -1 ? cx - offset - labelW - 5 : cx + offset + 5;
      const ly = cy - labelH / 2;

      ctx.fillStyle = '#F5F5F5';
      drawRoundedRect(ctx, lx, ly, labelW, labelH, 6);
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = color;
      ctx.font = `bold 11px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(m.date || '', lx + labelW / 2, ly + labelH / 2 - 4);

      ctx.fillStyle = '#333';
      ctx.font = `bold 12px ${FONT_BODY}, ${FONT_FALLBACK}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(m.label, lx + labelW / 2, ly + labelH / 2);

      if (m.desc) {
        ctx.fillStyle = C.grey;
        ctx.font = `10px ${FONT_BODY}, ${FONT_FALLBACK}`;
        ctx.textBaseline = 'top';
        ctx.fillText(m.desc, lx + labelW / 2, ly + labelH / 2 + 14);
      }
    }
  }

  return canvas.toBuffer('image/png');
}


// ============ Cycle Diagram Renderer ============

function drawCycle(data) {
  const title = data.title || '循环图';
  const items = data.items || ['P-计划','D-执行','C-检查','A-改进'];
  
  const w = 500, h = 500;
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = '#1A237E';
  ctx.font = `bold 18px ${FONT_TITLE}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, w / 2, 30);

  const cx = w / 2, cy = h / 2 + 20;
  const outerR = 160;
  const innerR = 80;
  const n = items.length;
  const colors = ['#1A237E','#1565C0','#42A5F5','#26A69A'];

  // Draw each arc segment
  for (let i = 0; i < n; i++) {
    const startAngle = -Math.PI / 2 + (i / n) * Math.PI * 2;
    const endAngle = -Math.PI / 2 + ((i + 1) / n) * Math.PI * 2;
    const midAngle = (startAngle + endAngle) / 2;

    // Arc segment
    ctx.beginPath();
    ctx.arc(cx, cy, outerR, startAngle, endAngle);
    ctx.arc(cx, cy, innerR, endAngle, startAngle, true);
    ctx.closePath();
    ctx.fillStyle = colorToRGBA(colors[i % colors.length], 0.12);
    ctx.fill();
    ctx.strokeStyle = colors[i % colors.length];
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Arrow tips
    const tipAngle = endAngle - 0.05;
    const tipX = cx + Math.cos(tipAngle) * (innerR + outerR) / 2;
    const tipY = cy + Math.sin(tipAngle) * (innerR + outerR) / 2;
    ctx.fillStyle = colors[i % colors.length];
    ctx.beginPath();
    const aSize = 8;
    const aAngle = endAngle + Math.PI / 2;
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(tipX + Math.cos(aAngle - 0.5) * aSize, tipY + Math.sin(aAngle - 0.5) * aSize);
    ctx.lineTo(tipX + Math.cos(aAngle + 0.5) * aSize, tipY + Math.sin(aAngle + 0.5) * aSize);
    ctx.closePath();
    ctx.fill();

    // Label
    const labelR = (innerR + outerR) / 2;
    const lx = cx + Math.cos(midAngle) * labelR;
    const ly = cy + Math.sin(midAngle) * labelR;

    ctx.fillStyle = colors[i % colors.length];
    ctx.font = `bold 14px ${FONT_BODY}, ${FONT_FALLBACK}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(items[i], lx, ly);
  }

  // Center circle
  ctx.beginPath();
  ctx.arc(cx, cy, innerR * 0.55, 0, Math.PI * 2);
  ctx.fillStyle = '#FFFFFF';
  ctx.fill();
  ctx.strokeStyle = C.deepBlue;
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = C.deepBlue;
  ctx.font = `bold 13px ${FONT_BODY}, ${FONT_FALLBACK}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('PDCA', cx, cy);

  return canvas.toBuffer('image/png');
}


// ============ Main ============
function parseArgs() {
  const args = {};
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      args[key] = argv[i + 1] !== undefined && !argv[i+1].startsWith('--') ? argv[i+1] : true;
      i += args[key] !== true ? 1 : 0;
    }
  }
  return args;
}

function main() {
  const args = parseArgs();
  const chartType = args.type || args.t;
  const dataArg = args.data || args.d;
  const outputPath = args.output || args.o || 'chart_output.png';

  if (!chartType || !dataArg) {
    console.error('Usage: node draw_chart.js --type <type> --data <json|jsonfile> --output <file.png>');
    console.error('Types: heatmap, bar, pie, line, colored_table, flowchart, timeline, cycle');
    process.exit(1);
  }

  // Parse data
  let data;
  if (fs.existsSync(dataArg)) {
    data = JSON.parse(fs.readFileSync(dataArg, 'utf-8'));
  } else {
    data = JSON.parse(dataArg);
  }

  const dispatch = {
    'heatmap': drawHeatmap,
    'bar': drawBarChart,
    'pie': drawPieChart,
    'line': drawLineChart,
    'colored_table': drawColoredTable,
    'table': drawColoredTable,
    'flowchart': drawFlowchart,
    'timeline': drawTimeline,
    'cycle': drawCycle,
  };

  const renderer = dispatch[chartType];
  if (!renderer) {
    console.error(`Unknown chart type: ${chartType}. Available: ${Object.keys(dispatch).join(', ')}`);
    process.exit(1);
  }

  const buf = renderer(data);
  const outDir = path.dirname(outputPath);
  if (outDir && !fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  fs.writeFileSync(outputPath, buf);
  console.log(`✅ Chart saved: ${outputPath}`);
}

main();
