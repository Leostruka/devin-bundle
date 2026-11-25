"""C13 pin: _hookrun event fallback for eventless payloads.

Residual edge from the two-pass review: when the stdin payload carries no
hook_event_name and a child emits hookSpecificOutput without
hookEventName, the merged output lacked hookEventName and the CLI
rejected it (parse fail -> fail_closed blocks opaquely). The runner now
passes its statically registered event and run() synthesizes
hookEventName from it as last fallback.
"""
import io
import json
import sys

sys.path.insert(0, "scripts")
import _hookrun  # noqa: E402

HSO_ONLY = '{"hookSpecificOutput": {"additionalContext": "ctx"}}'


def _run_with_stub(monkeypatch, capsys, payload, event):
    monkeypatch.setattr(
        _hookrun, "_run_one",
        lambda name, p: (0, HSO_ONLY, ""))
    monkeypatch.setattr(_hookrun, "emit_metric", lambda *a, **k: None)
    rc = _hookrun.run(["stub.py"], payload, event=event)
    return rc, capsys.readouterr().out


def test_eventless_payload_synthesizes_registered_event(monkeypatch, capsys):
    rc, out = _run_with_stub(monkeypatch, capsys, {}, "PreToolUse")
    obj = json.loads(out)
    assert obj["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert rc == 0


def test_payload_event_wins_over_registered(monkeypatch, capsys):
    rc, out = _run_with_stub(
        monkeypatch, capsys,
        {"hook_event_name": "Stop"}, "PreToolUse")
    obj = json.loads(out)
    assert obj["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert rc == 0


def test_no_event_anywhere_keeps_prior_shape(monkeypatch, capsys):
    rc, out = _run_with_stub(monkeypatch, capsys, {}, None)
    obj = json.loads(out)
    assert "hookEventName" not in obj["hookSpecificOutput"]
    assert obj["hookSpecificOutput"]["additionalContext"] == "ctx"
    assert rc == 0


def _consolidation_graph():
    """Registered entry scripts plus the transitive child graph.

    A guard can route to another aggregator (post-exec-guard ->
    post-exec -> grandchildren), so reachability must be transitive.
    Existence-gated like audit_checks.m_rules: quoted py-names without a
    scripts/ file are prose, not children."""
    import os
    import re
    hooks = json.load(open("hooks.v1.json", encoding="utf-8"))
    registered = {}
    for event, blocks in hooks.items():
        for block in blocks:
            for h in block.get("hooks", []):
                m = re.search(r"scripts[\\/]([\w.-]+\.py)", h.get("command", ""))
                if m:
                    registered.setdefault(m.group(1), event)

    def children_of(name):
        path = os.path.join("scripts", name)
        if not os.path.exists(path):
            return set()
        src = open(path, encoding="utf-8").read()
        return {m.group(1) for m in re.finditer(r"['\"]([\w-]+\.py)['\"]", src)
                if os.path.exists(os.path.join("scripts", m.group(1)))}

    # reaches[root] = every script transitively executed under root
    reaches = {}
    for root in registered:
        seen, frontier = set(), [root]
        while frontier:
            cur = frontier.pop()
            if cur in seen:
                continue
            seen.add(cur)
            frontier.extend(children_of(cur) - seen)
        reaches[root] = seen
    return registered, reaches


def test_entry_point_event_literals_match_registration():
    """Tripwire: an `event='X'` literal must match the registration event
    of every entry point that (transitively) executes the script - a stale
    literal would synthesize the WRONG hookEventName on eventless payloads."""
    import os
    import re
    registered, reaches = _consolidation_graph()
    # Reverse index: script -> events of the registered roots reaching it.
    reached_by = {}
    for root, scripts_in_scope in reaches.items():
        for s in scripts_in_scope:
            reached_by.setdefault(s, set()).add(registered[root])
    for path in sorted(os.listdir("scripts")):
        if not path.endswith(".py"):
            continue
        src = open("scripts/" + path, encoding="utf-8").read()
        m = re.search(r"event='(\w+)'", src)
        if not m:
            continue  # direct scripts pass no event literal; nothing to pin
        events = reached_by.get(path, set())
        assert events, path + " passes event= but no registered entry reaches it"
        assert events == {m.group(1)}, (
            path + " executes under " + str(sorted(events))
            + " but passes event=" + m.group(1))


def test_direct_script_event_literals_match_registration():
    """Tripwire: a script run as its OWN hooks.v1.json command that
    hardcodes `"hookEventName": "X"` emits X regardless of the event it
    was actually registered under - re-registering it silently emits the
    wrong event. Pin literal == every registration event."""
    import glob
    import os
    import re
    hooks = json.load(open("hooks.v1.json", encoding="utf-8"))
    registered = {}
    for event, blocks in hooks.items():
        for block in blocks:
            for h in block.get("hooks", []):
                m = re.search(r"scripts[\\/]([\w.-]+\.py)", h.get("command", ""))
                if m:
                    registered.setdefault(m.group(1), set()).add(event)
    # Scripts invoked as modules inside consolidated entry points (e.g.
    # context-pressure.py inside post-exec.py) emit under the ENTRY
    # point's event, not their own registration - their literal is
    # checked transitively by the entry-point pin above, so skip them.
    _, reaches = _consolidation_graph()
    modules = set()
    for scripts_in_scope in reaches.values():
        modules.update(scripts_in_scope)
    for path in glob.glob("scripts/*.py"):
        name = os.path.basename(path)
        if name not in registered or name in modules:
            continue
        literals = set(re.findall(
            r'"hookEventName":\s*"(\w+)"',
            open(path, encoding="utf-8").read()))
        for lit in literals:
            assert registered[name] == {lit}, (
                name + " hardcodes " + lit + " but is registered under "
                + str(sorted(registered[name])))
