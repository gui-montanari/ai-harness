#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, select, signal, subprocess, sys, time, tomllib
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CONFIG = HOME / ".config/ai-harness"
CATALOG_PATH = ROOT / "catalog/mcp-catalog.json"
STATE_DIR = CONFIG / "selections"
SECRETS_DIR = CONFIG / "secrets"
MANAGED_STATE = CONFIG / "managed-names.json"
OVERLAY = CONFIG / "overlay/mcp"
LEGACY_CONFIG = HOME / ".config/mcp-cli-toolkit"
GROK_MCP_MARKER = "# MCPs gerados por ai-harness."
AGY_TYPE = "exa.cascade_plugins_pb.CascadePluginCommandTemplate"
AGY_REMOTE_TYPE = "exa.cascade_plugins_pb.CascadePluginRemoteConfigTemplate"
OBSOLETE = {
    "metabase", "postgres", "redis-mcp-server",
    "ssh-hostinger-gamma-dados", "ssh-hostinger-hermes", "ssh-hostinger-usedata",
    "stockfy-bd-hmg", "stockfy-bd-prd", "stockfy-clickhouse-dev",
    "stockfy-ai-workers-dev", "stockfy-ai-db", "stockfy-ai-db-dev",
    "stockfy-langfuse-dev", "redis-stockfy",
}

def load_json(path: Path, default=None):
    fallback = {} if default is None else default
    if not path.exists(): return fallback
    text = path.read_text()
    return json.loads(text) if text.strip() else fallback

def catalog():
    items = dict(load_json(CATALOG_PATH).get("servers") or {})
    extra = load_json(OVERLAY / "catalog.json").get("servers") or {}
    items.update(extra)
    return {name: expand(cfg) for name, cfg in items.items()}

def expand(value):
    if isinstance(value, str):
        return (
            value.replace("{home}", str(HOME))
            .replace("{toolkit}", str(ROOT))
            .replace("{overlay}", str(OVERLAY))
        )
    if isinstance(value, list): return [expand(v) for v in value]
    if isinstance(value, dict): return {k: expand(v) for k, v in value.items()}
    return value

def selection(client: str, profile: str):
    state = STATE_DIR / f"{client}.json"
    if state.exists(): return set(load_json(state).get("enabled", []))
    return set(load_json(ROOT / f"profiles/{profile}.json").get("enabled", []))

def save_selection(client: str, enabled: set[str]):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"{client}.json").write_text(json.dumps({"enabled": sorted(enabled)}, indent=2)+"\n")

MCP_REMOTE_OAUTH_TIMEOUT_SEC = 300


def uses_mcp_remote(cfg) -> bool:
    parts = [str(cfg.get("command") or "")] + [str(a) for a in (cfg.get("args") or [])]
    return any("mcp-remote" in part for part in parts)


def uses_bearer_header(cfg) -> bool:
    return any("Authorization:" in str(a) for a in (cfg.get("args") or []))


def uses_browser_oauth(cfg) -> bool:
    return uses_mcp_remote(cfg) and not uses_bearer_header(cfg)


def oauth_timeout_sec(cfg):
    if "oauthTimeoutSec" in cfg:
        timeout = cfg["oauthTimeoutSec"]
        return int(timeout) if timeout else None
    if uses_browser_oauth(cfg):
        return MCP_REMOTE_OAUTH_TIMEOUT_SEC
    return None

def command_config(cfg):
    command, args = cfg["command"], list(cfg.get("args", []))
    timeout = oauth_timeout_sec(cfg)
    if timeout is not None and "--auth-timeout" not in args:
        args += ["--auth-timeout", str(timeout)]
    if secret := cfg.get("secretFile"):
        args = [str(ROOT/"scripts/run-with-env.sh"), str(SECRETS_DIR/secret), command, *args]
        command = "bash"
    return command, args, cfg.get("env", {})

def is_remote(cfg):
    return "url" in cfg

def managed_names():
    previous = set(load_json(MANAGED_STATE, {"names": []}).get("names", []))
    current = set(catalog())
    return previous | current | OBSOLETE

def record_managed():
    MANAGED_STATE.parent.mkdir(parents=True, exist_ok=True)
    MANAGED_STATE.write_text(json.dumps({"names": sorted(catalog())}, indent=2)+"\n")

def sync_claude(enabled):
    path=HOME/".claude.json"; data=load_json(path)
    active=data.setdefault("mcpServers",{}); disabled=data.setdefault("mcpServersDisabled",{})
    for name in managed_names(): active.pop(name,None); disabled.pop(name,None)
    for name,cfg in catalog().items():
        if is_remote(cfg): item={"type":"http","url":cfg["url"]}
        else:
            cmd,args,env=command_config(cfg); item={"command":cmd,"args":args}
            if env: item["env"]=env
        (active if name in enabled else disabled)[name]=item
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")

