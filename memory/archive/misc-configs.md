> 从 MEMORY.md 归档 | 归档日期: 2026-06-21

## Git 鑷姩鍚屾锛?026-05-28 閰嶇疆锛?
- **浠撳簱**: `https://github.com/rc17777/rongce-workspace.git` (绉佹湁)
- **绛栫暐**: 鈶?姣忔閲嶈鎿嶄綔鍚庢墜鍔?commit+push 鈶?cron 姣?灏忔椂鑷姩宸℃鎺ㄩ€?- **蹇界暐**: `output/`, `projects/`, `secrets/`, `.env`, `temp/` 绛夛紙瑙?.gitignore锛?- **瑙﹀彂**: 鐢ㄦ埛瑕佹眰鑷姩鎺ㄩ€?


---

## OpenRouter 鍏嶈垂妯″瀷鐩戞帶锛?026-06-10寤虹珛锛?


---

### 閮ㄧ讲缁勪欢
| 缁勪欢 | 璺緞 | 璇存槑 |
|------|------|------|
| 鐩戞帶鑴氭湰 | `scripts/openrouter_monitor.py` | 璋傾PI鈫掑姣斿揩鐓р啋杈撳嚭鍙樺寲 |
| 妯″瀷娴嬭瘯 | `scripts/openrouter_test_models.py` | 閫愪釜妯″瀷杩為€氭€ч獙璇?|
| 鍩哄噯蹇収 | `config/openrouter_free_models.json` | 27涓厤璐规ā鍨嬪揩鐓?|
| 娴嬭瘯鎶ュ憡 | `output/openrouter_free_models_report.md` | 13鍙敤/7闄愭祦/4澶辫触/3璺宠繃 |
| 瀹氭椂浠诲姟 | cron `0 */3 * * *` | 姣?灏忔椂妫€鏌ュ厤璐规ā鍨嬪彉鍖?|
| HEARTBEAT | HEARTBEAT.md | 蹇冭烦鏃堕『鎵嬫鏌?|



---

### API Key
- 宸查厤缃湪 `openclaw.json` env.vars.OPENROUTER_API_KEY
- 鍏紑 API 鏃犻渶 Key锛欸ET /api/v1/models锛堣幏鍙栨ā鍨嬪垪琛級
- 鑱婂ぉ闇€ Key锛歅OST /api/v1/chat/completions



---

### 鎺ㄨ崘澶囪儙妯″瀷锛圖eepSeek 涓嶅彲鐢ㄦ椂锛?1. `nvidia/nemotron-3-super-120b-a12b:free` 鈥?120B/1M ctx/鏈€蹇?1196ms)
2. `openai/gpt-oss-120b:free` 鈥?OpenAI寮€婧?120B/131K ctx
3. `google/gemma-4-31b-it:free` 鈥?Google澶氭ā鎬?262K ctx



---

### 娉ㄦ剰
- 鍏嶈垂妯″瀷 list 鏄叕寮€鐨勶紝浣?chat 闇€瑕?API Key
- 鐑棬鍏嶈垂妯″瀷(Qwen3/Llama/Kimi)鎸佺画429闄愭祦鈫掗渶鍏呭€?1+鎻愪紭鍏堢骇
- Lyria 鏄煶涔愮敓鎴愭ā鍨嬶紝涓嶈兘褰撴枃鏈ā鍨嬬敤
- 宸茬‘璁ゅ彲鐢?3涓紝璇﹁ output/openrouter_free_models_report.md


---

