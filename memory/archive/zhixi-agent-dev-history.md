> 从 MEMORY.md 归档 | 归档日期: 2026-06-21

## 鏅烘瀽Agent 绔彛鍐茬獊涓庝慨澶嶏紙2026-06-01锛?


---

### 鏍瑰洜
绔彛5001琚涓狿ython杩涚▼鎶㈠崰锛?- Desktop鍓湰 `铻嶇瓥鏅鸿兘浣?`锛堜笉瀹屾暣锛屽凡鍒犻櫎锛?- zhixi-v2锛堢鍙?002锛岀嫭绔嬮」鐩級
- data-analysis-agent锛堟纭増鏈紝绔彛5001锛?
鐪嬮棬鐙楋紙watchdog.ps1锛夊彧妫€娴嬬鍙ｅ崰鐢ㄤ笉妫€娴嬪崰鐢ㄨ€?鈫?閿欒杩涚▼鎶㈠崰5001 鈫?鐢ㄦ埛鐪嬪埌鏃犲搧鐗岀殑鍘熷鐗堟湰銆?


---

### 淇
1. `api/system.py` 鈥?PROTECTED闆嗕粠5椤光啋18椤癸紝闃叉鑷姩鏇存柊瑕嗙洊铻嶇瓥瀹氬埗鏂囦欢
2. `requirements.txt` 鈥?琛ヤ笂waitress+pymupdf+pytesseract+scikit-learn绛?涓己澶变緷璧?3. 鏉€鎺夋墍鏈夐潪workspace Python杩涚▼锛岄噸鍚痙ata-analysis-agent
4. 鍒犻櫎Desktop涓嶅畬鏁村壇鏈?`铻嶇瓥鏅鸿兘浣?`



---

### 璁″垝浠诲姟
- `\鏅烘瀽Agent宸℃` 鈥?姣忓皬鏃舵鏌?001
- `\鏅烘瀽Agent寮€鏈哄惎鍔╜ 鈥?寮€鏈虹櫥褰曞惎鍔?


---

### audit-plugin v3.1 鏇存柊锛堝悓鏃ワ級
鍩轰簬銆岃姰鍚煚璇淬€嶆枃绔犳洿鏂颁笁涓妧鑳?鈫?璇﹁ audit-plugin/README.md



---

### 鍙︿竴鍙版満鍣ㄩ儴缃茶鐐?- 鍒犻櫎 .venv 閲嶅缓锛坧yvenv.cfg纭紪鐮佷簡D:\python311锛?- pip install -r requirements.txt
- 棰濆瑁?Tesseract-OCR 鏈綋锛堥潪pip鍖咃級



---

## 鏅烘瀽鏅鸿兘浣?v2.0 閲嶆瀯锛?026-06-01寤虹珛锛?


---

### 鑳屾櫙
鐢ㄦ埛鍙嶉锛氫笂浼犳枃浠剁綉缁滈敊璇€佸鍑烘寜閽笉宸ヤ綔銆佸鍑鸿川閲忎綆銆丒xcel鑻辨枃鏍囬銆備竴鏅氬畬鎴愬叏閾捐矾淇閲嶆瀯銆?


---

### 鏍稿績妯″潡
| 妯″潡 | 鏍稿績鑳藉姏 |
|------|----------|
| 鏁版嵁閲囬泦 | 9绉岲B(鍚?鍥戒骇)+API+6绉嶈储鍔¤处濂楄В鏋?|
| 鏁版嵁鏍￠獙娓呮礂 | 10鏉″唴缃鍒?瀹屾暣鎬?鎬婚噺/涓氬姟鏍￠獙寮曟搸 |
| 鏁版嵁杩佺Щ鏍囧噯鍖?| 澶氬簱杩佺Щ+5鍩熷璁℃暟鎹爣鍑?|
| 闈炵粨鏋勫寲澶勭悊 | OCR+鍚堝悓/鎷涙姇鏍?浼氳绾鑷姩鎻愬彇 |
| 瀹¤妯″瀷宸ヤ綔鍙?| 31涓猄QL妯″瀷+7澶у垎鏋愭柟娉?|
| 澶ф暟鎹垎鏋?| 璧勯噾鍥捐氨+鍥存爣缃戠粶+鏂囨湰鎸栨帢+鍙鍖?|
| 鐭ヨ瘑璧勪骇寮曟搸 | 6鎬濈淮閾?6鎻愮ず璇?12妫€鏌?10鏂规硶璁烘鏋?|



---

### 铻嶇瓥10椤硅祫浜у祵鍏?bid-document / audit-data-analysis-methods / cot-capture / prompt-librarian / agent-data-standard / audit-knowledge-graph / procurement-audit-models / digital-audit-methodology / workflow-embedder / financial-fraud-detection 鍏ㄩ儴鍐呭祵

鎵€鏈夋ā鍧楀凡閫氳繃 `test_modules.py` 鍔犺浇楠岃瘉 鉁?


---

## 鏅烘瀽Agent PyInstaller 鐙珛 EXE 鎵撳寘锛?026-06-02寤虹珛锛?


---

### 鐩爣
灏嗘櫤鏋怉gent鎵撳寘涓哄畬鍏ㄧ嫭绔嬬殑鍗曚釜EXE鏂囦欢锛屼笉渚濊禆Python鐜銆?


---

### 鏍稿績鏂规
- **鍐呭祵鏈嶅姟鍣?*锛歚desktop_standalone.py` 鈫?鍦╠aemon绾跨▼涓敤Waitress鐩存帴鍚姩Flask app锛岄伩鍏峆yInstaller EXE鍐呮棤娉曡皟鐢ㄥ瓙杩涚▼Python鐨勯棶棰?- **PyInstaller** 6.20.0 + Python 3.11.9锛坴env锛?- **EXE浜у嚭**锛歚D:\openclaw-workspace\projects\data-analysis-agent\dist\鏅烘瀽Agent.exe`锛垀166.7MB锛?- **绔彛**锛?001锛堜笉鍙橈級
- **鍚姩鏂瑰紡**锛欵dge --app 妯″紡杩炴帴 `http://127.0.0.1:5001`



