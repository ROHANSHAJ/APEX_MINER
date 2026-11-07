"""
Miner Process Controller & Thermal Guardian
Manages Rigel (GPU) and XMRig (CPU) lifecycle, safety cooling, and real-time output parsing.
"""

import os
import re
import sys
import time
import signal
import subprocess
import threading
from presets import PRESETS

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

class MinerController:
    def __init__(self, bin_dir, log_callback=None, status_callback=None):
        self.bin_dir = bin_dir
        self.log_callback = log_callback
        self.status_callback = status_callback
        
        self.state = "STOPPED" # STOPPED, STARTING, RUNNING, PAUSED_OVERHEAT, ERROR
        self.active_engine = None
        self.process = None
        self.cpu_process = None
        self.read_thread = None
        self.uptime_thread = None
        
        self.start_time = None
        self.uptime_seconds = 0
        self.current_hashrate = "0.00 H/s"
        self.shares_accepted = 0
        self.shares_rejected = 0
        
        # Thermal guardian settings
        self.enable_temp_guard = True
        self.max_safe_temp = 74
        self.resume_temp = 63
        self.current_gpu_temp = 0
        self.last_config = None
        
        # Benchmark mode
        self.is_benchmark = False
        self.benchmark_duration = 30
        self.benchmark_thread = None

    def _strip_ansi(self, text):
        clean = ANSI_REGEX.sub('', text)
        return ''.join(c for c in clean if ord(c) <= 0xFFFF)

    def _notify_status(self):
        if self.status_callback:
            data = {
                "state": self.state,
                "engine": self.active_engine,
                "uptime": self.uptime_seconds,
                "hashrate": self.current_hashrate,
                "shares_accepted": self.shares_accepted,
                "shares_rejected": self.shares_rejected,
                "is_benchmark": self.is_benchmark
            }
            try:
                self.status_callback(data)
            except Exception as e:
                print(f"Status callback error: {e}")

    def _log(self, message):
        clean_msg = self._strip_ansi(message)
        if self.log_callback:
            try:
                self.log_callback(clean_msg)
            except Exception as e:
                print(f"Log callback error: {e}")
        else:
            print(clean_msg)

    def on_telemetry(self, stats):
        """Called every second by TelemetryMonitor"""
        gpu_temp = stats.get("gpu_temp", 0)
        self.current_gpu_temp = gpu_temp
        
        if not self.enable_temp_guard:
            return

        # Check for overheat while mining
        if self.state == "RUNNING" and gpu_temp >= self.max_safe_temp:
            self._log(f"\n[THERMAL GUARDIAN ALERT] GPU Temperature reached {gpu_temp}°C (Safe limit: {self.max_safe_temp}°C)!")
            self._log(f"[THERMAL GUARDIAN] Pausing miner to protect HP Victus 15 cooling. Will resume once cooled to {self.resume_temp}°C.\n")
            self.pause_due_to_heat()

        # Check for cool down while paused
        elif self.state == "PAUSED_OVERHEAT" and gpu_temp <= self.resume_temp:
            self._log(f"\n[THERMAL GUARDIAN] GPU cooled down to {gpu_temp}°C (Threshold: <= {self.resume_temp}°C).")
            self._log("[THERMAL GUARDIAN] Resuming mining now...\n")
            self.resume_after_heat()

    def build_command(self, config):
        preset_name = config.get("selected_preset", "Ergo (ERG) [Recommended]")
        preset = PRESETS.get(preset_name, PRESETS["Ergo (ERG) [Recommended]"])
        engine = preset.get("engine", "rigel")
        
        # Check custom pool
        if config.get("use_custom_pool", False) and config.get("custom_pool_url"):
            pool_url = config.get("custom_pool_url").strip()
        else:
            pool_url = config.get("pool_url", "").strip() or preset["pools"][0][1]
            
        wallet = config.get("wallet_address", "").strip() or preset["default_wallet"]
        worker = config.get("worker_name", "").strip() or "Victus-1650"
        
        if engine == "rigel":
            rigel_bin = os.path.join(self.bin_dir, "rigel")
            algo = preset["algo"]
            if algo == "custom":
                algo = config.get("custom_algo", "autolykos2").strip()
            
            # Format user string
            if preset.get("supports_unmineable", False):
                asset = config.get("payout_asset", "BTC").strip().upper()
                user_str = f"{asset}:{wallet}.{worker}"
            else:
                user_str = wallet
                
            cmd = [
                rigel_bin,
                "-a", algo,
                "-o", pool_url,
                "-u", user_str,
                "-w", worker,
                "--temp-limit", f"tc[{self.resume_temp}-{self.max_safe_temp}]",
                "--api-bind", "127.0.0.1:5000"
            ]
            
            if preset.get("coin_tag") and preset["coin_tag"] not in ["custom", "unmineable"]:
                cmd.extend(["--coin", preset["coin_tag"]])
                
            # Extra custom flags
            extra = config.get("custom_extra_flags", "").strip()
            if extra:
                cmd.extend(extra.split())
                
            return engine, cmd

        elif engine == "xmrig":
            xmrig_bin = os.path.join(self.bin_dir, "xmrig")
            threads = config.get("cpu_threads", 6)
            cmd = [
                xmrig_bin,
                "-o", pool_url.replace("stratum+tcp://", ""),
                "-u", wallet,
                "-p", worker,
                "-a", "rx/0",
                f"--threads={threads}",
                "--http-port=5001"
            ]
            return engine, cmd

        return None, []

    def start(self, config, is_benchmark=False):
        if self.state in ["RUNNING", "STARTING"]:
            return False, "Miner already running"

        self.last_config = config
        self.is_benchmark = is_benchmark
        self.enable_temp_guard = config.get("enable_temp_guard", True)
        self.max_safe_temp = config.get("max_safe_temp", 74)
        self.resume_temp = config.get("resume_temp", 63)
        
        engine, cmd = self.build_command(config)
        if not engine or not os.path.exists(cmd[0]):
            return False, f"Mining binary not found: {cmd[0] if cmd else 'unknown'}"

        self.active_engine = engine
        self.state = "STARTING"
        self.start_time = time.time()
        self.uptime_seconds = 0
        self.current_hashrate = "Initializing..."
        self.shares_accepted = 0
        self.shares_rejected = 0
        self._notify_status()

        self._log(f"============================================================")
        self._log(f" [START] Miner Engine: {engine.upper()}")
        self._log(f" [CONFIG] Command: {' '.join(cmd)}")
        self._log(f"️ [SAFETY] Laptop Thermal Limit: Auto-pause @ {self.max_safe_temp}°C | Resume @ {self.resume_temp}°C")
        if self.is_benchmark:
            self._log(f"⚡ [BENCHMARK] Running for Running for {self.benchmark_duration}s...")
        self._log(f"============================================================\n")

        try:
            # Set unbuffered stdout
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                preexec_fn=os.setsid
            )
            self.state = "RUNNING"
            self._notify_status()
            
            # Start output reading thread
            self.read_thread = threading.Thread(target=self._read_output_loop, daemon=True)
            self.read_thread.start()
            
            # Start uptime ticker
            self.uptime_thread = threading.Thread(target=self._uptime_loop, daemon=True)
            self.uptime_thread.start()

            # Benchmark timer if applicable
            if self.is_benchmark:
                self.benchmark_thread = threading.Thread(target=self._benchmark_timer, daemon=True)
                self.benchmark_thread.start()

            # Dual mining CPU engine launch if enabled
            if config.get("cpu_mining_enabled", False) and engine != "xmrig":
                threads = config.get("cpu_threads", 6)
                wallet = config.get("wallet_address", "").strip() or "16hEbjnQUr4KTk1mWdxktun12LbJ6942N7"
                cpu_bin = os.path.join(self.bin_dir, "xmrig")
                if os.path.exists(cpu_bin):
                    cpu_cmd = [
                        cpu_bin,
                        "-o", "209.38.61.60:3333",
                        "-u", f"BTC:{wallet}.Victus-CPU",
                        "-p", "x",
                        "-a", "rx/0",
                        f"--threads={threads}"
                    ]
                    self._log(f"[DUAL-MINING] Spawning AMD Ryzen 5 5600H CPU Miner ({threads} threads)...")
                    self.cpu_process = subprocess.Popen(
                        cpu_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid
                    )

            return True, "Miner started successfully"
        except Exception as e:
            self.state = "ERROR"
            self._notify_status()
            self._log(f"Failed to start miner: {e}")
            return False, str(e)

    def _read_output_loop(self):
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                line_str = line.strip()
                if line_str:
                    self._parse_metrics(line_str)
                    self._log(line_str)
            except Exception:
                break
                
        exit_code = self.process.poll() if self.process else None
        if self.state == "RUNNING":
            self.state = "STOPPED"
            self._log(f"\n[Miner process terminated with exit code {exit_code}]")
            self._notify_status()

    def _parse_metrics(self, line):
        """Extracts hashrates and share confirmations from miner log lines"""
        clean = self._strip_ansi(line)
        
        # Rigel hashrate pattern: e.g. "rigel: [autolykos2] 12.45 MH/s" or "32.10 MH/s"
        hr_match = re.search(r'([0-9]+\.[0-9]+\s+[kKMGT]?H/s)', clean)
        if hr_match:
            self.current_hashrate = hr_match.group(1)
            
        # Rigel shares: e.g. "shares: 5/5" or "accepted (5/5)"
        shares_match = re.search(r'shares:\s*([0-9]+)/([0-9]+)', clean, re.IGNORECASE)
        if shares_match:
            try:
                self.shares_accepted = int(shares_match.group(1))
            except ValueError:
                pass
                
        if "share accepted" in clean.lower() or "accepted share" in clean.lower():
            self.shares_accepted += 1
            
        if "share rejected" in clean.lower():
            self.shares_rejected += 1

    def _uptime_loop(self):
        while self.state in ["RUNNING", "PAUSED_OVERHEAT"]:
            if self.state == "RUNNING" and self.start_time:
                self.uptime_seconds = int(time.time() - self.start_time)
                self._notify_status()
            time.sleep(1.0)

    def _benchmark_timer(self):
        time.sleep(self.benchmark_duration)
        if self.state == "RUNNING" and self.is_benchmark:
            self._log(f"\n============================================================")
            self._log(f" Benchmark Complete (30 seconds)!")
            self._log(f" Final Hashrate: {self.current_hashrate}")
            self._log(f"️ Ending GPU Temp: {self.current_gpu_temp}°C")
            self._log(f"✅ Shares Accepted: {self.shares_accepted}")
            self._log(f"============================================================\n")
            self.stop()

    def pause_due_to_heat(self):
        if self.state == "RUNNING":
            self.state = "PAUSED_OVERHEAT"
            self._notify_status()
            self._kill_process()

    def resume_after_heat(self):
        if self.state == "PAUSED_OVERHEAT" and self.last_config:
            self.start(self.last_config, is_benchmark=False)

    def _kill_process(self):
        if self.process:
            try:
                # Terminate entire process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                try:
                    self.process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except Exception:
                pass
            self.process = None

        if self.cpu_process:
            try:
                os.killpg(os.getpgid(self.cpu_process.pid), signal.SIGTERM)
                try:
                    self.cpu_process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.cpu_process.pid), signal.SIGKILL)
            except Exception:
                pass
            self.cpu_process = None

    def stop(self):
        if self.state in ["STOPPED", "ERROR"]:
            return True, "Already stopped"
            
        self._log("\nStopping miner process...")
        self.state = "STOPPED"
        self._notify_status()
        self._kill_process()
        self.current_hashrate = "0.00 H/s"
        self._log("Miner stopped cleanly.\n")
        self._notify_status()
        return True, "Stopped"
