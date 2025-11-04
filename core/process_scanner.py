import psutil
from collections import defaultdict
import time
# class ProcessScanner:
class ProcessScanner:
    def __init__(self):
        # Warm-up CPU counters for all processes
        for p in psutil.process_iter():
            try:
                p.cpu_percent(None)
            except:
                pass
        # time.sleep(0.2)

    SYSTEM_PREFIX = [
        r"C:\Windows",
        r"C:\ProgramData\Microsoft",
        r"C:\Windows\System32",
        r"C:\Windows\SysWOW64"
    ]

    SYSTEM_NAMES = {
        "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe",
        "fontdrvhost.exe", "winlogon.exe", "svchost.exe", "memcompression", "system", "officeclicktorun.exe",
        "phoneexperiencehost.exe", "systemnotificationplugin.exe", "messagingplugin.exe", "amdrssrcext.exe", "radeonsoftware.exe",
        "warp-svc.exe", "widgets.exe", "widgetservice.exe", "amdrsserv.exe", "mcp-server.exe"
    }

    def is_system_process(self, proc):
        try:
            name = proc.info.get("name", "").lower()
            exe = (proc.info.get("exe") or "").lower()

            if name in self.SYSTEM_NAMES:
                return True
            if any(exe.startswith(p.lower()) for p in self.SYSTEM_PREFIX if exe):
                return True

        except Exception:
            return True

        return False

    def get_app_processes(self):
        """Return unique app processes with aggregated stats"""
        app_data = defaultdict(lambda: {"cpu": 0, "mem": 0, "disk": 0, "pids": []})

        for proc in psutil.process_iter(["pid","name","exe","cpu_percent","memory_info","io_counters"]):
            try:
                if self.is_system_process(proc):
                    continue

                name = proc.info.get("name") or "Unknown"
                # ✅ Ignore idle/system/unknown named processes
                if name.lower() in ["system idle process", "system", "idle", "unknown"]:
                    continue
                cpu = proc.info.get("cpu_percent", 0.0) or 0.0
                mem = proc.info.get("memory_info").rss / (1024 * 1024) if proc.info.get("memory_info") else 0

                io = proc.info.get("io_counters")
                disk = ((io.read_bytes + io.write_bytes) / (1024 * 1024)) if io else 0

                # aggregate by process name (sum)
                app_data[name]["cpu"] += cpu
                app_data[name]["mem"] += mem
                app_data[name]["disk"] += disk
                app_data[name]["pids"].append(proc.pid)

            except:
                continue

        return [
            {
                "name": name,
                "cpu": round(data["cpu"],2),
                "mem": round(data["mem"],2),
                "disk": round(data["disk"],2),
                "pids": data["pids"]
            }
            for name, data in app_data.items()
        ]
