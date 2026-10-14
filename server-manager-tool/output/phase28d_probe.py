import paramiko
import json
import sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""source /etc/platform/openrc 2>/dev/null
TOKEN=$(openstack token issue -c id -f value 2>/dev/null)
echo '###FM_ALARM_DETAIL_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:18002/v1/alarms 2>&1 | python3 -m json.tool 2>/dev/null
echo '###FM_ALARM_SHOW_CLI'
fm alarm-show 3f8bd835-5c66-468c-9328-928c83f0b11b 2>&1
echo '###FM_ALARM_LIST_JSON'
fm alarm-list --format json 2>/dev/null
echo '###FM_EVENT_LOG_ALT1'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:18002/v1/event_log" 2>&1 | head -20
echo '###FM_EVENT_LOG_ALT2'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:18002/v1/event_logs?limit=5" 2>&1 | head -20
echo '###FM_EVENT_LIST_CLI'
fm event-list 2>&1 | head -30
echo '###SYSINV_HOST_SHOW_JSON'
system host-show controller-0 --format json 2>/dev/null
echo '###SYSINV_HOST_MEMORY_LIST'
system host-memory-list controller-0 2>&1
echo '###SYSINV_HOST_MEMORY_SHOW'
system host-memory-show controller-0 2>&1 | head -80
echo '###SYSINV_IHOSTS_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/ihosts 2>&1 | python3 -m json.tool 2>/dev/null | head -120
echo '###SYSINV_ISYSTEMS_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/isystems 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###SMAPI_NODES_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:7777/v1/nodes/ 2>&1 | python3 -m json.tool 2>/dev/null
echo '###SSH_FREE_H'
free -h
echo '###SSH_PROC_MEMINFO_HEAD'
head -20 /proc/meminfo
echo '###SSH_DMIDECODE_SYSTEM'
sudo dmidecode -t system 2>&1 | head -30
echo '###SSH_DMIDECODE_BASEBOARD'
sudo dmidecode -t baseboard 2>&1 | head -20
echo '###SSH_DMI_PRODUCT_UUID'
cat /sys/class/dmi/id/product_uuid 2>/dev/null
echo '###SSH_DMI_PRODUCT_SERIAL'
cat /sys/class/dmi/id/product_serial 2>/dev/null
echo '###SSH_DMI_PRODUCT_NAME'
cat /sys/class/dmi/id/product_name 2>/dev/null
echo '###SSH_MACHINE_ID'
cat /etc/machine-id 2>/dev/null
echo '###SSH_HOSTNAME'
hostname
echo '###SSH_DMESG_PLATFORM_MEM'
dmesg 2>/dev/null | grep -i "platform.*memory\|memory.*threshold\|mem.*alloc" | tail -20
echo '###SYSINV_HOST_CPU_LIST'
system host-cpu-list controller-0 2>&1 | head -40
echo '###SYSINV_INODES_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:6385/v1/inodes 2>&1 | python3 -m json.tool 2>/dev/null | head -60
echo '###SYSINV_IMEMORYS_SUBRESOURCE'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:6385/v1/ihosts/a7aa8774-c383-4641-ba1d-dc13c1dee91d/imemorys" 2>&1 | python3 -m json.tool 2>/dev/null | head -120
echo '###SYSINV_IDISKS_SUBRESOURCE'
curl -sk -H "X-Auth-Token: $TOKEN" "http://192.168.204.1:6385/v1/ihosts/a7aa8774-c383-4641-ba1d-dc13c1dee91d/idisks" 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###USM_DEPLOY_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/deploy 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###USM_RELEASE_REST'
curl -sk -H "X-Auth-Token: $TOKEN" http://192.168.204.1:5492/v1/release 2>&1 | python3 -m json.tool 2>/dev/null | head -80
echo '###USM_DEPLOY_CLI'
usm deploy show 2>&1 | head -30
echo '###USM_RELEASE_CLI'
usm release list 2>&1 | head -30
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=120)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
