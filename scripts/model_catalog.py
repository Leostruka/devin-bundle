"""Model catalog drift helpers.

Parses `devin models list` output and compares it against bundle-cached
model facts in data/model-context-windows.json.
"""
import json
import re
import subprocess
from pathlib import Path


def _parse_window(value):
    """Convert a context-window string like '200K' or '1M' to an integer."""
    value = value.strip().replace(",", "")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([KkMm]?)\s*$", value)
    if not m:
        return None
    number, suffix = m.groups()
    number = float(number)
    if suffix.lower() == "k":
        number *= 1_000
    elif suffix.lower() == "m":
        number *= 1_000_000
    return int(number)


def parse_devin_models_list(output):
    """Parse `devin models list` plain text into model records.

    Each record contains id, name, context_window, and aliases.
    """
    models = []
    current_family = None
    current_aliases = []

    for line in output.splitlines():
        # Family header: "Family Name (family-slug)"
        family_match = re.match(r"^([A-Za-z0-9\s\.\-\(\)]+?)\s+\(([a-zA-Z0-9\-\_\.]+)\)\s*$", line)
        if family_match:
            current_family = family_match.group(2).strip()
            current_aliases = []
            continue

        # Aliases line: "  aliases: alias1, alias2"
        alias_match = re.match(r"^\s+aliases:\s*(.+)$", line)
        if alias_match:
            current_aliases = [a.strip() for a in alias_match.group(1).split(",") if a.strip()]
            continue

        # Model line: "  model-id                          Model Name  [200K context, ...]"
        model_match = re.match(
            r"^\s+([A-Za-z0-9_\-]+)\s+([A-Za-z0-9\s\.\-\(\)]+?)\s+\[(\S+)\s+context",
            line,
        )
        if model_match:
            model_id = model_match.group(1).strip()
            name = model_match.group(2).strip()
            window = _parse_window(model_match.group(3))
            models.append({
                "id": model_id,
                "name": name,
                "context_window": window,
                "aliases": current_aliases,
                "family": current_family,
            })

    return models


def load_bundle_models(path="data/model-context-windows.json"):
    """Load the bundle's cached model facts."""
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        return []
    data = p.read_text(encoding="utf-8-sig")
    return json.loads(data).get("models", [])


def compare_catalogs(cli_models, bundle_models, strict=True):
    """Compare CLI model facts against bundle cached facts.

    Returns (errors, warnings). In strict mode all drift is treated as errors.
    In non-strict mode all drift is reported as warnings so the audit can
    remain green while still surfacing stale catalog data.
    """
    drift = []
    bundle_by_id = {m.get("id", "").lower(): m for m in bundle_models if m.get("id")}

    for cli_model in cli_models:
        mid = cli_model.get("id", "").lower()
        if not mid:
            continue
        bundle_model = bundle_by_id.get(mid)
        if not bundle_model:
            drift.append(f"{cli_model['id']} present in CLI but missing from bundle cache")
            continue
        cli_window = cli_model.get("context_window")
        bundle_window = bundle_model.get("context_window")
        if cli_window is not None and bundle_window is not None and cli_window != bundle_window:
            drift.append(
                f"{cli_model['id']} context_window mismatch: "
                f"bundle {bundle_window} vs CLI {cli_window}"
            )

    cli_ids = {m.get("id", "").lower() for m in cli_models if m.get("id")}
    for bundle_model in bundle_models:
        mid = bundle_model.get("id", "").lower()
        if mid and mid not in cli_ids:
            drift.append(f"{bundle_model['id']} in bundle cache but not reported by CLI")

    if strict:
        return drift, []
    return [], drift


def fetch_devin_models_list():
    """Run `devin models list` and return parsed models."""
    result = subprocess.run(
        ["devin", "models", "list"], capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"devin models list failed: {result.stderr}")
    return parse_devin_models_list(result.stdout)


def run_drift_check(bundle_path="data/model-context-windows.json", cli_output=None, strict=False):
    """Run the drift check.

    If `cli_output` is None, run `devin models list`. Otherwise parse the
    provided string as CLI output. Returns (errors, warnings).
    """
    bundle_models = load_bundle_models(bundle_path)
    if cli_output is None:
        cli_models = fetch_devin_models_list()
    else:
        cli_models = parse_devin_models_list(cli_output)
    return compare_catalogs(cli_models, bundle_models, strict=strict)


if __name__ == "__main__":
    pass
