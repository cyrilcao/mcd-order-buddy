#!/usr/bin/env python3
# 真实麦当劳营养数据拉取 + 控卡/高蛋白筛选（实测脚本，可复现）
# 直连 MCP streamable-http，使用真实 Token；只读，不下单、不花钱。
import urllib.request, json, re

URL = "https://mcp.mcd.cn"

# 安全规范：严禁硬编码真实 Token。优先读环境变量 MCD_MCP_TOKEN，
# 其次尝试从 WorkBuddy 的 mcp.json 中读取（仅本地使用，不会随仓库公开）。
import os
def _load_token():
    t = os.environ.get("MCD_MCP_TOKEN")
    if t:
        return t
    try:
        cfg_path = os.path.expanduser("~/.workbuddy/mcp.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in cfg.get("mcpServers", {}).get("mcd-mcp", {}).get("env", {}).items():
                if "TOKEN" in k.upper():
                    return v
    except Exception:
        pass
    return ""
TOKEN = _load_token()
if not TOKEN:
    raise SystemExit("未找到 MCD MCP Token：请设置环境变量 MCD_MCP_TOKEN，或在 WorkBuddy 配置 mcd-mcp 后运行。")

def headers(session=None):
    h = {"Content-Type":"application/json","Accept":"application/json, text/event-stream","Authorization":f"Bearer {TOKEN}"}
    if session: h["Mcp-Session-Id"]=session
    return h

def post(payload, session=None):
    data=json.dumps(payload).encode()
    req=urllib.request.Request(URL,data=data,headers=headers(session),method="POST")
    try:
        resp=urllib.request.urlopen(req,timeout=30)
        return resp.headers.get("mcp-session-id"), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.headers.get("mcp-session-id"), e.read().decode()

def parse(body):
    body=(body or "").strip()
    if not body: return None
    if body.startswith("{"): return json.loads(body)
    out=None
    for line in body.splitlines():
        line=line.strip()
        if line.startswith("data:"):
            try: out=json.loads(line[5:].strip())
            except: pass
    return out

sid,_=post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"real-probe","version":"1.0"}}})
post({"jsonrpc":"2.0","method":"notifications/initialized","params":{}}, sid)
_,body2=post({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list-nutrition-foods","arguments":{}}}, sid)
res=parse(body2)
text="".join(c.get("text","") for c in (res or {}).get("result",{}).get("content",[]) if c.get("type")=="text")

# 提取 Original Response 后的 JSON，取 data 字段（真实换行已解码）
m=re.search(r'Original Response\s*\n+\s*(\{.*\})\s*$', text, re.S)
data_str=""
if m:
    try:
        obj=json.loads(m.group(1)); data_str=obj.get("data","") or ""
    except Exception as e:
        print("JSON parse err:", e); data_str=text
else:
    data_str=text

foods=[]
for ln in data_str.split("\n"):
    s=ln.strip()
    if not s or s.startswith("["):   # 跳过 [160]{...} 头
        continue
    p=[x.strip() for x in s.split(",")]
    if len(p)<9: continue
    try:
        kcal=float(p[3]); protein=float(p[4]); fat=float(p[5]); carb=float(p[6]); sodium=float(p[7])
    except Exception:
        continue
    foods.append({"name":p[0],"kcal":kcal,"protein":protein,"fat":fat,"carb":carb,"sodium":sodium})

print(f"=== parsed foods: {len(foods)}")
MAX_KCAL,MIN_PRO=550,20
cand=[f for f in foods if f["kcal"]<=MAX_KCAL and f["protein"]>=MIN_PRO]
cand.sort(key=lambda f:f["protein"]/f["kcal"],reverse=True)
print(f"=== 控卡(<= {MAX_KCAL}kcal)+高蛋白(>= {MIN_PRO}g) 候选 {len(cand)} 个 Top10:")
for f in cand[:10]:
    print(f"  {f['name']:20s} {f['kcal']:5.0f}kcal 蛋白{f['protein']:4.0f}g 脂肪{f['fat']:4.0f}g 钠{f['sodium']:5.0f}mg 效率{f['protein']/f['kcal']:.3f}g/100kcal")
