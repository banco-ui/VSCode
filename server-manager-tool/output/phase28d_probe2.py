import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###SYSINV_HOST_SHOW_JSON'
system host-show controller-0 --format json 2>/dev/null
echo '###SYSINV_HOST_MEMORY_LIST'
system host-memory-list controller-0 2>&1
echo '###SYSINV_HOST_MEMORY_SHOW'
system host-memory-show controller-0 2>&1 | head -80
echo '###SYSINV_IHOSTS_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/ihosts 2>&1 | python3 -m json.tool 2>/dev/null | head -120
echo '###SMAPI_NODES_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/nodes/ 2>&1 | python3 -m json.tool 2>/dev/null
echo '###SYSINV_IMEMORYS_SUB'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:6385/v1/ihosts/a7aa8774-c383-4641-ba1d-dc13c1dee91d/imemorys" 2>&1 | python3 -m json.tool 2>/dev/null | head -120
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
