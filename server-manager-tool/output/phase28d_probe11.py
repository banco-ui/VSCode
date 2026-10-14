import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###FM_EVENT_LOG_SINGULAR'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:18002/v1/event_log" 2>&1 | head -10
echo '###FM_EVENTS_PLURAL'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:18002/v1/events" 2>&1 | head -10
echo '###FM_EVENT_LIST_CLI'
fm event-list 2>&1 | head -20
echo '###REDFISH_CHASSIS_HEALTH'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Chassis/System.Embedded.1 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for k in ['Status','HealthRollup','Name','Model','Manufacturer','SerialNumber']:
    print(f'{k}: {d.get(k)}')" 2>&1
echo '###REDFISH_LOGSERVICES'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Managers/iDRAC.Embedded.1/LogServices 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for m in d.get('Members',[]):
    print(m['@odata.id'])" 2>&1
echo '###REDFISH_SEL_LATEST'
curl -sk -u root:calvin "https://10.254.174.17/redfish/v1/Managers/iDRAC.Embedded.1/LogServices/Lclog/Entries" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
entries = d.get('Members',[])
print(f'Total entries: {d.get(\"Members@odata.count\")}')
for e in entries[:10]:
    print(f'  {e.get(\"Created\")} [{e.get(\"Severity\")}] {e.get(\"Message\")}')" 2>&1
echo '###SYSINV_ISYSTEMS_DETAIL'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/isystems 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for s in d.get('isystems',[]):
    for k in ['uuid','name','sw_version','system_mode','system_type','description','capabilities','created_at','updated_at']:
        print(f'{k}: {s.get(k)}')" 2>&1
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
