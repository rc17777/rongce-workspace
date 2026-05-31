# 审计案例多源采集脚本 v2
# 每周五运行：审计署各地动态 + 省级审计厅案例
$STORE_DIR = "C:\Users\Admin\AuditKB\raw\projects"
$LAST_FETCH = "C:\Users\Admin\AuditKB\raw\last-fetch-record.json"
New-Item -ItemType Directory -Force -Path $STORE_DIR | Out-Null

Write-Host "=== 审计案例多源采集 [$(Get-Date -Format "yyyy-MM-dd HH:mm")] ==="

# 1. 上次记录
$record = @{}
if (Test-Path $LAST_FETCH) {
    $json = Get-Content $LAST_FETCH -Encoding UTF8 -Raw
    try { $record = ConvertFrom-Json $json } catch { $record = @{} }
}
$lastIds = @()
if ($record.last_article_ids) { $lastIds = @($record.last_article_ids) }
Write-Host "上次采集: $($record.last_fetch_date)"
Write-Host "已存文章: $($lastIds.Count) 篇"

# 2. 数据源配置
$sources = @(
    @{name="审计署-各地动态"; url="https://www.audit.gov.cn/n4/n20/n524/index.html"; base="https://www.audit.gov.cn"}
    @{name="海南审计厅-案件披露"; url="https://audit.hainan.gov.cn/ywdt/ajpl/"; base="https://audit.hainan.gov.cn"}
)

$allNew = 0
$currentIds = [System.Collections.ArrayList]@($lastIds)
$regex = [regex]::new("href=`"([^`"]*c(\d+)/content\.html)`"\s+target=_blank\s+title=`"([^`"]*)`"")

foreach ($src in $sources) {
    Write-Host ("--- [" + $src.name + "] ---")
    try {
        $resp = Invoke-WebRequest -Uri $src.url -TimeoutSec 15 -UseBasicParsing
    } catch {
        Write-Host ("  [跳过] " + $_)
        continue
    }
    
    $matches = $regex.Matches($resp.Content)
    $articles = @()
    $seen = @{}
    foreach ($m in $matches) {
        $cid = $m.Groups[2].Value
        if ($seen.ContainsKey($cid)) { continue }
        $seen[$cid] = $true
        $href = $m.Groups[1].Value -replace "\.\./\.\./\.\./", ($src.base + "/")
        $articles += @{id=($src.name + "_" + $cid); url=$href; title=$m.Groups[3].Value.Trim(); source=$src.name}
    }
    Write-Host ("  文章 " + $articles.Count + " 篇")
    
    $newArts = $articles | Where-Object { $_.id -notin $lastIds }
    Write-Host ("  新增 " + $newArts.Count + " 篇")
    
    $cnt = 0
    foreach ($art in $newArts) {
        if ($cnt -ge 5) { Write-Host "  ... 上限5篇，剩余跳过"; break }
        Write-Host ("  [下载] " + $art.title)
        try { $r = Invoke-WebRequest -Uri $art.url -TimeoutSec 15 -UseBasicParsing } catch { continue }
        
        $bodyMatch = [regex]::Match($r.Content, "<div class=`"article-con`"[^>]*>(.*?)</div>\s*<!--end component", "Singleline")
        if (-not $bodyMatch.Success) {
            $bodyMatch = [regex]::Match($r.Content, "<div class=`"TRS_Editor`"[^>]*>(.*?)</div>", "Singleline")
            if (-not $bodyMatch.Success) {
                $bodyMatch = [regex]::Match($r.Content, "<div class=`"article`"[^>]*>(.*?)</div>", "Singleline")
            }
        }
        $bodyText = if ($bodyMatch.Success) { $bodyMatch.Groups[1].Value -replace "<[^>]+>", "" } else { "(正文提取失败)" }
        if ($bodyText.Length -gt 2000) { $bodyText = $bodyText.Substring(0, 2000) }
        
        $safeName = $art.title -replace "[^\w\u4e00-\u9fff]", ""
        if ($safeName.Length -gt 25) { $safeName = $safeName.Substring(0, 25) }
        $filename = ($art.id -replace ':', '-') + "_" + $safeName + ".md"
        $filepath = Join-Path $STORE_DIR $filename
        $now = Get-Date -Format "yyyy-MM-dd HH:mm"
        
        "# " + $art.title | Out-File -FilePath $filepath -Encoding UTF8
        "> 来源：" + $art.source | Out-File -FilePath $filepath -Encoding UTF8 -Append
        "> 原文链接：" + $art.url | Out-File -FilePath $filepath -Encoding UTF8 -Append
        "> 采集时间：" + $now | Out-File -FilePath $filepath -Encoding UTF8 -Append
        "" | Out-File -FilePath $filepath -Encoding UTF8 -Append
        $bodyText | Out-File -FilePath $filepath -Encoding UTF8 -Append
        
        Write-Host ("  [保存] " + $filepath)
        $null = $currentIds.Add($art.id)
        $cnt++
        $allNew++
    }
}

# 3. 更新记录
@{ last_fetch_date = Get-Date -Format "yyyy-MM-dd HH:mm"; last_article_ids = @($currentIds) } | ConvertTo-Json | Out-File -FilePath $LAST_FETCH -Encoding UTF8

Write-Host ""
Write-Host ("=== 完成 === 新增 " + $allNew + " 篇，累计 " + $currentIds.Count + " 篇")