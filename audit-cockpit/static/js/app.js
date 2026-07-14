/* 融策审计驾驶舱 — 交互脚本 */
document.addEventListener('DOMContentLoaded', function() {
  // 自动刷新数据（每60秒）
  setInterval(updateKPI, 60000);
});

async function updateKPI() {
  try {
    const resp = await fetch('/api/project');
    const data = await resp.json();
    document.querySelector('.project-status').textContent = data.status;
  } catch(e) {
    console.log('KPI refresh failed');
  }
}
