> 从 MEMORY.md 归档 | 归档日期: 2026-06-21

### PaperBanana鐮旂┒涓庡璁″浘琛–ritic浣撶郴锛?026-05-27寤虹珛锛?- **鏉ユ簮**锛氬井淇″叕浼楀彿鏂囩珷鈫扜itHub dwzhu-pku/PaperBanana 婧愮爜娣卞害鍒嗘瀽
- **鍏抽敭婢勬竻**锛氭枃绔犲０绉?鐢熸垚SVG鐭㈤噺鍥?涓嶅噯纭€斺€擯aperBanana鐨刣iagram绠＄嚎浣跨敤鍥剧墖鐢熸垚API杈撳嚭PNG锛屼粎plot绠＄嚎鐢╩atplotlib浠ｇ爜鐢熸垚
- **鏍稿績鏋舵瀯**锛?Agent娴佹按绾匡紙Retriever鈫扨lanner鈫扴tylist鈫扸isualizer鈫扖ritic寰幆锛夛紝婧愯嚜Google Research PaperVizAgent
- **涓変釜鏈変环鍊肩殑璁捐妯″紡**锛?  1. **Critic瀹℃煡寰幆**锛氬鏌モ啋淇敼鈫掑啀鐢熸垚锛屾渶澶?杞紝4缁村害Veto Rules
  2. **Few-shot鍙傝€冮┍鍔?*锛歊etriever妫€绱㈢浉浼煎浘鈫扨lanner in-context learning
  3. **4缁村害璇勪及浣撶郴**锛欶aithfulness/Conciseness/Readability/Aesthetics锛屽悇鏈塚eto Rules
- **闆嗘垚鏂规**锛氫繚鎸乨rawio鐭㈤噺鍙紪杈戜紭鍔匡紝澶栨寕PaperBanana寮廋ritic瀹℃煡寰幆



---

### Phase 1锛欰udit Diagram Critic锛?026-05-27瀹屾垚锛?- **浜у嚭**锛?  - `skills/drawio/audit-diagram-critic/critic_prompts.py` 鈥?7缁村害瀹℃煡绯荤粺鎻愮ず璇?+ Veto Rules
  - `skills/drawio/audit-diagram-critic/style_guide.py` 鈥?瀹¤鍥捐〃椋庢牸鎸囧崡锛堥厤鑹?瀛椾綋/杩炵嚎璇箟/甯冨眬瑙勮寖锛?  - `skills/drawio/audit-diagram-critic/SKILL.md` 鈥?闆嗘垚鎶€鑳芥枃妗ｏ紙3绉嶄娇鐢ㄦā寮忥級
- **绔埌绔祴璇?*锛氫笓椤硅祫閲戞祦鍚戝浘 Round1鍙戠幇5闂鈫扲ound2鍏ㄩ儴閫氳繃
- **鍏抽敭鍙戠幇**锛氬璁′笓灞濩ritic蹇呴』棰嗗煙鍖栤€斺€?涓嬭揪"vs"鎷ㄤ粯"绛夋斂搴滄湳璇樊寮傞€氱敤Critic鏃犳硶瑕嗙洊



---

### Phase 2锛氬璁″浘琛ㄥ弬鑰冨簱 aud-bench锛?026-05-27瀹屾垚锛?- **浜у嚭**锛?  - `data/audit-bench/index.json` 鈥?22寮犲浘鐨勫畬鏁寸储寮曪紙id/绫诲瀷/鏍囬/鍥炬敞/鏍囩锛?  - `data/audit-bench/diagrams/` 鈥?22寮?drawio鍘熺敓鏂囦欢锛?澶х被鍨?  - `data/audit-bench/images/` 鈥?PNG棰勮锛?寮犲叧閿浘宸查獙璇佸彲瀵煎嚭锛?- **8澶х被鍨?*锛氳祫閲戞祦鍚戝浘(4)/缁勭粐鏋舵瀯鍥?3)/瀹¤娴佺▼鍥?4)/闂鍏崇郴鍥?3)/鐢樼壒鍥?2)/鍒跺害妗嗘灦鍥?2)/缁╂晥璇勪环鍥?2)/璧勪骇绠＄悊鍥?2)
- **鐢熸垚鏂瑰紡**锛?涓瓙浠ｇ悊骞惰锛屾€昏€楁椂~9min锛寏180k tokens
- **鐢ㄩ€?*锛歞rawio鎶€鑳紽ew-shot In-Context Learning鍙傝€冪礌鏉?- **涓嬩竴姝?*锛歅hase 3 鈥?闆嗘垚鍒癲rawio鎶€鑳斤紙鐢熸垚鈫扖ritic瀹℃煡鈫掕嚜鍔ㄨ凯浠ｄ慨鏀癸級



