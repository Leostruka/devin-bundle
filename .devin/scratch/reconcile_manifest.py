import json, hashlib, datetime, re, os

mpath = 'manifest.json'
m = json.load(open(mpath, encoding='utf-8'))
now = datetime.datetime.now().isoformat()

def sha(path):
    return hashlib.sha256(open(path, 'rb').read().replace(b'\r\n', b'\n')).hexdigest().upper()

def desc(path):
    txt = open(path, encoding='utf-8').read()
    mm = re.search(r'^description:\s*(.*)$', txt, re.M)
    return mm.group(1).strip() if mm else ''

new_skills = [
    ('thermo-nuclear-code-quality-review', 'vendored:v3.19.0 cursor/plugins thermos (MIT)'),
    ('thermo-nuclear-review', 'vendored:v3.19.0 cursor/plugins thermos (MIT)'),
    ('thermos', 'vendored:v3.19.0 cursor/plugins thermos (MIT), adapted to run_subagent'),
    ('unslop', 'vendored:v3.19.0 cursor/plugins pstack (MIT)'),
    ('typescript-best-practices', 'vendored:v3.19.0 cursor/plugins pstack (MIT), principle refs inlined'),
    ('vercel-react-best-practices', 'vendored:v3.19.0 vercel-labs/agent-skills (MIT)'),
    ('no-comments', 'created:v3.19.0 port of pstack no-comments (MIT)'),
    ('de-slop', 'created:v3.19.0 composite simplification pass'),
]
sk_names = {s['name'] for s in m['skills']}
for name, source in new_skills:
    p = 'skills/' + name + '/SKILL.md'
    if name in sk_names:
        print('skill present:', name); continue
    m['skills'].append({
        'name': name, 'source': source, 'purpose': desc(p),
        'original_path': '%APPDATA%\\devin\\skills\\' + name,
        'export_hash': sha(p), 'exported_at': now})
    print('added skill', name)
m['skills'].sort(key=lambda s: s['name'])
m['skill_count'] = len(m['skills'])

new_agents = ['thermo-nuclear-review-subagent', 'thermo-nuclear-code-quality-review-subagent']
ag_names = {a['name'] for a in m['agents']}
for name in new_agents:
    p = 'agents/' + name + '.md'
    if name in ag_names:
        print('agent present:', name); continue
    m['agents'].append({
        'name': name, 'source': 'vendored:v3.19.0 cursor/plugins thermos (MIT)',
        'original_path': '%APPDATA%\\devin\\agents\\' + name + '.md',
        'export_hash': sha(p), 'exported_at': now})
    print('added agent', name)
m['agents'].sort(key=lambda a: a['name'])
m['agent_count'] = len(m['agents'])

open(mpath, 'w', encoding='utf-8', newline='\n').write(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
print('skill_count =', m['skill_count'], 'agent_count =', m['agent_count'])
