import time
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCHLIST = [
    "PZU.WA", "PKO.WA", "PEO.WA", "LPP.WA", "BDX.WA", "PKN.WA", "XTB.WA",
    "NVDA", "MSFT", "AAPL", "UNH", "COST", "QCOM", "VOO"
]

session = requests.Session()


def send_msg(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        session.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[Błąd wysyłki] {e}")


def download_data(ticker: str):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            print(f"[{ticker}] Brak danych")
            return None
        return df
    except Exception as e:
        print(f"[{ticker}] Błąd pobierania: {e}")
        return None


def analyze_ticker(ticker: str):
    df = download_data(ticker)
    if df is None or len(df) < 200:
        return None

    df["SMA200"] = ta.sma(df["Close"], length=200)
    df["RSI"] = ta.rsi(df["Close"], length=14)

    macd = ta.macd(df["Close"])
    df["MACD"] = macd["MACD_12_26_9"]
    df["SIGNAL"] = macd["MACDs_12_26_9"]

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(curr["Close"])
    rsi = float(curr["RSI"])
    sma200 = float(curr["SMA200"])
    macd_line = float(curr["MACD"])
    signal_line = float(curr["SIGNAL"])
    prev_macd = float(prev["MACD"])
    prev_signal = float(prev["SIGNAL"])

    # KUPNO
    if (
        price > sma200 and
        macd_line > signal_line and prev_macd <= prev_signal and
        rsi > 40
    ):
        return (
            f"🟢 *KUPNO: {ticker}*\n"
            f"Cena: {price:.2f}\n"
            f"RSI: {rsi:.1f}\n"
            f"MACD cross: bullish\n"
            f"Trend: powyżej SMA200"
        )

    # SPRZEDAŻ
    if (
        price < sma200 and
        macd_line < signal_line and prev_macd >= prev_signal and
        rsi < 60
    ):
        return (
            f"🔴 *SPRZEDAŻ: {ticker}*\n"
            f"Cena: {price:.2f}\n"
            f"RSI: {rsi:.1f}\n"
            f"MACD cross: bearish\n"
            f"Trend: poniżej SMA200"
        )

    return None


def check_market(label: str):
    print(f"\n--- Skanowanie: {label} ---")
    signals = []

    for ticker in WATCHLIST:
        try:
            signal = analyze_ticker(ticker)
            if signal:
                signals.append(signal)
        except Exception as e:
            print(f"[Błąd przy {ticker}] {e}")

    if signals:
        msg = f"📊 *{label}*\n\n" + "\n\n".join(signals)
    else:
        msg = f"✅ *{label}*\nBrak nowych sygnałów."

    send_msg(msg)


# --- PĘTLA GŁÓWNA ---
last_run = {"morning": None, "evening": None}

print("Bot działa na Railway i czeka na 08:30 oraz 18:00 (czas lokalny)...")

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    print("DEBUG:", current_time)

    if current_time == "09:08" and last_run["morning"] != now.date():
        check_market("RAPORT PORANNY")
        last_run["morning"] = now.date()

    if current_time == "16:00" and last_run["evening"] != now.date():
        check_market("RAPORT WIECZORNY")
        last_run["evening"] = now.date()

    time.sleep(5)
