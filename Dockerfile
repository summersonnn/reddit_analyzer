FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nano \
    wget \
    curl \
    unzip \
    xvfb \
    libgl1-mesa-glx \
    libglib2.0-0 \
    fonts-liberation \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator1 \
    libasound2 \
    xdg-utils \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libxss1 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "frontend/home.py"]
