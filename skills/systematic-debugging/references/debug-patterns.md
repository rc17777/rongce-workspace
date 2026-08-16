# Common Debug Patterns

## Node.js Issues

| Symptom | Root Cause | Fix |
|:--------|:-----------|:----|
| `SyntaxError: Unexpected token` in JSON | 中文字符编码损坏/截断 | 用文件替代inline JSON传参 |
| `Module not found` | npm包未安装 | `npm install pkg` |
| `DOMMatrix is not defined` | Node.js缺乏DOM API | 用`@napi-rs/canvas`替代浏览器canvas |
| `canvas.toBuffer is not a function` | 旧版canvas API | 用`@napi-rs/canvas` |
| `signal SIGKILL` process | 超时或资源不足 | 增加timeout，减少内存使用 |

## Python Issues

| Symptom | Root Cause | Fix |
|:--------|:-----------|:----|
| `DLL load failed: 找不到指定的程序` | numpy C扩展不兼容Python alpha版 | 降级Python或升numpy |
| `ModuleNotFoundError` 安装成功但import失败 | 多环境冲突 | 检查`sys.path`和pip对应的python |
| `ImportError: cannot import name 'X'` | 版本依赖冲突 | `pip install pkg==compatible_version` |

## Data Issues

| Symptom | Root Cause | Fix |
|:--------|:-----------|:----|
| 中文变成乱码 `锟斤拷` | 编码不匹配 | `fs.readFileSync(path, 'utf-8')` 或指定编码 |
| JSON parse失败 | BOM头或不可见字符 | `str.replace(/^\uFEFF/, '')` |
| xlsx读取出错 | 多sheet / 保护视图 | 确认sheet名，用`readFile` + `sheet_to_json` |
| 数字变成科学计数法 | Excel格式问题 | 用`{raw:true}`选项读取 |

## Process/System Issues

| Symptom | Root Cause | Fix |
|:--------|:-----------|:----|
| `openclaw skill` 不存在 | 命令拼写 | 用 `openclaw skills`（带s） |
| `openclaw xxx` 卡住 | 网络/超时 | `Ctrl+C` 重试或加timeout |
| PowerShell中文传参乱码 | 编码问题 | 用临时文件代替命令行参数 |
| `which` 不存在 | Windows无which | 用 `Get-Command cmd` |
