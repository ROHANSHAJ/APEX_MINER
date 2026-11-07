"""
Pool Tracker & Account Intelligence for ApexMiner
Fetches live Unmineable pool balance, payout progress, and live BTC-to-INR conversions.
"""

import re
import json
import threading
import urllib.request

BTC_REGEX = re.compile(
    r'^(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59})$',
    re.IGNORECASE
)

def validate_btc_address(addr):
    addr = addr.strip()
    if not addr:
        return False, "Address field is empty"
    if BTC_REGEX.match(addr):
        if addr.startswith("bc1"):
            return True, "Valid Native SegWit (Bech32) Address"
        elif addr.startswith("3"):
            return True, "Valid SegWit (P2SH) Address"
        elif addr.startswith("1"):
            return True, "Valid Legacy Address"
        return True, "Valid Bitcoin Address"
    return False, "Invalid Bitcoin address format"

def fetch_btc_price():
    """Fetches real-time BTC price in INR and USD via CoinGecko API"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=inr,usd"
        req = urllib.request.Request(url, headers={"User-Agent": "ApexMiner/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            btc = data.get("bitcoin", {})
            return {
                "success": True,
                "inr": float(btc.get("inr", 7100000)),
                "usd": float(btc.get("usd", 75000))
            }
    except Exception as e:
        return {"success": False, "inr": 7100000.0, "usd": 75000.0, "error": str(e)}

def fetch_unmineable_stats(address, coin="BTC"):
    """Fetches real-time pool balance and payout threshold from Unmineable API"""
    clean_addr = address.strip()
    if not clean_addr:
        return {"success": False, "error": "No wallet address provided"}

    try:
        url = f"https://api.unmineable.com/v4/address/{clean_addr}?coin={coin}"
        req = urllib.request.Request(url, headers={"User-Agent": "ApexMiner/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success") and "data" in result:
                d = result["data"]
                bal = float(d.get("balance", "0.0"))
                threshold = float(d.get("payment_threshold", "0.00075"))
                
                # Progress calculation
                pct = min(100.0, (bal / threshold * 100.0)) if threshold > 0 else 0.0
                
                return {
                    "success": True,
                    "address": clean_addr,
                    "coin": coin,
                    "balance": bal,
                    "balance_str": f"{bal:.8f}",
                    "threshold": threshold,
                    "threshold_str": f"{threshold:.8f}",
                    "progress_pct": pct,
                    "network": d.get("network", "BTC"),
                    "auto_pay": d.get("auto", True),
                    "url": f"https://unmineable.com/coins/{coin}/address/{clean_addr}"
                }
            else:
                return {"success": False, "error": result.get("msg", "Failed to retrieve pool stats")}
    except Exception as e:
        return {"success": False, "error": str(e)}

class AsyncTracker:
    """Non-blocking background tracker for the GUI"""
    def __init__(self, callback):
        self.callback = callback

    def query(self, address, coin="BTC"):
        threading.Thread(target=self._run_query, args=(address, coin), daemon=True).start()

    def _run_query(self, address, coin):
        stats = fetch_unmineable_stats(address, coin)
        price_info = fetch_btc_price()
        
        balance_btc = stats.get("balance", 0.0) if stats.get("success") else 0.0
        btc_inr = price_info.get("inr", 7100000.0)
        btc_usd = price_info.get("usd", 75000.0)
        
        val_inr = balance_btc * btc_inr
        val_usd = balance_btc * btc_usd

        payload = {
            "stats": stats,
            "price": price_info,
            "value_inr": val_inr,
            "value_usd": val_usd
        }
        
        if self.callback:
            try:
                self.callback(payload)
            except Exception as e:
                print(f"AsyncTracker callback error: {e}")
