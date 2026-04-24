import time
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

# 1. ŁADOWANIE KONFIGURACJI
load_dotenv()

# PRZYPISANIE - To musi być przed printami!
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# DEBUG - Sprawdzamy czy Railway widzi zmienne
print(f"--- DIAGNOSTYKA STARTU ---")
print(f"DEBUG: Czy TOKEN został wczytany? {'TAK' if TOKEN else 'NIE'}")
print(f"DEBUG: Czy CHAT_ID został wczytany? {'TAK' if CHAT_ID else 'NIE'}")
if CHAT_ID:
    print(f"DEBUG: CHAT_ID zaczyna się od: {str(CHAT_ID)[:3]}...")
print(f"--------------------------")

WATCHLIST = [
    "PZU.WA", "PKO.WA", "PEO.WA", "LPP.WA", "BDX.WA", "PKN.WA", "XTB.WA",
    "NVDA", "MSFT", "AAPL", "UNH", "COST", "QCOM", "VOO"
]

session = requests.Session()

def send_msg(text: str):
    if not TOKEN or not CHAT_ID:
        print("[Błąd] Brak TOKENA lub CHAT_ID w zmiennych środowiskowych!")
        return
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = session.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"[Błąd Telegrama] Status: {response.status_code}, Treść: {response.text}")
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

    # Obliczanie wskaźników
    df["SMA200"] = ta.sma(df["Close"], length=200)
    df["RSI"] = ta.rsi(df["Close"], length=14)
    
    macd = ta.macd(df["Close"])
    # Zabezpieczenie przed różnymi nazwami kolumn w MACD
    df["MACD"] = macd.iloc[:, 0]
    df["SIGNAL"] = macd.iloc[:, 2]

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(curr["Close"])
    rsi = float(curr["RSI"])
    sma200 = float(curr["SMA200"])
    macd_line = float(curr["MACD"])
    signal_line = float(curr["SIGNAL"])
    prev_macd = float(prev["MACD"])
    prev_signal = float(prev["SIGNAL"])

    # LOGIKA KUPNA
    if (price > sma200 and 
        macd_line > signal_line and prev_macd <= prev_signal and 
        rsi > 40):
        return (f"🟢 *KUPNO: {ticker}*\n"
                f"Cena: {price:.2f}\n"
                f"RSI: {rsi:.1f}\n"
                f"Trend: powyżej SMA200")

    # LOGIKA SPRZEDAŻY
    if (price < sma200 and 
        macd_line < signal_line and prev_macd >= prev_signal and 
        rsi < 60):
        return (f"🔴 *SPRZEDAŻ: {ticker}*\n"
                f"Cena: {price:.2f}\n"
                f"RSI: {rsi:.1f}\n"
                f"Trend: poniżej SMA200")

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
        msg = f"✅ *{label}*\nBrak nowych sygnałów technicznych."

    send_msg(msg)

# --- PĘTLA GŁÓWNA ---
if __name__ == "__main__":
    last_run = {"morning": None, "evening": None}
    
    # TEST NATYCHMIASTOWY - Wyśle raport od razu po starcie bota na Railway
    print("Uruchamiam raport testowy...")
    check_market("RAPORT STARTOWY (TEST)")

    print("Bot jest aktywny i czeka na godziny raportów (UTC)...")

    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Raport poranny (08:30 czasu polskiego = 06:30 UTC)
        if current_time == "06:30" and last_run["morning"] != now.date():
            check_market("RAPORT PORANNY")
            last_run["morning"] = now.date()

        # Raport wieczorny (18:00 czasu polskiego = 16:00 UTC)
        if current_time == "16:00" and last_run["evening"] != now.date():
            check_market("RAPORT WIECZORNY")
            last_run["evening"] = now.date()

        # Co 30 sekund wypisz czas do logów, żeby wiedzieć, że bot żyje
        if now.second % 30 == 0:
            print(f"Czuwam... Czas serwera: {current_time}")
            
        time.sleep(1)
