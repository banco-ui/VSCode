import urllib.request, json

urls = [
    '/api/switches',
    '/api/dashboard/summary',
    '/api/alerts/rules',
    '/api/sdn-flavors',
    '/api/misc-devices',
    '/api/admin/teams',
    '/api/validation/profiles',
    '/api/install/wrcp/templates',
    '/api/audit/cycles',
    '/api/testbeds/settings',
]

for u in urls:
    try:
        r = urllib.request.urlopen(f'http://10.251.213.91:30080{u}')
        d = json.loads(r.read().decode())
        print(f'--- {u} ---')
        print(json.dumps(d, indent=2)[:500])
        print()
    except Exception as e:
        print(f'--- {u} --- ERROR: {e}')
        print()
