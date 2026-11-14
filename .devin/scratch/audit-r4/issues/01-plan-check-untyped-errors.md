# Issue: plan_check.py escapes typed-error contract

- **Severity**: P2
- **Status**: resolved
- **File**: `extensions/remotion-render/plan_check.py`

## Evidence

`main()` (lines 88-91):

```python
def main(argv=None):
    plan = json.loads(Path(argv[0] if argv else sys.argv[1])
                      .read_text(encoding="utf-8"))
    print(json.dumps(check(plan), indent=2, ensure_ascii=False))
    return 0
```

No try/except anywhere in the file (ast scan: `has_try: False`).

## Reproduce

```powershell
python extensions/remotion-render/plan_check.py missing.json   # FileNotFoundError traceback
python extensions/remotion-render/plan_check.py bad.json       # JSONDecodeError traceback
echo '[1,2]' > arr.json; python extensions/remotion-render/plan_check.py arr.json   # AttributeError (plan.get on list)
```

`check(plan)` also does `plan.get(...)`, `b.get(...)` per beat without
type guards: `{"beats": "x"}` iterates a string -> AttributeError;
`{"beats": [42]}` -> AttributeError; `{"beats": [{"sync_range":[0,1],
"visual": "x"}]}` -> `vis.get` AttributeError.

## Contract violated

Every other user-facing CLI in the bundle emits typed JSON errors +
exit 2 (`scene_manifest`, `render.py`, `abliterator`, `compact`,
`presets` -- R3 fixes). plan_check is the odd one out; it runs before
the approval gate so its failures are on the user path.

## Acceptance

- Missing/unreadable file -> `{"ok": false, "errors": ["read_error:..."]}` exit 2
- Invalid JSON / non-dict plan -> typed error, exit 2
- Malformed beats entries (non-dict beat, non-dict visual/motion_spec/props)
  reported as per-beat errors, not crash
- Regression tests in `tests/test_animation_pipeline.py` (or sibling)

## Answer

Fixed. `main()` wraps file read (`read_error:`), JSON parse
(`json_error:`), and non-dict plans (`plan must be a JSON object`) in a
typed `{"ok": false, "errors": [...]}` envelope with exit 2. `check()`
gains type guards: `beats` non-list -> per-plan error, non-dict beat ->
`beat{i}: entry must be an object`, non-dict `visual` ->
`{bid}: visual must be an object`, non-dict `props`/`motion_spec` ->
treated as empty. 6 regression tests in `test_animation_pipeline.py`
(missing file, bad JSON, non-dict plan, beats non-list, beat non-dict,
visual non-dict).
