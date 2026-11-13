import argparse
import ast
import json
from collections import Counter
from pathlib import Path
import re
import runpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    text = (root / "swe2-action-capabilities.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (C[1-5]-[FCA]\d{2}) \| (.+)$", text, re.MULTILINE)
    expected = {f"C{category}-{pillar}{i:02}" for category in range(1, 6) for pillar in "FCA" for i in range(1, 11)}
    ids = [identifier for identifier, _ in rows]
    assert len(ids) == 150 and set(ids) == expected, "matrix IDs missing, duplicate or unexpected"
    groups = Counter(identifier[:4] for identifier in ids)
    assert len(groups) == 15 and set(groups.values()) == {10}
    definitions = re.findall(r"^\[([SL]\d+)\]:\s+(\S+)", text, re.MULTILINE)
    assert len(definitions) == len(dict(definitions)), "duplicate reference definition"
    references = dict(definitions)
    used = set(re.findall(r"\[([SL]\d+)\](?!:)", text))
    assert used <= references.keys(), f"unresolved references: {used - references.keys()}"
    for identifier, body in rows:
        assert re.search(r"\[[SL]\d+\]", body), f"uncited matrix row: {identifier}"
        assert len(body.split(" | ")) == 3, f"malformed matrix row: {identifier}"
    for identifier, target in definitions:
        if identifier.startswith("L"):
            assert (root / target).is_file(), f"missing local source: {target}"
        else:
            assert target.startswith("https://"), f"unexpected source scheme: {target}"
    print(f"matrix: {len(ids)} unique vectors; {len(groups)} groups x 10; references resolved")
    if args.matrix_only:
        return
    assert "_PENDENTE" not in text, "unfinished report section"
    for axis in "ABCDEF":
        assert f"### Eixo {axis} —" in text, f"missing axis {axis}"
    for heading in ("### 4.1 Mecanismos de input", "### 4.2 Captura e renderização", "### 4.3 Benchmarks publicados", "### 4.4 Protocolo local proposto", "### 5.1 Minimum jerk", "### 5.2 Digramas e trigramas", "### 6.1 Contratos", "### 6.2 Etapas e critérios de aceite"):
        assert heading in text, f"missing deliverable: {heading}"
    assert "não resultados locais" in text
    source = ast.parse((root / "swe2_action_models.py").read_text(encoding="utf-8"))
    functions = {node.name: ast.dump(node) for node in source.body if isinstance(node, ast.FunctionDef)}
    embedded = {}
    for block in re.findall(r"```python\n(.*?)\n```", text, re.DOTALL):
        for node in ast.parse(block).body:
            if isinstance(node, ast.FunctionDef):
                assert node.name not in embedded, "duplicate embedded function"
                embedded[node.name] = ast.dump(node)
    assert embedded == functions, "report prototypes differ from executable source"
    json_blocks = re.findall(r"```json\n(.*?)\n```", text, re.DOTALL)
    assert len(json_blocks) == 3, "expected three contract examples"
    for block in json_blocks:
        json.loads(block)
    print("embedded Python matches source; 3 JSON contracts parse")
    runpy.run_path(str(root / "swe2_action_models.py"), run_name="__main__")
    print("report structural checks: PASS (not an external-fact or performance certification)")


if __name__ == "__main__":
    main()
