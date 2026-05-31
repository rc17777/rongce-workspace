# 想打造自己的 OpenClaw？从零构建一个可记忆、可扩展、可追踪的本地 AI Agent

> 来源：微信公众号「智能体AI」| 2026-05-14 08:01 | 原创

---

## 一、文章动机

作者受够了黑盒 AI 助手——不知道它记住了多少秘密，不知道工具调用后台流转了什么数据，有的企业甚至禁止部署使用 OpenClaw。于是造出了 **AgentClaw**：核心逻辑仅约 500 行 Python，实现真正的"数据主权"——记忆是桌面上随手可改的 Markdown，技能是文件夹里拖进即用的说明书。

---

## 二、三层架构

| 层 | 技术栈 | 说明 |
|---|---|---|
| 前端 | Next.js | 对话界面，可选，没有也能用 API 跑 |
| 后端 | FastAPI (8002端口) | 处理请求、读写文件、SSE事件推送 |
| Agent运行时 | LangChain | 决策→调工具→拿结果→循环 |

Agent 运行时的工作方式：拿到问题 → 决定用哪个工具 → 调用工具 → 拿到结果 → 再决定下一步 → 直到给出最终回答。整个过程是一个循环，不是一次性的。

---

## 三、核心设计：System Prompt 拼装

每次对话开始，后端把 **6 个本地 Markdown 文件** 拼成完整 System Prompt：

```
SKILLS_SNAPSHOT.md  ← 告诉 Agent「你会什么」
SOUL.md             ← 性格和语气设定
IDENTITY.md         ← 自我认知（它知道自己在哪里运行）
USER.md             ← 你是谁，你的背景信息
AGENTS.md           ← 行为准则，包含技能调用协议
MEMORY.md           ← 长期记忆，你告诉它的一切
```

全部是本地文本文件，用 VS Code 或记事本随时可以打开改。Agent 的「大脑」不是云端黑盒，而是桌面上几个文本文件。

---

## 四、技能系统：三级加载机制

> 技能不是函数，是**说明书**。

### 加载链路

| 级别 | 说明 | Token 消耗 |
|---|---|---|
| Level 1 | System Prompt 里只放名字+一句话描述 | 每个技能约 30 Token |
| Level 2 | Agent 匹配任务后，调 `read_file` 读 SKILL.md | 按需加载，不占 System Prompt |
| Level 3 | 照着说明书用底层工具执行 | 正常工具调用开销 |

### 查天气示例链路

```
用户：「帮我查北京今天天气」
  ↓
Agent 扫 SKILLS_SNAPSHOT → 找到 get_weather 技能
  ↓
调用 read_file("get_weather/SKILL.md")
  ↓
读到：「用 fetch_url 访问 https://wttr.in/Beijing?format=j1，解析 JSON...」
  ↓
调用 fetch_url(url)
  ↓
解析数据 → 返回「北京：晴，22°C，湿度 45%」
```

**核心优势：** 加新技能只需建文件夹 + 写 SKILL.md + 重启服务，不用改任何后端代码。

---

## 五、4 个内置工具

| 工具 | 关键设计点 |
|---|---|
| `read_file` | 路径分区(skills/workspace/memory)，防 `..` 路径穿越 |
| `fetch_url` | html2text 转 Markdown，节省 60-70% Token |
| `terminal` | 正则黑名单拦截高危命令(rm -rf/sudo/chmod 777/dd/curl\|bash/fork bomb等) |
| `python_repl` | 封装 LangChain 的 PythonREPLTool |

计划扩展：RAG 检索工具、浏览器自动化工具（后续单独写）。

---

## 六、代码实现步骤

### Step 1：初始化 6 个工作区文件

最重要的 `AGENTS.md` 必须写清楚：

