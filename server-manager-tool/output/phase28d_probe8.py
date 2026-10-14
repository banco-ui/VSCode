import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###REDFISH_SYSTEM_DETAIL'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems/System.Embedded.1 2>&1 | python3 -m json.tool 2>/dev/null | head -100
echo '###REDFISH_MEMORY'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems/System.Embedded.1/Memory 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###REDFISH_CHASSIS_DETAIL'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Chassis 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null
CHURL=$(curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Chassis 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null)
curl -sk -u root:calvin "https://10.254.174.17${CHURL}" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###REDFISH_MANAGER_DETAIL'
MGRURL=$(curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Managers 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null)
curl -sk -u root:calvin "https://10.254.174.17${MGRURL}" 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
