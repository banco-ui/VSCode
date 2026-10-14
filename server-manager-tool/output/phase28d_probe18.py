import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###USM_API_AUTH_ROOT'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/ 2>&1 | head -10
echo '###USM_API_AUTH_V1'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/ 2>&1 | head -10
echo '###USM_API_AUTH_DEPLOY'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/deploy/ 2>&1 | head -10
echo '###USM_API_AUTH_RELEASE'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/release/ 2>&1 | head -10
echo '###SOFTWARE_CLI'
which software 2>/dev/null
software --version 2>&1 | head -5
echo '###SOFTWARE_LIST'
software list 2>&1 | head -20
echo '###SYSINV_HEALTH_UPGRADE'
system health-query-upgrade 2>&1 | head -10
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=20)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
