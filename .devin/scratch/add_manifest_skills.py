import json, hashlib, datetime, re

mpath = 'manifest.json'
m = json.load(open(mpath, encoding='utf-8'))
names = {s['name'] for s in m['skills']}
now = datetime.datetime.now().isoformat()

def desc(path):
    txt = open(path, encoding='utf-8').read()
    mm = re.search(r'^description:\s*(.*)$', txt, re.M)
    return mm.group(1).strip() if mm else ''

new = [
    ('lean-code', 'created:v3.18.0 reels-adoption (port of DietrichGebert/ponytail, MIT)', 'skills/lean-code/SKILL.md'),
    ('security-audit-cf', 'vendored:v3.18.0 cloudflare/security-audit-skill (MIT)', 'skills/security-audit-cf/SKILL.md'),
    ('shorts-factory', 'created:v3.18.0 reels-adoption (MoneyPrinterTurbo-equivalent assembly)', 'skills/shorts-factory/SKILL.md'),
]
for name, source, path in new:
    if name in names:
        print('already present:', name)
        continue
    h = hashlib.sha256(open(path, 'rb').read().replace(b'\r\n', b'\n')).hexdigest().upper()
    m['skills'].append({
        'name': name,
        'source': source,
        'purpose': desc(path),
        'original_path': '%APPDATA%\\devin\\skills\\' + name,
        'export_hash': h,
        'exported_at': now,
    })
    print('added', name)

m['skills'].sort(key=lambda s: s['name'])
m['skill_count'] = len(m['skills'])
open(mpath, 'w', encoding='utf-8', newline='\n').write(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
print('skill_count =', m['skill_count'])
