"""
Configuration Manager for ApexMiner GUI
Persists user settings safely in ~/.config/apexminer/config.json
"""

import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/apexminer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "selected_preset": "Unmineable [Mine & Payout in BTC/USDT/DOGE]",
    "pool_url": "stratum+tcp://autolykos.unmineable.com:3333",
    "use_custom_pool": False,
    "custom_pool_url": "",
    "wallet_address": "",
    "worker_name": "Victus-1650",
    "payout_asset": "BTC",
    "upi_id": "",
    "preferred_exchange": "Binance P2P",
    "max_safe_temp": 74,
    "resume_temp": 63,
    "enable_temp_guard": True,
    "power_limit_watts": 45,
    "low_intensity": False,
    "cpu_mining_enabled": False,
    "cpu_threads": 6,
    "custom_algo": "autolykos2",
    "custom_extra_flags": "",
    "auto_start": False,
    "theme": "dark"
}

def load_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            return merged
    except Exception as e:
        print(f"Error loading config, using defaults: {e}")
        return dict(DEFAULT_CONFIG)

def save_config(config_dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
