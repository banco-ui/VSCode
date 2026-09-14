import urllib.request, json, sys

# Read-only GET probes only - NO mutations
endpoints = [
    ('GET', '/api/servers'),
    ('GET', '/api/switches'),
    ('GET', '/api/dashboard/summary'),
    ('GET', '/api/topology'),
    ('GET', '/api/physical'),
    ('GET', '/api/sdn-flavors'),
    ('GET', '/api/validation/profiles'),
    ('GET', '/api/alerts/rules'),
    ('GET', '/api/alerts/stats?days=30'),
    ('GET', '/api/misc-devices'),
    ('GET', '/api/audit/cycles'),
    ('GET', '/api/testbeds/settings'),
    ('GET', '/api/install/wrcp/templates'),
    ('GET', '/api/backup/preview'),
    ('GET', '/api/tasks/nonexistent-read-only'),
]

results = {}
for method, path in endpoints:
    url = f'http://10.251.213.91:30080{path}'
    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('Accept', 'application/json')
        r = urllib.request.urlopen(req, timeout=10)
        body = r.read().decode('utf-8')
        ct = r.headers.get('Content-Type', '')
        results[path] = {
            'status': r.status,
            'content_type': ct,
            'body_preview': body[:500],
            'body_length': len(body),
            'is_json': 'json' in ct,
        }
    except urllib.error.HTTPError as e:
        results[path] = {
            'status': e.code,
            'error': str(e),
        }
    except Exception as e:
        results[path] = {
            'status': 'ERROR',
            'error': str(e),
        }

print(json.dumps(results, indent=2, ensure_ascii=False))
