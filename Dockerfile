FROM python:3.11

RUN apt-get update && apt-get install -y build-essential gcc

WORKDIR /app

# Aktualizacja instalatora pip
RUN pip install --upgrade pip

COPY requirements.txt .

# Instalacja z dodatkowym parametrem, żeby widzieć błędy w logach
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
