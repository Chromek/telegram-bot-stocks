# Używamy nowszej i pełniejszej wersji Pythona
FROM python:3.11

# Instalujemy narzędzia niezbędne do budowania pakietów (często wymagane przez TA-Lib/Pandas)
RUN apt-get update && apt-get install -y build-essential gcc

WORKDIR /app

# Najpierw kopiujemy requirements
COPY requirements.txt .

# Instalujemy pakiety
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę plików (twój bot.py)
COPY . .

# Komenda startowa
CMD ["python", "bot.py"]
