import time
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

# 1. KONFIGURACJA I ZMIENNE
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# LISTA SPÓŁEK (Możesz tu dopisywać własne)
WATCHLIST = [
    # GPW (Polska)
    "PZU.WA", "PKO.WA", "PEO.WA", "LPP.WA", "BDX.WA", "PKN.WA", "XTB.WA", 
    "KGH.WA", "DNP.WA", "CDR.WA", "JSW.WA", "ALE.WA", "KRU.WA",
    # USA / ETF
    "NVDA", "MSFT", "AAPL", "AMD", "TSLA", "META", "GOOGL", "AMZN",
    "VOO", "QQQ", "GLD", "BITO"
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
        # Pobieranie danych z auto-naprawą formatu
        df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 200: return None

        # Naprawa formatu danych Yahoo Finance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close_prices = df["Close"].copy()
        df["SMA200"] = ta.sma(close_prices, length=200)
        df["RSI"] = ta.rsi(close_prices, length=14)
        macd_df = ta.macd(close_prices)
        
        if macd_df is None or macd_df.empty: return None
        df["MACD"] = macd_df.iloc[:, 0]
        df["SIGNAL"] = macd_df.iloc[:, 2]

        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # Wartości do analizy
        price = float(curr["Close"])
        prev_price = float(prev["Close"])
        rsi = float(curr["RSI"])
        sma200 = float(curr["SMA200"])
        macd_val = float(curr["MACD"])
        sig_val = float(curr["SIGNAL"])
        prev_macd = float(prev["MACD"])
        prev_sig = float(prev["SIGNAL"])

        # --- LOGIKA DECYZYJNA ---
        
        # 🟢 SILNE KUPNO (Przecięcie MACD nad SMA200)
        if price > sma200 and macd_val > sig_val and prev_macd <= prev_sig and rsi > 40:
            return {"status": "KUPNO", "msg": f"🚀 *KUPNO: {ticker}*\nCena: {price:.2f} | RSI: {rsi:.1f} (Przecięcie MACD)", "rsi": rsi}

        # 🟡 AKUMULUJ (W trendzie wzrostowym, ale cena lekko spadła / RSI niskie)
        if price > sma200 and rsi < 45:
            return {"status": "AKUMULUJ", "msg": f"✨ *AKUMULUJ: {ticker}*\nCena: {price:.2f} | RSI: {rsi:.1f} (Korekta w trendzie)", "rsi": rsi}

        # 🔵 TRZYMAJ (Trend wzrostowy, cena powyżej wczorajszej)
        if price > sma200 and price > prev_price:
            return {"status": "TRZYMAJ", "msg": f"💎 *TRZYMAJ: {ticker}*\nCena: {price:.2f} (Stabilny wzrost)", "rsi": rsi}

        # 🔴 SPRZEDAŻ (Przecięcie MACD w dół poniżej SMA200)
        if price < sma200 and macd_val < sig_val and prev_macd >= prev_sig:
            return {"status": "SPRZEDAŻ", "msg": f"⚠️ *SPRZEDAŻ: {ticker}*\nCena: {price:.2f} (Sygnał wyjścia!)", "rsi": rsi}

        # Jeśli brak sygnału, zwróć tylko RSI (do statystyk)
        return {"status": "BRAK", "rsi": rsi, "ticker": ticker}

    except Exception as e:
        print(f"[{ticker}] Błąd: {e}")
        return None

def check_market(label: str):
    print(f"\n--- Skanowanie: {label} ---")
    results = []
    all_data = []

    for ticker in WATCHLIST:
        res = analyze_ticker(ticker)
        if res:
            all_data.append(res)
            if res["status"] != "BRAK":
                results.append(res["msg"])

    # Jeśli nie ma żadnych sygnałów KUP/SPRZEDAJ/TRZYMAJ, wybierz spółkę z najniższym RSI
    if not results and all_data:
        # Sortujemy po RSI rosnąco
        all_data.sort(key=lambda x: x["rsi"])
        best_candidate = all_data[0]
        results.append(f"🔍 *OKAZJA DO OBSERWACJI*\nObecnie brak sygnałów, ale {best_candidate.get('ticker', 'spółka')} ma najniższe RSI: {best_candidate['rsi']:.1f} (możliwe wyprzedanie).")

    final_msg = f"📊 *{label}*\n\n" + "\n\n".join(results)
    send_msg(final_msg)

if __name__ == "__main__":
    print("Bot uruchomiony. Wysyłam raport startowy...")
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
