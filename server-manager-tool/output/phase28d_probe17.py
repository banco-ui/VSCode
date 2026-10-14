import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###REDFISH_FAULTLIST'
curl -sk -u root:calvin "https://10.254.174.17/redfish/v1/Managers/iDRAC.Embedded.1/LogServices/FaultList/Entries" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
entries = d.get('Members',[])
print(f'Total fault entries: {d.get(\"Members@odata.count\")}')
for e in entries[:15]:
    print(f'  {e.get(\"Created\")} [{e.get(\"Severity\")}] {e.get(\"Message\")}')" 2>&1
echo '###REDFISH_SEL_LATEST_CRITICAL'
curl -sk -u root:calvin "https://10.254.174.17/redfish/v1/Managers/iDRAC.Embedded.1/LogServices/Sel/Entries" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
entries = d.get('Members',[])
print(f'Total SEL entries: {d.get(\"Members@odata.count\")}')
for e in entries[:15]:
    print(f'  {e.get(\"Created\")} [{e.get(\"Severity\")}] {e.get(\"Message\")}')" 2>&1
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
