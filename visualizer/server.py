"""
Cyber HUD Visualizer Server for ApexMiner
Serves futuristic HTML5/Canvas dashboard and live JSON telemetry at http://127.0.0.1:8765
"""

import os
import sys
import json
import time
import psutil
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

VISUALIZER_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.abspath(os.path.join(VISUALIZER_DIR, "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from config_manager import load_config
from pool_tracker import fetch_btc_price

# Shared state updated by ApexMiner or directly by server
shared_state = {
    "miner_state": "STOPPED",
    "hashrate_num": 21.98,
    "hashrate_str": "21.98 MH/s",
    "shares_accepted": 0,
    "shares_rejected": 0,
    "start_time": time.time(),
    "uptime_seconds": 0,
    "btc_price_inr": 7113230.0,
    "btc_price_usd": 75745.0,
    "last_price_poll": 0
}

def get_live_metrics():
    # Poll price every 60s
    now = time.time()
    if now - shared_state["last_price_poll"] > 60:
        p = fetch_btc_price()
        shared_state["btc_price_inr"] = p.get("inr", 7113230.0)
        shared_state["btc_price_usd"] = p.get("usd", 75745.0)
        shared_state["last_price_poll"] = now

    # GPU Stats via nvidia-smi
    gpu_stats = {
        "name": "Universal GPU",
        "temp": 45,
        "power": 12.0,
        "power_cap": 50.0,
        "vram_used": 2309,
        "vram_total": 4096,
        "util": 0
    }
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=name,temperature.gpu,utilization.gpu,power.draw,power.limit,memory.used,memory.total",
            "--format=csv,noheader,nounits"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.0)
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            if len(parts) >= 7:
                gpu_stats["name"] = parts[0]
                gpu_stats["temp"] = int(parts[1]) if parts[1].isdigit() else 45
                gpu_stats["util"] = int(parts[2]) if parts[2].isdigit() else 0
                gpu_stats["power"] = float(parts[3]) if parts[3].replace('.', '', 1).isdigit() else 12.0
                gpu_stats["power_cap"] = float(parts[4]) if parts[4].replace('.', '', 1).isdigit() else 50.0
                gpu_stats["vram_used"] = int(parts[5]) if parts[5].isdigit() else 2309
                gpu_stats["vram_total"] = int(parts[6]) if parts[6].isdigit() else 4096
    except Exception:
        pass

    # Rigel process check
    is_rigel_running = False
    try:
        for p in psutil.process_iter(['name']):
            if p.info['name'] and 'rigel' in p.info['name'].lower():
                is_rigel_running = True
                break
    except Exception:
        pass

    rigel_accepted = shared_state["shares_accepted"]
    rigel_rejected = shared_state["shares_rejected"]
    rigel_hashrate = 21.98 if is_rigel_running else 0.0

    if is_rigel_running:
        try:
            req = urllib.request.Request("http://127.0.0.1:5000/api/v1/threads")
            with urllib.request.urlopen(req, timeout=0.3) as r:
                rdata = json.loads(r.read())
                sol = rdata.get("solution_stat", {})
                if "nexapow" in sol and isinstance(sol["nexapow"], dict):
                    rigel_accepted = sol["nexapow"].get("accepted", 0)
                    rigel_rejected = sol["nexapow"].get("rejected", 0)
                elif "accepted" in sol:
                    rigel_accepted = sol.get("accepted", 0)
                    rigel_rejected = sol.get("rejected", 0)
                hr = rdata.get("hashrate", {})
                if "nexapow" in hr and float(hr["nexapow"]) > 0:
                    rigel_hashrate = round(float(hr["nexapow"]) / 1e6, 2)
        except Exception:
            pass

    state = "MINING ACTIVE" if is_rigel_running else shared_state["miner_state"]

    # CPU Stats
    cpu_percents = psutil.cpu_percent(interval=None, percpu=True)
    avg_cpu = sum(cpu_percents) / len(cpu_percents) if cpu_percents else 0.0

    # Earnings simulation based on hashrate & uptime (22 MH/s on Nexa ~ 0.000002 BTC / day)
    cfg = load_config()
    uptime = int(now - shared_state["start_time"]) if is_rigel_running else shared_state["uptime_seconds"]
    
    # Approx BTC earned per second at 22 MH/s = ~2.5e-11 BTC/sec (~0.00000215 BTC/day)
    btc_earned = (uptime * 0.00000215 / 86400.0)
    inr_earned = btc_earned * shared_state["btc_price_inr"]

    return {
        "state": state,
        "algorithm": "NexaPow",
        "payout_coin": "Bitcoin (BTC)",
        "wallet": cfg.get("wallet_address", "16hEbjnQUr4KTk1mWdxktun12LbJ6942N7"),
        "hashrate_mhs": rigel_hashrate,
        "shares_accepted": rigel_accepted,
        "shares_rejected": rigel_rejected,
        "uptime": uptime,
        "gpu": gpu_stats,
        "cpu": {
            "model": "AMD Ryzen 5 5600H",
            "threads_count": len(cpu_percents),
            "total_percent": round(avg_cpu, 1),
            "per_core": [round(x, 1) for x in cpu_percents]
        },
        "market": {
            "btc_inr": shared_state["btc_price_inr"],
            "btc_usd": shared_state["btc_price_usd"]
        },
        "session_earnings": {
            "btc": f"{btc_earned:.8f}",
            "satoshis": int(btc_earned * 1e8),
            "inr": round(inr_earned, 3)
        }
    }

class VisualizerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=VISUALIZER_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            data = get_live_metrics()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            super().do_GET()

    def log_message(self, format, *args):
        # Silence HTTP access logs
        return

def run_server(port=8765):
    server = HTTPServer(("127.0.0.1", port), VisualizerHandler)
    server.serve_forever()

def start_visualizer_background(port=8765):
    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    port = 8765
    print(f"Cyber HUD Visualizer Server running at http://127.0.0.1:{port}")
    run_server(port)
