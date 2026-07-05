import json
import time
import os
from pathlib import Path

# 配置路径
WORKSPACE_CONFIG = Path(r"D:\openclaw-workspace\models.json")
CORRECT_API_KEY = "sk-4253399e4b624bee87b2b248d80731f7"

def fix_config():
    """修复工作区配置中的环境变量引用"""
    if not WORKSPACE_CONFIG.exists():
        print(f"✅ {time.strftime('%H:%M:%S')} 工作区配置不存在")
        return False
    
    try:
        with open(WORKSPACE_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查DeepSeek配置
        if 'deepseek' in config.get('providers', {}):
            current_key = config['providers']['deepseek'].get('apiKey', '')
            
            if current_key == 'DEEPSEEK_API_KEY':
                print(f"⚠️  {time.strftime('%H:%M:%S')} 检测到环境变量引用，正在修复...")
                
                # 修复为硬编码密钥
                config['providers']['deepseek']['apiKey'] = CORRECT_API_KEY
                
                with open(WORKSPACE_CONFIG, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {time.strftime('%H:%M:%S')} 已修复，需要重启Gateway")
                return True
            else:
                print(f"✅ {time.strftime('%H:%M:%S')} 工作区配置正常")
                return False
    except Exception as e:
        print(f"❌ {time.strftime('%H:%M:%S')} 错误: {e}")
        return False

if __name__ == '__main__':
    print("=== OpenClaw 工作区配置自动修复工具 ===")
    print("监控路径:", WORKSPACE_CONFIG)
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            if fix_config():
                print("   请手动执行: openclaw gateway restart")
                print()
            
            time.sleep(30)  # 每30秒检查一次
    except KeyboardInterrupt:
        print("\n监控已停止")
