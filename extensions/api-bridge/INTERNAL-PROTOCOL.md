# Devin CLI internal inference protocol (recon 2026-11-11)

Reverse-engineered from `devin.exe` 3000.12.43 traffic (see `recon/`).
**Undocumented, unstable — may break on any CLI update. Use locally only;
account-risk applies (product credential on non-public endpoint).**

## Transport

Connect-RPC server-streaming over HTTPS:

```
POST {api_server_url}/exa.api_server_pb.ApiServerService/GetChatMessage
content-type: application/connect+proto
connect-protocol-version: 1
authorization: Basic base64(<windsurf_api_key>)
```

- `api_server_url` from `credentials.toml` (`https://server.codeium.com`).
- Override: env `WINDSURF_API_SERVER_URL` (accepts http for capture).
- Auth accepts `Basic base64(key)`, `Basic base64(raw-jwt)`; the CLI's own
  blob is `base64(<150B binary prefix><jwt header|payload|sig>)` — prefix not
  required server-side.
- `windsurf_api_key` = `devin-session-token$<JWT>`; JWT payload:
  `{"session_id":"windsurf-session-<hex>"}`.
- Envelope: 1B flags + 4B BE len; flag&1 = gzip, flag==2 = end-stream
  trailer (JSON `{}` or `{"error":{...}}`).

## Service surface observed

`exa.api_server_pb.ApiServerService`:
`GetChatMessage` (server-stream, inference), `GetCliModelConfigs`,
`GetAccountManagedPlugins`, `GetDevstralStream`, `AssignModel`,
`JudgeToolCall`, `GetImageCaption`, `GetWebSearchResults`,
`ShareCodeMap`, `GetSharedCodeMap`, `RecordTrajectorySegmentEvents`,
`AddUserManagedPlugin`, `RemoveUserManagedPlugin`, `SubmitBugReport`,
`GetChatMessage` unary siblings.

`exa.seat_management_pb.SeatManagementService`: `GetUserStatus`,
`GetCliTeamSettings` (unary `application/proto`).

`exa.product_analytics_pb.ProductAnalyticsService`:
`BatchRecordAnalyticsEvents`.

## GetChatMessageRequest (single connect frame)

```
f1  meta:   f1 ide_name 'devin-cli' · f2 version '3000.12.43'
            f3 windsurf_api_key (verbatim) · f4 'en' · f5 'windows'
            f7 version · f12 'chisel' · f28 'chisel' · f31 fingerprint(hex, 732B, optional)
f2  system prompt (string; or msg for large prompts)
f3* message: f1 uuid · f2 role (1=user,2=assistant,4=tool) · f3 text
            f6 ToolCall{f1 '<name>:<n>#<hex>', f2 name, f3 args_json}
            f7 tool_call_id (role=4 results)
            f8 bytes \x08\x01 (user/tool msgs)
            f11 reasoning text · f12 'sealed.v1.<b64>' seal
            f18 'sealed' · f22 model_uid   (assistant msgs)
f7  mode varint (5 observed)
f8  modelcfg: f1 1 · f2 128000 (ctx) · f3 400 (max_out) · f5 f64 · f7 40 · f8 f64
f10* tool:    f1 name · f2 description · f3 json_schema(string)
f15 msg:      f1 uuid · f2 1 · f3 4
f16 request uuid
f20 varint 1
f21 agent/model label ('swe-2-max', 'session-titler')
f22 uuid
f28 'user-<uid>:<session-slug>'
```

## GetChatMessageResponse (stream frames, one message each)

```
f1  'bot-<uuid>' message id            f12 f64 timestamp
f2  timestamp msg {f1 sec, f2 nsec}    f15 output_id 'msg_...'
f3  delta_text                         f17 request uuid
f5  varint (tool-call seq, seen 10)    f21 model/provider str
f6  delta_tool_calls:                  f25 stop_reason ('final_answer')
      f1 'exec:0#<hex>' id             f28 Token Usage notification
      f2 name                            f1 'Token Usage' · f2* dims
      f3 args_json                         f5 'input_tokens' · f4{f1 label,f2 f32 val}
f7  usage: f2 prompt_tok · f3 out_tok
    f5 cached? · f6 ? · f9 model_uid
f9  delta_thinking
f10 sealed blob 'sealed.v1.<b64>'  (f21='sealed' in that frame)
f10 (other frames) raw upstream JSON blob '[{"id":"rs_..."'
```

## Sealing (state integrity)

Every assistant response segment is sealed (`sealed.v1.<b64>`). When the
conversation continues (tool-result turn), the assistant message must echo:
f6 ToolCall + f11 reasoning + **f12 seal** + f18 'sealed' + f22 model_uid.
The bridge stores seals keyed by tool_call_id and re-injects them —
harnesses never see them (OpenAI schema has no field).

## Multi-turn tool loop

1. Harness → OpenAI req → bridge → GetChatMessage (tools f10*)
2. Stream f6 deltas → OpenAI `tool_calls` chunks (index by f5 seq)
3. Harness executes → sends `role:tool` + `tool_call_id`
4. Bridge rebuilds: assistant msg {role 2, f6 ToolCall, f12 seal, f18, f22}
   + tool msg {role 4, f3 output, f7 tool_call_id, f8 \x08\x01} → next call.

## Model uids (GetCliModelConfigs, ~1000)

`swe-2-max`, `swe-2-flash-*`, `swe-1p6`, `gpt-5-*`, `gpt-6-*`,
`claude-*`, `gpt-6-luna-low` (title-gen). Errors observed:
`unknown` (capacity), `invalid_argument` (shape), `permission_denied`
(model not entitled), `internal`/`unimplemented` (stale ids on replay).

## Failure modes observed

- Replayed requests fail `internal` — ids/seals single-use.
- Missing f15/f28/meta fields → `invalid_argument`.
- Empty response bodies from gate calls → CLI aborts before inference.
