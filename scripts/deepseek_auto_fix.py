import json
import time
import os
import subprocess
from pathlib import Path

# 配置
WORKSPACE_CONFIG = Path(r"D:\openclaw-workspace\models.json")
CORRECT_API_KEY = "sk-4253399e4b624bee87b2b248d80731f7"
CHECK_INTERVAL = 5  # 每5秒检查一次

def fix_config():
    """修复工作区配置"""
    if not WORKSPACE_CONFIG.exists():
        return False
    
    try:
        with open(WORKSPACE_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'deepseek' not in config.get('providers', {}):
            return False
        
        current_key = config['providers']['deepseek'].get('apiKey', '')
        
        # 如果是环境变量引用，修复为硬编码
        if current_key == 'DEEPSEEK_API_KEY':
            print(f"[{time.strftime('%H:%M:%S')}] 检测到环境变量引用，正在修复...")
            
            config['providers']['deepseek']['apiKey'] = CORRECT_API_KEY
            
            with open(WORKSPACE_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"[{time.strftime('%H:%M:%S')}] 已修复为硬编码密钥")
            
            # 重启Gateway
            try:
                subprocess.run(['openclaw', 'gateway', 'restart'], 
                             capture_output=True, timeout=10)
                print(f"[{time.strftime('%H:%M:%S')}] Gateway已重启")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Gateway重启失败: {e}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("DeepSeek 配置自动修复服务")
    print("=" * 60)
    print(f"监控路径: {WORKSPACE_CONFIG}")
    print(f"检查间隔: {CHECK_INTERVAL}秒")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    print()
    
    fix_count = 0
    
    try:
        while True:
            if fix_config():
                fix_count += 1
                print(f"   累计修复次数: {fix_count}")
                print()
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n服务已停止（累计修复 {fix_count} 次）")
