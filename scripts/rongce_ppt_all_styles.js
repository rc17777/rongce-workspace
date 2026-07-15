const pptxgen = require("pptxgenjs");
const fs = require("fs");

// ─── 6套风格配色 ───
const STYLES = {
  "华为方案": {
    slide: { w: 10, h: 5.625 },
    C: { primary:"0D2B4B", secondary:"0074CC", accent:"C5955C", light:"EEF5FB", bg:"FFFFFF", text:"1A1A1A", muted:"5C5C5C", border:"C9DFF0", accentLight:"FFF5E5" },
    desc: "政企客户提案 · 解决方案汇报",
  },
  "麦肯锡蓝": {
    slide: { w: 10, h: 5.625 },
    C: { primary:"1B3A5C", secondary:"2B6CB0", accent:"E8A838", light:"EBF4FF", bg:"FFFFFF", text:"2D3748", muted:"718096", border:"CBD5E0", accentLight:"FFFAF0" },
    desc: "战略汇报 · 管理层提案 · 咨询报告",
  },
  "苹果极简": {
    slide: { w: 10, h: 5.625 },
    C: { primary:"000000", secondary:"0071E3", accent:"86868B", light:"F5F5F7", bg:"FFFFFF", text:"1D1D1F", muted:"86868B", border:"D2D2D7", accentLight:"F0F0F0" },
    desc: "产品发布 · 品牌故事 · Vision演讲",
  },
  "PitchDeck": {
    slide: { w: 10, h: 5.625 },
    C: { primary:"1A365D", secondary:"2B6CB0", accent:"ED8936", light:"F7FAFC", bg:"FFFFFF", text:"1A202C", muted:"718096", border:"E2E8F0", accentLight:"FFFAF0" },
    desc: "融资路演 · 商业计划 · 产品Roadmap",
  },
  "数据分析": {
    slide: { w: 10, h: 5.625 },
    C: { primary:"2C3E50", secondary:"3498DB", accent:"E74C3C", light:"F8F9FA", bg:"FFFFFF", text:"2D3748", muted:"718096", border:"CBD5E0", accentLight:"FEF2F2" },
    desc: "数据报告 · 指标Review · 分析汇报",
  },
  "暗黑科技": {
    slide: { w: 10, h: 5.625 },
    C: { primary:"0A0A0A", secondary:"00C9A7", accent:"4FC3F7", light:"1A1A2E", bg:"0D1117", text:"E0E0E0", muted:"888888", border:"333333", accentLight:"0A1929" },
    desc: "发布会 · 技术展示 · AI能力秀",
  },
};

const STYLE_NAMES = Object.keys(STYLES);