---

### 鍏抽敭鏂囦欢
| 鏂囦欢 | 璺緞 |
|------|------|
| 鐙珛鍚姩鍣?| `desktop_standalone.py` |
| PyInstaller閰嶇疆 | `zhixi_agent.spec` |
| 鏈€缁圗XE | `dist\鏅烘瀽Agent.exe` |
| 宸℃鑴氭湰 | `patrol.ps1` |



---

### 瑙ｅ喅闂
1. **`ModuleNotFoundError: No module named 'http'`**锛歴pec鏂囦欢鐨別xcludes閿欒鎺掗櫎浜嗘爣鍑嗗簱`http`鍖咃紙werkzeug闇€瑕侊級锛屽凡绉婚櫎
2. **`ModuleNotFoundError: No module named 'email'`**锛氬悓鐞嗙Щ闄や簡閿欒鎺掗櫎
3. **绔彛5001娈嬬暀**锛氭棫Python杩涚▼鍗犵敤锛圥ID 16784骞界伒杩涚▼锛夛紝kill鍚庨噴鏀?


---

### spec鏂囦欢鍏抽敭閰嶇疆
- 鍏ュ彛锛歚desktop_standalone.py`
- 鍥炬爣锛歚static/Images/rongce-logo.ico`
- 鏁版嵁鏂囦欢锛歵emplates/銆乻tatic/銆丩LM/銆丗unction/銆両nformation/
- excludes锛歚['tkinter', 'unittest', 'pydoc', 'xmlrpc', 'pkg_resources', 'setuptools']`
- 娉ㄦ剰锛氫笉鍙帓闄?`http` 鍜?`email` 鏍囧噯搴擄紒



---

### 璁″垝浠诲姟鏇存柊
- `\鏅烘瀽Agent寮€鏈哄惎鍔╜ 鈫?鐩存帴鍚姩 `鏅烘瀽Agent.exe`锛堢櫥褰曟椂锛?- `\鏅烘瀽Agent宸℃` 鈫?姣?鍒嗛挓妫€鏌ョ鍙?001锛屾棤鍝嶅簲鍒欓噸鍚疎XE



---

