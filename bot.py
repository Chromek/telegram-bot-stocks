import time
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

# 1. KONFIGURACJA
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print(f"--- DIAGNOSTYKA STARTU ---")
print(f"DEBUG: Czy TOKEN został wczytany? {'TAK' if TOKEN else 'NIE'}")
print(f"DEBUG: Czy CHAT_ID został wczytany? {'TAK' if CHAT_ID else 'NIE'}")
print(f"--------------------------")

WATCHLIST = [
    "PZU.WA", "PKO.WA", "PEO.WA", "LPP.WA", "BDX.WA", "PKN.WA", "XTB.WA",
    "NVDA", "MSFT", "AAPL", "UNH", "COST", "QCOM", "VOO"
]

session = requests.Session()

def send_msg(text: str):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        session.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"[Błąd wysyłki] {e}")

def analyze_ticker(ticker: str):
    try:
        # Pobieramy dane i wymuszamy prosty format (spłaszczenie)
        df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        
        if df.empty or len(df) < 200:
            return None

        # KLUCZOWA POPRAWKA: Spłaszczamy dane, bo yfinance zwraca teraz MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Obliczamy wskaźniki na "czystych" danych
        close_prices = df["Close"].copy()
        
        df["SMA200"] = ta.sma(close_prices, length=200)
        df["RSI"] = ta.rsi(close_prices, length=14)
        
        macd_df = ta.macd(close_prices)
        
        if macd_df is None or macd_df.empty:
            return None

        # Przypisujemy wyniki MACD (używamy nazw kolumn generowanych przez pandas-ta)
        df["MACD"] = macd_df.iloc[:, 0]
        df["SIGNAL"] = macd_df.iloc[:, 2]

        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # Logika sygnałów
        price = float(curr["Close"])
        rsi = float(curr["RSI"])
        sma200 = float(curr["SMA200"])
        macd_val = float(curr["MACD"])
        sig_val = float(curr["SIGNAL"])
        prev_macd = float(prev["MACD"])
        prev_sig = float(prev["SIGNAL"])

        if (price > sma200 and macd_val > sig_val and prev_macd <= prev_sig and rsi > 40):
            return f"🟢 *KUPNO: {ticker}*\nCena: {price:.2f}\nRSI: {rsi:.1f}\nTrend: powyżej SMA200"

        if (price < sma200 and macd_val < sig_val and prev_macd >= prev_sig and rsi < 60):
            return f"🔴 *SPRZEDAŻ: {ticker}*\nCena: {price:.2f}\nRSI: {rsi:.1f}\nTrend: poniżej SMA200"

    except Exception as e:
        print(f"[{ticker}] Błąd: {e}")
        return None
    return None

def check_market(label: str):
    print(f"\n--- Skanowanie: {label} ---")
    signals = []
    for ticker in WATCHLIST:
        sig = analyze_ticker(ticker)
        if sig: signals.append(sig)

    msg = f"📊 *{label}*\n\n" + ("\n\n".join(signals) if signals else "Brak nowych sygnałów.")
    send_msg(msg)

if __name__ == "__main__":
    # Test na starcie
    check_market("RAPORT STARTOWY (TEST)")
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 08:30 PL = 06:30 UTC | 18:00 PL = 16:00 UTC
        if current_time == "06:30":
            check_market("RAPORT PORANNY")
            time.sleep(70)
        if current_time == "16:00":
            check_market("RAPORT WIECZORNY")
            time.sleep(70)
            
        time.sleep(30)
