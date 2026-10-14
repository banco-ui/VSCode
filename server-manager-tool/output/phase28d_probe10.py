import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###REDFISH_SYS_IDENTITY'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems/System.Embedded.1 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for k in ['Manufacturer','Model','SerialNumber','UUID','PartNumber','SKU','HostName','BiosVersion','PowerState','Status','AssetTag','Description','Id']:
    print(f'{k}: {d.get(k)}')" 2>&1
echo '###REDFISH_CHASSIS_IDENTITY'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Chassis/System.Embedded.1 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for k in ['Manufacturer','Model','SerialNumber','PartNumber','SKU','ChassisType','AssetTag','Status','PowerState','Id']:
    print(f'{k}: {d.get(k)}')" 2>&1
echo '###REDFISH_MANAGER_IDENTITY'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Managers/iDRAC.Embedded.1 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for k in ['Manufacturer','Model','SerialNumber','UUID','FirmwareVersion','Status','Id','ManagerType']:
    print(f'{k}: {d.get(k)}')" 2>&1
echo '###REDFISH_MEMORY_SUMMARY'
curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems/System.Embedded.1/Memory 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
members=d.get('Members',[])
print(f'MemoryModules: {len(members)}')
for m in members:
    print(f'  {m[\"@odata.id\"]}')" 2>&1
echo '###REDFISH_MEMORY_DETAIL_ALL'
for url in $(curl -sk -u root:calvin https://10.254.174.17/redfish/v1/Systems/System.Embedded.1/Memory 2>/dev/null | python3 -c "import sys,json; [print(m['@odata.id']) for m in json.load(sys.stdin)['Members']]" 2>/dev/null); do
  curl -sk -u root:calvin "https://10.254.174.17${url}" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'DIMM: {d.get(\"DeviceLocator\")} Capacity={d.get(\"CapacityMiB\")}MiB Manufacturer={d.get(\"Manufacturer\")} Type={d.get(\"MemoryDeviceType\")} Speed={d.get(\"OperatingSpeedMhz\")} Status={d.get(\"Status\",{}).get(\"Health\")}')" 2>&1
done
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
