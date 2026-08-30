---
name: object-storage
description: >
  Use when adding file upload, blob, S3, Azure Blob, signed URL, quarantine,
  magic-number validation, or when a handler would write to disk or a public
  bucket. Database: persistence-ports. Authz of the download: auth.
---

# Object storage por porta

Arquivo não é coluna de banco e não é URL eterna. O domínio fala `ObjectStoragePort`. Bucket **privado**. Download = URL curta, assinada, autorizada no servidor.

**REQUIRED BACKGROUND:** `AGENTS.md` (storage, mídia). **REQUIRED SUB-SKILL:** `auth` (quem lê), `persistence-ports` (metadado no banco do dono).

## Antes de implementar — pergunte

Se o provider **ainda não** está no ADR/`AGENTS.md`:

> Qual object storage neste produto?
> 1. S3-compatível (AWS, MinIO, …)
> 2. Azure Blob
> 3. Outro (nomeie)

Implemente **um** adapter. O porto não muda. Segundo provider só com segundo ambiente real.

## Porto

```
ObjectStoragePort.put(path, bytes, content_type) -> location
ObjectStoragePort.sign_get(path, ttl, principal) -> url
ObjectStoragePort.delete(path)
```

`path` o **servidor** monta: `{tenant}/{bounded_context}/{id}/{uuid}.{ext}`. Path vindo do cliente é achado (path traversal / IDOR).

Metadado canônico (tamanho, tipo declarado, tipo real, hash, tenant, owner) vive na tabela do **serviço dono**. Storage não é SSOT de autorização.

## Regras

- Bucket privado. Sem ACL pública em dado operacional/confidencial.
- URL assinada: TTL curto (minutos), `no-store`. Authz **antes** de assinar (`auth` + posse).
- Upload: allowlist de tipo, teto de tamanho (e duração se áudio). Verificar **magic number** do bytes, não o `Content-Type` do cliente.
- Quarentena: objeto só fica legível depois da verificação (antimalware se o requisito pedir — porta pequena, não um “agente”).
- I/O async. CPU de hash/scan fora do event loop (`to_thread` / worker).
- Tenant no path **e** na authz. Cross-tenant no mesmo key prefix = achado.
- Delete no mesmo use case que invalida o metadado. Sem arquivo órfão silencioso e sem apagar o último leitor no mesmo deploy (`sql-migrations` destrutiva).

Áudio/imagem/PDF são **tipos**, não serviços. Parser/OCR/LLM só se o requisito mandar, e nunca no upload cru.

## Red flags

- `open('/tmp/'+filename)` no handler
- Bucket público “porque o front precisa”
- URL sem expirar; path montado pelo cliente
- Confiar em `file.type` do browser
- SDK S3/Blob em `core/` / `application/`
- Três adapters no mesmo PR

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Provider perguntado; **um** adapter
- [ ] `ObjectStoragePort`; path servidor com tenant
- [ ] Bucket privado; sign_get com TTL + authz prévia
- [ ] Magic number + teto de tamanho; tipo allowlisted
- [ ] Metadado no serviço dono; storage não autoriza
- [ ] I/O async; scan pesado fora do event loop
