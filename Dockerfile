FROM python:3.12-slim

# Instalacja niezbędnych narzędzi systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Aktualizacja pip
RUN pip install --upgrade pip

# Czysta instalacja wszystkich potrzebnych bibliotek
RUN pip install pandas requests yfinance pandas-ta python-dotenv pytz


# Kopiujemy resztę plików (Twój skrypt)
COPY . .

CMD ["python", "bot.py"]