```markdown
# AgentClaw 行为准则

## 技能调用协议（SKILL PROTOCOL）
当用户请求的任务匹配某个技能时，必须严格遵守：
1. 第一步永远调用 `read_file`，读取该技能 location 路径下的 SKILL.md
2. 仔细阅读文件中的步骤和示例
3. 根据文件指示，使用 Core Tools 执行任务
**绝对禁止**：在没有读取 SKILL.md 的情况下，猜测技能的用法或直接执行操作。

## 记忆协议
当用户告知重要个人信息、偏好或背景时，询问是否需要记录。

## Canvas 输出协议
当用户请求创建图表、网页、仪表盘等可视化内容时，将完整 HTML 包裹在 `<openclaw-canvas>` 标签中输出。
```

> ⚠️ 必须用命令式语气写死「必须先读文件」——大模型太聪明，经常「猜」到怎么做就直接干，绕过说明书几乎必然出错。

其他文件（SOUL.md、IDENTITY.md、USER.md、MEMORY.md）相对简单。

### Step 2：实现 4 个 Core Tools

#### read_file_tool.py
```python
import os
from langchain_core.tools import tool
from langchain_community.tools.file_management import ReadFileTool

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_skills_reader = ReadFileTool(root_dir=os.path.join(_BASE_DIR, "skills"))
_workspace_reader = ReadFileTool(root_dir=os.path.join(_BASE_DIR, "workspace"))
_memory_reader = ReadFileTool(root_dir=os.path.join(_BASE_DIR, "memory"))

@tool
def read_file(file_path: str) -> str:
    """
    读取本地文件内容。用于读取技能定义文件（SKILL.md）或工作区配置。
    路径规则：
    - 技能文件: "get_weather/SKILL.md"（相对 skills/ 目录）
    - 工作区文件: "workspace/AGENTS.md"（加 workspace/ 前缀）
    - 记忆文件: "memory/MEMORY.md"（加 memory/ 前缀）
    """
    # 防止路径穿越攻击
    if ".." in file_path:
        return "Error: 不允许使用 .. 访问上级目录。"
    try:
        if file_path.startswith("workspace/"):
            return _workspace_reader.invoke({"file_path": file_path[len("workspace/"):]})
        elif file_path.startswith("memory/"):
            return _memory_reader.invoke({"file_path": file_path[len("memory/"):]})
        else:
            return _skills_reader.invoke({"file_path": file_path})
    except Exception as e:
        return f"Error: {str(e)}"
```

#### fetch_url_tool.py
```python
import html2text
from langchain_core.tools import tool
from langchain_community.tools import RequestsGetTool
from langchain_community.utilities import TextRequestsWrapper

_requests = RequestsGetTool(requests_wrapper=TextRequestsWrapper(), allow_dangerous_requests=True)
_h2t = html2text.HTML2Text()
_h2t.ignore_links = False
_h2t.ignore_images = True
_h2t.body_width = 0  # 不自动换行

@tool
def fetch_url(url: str) -> str:
    """
    发起 HTTP GET 请求，获取指定 URL 的内容。
    HTML 页面会自动转换为 Markdown 格式以节省 Token。内容限制 3000 字符。
    """
    try:
        raw = _requests.invoke({"url": url})
        if raw and ("<html" in raw[:500].lower() or "<body" in raw[:500].lower()):
            result = _h2t.handle(raw)
        else:
            result = raw
        return result[:3000]
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"
```

#### terminal_tool.py
```python
import re
from langchain_core.tools import tool
from langchain_community.tools import ShellTool

_shell = ShellTool()

_BLACKLIST = [
    r"rm\s+-rf", r"\bsudo\b", r"chmod\s+777", r">\s*/dev/",
    r"\bmkfs\b", r"\bdd\b.+if=", r"(curl|wget).+\|\s*(ba)?sh",
    r":\(\)\{.*\}",  # fork bomb
]

@tool
def terminal(command: str) -> str:
    """在受限的安全沙箱中执行 Shell 命令。高危命令会被拦截。输出限制 2000 字符。"""
    for pattern in _BLACKLIST:
        if re.search(pattern, command, re.IGNORECASE):
            return f"拒绝执行：命令匹配高危规则 [{pattern}]"
    try:
        result = _shell.invoke({"commands": [command]})
        return str(result)[:2000]
    except Exception as e:
        return f"Error: {str(e)}"
```

