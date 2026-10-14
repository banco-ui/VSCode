import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###SSH_FREE_H'
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
echo '###SSH_DMESG_MEM'
dmesg 2>/dev/null | grep -i "memory\|threshold\|platform.*mem" | tail -20
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=25)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
