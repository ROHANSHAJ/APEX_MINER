# ⚡ ApexMiner Studio — Universal Edition

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-brightgreen.svg?logo=linux&logoColor=white)](https://github.com/)
[![GPU Support](https://img.shields.io/badge/GPU-NVIDIA%20%7C%20AMD%20%7C%20Intel-76B900.svg?logo=nvidia&logoColor=white)](https://github.com/)
[![CPU Mining](https://img.shields.io/badge/CPU-AMD%20Ryzen%20%7C%20Intel%20Core-ED1C24.svg?logo=amd&logoColor=white)](https://github.com/)
[![Visualizer](https://img.shields.io/badge/Cyber%20HUD-3D%20Live%20Cockpit-ff007f.svg)](http://127.0.0.1:8765)

**ApexMiner Studio** is an open-source, universal cryptocurrency mining suite and hardware management dashboard. Engineered to support **any GPU** (NVIDIA, AMD, Intel) across all VRAM tiers (2 GB to 24 GB) and **any multi-core CPU** across Linux and Windows.

ApexMiner combines high-efficiency GPU algorithms, CPU dual-mining, an automated **Bitcoin (BTC) payout engine via Unmineable**, real-time **UPI cashout integration** (Google Pay, PhonePe, Paytm), and a standalone **3D Cyberpunk Cockpit Visualizer**.

---

## 🌟 Highlights & Features

- 🎮 **Universal Hardware Detection**: Automatically detects your exact GPU model, total VRAM, power limits, and multi-core CPU topology on launch.
- 🪙 **Direct Bitcoin (BTC) Payouts**: Uses Unmineable auto-swap pools so you earn real Bitcoin directly into your wallet without manual exchange trading.
- ⚡ **Dual-Mining Engine**: Simultaneously mines GPU-efficient Proof-of-Work (e.g. NexaPow) and CPU RandomX (XMRig) for **+35% extra daily Satoshi earnings**.
- 🛡️ **Thermal Guardian**: Autonomous hardware safety system that continuously monitors GPU temperatures. Automatically pauses mining if temperatures exceed limit (e.g. 74°C) and resumes when cooled (63°C).
- 📊 **In-App Account & Pool Tracker**:
  - Live Bitcoin Market Price ticker (BTC/INR and BTC/USD via CoinGecko).
  - Unpaid pool balance query with percentage progress bar toward minimum payout (`0.00075 BTC`).
  - Real-time ₹ INR balance converter.
  - Multi-format Bitcoin address validator (Native SegWit `bc1`, SegWit `3...`, Legacy `1...`).
  - UPI Cashout Profile (stores UPI ID and step-by-step guides for Binance P2P, CoinDCX, Mudrex).
- 🚀 **Cyber HUD Cockpit Visualizer**:
  - Futuristic sci-fi dashboard running at `http://127.0.0.1:8765`.
  - Interactive 3D rotating Bitcoin blockchain node.
  - Radial speedometer gauge for live hashrate.
  - Multi-thread audio-equalizer spectrum tracking every CPU thread.
  - Rolling Satoshi & Indian Rupee (₹ INR) accumulator with celebratory audio cues on accepted shares.
  - Borderless Fullscreen toggle (`F11`).

---

## 🖥️ Universal Hardware Compatibility & VRAM Tiers

ApexMiner dynamically adapts to your hardware configuration:

| Tier | Hardware Example | Recommended Algorithm | VRAM Required | Power / Thermals |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1 (Ultra-Low / Low VRAM)** | GTX 1650 (4GB), GTX 1050 Ti, GTX 1060 3GB, RX 570 4GB | **NexaPow** (`nexapow`), **Karlsen** (`karlsenhashv2`), **Radiant** (`sha512256d`), **IronFish** (`fishhash`) | **0.3 GB – 1.8 GB** | Extremely cool (25W – 50W), silent fans, peak hashrate efficiency |
| **Tier 2 (Mid / High VRAM)** | RTX 2060, 3060, 4060, 4070, 4080/4090, RX 6700/7800 | **NexaPow**, **Ravencoin** (`kawpow`), **Ethereum Classic** (`etchash`), **Ergo** (`autolykos2`) | **5.0 GB – 8.0 GB+** | Maximum profit throughput on full DAG networks |
| **Tier 0 (Multi-Core CPU)** | AMD Ryzen (5600H, 5800X, 7900X), Intel Core (i5, i7, i9) | **Monero RandomX** (`xmrig`) | **0 GB (CPU Only)** | Configurable background thread limiter (dual-mines with GPU) |

---

## 🚀 Quick Start & Installation

### Option 1: Linux (Ubuntu, Debian, Fedora, Arch, Pop!_OS)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/crypto_miner.git
   cd crypto_miner
   ```

2. **Run the one-click installer:**
   ```bash
   ./install.sh
   ```
   *The installer automatically validates Python, installs pip packages, fetches native mining engines, and creates desktop shortcuts.*

3. **Launch ApexMiner Studio:**
   - Double-click the **ApexMiner Studio** icon on your Desktop, or
   - Run from terminal:
     ```bash
     apexminer
     # or
     ./start_miner.sh
     ```

---

### Option 2: Windows 10 / Windows 11

1. **Clone or download the ZIP:**
   ```cmd
   git clone https://github.com/<your-username>/crypto_miner.git
   cd crypto_miner
   ```

2. **Run the one-click installer:**
   - Double-click `install.bat` (or execute in PowerShell / Command Prompt):
   ```cmd
   install.bat
   ```

3. **Launch ApexMiner Studio:**
   - Double-click `start_miner.bat`

---

## 🎮 Launching the Cyber HUD Visualizer

Launch the Cyber HUD Visualizer in any browser:
- Click **"Launch Cyber HUD Visualizer"** inside ApexMiner Studio GUI, or
- Double-click **Cyber HUD Visualizer** on your Desktop, or
- Run directly:
  ```bash
  apex-hud
  # or
  ./launch_hud.sh
  ```
- Open `http://127.0.0.1:8765` in any web browser and press `F11` for borderless fullscreen.

---

## 💳 Cashing Out Mined Bitcoin via UPI (India)

ApexMiner is configured to pay out directly to your Bitcoin address via Unmineable:

1. **Receive Bitcoin**:
   - Provide your Bitcoin wallet address (`1...`, `3...`, or `bc1...`) in the **Mining Suite** or **Account & Tracker** tab.
   - Once your unpaid balance hits `0.00075 BTC`, the pool automatically deposits your BTC.
2. **Transfer to Your Preferred Indian Exchange**:
   - Use an Indian FIU-registered exchange or global P2P exchange (e.g. Binance, CoinDCX, Mudrex, Bybit).
3. **Sell for Instant UPI Credit**:
   - In your exchange app, open **P2P** or **Quick Sell**.
   - Select **Sell BTC** and choose **UPI** as your receiving payment method.
   - Enter your UPI ID (e.g. `yourname@okaxis`, `yourname@paytm`, or `yourname@okhdfcbank`).
   - The verified P2P buyer transfers INR directly into your Indian bank account via Google Pay, PhonePe, or Paytm.
   - Once confirmed in your banking app, release the Bitcoin!

---

## 🛠️ Architecture & Project Structure

```text
crypto_miner/
├── app/
│   ├── main.py                  # CustomTkinter modern 5-tab GUI application
│   ├── hardware_detector.py     # Universal hardware detector (NVIDIA, AMD, Intel, CPU)
│   ├── telemetry.py             # Asynchronous hardware sensor monitor
│   ├── miner_controller.py      # Subprocess supervisor for Rigel & XMRig with Thermal Guardian
│   ├── presets.py               # Universal multi-tier algorithm preset database
│   ├── pool_tracker.py          # Real-time Unmineable API, CoinGecko price & wallet validator
│   ├── config_manager.py        # Persistent JSON configuration store
│   └── binary_downloader.py     # Automated cross-platform miner binary fetcher
├── bin/
│   └── .gitkeep                 # Native binary directory (populated by setup_binaries.py)
├── visualizer/
│   ├── index.html               # 3D sci-fi cockpit HUD (Canvas, Web Audio, SVG Gauges)
│   └── server.py                # Lightweight HTTP & telemetry API server (port 8765)
├── .github/
│   └── workflows/ci.yml         # GitHub Actions multi-OS syntax and import validation
├── install.sh                   # One-click Linux installer & desktop shortcut creator
├── install.bat                  # One-click Windows installer
├── start_miner.sh               # CLI launcher for Linux
├── launch_hud.sh                # Visualizer launcher
├── setup_binaries.py            # Standalone binary setup utility
├── requirements.txt             # Minimal Python dependencies
├── setup.py                     # Standard setuptools configuration
├── pyproject.toml               # Modern build backend specification
├── LICENSE                      # MIT Open Source License
└── README.md                    # Universal documentation
```

---

## 🛡️ Laptop & Desktop Safety Guidelines

1. **Elevation**: Elevate laptop rear rubber feet by 1–2 cm to ensure unobstructed air intake.
2. **Thermal Guardian**: Never disable the Thermal Guardian cutoff limit (default 74°C) when running on mobile GPUs.
3. **Laptop Lid**: Always keep the laptop lid open while mining to allow keyboard-deck heat dissipation.
4. **Campus Firewalls**: If mining on university or enterprise networks (e.g. Anna University / NKN), use mobile hotspot or connect via SSL stratum ports (`stratum+ssl://...:4444` or port `443`).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues, suggest new coin algorithms, or submit pull requests.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit your Changes (`git commit -m 'Add NewFeature'`)
4. Push to the Branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
