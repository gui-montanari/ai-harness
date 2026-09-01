#!/usr/bin/env python3
"""Importa seleções existentes uma única vez, sem alterar configurações dos clientes."""
import json, tomllib
from pathlib import Path

home=Path.home(); root=Path(__file__).resolve().parents[1]
known=set(json.loads((root/"catalog/mcp-catalog.json").read_text())["servers"])
overlay=home/".config/ai-harness/overlay/mcp/catalog.json"
if overlay.exists() and overlay.read_text().strip():
    known |= set(json.loads(overlay.read_text()).get("servers") or {})
target=home/".config/ai-harness/selections"; target.mkdir(parents=True,exist_ok=True)
legacy=home/".config/mcp-cli-toolkit/selections"
if legacy.exists() and not any(target.glob("*.json")):
    for src in legacy.glob("*.json"):
        dest=target/src.name
        if not dest.exists():
            dest.write_text(src.read_text())
            print(f"✅ {src.stem}: seleção herdada do toolkit")

def save(client,names):
    path=target/f"{client}.json"
    if path.exists(): print(f"⏭️  {client}: seleção já existe"); return
    enabled=sorted(set(names)&known)
    if not enabled:
        print(f"⏭️  {client}: nada conhecido para migrar")
        return
    path.write_text(json.dumps({"enabled":enabled},indent=2)+"\n"); print(f"✅ {client}: seleção migrada")

def load_json(path):
    if not path.exists(): return {}
    text=path.read_text()
    return json.loads(text) if text.strip() else {}

claude=home/".claude.json"
save("claude", load_json(claude).get("mcpServers",{}))
codex=home/".codex-cli/config.toml"
save("codex", tomllib.loads(codex.read_text()).get("mcp_servers",{}) if codex.exists() and codex.read_text().strip() else [])
opencode=home/".config/opencode/opencode.json"
od=load_json(opencode).get("mcp",{})
save("opencode", [name for name,cfg in od.items() if cfg.get("enabled",False)])
agy=home/".gemini/config/mcp_config.json"
ad=load_json(agy).get("mcpServers",{})
save("agy", [name for name,cfg in ad.items() if not cfg.get("disabled",False)])
grok=home/".grok/config.toml"
gd=tomllib.loads(grok.read_text()).get("mcp_servers",{}) if grok.exists() and grok.read_text().strip() else {}
save("grok", [name for name,cfg in gd.items() if cfg.get("enabled",True)])
cursor=home/".cursor/mcp.json"
save("cursor", load_json(cursor).get("mcpServers",{}))