> ⚠️ 生产环境建议放到 Docker 容器里跑。

#### python_repl_tool.py
```python
from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool

_repl = PythonREPLTool()

@tool
def python_repl(code: str) -> str:
    """执行 Python 代码并返回结果。变量在同一会话内保持，可以分步执行。"""
    try:
        result = _repl.invoke({"query": code})
        return str(result)[:3000]
    except Exception as e:
        return f"Error: {str(e)}"
```

### Step 3：技能扫描器（Bootstrap）

启动时扫描 `skills/` 目录，生成 XML 格式的技能快照注入 System Prompt：

```python
import os
import frontmatter  # pip install python-frontmatter

def generate_skills_snapshot(skills_dir: str = None) -> str:
    """扫描技能目录，生成 XML 格式的技能快照。只提取 name 和 description。"""
    if skills_dir is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skills_dir = os.path.join(base, "skills")
    if not os.path.exists(skills_dir):
        return "<available_skills></available_skills>"
    entries = []
    for skill_name in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, skill_name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            post = frontmatter.load(skill_md)
            name = post.get("name", skill_name)
            description = post.get("description", "详见技能文件")
        except Exception:
            name = skill_name
            description = "详见技能文件"
        entries.append(
            f"  <skill>\n"
            f"    <name>{name}</name>\n"
            f"    <description>{description}</description>\n"
            f"    <location>./{skill_name}/SKILL.md</location>\n"
            f"  </skill>"
        )
    inner = "\n".join(entries) if entries else "  <!-- 暂无技能 -->"
    return f"<available_skills>\n{inner}\n</available_skills>"
```

> 💡 为什么用 XML？Claude 系列模型对 XML 结构的路由准确率明显更高——这是 Anthropic 官方提示词工程文档里的建议。

### Step 4：System Prompt 构建器

```python
import os
from tools.skills_scanner import generate_skills_snapshot

def _read(path: str, max_chars: int = 20000) -> str:
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if len(content) > max_chars:
            return content[:max_chars] + "\n\n...[内容过长，已截断]"
        return content
    except Exception:
        return ""

def build_system_prompt() -> str:
    """动态拼接 6 个部分，构建完整 System Prompt。"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parts = [
        "# 你的能力清单\n\n" + generate_skills_snapshot(),
        _read(os.path.join(base, "workspace", "SOUL.md")),
        _read(os.path.join(base, "workspace", "IDENTITY.md")),
        _read(os.path.join(base, "workspace", "USER.md")),
        _read(os.path.join(base, "workspace", "AGENTS.md")),
        _read(os.path.join(base, "memory", "MEMORY.md")),
    ]
    prompt = "\n\n---\n\n".join(p for p in parts if p.strip())
    if len(prompt) > 40000:  # 总长度保护
        prompt = prompt[:40000] + "\n\n...[System Prompt 已截断]"
    return prompt
```

### Step 5：Agent 运行时

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from tools.* import read_file, fetch_url, terminal, python_repl
from graph.prompt_builder import build_system_prompt

load_dotenv()
CORE_TOOLS = [read_file, fetch_url, terminal, python_repl]

