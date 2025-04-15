FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg ca-certificates \
    libnss3 libxss1 libasound2 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxi6 libxtst6 libglib2.0-0 libu2f-udev libvulkan1 libxrandr2 \
    libwayland-client0 libwayland-cursor0 libwayland-egl1 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
# https://www.ubuntuupdates.org/package/google_chrome/stable/main/base/google-chrome-stable
RUN wget http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_135.0.7049.84-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_135.0.7049.84-1_amd64.deb && \
    apt-mark hold google-chrome-stable && \
    rm -f /app/google-chrome-stable_135.0.7049.84-1_amd64.deb

# Install ChromeDriver
# https://googlechromelabs.github.io/chrome-for-testing/
RUN CHROME_DRIVER_VERSION="135.0.7049.84" && \
    wget https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.84/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/chromedriver-linux64/chromedriver && \
    rm -f /app/chromedriver_linux64.zip

# Set display (not really needed in headless, but some libs expect it)
ENV DISPLAY=:99

# Set workdir
WORKDIR /app

# Update timezone
ENV TZ=Asia/Kuala_Lumpur

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY src/ ./src

# Create logs folder
RUN mkdir -p /app/logs

CMD ["python", "src/scraper.py"]