---
name: dead-wire
description: Use when running completeness audits, before declaring "it works", or when something looks too implemented to be true. Hunts cut wires: features that look alive but are dead - tables never populated, buttons leading nowhere, events without emitter or listener, flags without write path, request fields the server ignores.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, exec]
---

# Dead Wire

Every feature is a circuit: producer -> wire -> consumer. A wire cut at either end = a dead feature dressed as alive. The dev saw the button render and called it done; nobody asked whether the other side exists.

## Why this finds things

Large software accumulates half-circuits: the UI shipped, the handler never did; the log is written, the reader never was; the flag is consulted, the screen that turns it on was cut from the MVP. No test catches it because the live part works and the dead part only produces silence.

## Classes of cut wire

### 1. Write without read (sinkhole)

Table/log/metric populated by code nobody reads. Looks like audit; it is disk occupation.

- Grep the table both ways: who `::create`/`insert` vs who `->where`/select/`->get`
- Same for a column: written on every INSERT, never appearing in SELECT or a view

### 2. Read without write (ghost flag)

Setting/config/column consulted that nobody can populate. The `if` exists; the condition is always the same.

- `Setting::where('name','x')` read but no UI/migration/seeder creates 'x'
- Column with a default no write path touches: `use_biometric_login` `default(true)` with no endpoint writing it = vestigial feature flag disguised as config
- Enum/constant value no producer emits

### 3. Disconnected event (one loose end)

- Listener without emitter: `#[On('x')]` / `addEventListener('x')` / `->on('x')` no `dispatch`/`emit`/`dispatchEvent` produces
- Emitter without listener: `dispatch('x')` nobody listens to = action vanishing into the void
- Method: grep the exact event name across the whole codebase (emitter + listener). One match only = cut wire

### 4. Action without destination (decorative button)

- `wire:click="foo"` without `public function foo()` in the component = silent error on click
- `href="#"`, `href="javascript:void"`, `route('name')` of a removed route, form with action to a 404
- `@click`/`onclick` calling a JS function absent from the bundle
- Menu/dropdown item with neither wire:click nor href
- UI disabled "temporarily" for 2 years

### 5. Asymmetric payload (client speaks, server deaf)

- Field sent in the request the server neither reads nor validates: app sends `device_name`, request expects `device_info` = telemetry dead since the first commit
- DTO/FormRequest field no consumer uses afterwards
- Route param ignored in the handler
- Grep the field name at both ends: producer (request/DTO/JS) and consumer (validation, controller, model)

### 6. Dead route

- Registered route whose controller always redirects elsewhere (handler never does what the name says)
- View referencing a removed `route('x')`
- Endpoint that only validates and returns a stub: `return response()->json(['ok'=>true])` with no effect

### 7. Branch that never runs

- `if` whose condition is impossible given the type/prior validation (`if ($x === null)` after `required`)
- `catch` of an exception the try never throws
- `switch` missing the cases the data can produce
- `default:` swallowing every valid value

### 8. Placeholder in production

- `// [FIX]`, `// TODO`, `// HACK`, `return true`, `return []` on a production path
- `abort(501)`, `dd()`, `dump()`, `var_dump`, live `console.log` in release
- Function whose body is a comment plus a default return

### 9. Zombie state

- Soft-delete that only hides in UI but stays functional (deleted profile still authenticates)
- `status`/`active` column nothing consults on the auth path
- Cache/flag "already processed" never set = processes every time

### 10. Divergent parallel implementation (redundancy that becomes a hole)

Same business operation via two paths: web vs API, controller vs Livewire, old handler vs new, admin vs self-service. They diverge silently and the weaker path defines the real level.

- Example: `markCard` web verifies biometry server-side; the API `mark-card` lacks even a proof field = verification "exists" but the product does not require it
- Fix drift: a fix applied to one implementation, the other stays vulnerable. Whenever you find a fix, grep the same business effect in other handlers
- Duplicate check where the second cannot fail (or is unreachable): cosmetic redundancy masking the hole
- Two audit trails with different coverage: consulting only one misses the rest
- Method: grep the business effect (`Model::create`, `->save()`, the core query) instead of the function name. Each write site is a path to compare authz/validation side by side

## Hunting method

### 0. Context (parameterize before searching)

Without a target the sweep becomes noise. Before the first grep, pin down:

- **Scope**: one feature, one entity, one circuit (button X to the database), or a general sweep of a module
- **Expected business effect**: what does the user think happens? The dead feature is the gap between that contract and reality
- **Circuit ends**: at least one concrete end per direction - an event name, a column, a route, a method. Grep without an exact name proves no absence
- **Parallel surfaces**: list ALL paths producing the same effect (web/API/Livewire/job/console). The preferred target is the least-watched one
- **Expected output**: `X with Y` should produce `Z`. Without that, "dead" is undecidable
- If the user gave no scope, prioritize by the cost of silence: audit > authz > money > state > cosmetic

### Steps

1. **Pairing**: for each producer, grep the consumer; for each consumer, grep the producer. Exact name of the event, column, route, setting
2. **Bidirectional on new flow**: incoming request -> field by field, does each appear in the handler? Does each handler field appear in the response/DTO the client reads?
3. **Parallels**: grep the business effect (`Model::create`, the core query) and compare each site: same authz? same validation? same audit? Divergence = finding
4. **Table by table** on new schema: every table has at least one live write path and one live read path
5. **UI sweep**: every visible `wire:click`, `href`, `form action`, `@click` on a page resolves to a destination
6. **Flag sweep**: every `if (config|setting|flag)` has a producer of the value
7. **Runtime** when possible: use the feature and check the trail (log, table, network). Total silence = dead even with code looking wired

## Commands that prove

```bash
# emitter without listener / listener without emitter
grep -rn "dispatch('event'" . ; grep -rn "On('event'" .
# column written but never read
grep -rn "'column'" app/ | grep -v migration
# request field unused
grep -rn "field" app/Http app/Livewire
# route without a real handler
grep -rn "function methodName" app/
```

## Evidence and honesty

- Absence of a grep match is evidence OF a cut wire, provided the search covered both ends (event/column/route name on both sides). Paste both greps in the report
- Distinguish: `confirmed dead` (both ends proven absent) / `probably dead` (pattern and context suggest, runtime unproven) / `intentionally vestigial` (commented WIP, documented feature flag)
- Live test when safe: click the button and see nothing happen + nothing in the log + nothing on the network = evidence triad
- Beware indirection: the consumer may live in a job, queue, vendor package, or external webhook. Grep the whole codebase before declaring dead; absence in the repo does not prove absence in the world

## Delivery

Each finding: what the user sees (button, flag, "audit"), the missing end (method, emitter, write path), the two greps, and whether the impact is cosmetic (dead UI), data (sinkhole), or trust (audit that does not audit).
