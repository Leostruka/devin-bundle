# Obsidian Bases Reference

Obsidian Bases (`.base` files) provide database-like views of vault notes. Files contain YAML.

## Structure

```yaml
filters:
  and:
    - 'file.hasTag("module")'

properties:
  status:
    displayName: Status

formulas:
  is_active: 'status == "active"'

views:
  - type: table
    name: "Modules"
    order:
      - file.name
      - status
```

## Key sections

- `filters` — global filters for all views
- `filters.<view>` — view-specific filters
- `formulas` — computed properties (`formula.<name>`)
- `properties` — display names and settings
- `summaries` — aggregate formulas (Sum, Average, etc.)
- `views` — one or more views (`table`, `cards`, `list`, `map`)

## Filter operators

`==`, `!=`, `>`, `< `, `>=`, `<=`, `&&`, `||`, `!`

## File properties

| Property | Description |
|----------|-------------|
| `file.name` | File name |
| `file.path` | Full vault path |
| `file.folder` | Parent folder |
| `file.tags` | All tags |
| `file.links` | Outgoing wikilinks |
| `file.backlinks` | Incoming wikilinks |
| `file.properties` | Frontmatter object |

## Formula functions

| Function | Description |
|----------|-------------|
| `if(c, t, f)` | Conditional |
| `date(s)` | Parse date |
| `now()` | Current date/time |
| `today()` | Today at 00:00 |
| `file(path)` | Get file object |
| `link(path, text)` | Create a link |

## Gotchas

- Quote strings that contain special YAML characters.
- Access `formula.X` only after defining `X` in `formulas`.
- Duration arithmetic: `(now() - file.ctime).days`.
