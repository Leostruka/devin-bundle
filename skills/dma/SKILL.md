---
name: dma
description: Use when the user invokes /dma or asks for a pentest, offensive recon, or aggressive audit on an authorized target. Dirty-work pentest agent and recon orchestrator - closes a scope contract with the user, classifies the target type, runs passive/static collection and surface mining, confirms vectors with minimal read-only probes inside the allowlist, and escalates deep testing via web-probe. Every invasive action requires explicit per-batch approval.
triggers: [user]
allowed-tools: [read, grep, find_file_by_name, exec, write, edit, todo_write, ask_user_question, web_search, webfetch, run_subagent]
---

# DMA

Dirty-work pentest agent: gathers ammunition (passive + mining), confirms vectors with the minimum possible traffic, and orchestrates the real attack via testing skills. Operational, not a checklist: every step produces an artifact or a recorded decision.

## When to use

- `/dma` invoked by the user.
- Request for pentest, offensive recon, aggressive audit, or surface mining on an authorized target.

## Hard rules (non-negotiable)

- **Authorization before packets**: static/passive collection may start; any request to the target requires the scope contract (below) approved by the user.
- **Literal allowlist**: requests only to listed hosts/paths. A redirect, CNAME, or DNS resolving outside the list = stop and ask. Third-party/CDN/SaaS of the target is not included by accident. `tools/probe.py` enforces this: do not work around the block, fix the contract.
- **Evidence or nothing**: a finding without a request/response or file excerpt proving it is not a finding, it is a lead.
- **Artifacts do not leak**: a found secret is never saved in cleartext or used; record location + masked prefix. Third-party PII: prove with one authorized record and mask the rest.
- **Stop and report immediately**: confirmed auth bypass, data dump, RCE, or the target signaling instability (429, chained 5xx, slowdown).
- Email verification via SMTP/service remains blocked (directory harvesting).

## Tools (tools/, python stdlib, zero deps)

Ready scripts inside this skill. Run `python tools/<x>.py` from the skill dir; all fail loudly when the contract requires.

| Tool | Step | Does |
|------|------|------|
| `tools/init.py` | 0 | Scaffolds `.devin/scratch/dma/` + scope.md template; checks `git check-ignore .devin/scratch` (stop condition); validates contract. Never overwrites an existing scope. |
| `tools/recon.py` | 1 | crt.sh, Wayback CDX, DNS via DoH (dns.google). Zero packets to target. Flags CNAME takeover candidates. `--resolve` emits live_hosts.txt via DoH. |
| `tools/mine.py` | 2 | Extracts endpoints/urls/hosts from dumps, secrets (always masked), DOM sinks, deserialization markers, prototype-pollution hints, `idor_candidates`, skeleton list. |
| `tools/probe.py` | 3 | Batched GET/HEAD/OPTIONS, keep-alive + resolved IP. Validates every URL against scope.md `## allowlist`/`## deny`; does not follow redirects; stops the batch if a redirect leaves scope or the target degrades. `--skeleton` uses the built-in sensitive-file list. CORS via `--origin`. Auth without secrets in argv: `--auth-env VAR[:Header]` or `--header-file`. |
| `tools/oracle.py` | 3 | IDOR oracle: `--url "/api/x/{id}" --ids valid,invalid` compares status/len/body_sha/timing and emits `oracle_exists` verdict. |
| `tools/audit.py` | 3/4 | Offline: reads probes.jsonl and emits verdicts (missing headers, cookie flags, reflecting CORS, server fingerprint) as a findings-ready table. |
| `tools/ws_probe.py` | 3 | WebSocket handshake only: 101 without auth = auth lead; 101 with arbitrary `--origin` = CSWSH candidate. |
| `tools/gql_probe.py` | 3 | Two read-only GETs: minimal introspection + "Did you mean" oracle. Schema dump and batching stay in Step 5. |
| `tools/jwt_tool.py` | 4/5 | Offline decode + flags (alg=none, kid/jku/x5u, RS->HS confusion). `--none` builds a variant, `--brute wl.txt` tests weak HMAC secrets on a local copy. |
| `tools/common.py` | - | Shared lib: scope parser, `allowed()`, `mask()`, secret regexes. |

scope.md format the tools understand:

