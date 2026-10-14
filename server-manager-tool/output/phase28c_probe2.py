import paramiko
import sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###SMAPI_NODES'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/nodes/ 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SMAPI_SERVICE_GROUPS'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/service_groups/ 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SMAPI_SERVICES'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/services/ 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SMAPI_SERVICENODE'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/servicenode/ 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###SMAPI_SM_SDA'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/sm_sda/ 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###FM_ALARM_DETAIL'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:18002/v1/alarms 2>&1 | python3 -m json.tool 2>/dev/null | head -120
echo '###FM_ALARM_LIST_CLI'
fm alarm-list 2>&1 | head -30
echo '###SYSINV_ICPUS'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:6385/v1/icpus" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SYSINV_IDISKS'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:6385/v1/idisks?ihost_id=1" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SYSINV_IMEMORY'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:6385/v1/imemorys?ihost_id=1" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SYSINV_IHOST_SHOW_CLI'
system host-show controller-0 2>&1 | head -60
echo '###SYSINV_PORT_CLI'
system host-port-list controller-0 2>&1 | head -30
echo '###SYSINV_INTERFACE_CLI'
system if-list -a controller-0 2>&1 | head -30
echo '###FM_EVENT_LOGS'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:18002/v1/event_logs?limit=3" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###VIM_API_VERSIONS'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:4545/api/ 2>&1 | head -20
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=45)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
