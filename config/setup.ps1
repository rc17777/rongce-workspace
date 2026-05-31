# OpenClaw 新电脑初始化脚本
# 用法: 以管理员身份运行 PowerShell，执行 .\setup.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  融策 OpenClaw 工作区初始化" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$WORKSPACE = "D:\openclaw-workspace"
$REPO = "https://github.com/rc17777/rongce-workspace.git"

# 1. 检查 Git
Write-Host "[1/5] 检查 Git..." -ForegroundColor Yellow
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ 未找到 Git，请先安装: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Git 已安装" -ForegroundColor Green

# 2. 克隆/更新工作区
Write-Host "[2/5] 同步工作区..." -ForegroundColor Yellow
if (Test-Path $WORKSPACE) {
    Write-Host "工作区已存在，执行 git pull..." -ForegroundColor Gray
    Set-Location $WORKSPACE
    git pull origin master
} else {
    Write-Host "克隆仓库..." -ForegroundColor Gray
    git clone $REPO $WORKSPACE
    Set-Location $WORKSPACE
}
Write-Host "✅ 工作区就绪" -ForegroundColor Green

# 3. 配置 API 密钥
Write-Host "[3/5] 配置 API 密钥..." -ForegroundColor Yellow
$envFile = Join-Path $WORKSPACE ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "创建 .env 模板文件..." -ForegroundColor Gray
    @"
# DeepSeek API Key (必填)
DEEPSEEK_API_KEY=sk-your-key-here

# 阿里云 DashScope API Key (图片分析用)
DASHSCOPE_API_KEY=sk-your-key-here

# Google Gemini API Key (可选)
GEMINI_API_KEY=your-key-here
"@ | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "⚠️  请编辑 $envFile 填入你的 API 密钥" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env 已存在，跳过" -ForegroundColor Green
}

# 4. 安装 Python 依赖
Write-Host "[4/5] 安装 Python 依赖..." -ForegroundColor Yellow
$reqFile = Join-Path $WORKSPACE "requirements.txt"
if (Test-Path $reqFile) {
    pip install -r $reqFile
    Write-Host "✅ Python 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "⚠️  requirements.txt 不存在，跳过" -ForegroundColor Yellow
}

# 5. 应用共享配置
Write-Host "[5/5] 应用 OpenClaw 共享配置..." -ForegroundColor Yellow
$configFile = Join-Path $WORKSPACE "config\openclaw-shared.yaml"
if (Get-Command openclaw -ErrorAction SilentlyContinue) {
    Write-Host "提示: 请手动执行以下命令合并配置:" -ForegroundColor Gray
    Write-Host "  openclaw config apply $configFile" -ForegroundColor White
} else {
    Write-Host "⚠️  OpenClaw 未安装，请先执行:" -ForegroundColor Yellow
    Write-Host "  npm install -g openclaw" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  初始化完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后续步骤:" -ForegroundColor White
Write-Host "  1. 编辑 $envFile 填入 API 密钥" -ForegroundColor Gray
Write-Host "  2. 执行: openclaw gateway start" -ForegroundColor Gray
Write-Host "  3. 浏览器打开: http://localhost:18789" -ForegroundColor Gray
