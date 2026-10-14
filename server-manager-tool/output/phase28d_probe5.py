import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###FM_ALARMS_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:18002/v1/alarms 2>&1 | python3 -m json.tool 2>/dev/null
echo '###FM_ALARM_SHOW_CLI'
fm alarm-show 3f8bd835-5c66-468c-9328-928c83f0b11b 2>&1
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=20)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
