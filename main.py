import os
import time
import requests
import threading
from flask import Flask
import yfinance as yf

# === Konfigurasi dasar ===
PAIR = "XAUUSD=X"
RR_RATIO = 3
TIMEFRAMES = ["5m", "15m", "1h", "4h"]
UPDATE_INTERVAL = 600  # 10 menit

# === Token Telegram dari .env ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ VX RSI GACOR+ Bot is running on Render!"

def send_telegram_message(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Token/Chat ID belum diatur.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
        print("✅ Pesan terkirim ke Telegram")
    except Exception as e:
        print("⚠️ Gagal kirim pesan:", e)

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fetch_data():
    msg = f"💎 <b>XAUUSD</b> — VX RSI GACOR+ (Intraday)\n\n"
    try:
        ticker = yf.Ticker(PAIR)
        for tf in TIMEFRAMES:
            data = ticker.history(period="1d", interval=tf)
            if data.empty:
                msg += f"⚠️ No data for {tf}\n"
                continue

            price = data["Close"].iloc[-1]
            rsi = calculate_rsi(data["Close"]).iloc[-1]
            signal = ""
            tp, sl = 0, 0

            if rsi > 70:
                signal = "🔴 SELL"
                sl = price + 3
                tp = price - (3 * RR_RATIO)
            elif rsi < 30:
                signal = "🟢 BUY"
                sl = price - 3
                tp = price + (3 * RR_RATIO)
            else:
                signal = "⚪ WAIT"

            msg += f"⏱ <b>{tf.upper()}</b> RSI: {rsi:.2f} → {signal}\n🎯 TP: {tp:.2f} | 🛡 SL: {sl:.2f}\n\n"

        msg += f"⏰ Update otomatis tiap {UPDATE_INTERVAL/60:.0f} menit."
        send_telegram_message(msg)

    except Exception as e:
        print(f"❌ Error fetching data: {e}")

def scheduler():
    while True:
        fetch_data()
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=scheduler).start()
    app.run(host="0.0.0.0", port=8080)
