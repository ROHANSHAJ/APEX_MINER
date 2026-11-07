"""
Universal Hardware Detection & Auto-Tuning Engine
Detects NVIDIA, AMD, Intel GPUs and multi-core CPUs across Linux & Windows.
"""

import os
import sys
import platform
import subprocess
import psutil

class HardwareDetector:
    def __init__(self):
        self.os_type = platform.system() # 'Linux', 'Windows', 'Darwin'
        self.gpus = []
        self.cpu = self._detect_cpu()
        self._detect_gpus()

    def _detect_cpu(self):
        model = "Universal Multi-Core Processor"
        try:
            if self.os_type == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            model = line.split(":", 1)[1].strip()
                            break
            elif self.os_type == "Windows":
                cmd = ["wmic", "cpu", "get", "name"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip() and "Name" not in l]
                    if lines:
                        model = lines[0]
        except Exception:
            pass

        return {
            "model": model,
            "logical_threads": psutil.cpu_count(logical=True) or 8,
            "physical_cores": psutil.cpu_count(logical=False) or 4
        }

    def _detect_gpus(self):
        # 1. NVIDIA Detection via nvidia-smi
        try:
            cmd = ["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version", "--format=csv,noheader,nounits"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        idx = int(parts[0])
                        name = parts[1]
                        vram_mb = int(parts[2])
                        self.gpus.append({
                            "index": idx,
                            "name": name,
                            "vendor": "NVIDIA",
                            "vram_mb": vram_mb,
                            "vram_gb": round(vram_mb / 1024, 1),
                            "driver": parts[3] if len(parts) > 3 else "Unknown"
                        })
        except Exception:
            pass

        # 2. AMD / Intel Detection (if no NVIDIA found or hybrid)
        if not self.gpus:
            try:
                if self.os_type == "Linux":
                    cmd = ["lspci"]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if res.returncode == 0:
                        for line in res.stdout.splitlines():
                            if "VGA" in line or "3D" in line:
                                vendor = "AMD" if "AMD" in line or "Radeon" in line else ("Intel" if "Intel" in line else "Generic")
                                self.gpus.append({
                                    "index": len(self.gpus),
                                    "name": line.split(":", 2)[-1].strip(),
                                    "vendor": vendor,
                                    "vram_mb": 4096,
                                    "vram_gb": 4.0,
                                    "driver": "Kernel/DRM"
                                })
            except Exception:
                pass

    @property
    def has_gpu(self):
        return len(self.gpus) > 0

    @property
    def primary_gpu(self):
        return self.gpus[0] if self.gpus else None

    @property
    def primary_vram_gb(self):
        return self.gpus[0]["vram_gb"] if self.gpus else 0.0

    def get_tier(self):
        """Calculates VRAM tier to recommend optimal algorithms"""
        if not self.has_gpu:
            return 0 # CPU Only
        vram = self.primary_vram_gb
        if vram < 4.0:
            return 1 # Ultra-low memory (< 4GB)
        elif vram < 6.0:
            return 2 # Mid memory (4GB - 5GB, e.g. GTX 1650, RX 570 4GB)
        elif vram < 10.0:
            return 3 # Standard gaming (6GB - 8GB, e.g. RTX 2060, 3060 8GB, 4060)
        else:
            return 4 # High VRAM (10GB - 24GB, e.g. RTX 3080/3090, 4080/4090)

    def is_algo_compatible(self, algo_key, req_vram_gb):
        """Checks if selected algorithm fits in primary GPU VRAM"""
        if req_vram_gb == 0:
            return True, "Compatible (CPU or zero VRAM required)"
        if not self.has_gpu:
            return False, "No dedicated GPU detected (Switch to CPU mining)"
        if self.primary_vram_gb >= req_vram_gb:
            return True, f"Compatible ({self.primary_vram_gb} GB VRAM available)"
        return False, f"Requires {req_vram_gb} GB VRAM, but GPU has {self.primary_vram_gb} GB"
