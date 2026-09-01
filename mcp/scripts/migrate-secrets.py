#!/usr/bin/env python3
"""Migra somente valores locais para ~/.config; nunca escreve segredos no repositório."""
import json
from pathlib import Path

home=Path.home(); root=Path(__file__).resolve().parents[1]
target=home/".config/ai-harness/secrets"; target.mkdir(parents=True,exist_ok=True)
claude=json.loads((home/".claude.json").read_text()) if (home/".claude.json").exists() else {}
servers={**claude.get("mcpServersDisabled",{}),**claude.get("mcpServers",{})}

def parse_env(path):
    result={}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key,value=line.split("=",1); result[key.strip()]=value.strip().strip('"').strip("'")
    return result

sources={name:dict(cfg.get("env",{})) for name,cfg in servers.items()}
sources["gdrive"]={**sources.get("gdrive",{}),**parse_env(home/"mcp-servers/gdrive/.env")}
for name in list(sources):
    sources[name]={**parse_env(home/f"mcp-servers/{name}/.env"),**sources[name]}
sources["brave-search"]={**parse_env(home/"mcp-servers/.env"),**sources.get("brave-search",{})}
for example in (root/"secrets.example").glob("*.env.example"):
    name=example.name.removesuffix(".env.example"); keys=[line.split("=",1)[0] for line in example.read_text().splitlines() if "=" in line]
    values=sources.get(name,{})
    missing=[key for key in keys if key not in values]
    if missing: print(f"⚠️  {name}: faltam {', '.join(missing)}"); continue
    path=target/f"{name}.env"; path.write_text("\n".join(f"{key}={values[key]}" for key in keys)+"\n"); path.chmod(0o600); print(f"✅ {path}")
