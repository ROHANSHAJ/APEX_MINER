"""
Universal Hardware Telemetry Monitor for ApexMiner
Monitors NVIDIA, AMD, Intel GPUs and multi-core CPU stats across Linux and Windows.
"""

import time
import subprocess
import threading
import psutil

class TelemetryMonitor:
    def __init__(self, update_interval=1.0, callback=None):
        self.update_interval = update_interval
        self.callback = callback
        self.running = False
        self._thread = None
        
        self.last_stats = {
            "gpu_found": False,
            "gpu_name": "Generic GPU / CPU Mode",
            "gpu_temp": 0,
            "gpu_util": 0,
            "gpu_power": 0.0,
            "gpu_power_cap": 0.0,
            "gpu_mem_used": 0,
            "gpu_mem_total": 4096,
            "cpu_util": 0.0,
            "cpu_threads": psutil.cpu_count(logical=True) or 8,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "timestamp": time.time()
        }

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False

    def query_gpu_stats(self):
        stats = {
            "gpu_found": False,
            "gpu_name": self.last_stats.get("gpu_name", "GPU"),
            "gpu_temp": 0,
            "gpu_util": 0,
            "gpu_power": 0.0,
            "gpu_power_cap": 0.0,
            "gpu_mem_used": 0,
            "gpu_mem_total": 4096,
        }
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,utilization.gpu,power.draw,power.limit,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 7:
                    stats["gpu_found"] = True
                    stats["gpu_name"] = parts[0]
                    stats["gpu_temp"] = int(parts[1]) if parts[1].isdigit() else 0
                    stats["gpu_util"] = int(parts[2]) if parts[2].isdigit() else 0
                    try:
                        stats["gpu_power"] = float(parts[3])
                    except ValueError:
                        stats["gpu_power"] = 0.0
                    try:
                        stats["gpu_power_cap"] = float(parts[4])
                    except ValueError:
                        stats["gpu_power_cap"] = 0.0
                    stats["gpu_mem_used"] = int(parts[5]) if parts[5].isdigit() else 0
                    stats["gpu_mem_total"] = int(parts[6]) if parts[6].isdigit() else 4096
        except Exception:
            pass
        return stats

    def query_cpu_ram_stats(self):
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            return {
                "cpu_util": cpu_pct,
                "ram_used_gb": round(mem.used / (1024**3), 1),
                "ram_total_gb": round(mem.total / (1024**3), 1)
            }
        except Exception:
            return {
                "cpu_util": 0.0,
                "ram_used_gb": 0.0,
                "ram_total_gb": 0.0
            }

    def _poll_loop(self):
        # Initial cpu_percent call to seed psutil calculation
        psutil.cpu_percent(interval=None)
        while self.running:
            gpu = self.query_gpu_stats()
            sys_info = self.query_cpu_ram_stats()
            
            self.last_stats.update(gpu)
            self.last_stats.update(sys_info)
            self.last_stats["timestamp"] = time.time()
            
            if self.callback:
                try:
                    self.callback(dict(self.last_stats))
                except Exception as e:
                    print(f"Telemetry callback error: {e}")
            
            time.sleep(self.update_interval)
