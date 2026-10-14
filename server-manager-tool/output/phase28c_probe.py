import paramiko
import sys
import json

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

# First, source the openrc to get Keystone token, then probe each API
cmds = r"""echo '###KEYSTONE_TOKEN'
source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo "TOKEN_LEN=${#TOKEN}"
echo '###SYSINV_API_VERSION'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/ 2>&1 | head -50
echo '###SYSINV_ISYSTEMS'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/isystems 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SYSINV_IHOSTS'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/ihosts 2>&1 | python3 -m json.tool 2>/dev/null | head -120
echo '###SYSINV_INODES'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/inodes 2>&1 | head -20
echo '###SYSINV_ETHERNET'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/iinterfaces 2>&1 | head -10
echo '###FM_API'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:18002/ 2>&1 | head -20
echo '###FM_ALARMS'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:18002/v1/alarms 2>&1 | python3 -m json.tool 2>/dev/null | head -100
echo '###FM_EVENTS'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:18002/v1/events?limit=5" 2>&1 | head -30
echo '###USM_API'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/ 2>&1 | head -20
echo '###USM_DEPLOY'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/deploy 2>&1 | head -30
echo '###USM_RELEASE'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/release 2>&1 | head -30
echo '###VIM_API'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:4545/ 2>&1 | head -20
echo '###VIM_DETAIL'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:4545/v1/ 2>&1 | head -20
echo '###SMAPI_API'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/ 2>&1 | head -20
echo '###SMAPI_V1'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/ 2>&1 | head -20
echo '###SYSINV_HOST_LIST_CLI'
system host-list --format json 2>/dev/null | head -30
echo '###SYSINV_HOST_SHOW_CLI'
system host-show 1 --format json 2>/dev/null | head -80
echo '###FM_ALARM_LIST_CLI'
fm alarm-list --format json 2>/dev/null | head -50
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=45)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
