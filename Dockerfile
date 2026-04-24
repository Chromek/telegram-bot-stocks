FROM python:3.11-slim

# Instalacja niezbędnych narzędzi systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Najpierw instalujemy podstawowe zależności
RUN pip install --upgrade pip
RUN pip install pandas requests yfinance

# INSTALACJA PANDAS-TA BEZPOŚREDNIO Z REPOZYTORIUM (Omija błąd wersji)
RUN pip install git+https://github.com/twopirllc/pandas-ta.git@development

# Kopiujemy resztę plików
COPY . .

CMD ["python", "bot.py"]
