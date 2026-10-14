import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###REDFISH_SYSTEMS_NOAUTH'
curl -sk https://10.254.174.17/redfish/v1/Systems 2>&1 | python3 -m json.tool 2>/dev/null | head -20
echo '###REDFISH_CHASSIS_NOAUTH'
curl -sk https://10.254.174.17/redfish/v1/Chassis 2>&1 | python3 -m json.tool 2>/dev/null | head -20
echo '###REDFISH_MANAGERS_NOAUTH'
curl -sk https://10.254.174.17/redfish/v1/Managers 2>&1 | python3 -m json.tool 2>/dev/null | head -20
echo '###REDFISH_SYSTEM_CALVIN'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems 2>&1 | python3 -m json.tool 2>/dev/null | head -20
echo '###REDFISH_SYSTEM_ROOT_SSH'
curl -sk -u root:W!ndR00tUser https://10.254.174.17/redfish/v1/Systems 2>&1 | python3 -m json.tool 2>/dev/null | head -20
echo '###REDFISH_CHASSIS_DETAIL_NOAUTH'
CHASSISURL=$(curl -sk https://10.254.174.17/redfish/v1/Chassis 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null)
echo "CHASSISURL=$CHASSISURL"
curl -sk "https://10.254.174.17${CHASSISURL}" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###REDFISH_MANAGER_DETAIL_NOAUTH'
MGRURL=$(curl -sk https://10.254.174.17/redfish/v1/Managers 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null)
echo "MGRURL=$MGRURL"
curl -sk "https://10.254.174.17${MGRURL}" 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
