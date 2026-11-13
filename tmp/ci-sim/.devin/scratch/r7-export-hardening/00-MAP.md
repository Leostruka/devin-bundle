# R7 export-hardening -- issue map

| Issue | Defect | Sev | Fix |
|---|---|---|---|
| 01 | mcp mask value-only | P2 | SECRET_KEY regex on key names (.sh+ps1) |
| 02 | TOML multiline leak | P2 | skip_until tracking (.sh+ps1) |
| 03 | audit/pytest wrong cwd | P2 | subshell cd / Push-Location |
| 04 | git add -A scope | P3 | scoped path list |
| 05 | python -c path interp | P3 | sys.argv (.sh) |
| 06 | stale bundle entries | P3 | report_stale / Report-Stale |

All 6 fixed in export.sh + mirrored in export.ps1 where applicable
(05 is .sh-only: ps1 already passes paths via argv).
