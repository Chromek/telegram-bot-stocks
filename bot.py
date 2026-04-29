import time
import datetime
import pytz
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

# 2. ROZSZERZONA LISTA SPÓŁEK
WATCHLIST = [
    # TWOJE NOWE WYBORY - POLSKA
    "KTY.WA", "CBF.WA", "TXT.WA", "GPW.WA", "IMS.WA", "SNT.WA", "ACP.WA",
    # TWOJE NOWE WYBORY - ZAGRANICA & KRYPTO
    "WDC", "TSM", "O", "BTC-USD", "ETH-USD",
    # GPW - POZOSTAŁE
    "PZU.WA", "PKO.WA", "PEO.WA", "LPP.WA", "BDX.WA", "PKN.WA", "XTB.WA", 
    "KGH.WA", "DNP.WA", "CDR.WA", "JSW.WA", "ALE.WA", "KRU.WA", "SPL.WA",
    # USA / ETF
    "NVDA", "MSFT", "AAPL", "AMD", "TSLA", "META", "GOOGL", "AMZN",
    "VOO", "QQQ", "GLD", "BITO"
]

session = requests.Session()

def send_msg(text: str):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        session.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e:
        print(f"[Błąd wysyłki] {e}")

def analyze_ticker(ticker: str):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 200: return None

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

        price = float(curr["Close"])
        prev_price = float(prev["Close"])
        rsi = float(curr["RSI"])
        sma200 = float(curr["SMA200"])
        macd_val = float(curr["MACD"])
        sig_val = float(curr["SIGNAL"])
        prev_macd = float(prev["MACD"])
        prev_sig = float(prev["SIGNAL"])

        # LOGIKA STATUSÓW
        if price > sma200 and macd_val > sig_val and prev_macd <= prev_sig and rsi > 40:
            return {"status": "KUPNO", "msg": f"🚀 *KUPNO: {ticker}*\nCena: {price:.2f} | RSI: {rsi:.1f}", "rsi": rsi}

        if price > sma200 and rsi < 45:
            return {"status": "AKUMULUJ", "msg": f"✨ *AKUMULUJ: {ticker}*\nCena: {price:.2f} | RSI: {rsi:.1f}", "rsi": rsi}

        if price > sma200 and price > prev_price:
            return {"status": "TRZYMAJ", "msg": f"💎 *TRZYMAJ: {ticker}*\nCena: {price:.2f}", "rsi": rsi}

        if price < sma200 and macd_val < sig_val and prev_macd >= prev_sig:
            return {"status": "SPRZEDAŻ", "msg": f"⚠️ *SPRZEDAŻ: {ticker}*\nCena: {price:.2f}", "rsi": rsi}

        return {"status": "BRAK", "rsi": rsi, "ticker": ticker}
    except:
        return None

def check_market(label: str):
    print(f"--- Skanowanie: {label} ---")
    results = []
    all_data = []
    for ticker in WATCHLIST:
        res = analyze_ticker(ticker)
        if res:
            all_data.append(res)
            if res["status"] != "BRAK": results.append(res["msg"])

    if not results and all_data:
        all_data.sort(key=lambda x: x["rsi"])
        best = all_data[0]
        results.append(f"🔍 *OKAZJA (Niskie RSI)*\nBrak sygnałów, ale {best.get('ticker')} ma RSI: {best['rsi']:.1f}")

    final_msg = f"📊 *{label}*\n\n" + "\n\n".join(results[:25]) # Limit 25 wiadomości, żeby Telegram nie zablokował
    send_msg(final_msg)

# --- PĘTLA GŁÓWNA ---
if __name__ == "__main__":
    tz_pl = pytz.timezone('Europe/Warsaw')
    last_run_date = None
    last_run_type = None

    print(f"Bot uruchomiony. Czas w PL: {datetime.datetime.now(tz_pl).strftime('%H:%M:%S')}")
    check_market("RAPORT STARTOWY")

    while True:
        now_pl = datetime.datetime.now(tz_pl)
        current_time = now_pl.strftime("%H:%M")
        today = now_pl.date()

        # Harmonogram raportów
        schedule = {
            "08:30": "morning",
            "13:00": "midday",
            "18:00": "evening"
        }

        if current_time in schedule:
            run_type = schedule[current_time]
            if last_run_date != today or last_run_type != run_type:
                labels = {
                    "morning": "RAPORT PORANNY (PRZED SESJĄ)",
                    "midday": "RAPORT ŚRÓDDZIENNY (W TRAKCIE)",
                    "evening": "RAPORT WIECZORNY (PO SESJI)"
                }
                check_market(labels[run_type])
                last_run_date = today
                last_run_type = run_type
                time.sleep(65)

        # Logi co 15 minut
        if now_pl.minute % 15 == 0 and now_pl.second < 30:
            print(f"Status OK. Godzina w PL: {current_time}")
            time.sleep(30)

        time.sleep(30)
