import os, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Admin\.openclaw\workspace\skills\guizang-ppt'
tmpl_path = os.path.join(base, 'assets', 'template-swiss.html')
out_path = os.path.join(base, 'index.html')

slides = '''
<!-- PAGE 1: Cover -->
<section class="slide accent" data-animate="hero">
  <div class="canvas-card">
    <canvas class="ascii-bg" aria-hidden="true"></canvas>
    <div class="chrome-min">
      <div class="l">融策数字审计 · Rongce Audit</div>
      <div class="r">SS · 26.05.31 · 01 / 08</div>
    </div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr auto;gap:2.6vh">
      <div data-anim="kicker" class="t-meta" style="color:rgba(255,255,255,.78);letter-spacing:.22em">DATA DRIVEN · AUDIT TRANSFORMED</div>
      <h1 data-anim="title" style="align-self:center;font-family:var(--sans),var(--sans-zh);font-weight:200;font-size:min(8vw,14vh);line-height:1.05;letter-spacing:-.025em;color:#fff">
        审计数字化<br><span style="font-style:italic;font-weight:300">实战方法论</span>
      </h1>
      <div data-anim="bottom" style="display:grid;grid-template-rows:auto auto;gap:1.6vh;border-top:1px solid rgba(255,255,255,.22);padding-top:2vh">
        <div data-anim="lead" class="lead" style="max-width:52ch;color:rgba(255,255,255,.86);font-weight:300">融策会计师事务所 · 从数据审计到智能决策的完整路径</div>
        <div style="display:flex;justify-content:space-between;align-items:end">
          <div class="t-meta" style="color:rgba(255,255,255,.6)">融策左护法 · 2026</div>
          <div class="t-meta" style="color:rgba(255,255,255,.6)">-> swipe / arrow keys</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PAGE 2: Challenge -->
<section class="slide" data-animate="">
  <div class="canvas-card">
    <header class="chrome-min">
      <div class="l">SITUATION</div>
      <div class="r">02 / 08</div>
    </header>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto auto 1fr;gap:3vh">
      <div data-anim="kicker" class="t-meta" style="letter-spacing:.22em">PROBLEM · 核心矛盾</div>
      <h2 data-anim="title" class="h-xl-zh" style="font-weight:200">中小事务所的数字化鸿沟</h2>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2vw">
        <div class="card-ink" style="padding:2.4vh 1.6vw;display:flex;flex-direction:column;gap:1.2vh">
          <span style="font-weight:200;font-size:min(3vw,3.2rem);color:var(--accent)">40%</span>
          <span style="font-weight:500;font-size:14px;line-height:1.5">政府审计业务占比<br><span style="font-weight:300;font-size:12px;opacity:.6">通过政府采购中标获取</span></span>
        </div>
        <div class="card-ink" style="padding:2.4vh 1.6vw;display:flex;flex-direction:column;gap:1.2vh">
          <span style="font-weight:200;font-size:min(3vw,3.2rem);color:var(--accent)">10人</span>
          <span style="font-weight:500;font-size:14px;line-height:1.5">团队规模<br><span style="font-weight:300;font-size:12px;opacity:.6">1名合伙人 + 9名助理</span></span>
        </div>
        <div class="card-ink" style="padding:2.4vh 1.6vw;display:flex;flex-direction:column;gap:1.2vh">
          <span style="font-weight:200;font-size:min(3vw,3.2rem);color:var(--accent)">3年</span>
          <span style="font-weight:500;font-size:14px;line-height:1.5">新人成长周期<br><span style="font-weight:300;font-size:12px;opacity:.6">经验锁在资深人员身上</span></span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PAGE 3: 4-layer Framework -->
<section class="slide accent" data-animate="">
  <div class="canvas-card">
    <header class="chrome-min">
      <div class="l" style="color:rgba(255,255,255,.6)">FRAMEWORK</div>
      <div class="r" style="color:rgba(255,255,255,.6)">03 / 08</div>
    </header>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr;gap:3vh">
      <div data-anim="kicker" class="t-meta" style="color:rgba(255,255,255,.5);letter-spacing:.22em">DATA-DRIVEN DECISION · 四层闭环架构</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1.5vw">
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding-top:2vh;border-top:3px solid var(--accent-bright)">
          <div class="t-meta" style="color:var(--accent-bright);margin-bottom:.8vh">LAYER 1</div>
          <div style="color:#fff;font-weight:500;font-size:1.2vw">数据采集</div>
          <div style="font-weight:300;font-size:13px;opacity:.7;line-height:1.5;color:rgba(255,255,255,.8)">业务数据·行为数据·环境数据·历史数据 全域采集</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding-top:2vh;border-top:3px solid var(--accent-bright)">
          <div class="t-meta" style="color:var(--accent-bright);margin-bottom:.8vh">LAYER 2</div>
          <div style="color:#fff;font-weight:500;font-size:1.2vw">数据治理</div>
          <div style="font-weight:300;font-size:13px;opacity:.7;line-height:1.5;color:rgba(255,255,255,.8)">清洗去噪·格式统一·分类归档 数据质量决定决策质量</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding-top:2vh;border-top:3px solid var(--accent-bright)">
          <div class="t-meta" style="color:var(--accent-bright);margin-bottom:.8vh">LAYER 3</div>
          <div style="color:#fff;font-weight:500;font-size:1.2vw">分析研判</div>
          <div style="font-weight:300;font-size:13px;opacity:.7;line-height:1.5;color:rgba(255,255,255,.8)">深度拆解 区分表象与本质 建立数据与业务问题的关联</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding-top:2vh;border-top:3px solid var(--accent-bright)">
          <div class="t-meta" style="color:var(--accent-bright);margin-bottom:.8vh">LAYER 4</div>
          <div style="color:#fff;font-weight:500;font-size:1.2vw">决策迭代</div>
          <div style="font-weight:300;font-size:13px;opacity:.7;line-height:1.5;color:rgba(255,255,255,.8)">落地执行 新数据反馈 修正方案 持续闭环迭代</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PAGE 4: Blind Spots -->
<section class="slide" data-animate="">
  <div class="canvas-card">
    <header class="chrome-min">
      <div class="l">AUDIT BLIND SPOTS</div>
      <div class="r">04 / 08</div>
    </header>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto auto 1fr auto;gap:2vh">
      <div data-anim="kicker" class="t-meta" style="letter-spacing:.22em">COMPREHENSIVE CHECKLIST</div>
      <h2 data-anim="title" class="h-xl-zh" style="font-weight:200">审计10大盲区速查</h2>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.2vh 3vw;padding-top:1vh">
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">01</span><span style="font-size:14px;font-weight:400">合同之外隐形交易</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">02</span><span style="font-size:14px;font-weight:400">长期挂账/小金库</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">03</span><span style="font-size:14px;font-weight:400">电子数据与系统日志</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">04</span><span style="font-size:14px;font-weight:400">临时机构专项小组</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">05</span><span style="font-size:14px;font-weight:400">非核心边缘业务</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">06</span><span style="font-size:14px;font-weight:400">离职/外包人员管控</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">07</span><span style="font-size:14px;font-weight:400">沉默证据缺失记录</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">08</span><span style="font-size:14px;font-weight:400">隐蔽关联交易</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">09</span><span style="font-size:14px;font-weight:400">费用报销灰色地带</span></div>
        <div style="display:flex;gap:.8vw;align-items:center"><span class="t-meta" style="font-size:10px;color:var(--accent);min-width:24px">10</span><span style="font-size:14px;font-weight:400">制度执行最后一公里</span></div>
      </div>
      <div class="t-meta" style="text-align:center;padding-top:1vh;border-top:1px solid var(--border-subtle)">来源：内审人生 · 已整合进 rongce-gov-audit skill</div>
    </div>
  </div>
</section>

<!-- PAGE 5: Deep Research -->
<section class="slide accent" data-animate="">
  <div class="canvas-card">
    <header class="chrome-min">
      <div class="l" style="color:rgba(255,255,255,.6)">RESEARCH METHODOLOGY</div>
      <div class="r" style="color:rgba(255,255,255,.6)">05 / 08</div>
    </header>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto auto 1fr;gap:2vh">
      <div data-anim="kicker" class="t-meta" style="color:rgba(255,255,255,.5)">THREE-MODE ADAPTIVE</div>
      <h2 data-anim="title" class="h-xl-zh" style="font-weight:200;color:#fff">三档自适应研究体系</h2>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2vw">
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding:2.4vh 1.6vw;background:rgba(255,255,255,.06)">
          <span style="font-weight:200;font-size:min(2.5vw,2rem);color:var(--accent-bright)">Light</span>
          <span class="t-meta" style="color:rgba(255,255,255,.5)">5页决策备忘</span>
          <span style="font-weight:300;font-size:13px;opacity:.7;color:rgba(255,255,255,.8)">6步 · 无图 · 30分钟<br>日常快决策、内部备忘</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding:2.4vh 1.6vw;background:rgba(255,255,255,.06)">
          <span style="font-weight:200;font-size:min(2.5vw,2rem);color:var(--accent-bright)">Medium</span>
          <span class="t-meta" style="color:rgba(255,255,255,.5)">10-15页分析</span>
          <span style="font-weight:300;font-size:13px;opacity:.7;color:rgba(255,255,255,.8)">8步+质量门 · 3-8张图 · 1-2h<br>部门汇报、专题研究</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding:2.4vh 1.6vw;background:rgba(255,255,255,.06)">
          <span style="font-weight:200;font-size:min(2.5vw,2rem);color:var(--accent-bright)">Heavy</span>
          <span class="t-meta" style="color:rgba(255,255,255,.5)">1.5万字旗舰</span>
          <span style="font-weight:300;font-size:13px;opacity:.7;color:rgba(255,255,255,.8)">11步+多LLM · 20+图 · 半日<br>战略规划、对外发布</span>
        </div>
      </div>
      <div style="display:flex;gap:2vw;padding-top:1vh;border-top:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.6);font-size:13px">
        <span><span style="font-weight:500">质量门6维度</span>: 事实/单位/引用/连贯/论证/语言</span>
        <span><span style="font-weight:500">多LLM</span>: Claude写+GPT-5核验+DeepSeek润色</span>
      </div>
    </div>
  </div>
</section>

<!-- PAGE 6: Skill Library -->
<section class="slide" data-animate="">
  <div class="canvas-card">
    <header class="chrome-min">
      <div class="l">SKILL ECOSYSTEM</div>
      <div class="r">06 / 08</div>
    </header>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto auto 1fr;gap:2vh">
      <div data-anim="kicker" class="t-meta" style="letter-spacing:.22em">CAPABILITIES · 能力体系</div>
      <h2 data-anim="title" class="h-xl-zh" style="font-weight:200">融策技能库 · 90+技能生态</h2>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2vw">
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding:2vh 1.6vw;border-top:1px solid var(--border-subtle)">
          <div class="t-meta" style="color:var(--accent)">审计工具 · 17个</div>
          <ul style="list-style:none;padding:0;margin:0;font-weight:300;font-size:13px;line-height:1.8;opacity:.7">
            <li>audit-data-analyst</li>
            <li>rongce-gov-audit</li>
            <li>audit-benford / watchdog</li>
            <li>bid-collusion-audit</li>
          </ul>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding:2vh 1.6vw;border-top:1px solid var(--border-subtle)">
          <div class="t-meta" style="color:var(--accent)">研究方法 · 8个</div>
          <ul style="list-style:none;padding:0;margin:0;font-weight:300;font-size:13px;line-height:1.8;opacity:.7">
            <li>deep-research / analysis-report</li>
            <li>forecast-simulation</li>
            <li>cnki-* 学术链(8个)</li>
          </ul>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2vh;padding:2vh 1.6vw;border-top:1px solid var(--border-subtle)">
          <div class="t-meta" style="color:var(--accent)">文档设计 · 10+个</div>
          <ul style="list-style:none;padding:0;margin:0;font-weight:300;font-size:13px;line-height:1.8;opacity:.7">
            <li>word-cn-format</li>
            <li>guizang-ppt (归藏)</li>
            <li>writing-polish</li>
            <li>khazix-writer</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PAGE 7: Case Study -->
<section class="slide accent" data-animate="">
  <div class="canvas-card">
    <header class="chrome-min">
      <div class="l" style="color:rgba(255,255,255,.6)">CASE STUDY</div>
      <div class="r" style="color:rgba(255,255,255,.6)">07 / 08</div>
    </header>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto auto 1fr;gap:2vh">
      <div data-anim="kicker" class="t-meta" style="color:rgba(255,255,255,.5)">PRACTICE · 实战案例</div>
      <h2 data-anim="title" class="h-xl-zh" style="font-weight:200;color:#fff">金川医保 · 525万条数据</h2>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:3vw">
        <div style="display:flex;flex-direction:column;gap:2vh">
          <div style="font-weight:300;font-size:14px;line-height:1.7;color:rgba(255,255,255,.8)">
            240MB .xltx -> Excel COM SaveAs -> pandas分块读取<br>
            525万行x111列 · 30秒完成全量分析
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1vh">
            <div style="background:rgba(255,255,255,.06);padding:2vh 1.6vw">
              <span style="font-weight:200;font-size:min(2.5vw,2.2rem);color:var(--accent-bright)">2,393</span>
              <div style="font-weight:300;font-size:13px;color:rgba(255,255,255,.7)">分解住院检出</div>
            </div>
            <div style="background:rgba(255,255,255,.06);padding:2vh 1.6vw">
              <span style="font-weight:200;font-size:min(2.5vw,2.2rem);color:var(--accent-bright)">1,812</span>
              <div style="font-weight:300;font-size:13px;color:rgba(255,255,255,.7)">进销存异常品种</div>
            </div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.5vh;justify-content:center">
          <div style="background:rgba(255,255,255,.08);padding:3vh 2vw;font-style:italic;font-weight:300;font-size:1.3vw;color:rgba(255,255,255,.9)">很不错，帮了大忙</div>
          <div class="t-meta" style="color:rgba(255,255,255,.5)">-- 融策平头哥</div>
          <div style="display:flex;gap:1vw;flex-wrap:wrap;margin-top:.5vh">
            <span class="t-meta" style="color:var(--accent-bright);font-size:10px;padding:3px 10px;border:1px solid rgba(255,255,255,.2)">P0 5个</span>
            <span class="t-meta" style="color:var(--accent-bright);font-size:10px;padding:3px 10px;border:1px solid rgba(255,255,255,.2)">P1 4个</span>
            <span class="t-meta" style="color:var(--accent-bright);font-size:10px;padding:3px 10px;border:1px solid rgba(255,255,255,.2)">P2 8个</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PAGE 8: Closing -->
<section class="slide accent" data-animate="hero">
  <div class="canvas-card" style="justify-content:center;align-items:center;text-align:center">
    <div class="t-meta" style="color:rgba(255,255,255,.5);margin-bottom:4vh">DATA DRIVEN · AUDIT TRANSFORMED</div>
    <h1 style="font-family:var(--sans),var(--sans-zh);font-weight:200;font-size:min(5vw,8vh);color:#fff;line-height:1.2">AI让执行变快了<br><span style="color:var(--accent-bright)">但什么是好的</span><br>这个判断还得靠人</h1>
    <div style="margin-top:5vh;border-top:1px solid rgba(255,255,255,.18);padding-top:2vh;display:flex;justify-content:center;gap:3vw">
      <div class="t-meta" style="color:rgba(255,255,255,.5)">融策左护法 · 2026</div>
      <div class="t-meta" style="color:rgba(255,255,255,.5)" style="color:rgba(255,255,255,.5)">SKILL IS CONTAINER · EXPERTISE IS CONTENT</div>
    </div>
  </div>
</section>
'''

# Replace placeholder
new_html = tmpl.replace('SLIDES_HERE', slides.strip())
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'Generated: {out_path}')
print(f'Size: {len(new_html)} chars')
print(f'Slides inserted: {len(slides.strip())} chars')
