import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###CGROUP_PLATFORM_MEM'
for cg in /sys/fs/cgroup/memory/k8s-infra /sys/fs/cgroup/memory/platform /sys/fs/cgroup/memory.system.slice; do
  if [ -d "$cg" ]; then
    echo "CG=$cg"
    cat "$cg/memory.usage_in_bytes" 2>/dev/null
    cat "$cg/memory.limit_in_bytes" 2>/dev/null
  fi
done
echo '###CGROUP_V2_PLATFORM'
if [ -f /sys/fs/cgroup/system.slice/memory.current ]; then
  echo "V2 system.slice:"
  cat /sys/fs/cgroup/system.slice/memory.current
  cat /sys/fs/cgroup/system.slice/memory.max
fi
echo '###CGROUP_KUBEPODS'
ls /sys/fs/cgroup/memory/k8s-infra/kubepods/ 2>/dev/null | head -5
for cg in /sys/fs/cgroup/memory/k8s-infra/kubepods/burstable /sys/fs/cgroup/memory/k8s-infra/kubepods/besteffort /sys/fs/cgroup/memory/k8s-infra/kubepods; do
  if [ -f "$cg/memory.usage_in_bytes" ]; then
    echo "CG=$cg usage=$(cat $cg/memory.usage_in_bytes) limit=$(cat $cg/memory.limit_in_bytes)"
  fi
done
echo '###PLATFORM_MEM_CGROUP'
cat /sys/fs/cgroup/memory/k8s-infra/memory.usage_in_bytes 2>/dev/null
cat /sys/fs/cgroup/memory/k8s-infra/memory.limit_in_bytes 2>/dev/null
echo '###USM_API_ROOT'
curl -sk http://192.168.204.1:5492/ 2>&1 | head -10
echo '###USM_V1_ROOT'
curl -sk http://192.168.204.1:5492/v1/ 2>&1 | head -10
echo '###USM_DEPLOY_SHOW_CLI'
system deploy-show 2>&1 | head -20
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=20)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