def create_agent_executor() -> AgentExecutor:
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o"),
        temperature=0,
        streaming=True,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )
    system_prompt = build_system_prompt()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, CORE_TOOLS, prompt)
    return AgentExecutor(
        agent=agent, tools=CORE_TOOLS, verbose=True,
        max_iterations=12,  # 经验值：太小提前停，太大烧Token
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
```

### Step 6：FastAPI SSE 流式输出

```python
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.agent import create_agent_executor

app = FastAPI(title="AgentClaw", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"], allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

_histories: dict = {}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    async def stream():
        executor = create_agent_executor()
        history = _histories.get(req.session_id, [])
        full_output = ""
        try:
            async for event in executor.astream_events(
                {"input": req.message, "chat_history": history}, version="v2"
            ):
                kind = event.get("event", "")
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        full_output += chunk
                        # 检测 Canvas HTML
                        if "<openclaw-canvas>" in full_output and "</openclaw-canvas>" in full_output:
                            s = full_output.find("<openclaw-canvas>")
                            e = full_output.find("</openclaw-canvas>") + len("</openclaw-canvas>")
                            yield f"event: canvas\ndata: {json.dumps({'html': full_output[s:e]})}\n\n"
                        else:
                            yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                elif kind == "on_tool_start":
                    payload = {"tool": event["name"], "input": str(event["data"].get("input", ""))[:300]}
                    yield f"event: tool_start\ndata: {json.dumps(payload)}\n\n"
                elif kind == "on_tool_end":
                    payload = {"tool": event["name"], "output": str(event["data"].get("output", ""))[:300]}
                    yield f"event: tool_end\ndata: {json.dumps(payload)}\n\n"
            history.append({"role": "human", "content": req.message})
            history.append({"role": "assistant", "content": full_output})
            _histories[req.session_id] = history[-40:]  # 保留最近20轮
            yield f"event: done\ndata: {json.dumps({'ok': True})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    return StreamingResponse(
        stream(), media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 必须加！否则Nginx后面SSE不流
        },
    )
```

### Step 7：创建第一个技能——天气查询

```markdown
---
name: get_weather
description: 获取指定城市的实时天气信息。当用户询问天气、气温、降雨、风速等信息时使用此技能。
version: 1.0.0
---
# 天气查询
## Usage
当用户询问任何城市或地区的天气、温度、降水情况时，使用此技能。
## Steps
1. 从用户消息中提取城市名称
2. 如果是中文城市名，转换为对应英文（如「北京」→「Beijing」）
3. 使用 `fetch_url` 访问：https://wttr.in/{城市英文名}?format=j1
4. 从返回的 JSON 中提取：temp_C、weatherDesc、humidity、windspeedKmph
5. 用自然语言回复用户
```

### 扩展：加汇率查询技能（3分钟）

只需 `mkdir backend/skills/exchange_rate` + 写 SKILL.md + 重启服务。不改后端一行代码。

---

## 七、长期记忆机制

原理：在 AGENTS.md 的「记忆协议」里告诉 Agent 什么情况下把信息写入 MEMORY.md。每次启动 Agent，它都会把这个文件读进 System Prompt，「想起」你是谁、你在做什么。

---

## 八、踩过的坑

| 问题 | 原因 | 解决 |
|---|---|---|
| Agent stopped due to max iterations | AGENTS.md 太模糊 | 加更明确的指引 |
| root_dir 报路径错误 | 相对路径基准不确定 | 必须用 `os.path.abspath()` 算绝对路径 |
| Nginx 后面 SSE 不流 | Nginx 默认缓冲 | 加 `X-Accel-Buffering: no` 头 |
| 模型不遵循技能调用协议 | DeepSeek 复杂任务偷懒 | 换 Claude 3.5 Sonnet |
| langchain_experimental ImportError | 包在主包外 | 单独 `pip install langchain-experimental` |

---

## 九、下一步扩展方向

1. **前端**：Next.js 14 对话界面 + Canvas 面板 + Memory 编辑页 + 技能管理页
2. **知识库 RAG**：LlamaIndex + 本地 PDF/Markdown 索引
3. **浏览器自动化**：browser-use + Playwright
4. **会话持久化**：sessions/{id}.json 替代内存存储

社区资源：
- github.com/anthropics/skills（官方技能仓库，与 AgentClaw 格式兼容）
- agentskills.io
- github.com/VoltAgent/awesome-agent-skills
