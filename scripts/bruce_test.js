const pptxgen = require("pptxgenjs");
const fs = require("fs");

const pptx = new pptxgen();

// ─── 华为方案配色 ───
const C = {
  bg:       "0A1F3F",   // 深蓝底
  primary:  "0A1F3F",   // 深蓝
  gold:     "C5955C",   // 铜金
  accent:   "1A5C6E",   // 青绿
  white:    "FFFFFF",
  light:    "F0EDE6",   // 暖灰
  text:     "333333",
  gray:     "888888",
  goldLight:"E8CFA0",
};

pptx.defineLayout({ name: "CUSTOM", width: 13.33, height: 7.5 });
pptx.layout = "CUSTOM";

// ─── P1: Cover ───
const s1 = pptx.addSlide();
s1.background = { fill: C.bg };
s1.addShape("rect", { x: 0, y: 0, w: 13.33, h: 0.15, fill: C.gold });
s1.addShape("rect", { x: 0, y: 7.35, w: 13.33, h: 0.15, fill: C.gold });
s1.addShape("rect", { x: 0.8, y: 1.5, w: 0.04, h: 4.5, fill: C.gold });
s1.addText("四川融策会计师事务所", { x: 1.5, y: 1.5, w: 10, h: 1.2, fontSize: 32, fontFace: "Microsoft YaHei", bold: true, color: C.white });
s1.addText("SICHUAN RONGCE CERTIFIED PUBLIC ACCOUNTANTS", { x: 1.5, y: 2.8, w: 10, h: 0.6, fontSize: 11, fontFace: "SimSun", color: C.goldLight });
s1.addText("政府审计  ·  绩效评价  ·  工程咨询  ·  财政评审", { x: 1.5, y: 3.8, w: 10, h: 0.6, fontSize: 14, color: C.white });
s1.addShape("rect", { x: 1.5, y: 4.8, w: 3, h: 0.04, fill: C.gold });
s1.addText("专业 · 诚信 · 高效  |  值得信赖的审计服务伙伴", { x: 1.5, y: 5.2, w: 10, h: 0.5, fontSize: 11, color: C.goldLight });
s1.addText("2026", { x: 1.5, y: 5.8, w: 4, h: 0.6, fontSize: 16, bold: true, color: C.gold });

// ─── P2: Content page ───
const s2 = pptx.addSlide();
s2.background = { fill: C.white };
s2.addShape("rect", { x: 0, y: 0, w: 13.33, h: 0.06, fill: C.gold });
s2.addShape("rect", { x: 0, y: 7.3, w: 13.33, h: 0.2, fill: C.bg });
s2.addText("公司概览", { x: 0.8, y: 0.4, w: 8, h: 0.8, fontSize: 22, fontFace: "Microsoft YaHei", bold: true, color: C.bg });
s2.addShape("rect", { x: 0.8, y: 1.2, w: 2, h: 0.04, fill: C.gold });

// 简介
s2.addText("四川融策会计师事务所主营政府审计业务，涵盖绩效评价、资产清查、专项债申报、监督检查等财政职能；四川融策工程咨询公司主营预算编制、财政评审、全过程工程咨询与工程结算。", 
  { x: 0.8, y: 1.6, w: 11.5, h: 1.5, fontSize: 12, fontFace: "SimSun", color: C.text, lineSpacingMultiple: 1.5 });

// 三个数据卡片
const cards = [
  { num: "300+", label: "服务客户", sub: "覆盖政府与企事业单位" },
  { num: "50+",  label: "专业团队", sub: "注册会计师+工程师" },
  { num: "800+", label: "服务项目", sub: "12年行业经验积累" },
];
cards.forEach((c, i) => {
  const cx = 0.8 + i * 4.1;
  s2.addShape("roundRect", { x: cx, y: 3.5, w: 3.7, h: 3, fill: C.light, rectRadius: 0.1 });
  s2.addText(c.num, { x: cx, y: 3.6, w: 3.7, h: 1.5, fontSize: 32, fontFace: "Microsoft YaHei", bold: true, color: C.gold, align: "center", valign: "bottom" });
  s2.addText(c.label, { x: cx, y: 5.0, w: 3.7, h: 0.5, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.bg, align: "center" });
  s2.addText(c.sub, { x: cx, y: 5.5, w: 3.7, h: 0.5, fontSize: 9, fontFace: "SimSun", color: C.gray, align: "center" });
});

// 页码
s2.addText("2/3", { x: 11.5, y: 7.3, w: 1.5, h: 0.2, fontSize: 8, color: C.white, align: "right" });

// ─── P3: 核心业务 ───
const s3 = pptx.addSlide();
s3.background = { fill: C.white };
s3.addShape("rect", { x: 0, y: 0, w: 13.33, h: 0.06, fill: C.gold });
s3.addShape("rect", { x: 0, y: 7.3, w: 13.33, h: 0.2, fill: C.bg });
s3.addText("核心业务板块", { x: 0.8, y: 0.4, w: 8, h: 0.8, fontSize: 22, fontFace: "Microsoft YaHei", bold: true, color: C.bg });
s3.addShape("rect", { x: 0.8, y: 1.2, w: 2, h: 0.04, fill: C.gold });

const biz = [
  ["经济责任审计", "任中·离任·自然资源"],
  ["专项资金审计", "社保·营养餐等"],
  ["预算执行审计", "部门预算·财政收支"],
  ["招投标审计", "串标围标检测"],
  ["预算绩效管理", "目标·监控·评价"],
  ["工程全过程咨询", "预算·评审·结算"],
  ["财政评审与结算", "投资评审·决算"],
];

biz.forEach((b, i) => {
  const row = Math.floor(i / 4);
  const col = i % 4;
  const cx = 0.8 + col * 3.1;
  const cy = 1.8 + row * 2.5;
  s3.addShape("roundRect", { x: cx, y: cy, w: 2.8, h: 2.1, fill: C.light, rectRadius: 0.08 });
  s3.addShape("rect", { x: cx, y: cy, w: 0.08, h: 2.1, fill: C.bg });
  s3.addText(b[0], { x: cx + 0.3, y: cy + 0.2, w: 2.3, h: 0.7, fontSize: 12, fontFace: "Microsoft YaHei", bold: true, color: C.bg });
  s3.addText(b[1], { x: cx + 0.3, y: cy + 1.0, w: 2.3, h: 0.7, fontSize: 10, fontFace: "SimSun", color: C.gray });
});

s3.addText("审计 + 工程咨询 · 双轮驱动  |  12大业务线全覆盖", { x: 0.8, y: 7.0, w: 11, h: 0.3, fontSize: 9, color: C.gray, align: "center" });
s3.addText("3/3", { x: 11.5, y: 7.3, w: 1.5, h: 0.2, fontSize: 8, color: C.white, align: "right" });

// ─── Save ───
const out = "C:\\Users\\scrccpa\\Desktop\\bruce-pptx-test.pptx";
pptx.writeFile({ fileName: out }).then(() => {
  const stat = fs.statSync(out);
  console.log("OK:", out);
  console.log("Size:", (stat.size / 1024).toFixed(1), "KB");
  console.log("Slides:", pptx.slides.length);
});