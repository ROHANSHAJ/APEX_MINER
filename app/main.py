#!/usr/bin/env python3
"""
ApexMiner Studio - Universal Multi-GPU & CPU Mining Suite
Modern GUI for NVIDIA, AMD, Intel GPUs & Multi-Core CPUs on Linux & Windows
Includes Bitcoin Account Setup Wizard, Live Pool Balance Tracker & UPI Cashout Integration.
"""

import os
import sys
import time
import webbrowser
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Add script directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from presets import PRESETS
from config_manager import load_config, save_config
from telemetry import TelemetryMonitor
from miner_controller import MinerController
from pool_tracker import validate_btc_address, AsyncTracker
from hardware_detector import HardwareDetector

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ApexMinerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Hardware Detection
        self.hw = HardwareDetector()
        gpu_name = self.hw.primary_gpu["name"] if self.hw.has_gpu else "Universal CPU Mode"
        self.title(f"ApexMiner Studio - Universal Edition [{gpu_name}]")
        self.geometry("1100x780")
        self.minsize(1000, 700)

        # Base paths
        self.base_dir = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
        self.bin_dir = os.path.join(self.base_dir, "bin")

        # Config
        self.config = load_config()

        # Telemetry & Controller
        self.telemetry = TelemetryMonitor(update_interval=1.0, callback=self.on_telemetry_update)
        self.miner = MinerController(
            bin_dir=self.bin_dir,
            log_callback=self.on_miner_log,
            status_callback=self.on_miner_status
        )

        # Pool Tracker
        self.tracker = AsyncTracker(callback=self.on_tracker_update)

        # UI Build
        self._build_header_telemetry()
        self._build_tabs()
        
        # Initialize form state from config
        self._load_config_to_ui()

        # Start telemetry monitor
        self.telemetry.start()

        # Start Cyber HUD background server
        try:
            from visualizer.server import start_visualizer_background
            start_visualizer_background(port=8765)
        except Exception:
            pass

        # Auto-query pool tracker if wallet exists
        if self.config.get("wallet_address"):
            self.query_tracker_stats()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_header_telemetry(self):
        """Top hardware dashboard cards"""
        self.header_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#181a20")
        self.header_frame.pack(fill="x", padx=16, pady=(14, 8))

        # Title & Device Badge
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            title_box,
            text="ApexMiner Studio",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w")

        if self.hw.has_gpu:
            gpu = self.hw.primary_gpu
            device_desc = f"GPU: {gpu['name']} ({gpu['vram_gb']}GB VRAM) | CPU: {self.hw.cpu['model']}"
        else:
            device_desc = f"CPU Mode: {self.hw.cpu['model']} ({self.hw.cpu['logical_threads']} Threads)"

        self.lbl_device = ctk.CTkLabel(
            title_box,
            text=device_desc,
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        self.lbl_device.pack(anchor="w")

        # Telemetry Cards on the right
        telemetry_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        telemetry_box.pack(side="right", padx=16, pady=8)

        # Card: GPU Temp
        self.card_temp = ctk.CTkFrame(telemetry_box, corner_radius=8, fg_color="#24283b", width=125, height=58)
        self.card_temp.pack(side="left", padx=6)
        self.card_temp.pack_propagate(False)
        ctk.CTkLabel(self.card_temp, text="GPU TEMP", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8").pack(pady=(4, 0))
        self.lbl_temp = ctk.CTkLabel(self.card_temp, text="-- °C", font=ctk.CTkFont(size=17, weight="bold"), text_color="#10b981")
        self.lbl_temp.pack()

        # Card: GPU Power
        self.card_power = ctk.CTkFrame(telemetry_box, corner_radius=8, fg_color="#24283b", width=125, height=58)
        self.card_power.pack(side="left", padx=6)
        self.card_power.pack_propagate(False)
        ctk.CTkLabel(self.card_power, text="POWER DRAW", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8").pack(pady=(4, 0))
        self.lbl_power = ctk.CTkLabel(self.card_power, text="-- W", font=ctk.CTkFont(size=15, weight="bold"), text_color="#38bdf8")
        self.lbl_power.pack()

        # Card: VRAM Usage
        self.card_vram = ctk.CTkFrame(telemetry_box, corner_radius=8, fg_color="#24283b", width=135, height=58)
        self.card_vram.pack(side="left", padx=6)
        self.card_vram.pack_propagate(False)
        ctk.CTkLabel(self.card_vram, text="VRAM USAGE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8").pack(pady=(4, 0))
        total_vram_str = f"{int(self.hw.primary_gpu['vram_mb'])} MB" if self.hw.has_gpu else "N/A"
        self.lbl_vram = ctk.CTkLabel(self.card_vram, text=f"-- / {total_vram_str}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#c084fc")
        self.lbl_vram.pack()

        # Card: Status / Hashrate
        self.card_status = ctk.CTkFrame(telemetry_box, corner_radius=8, fg_color="#24283b", width=150, height=58)
        self.card_status.pack(side="left", padx=6)
        self.card_status.pack_propagate(False)
        self.lbl_status_title = ctk.CTkLabel(self.card_status, text="STOPPED", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b")
        self.lbl_status_title.pack(pady=(4, 0))
        self.lbl_hashrate_hud = ctk.CTkLabel(self.card_status, text="0.00 H/s", font=ctk.CTkFont(size=16, weight="bold"), text_color="#e2e8f0")
        self.lbl_hashrate_hud.pack()

    def _build_tabs(self):
        """Construct Tab View with clean titles"""
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.tab_miner = self.tabview.add("Mining Suite")
        self.tab_tracker = self.tabview.add("Account & Tracker")
        self.tab_safety = self.tabview.add("Safety & Tuning")
        self.tab_console = self.tabview.add("Live Console")
        self.tab_guide = self.tabview.add("Universal Guide")

        self._build_tab_miner()
        self._build_tab_tracker()
        self._build_tab_safety()
        self._build_tab_console()
        self._build_tab_guide()

    # ---------------- TAB 1: MINING SUITE ----------------
    def _build_tab_miner(self):
        self.tab_miner.grid_columnconfigure(0, weight=6)
        self.tab_miner.grid_columnconfigure(1, weight=4)
        self.tab_miner.grid_rowconfigure(0, weight=1)

        # Left Column: Configuration Form
        form_frame = ctk.CTkScrollableFrame(self.tab_miner, fg_color="transparent")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        # Preset Selector
        ctk.CTkLabel(form_frame, text="1. Select Coin & Algorithm Preset", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(4, 4))
        self.preset_var = ctk.StringVar(value=self.config.get("selected_preset", "Unmineable [Mine & Payout in BTC/USDT/DOGE]"))
        self.preset_menu = ctk.CTkOptionMenu(
            form_frame,
            values=list(PRESETS.keys()),
            variable=self.preset_var,
            command=self.on_preset_changed,
            height=34
        )
        self.preset_menu.pack(fill="x", pady=(0, 6))

        # Preset Description Box
        self.lbl_preset_desc = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#38bdf8",
            wraplength=520,
            justify="left"
        )
        self.lbl_preset_desc.pack(anchor="w", pady=(0, 10))

        # Pool Selector
        ctk.CTkLabel(form_frame, text="2. Mining Pool (Stratum)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(4, 4))
        self.pool_var = ctk.StringVar()
        self.pool_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["Select a preset first"],
            variable=self.pool_var,
            height=34
        )
        self.pool_menu.pack(fill="x", pady=(0, 6))

        # Custom Pool Toggle
        self.use_custom_pool_var = ctk.BooleanVar(value=self.config.get("use_custom_pool", False))
        self.chk_custom_pool = ctk.CTkCheckBox(
            form_frame,
            text="Use Custom Pool Address",
            variable=self.use_custom_pool_var,
            command=self.toggle_custom_pool
        )
        self.chk_custom_pool.pack(anchor="w", pady=(0, 6))

        self.entry_custom_pool = ctk.CTkEntry(
            form_frame,
            placeholder_text="stratum+tcp://pool_host:port",
            height=32
        )
        self.entry_custom_pool.pack(fill="x", pady=(0, 12))

        # Wallet Address
        ctk.CTkLabel(form_frame, text="3. Payout Wallet Address (Bitcoin BTC / Coin)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(4, 4))
        
        wallet_entry_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        wallet_entry_row.pack(fill="x", pady=(0, 12))
        wallet_entry_row.grid_columnconfigure(0, weight=1)

        self.entry_wallet = ctk.CTkEntry(
            wallet_entry_row,
            placeholder_text="Enter your Bitcoin (BTC) address here",
            height=34
        )
        self.entry_wallet.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry_wallet.bind("<KeyRelease>", self._on_wallet_key_release)

        btn_setup_wiz = ctk.CTkButton(
            wallet_entry_row,
            text="Account Wizard",
            width=120,
            height=34,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=lambda: self.tabview.set("Account & Tracker")
        )
        btn_setup_wiz.grid(row=0, column=1)

        # Worker Name & Payout Asset (in a row)
        row_worker_asset = ctk.CTkFrame(form_frame, fg_color="transparent")
        row_worker_asset.pack(fill="x", pady=(0, 12))
        row_worker_asset.grid_columnconfigure((0, 1), weight=1)

        # Worker name
        worker_box = ctk.CTkFrame(row_worker_asset, fg_color="transparent")
        worker_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(worker_box, text="Worker Name", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.entry_worker = ctk.CTkEntry(worker_box, placeholder_text="Victus-1650", height=34)
        self.entry_worker.pack(fill="x")

        # Payout Asset (Unmineable)
        self.asset_box = ctk.CTkFrame(row_worker_asset, fg_color="transparent")
        self.asset_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.lbl_asset = ctk.CTkLabel(self.asset_box, text="Payout Coin (Unmineable)", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_asset.pack(anchor="w", pady=(0, 4))
        self.asset_var = ctk.StringVar(value=self.config.get("payout_asset", "BTC"))
        self.asset_menu = ctk.CTkOptionMenu(
            self.asset_box,
            values=["BTC", "USDT", "DOGE", "SOL", "ETH", "LTC", "MATIC", "ADA", "XRP"],
            variable=self.asset_var,
            command=self._on_asset_changed,
            height=34
        )
        self.asset_menu.pack(fill="x")

        # Right Column: Big Action Center & KPIs
        action_frame = ctk.CTkFrame(self.tab_miner, corner_radius=12, fg_color="#181a20")
        action_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        action_frame.pack_propagate(False)

        ctk.CTkLabel(action_frame, text="Control Center", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(16, 10))

        # Start / Stop Button
        self.btn_toggle_mine = ctk.CTkButton(
            action_frame,
            text="START MINING",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=50,
            corner_radius=10,
            command=self.toggle_mining
        )
        self.btn_toggle_mine.pack(fill="x", padx=20, pady=(4, 10))

        # Benchmark Button
        self.btn_benchmark = ctk.CTkButton(
            action_frame,
            text="Run 30s Benchmark",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=38,
            corner_radius=8,
            command=self.run_benchmark
        )
        self.btn_benchmark.pack(fill="x", padx=20, pady=(0, 10))

        # Launch Cyber HUD Visualizer Button
        self.btn_hud = ctk.CTkButton(
            action_frame,
            text="Launch Cyber HUD Visualizer",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            height=38,
            corner_radius=8,
            command=self.open_cyber_hud
        )
        self.btn_hud.pack(fill="x", padx=20, pady=(0, 10))

        # Save Settings Button
        self.btn_save = ctk.CTkButton(
            action_frame,
            text="Save Configuration",
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            height=32,
            corner_radius=8,
            command=self.save_ui_to_config
        )
        self.btn_save.pack(fill="x", padx=20, pady=(0, 14))

        # KPI Stats Card
        kpi_card = ctk.CTkFrame(action_frame, corner_radius=10, fg_color="#24283b")
        kpi_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        ctk.CTkLabel(kpi_card, text="CURRENT SESSION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(pady=(10, 4))

        self.lbl_kpi_hashrate = ctk.CTkLabel(
            kpi_card,
            text="0.00 H/s",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_kpi_hashrate.pack(pady=(0, 2))

        self.lbl_kpi_algo = ctk.CTkLabel(
            kpi_card,
            text="Payout: Bitcoin (BTC)",
            font=ctk.CTkFont(size=12),
            text_color="#f59e0b"
        )
        self.lbl_kpi_algo.pack(pady=(0, 6))

        # Share counts
        stats_sub = ctk.CTkFrame(kpi_card, fg_color="transparent")
        stats_sub.pack(fill="x", padx=16, pady=(2, 6))
        stats_sub.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(stats_sub, text="Accepted Shares:", font=ctk.CTkFont(size=12), text_color="#94a3b8").grid(row=0, column=0, sticky="w")
        self.lbl_kpi_shares = ctk.CTkLabel(stats_sub, text="0", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981")
        self.lbl_kpi_shares.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(stats_sub, text="Rejected Shares:", font=ctk.CTkFont(size=12), text_color="#94a3b8").grid(row=1, column=0, sticky="w")
        self.lbl_kpi_rejected = ctk.CTkLabel(stats_sub, text="0", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ef4444")
        self.lbl_kpi_rejected.grid(row=1, column=1, sticky="e")

        ctk.CTkLabel(stats_sub, text="Session Uptime:", font=ctk.CTkFont(size=12), text_color="#94a3b8").grid(row=2, column=0, sticky="w")
        self.lbl_kpi_uptime = ctk.CTkLabel(stats_sub, text="00:00:00", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        self.lbl_kpi_uptime.grid(row=2, column=1, sticky="e")

        # Mini Pool Tracker in KPI
        mini_track_box = ctk.CTkFrame(kpi_card, fg_color="#181a20", corner_radius=8)
        mini_track_box.pack(fill="x", padx=14, pady=(6, 10))
        ctk.CTkLabel(mini_track_box, text="UNPAID BTC BALANCE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8").pack(pady=(4, 0))
        self.lbl_mini_balance = ctk.CTkLabel(mini_track_box, text="-- BTC", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f59e0b")
        self.lbl_mini_balance.pack()
        self.lbl_mini_inr = ctk.CTkLabel(mini_track_box, text="-- INR", font=ctk.CTkFont(size=11), text_color="#10b981")
        self.lbl_mini_inr.pack(pady=(0, 4))

    # ---------------- TAB 2: ACCOUNT & TRACKER ----------------
    def _build_tab_tracker(self):
        scroll_tracker = ctk.CTkScrollableFrame(self.tab_tracker, fg_color="transparent")
        scroll_tracker.pack(fill="both", expand=True, padx=20, pady=10)

        # Top Live Market Price Banner
        price_banner = ctk.CTkFrame(scroll_tracker, corner_radius=10, fg_color="#1e293b")
        price_banner.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            price_banner,
            text="LIVE BITCOIN (BTC) MARKET PRICE:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8"
        ).pack(side="left", padx=16, pady=10)

        self.lbl_market_price = ctk.CTkLabel(
            price_banner,
            text="1 BTC ≈ ₹7,113,230 INR ($75,745 USD)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_market_price.pack(side="left", padx=4, pady=10)

        btn_refresh_price = ctk.CTkButton(
            price_banner,
            text="Refresh Stats",
            width=110,
            height=28,
            fg_color="#0284c7",
            command=self.query_tracker_stats
        )
        btn_refresh_price.pack(side="right", padx=14, pady=8)

        # Section 1: Live Unmineable Balance & Payout Progress Card
        tracker_card = ctk.CTkFrame(scroll_tracker, corner_radius=12, fg_color="#181a20")
        tracker_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            tracker_card,
            text="Live Pool Balance & Payout Tracker",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f59e0b"
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            tracker_card,
            text="Directly tracks your unpaid Bitcoin balance and threshold progress from Unmineable pool API.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Balance Display Grid
        bal_grid = ctk.CTkFrame(tracker_card, fg_color="transparent")
        bal_grid.pack(fill="x", padx=16, pady=(0, 10))
        bal_grid.grid_columnconfigure((0, 1), weight=1)

        # Left: Unpaid BTC Balance
        b_left = ctk.CTkFrame(bal_grid, corner_radius=8, fg_color="#24283b")
        b_left.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(b_left, text="CURRENT UNPAID BALANCE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(pady=(8, 2))
        self.lbl_track_btc = ctk.CTkLabel(b_left, text="0.00000000 BTC", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f59e0b")
        self.lbl_track_btc.pack(pady=(0, 2))
        self.lbl_track_inr = ctk.CTkLabel(b_left, text="≈ ₹0.00 INR", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10b981")
        self.lbl_track_inr.pack(pady=(0, 8))

        # Right: Threshold
        b_right = ctk.CTkFrame(bal_grid, corner_radius=8, fg_color="#24283b")
        b_right.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(b_right, text="PAYOUT THRESHOLD & NETWORK", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(pady=(8, 2))
        self.lbl_track_thresh = ctk.CTkLabel(b_right, text="0.00075000 BTC", font=ctk.CTkFont(size=20, weight="bold"), text_color="#38bdf8")
        self.lbl_track_thresh.pack(pady=(0, 2))
        self.lbl_track_net = ctk.CTkLabel(b_right, text="Network: Bitcoin (Auto-Transfer on 100%)", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        self.lbl_track_net.pack(pady=(0, 8))

        # Progress Bar towards payout
        prog_box = ctk.CTkFrame(tracker_card, fg_color="transparent")
        prog_box.pack(fill="x", padx=16, pady=(4, 10))

        self.lbl_progress_text = ctk.CTkLabel(
            prog_box,
            text="Payout Progress: 0.0%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_progress_text.pack(anchor="w", pady=(0, 4))

        self.prog_bar = ctk.CTkProgressBar(prog_box, height=14, corner_radius=7)
        self.prog_bar.set(0.0)
        self.prog_bar.pack(fill="x")

        # Open web dashboard button
        btn_open_web = ctk.CTkButton(
            tracker_card,
            text="Open Full Web Dashboard on Unmineable.com",
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            height=32,
            command=self.open_unmineable_web
        )
        btn_open_web.pack(anchor="w", padx=16, pady=(6, 16))

        # Section 2: Bitcoin & UPI Account Setup Wizard Card
        acc_card = ctk.CTkFrame(scroll_tracker, corner_radius=12, fg_color="#181a20")
        acc_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            acc_card,
            text="Bitcoin (BTC) & UPI Cashout Setup Wizard",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            acc_card,
            text="Configure where your mined Bitcoin is sent and link your UPI ID for instant INR withdrawals.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Step 1: Bitcoin Address Setup & Real-Time Validator
        ctk.CTkLabel(acc_card, text="Step 1: Your Bitcoin (BTC) Payout Address", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.entry_wiz_btc = ctk.CTkEntry(
            acc_card,
            placeholder_text="e.g. 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa or bc1qar0srrr...",
            height=34
        )
        self.entry_wiz_btc.pack(fill="x", padx=16, pady=(2, 4))
        self.entry_wiz_btc.bind("<KeyRelease>", self._on_wiz_btc_key_release)

        self.lbl_btc_val_badge = ctk.CTkLabel(
            acc_card,
            text="Paste a Bitcoin address above to validate",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        self.lbl_btc_val_badge.pack(anchor="w", padx=16, pady=(0, 10))

        # Step 2: UPI ID for Cashout
        row_upi = ctk.CTkFrame(acc_card, fg_color="transparent")
        row_upi.pack(fill="x", padx=16, pady=(4, 12))
        row_upi.grid_columnconfigure((0, 1), weight=1)

        # UPI ID Field
        box_u1 = ctk.CTkFrame(row_upi, fg_color="transparent")
        box_u1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(box_u1, text="Step 2: Your UPI ID (Google Pay / PhonePe / Paytm)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.entry_wiz_upi = ctk.CTkEntry(box_u1, placeholder_text="e.g. yourname@okhdfcbank or 9876543210@paytm", height=34)
        self.entry_wiz_upi.pack(fill="x")

        # Preferred Exchange for Cashout
        box_u2 = ctk.CTkFrame(row_upi, fg_color="transparent")
        box_u2.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(box_u2, text="Preferred Exchange Platform", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.exch_var = ctk.StringVar(value=self.config.get("preferred_exchange", "Binance P2P"))
        self.menu_exch = ctk.CTkOptionMenu(
            box_u2,
            values=["Binance P2P (0% Fee, Fast UPI)", "CoinDCX (Indian Direct UPI)", "Mudrex (Indian Direct UPI)", "Bybit P2P", "WazirX"],
            variable=self.exch_var,
            height=34
        )
        self.menu_exch.pack(fill="x")

        # Action Button to Save Account Details & Apply
        btn_save_account = ctk.CTkButton(
            acc_card,
            text="Apply & Save Account to Miner",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=38,
            command=self.save_account_wizard
        )
        btn_save_account.pack(anchor="w", padx=16, pady=(4, 16))

    # ---------------- TAB 3: SAFETY & TUNING ----------------
    def _build_tab_safety(self):
        scroll_safety = ctk.CTkScrollableFrame(self.tab_safety, fg_color="transparent")
        scroll_safety.pack(fill="both", expand=True, padx=20, pady=10)

        # Thermal Guardian Card
        therm_card = ctk.CTkFrame(scroll_safety, corner_radius=12, fg_color="#181a20")
        therm_card.pack(fill="x", pady=(0, 14), padx=4)

        ctk.CTkLabel(
            therm_card,
            text="HP Victus Laptop Thermal Guardian",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f59e0b"
        ).pack(anchor="w", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            therm_card,
            text="Protects laptop thermals, fan bearings, and battery from prolonged heat buildup.\nAutomatically pauses mining when GPU temp crosses max threshold and resumes once cooled down.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Enable Thermal Guard switch
        self.guard_switch_var = ctk.BooleanVar(value=self.config.get("enable_temp_guard", True))
        self.sw_guard = ctk.CTkSwitch(
            therm_card,
            text="Enable Active Thermal Guardian Auto-Pause",
            variable=self.guard_switch_var,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.sw_guard.pack(anchor="w", padx=16, pady=(0, 12))

        # Max Safe Temp Slider
        self.lbl_slider_max = ctk.CTkLabel(
            therm_card,
            text=f"Max Safe GPU Temperature: {self.config.get('max_safe_temp', 74)}°C (Pause Trigger)",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_slider_max.pack(anchor="w", padx=16, pady=(4, 2))

        self.slider_max_temp = ctk.CTkSlider(
            therm_card,
            from_=60,
            to=82,
            number_of_steps=22,
            command=self._on_max_temp_slider
        )
        self.slider_max_temp.set(self.config.get("max_safe_temp", 74))
        self.slider_max_temp.pack(fill="x", padx=16, pady=(0, 12))

        # Resume Temp Slider
        self.lbl_slider_resume = ctk.CTkLabel(
            therm_card,
            text=f"Resume Mining Cooldown Temperature: {self.config.get('resume_temp', 63)}°C",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_slider_resume.pack(anchor="w", padx=16, pady=(4, 2))

        self.slider_resume_temp = ctk.CTkSlider(
            therm_card,
            from_=50,
            to=70,
            number_of_steps=20,
            command=self._on_resume_temp_slider
        )
        self.slider_resume_temp.set(self.config.get("resume_temp", 63))
        self.slider_resume_temp.pack(fill="x", padx=16, pady=(0, 16))

        # CPU Mining Tuning Card
        cpu_card = ctk.CTkFrame(scroll_safety, corner_radius=12, fg_color="#181a20")
        cpu_card.pack(fill="x", pady=(0, 14), padx=4)

        ctk.CTkLabel(
            cpu_card,
            text="CPU Dual-Mining (AMD Ryzen 5 5600H - 12 Threads)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=16, pady=(14, 6))

        # Enable Dual CPU Mining switch
        self.dual_cpu_var = ctk.BooleanVar(value=self.config.get("cpu_mining_enabled", True))
        self.sw_dual_cpu = ctk.CTkSwitch(
            cpu_card,
            text="Enable Dual CPU Mining (+35% Extra Profit to Bitcoin)",
            variable=self.dual_cpu_var,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.sw_dual_cpu.pack(anchor="w", padx=16, pady=(0, 10))

        self.lbl_cpu_threads = ctk.CTkLabel(
            cpu_card,
            text=f"Max CPU Mining Threads: {self.config.get('cpu_threads', 6)} / 12 (Keeps laptop responsive)",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_cpu_threads.pack(anchor="w", padx=16, pady=(4, 2))

        self.slider_cpu_threads = ctk.CTkSlider(
            cpu_card,
            from_=1,
            to=12,
            number_of_steps=11,
            command=self._on_cpu_threads_slider
        )
        self.slider_cpu_threads.set(self.config.get("cpu_threads", 6))
        self.slider_cpu_threads.pack(fill="x", padx=16, pady=(0, 16))

        # Advanced CLI flags Card
        adv_card = ctk.CTkFrame(scroll_safety, corner_radius=12, fg_color="#181a20")
        adv_card.pack(fill="x", pady=(0, 14), padx=4)

        ctk.CTkLabel(
            adv_card,
            text="Custom Miner CLI Flags (Advanced)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.entry_extra_flags = ctk.CTkEntry(
            adv_card,
            placeholder_text="e.g. --lock-cclock 1200 --api-bind 127.0.0.1:5000",
            height=34
        )
        self.entry_extra_flags.insert(0, self.config.get("custom_extra_flags", ""))
        self.entry_extra_flags.pack(fill="x", padx=16, pady=(0, 16))

    def _on_max_temp_slider(self, val):
        val_int = int(val)
        self.lbl_slider_max.configure(text=f"Max Safe GPU Temperature: {val_int}°C (Pause Trigger)")

    def _on_resume_temp_slider(self, val):
        val_int = int(val)
        self.lbl_slider_resume.configure(text=f"Resume Mining Cooldown Temperature: {val_int}°C")

    def _on_cpu_threads_slider(self, val):
        val_int = int(val)
        self.lbl_cpu_threads.configure(text=f"Max CPU Mining Threads: {val_int} / 12 (Keeps laptop responsive)")

    # ---------------- TAB 4: LIVE CONSOLE ----------------
    def _build_tab_console(self):
        bar = ctk.CTkFrame(self.tab_console, fg_color="transparent")
        bar.pack(fill="x", padx=4, pady=(6, 8))

        ctk.CTkLabel(bar, text="Real-Time Miner Output", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_copy = ctk.CTkButton(bar, text="Copy Log", width=90, height=28, command=self.copy_console_log)
        btn_copy.pack(side="right", padx=(6, 0))

        btn_clear = ctk.CTkButton(bar, text="Clear", width=80, height=28, fg_color="#475569", command=self.clear_console_log)
        btn_clear.pack(side="right")

        self.autoscroll_var = ctk.BooleanVar(value=True)
        chk_scroll = ctk.CTkCheckBox(bar, text="Autoscroll", variable=self.autoscroll_var)
        chk_scroll.pack(side="right", padx=(0, 14))

        self.console_box = ctk.CTkTextbox(
            self.tab_console,
            font=ctk.CTkFont(family="monospace", size=12),
            wrap="none",
            fg_color="#0f172a",
            text_color="#38bdf8"
        )
        self.console_box.pack(fill="both", expand=True, padx=4, pady=(0, 6))

    def copy_console_log(self):
        txt = self.console_box.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(txt)
        messagebox.showinfo("Copied", "Console logs copied to clipboard!")

    def clear_console_log(self):
        self.console_box.delete("1.0", "end")

    # ---------------- TAB 5: GUIDE & FAQ ----------------
    def _build_tab_guide(self):
        scroll_guide = ctk.CTkScrollableFrame(self.tab_guide, fg_color="transparent")
        scroll_guide.pack(fill="both", expand=True, padx=20, pady=10)

        guide_text = """Universal Cryptocurrency Mining & Cashout Guide

1. Universal GPU & VRAM Tier Recommendations
- Tier 1 (Low VRAM: 2GB - 4GB, e.g. GTX 1650, GTX 1050 Ti, RX 570 4GB):
  * Optimal: NexaPow (NEXA), Karlsen (KLS), Radiant (RXD), IronFish (IRON).
  * Uses ~1.2 GB VRAM, operates cool, silent fans, peak hash efficiency.
- Tier 2 (Mid/High VRAM: 6GB - 24GB, e.g. RTX 2060, 3060, 4060, 4070, 4080/4090, RX 6700/7800):
  * Optimal: NexaPow, Ravencoin (KawPow), Ethereum Classic (Etchash), Ergo (Autolykos2).
- Tier 0 (Multi-Core CPU: AMD Ryzen & Intel Core):
  * Optimal: Monero (RandomX via XMRig). Can run concurrently alongside any GPU for +35% earnings!

2. Direct Bitcoin (BTC) Payouts via Unmineable
- Select the 'Unmineable' preset in the Mining Suite.
- Your GPU mines NexaPow; the pool automatically converts your mining rewards into real Bitcoin (BTC).
- No manual exchange trading needed: payouts are sent directly to your Bitcoin wallet once 0.00075 BTC is reached.

3. Cashing out Bitcoin to Bank via UPI (Google Pay, PhonePe, Paytm)
- Step 1: When your mined BTC arrives in your exchange wallet (Binance, CoinDCX, Bybit), open the P2P or Quick Sell tab.
- Step 2: Choose 'Sell BTC' and select 'UPI' or 'IMPS' as your payment method.
- Step 3: Enter your UPI ID (e.g. name@okhdfcbank or 9876543210@paytm).
- Step 4: The buyer transfers INR directly into your bank via UPI. Once confirmed in your banking app, release the BTC!

4. Thermal Guardian & Hardware Longevity
- Laptop Care: Elevate the rear rubber feet by 1-2 cm for intake airflow. Never mine with laptop lid closed.
- Keep the Thermal Guardian active (default 74 deg C cutoff, resumes at 63 deg C).
- Desktop Care: Maintain clean dust filters and adequate case airflow."""
        lbl = ctk.CTkLabel(
            scroll_guide,
            text=guide_text,
            font=ctk.CTkFont(size=13),
            justify="left",
            wraplength=850
        )
        lbl.pack(anchor="w", padx=10, pady=10)

    # ---------------- UI STATE & PRESETS ----------------
    def _load_config_to_ui(self):
        preset_name = self.config.get("selected_preset", "Unmineable [Mine & Payout in BTC/USDT/DOGE]")
        if preset_name not in PRESETS:
            preset_name = "Unmineable [Mine & Payout in BTC/USDT/DOGE]"
            
        self.preset_var.set(preset_name)
        self.on_preset_changed(preset_name)

        wallet = self.config.get("wallet_address", "")
        if wallet:
            self.entry_wallet.delete(0, "end")
            self.entry_wallet.insert(0, wallet)
            self.entry_wiz_btc.delete(0, "end")
            self.entry_wiz_btc.insert(0, wallet)
            self._validate_and_display_badge(wallet)

        if self.config.get("upi_id"):
            self.entry_wiz_upi.delete(0, "end")
            self.entry_wiz_upi.insert(0, self.config.get("upi_id"))

        if self.config.get("worker_name"):
            self.entry_worker.delete(0, "end")
            self.entry_worker.insert(0, self.config.get("worker_name"))

        if self.config.get("custom_pool_url"):
            self.entry_custom_pool.delete(0, "end")
            self.entry_custom_pool.insert(0, self.config.get("custom_pool_url"))

        self.toggle_custom_pool()

    def on_preset_changed(self, choice):
        preset = PRESETS.get(choice, PRESETS["Unmineable [Mine & Payout in BTC/USDT/DOGE]"])
        self.lbl_preset_desc.configure(text=f"{preset['description']}\nVRAM Usage: {preset['vram_req']}")

        pool_names = [f"{name} ({url})" for name, url in preset["pools"]]
        self.pool_menu.configure(values=pool_names)
        
        current_saved_pool = self.config.get("pool_url", "")
        matched = False
        for name, url in preset["pools"]:
            if url == current_saved_pool:
                self.pool_var.set(f"{name} ({url})")
                matched = True
                break
        if not matched and pool_names:
            self.pool_var.set(pool_names[0])

        self.entry_wallet.configure(placeholder_text=preset.get("wallet_placeholder", "Enter wallet address"))

        if preset.get("supports_unmineable", False):
            self.lbl_asset.configure(text_color="#f59e0b")
            self.asset_menu.configure(state="normal")
        else:
            self.lbl_asset.configure(text_color="#64748b")
            self.asset_menu.configure(state="disabled")

    def _on_asset_changed(self, choice):
        self.lbl_kpi_algo.configure(text=f"Payout: {choice}")
        self.query_tracker_stats()

    def toggle_custom_pool(self):
        if self.use_custom_pool_var.get():
            self.entry_custom_pool.configure(state="normal")
            self.pool_menu.configure(state="disabled")
        else:
            self.entry_custom_pool.configure(state="disabled")
            self.pool_menu.configure(state="normal")

    def _on_wallet_key_release(self, event=None):
        addr = self.entry_wallet.get().strip()
        self.entry_wiz_btc.delete(0, "end")
        self.entry_wiz_btc.insert(0, addr)
        self._validate_and_display_badge(addr)

    def _on_wiz_btc_key_release(self, event=None):
        addr = self.entry_wiz_btc.get().strip()
        self.entry_wallet.delete(0, "end")
        self.entry_wallet.insert(0, addr)
        self._validate_and_display_badge(addr)

    def _validate_and_display_badge(self, addr):
        if not addr:
            self.lbl_btc_val_badge.configure(text="Paste a Bitcoin address above to validate", text_color="#94a3b8")
            return
        is_valid, msg = validate_btc_address(addr)
        if is_valid:
            self.lbl_btc_val_badge.configure(text=f"✓ {msg}", text_color="#10b981")
        else:
            self.lbl_btc_val_badge.configure(text=f"✕ {msg}", text_color="#ef4444")

    # ---------------- POOL TRACKER & WIZARD ACTIONS ----------------
    def query_tracker_stats(self):
        addr = self.entry_wallet.get().strip()
        coin = self.asset_var.get() if self.preset_var.get().startswith("Unmineable") else "BTC"
        if addr:
            self.lbl_market_price.configure(text="Updating pool stats & market price...")
            self.tracker.query(addr, coin=coin)

    def on_tracker_update(self, payload):
        self.after(0, self._apply_tracker_ui, payload)

    def _apply_tracker_ui(self, payload):
        stats = payload.get("stats", {})
        price = payload.get("price", {})
        val_inr = payload.get("value_inr", 0.0)
        
        inr_rate = price.get("inr", 7100000.0)
        usd_rate = price.get("usd", 75000.0)
        self.lbl_market_price.configure(text=f"1 BTC ≈ ₹{inr_rate:,.0f} INR (${usd_rate:,.0f} USD)")

        if stats.get("success"):
            bal_str = stats.get("balance_str", "0.00000000")
            coin = stats.get("coin", "BTC")
            thresh_str = stats.get("threshold_str", "0.00075000")
            pct = stats.get("progress_pct", 0.0)

            self.lbl_track_btc.configure(text=f"{bal_str} {coin}")
            self.lbl_track_inr.configure(text=f"≈ ₹{val_inr:,.2f} INR")
            self.lbl_mini_balance.configure(text=f"{bal_str} {coin}")
            self.lbl_mini_inr.configure(text=f"≈ ₹{val_inr:,.2f} INR")

            self.lbl_track_thresh.configure(text=f"{thresh_str} {coin}")
            self.lbl_progress_text.configure(text=f"Payout Progress: {pct:.1f}% ({bal_str} / {thresh_str} {coin})")
            self.prog_bar.set(min(1.0, pct / 100.0))
        else:
            err = stats.get("error", "Ready to mine")
            self.lbl_track_btc.configure(text="0.00000000 BTC")
            self.lbl_track_inr.configure(text=f"Status: {err}")

    def open_unmineable_web(self):
        addr = self.entry_wallet.get().strip()
        coin = self.asset_var.get()
        if addr:
            url = f"https://unmineable.com/coins/{coin}/address/{addr}"
            webbrowser.open(url)
        else:
            messagebox.showinfo("Address Required", "Please enter your wallet address first to view your dashboard.")

    def save_account_wizard(self):
        btc_addr = self.entry_wiz_btc.get().strip()
        upi_id = self.entry_wiz_upi.get().strip()
        pref_exch = self.exch_var.get()

        if btc_addr:
            is_valid, msg = validate_btc_address(btc_addr)
            if not is_valid:
                res = messagebox.askyesno("Address Warning", f"The address format does not appear to be standard Bitcoin:\n{msg}\n\nDo you still want to save it?")
                if not res:
                    return

        self.entry_wallet.delete(0, "end")
        self.entry_wallet.insert(0, btc_addr)

        self.config["wallet_address"] = btc_addr
        self.config["upi_id"] = upi_id
        self.config["preferred_exchange"] = pref_exch
        self.config["payout_asset"] = "BTC"
        self.config["selected_preset"] = "Unmineable [Mine & Payout in BTC/USDT/DOGE]"
        
        save_config(self.config)
        self.query_tracker_stats()
        messagebox.showinfo("Saved", "Account & Bitcoin wallet successfully configured and applied to Miner Suite!")
        self.tabview.set("Mining Suite")

    def _collect_current_config(self):
        preset_name = self.preset_var.get()
        preset = PRESETS.get(preset_name, PRESETS["Unmineable [Mine & Payout in BTC/USDT/DOGE]"])
        
        pool_str = self.pool_var.get()
        pool_url = ""
        for name, url in preset["pools"]:
            if url in pool_str:
                pool_url = url
                break
        if not pool_url and preset["pools"]:
            pool_url = preset["pools"][0][1]

        return {
            "selected_preset": preset_name,
            "pool_url": pool_url,
            "use_custom_pool": self.use_custom_pool_var.get(),
            "custom_pool_url": self.entry_custom_pool.get().strip(),
            "wallet_address": self.entry_wallet.get().strip(),
            "worker_name": self.entry_worker.get().strip() or "Victus-1650",
            "payout_asset": self.asset_var.get(),
            "upi_id": self.entry_wiz_upi.get().strip(),
            "preferred_exchange": self.exch_var.get(),
            "max_safe_temp": int(self.slider_max_temp.get()),
            "resume_temp": int(self.slider_resume_temp.get()),
            "enable_temp_guard": self.guard_switch_var.get(),
            "cpu_mining_enabled": self.dual_cpu_var.get(),
            "cpu_threads": int(self.slider_cpu_threads.get()),
            "custom_extra_flags": self.entry_extra_flags.get().strip()
        }

    def open_cyber_hud(self):
        try:
            base_dir = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
            server_path = os.path.join(base_dir, "visualizer", "server.py")
            subprocess.Popen([sys.executable, server_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        webbrowser.open("http://127.0.0.1:8765")

    def save_ui_to_config(self):
        cfg = self._collect_current_config()
        self.config.update(cfg)
        if save_config(self.config):
            messagebox.showinfo("Saved", "Configuration successfully saved to ~/.config/apexminer/config.json")

    # ---------------- MINER CONTROLS ----------------
    def toggle_mining(self):
        if self.miner.state in ["RUNNING", "STARTING", "PAUSED_OVERHEAT"]:
            self.miner.stop()
        else:
            cfg = self._collect_current_config()
            wallet = cfg["wallet_address"]
            if not wallet:
                res = messagebox.askyesno(
                    "Wallet Address Empty",
                    "No payout Bitcoin wallet address was entered.\n\nWould you like to open the Account Setup Wizard to configure one now?"
                )
                if res:
                    self.tabview.set("Account & Tracker")
                return

            success, msg = self.miner.start(cfg, is_benchmark=False)
            if not success:
                messagebox.showerror("Failed to Start", msg)

    def run_benchmark(self):
        if self.miner.state in ["RUNNING", "STARTING", "PAUSED_OVERHEAT"]:
            messagebox.showwarning("Busy", "Stop the current mining session before starting a benchmark.")
            return

        cfg = self._collect_current_config()
        self.tabview.set("Live Console")
        success, msg = self.miner.start(cfg, is_benchmark=True)
        if not success:
            messagebox.showerror("Benchmark Error", msg)

    # ---------------- CALLBACKS ----------------
    def on_telemetry_update(self, stats):
        try:
            self.after(0, self._apply_telemetry_ui, stats)
        except Exception:
            pass

    def _apply_telemetry_ui(self, stats):
        try:
            gpu_temp = stats.get("gpu_temp", 0)
            gpu_power = stats.get("gpu_power", 0.0)
            gpu_power_cap = stats.get("gpu_power_cap", 0.0)
            vram_used = stats.get("gpu_mem_used", 0)
            fallback_vram = int(self.hw.primary_gpu["vram_mb"]) if self.hw.has_gpu else 4096
            vram_total = stats.get("gpu_mem_total") or fallback_vram
            
            if gpu_temp < 65:
                t_color = "#10b981"
            elif gpu_temp < 74:
                t_color = "#f59e0b"
            else:
                t_color = "#ef4444"

            self.lbl_temp.configure(text=f"{gpu_temp} °C", text_color=t_color)
            if gpu_power_cap > 0:
                self.lbl_power.configure(text=f"{gpu_power:.1f} W / {int(gpu_power_cap)}W")
            else:
                self.lbl_power.configure(text=f"{gpu_power:.1f} W")
            self.lbl_vram.configure(text=f"{vram_used} / {vram_total} MB")

            self.miner.on_telemetry(stats)
        except Exception:
            pass

    def on_miner_status(self, data):
        try:
            self.after(0, self._apply_status_ui, data)
        except Exception:
            pass

    def _apply_status_ui(self, data):
        try:
            state = data["state"]
            hashrate = data["hashrate"]
            shares = data["shares_accepted"]
            rejected = data["shares_rejected"]
            uptime = data["uptime"]
            
            hours, rem = divmod(uptime, 3600)
            mins, secs = divmod(rem, 60)
            uptime_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

            self.lbl_kpi_hashrate.configure(text=hashrate)
            self.lbl_hashrate_hud.configure(text=hashrate)
            self.lbl_kpi_shares.configure(text=str(shares))
            self.lbl_kpi_rejected.configure(text=str(rejected))
            self.lbl_kpi_uptime.configure(text=uptime_str)

            if state == "RUNNING":
                self.lbl_status_title.configure(text="ACTIVE MINING", text_color="#10b981")
                self.btn_toggle_mine.configure(
                    text="STOP MINING",
                    fg_color="#ef4444",
                    hover_color="#dc2626"
                )
                self.btn_benchmark.configure(state="disabled")
            elif state == "PAUSED_OVERHEAT":
                self.lbl_status_title.configure(text="THERMAL PAUSED", text_color="#f59e0b")
                self.btn_toggle_mine.configure(
                    text="CANCEL COOLDOWN",
                    fg_color="#f59e0b",
                    hover_color="#d97706"
                )
            elif state == "STARTING":
                self.lbl_status_title.configure(text="INITIALIZING...", text_color="#38bdf8")
            else:
                self.lbl_status_title.configure(text="STOPPED", text_color="#64748b")
                self.btn_toggle_mine.configure(
                    text="START MINING",
                    fg_color="#10b981",
                    hover_color="#059669"
                )
                self.btn_benchmark.configure(state="normal")
        except Exception:
            pass

    def on_miner_log(self, text):
        try:
            self.after(0, self._append_console_log, text)
        except Exception:
            pass

    def _append_console_log(self, text):
        try:
            self.console_box.insert("end", text + "\n")
            if self.autoscroll_var.get():
                self.console_box.see("end")
        except Exception:
            pass

    def on_close(self):
        self.telemetry.stop()
        self.miner.stop()
        self.destroy()

def main():
    app = ApexMinerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