---

## Cocoon-AI 鍥捐〃璁捐绯荤粺鍊熼壌锛?026-05-30锛?


---

### 鏍稿績鍊熼壌
- **8鑹插璁¤涔夐厤鑹蹭綋绯?*锛氳祫閲戠豢(#27AE60)/椋庨櫓绾?#E74C3C)/鏁存敼姗?#E67E22)/鍒跺害钃?#2980B9)/娴佺▼绱?#8E44AD)/缁勭粐鐏?#7F8C8D)/鍐崇瓥閲?#F39C12)/璇佹嵁闈?#1ABC9C)
- **绠ご灞傜骇鎺у埗**锛歟dge鍏堜簬vertex娓叉煋锛岄伩鍏嶇澶寸┛閫忕粍浠舵爣绛?- **缃戞牸鑳屾櫙**锛歞rawio `grid="1" gridSize="10"`
- **绛夊瀛椾綋**锛氭妧鏈爣绛綜onsolas + 涓氬姟鏍囩Microsoft YaHei
- **鐪嬭壊璇嗘祦**锛氫笉鍚屾€ц川鐨勬祦鐢ㄤ笉鍚岄鑹茬澶达紙璧勯噾缁?鏁版嵁闈?瀹℃壒閲?闂绾級



---

### 钀藉湴
- 鉁?drawio SKILL.md 鏂板銆屽璁¤涔夐厤鑹蹭綋绯汇€?銆屽璁″浘琛ㄧ敓鎴愯鑼冦€嶇珷鑺?- 鉁?arch-diagrammer SKILL.md 鏂板銆屽璁″浘琛ㄨ璁¤鑼冦€嶇珷鑺?- 鉁?drawio Critic Mode 瀹℃煡缁村害E鏇存柊涓哄璁¤涔夐厤鑹叉鏌?- 鉁?鍒嗘瀽鏂囨。锛歚knowledge/references/Cocoon-AI鏋舵瀯鍥捐璁＄郴缁熷垎鏋?md`
- 鉁?瀛樻。鍘熸枃锛歚knowledge/references/Cocoon-AI鏋舵瀯鍥捐璁＄郴缁熷垎鏋?md`锛堝惈瀹屾暣璁捐绯荤粺鎷嗚В+瀵规瘮鍒嗘瀽+钀藉湴璁″垝锛?


---

## audit-card-generator 鎻掔敾椋庡崱鐗囩敓鎴愬櫒锛?026-05-30寤虹珛锛?


---

### 鏂规
Napkin.ai 鏃犲叕寮€API 鈫?鑷缓 Pillow 娓叉煋鏂规



---

### 涓夌妯℃澘
- `steps` 鈥?娴佺▼姝ラ锛堢珫鐗?765脳1024锛?- `checklist` 鈥?瑕佺偣娓呭崟锛堢珫鐗堬級
- `compare` 鈥?瀵规瘮鍗＄墖锛堟í鐗?1080脳864锛?


---

### 璁捐鐗瑰緛
鏆栫背鑹茶儗鏅?#f8edd7) + 鎵嬬粯椋庣嚎鏉?+ 8鑹插璁¤涔夐厤鑹?+ 鍦嗚鍗＄墖 + 缂栧彿鍦嗗湀鍥炬爣
鐢ㄦ硶锛氱紪杈?JSON 鈫?`python card_generator.py <template> <json> <output.png>`

---



---

