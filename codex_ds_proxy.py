"""
Codex Responses API → DeepSeek Chat Completions proxy v2
Properly handles the full Responses API SSE event sequence.
"""
import json, urllib.request, ssl, threading, uuid

PORT = 15722
DS_KEY = None
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    DS_KEY = json.load(f)['models']['providers']['deepseek-direct']['apiKey']
DS_URL = 'https://api.deepseek.com/v1/chat/completions'

# Use asyncio + aiohttp for better streaming, fallback to flask if available
try:
    from aiohttp import web
    USE_AIOHTTP = True
except ImportError:
    USE_AIOHTTP = False

if not USE_AIOHTTP:
    import http.server

ctx = ssl.create_default_context()

def build_messages(body):
    d = json.loads(body)
    messages = []
    instr = d.get('instructions', '')
    
    # Add instructions as system message if present
    if instr and len(instr) > 10:
        # Truncate very long instructions to first 4000 chars to avoid overwhelming
        sys_msg = instr[:4000] if len(instr) > 4000 else instr
        messages.append({'role': 'system', 'content': sys_msg})
    
    # Build user input
    inp = d.get('input', '')
    if isinstance(inp, list):
        parts = []
        for item in inp:
            if isinstance(item, dict) and item.get('type') == 'input_text':
                parts.append(item.get('text', ''))
            elif isinstance(item, str):
                parts.append(item)
        inp = '\n'.join(parts)
    if inp:
        messages.append({'role': 'user', 'content': inp})
    else:
        messages.append({'role': 'user', 'content': '.'})
    return {
        'model': 'deepseek-chat',
        'messages': messages,
        'max_tokens': d.get('max_output_tokens', 4096),
        'stream': d.get('stream', True),
        'temperature': d.get('temperature', 1.0),
        'top_p': d.get('top_p', 1.0),
    }

if USE_AIOHTTP:
    async def handle_responses(request):
        body = await request.read()
        chat_body = build_messages(body)
        req_data = json.dumps(chat_body).encode()
        
        headers = {
            'Authorization': f'Bearer {DS_KEY}',
            'Content-Type': 'application/json',
        }
        
        is_stream = json.loads(body).get('stream', True)
        
        if not is_stream:
            req = urllib.request.Request(DS_URL, data=req_data, headers=headers, method='POST')
            resp = urllib.request.urlopen(req, context=ctx, timeout=120)
            resp_data = json.loads(resp.read().decode())
            content = resp_data['choices'][0]['message']['content']
            return web.json_response({
                'id': str(uuid.uuid4()),
                'object': 'response',
                'status': 'completed',
                'output': [{
                    'id': str(uuid.uuid4()),
                    'type': 'message',
                    'role': 'assistant',
                    'content': [{'type': 'output_text', 'text': content}]
                }],
                'usage': resp_data.get('usage', {}),
            })
        
        # Streaming response
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        await response.prepare(request)
        
        resp_id = str(uuid.uuid4())
        item_id = str(uuid.uuid4())
        part_id = str(uuid.uuid4())
        
        # 1. response.created
        await response.write(
            f'event: response.created\ndata: {json.dumps({"type":"response.created","response":{"id":resp_id,"object":"response","status":"in_progress","output":[]}})}\n\n'.encode()
        )
        
        # 2. response.output_item.added
        await response.write(
            f'event: response.output_item.added\ndata: {json.dumps({"type":"response.output_item.added","item":{"id":item_id,"type":"message","role":"assistant","content":[]},"output_index":0})}\n\n'.encode()
        )
        
        # 3. response.content_part.added
        await response.write(
            f'event: response.content_part.added\ndata: {json.dumps({"type":"response.content_part.added","part":{"id":part_id,"type":"output_text","text":""},"item_id":item_id,"output_index":0,"content_index":0})}\n\n'.encode()
        )
        
        try:
            req = urllib.request.Request(DS_URL, data=req_data, headers=headers, method='POST')
            ds_resp = urllib.request.urlopen(req, context=ctx, timeout=120)
            
            buffer = b''
            text_content = ''
            while True:
                chunk = ds_resp.read(4096)
                if not chunk:
                    break
                buffer += chunk
                lines = buffer.split(b'\n')
                buffer = lines.pop()
                
                for line in lines:
                    line_str = line.decode('utf-8', errors='replace').strip()
                    if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                        try:
                            data = json.loads(line_str[6:])
                            choices = data.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    text_content += content
                                    # 4. response.output_text.delta
                                    await response.write(
                                        f'event: response.output_text.delta\ndata: {json.dumps({"type":"response.output_text.delta","delta":content,"item_id":item_id,"output_index":0,"content_index":0})}\n\n'.encode()
                                    )
                        except json.JSONDecodeError:
                            pass
            
            # 5. response.content_part.done
            await response.write(
                f'event: response.content_part.done\ndata: {json.dumps({"type":"response.content_part.done","part":{"id":part_id,"type":"output_text","text":text_content},"item_id":item_id,"output_index":0,"content_index":0})}\n\n'.encode()
            )
            
            # 6. response.output_item.done
            await response.write(
                f'event: response.output_item.done\ndata: {json.dumps({"type":"response.output_item.done","item":{"id":item_id,"type":"message","role":"assistant","status":"completed","content":[{"type":"output_text","text":text_content}]},"output_index":0})}\n\n'.encode()
            )
            
            # 7. response.completed
            await response.write(
                f'event: response.completed\ndata: {json.dumps({"type":"response.completed","response":{"id":resp_id,"object":"response","status":"completed","output":[{"id":item_id,"type":"message","role":"assistant","content":[{"type":"output_text","text":text_content}]}]}})}\n\n'.encode()
            )
            
        except Exception as e:
            err = json.dumps({"type":"error","error":{"type":"server_error","message":str(e)}})
            await response.write(f'event: error\ndata: {err}\n\n'.encode())
        
        await response.write_eof()
        return response

    app = web.Application()
    app.router.add_post('/v1/responses', handle_responses)
    app.router.add_get('/v1/responses', lambda r: web.json_response({'status': 'ok'}))
    
    web.run_app(app, host='127.0.0.1', port=PORT, print=lambda *_: None)
