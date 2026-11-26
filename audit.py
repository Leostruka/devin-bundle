import sys
import re
from audit_checks._ctx import Ctx
from audit_checks import m_contract
from audit_checks import m_integrity
from audit_checks import m_lifecycle
from audit_checks import m_manifest
from audit_checks import m_packages
from audit_checks import m_repo
from audit_checks import m_rules
from audit_checks import m_scripts
from audit_checks import m_sync

ctx = Ctx()

print('=== FULL REPO AUDIT ===')
print()

# 1. All JSON files valid
print('[1] JSON files validation')
m_integrity.c1(ctx)

print('[2] Python scripts validation')
m_integrity.c2(ctx)

print('[2b] Hook script __main__ guard validation')
m_integrity.c2b(ctx)

print('[3] Skill frontmatter validation')
m_integrity.c3(ctx)

print('[4] Manifest sync')
m_integrity.c4(ctx)

print('[5] Manifest version')
m_integrity.c5(ctx)

print('[6] AGENTS.md rules')
m_rules.c6(ctx)

print('[6c] AGENTS.md context budget')
m_rules.c6c(ctx)

print('[7] hooks.v1.json script references')
m_rules.c7(ctx)

print('[7b] config.json / hooks.v1.json schema validation')
m_rules.c7b(ctx)

print('[8] Scripts directory')
m_manifest.c8(ctx)

print('[9] README counts vs reality')
m_manifest.c9(ctx)

print('[9b] manifest.json scripts list')
m_manifest.c9b(ctx)

print('[9c] manifest.json agents')
m_manifest.c9c(ctx)

print('[9d] manifest.json skill hashes')
m_manifest.c9d(ctx)

print('[10] Secrets check')
m_manifest.c10(ctx)

print('[10b] mcp_config.json schema validation')
m_repo.c10b(ctx)

print('[11] .gitignore coverage')
m_repo.c11(ctx)

print('[12] CI workflow')
m_repo.c12(ctx)

print('[13] GitHub templates')
m_repo.c13(ctx)

print('[13b] GitHub governance files')
m_repo.c13b(ctx)

print('[14] Repo docs')
m_repo.c14(ctx)

print('[15] Live vs bundle sync')
m_repo.c15(ctx)

print('[16] Skills live vs bundle sync')
m_sync.c16(ctx)

print('[17] Version consistency')
m_sync.c17(ctx)

print('[18] README badges')
m_sync.c18(ctx)

print('[19] Subagent profiles')
m_sync.c19(ctx)

print('[20] Temp files check')
m_sync.c20(ctx)

print('[21] Git tag vs manifest version')
m_sync.c21(ctx)

print('[22] Export/install scripts')
m_sync.c22(ctx)

print('[22b] Export/install script structural validation')
m_scripts.c22b(ctx)

print('[23] .gitattributes')
m_scripts.c23(ctx)

print('[24] Doc count consistency (TOOLS-MAP.md, SKILL-TIERS.md)')
m_scripts.c24(ctx)

print('[25] Refinement log ID uniqueness')
m_scripts.c25(ctx)

print('[26] Manifest purpose vs SKILL.md description sync')
m_scripts.c26(ctx)

print('[27] No tracked temp artifacts')
m_scripts.c27(ctx)

print('[28] No tracked credential/secret files')
m_scripts.c28(ctx)

print('[29] arXiv refs in scripts/ and tests/ tracked in MODEL-GUIDE.md')
m_lifecycle.c29(ctx)

print('[30] Hook events match Devin CLI lifecycle docs')
m_lifecycle.c30(ctx)

print('[31] Model context windows data file')
m_lifecycle.c31(ctx)

print('[31b] Model free-window transitions')
m_lifecycle.c31b(ctx)

print('[32] CHANGELOG [Unreleased] merge coverage')
m_lifecycle.c32(ctx)

print('[33] Resolved issues carry an Answer section')
m_lifecycle.c33(ctx)

print('[34] Install drift ledger')
m_lifecycle.c34(ctx)

print('[35] tools.json renderers')
m_lifecycle.c35(ctx)

print('[36] CLI exit-code contract')
m_lifecycle.c36(ctx)

print('[37] subprocess utf-8 decode')
m_contract.c37(ctx)

print('[38] file-I/O utf-8 decode')
m_contract.c38(ctx)

print('[39] stdio utf-8 decode')
m_contract.c39(ctx)

print('[40] Skills debt (staleness)')
m_contract.c40(ctx)

print('[41] Compat doc version pin')
m_contract.c41(ctx)

print('[42] stdout utf-8 pin on JSON emitters')
m_contract.c42(ctx)

print('[43] stdlib names used without import')
m_contract.c43(ctx)

print('[44] Python floor compat (3.11)')
m_contract.c44(ctx)

print('[45] --out overwrite-refusal')
m_contract.c45(ctx)

print('[46] Package install/exec refs (slop-squatting guard)')
m_packages.c46(ctx)

print()
print('=== SUMMARY ===')
print('Errors:   ' + str(len(ctx.errors)))
print('Warnings: ' + str(len(ctx.warnings)))
if ctx.errors:
    print()
    print('ERRORS:')
    for e in ctx.errors:
        print('  - ' + e)
if ctx.warnings:
    print()
    print('WARNINGS:')
    for w in ctx.warnings:
        print('  - ' + w)
if not ctx.errors and not ctx.warnings:
    print()
    _n_checks = len(set(re.findall(
        r"^print\('\[(\d+[a-z]?)\]",
        open(__file__, encoding='utf-8').read(), re.M)))
    print('ALL ' + str(_n_checks) + ' CHECKS PASSED - NO ERRORS, NO WARNINGS')
sys.exit(1 if ctx.errors else 0)