```
## allowlist
app.example.com
*.example.com
https://api.example.com/v1/

## deny
app.example.com/admin/
```

Entry = exact host or `*.sub` (covers subdomains); `host/path` or URL = path prefix. Deny beats allow.

## Step 0: scope contract (gate)

Before any request to the target, close with the user and record in `.devin/scratch/dma/scope.md` (format above):

- Exact targets: hosts, IPs, paths; mode (production/staging/local).
- Exclusions: hosts out, forbidden paths, accounts not to touch.
- Window and limit: schedule, max rate, duration.
- Accounts/data authorized for proof (what may be used).
- Detected target type: `repo` (code only), `web/api` (HTTP), `other` (mobile/desktop/cloud -> extra scope to negotiate, default = static review + inventory).

Without a contract: stay on static/passive and report what is missing.

`tools/init.py` in the target repo creates the structure and confirms `.devin/scratch/` is gitignored - a tool-verified stop condition, not goodwill.

## Step 1: static and passive (zero packets to target)

- **In own repo**: dependency manifests and lockfiles, routes, handlers, input sinks, committed secrets, security configs, CI workflows.
- **Public sources**: `tools/recon.py --domain X` covers CT logs (crt.sh), Wayback CDX, and DNS/TXT/CNAME via DoH. Add: Common Crawl, GitHub/code search with domain/org/endpoint names, file-and-panel dorks.
- **Fingerprint**: tech stack via headers/cache, favicon hash, DNS/TXT records (reveal SaaS), CNAMEs to third parties (recon.py flags takeover candidates = note, do not execute).
- Each source becomes a file under `.devin/scratch/dma/recon/`.

## Step 2: surface mining

`tools/mine.py` over everything collected (and the front mirror, if authorized). What comes out and what to look for:

- Endpoints: `/api/`, `/v\d+/`, compiled SPA routes, `action=`, baseURL, `ws(s)://`, `/graphql`.
- Secrets: trufflehog-style regexes; record only location + masked prefix (the tool does this by design).
- DOM sinks: `innerHTML`, `eval`, `v-html`, `postMessage` without origin check, `location.*` as source.
- Deserialization markers: `rO0AB` (Java b64), `__VIEWSTATE`, `O:N:"Class"` (PHP), pickle.
- Prototype pollution: `__proto__`, `constructor[`, recursive merge in own code.
- Skeletons: served `.git/`, `.env`, `*.bak`, open swagger/actuator/debug, parallel legacy API namespace, sourcemaps.
- Feature flags and client-side protections disabled by served config.

## Step 3: minimal read-only probes (inside allowlist)

`tools/probe.py` with Step 2 candidates, one request per candidate, delay >= 2s, GET/HEAD/OPTIONS, no mutation:

- Confirms real existence (200 vs 404 vs out-of-scope redirect = stop).
- Security headers, cookies (Secure/HttpOnly/SameSite), CORS with arbitrary `--origin`.
- Existence oracle: `tools/oracle.py` with `--url "...{id}"` and `--ids valid,invalid` emits `oracle_exists` verdict via status/length/timing/body_sha256 diff.
- Contract-authorized auth: `--auth-env VAR` (secret from env var, never argv) or `--header-file`.
- Result: each lead becomes "confirmed" or "discarded" with the (sanitized) response recorded.

## Step 4: classification and corpus

In `findings.md`, per confirmed lead:

```
[ID][Lead|Vuln][Severity] <asset> <summary>
Minimal repro: <exact request>
Sanitized evidence: <proving excerpt>
Confidence: <what remains unproven>
Suggested fix: <one line>
```

