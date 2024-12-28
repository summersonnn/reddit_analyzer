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

# Install Google Chrome and ChromeDriver
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    CHROME_VERSION=$(google-chrome-stable --version | cut -d " " -f3) && \
    wget -q https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip -P /tmp/ && \
    unzip /tmp/chromedriver-linux64.zip -d /usr/local/bin/ && \
    rm -f /tmp/chromedriver-linux64.zip && \
    chmod +x /usr/local/bin/chromedriver-linux64/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "frontend/home.py"]