### 妗岄潰蹇嵎鏂瑰紡
- `$env:USERPROFILE\Desktop\鏅烘瀽Agent.lnk` 鈫?鎸囧悜 `dist\鏅烘瀽Agent.exe`



---

### 楠岃瘉缁撴灉
- 涓婁紶CSV 鈫?Excel(鍥捐〃+鍒嗘瀽+鏁版嵁) 鉁?- Word(灏侀潰+鎽樿+绔犺妭+宓屽叆鍥捐〃 192KB) 鉁?- PPT(4涓婚/灏侀潰+鐩綍+KPI+鍥捐〃+鏄庣粏+缁撴潫 144KB) 鉁?- MCP鍦ㄧ嚎 鉁?- 鏂囦欢涓嬭浇绔偣200 鉁?


---

## 铻嶇瓥Agent 涓夌瀵煎嚭绯荤粺閲嶆瀯锛?026-06-02锛?


---

### 鏈嶅姟鍣ㄧǔ瀹氭€т慨澶?1. **鏂囦欢涓婁紶宕╂簝** 鈫?Flask `app.run()` 鍗曠嚎绋?鈫?Waitress 澶氱嚎绋嬶紙8绾跨▼/300s瓒呮椂/1GB涓婁紶闄愬埗锛?2. **绔彛鍐茬獊** 鈫?3涓狿ython杩涚▼鎶㈠崰5001 鈫?缁熶竴鐢?`server.py` 绠＄悊
3. **MCP鏂繛** 鈫?debug鐑噸杞芥潃鎺塎CP瀛愯繘绋?鈫?`debug=False` 绋冲畾杩愯



---

### 鍝佺墝閲嶅懡鍚?- 鏅烘瀽Agent 鈫?**铻嶇瓥Agent**锛堝叏閮ㄦ枃浠讹細妯℃澘/i18n/JS/CSS/鍚姩淇℃伅锛?


---

### Excel 瀵煎嚭
- 鑻辨枃鍒楀悕鈫掍腑鏂囷細77椤规槧灏勮〃锛坉epartment鈫掗儴闂? amount鈫掗噾棰? debit鈫掑€熸柟閲戦锛?- 澶嶅悎璇嶆媶瑙ｏ細`total_amount` 鈫?`鍚堣閲戦`
- 鏂板"鏁版嵁姒傚喌"Sheet锛氭瘡鍒楁暟鎹被鍨?缂哄け鍊?鍞竴鍊?min/max/mean/sum
- 鏂板"鍥捐〃鍒嗘瀽"Sheet锛氳嚜鍔ㄧ敓鎴愭煴鐘跺浘/楗煎浘/瓒嬪娍鍥惧祵鍏?- 鏁版嵁Sheet锛氭潯浠惰壊闃躲€佹暟鎹潯銆佽嚜鍔ㄧ瓫閫夈€佸喕缁撹〃澶淬€佸崈鍒嗕綅



---

### Word 瀵煎嚭
- 褰诲簳閲嶆瀯锛歋SE娴佸紡AI瀵硅瘽 鈫?**鐩存帴鐢熸垚**锛堣烦杩嘇I锛?- 鏂板"鎵ц鎽樿"绔犺妭 + KPI鎸囨爣姹囨€?- 宓屽叆鍥捐〃鍥剧墖锛坢atplotlib鐢熸垚鐨凱NG锛?- 淇濈暀灏侀潰/鐩綍/绔犺妭/琛ㄦ牸鐨勫叕鏂囬/鍟嗗姟椋庢帓鐗?


---

### PPT 瀵煎嚭
- 褰诲簳閲嶆瀯锛氫粠鏃犲埌鏈夛紝python-pptx鐩存帴鐢熸垚
- **4绉嶄富棰?*锛氬晢鍔℃繁钃?/ 鎻掔敾鏄庝寒 / 鏆楅粦涓撲笟 / 鏆栨娲诲姏
- 澶氶〉缁撴瀯锛氬皝闈?鈫?鐩綍 鈫?KPI鎬昏 鈫?鍥捐〃椤?鈫?鏁版嵁鏄庣粏 鈫?缁撴潫椤?- KPI鍗＄墖甯冨眬锛堝ぇ鏁板瓧+鏍囩+缁熻锛?- 鍥捐〃宓屽叆 + 鏁版嵁琛ㄦ牸



