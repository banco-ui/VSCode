import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###DMI_UUID'
cat /sys/class/dmi/id/product_uuid 2>&1
echo '###DMI_SERIAL'
cat /sys/class/dmi/id/product_serial 2>&1
echo '###DMI_BOARD_SERIAL'
cat /sys/class/dmi/id/board_serial 2>&1
echo '###DMI_BOARD_VENDOR'
cat /sys/class/dmi/id/board_vendor 2>&1
echo '###DMI_BOARD_NAME'
cat /sys/class/dmi/id/board_name 2>&1
echo '###DMI_BIOS_VENDOR'
cat /sys/class/dmi/id/bios_vendor 2>&1
echo '###DMI_BIOS_VERSION'
cat /sys/class/dmi/id/bios_version 2>&1
echo '###DMI_SYS_VENDOR'
cat /sys/class/dmi/id/sys_vendor 2>&1
echo '###DMI_SKU'
cat /sys/class/dmi/id/product_sku 2>&1
echo '###DMI_FAMILY'
cat /sys/class/dmi/id/product_family 2>&1
echo '###REDFISH_NO_AUTH'
curl -sk https://10.254.174.17/redfish/v1/ 2>&1 | python3 -m json.tool 2>/dev/null | head -30
echo '###IPMI_LAN'
which ipmitool 2>/dev/null && ipmitool lan print 2>&1 | head -20
echo '###IPMI_MC_INFO'
which ipmitool 2>/dev/null && ipmitool mc info 2>&1 | head -15
echo '###DMIDECODE_NO_SUDO'
dmidecode -t 1 2>&1 | head -5
echo '###LSCPU'
lscpu 2>&1 | head -20
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=20)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
