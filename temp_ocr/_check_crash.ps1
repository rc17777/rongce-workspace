# encoding: utf-8
import subprocess, json, sys
sys.stdout.reconfigure(encoding='utf-8')
ps = r'''
$evts = Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error'} -MaxEvents 30 -ErrorAction SilentlyContinue | Where-Object { $_.TimeCreated -gt (Get-Date).AddHours(-5) }
foreach ($e in $evts) {
    Write-Host ("--- " + $e.TimeCreated.ToString('MM-dd HH:mm:ss'))
    Write-Host $e.Message.Substring(0, [Math]::Min(300, $e.Message.Length))
}
'''
r = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
print(r.stdout)
if r.stderr:
    print('STDERR:', r.stderr[:500])
