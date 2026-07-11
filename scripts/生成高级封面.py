import os
import sys

# Windows 编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from seedream import generate_image

# 高级配色方案参考
PREMIUM_PROMPTS = {
    "深海蓝金": "Premium corporate cover design, deep ocean blue gradient background with subtle gold leaf accents, minimalist luxury aesthetic, soft lighting, elegant geometric patterns, matte texture, professional consulting report style, sophisticated and refined, high-end business presentation, 16:9, ultra high quality",
    
    "曜石黑金": "Luxury black obsidian background with champagne gold metallic lines, premium consulting firm cover, dark mode elegant design, subtle light rays, marble texture undertone, high-end financial audit report aesthetic, sophisticated business style, 16:9, photorealistic quality",
    
    "鎏金墨绿": "Premium dark emerald green with flowing gold ink brush strokes, Chinese ink painting fusion modern corporate design, jade texture background, luxury consulting report cover, sophisticated cultural aesthetic, professional and refined, 16:9, cinematic lighting",
    
    "极简留白": "Ultra minimalist cover design, pristine white background with single elegant gold line art, generous white space, Swiss design aesthetic, premium typography layout, subtle shadow gradients, professional consulting document, understated luxury, 16:9, clean and modern",
    
    "星空科技": "Dark navy cosmic background with constellation patterns, subtle nebula gradients, holographic silver geometric accents, futuristic corporate design, premium tech consulting aesthetic, sophisticated and mysterious, high-end business presentation, 16:9, ultra detailed"
}

print("=" * 60)
print("融策封面高级配色生成器")
print("=" * 60)
print("\n可选高级方案：")
for i, (name, prompt) in enumerate(PREMIUM_PROMPTS.items(), 1):
    print(f"{i}. {name}")

print("\n生成全部 5 种方案...")

output_dir = "D:/openclaw-workspace/output/premium_covers"
os.makedirs(output_dir, exist_ok=True)

for i, (name, prompt) in enumerate(PREMIUM_PROMPTS.items(), 1):
    print(f"\n生成 [{name}] ...")
    try:
        result = generate_image(
            prompt=prompt,
            size="2K",
            download_dir=output_dir
        )
        if "data" in result:
            # 重命名为中文名
            original_path = result["data"][0].get("local_path", "")
            if original_path and os.path.exists(original_path):
                ext = os.path.splitext(original_path)[1]
                new_name = f"{i:02d}_{name}{ext}"
                new_path = os.path.join(output_dir, new_name)
                os.rename(original_path, new_path)
                print(f"  ✅ 已保存: {new_path}")
        else:
            print(f"  ⚠️ 生成失败: {result.get('error', 'unknown')}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

print(f"\n{'='*60}")
print(f"全部生成完成！查看目录: {output_dir}")
print(f"{'='*60}")
