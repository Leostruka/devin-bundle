# JSON Canvas Reference

Canvas files use the `.canvas` extension and contain JSON following the [JSON Canvas Spec 1.0](https://jsoncanvas.org/spec/1.0/).

## Structure

```json
{
  "nodes": [],
  "edges": []
}
```

## Node types

- `text` — Markdown text
- `file` — Reference to a vault file
- `link` — External URL
- `group` — Visual container

## Common node fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | 16-character lowercase hex |
| `type` | Yes | `text`, `file`, `link`, `group` |
| `x` | Yes | X position (px) |
| `y` | Yes | Y position (px) |
| `width` | Yes | Width (px) |
| `height` | Yes | Height (px) |
| `color` | No | `"1"`–`"6"` preset or hex |
| `text` | For `text` | Markdown content (use `\n` for newlines) |
| `file` | For `file` | Vault path to file |
| `url` | For `link` | External URL |
| `label` | For `group` | Group label |

## Edges

```json
{
  "id": "...",
  "fromNode": "<source-id>",
  "toNode": "<target-id>",
  "fromSide": "right",
  "toSide": "left",
  "fromEnd": "none",
  "toEnd": "arrow",
  "color": "2",
  "label": "calls"
}
```

## Validation

- All `id` values must be unique across nodes and edges.
- Every `fromNode` and `toNode` must reference an existing node.
- Use `\n` (not literal newline) inside JSON strings.
- Space nodes 50–100 px apart; align to a 10 or 20 px grid.

## Color presets

| Preset | Use case |
|--------|----------|
| `1` | Red — errors, external risks |
| `2` | Orange — dependencies, external systems |
| `3` | Yellow — data / databases |
| `4` | Green — modules / core logic |
| `5` | Cyan — config / infrastructure |
| `6` | Purple — UI / entry points |
