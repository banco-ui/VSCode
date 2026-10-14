"""Phase 1-RF Live Validation Test Script"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server_manager.collectors.redfish import RedfishCollector

servers = [
    {'name': 'Dell XR11', 'host': '10.254.174.17', 'user': 'root', 'pass': 'calvin'},
    {'name': 'Dell R750', 'host': '10.254.171.113', 'user': 'root', 'pass': 'calvin'},
    {'name': 'HPE e910t', 'host': '10.254.170.196', 'user': 'admin', 'pass': 'password'},
]

results = []

for srv in servers:
    print(f"\n=== Testing {srv['name']} ({srv['host']}) ===")
    try:
        coll = RedfishCollector(
            host=srv['host'],
            port=443,
            username=srv['user'],
            password=srv['pass'],
            verify_ssl=True,  # Phase 0.2: TLS verification enabled
            timeout=10
        )
        data = coll.collect()
        status = 'PASS'
        model = data.get('system', {}).get('Model', 'unknown') if data else 'unknown'
        manufacturer = data.get('system', {}).get('Manufacturer', 'unknown') if data else 'unknown'
        redfish_ver = data.get('redfish_version', 'unknown') if data else 'unknown'
        print(f'Status: {status}')
        print(f'Redfish Version: {redfish_ver}')
        print(f'Model: {model}')
        print(f'Manufacturer: {manufacturer}')
        results.append({'name': srv['name'], 'host': srv['host'], 'status': status, 'model': model, 'tls': 'PASS'})
    except Exception as e:
        error_msg = str(e)
        if 'SSL' in error_msg.upper() or 'CERTIFICATE' in error_msg.upper() or 'verify' in error_msg.lower() or 'CERT' in error_msg.upper():
            status = 'BLOCKED'
            reason = 'TLS Certificate Verification Failed (Self-signed cert)'
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            status = 'FAIL'
            reason = 'Authentication Failed (401)'
        elif 'Connection' in error_msg or 'Timeout' in error_msg or 'refused' in error_msg or 'ENOTFOUND' in error_msg:
            status = 'BLOCKED'
            reason = 'Connection Failed'
        else:
            status = 'FAIL'
            reason = error_msg[:100]
        print(f'Status: {status}')
        print(f'Reason: {reason}')
        results.append({'name': srv['name'], 'host': srv['host'], 'status': status, 'reason': reason, 'tls': 'FAIL' if 'TLS' in reason else 'N/A'})

print("\n\n=== SUMMARY ===")
for r in results:
    print(f"{r['name']} ({r['host']}): {r['status']}")