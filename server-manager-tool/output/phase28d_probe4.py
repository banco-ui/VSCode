import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###USM_DEPLOY_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/deploy 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###USM_RELEASE_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/release 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###USM_DEPLOY_CLI'
usm deploy show 2>&1 | head -30
echo '###USM_RELEASE_CLI'
usm release list 2>&1 | head -30
echo '###REDFISH_SYSTEM'
curl -sk -u root:W!ndR00tUser https://10.254.174.17/redfish/v1/Systems 2>&1 | python3 -m json.tool 2>/dev/null | head -40
echo '###REDFISH_SYSTEM_DETAIL'
SYSURL=$(curl -sk -u root:W!ndR00tUser https://10.254.174.17/redfish/v1/Systems 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null)
echo "SYSURL=$SYSURL"
curl -sk -u root:W!ndR00tUser "https://10.254.174.17$SYSURL" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###REDFISH_MEMORY'
curl -sk -u root:W!ndR00tUser "https://10.254.174.17${SYSURL}/Memory" 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###REDFISH_PROCESSOR'
curl -sk -u root:W!ndR00tUser "https://10.254.174.17${SYSURL}/Processors" 2>&1 | python3 -m json.tool 2>/dev/null | head -40
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
