# 05 -- --backup silently does nothing for directories (skills, docs, extensions)
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P2
- **File**: install.sh:64-76, install.ps1:118-129

## Evidence
install.sh `backup_file` guards with `[[ -f "$file" ]]` (line 66). It is called
on directories at lines 290 (skills), 532 (extensions), 621 (docs): `-f` fails,
function returns, no backup, no warning. The user asked for backups before a
destructive `rm -rf "$dst_dir"` (line 292) and gets none.

install.ps1 has the mirror bug: `Install-SkillDir` calls `Backup-File $dst`
on a directory (line 211); `Backup-File` then runs `Copy-Item $path $bPath
-Force` without `-Recurse` (line 126), which copies an empty directory
container, not the skill contents. (`Backup-Dir` exists and recurses, but is
only used for the legacy config dir.)

## Recommendation
install.sh: dispatch on type -- `[[ -d ]]` -> `cp -r "$file" "$backup"`.
install.ps1: in `Install-SkillDir` call `Backup-Dir` instead of `Backup-File`
(or make `Backup-File` detect directories and recurse).

## Tradeoffs
Directory backups are larger; acceptable given --backup is opt-in.

## Verification
`install.sh --force --backup` over an existing skill dir; assert
`<backup>` contains the old SKILL.md, not just an empty dir.

## Answer

backup_file now dispatches on type: `[[ -d ]]` -> `cp -r` recursive backup, so --backup works for skills/docs/extensions dirs before rm -rf. Verified by test_backup_directory_contains_files.