def toml_value(v):
    if isinstance(v,str): return json.dumps(v,ensure_ascii=False)
    if isinstance(v,bool): return "true" if v else "false"
    if isinstance(v,list): return "["+", ".join(toml_value(x) for x in v)+"]"
    if isinstance(v,dict): return "{ "+", ".join(f'{json.dumps(str(k))} = {toml_value(x)}' for k,x in v.items())+" }"
    return str(v)

def sync_codex(enabled):
    base=HOME/".codex/config.toml"; target=HOME/".codex-cli/config.toml"
    text=base.read_text().rstrip() if base.exists() else ""
    lines=[text,"",GROK_MCP_MARKER,""]
    for name,cfg in catalog().items():
        if name not in enabled: continue
        lines.append(f"[mcp_servers.{name}]")
        if is_remote(cfg): lines.append(f"url = {toml_value(cfg['url'])}")
        else:
            cmd,args,env=command_config(cfg); lines += [f"command = {toml_value(cmd)}",f"args = {toml_value(args)}"]
            if env: lines.append(f"env = {toml_value(env)}")
        lines.append("")
    target.parent.mkdir(parents=True,exist_ok=True); target.write_text("\n".join(lines).lstrip()+"\n"); target.chmod(0o600)

def opencode_path():
    local=Path.cwd()/"opencode.json"; return local if local.exists() else HOME/".config/opencode/opencode.json"

def sync_opencode(enabled):
    path=opencode_path(); data=load_json(path,{"$schema":"https://opencode.ai/config.json","mcp":{}}); servers=data.setdefault("mcp",{})
    for name in managed_names(): servers.pop(name,None)
    for name,cfg in catalog().items():
        if is_remote(cfg): item={"type":"remote","url":cfg["url"],"enabled":name in enabled}
        else:
            cmd,args,env=command_config(cfg); item={"type":"local","command":[cmd,*args],"enabled":name in enabled}
            if env:item["environment"]=env
        servers[name]=item
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")

def sync_agy(enabled):
    path=HOME/".gemini/config/mcp_config.json"; data=load_json(path,{"mcpServers":{}}); servers=data.setdefault("mcpServers",{})
    for name in managed_names(): servers.pop(name,None)
    for name,cfg in catalog().items():
        if is_remote(cfg): item={"$typeName":AGY_REMOTE_TYPE,"serverUrl":cfg["url"],"disabled":name not in enabled}
        else:
            cmd,args,env=command_config(cfg); item={"$typeName":AGY_TYPE,"command":cmd,"args":args,"disabled":name not in enabled}
            if env:item["env"]=env
        servers[name]=item
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")

def strip_managed_grok_servers(text):
    names=managed_names(); lines=text.splitlines(keepends=True); result=[]; skipping=False
    for line in lines:
        stripped=line.strip()
        if stripped in (GROK_MCP_MARKER, "# MCPs gerados por mcp-cli-toolkit."): continue
        if stripped.startswith("[") and stripped.endswith("]"):
            table=stripped[1:-1]
            parts=table.split(".")
            skipping=len(parts)>=2 and parts[0]=="mcp_servers" and parts[1].strip('"') in names
        if not skipping: result.append(line)
    return "".join(result).rstrip()

def sync_grok(enabled):
    path=HOME/".grok/config.toml"; text=strip_managed_grok_servers(path.read_text() if path.exists() else "")
    lines=[text,"",GROK_MCP_MARKER,""]
    for name,cfg in catalog().items():
        lines.append(f"[mcp_servers.{name}]")
        if is_remote(cfg): lines.append(f"url = {toml_value(cfg['url'])}")
        else:
            cmd,args,env=command_config(cfg); lines += [f"command = {toml_value(cmd)}",f"args = {toml_value(args)}"]
            if env: lines.append(f"env = {toml_value(env)}")
        if timeout := oauth_timeout_sec(cfg):
            lines.append(f"startup_timeout_sec = {timeout}")
        lines += [f"enabled = {toml_value(name in enabled)}",""]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines).lstrip()+"\n"); path.chmod(0o600)

def sync_cursor(enabled):
    path=HOME/".cursor/mcp.json"; data=load_json(path,{"mcpServers":{}}); servers=data.setdefault("mcpServers",{})
    for name in managed_names(): servers.pop(name,None)
    for name,cfg in catalog().items():
        if name not in enabled: continue
        if is_remote(cfg): item={"url":cfg["url"]}
        else:
            cmd,args,env=command_config(cfg); item={"command":cmd,"args":args}
            if env: item["env"]=env
        servers[name]=item
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n"); path.chmod(0o600)