---

### 鍥捐〃寮曟搸
- 鏂板缓 `Function/Output/chart_engine.py`
- 鑷姩妫€娴嬫暟鎹被鍨?鈫?閫夋嫨鏌辩姸鍥?楗煎浘/鎶樼嚎鍥?- 鍝佺墝閰嶈壊锛?1C355E娣辫摑涓昏壊锛?- matplotlib鐢熸垚150dpi楂樻竻PNG 鈫?宓屽叆Excel/Word/PPT



---

### 杩炵画宸ュ叿璋冪敤澶辫触淇
- `_MAX_CONSECUTIVE_ERRORS`: 3鈫?鈫?2
- SQL閿欒鑷姩闄勫甫schema淇℃伅甯姪AI鑷籂姝?- `create_analysis_table` 澶辫触涔熼檮甯chema
- 缁堟娑堟伅甯﹁缁嗘帓鏌ユ寚鍗?


---

### 鍏抽敭鏂囦欢鍙樻洿
| 鏂囦欢 | 鏀瑰姩 |
|------|------|
| `server.py` | Flask鈫扺aitress + MCP鑷姩杩炴帴 |
| `api/quick_export.py` | 瀹屽叏閲嶅啓锛圫SE鈫扟SON锛岀洿鎺ョ敓鎴愶級 |
| `Function/Output/enhanced_excel.py` | 鍥捐〃Sheet + 鏉′欢鑹查樁 + 绛涢€?|
| `Function/Output/enhanced_word.py` | 鏂板chart_images宓屽叆 |
| `Function/Output/chart_engine.py` | 鏂板缓鍥捐〃寮曟搸 |
| `agent/agent.py` | 瀹归敊12娆?+ 缁堟鎸囧崡 |
| `agent/tools_data.py` | SQL澶辫触闄剆chema |
| `templates/agent_chat.html` | 鍝佺墝/瀵煎嚭JS/PPT鍥涢鏍?|



---

## 铻嶇瓥Agent椤圭洰绠＄悊椤甸潰澧炲己锛?026-06-03锛?


---

### 鏂板涓夊ぇ妯″潡
- **馃О 宸ュ叿绠?*锛?涓璁″伐鍏凤紙SQL鏍煎紡鍖?鏁版嵁鑴辨晱/MUS鎶芥牱/灞炴€ф娊鏍?闅忔満鎶芥牱/閲戦澶у啓/鏃ユ湡璁＄畻锛?- **馃彞 椤圭洰鍋ュ悍搴︽鏌?*锛氳嚜鍔ㄦ娴嬪簳绋垮畬鎴愮巼/鏈暣鏀归棶棰?杩囨湡寰呭姙锛屽叏閮ㄦ暣鏀瑰畬姣曞缓璁綊妗?- **馃 鑷姩鐢熸垚闂**锛氳緭鍏ュ垎鏋愬彂鐜扳啋涓€閿敓鎴愰棶棰樼嚎绱?鍙栬瘉鍗?宸ヤ綔搴曠+浜ゅ弶寮曠敤



---

### 鏂板鍚庣鏂囦欢
`api/toolbox.py` `api/audit_assets.py` `api/workpaper.py` `data/integration.py`



---

### 馃敶 classList.add('') 绌哄瓧绗︿覆Bug
- 浠ｇ爜 `classList.add(section==='projects'?'active':'')` 鍦ㄩ潪椤圭洰椤垫姏DOMException
- 瀵艰嚧鎵€鏈変晶杈规爮瀵艰埅锛堝伐鍏风/宸ヤ綔搴曠/鍙栬瘉鍗?鐭ヨ瘑搴撶瓑锛夊畬鍏ㄤ笉娓叉煋
- 绫讳技浠ｇ爜妯″紡搴斿缁堢敤 `if (condition) classList.add('class')` 閬垮厤



---

### 鏁版嵁搴揝chema
8寮犺〃锛歱rojects/workpapers/evidence/issues/reports/sql_scripts/knowledge_entries/todos + cross_refs鍏宠仈琛?
---

鏈€鍚庢洿鏂? 2026-06-11



---

