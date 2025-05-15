FROM python:3.13-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg ca-certificates \
    libnss3 libxss1 libasound2 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxi6 libxtst6 libglib2.0-0 libu2f-udev libvulkan1 libxrandr2 \
    libwayland-client0 libwayland-cursor0 libwayland-egl1 \
    fonts-liberation libappindicator3-1 xdg-utils xvfb \
    python3-tk python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
# https://www.ubuntuupdates.org/package/google_chrome/stable/main/base/google-chrome-stable
RUN wget http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_136.0.7103.113-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_136.0.7103.113-1_amd64.deb && \
    apt-mark hold google-chrome-stable && \
    rm -f /app/google-chrome-stable_136.0.7103.113-1_amd64.deb

# Install ChromeDriver
# https://googlechromelabs.github.io/chrome-for-testing/
RUN wget https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.113/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    chmod +x chromedriver-linux64/chromedriver && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/ && \
    rm -rf chromedriver-linux64 chromedriver-linux64.zip

# Set display
ENV DISPLAY=:99

# Set ChromeDriver version to prevent automatic downloads
ENV CHROMEDRIVER_VERSION=136.0.7103.113

# Disable automatic ChromeDriver downloads
ENV SB_NO_DRIVER_DOWNLOAD=1

# Set workdir
WORKDIR /app

# Update timezone
ENV TZ=Asia/Kuala_Lumpur

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the application
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & python src/main.py"]