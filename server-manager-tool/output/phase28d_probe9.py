import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###REDFISH_MEMORY_DETAIL'
MEMURL=$(curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems/System.Embedded.1/Memory 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Members'][0]['@odata.id'])" 2>/dev/null)
echo "MEMURL=$MEMURL"
curl -sk -u root:calvin "https://10.254.174.17${MEMURL}" 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###REDFISH_THERMAL'
curl -sk -u root:calvin "https://10.254.174.17/redfish/v1/Chassis/System.Embedded.1/Thermal" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
