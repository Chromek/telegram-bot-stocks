FROM python:3.11-slim

# Instalacja niezbędnych narzędzi systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiujemy wszystko od razu
COPY . .

# Instalujemy pip i biblioteki pojedynczo, aby widzieć, gdzie dokładnie jest błąd
# Używamy --no-deps dla yfinance, jeśli standardowa instalacja zawiedzie, 
# ale najpierw spróbujemy tej metody:
RUN pip install --upgrade pip
RUN pip install pandas requests
RUN pip install yfinance --upgrade --no-cache-dir
RUN pip install pandas-ta

CMD ["python", "bot.py"]
