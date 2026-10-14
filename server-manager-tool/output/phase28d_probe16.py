import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.254.174.70", username="sysadmin", password="W!ndR00tUser", timeout=15)

cmds = r"""echo '###CGROUP_MOUNTS'
mount | grep cgroup 2>&1
echo '###CGROUP_MEMORY_TREE'
ls /sys/fs/cgroup/memory/ 2>/dev/null | head -20
echo '###CGROUP_K8S_INFRA'
ls /sys/fs/cgroup/memory/k8s-infra/ 2>/dev/null | head -10
echo '###CGROUP_K8S_INFRA_MEM'
cat /sys/fs/cgroup/memory/k8s-infra/memory.usage_in_bytes 2>/dev/null
cat /sys/fs/cgroup/memory/k8s-infra/memory.limit_in_bytes 2>/dev/null
echo '###CGROUP_K8S_PODS'
cat /sys/fs/cgroup/memory/k8s-infra/kubepods/memory.usage_in_bytes 2>/dev/null
cat /sys/fs/cgroup/memory/k8s-infra/kubepods/memory.limit_in_bytes 2>/dev/null
echo '###HEALTH_QUERY'
source /etc/platform/openrc 2>/dev/null
system health-query 2>&1 | head -30
echo '###HOST_MEM_SHOW_PROC0'
system host-memory-show controller-0 0 2>&1
echo '###END'
"""
_, stdout, stderr = c.exec_command(cmds, timeout=20)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("STDERR:", err[:500])
c.close()