function generateAll() {
  STYLE_NAMES.forEach((name, si) => {
    const cfg = STYLES[name];
    const C = cfg.C;
    const W = cfg.slide.w;
    const H = cfg.slide.h;

    const pptx = new pptxgen();
    pptx.defineLayout({ name: "CUSTOM", width: W, height: H });
    pptx.layout = "CUSTOM";

    // ─── Helpers ───
    function addTitle(slide, tag, title) {
      slide.addShape("rect", { x: 0, y: 0, w: W, h: 0.78, fill: C.primary });
      slide.addShape("rect", { x: 0, y: 0, w: 0.68, h: 0.78, fill: C.accent });
      if (tag) slide.addText(tag, { x: 0, y: 0, w: 0.68, h: 0.78, fontSize: 11, fontFace: "Arial", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
      slide.addText(title, { x: 0.82, y: 0, w: 8.8, h: 0.78, fontSize: 20, fontFace: "Microsoft YaHei", color: "FFFFFF", bold: true, align: "left", valign: "middle", margin: 0 });
      slide.addShape("rect", { x: 0, y: 0.78, w: W, h: 0.04, fill: C.accent });
    }

    function pageBadge(slide, n) {
      slide.addShape("rect", { x: 9.1, y: 5.15, w: 0.6, h: 0.35, fill: C.accent });
      slide.addText(String(n), { x: 9.1, y: 5.15, w: 0.6, h: 0.35, fontSize: 10, fontFace: "Arial", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
    }

    function richCard(slide, x, y, w, h, num, title, tagline, features, detail, hl) {
      const bc = hl ? C.accent : C.secondary;
      const bg = hl ? C.accentLight : C.light;
      slide.addShape("rect", { x, y, w, h, fill: bg, line: { color: C.border, width: 0.5 } });
      slide.addShape("rect", { x, y, w, h: 0.06, fill: bc });
      slide.addShape("oval", { x: x + 0.16, y: y + 0.18, w: 0.44, h: 0.44, fill: bc });
      slide.addText(String(num), { x: x + 0.16, y: y + 0.18, w: 0.44, h: 0.44, fontSize: 14, fontFace: "Arial Black", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
      slide.addText(title, { x: x + 0.72, y: y + 0.12, w: w - 0.85, h: 0.32, fontSize: 13, fontFace: "Microsoft YaHei", color: hl ? C.accent : C.primary, bold: true, align: "left", valign: "middle", margin: 0 });
      if (tagline) slide.addText(tagline, { x: x + 0.72, y: y + 0.44, w: w - 0.85, h: 0.22, fontSize: 9, fontFace: "Microsoft YaHei", color: bc, align: "left", valign: "middle", margin: 0 });
      slide.addShape("line", { x: x + 0.14, y: y + 0.74, w: w - 0.28, h: 0, line: { color: C.border, width: 0.5 } });
      (features || []).slice(0, 4).forEach((f, i) => {
        const fy = y + 0.84 + i * 0.38;
        slide.addShape("rect", { x: x + 0.16, y: fy + 0.1, w: 0.1, h: 0.1, fill: bc });
        slide.addText(f, { x: x + 0.32, y: fy, w: w - 0.48, h: 0.38, fontSize: 10, fontFace: "Microsoft YaHei", color: C.text, align: "left", valign: "middle", margin: 0 });
      });
      if (detail) {
        const fy = y + h - 0.5;
        slide.addShape("rect", { x: x + 0.14, y: fy, w: w - 0.28, h: 0.4, fill: "FFFFFF", line: { color: C.border, width: 0.3 } });
        slide.addShape("rect", { x: x + 0.14, y: fy, w: 0.05, h: 0.4, fill: C.muted });
        slide.addText(detail, { x: x + 0.24, y: fy, w: w - 0.42, h: 0.4, fontSize: 8, fontFace: "Microsoft YaHei", color: C.muted, align: "left", valign: "middle", margin: 0 });
      }
    }

    function kpiCard(slide, x, y, w, h, val, label, desc, useGold) {
      const bc = useGold ? C.accent : C.secondary;
      slide.addShape("rect", { x, y, w, h, fill: useGold ? C.accentLight : C.light, line: { color: useGold ? C.accent : C.border, width: 0.5 } });
      slide.addShape("rect", { x, y, w, h: 0.06, fill: bc });
      slide.addText(val, { x: x + 0.08, y: y + 0.12, w: w - 0.16, h: 0.7, fontSize: 36, fontFace: "Arial Black", color: bc, bold: true, align: "center", valign: "middle", margin: 0 });
      slide.addText(label, { x: x + 0.08, y: y + 0.88, w: w - 0.16, h: 0.3, fontSize: 11, fontFace: "Microsoft YaHei", color: C.primary, bold: true, align: "center", margin: 0 });
      if (desc) slide.addText(desc, { x: x + 0.08, y: y + 1.2, w: w - 0.16, h: 0.28, fontSize: 8, fontFace: "Microsoft YaHei", color: C.muted, align: "center", margin: 0 });
    }

    // ─── P1: Cover ───
    const s1 = pptx.addSlide();
    s1.background = { fill: C.bg };
    s1.addShape("rect", { x: 0, y: 0, w: 4.4, h: H, fill: C.primary });
    s1.addShape("rect", { x: 4.4, y: 0, w: 0.06, h: H, fill: C.accent });
    s1.addShape("rect", { x: 0, y: 4.4, w: 4.4, h: 1.225, fill: C.secondary });
    s1.addShape("rect", { x: 0.4, y: 1.0, w: 1.0, h: 0.06, fill: C.accent });
    s1.addText("专业服务能力展示", { x: 0.4, y: 1.14, w: 3.6, h: 0.3, fontSize: 11, fontFace: "Microsoft YaHei", color: C.light, align: "left", margin: 0 });
    s1.addText("四川融策\n会计师事务所", { x: 0.4, y: 1.5, w: 3.6, h: 2.0, fontSize: 26, fontFace: "Microsoft YaHei", color: "FFFFFF", bold: true, align: "left", valign: "top", margin: 0, lineSpaceMult: 1.3 });
    s1.addText("政府审计 | 绩效评价 | 工程咨询", { x: 0.4, y: 3.6, w: 3.6, h: 0.5, fontSize: 11, fontFace: "Microsoft YaHei", color: C.light, align: "left", margin: 0 });
    s1.addText("2026", { x: 0.4, y: 4.55, w: 3.6, h: 0.3, fontSize: 10, fontFace: "Microsoft YaHei", color: "FFFFFF", align: "left", margin: 0 });
    s1.addText("专业 · 诚信 · 高效", { x: 4.7, y: 0.6, w: 5.0, h: 0.7, fontSize: 18, fontFace: "Microsoft YaHei", color: C.primary, bold: true, align: "left", valign: "middle", margin: 0 });
    s1.addShape("rect", { x: 4.7, y: 1.4, w: 1.2, h: 0.04, fill: C.accent });
    s1.addText("值得信赖的审计服务伙伴", { x: 4.7, y: 1.5, w: 5.0, h: 0.5, fontSize: 12, fontFace: "Microsoft YaHei", color: C.muted, align: "left", margin: 0 });
    [ { val: "300+", label: "服务客户" }, { val: "50+", label: "专业团队" }, { val: "800+", label: "服务项目" } ].forEach((m, i) => {
      const cx = 4.7 + i * 1.65;
      s1.addShape("rect", { x: cx, y: 2.3, w: 1.5, h: 1.5, fill: C.light, line: { color: C.border, width: 0.5 } });
      s1.addShape("rect", { x: cx, y: 2.3, w: 1.5, h: 0.06, fill: i === 0 ? C.accent : C.secondary });
      s1.addText(m.val, { x: cx + 0.06, y: 2.4, w: 1.38, h: 0.7, fontSize: 30, fontFace: "Arial Black", color: i === 0 ? C.accent : C.secondary, bold: true, align: "center", valign: "middle", margin: 0 });
      s1.addText(m.label, { x: cx + 0.06, y: 3.2, w: 1.38, h: 0.5, fontSize: 11, fontFace: "Microsoft YaHei", color: C.primary, bold: true, align: "center", valign: "middle", margin: 0 });
    });
    s1.addShape("rect", { x: 4.7, y: 4.55, w: 5.0, h: 0.62, fill: C.light });
    s1.addShape("rect", { x: 4.7, y: 4.55, w: 0.06, h: 0.62, fill: C.accent });
    s1.addText("双业务线协同 · 会计师事务所 + 工程咨询公司", { x: 4.82, y: 4.55, w: 4.8, h: 0.62, fontSize: 11, fontFace: "Microsoft YaHei", color: C.primary, align: "left", valign: "middle", margin: 0 });

    // ─── P2: 公司概览 ───
    const s2 = pptx.addSlide(); s2.background = { fill: C.bg };
    addTitle(s2, "01", "公司概览");
    s2.addText("四川融策会计师事务所主营政府审计业务，涵盖绩效评价、资产清查、专项债申报、监督检查等财政职能；四川融策工程咨询公司主营预算编制、财政评审、全过程工程咨询与工程结算。", { x: 0.4, y: 1.05, w: 9.2, h: 1.2, fontSize: 11, fontFace: "Microsoft YaHei", color: C.text, align: "left", margin: 0, lineSpaceMult: 1.5 });
    [ { val: "300+", label: "服务客户", desc: "覆盖政府与企事业单位" }, { val: "50+", label: "专业团队", desc: "注册会计师+工程师" }, { val: "800+", label: "服务项目", desc: "12年行业经验积累" } ].forEach((m, i) => {
      kpiCard(s2, 0.4 + i * 3.15, 2.5, 2.85, 1.6, m.val, m.label, m.desc, i === 0);
    });
    s2.addText("双业务线协同 · 会计师事务所 + 工程咨询公司", { x: 0.4, y: 4.3, w: 9.2, h: 0.3, fontSize: 10, fontFace: "Microsoft YaHei", color: C.muted, align: "center", margin: 0 });
    pageBadge(s2, 2);

    // ─── P3: 核心业务 (TOC) ───
    const s3 = pptx.addSlide(); s3.background = { fill: C.bg };
    s3.addShape("rect", { x: 0, y: 0, w: 2.0, h: H, fill: C.primary });
    s3.addShape("rect", { x: 2.0, y: 0, w: 0.07, h: H, fill: C.accent });
    s3.addText("业务体系", { x: 0.1, y: 1.8, w: 1.8, h: 0.65, fontSize: 24, fontFace: "Microsoft YaHei", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
    s3.addText("SERVICES", { x: 0.1, y: 2.5, w: 1.8, h: 0.28, fontSize: 9, fontFace: "Arial", color: C.light, align: "center", margin: 0 });
    s3.addShape("rect", { x: 0.55, y: 1.6, w: 0.9, h: 0.05, fill: C.accent });
    ["经济责任审计","专项资金审计","预算执行审计","招投标审计","预算绩效管理","工程全过程咨询","财政评审与结算"].forEach((ch, i) => {
      const cy = 0.35 + i * 0.7;
      s3.addShape("oval", { x: 2.3, y: cy + 0.13, w: 0.4, h: 0.4, fill: C.accent });
      s3.addText(String(i + 1).padStart(2, "0"), { x: 2.3, y: cy + 0.13, w: 0.4, h: 0.4, fontSize: 11, fontFace: "Arial Black", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
      s3.addText(ch, { x: 2.88, y: cy, w: 6.5, h: 0.65, fontSize: 14, fontFace: "Microsoft YaHei", color: C.primary, bold: true, align: "left", valign: "middle", margin: 0 });
      if (i < 6) s3.addShape("line", { x: 2.3, y: cy + 0.65, w: 7.2, h: 0, line: { color: C.border, width: 0.4 } });
    });
    pageBadge(s3, 3);

    // ─── P4: 审计业务线 ───
    const s4 = pptx.addSlide(); s4.background = { fill: C.bg };
    addTitle(s4, "02", "政府审计业务线");
    [{n:1,t:"绩效评价",tag:"事前·事中·事后",f:["覆盖财政支出评价","项目支出绩效评价","政策评价全链条"],d:"全过程绩效管理"},{n:2,t:"资产清查",tag:"账实核对",f:["固定资产全面盘点","往来款专项清理","专项资金清理"],d:"全流程资产管理工作"},{n:3,t:"专项债申报",tag:"规划·评审",f:["项目规划与方案编制","评审对接与沟通","资金使用全程监管"],d:"全过程专项债咨询"},{n:4,t:"监督检查",tag:"财政·会计",f:["财政监督检查","会计信息质量检查","内部控制评价"],d:"助力规范财政管理"}].forEach((c,i)=>{richCard(s4,0.4+i*2.35,1.05,2.15,3.9,c.n,c.t,c.tag,c.f,c.d,i===0);});
    pageBadge(s4, 4);

    // ─── P5: 典型案例 ───
    const s5 = pptx.addSlide(); s5.background = { fill: C.bg };
    addTitle(s5, "03", "典型案例");
    [{cl:"某市财政局",tg:"绩效评价",st:"50+项目·3亿资金",dt:["完成财政支出绩效评价50余项","涉及教育、社保、农业等领域","提出整改建议200余条"]},{cl:"某交通局",tg:"资产清查",st:"2.5亿资产·20+项目",dt:["全面清查交通系统固定资产","盘活闲置资产5000余万元","建立资产管理制度体系"]},{cl:"某县审计局",tg:"经责审计",st:"15+项目·整改8000万",dt:["完成经责审计15项","发现违规资金8000余万元","推动出台3项管理制度"]}].forEach((c,i)=>{
      const cx=0.4+i*3.15;
      s5.addShape("rect",{x:cx,y:1.05,w:2.85,h:3.8,fill:C.light,line:{color:C.border,width:0.5}});
      s5.addShape("rect",{x:cx,y:1.05,w:2.85,h:0.06,fill:C.accent});
      s5.addText(c.cl,{x:cx+0.2,y:1.2,w:2.45,h:0.4,fontSize:15,fontFace:"Microsoft YaHei",color:C.primary,bold:true,align:"center",margin:0});
      s5.addShape("rect",{x:cx+0.8,y:1.65,w:1.25,h:0.35,fill:C.accent});
      s5.addText(c.tg,{x:cx+0.8,y:1.65,w:1.25,h:0.35,fontSize:9,fontFace:"Microsoft YaHei",color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
      s5.addText(c.st,{x:cx+0.2,y:2.1,w:2.45,h:0.35,fontSize:11,fontFace:"Microsoft YaHei",color:C.secondary,bold:true,align:"center",margin:0});
      c.dt.forEach((d,j)=>{s5.addShape("rect",{x:cx+0.25,y:2.55+j*0.4,w:0.08,h:0.08,fill:C.secondary});s5.addText(d,{x:cx+0.4,y:2.5+j*0.4,w:2.2,h:0.35,fontSize:10,fontFace:"Microsoft YaHei",color:C.text,align:"left",valign:"middle",margin:0});});
    });
    pageBadge(s5, 5);

    // ─── P6: 关键数据 ───
    const s6 = pptx.addSlide(); s6.background = { fill: C.bg };
    addTitle(s6, "04", "关键数据");
    s6.addText("800+", { x: 0.4, y: 1.2, w: 9.2, h: 1.5, fontSize: 60, fontFace: "Arial Black", color: C.accent, bold: true, align: "center", valign: "middle", margin: 0 });
    s6.addText("累计服务项目", { x: 0.4, y: 2.7, w: 9.2, h: 0.4, fontSize: 14, fontFace: "Microsoft YaHei", color: C.primary, bold: true, align: "center", margin: 0 });
    s6.addShape("line", { x: 4, y: 3.3, w: 2, h: 0, line: { color: C.accent, width: 1 } });
    [{val:"92%",label:"客户续约率"},{val:"50人+",label:"专业团队"},{val:"30个",label:"覆盖市县"}].forEach((m,i)=>{kpiCard(s6,0.4+i*3.15,3.6,2.85,1.5,m.val,m.label,"",i===0);});
    pageBadge(s6, 6);

    // ─── P7: 质量保障 ───
    const s7 = pptx.addSlide(); s7.background = { fill: C.bg };
    addTitle(s7, "05", "质量保障体系");
    [{n:1,t:"三级复核制",tag:"层层把关",f:["项目组自复核","部门交叉复核","质控部独立复核"],d:"确保报告零差错"},{n:2,t:"AI辅助复核",tag:"智能检查",f:["15维度智能检查系统","自动检测错别字/金额","法规引用一致性校验"],d:"提升复核效率"},{n:3,t:"法规数据库",tag:"实时更新",f:["13,000+审计法规","覆盖审计法/会计法等","智能化法规匹配检索"],d:"确保法规引用准确"},{n:4,t:"客户满意度",tag:"持续改进",f:["98%客户好评率","12年持续服务经验","定期回访与改进"],d:"以客户为中心"}].forEach((c,i)=>{richCard(s7,0.4+i*2.35,1.05,2.15,3.9,c.n,c.t,c.tag,c.f,c.d,i===0);});
    pageBadge(s7, 7);

    // ─── P8: 企业使命 ───
    const s8 = pptx.addSlide(); s8.background = { fill: C.primary };
    s8.addShape("rect", { x: 0, y: 0, w: W, h: 0.06, fill: C.accent });
    s8.addShape("rect", { x: 0, y: H - 0.06, w: W, h: 0.06, fill: C.accent });
    s8.addText("以专业审计服务\n助力政府治理现代化", { x: 1, y: 1.2, w: 8, h: 2.2, fontSize: 30, fontFace: "Microsoft YaHei", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0, lineSpaceMult: 1.4 });
    s8.addShape("rect", { x: 4, y: 3.5, w: 2, h: 0.06, fill: C.accent });
    ["专业立身","诚信为本","高效服务"].forEach((v, i) => {
      const cx = 1.5 + i * 3.2;
      s8.addShape("rect", { x: cx, y: 3.8, w: 2.2, h: 0.55, fill: C.accent });
      s8.addText(v, { x: cx, y: 3.8, w: 2.2, h: 0.55, fontSize: 14, fontFace: "Microsoft YaHei", color: C.primary, bold: true, align: "center", valign: "middle", margin: 0 });
    });
    s8.addText("SICHUAN RONGCE CPA FIRM", { x: 1, y: 4.6, w: 8, h: 0.4, fontSize: 11, fontFace: "Arial", color: C.light, align: "center", margin: 0 });
    pageBadge(s8, 8);

    // ─── P9: 工程咨询 ───
    const s9 = pptx.addSlide(); s9.background = { fill: C.bg };
    addTitle(s9, "06", "全过程工程咨询");
    s9.addText("从预算编制到工程结算，覆盖项目建设全生命周期，以专业能力为政府投资项目保驾护航。", { x: 0.4, y: 1.05, w: 9.2, h: 0.8, fontSize: 12, fontFace: "Microsoft YaHei", color: C.text, align: "left", margin: 0, lineSpaceMult: 1.4 });
    [{n:1,t:"预算编制",tag:"投资估算·概算·预算",f:["投资估算编制","设计概算审核","施工图预算"]},{n:2,t:"财政评审",tag:"预算评审·控制价",f:["预算评审","招标控制价编制","评审报告"]},{n:3,t:"全过程咨询",tag:"跟踪审计·变更管理",f:["跟踪审计服务","进度款审核","变更与签证管理"]},{n:4,t:"工程结算",tag:"结算审核·决算",f:["结算审核","竣工决算编制","决算报告"]}].forEach((c,i)=>{richCard(s9,0.4+i*2.35,2.0,2.15,3.0,c.n,c.t,c.tag,c.f,null,i===0);});
    pageBadge(s9, 9);

    // ─── P10: 联系我们 ───
    const s10 = pptx.addSlide(); s10.background = { fill: C.primary };
    s10.addShape("rect", { x: 0, y: 0, w: W, h: 0.06, fill: C.accent });
    s10.addShape("rect", { x: 0, y: H - 0.06, w: W, h: 0.06, fill: C.accent });
    s10.addText("联系我们", { x: 1, y: 0.8, w: 8, h: 0.8, fontSize: 28, fontFace: "Microsoft YaHei", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
    s10.addShape("rect", { x: 4.2, y: 1.7, w: 1.6, h: 0.05, fill: C.accent });
    s10.addText("四川融策 · 与您同行", { x: 1, y: 2.0, w: 8, h: 0.5, fontSize: 14, fontFace: "Microsoft YaHei", color: C.light, align: "center", margin: 0 });
    s10.addText("无论您是政府部门还是企事业单位，融策都将以专业、诚信、高效的服务，为您提供最优质的审计与工程咨询解决方案。", { x: 1, y: 2.5, w: 8, h: 0.8, fontSize: 11, fontFace: "Microsoft YaHei", color: C.light, align: "center", margin: 0, lineSpaceMult: 1.4 });
    [{l:"公司地址",v:"四川省成都市高新区"},{l:"联系电话",v:"028-XXXXXXX"},{l:"电子邮箱",v:"rongce@rongcecpa.com"},{l:"官方网站",v:"www.rongcecpa.com"}].forEach((m,i)=>{const cx=0.4+i*2.4;s10.addText(m.l,{x:cx,y:3.6,w:2.2,h:0.4,fontSize:12,fontFace:"Microsoft YaHei",color:C.accent,bold:true,align:"center",margin:0});s10.addText(m.v,{x:cx,y:4.0,w:2.2,h:0.4,fontSize:11,fontFace:"Microsoft YaHei",color:"FFFFFF",align:"center",margin:0});});
    pageBadge(s10, 10);

    // ─── Save ───
    const out = `C:\\Users\\scrccpa\\Desktop\\融策业务能力展示_${name}.pptx`;
    pptx.writeFile({ fileName: out }).then(() => {
      const stat = fs.statSync(out);
      console.log(`✅ ${name.padEnd(8)} | ${(stat.size/1024).toFixed(1).padStart(5)}KB | ${pptx.slides.length}页 | ${cfg.desc}`);
    });
  });
}

generateAll();