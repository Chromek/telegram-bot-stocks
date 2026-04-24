FROM python:3.11-slim

# Instalacja narzędzi (bez gita, żeby było lżej i bez błędów)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Aktualizacja pip i instalacja bazy
RUN pip install --upgrade pip
RUN pip install pandas requests yfinance

# INSTALACJA PANDAS-TA Z PLIKU ZIP (Omija błędy Git'a)
RUN pip install https://github.com/twopirllc/pandas-ta/archive/refs/heads/main.zip

# Kopiujemy resztę plików (Twój skrypt)
COPY . .

CMD ["python", "bot.py"]