- **Lead**: exposed but impact unproven (served sourcemap, missing header, endpoint that exists but responds empty).
- **Vuln**: proven impact (someone else's data, bypass, execution).
- `payloads.md`: corpus per confirmed vector. Fetch a fresh variant from public corpora (PayloadsAllTheThings, PortSwigger cheat sheets, OWASP WSTG) instead of reciting from memory.

### Vector matrix (corpus by class)

Surface -> classes to consider when building payloads.md:

- **Reflected input/params**: XSS, SSTI (`{{7*7}}`, `${7*7}`), SQLi, NoSQLi (`{"$gt":""}`, `[$ne]`), CMDi (`;id`, `|id`), CRLF (`%0d%0a`), open redirect (`?next=`), LFI/RFI (file/local-URL param), HPP (duplicate param).
- **URL input**: SSRF (webhook, avatar, fetch, import), open redirect, file inclusion.
- **JSON/XML body**: mass assignment (`role`, `is_admin`), XXE (xml content-type), prototype pollution (`__proto__` in JSON), deserialization (Step 2 markers).
- **Auth/session**: JWT (jwt_tool decode; gated: alg=none, confusion, kid/jku, local brute), OAuth (state/nonce, redirect_uri), session fixation, predictable reset token, MFA/rate-limit.
- **Object/id in path**: IDOR/BOLA via oracle (Step 3).
- **Header**: host-header injection (reset poisoning, cache), X-Forwarded-* spoof, verb tampering (OPTIONS shows Allow).
- **Cache**: poisoning (reflected unkeyed header/body), deception (`.css` suffix path confusion).
- **Upload**: double extension, content-type lie, polyglot (GIFAR/SVG), filename traversal, XXE in docx/svg/xlsx.
- **WebSocket**: auth only on handshake?, frame injection, CSWSH (Origin unvalidated).
- **GraphQL**: introspection, field suggestion, batching, depth/cost, alias abuse, directive overload.
- **Front/DOM**: Step 2 sinks + sources (location, hash, postMessage), DOM clobbering, client-side traversal.
- **Passive infra**: dangling CNAME (lead; verify is gated), weak TLS/config, CT logs -> forgotten host.

## Step 5: approval for invasive work

The classes below **never** run by default. Each batch needs explicit user approval at the time, with defined scope and quantity:

- Auth/session: JWT (alg=none, RS->HS confusion, kid/jku injection - jwt_tool builds variants offline), OAuth games, session fixation, MFA bypass, rate-limit probing.
- Active bypass: 403 via header/path/method, param pollution, race condition, cache poisoning, cache deception.
- Enumeration: sequentials, mass oracle, ID brute-forcing.
- HTTP request smuggling: CL.TE/TE.CL detection on a proxied target; desync probes risk poisoning others' connections - separate batch, minimal quantity.
- Subdomain takeover verify: confirming a dangling CNAME responds "unclaimed" at the provider (touches a third party = extra approval).
- Credentials: weak-secret brute only on a local copy of the token/artifact (jwt_tool --brute), never online.
- Public CVE PoC: analyze the trigger condition; execute only in an isolated own environment.

## Step 6: orchestrate and report

1. Invoke `web-probe` with the map as the target list (offsec-tools: zap, sqlmap, nuclei, ffuf under engagement contract).
2. A payload that lands = finding with repro; one that fails = tested coverage (record vector + result).
3. Maintain `graph.md`: each new identifier/secret/endpoint records "what does this unlock?". A chain beats an isolated finding.
4. Final report: findings by severity + tested coverage + pending leads + suggested reverts/fixes.

## Immediate stop conditions

- Target resolves/redirects to a host outside the contract (probe.py stops the batch itself).
- Unexpected response containing unplanned PII or secrets.
- Target degrades (persistent 429, chained 5xx - probe.py stops after 3 in a row, backing off).
- Any request that would change state without batch approval.
- `.devin/scratch/` not confirmed gitignored -> move artifacts to a temp dir outside the repo.

## Anti-patterns

- Running active recon before the scope contract.
- Saving a secret/token in cleartext in a dump file.
- Expanding scope "because the CNAME led there".
- Bypassing probe.py's allowlist block by editing scope without telling the user.
- Declaring vuln from a lead: a served sourcemap is exposure, not exploitation. Keep the labels separate.
- Running a public PoC directly against a live target.
- Blind fuzzing with a giant wordlist: the wordlist follows the fingerprint.
- Depending on an installed tool: the technique re-implements in python/curl when the binary is missing (tools/ are pure stdlib).
- Hardcoding target/stack: the technique applies to any authorized target.

## Cascade

- `red-team`: engagement contract + heavyweight tooling orchestration (nmap/zap/sqlmap via offsec-tools).
- `web-probe`: deep testing on the mapped endpoints and forms.
- `security`: found secrets enter the rotation flow; defensive audit of own code.
- `research`: an unknown target may need study first.
