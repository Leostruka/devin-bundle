import json
m=json.load(open('manifest.json',encoding='utf-8'))
bad=[(r['name'],repr(r.get('original_path',''))) for r in m['resources'] if any(ord(c)<32 for c in r.get('original_path',''))]
print('ctrl:',bad[:4])
bs=[r['name'] for r in m['resources'] if chr(92)*2 in r.get('original_path','')]
print('dbl-backslash:',len(bs),bs[:10])
