"""
智析Agent · 一键数据采集器 v1.0
===========================
浏览器端专业数据采集工具
- 连接信息保存为Profile，一次配置，反复使用
- 一键采集数据库全部数据
- 实时进度显示
- 支持MySQL/PostgreSQL/SQLite/SQL Server/Oracle
"""
import sys
import json
import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, Response
from sqlalchemy import create_engine, inspect, text, MetaData

app = Flask(__name__)

# 配置路径：开发模式用源码目录，打包后用 exe 所在目录
def _get_base_dir():
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，数据放在 exe 同级目录
        return os.path.dirname(sys.executable)
    else:
        # 开发模式：用当前脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _get_base_dir()
PROFILES_FILE = os.path.join(BASE_DIR, "profiles", "connections.json")
COLLECTED_DIR = os.path.join(BASE_DIR, "collected_data")
os.makedirs(os.path.join(BASE_DIR, "profiles"), exist_ok=True)
os.makedirs(COLLECTED_DIR, exist_ok=True)

# 采集状态（内存中）
collection_status = {"running": False, "progress": 0, "current": "", "log": []}

# ============================================================
# HTML 模板（单文件，无外部依赖）
# ============================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>智析Agent · 一键数据采集器</title>
<style>
:root {
  --bg: #0f1923;
  --card: #1a2736;
  --accent: #2196F3;
  --green: #4CAF50;
  --orange: #FF9800;
  --red: #f44336;
  --text: #e0e0e0;
  --muted: #78909C;
  --border: #263545;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: 'Microsoft YaHei', -apple-system, sans-serif; background: var(--bg); color: var(--text); height:100vh; overflow:hidden; }
.app { display:flex; height:100vh; }

/* 左侧边栏 */
.sidebar { width:280px; background: var(--card); border-right:1px solid var(--border); display:flex; flex-direction:column; flex-shrink:0; }
.sidebar-header { padding:20px; border-bottom:1px solid var(--border); }
.sidebar-header h2 { font-size:16px; color:#fff; margin-bottom:4px; }
.sidebar-header .ver { font-size:11px; color:var(--muted); }
.profile-list { flex:1; overflow-y:auto; padding:12px; }
.profile-item { background:#15202b; border:1px solid var(--border); border-radius:8px; padding:12px; margin-bottom:8px; cursor:pointer; transition: all 0.2s; }
.profile-item:hover { border-color: var(--accent); }
.profile-item.active { border-color: var(--accent); background: #1a2940; }
.profile-item .name { font-size:14px; font-weight:600; color:#fff; }
.profile-item .info { font-size:11px; color:var(--muted); margin-top:4px; }
.profile-item .badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:10px; margin-top:6px; }
.badge-mysql { background: #00758f; color:#fff; }
.badge-pg { background: #336791; color:#fff; }
.badge-ora { background: #f80000; color:#fff; }
.badge-mssql { background: #CC2927; color:#fff; }
.badge-sqlite { background: #003B57; color:#fff; }
.sidebar-footer { padding:12px; border-top:1px solid var(--border); }
.btn { display:block; width:100%; padding:10px 16px; border:none; border-radius:6px; font-size:13px; font-family:inherit; cursor:pointer; text-align:center; transition: all 0.2s; }
.btn-add { background: transparent; border:1px dashed var(--border); color:var(--muted); }
.btn-add:hover { border-color: var(--accent); color: var(--accent); }
.btn-delete { background: transparent; color: var(--red); font-size:11px; padding:4px 8px; display:inline; margin-top:6px; border:1px solid transparent; border-radius:4px; }
.btn-delete:hover { border-color: var(--red); }

/* 主区域 */
.main { flex:1; display:flex; flex-direction:column; overflow-y:auto; padding:24px 32px; }
.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.topbar h1 { font-size:22px; color:#fff; }
.status-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
.status-dot.connected { background:var(--green); box-shadow:0 0 6px var(--green); }
.status-dot.disconnected { background:var(--muted); }

/* 连接面板 */
.panel { background: var(--card); border-radius:10px; padding:24px; margin-bottom:20px; border:1px solid var(--border); }
.panel h3 { font-size:14px; color:var(--muted); margin-bottom:16px; text-transform:uppercase; letter-spacing:1px; }
.form-row { display:flex; gap:12px; margin-bottom:12px; flex-wrap:wrap; }
.form-group { display:flex; flex-direction:column; flex:1; min-width:140px; }
.form-group label { font-size:11px; color:var(--muted); margin-bottom:4px; text-transform:uppercase; }
.form-group input, .form-group select { padding:8px 12px; border:1px solid var(--border); border-radius:6px; background:#15202b; color:var(--text); font-size:13px; font-family:inherit; }
.form-group input:focus, .form-group select:focus { outline:none; border-color: var(--accent); }
.form-group select { cursor:pointer; }

/* 按钮 */
.btn-row { display:flex; gap:10px; margin-top:8px; flex-wrap:wrap; }
.btn-primary { background: var(--accent); color:#fff; font-weight:600; }
.btn-primary:hover { background: #1976D2; }
.btn-primary:disabled { background: #455a64; cursor:not-allowed; }
.btn-collect { background: linear-gradient(135deg, #4CAF50, #2E7D32); color:#fff; font-weight:700; font-size:16px; padding:14px 24px; }
.btn-collect:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(76,175,80,0.4); }
.btn-collect:disabled { background: #455a64; transform:none; box-shadow:none; cursor:not-allowed; }
.btn-test { background: transparent; border:1px solid var(--accent); color: var(--accent); }
.btn-test:hover { background: rgba(33,150,243,0.1); }

/* 进度条 */
.progress-container { margin-top:16px; display:none; }
.progress-container.show { display:block; }
.progress-bar { background: #15202b; border-radius:8px; height:24px; overflow:hidden; margin:8px 0; }
.progress-fill { background: linear-gradient(90deg, #4CAF50, #8BC34A); height:100%; border-radius:8px; transition: width 0.3s; display:flex; align-items:center; justify-content:flex-end; padding-right:8px; font-size:11px; font-weight:600; color:#fff; min-width:40px; }
.progress-text { font-size:12px; color:var(--muted); }

/* 日志区 */
.log-container { background: #0a0f14; border-radius:8px; padding:12px; max-height:200px; overflow-y:auto; font-family: 'Consolas', 'Courier New', monospace; font-size:12px; border:1px solid var(--border); }
.log-container .log-line { padding:3px 0; border-bottom:1px solid rgba(255,255,255,0.03); }
.log-line.info { color: var(--muted); }
.log-line.success { color: var(--green); }
.log-line.error { color: var(--red); }
.log-line.warning { color: var(--orange); }

/* 表格预览 */
.table-preview { margin-top:12px; }
.table-preview table { width:100%; border-collapse:collapse; font-size:12px; }
.table-preview th { background: #15202b; padding:8px; text-align:left; color:var(--accent); font-size:11px; border-bottom:1px solid var(--border); }
.table-preview td { padding:6px 8px; border-bottom:1px solid rgba(255,255,255,0.04); }
.table-preview .table-name { color: var(--green); cursor:pointer; }
.table-preview .table-name:hover { text-decoration:underline; }
.table-count { color: var(--accent); font-weight:600; }

/* 对话框 */
.modal { display:none; position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.7); z-index:999; align-items:center; justify-content:center; }
.modal.show { display:flex; }
.modal-content { background: var(--card); border-radius:12px; padding:24px; width:500px; max-height:80vh; overflow-y:auto; border:1px solid var(--border); }
.modal-content h3 { margin-bottom:16px; color:#fff; }
.modal-actions { display:flex; gap:10px; margin-top:16px; justify-content:flex-end; }

::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius:2px; }

/* 统计卡片 */
.stats { display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }
.stat-card { background: var(--card); border-radius:8px; padding:16px; flex:1; min-width:140px; border:1px solid var(--border); }
.stat-card .stat-value { font-size:24px; font-weight:700; color:#fff; }
.stat-card .stat-label { font-size:11px; color:var(--muted); margin-top:2px; }
</style>
</head>
<body>
<div class="app">
  <!-- 左侧边栏 -->
  <div class="sidebar">
    <div class="sidebar-header">
      <h2>📊 智析Agent</h2>
      <div class="ver">一键数据采集器 v1.0</div>
    </div>
    <div class="profile-list" id="profileList">
      <!-- 动态填充 -->
    </div>
    <div class="sidebar-footer">
      <button class="btn btn-add" onclick="showAddModal()">+ 新建采集任务</button>
    </div>
  </div>

  <!-- 主区域 -->
  <div class="main" id="mainArea">
    <!-- 空状态 -->
    <div id="emptyState" style="text-align:center;padding:80px 20px;">
      <div style="font-size:64px;margin-bottom:16px;">🗄️</div>
      <h2 style="color:#fff;margin-bottom:8px;">一键采集数据库数据</h2>
      <p style="color:var(--muted);margin-bottom:24px;">点击左侧「+ 新建采集任务」，配置数据库连接信息</p>
      <p style="color:var(--muted);font-size:12px;">支持 MySQL / PostgreSQL / SQL Server / Oracle / SQLite</p>
    </div>

    <!-- 有任务时显示 -->
    <div id="taskPanel" style="display:none;width:100%;">
      <div class="topbar">
        <h1 id="taskTitle">数据采集</h1>
        <span id="connStatus"></span>
      </div>

      <!-- 统计卡片 -->
      <div class="stats" id="statsRow"></div>

      <!-- 连接信息 -->
      <div class="panel" id="connPanel">
        <h3>📡 数据库连接信息</h3>
        <div id="connInfo"></div>
        <div class="btn-row" style="margin-top:12px;">
          <button class="btn btn-test" onclick="testConnection()" style="width:auto;padding:8px 20px;">🔍 测试连接</button>
          <button class="btn btn-test" onclick="previewTables()" style="width:auto;padding:8px 20px;">📋 预览表结构</button>
        </div>
        <div id="tablePreview" class="table-preview"></div>
      </div>

      <!-- 采集按钮 -->
      <div class="panel" style="text-align:center;">
        <button class="btn btn-collect" onclick="startCollection()" id="btnCollect" style="width:auto;min-width:300px;">
          ⚡ 一键采集全部数据
        </button>
        <div id="progressBox" class="progress-container">
          <div class="progress-text" id="progressLabel">准备中...</div>
          <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width:0%">0%</div>
          </div>
        </div>
      </div>

      <!-- 日志 -->
      <div class="panel">
        <h3>📝 采集日志</h3>
        <div class="log-container" id="logBox">
          <div class="log-line info">等待采集指令...</div>
        </div>
      </div>
    </div>
  </div>

  <!-- 新建对话框 -->
  <div class="modal" id="addModal">
    <div class="modal-content">
      <h3>新建采集任务</h3>
      <div class="form-group" style="margin-bottom:12px;">
        <label>任务名称</label>
        <input type="text" id="newName" placeholder="如：省财政厅" style="width:100%">
      </div>
      <div class="form-row">
        <div class="form-group"><label>数据库类型</label><select id="newType"><option value="mysql">MySQL</option><option value="postgresql">PostgreSQL</option><option value="sqlserver">SQL Server</option><option value="oracle">Oracle</option><option value="sqlite">SQLite</option></select></div>
        <div class="form-group"><label>主机地址</label><input type="text" id="newHost" placeholder="10.x.x.x"></div>
        <div class="form-group"><label>端口</label><input type="text" id="newPort" value="3306"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>数据库名</label><input type="text" id="newDB" placeholder="db_name"></div>
        <div class="form-group"><label>用户名</label><input type="text" id="newUser" placeholder="audit_read"></div>
        <div class="form-group"><label>密码</label><input type="password" id="newPass" placeholder=""></div>
      </div>
      <div class="modal-actions">
        <button class="btn" onclick="closeModal()" style="width:auto;background:transparent;color:var(--muted);border:1px solid var(--border);">取消</button>
        <button class="btn btn-primary" onclick="saveProfile()" style="width:auto;">保存任务</button>
      </div>
    </div>
  </div>
</div>

<script>
let activeProfile = null;
let profiles = {};
let eventSource = null;

// 加载Profile列表
async function loadProfiles() {
  const r = await fetch('/api/profiles');
  profiles = await r.json();
  renderProfileList();
  if (activeProfile && profiles[activeProfile]) {
    showTask(activeProfile);
  } else if (Object.keys(profiles).length > 0 && !activeProfile) {
    activeProfile = Object.keys(profiles)[0];
    showTask(activeProfile);
  }
}

function renderProfileList() {
  const list = document.getElementById('profileList');
  if (Object.keys(profiles).length === 0) {
    list.innerHTML = '<div style="text-align:center;color:var(--muted);padding:20px;font-size:12px;">暂无采集任务<br>点击下方按钮创建</div>';
    return;
  }
  const badgeMap = {mysql:'badge-mysql',postgresql:'badge-pg',oracle:'badge-ora',sqlserver:'badge-mssql',sqlite:'badge-sqlite'};
  list.innerHTML = Object.entries(profiles).map(([name, p]) => `
    <div class="profile-item ${name===activeProfile?'active':''}" onclick="selectProfile('${name}')">
      <div class="name">${name}</div>
      <div class="info">${p.db_type} | ${p.host}:${p.port}/${p.database}</div>
      <span class="badge ${badgeMap[p.db_type]||''}">${p.db_type.toUpperCase()}</span>
      <br><button class="btn-delete" onclick="event.stopPropagation();deleteProfile('${name}')">删除</button>
    </div>
  `).join('');
}

function selectProfile(name) {
  activeProfile = name;
  showTask(name);
}

async function showTask(name) {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('taskPanel').style.display = 'block';
  document.getElementById('taskTitle').textContent = name;
  const p = profiles[name];
  document.getElementById('connInfo').innerHTML = `
    <div class="form-row">
      <div class="form-group"><label>类型</label><span style="padding:6px 0;display:block">${p.db_type.toUpperCase()}</span></div>
      <div class="form-group"><label>主机</label><span style="padding:6px 0;display:block">${p.host}:${p.port}</span></div>
      <div class="form-group"><label>数据库</label><span style="padding:6px 0;display:block">${p.database}</span></div>
      <div class="form-group"><label>用户</label><span style="padding:6px 0;display:block;font-family:monospace">${p.user}</span></div>
    </div>
  `;
  renderProfileList();
  clearStats();
  checkStatus();
}

function clearStats() {
  document.getElementById('statsRow').innerHTML = '';
  document.getElementById('tablePreview').innerHTML = '';
  document.getElementById('connStatus').innerHTML = '';
}

async function testConnection() {
  if (!activeProfile) return;
  addLog('info', '正在测试连接...');
  const r = await fetch('/api/test', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name: activeProfile})
  });
  const data = await r.json();
  if (data.status === 'connected') {
    addLog('success', '连接成功！');
    document.getElementById('connStatus').innerHTML = '<span class="status-dot connected"></span>已连接';
    await previewTables();
  } else {
    addLog('error', '连接失败: ' + data.error);
    document.getElementById('connStatus').innerHTML = '<span class="status-dot disconnected"></span>连接失败';
  }
}

async function previewTables() {
  if (!activeProfile) return;
  const r = await fetch('/api/preview', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name: activeProfile})
  });
  const data = await r.json();
  if (data.error) {
    addLog('error', data.error);
    return;
  }
  document.getElementById('connStatus').innerHTML = '<span class="status-dot connected"></span>已连接';
  
  let html = `<p style="color:var(--muted);font-size:12px;margin:12px 0 8px 0;">
    📊 共 <span class="table-count">${data.tables.length}</span> 张表 | 
    总字段: ${data.total_columns} | 
    估计总行数: ${data.estimated_rows?.toLocaleString()||'N/A'}
  </p>`;
  html += '<table><thead><tr><th>表名</th><th>字段数</th><th>行数</th><th>主键</th><th>字段预览</th></tr></thead><tbody>';
  for (const t of data.tables.slice(0, 50)) {
    html += `<tr>
      <td><span class="table-name">${t.table_name}</span></td>
      <td>${t.column_count}</td>
      <td>${t.row_count?.toLocaleString()||'-'}</td>
      <td>${t.primary_key.join(', ')||'-'}</td>
      <td style="font-size:11px;color:var(--muted)">${t.columns_preview||''}</td>
    </tr>`;
  }
  html += '</tbody></table>';
  if (data.tables.length > 50) {
    html += `<p style="color:var(--muted);font-size:11px;margin-top:8px;">... 还有 ${data.tables.length - 50} 张表未显示</p>`;
  }
  
  document.getElementById('tablePreview').innerHTML = html;
  document.getElementById('statsRow').innerHTML = `
    <div class="stat-card"><div class="stat-value">${data.tables.length}</div><div class="stat-label">数据表</div></div>
    <div class="stat-card"><div class="stat-value">${data.total_columns}</div><div class="stat-label">总字段</div></div>
    <div class="stat-card"><div class="stat-value">${(data.estimated_rows||0).toLocaleString()}</div><div class="stat-label">估计总行数</div></div>
  `;
  addLog('success', `发现 ${data.tables.length} 张表`);
}

async function startCollection() {
  if (!activeProfile) return;
  const btn = document.getElementById('btnCollect');
  btn.disabled = true;
  btn.textContent = '采集中...';
  document.getElementById('progressBox').classList.add('show');
  document.getElementById('logBox').innerHTML = '';
  
  const r = await fetch('/api/collect', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name: activeProfile, output_dir: COLLECTED_DIR})
  });
  const data = await r.json();
  
  if (data.error) {
    addLog('error', '采集启动失败: ' + data.error);
    btn.disabled = false;
    btn.textContent = '⚡ 一键采集全部数据';
    return;
  }
  
  // 启动SSE监听进度
  listenProgress();
}

function listenProgress() {
  if (eventSource) eventSource.close();
  eventSource = new EventSource('/api/progress');
  eventSource.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const fill = document.getElementById('progressFill');
    const label = document.getElementById('progressLabel');
    fill.style.width = data.progress + '%';
    fill.textContent = data.progress + '%';
    label.textContent = data.current || '准备中...';
    if (data.log) {
      for (const line of data.log) {
        addLog(line.level, line.msg);
      }
    }
    if (data.progress >= 100) {
      setTimeout(() => {
        const btn = document.getElementById('btnCollect');
        btn.disabled = false;
        btn.textContent = '⚡ 一键采集全部数据';
        document.getElementById('progressLabel').textContent = '采集完成！';
        eventSource.close();
      }, 1000);
    }
  };
  eventSource.onerror = function() {
    eventSource.close();
    document.getElementById('btnCollect').disabled = false;
    document.getElementById('btnCollect').textContent = '⚡ 一键采集全部数据';
  };
}

function addLog(level, msg) {
  const box = document.getElementById('logBox');
  const time = new Date().toLocaleTimeString();
  box.innerHTML += `<div class="log-line ${level}">[${time}] ${msg}</div>`;
  box.scrollTop = box.scrollHeight;
}

async function checkStatus() {
  const r = await fetch('/api/status');
  const data = await r.json();
  if (data.collecting) {
    document.getElementById('btnCollect').disabled = true;
    document.getElementById('btnCollect').textContent = '采集中...';
    document.getElementById('progressBox').classList.add('show');
    listenProgress();
  }
}

function showAddModal() { document.getElementById('addModal').classList.add('show'); }
function closeModal() { document.getElementById('addModal').classList.remove('show'); }

async function saveProfile() {
  const name = document.getElementById('newName').value;
  if (!name) { alert('请输入任务名称'); return; }
  const data = {
    name: name,
    db_type: document.getElementById('newType').value,
    host: document.getElementById('newHost').value,
    port: parseInt(document.getElementById('newPort').value) || 3306,
    database: document.getElementById('newDB').value,
    user: document.getElementById('newUser').value,
    password: document.getElementById('newPass').value,
  };
  const r = await fetch('/api/profiles', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(data)
  });
  if (r.ok) {
    closeModal();
    activeProfile = name;
    await loadProfiles();
    showTask(name);
  }
}

async function deleteProfile(name) {
  if (!confirm('确定删除采集任务 "' + name + '" 吗？此操作不会删除已采集的数据。')) return;
  await fetch('/api/profiles/' + encodeURIComponent(name), {method:'DELETE'});
  if (activeProfile === name) activeProfile = null;
  await loadProfiles();
  if (!activeProfile) {
    document.getElementById('taskPanel').style.display = 'none';
    document.getElementById('emptyState').style.display = 'block';
  }
}

loadProfiles();
</script>
</body>
</html>"""

# ============================================================
# 配置管理
# ============================================================
def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

# ============================================================
# 数据库连接
# ============================================================
DIALECTS = {
    "mysql": "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4",
    "postgresql": "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
    "sqlite": "sqlite:///{database}",
    "sqlserver": "mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
    "oracle": "oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={database}",
}

def get_engine(profile):
    template = DIALECTS.get(profile["db_type"])
    if not template:
        return None
    conn_str = template.format(
        user=profile.get("user",""), password=profile.get("password",""),
        host=profile.get("host",""), port=profile.get("port",0),
        database=profile.get("database","")
    )
    return create_engine(conn_str, echo=False, pool_pre_ping=True)

def collect_table(engine, table_name, output_dir, dialect):
    """导出单张表到CSV"""
    import csv
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{table_name}.csv")
    
    # SQL: 兼容不同数据库的引用方式
    if dialect == "sqlite":
        tbl = f"[{table_name}]"
    elif dialect == "mysql":
        tbl = f"`{table_name}`"
    elif dialect in ("postgresql",):
        tbl = f'"{table_name}"'
    elif dialect == "mssql":
        tbl = f"[{table_name}]"
    else:
        tbl = table_name
    
    with engine.connect() as conn:
        # 先获取列名
        cols = conn.execute(text(f"SELECT * FROM {tbl} LIMIT 1"))
        col_names = list(cols.keys())
        
        # 全量导出（分段读取，防止内存溢出）
        result = conn.execute(text(f"SELECT * FROM {tbl}"))
        
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(col_names)
            count = 0
            while True:
                rows = result.fetchmany(10000)
                if not rows:
                    break
                writer.writerows(rows)
                count += len(rows)
        
        return count, filepath

# ============================================================
# API 路由
# ============================================================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, COLLECTED_DIR=COLLECTED_DIR)

@app.route("/api/profiles", methods=["GET", "POST"])
def api_profiles():
    profiles = load_profiles()
    if request.method == "POST":
        data = request.json
        name = data.pop("name")
        profiles[name] = data
        save_profiles(profiles)
        return jsonify({"ok": True})
    # 返回时去掉密码明文显示
    safe = {}
    for k, v in profiles.items():
        safe[k] = {**v, "password": "***" if v.get("password") else ""}
    return jsonify(safe)

@app.route("/api/profiles/<name>", methods=["DELETE"])
def api_delete_profile(name):
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        save_profiles(profiles)
    return jsonify({"ok": True})

@app.route("/api/test", methods=["POST"])
def api_test():
    profiles = load_profiles()
    name = request.json.get("name")
    profile = profiles.get(name)
    if not profile:
        return jsonify({"error": "任务不存在"})
    try:
        engine = get_engine(profile)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT 1")).scalar()
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)})

@app.route("/api/preview", methods=["POST"])
def api_preview():
    profiles = load_profiles()
    name = request.json.get("name")
    profile = profiles.get(name)
    if not profile:
        return jsonify({"error": "任务不存在"})
    try:
        engine = get_engine(profile)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        total_cols = 0
        total_rows = 0
        table_list = []
        
        with engine.connect() as conn:
            for t in tables[:200]:  # 最多200张表
                cols = inspector.get_columns(t)
                pk = inspector.get_pk_constraint(t)
                total_cols += len(cols)
                
                try:
                    dialect = engine.dialect.name
                    if dialect == "sqlite": s = f"SELECT COUNT(*) FROM [{t}]"
                    elif dialect == "mysql": s = f"SELECT COUNT(*) FROM `{t}`"
                    elif dialect == "postgresql": s = f'SELECT COUNT(*) FROM "{t}"'
                    else: s = f"SELECT COUNT(*) FROM {t}"
                    rows = conn.execute(text(s)).scalar()
                except:
                    rows = None
                
                if rows: total_rows += rows
                cols_preview = ", ".join(c["name"] for c in cols[:5])
                if len(cols) > 5: cols_preview += "..."
                
                table_list.append({
                    "table_name": t,
                    "column_count": len(cols),
                    "row_count": rows,
                    "primary_key": pk.get("constrained_columns", []),
                    "columns_preview": cols_preview,
                })
        
        return jsonify({
            "tables": table_list,
            "total_tables": len(table_list),
            "total_columns": total_cols,
            "estimated_rows": total_rows,
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/collect", methods=["POST"])
def api_collect():
    global collection_status
    if collection_status["running"]:
        return jsonify({"error": "已有采集任务在运行"})
    
    profiles = load_profiles()
    name = request.json.get("name")
    profile = profiles.get(name)
    if not profile:
        return jsonify({"error": "任务不存在"})
    
    output_dir = request.json.get("output_dir", COLLECTED_DIR)
    task_dir = os.path.join(output_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # 在后台线程执行采集
    collection_status = {
        "running": True, "progress": 0, "current": "连接数据库...",
        "log": [], "task_dir": task_dir
    }
    
    def _collect():
        global collection_status
        log = collection_status["log"]
        try:
            engine = get_engine(profile)
            log.append({"level": "info", "msg": "正在连接数据库..."})
            collection_status["current"] = "连接数据库..."
            
            with engine.connect() as conn:
                pass  # 测试连接
            
            dialect = engine.dialect.name
            log.append({"level": "success", "msg": f"已连接到 {dialect} 数据库"})
            
            # 获取所有表
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            total = len(tables)
            log.append({"level": "info", "msg": f"发现 {total} 张表，开始采集..."})
            
            os.makedirs(task_dir, exist_ok=True)
            total_rows = 0
            failed = []
            
            for i, table_name in enumerate(tables):
                collection_status["current"] = f"采集 {table_name} ({i+1}/{total})"
                collection_status["progress"] = int((i / total) * 100)
                
                try:
                    row_count, filepath = collect_table(engine, table_name, task_dir, dialect)
                    total_rows += row_count
                    log.append({"level": "success", "msg": f"✓ {table_name}: {row_count:,} 行"})
                except Exception as e:
                    failed.append(table_name)
                    log.append({"level": "error", "msg": f"✗ {table_name}: {str(e)[:80]}"})
            
            log.append({"level": "success", "msg": f"═" * 40})
            log.append({"level": "success", "msg": f"采集完成！共 {total - len(failed)}/{total} 张表，{total_rows:,} 行数据"})
            log.append({"level": "info", "msg": f"输出目录: {task_dir}"})
            if failed:
                log.append({"level": "warning", "msg": f"失败 {len(failed)} 张表: {', '.join(failed[:5])}"})
            
            # 保存元数据
            import json as jmod
            meta = {
                "task": name, "db_type": dialect,
                "collected_at": datetime.now().isoformat(),
                "total_tables": total, "collected": total - len(failed),
                "total_rows": total_rows, "output_dir": task_dir,
                "failed_tables": failed
            }
            with open(os.path.join(task_dir, "metadata.json"), "w", encoding="utf-8") as f:
                jmod.dump(meta, f, ensure_ascii=False, indent=2)
            
            collection_status["progress"] = 100
            collection_status["current"] = "采集完成！"
            
        except Exception as e:
            log.append({"level": "error", "msg": f"采集失败: {str(e)}"})
            collection_status["progress"] = 0
            collection_status["current"] = "失败"
        finally:
            collection_status["running"] = False
    
    threading.Thread(target=_collect, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/api/progress")
def api_progress():
    def generate():
        import json as jmod
        last_log_count = 0
        while True:
            new_logs = collection_status["log"][last_log_count:]
            last_log_count = len(collection_status["log"])
            data = {
                "progress": collection_status["progress"],
                "current": collection_status["current"],
                "running": collection_status["running"],
                "log": new_logs,
            }
            yield f"data: {jmod.dumps(data)}\n\n"
            if not collection_status["running"] and collection_status["progress"] >= 100:
                break
            time.sleep(0.5)
    return Response(generate(), mimetype="text/event-stream")

@app.route("/api/status")
def api_status():
    return jsonify({"collecting": collection_status["running"], "progress": collection_status["progress"]})

# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  智析Agent · 一键数据采集器 v1.0")
    print("=" * 50)
    print(f"  访问地址: http://127.0.0.1:5000")
    print(f"  配置文件: {PROFILES_FILE}")
    print(f"  数据目录: {COLLECTED_DIR}")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=False)
