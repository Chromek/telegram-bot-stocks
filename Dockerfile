FROM python:3.11-slim

# Instalacja niezbędnych narzędzi systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Najpierw instalujemy podstawowe zależności
RUN pip install --upgrade pip
RUN pip install pandas requests yfinance

# INSTALACJA PANDAS-TA Z POPRAWNEGO LINKU (master)
RUN pip install https://github.com/twopirllc/pandas-ta/archive/master.zip

# Kopiujemy resztę plików
COPY . .

CMD ["python", "bot.py"]