else:
    # Fallback: threaded http.server
    import http.server
    
    class ProxyHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl).decode()
            if '/v1/responses' not in self.path:
                self.send_response(404); self.end_headers(); return
            try:
                chat_body = build_messages(body)
                req_data = json.dumps(chat_body).encode()
                is_stream = json.loads(body).get('stream', True)
                
                if not is_stream:
                    req = urllib.request.Request(DS_URL, data=req_data, headers={
                        'Authorization': f'Bearer {DS_KEY}', 'Content-Type': 'application/json'}, method='POST')
                    resp = urllib.request.urlopen(req, context=ctx, timeout=120)
                    rd = json.loads(resp.read().decode())
                    content = rd['choices'][0]['message']['content']
                    iid = str(uuid.uuid4())
                    result = {
                        'id': str(uuid.uuid4()), 'object': 'response', 'status': 'completed',
                        'output': [{'id': iid, 'type': 'message', 'role': 'assistant',
                            'content': [{'type': 'output_text', 'text': content}]}],
                        'usage': rd.get('usage', {})
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                    return
                
                # Stream
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                rid = str(uuid.uuid4())
                iid = str(uuid.uuid4())
                pid = str(uuid.uuid4())
                
                self.wfile.write(
                    f'event: response.created\ndata: {json.dumps({"type":"response.created","response":{"id":rid,"status":"in_progress","output":[]}})}\n\n'.encode()
                )
                self.wfile.write(
                    f'event: response.output_item.added\ndata: {json.dumps({"type":"response.output_item.added","item":{"id":iid,"type":"message","role":"assistant","content":[]},"output_index":0})}\n\n'.encode()
                )
                self.wfile.write(
                    f'event: response.content_part.added\ndata: {json.dumps({"type":"response.content_part.added","part":{"id":pid,"type":"output_text","text":""},"item_id":iid,"output_index":0,"content_index":0})}\n\n'.encode()
                )
                self.wfile.flush()
                
                req = urllib.request.Request(DS_URL, data=req_data, headers={
                    'Authorization': f'Bearer {DS_KEY}', 'Content-Type': 'application/json'}, method='POST')
                ds_resp = urllib.request.urlopen(req, context=ctx, timeout=120)
                
                buffer = b''
                text_content = ''
                while True:
                    chunk = ds_resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    lines = buffer.split(b'\n')
                    buffer = lines.pop()
                    for line in lines:
                        ls = line.decode('utf-8', errors='replace').strip()
                        if ls.startswith('data: ') and ls != 'data: [DONE]':
                            try:
                                d = json.loads(ls[6:])
                                for c in d.get('choices', []):
                                    ct = c.get('delta', {}).get('content', '')
                                    if ct:
                                        text_content += ct
                                        self.wfile.write(
                                            f'event: response.output_text.delta\ndata: {json.dumps({"type":"response.output_text.delta","delta":ct,"item_id":iid,"output_index":0,"content_index":0})}\n\n'.encode()
                                        )
                                        self.wfile.flush()
                            except:
                                pass
                
                self.wfile.write(
                    f'event: response.content_part.done\ndata: {json.dumps({"type":"response.content_part.done","part":{"id":pid,"type":"output_text","text":text_content},"item_id":iid,"output_index":0,"content_index":0})}\n\n'.encode()
                )
                self.wfile.write(
                    f'event: response.output_item.done\ndata: {json.dumps({"type":"response.output_item.done","item":{"id":iid,"type":"message","role":"assistant","status":"completed","content":[{"type":"output_text","text":text_content}]},"output_index":0})}\n\n'.encode()
                )
                self.wfile.write(
                    f'event: response.completed\ndata: {json.dumps({"type":"response.completed","response":{"id":rid,"status":"completed","output":[{"id":iid,"type":"message","role":"assistant","content":[{"type":"output_text","text":text_content}]}]}})}\n\n'.encode()
                )
                self.wfile.flush()
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        def log_message(self, *a):
            pass
    
    httpd = http.server.HTTPServer(('127.0.0.1', PORT), ProxyHandler)
    print(f'Codex DS Proxy v2 on http://127.0.0.1:{PORT}')
    httpd.serve_forever()
