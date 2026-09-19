#!/usr/bin/env python3
"""Sync skill-derived metadata after merges: manifest purposes, skill_count,
README badge/diagram counts, TOOLS-MAP count. Dev tool for bundle-slim work."""
import json, os, re

m = json.load(open('manifest.json', encoding='utf-8'))
disk = set(os.listdir('skills'))
by_name = {}
for s in disk:
    p = os.path.join('skills', s, 'SKILL.md')
    if os.path.exists(p):
        txt = open(p, encoding='utf-8').read()
        desc = re.search(r'^description:\s*(.+)$', txt, re.M)
        by_name[s] = desc.group(1).strip() if desc else ''

m['skills'] = [s for s in m['skills'] if s['name'] in disk]
have = {s['name'] for s in m['skills']}
for name in sorted(disk - have):
    m['skills'].append({'name': name, 'source': 'devin-bundle', 'purpose': by_name.get(name, '')})
for s in m['skills']:
    d = by_name.get(s['name'], '')
    if d and s.get('purpose', '')[:60] != d[:60] and d.startswith('Use when'):
        s['purpose'] = d
m['skill_count'] = len(disk)
json.dump(m, open('manifest.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
open('manifest.json', 'a', encoding='utf-8').write('\n')
n = len(disk)

def sub_count(path, patterns):
    txt = open(path, encoding='utf-8').read()
    for pat, rep in patterns:
        txt = re.sub(pat, rep, txt, count=1)
    open(path, 'w', encoding='utf-8', newline='').write(txt)

sub_count('README.md', [
    (r'skills-\d+-blue', f'skills-{n}-blue'),
    (r'As \d+ skills são', f'As {n} skills são'),
    (r'Inventário e metadados das \d+ skills', f'Inventário e metadados das {n} skills'),
])
sub_count('docs/TOOLS-MAP.md', [(r'\| \d+ skills \|', f'| {n} skills |')])
print(f'synced: {n} skills')