SYNC={"claude":sync_claude,"codex":sync_codex,"opencode":sync_opencode,"agy":sync_agy,"grok":sync_grok,"cursor":sync_cursor}

def sync(client, profile):
    clients=list(SYNC) if client=="all" else [client]
    for current in clients:
        enabled=selection(current,profile)&set(catalog()); save_selection(current,enabled); SYNC[current](enabled); print(f"{current}: {len(enabled)} MCP(s) ativo(s)")
    record_managed()

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def _color(text, code, enabled):
    if not enabled:
        return text
    return f"{code}{text}{RESET}"


def format_menu(client, names, enabled, *, color=False):
    indexed = list(enumerate(names, 1))
    active = [(i, name) for i, name in indexed if name in enabled]
    inactive = [(i, name) for i, name in indexed if name not in enabled]
    lines = [f"MCPs para {client}:", "", _color("Ativos:", GREEN, color)]
    if active:
        lines.extend(_color(f" {i:2}. {name}", GREEN, color) for i, name in active)
    else:
        lines.append("  (nenhum)")
    lines.extend(["", _color("Inativos:", RED, color)])
    if inactive:
        lines.extend(_color(f" {i:2}. {name}", RED, color) for i, name in inactive)
    else:
        lines.append("  (nenhum)")
    return lines

def menu_uses_color():
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()

def menu(client, profile):
    enabled=selection(client,profile)&set(catalog()); names=list(catalog())
    while True:
        print()
        print("\n".join(format_menu(client, names, enabled, color=menu_uses_color())))
        choice=input("Número alterna (fixo); [s] salvar; [q] sair: ").strip().lower()
        if choice=="q": return False
        if choice=="s": save_selection(client,enabled); SYNC[client](enabled); record_managed(); return True
        try:
            name=names[int(choice)-1]; enabled.symmetric_difference_update({name})
        except (ValueError,IndexError): print("Opção inválida")

def doctor(profile, all_servers=False):
    enabled=set(catalog()) if all_servers else set().union(*(selection(c,profile) for c in SYNC))
    failures=0
    for name,cfg in catalog().items():
        if name not in enabled: continue
        if is_remote(cfg):
            failures += doctor_remote(name, cfg["url"])
            continue
        if secret:=cfg.get("secretFile"):
            if not (SECRETS_DIR/secret).exists(): print(f"⚠️  {name}: segredo ausente ({secret})"); failures+=1; continue
        cmd,args,env=command_config(cfg); process_env=os.environ.copy(); process_env.update(env)
        try:
            p=subprocess.Popen([cmd,*args],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,env=process_env,start_new_session=True)
            msg={"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mcp-doctor","version":"1"}}}
            p.stdin.write(json.dumps(msg)+"\n"); p.stdin.flush()
            ready=select.select([p.stdout],[],[],25)[0]; ok=bool(ready and p.stdout.readline().strip())
            print(f"{'✅' if ok else '❌'} {name}: {'handshake OK' if ok else 'sem resposta'}"); failures+=0 if ok else 1
            os.killpg(p.pid,signal.SIGTERM)
        except Exception as error: print(f"❌ {name}: {error}"); failures+=1
    return failures

def doctor_remote(name, url):
    message={"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mcp-doctor","version":"1"}}}
    request=urllib_request.Request(url,data=json.dumps(message).encode(),headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"},method="POST")
    try:
        with urllib_request.urlopen(request,timeout=25) as response:
            ok=200 <= response.status < 300
            print(f"{'✅' if ok else '❌'} {name}: HTTP {response.status}")
            return 0 if ok else 1
    except urllib_error.HTTPError as error:
        if error.code in (401,403):
            print(f"⚠️  {name}: acessível, autenticação necessária (HTTP {error.code})")
            return 0
        print(f"❌ {name}: HTTP {error.code}")
        return 1
    except Exception as error:
        print(f"❌ {name}: {error}")
        return 1

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="command",required=True)
    for action in ("sync","menu"):
        p=sub.add_parser(action); p.add_argument("--client",choices=[*SYNC,"all"] if action=="sync" else list(SYNC),default="all" if action=="sync" else "codex"); p.add_argument("--profile",default="default")
    p=sub.add_parser("list"); p.add_argument("--profile",default="default")
    p=sub.add_parser("doctor"); p.add_argument("--profile",default="default"); p.add_argument("--all",action="store_true")
    args=ap.parse_args()
    if args.command=="sync": sync(args.client,args.profile)
    elif args.command=="menu": raise SystemExit(0 if menu(args.client,args.profile) else 1)
    elif args.command=="list":
        for name in catalog(): print(name)
    elif args.command=="doctor": raise SystemExit(doctor(args.profile,args.all))

if __name__=="__main__": main()
