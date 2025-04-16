# Use a multi-architecture Python base image
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    libnss3 \
    libasound2 \
    fonts-liberation \
    libgbm-dev \
    libx11-xcb1 \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver for both architectures
RUN set -ex; \
    ARCH=$(uname -m); \
    if [ "$ARCH" = "x86_64" ]; then \
    CHROME_URL="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"; \
    CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip"; \
    elif [ "$ARCH" = "aarch64" ]; then \
    CHROME_URL="https://dl.google.com/linux/direct/google-chrome-stable_current_arm64_deb.deb"; \
    CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip"; \
    else \
    echo "Unsupported architecture: $ARCH" && exit 1; \
    fi; \
    \
    wget -q "$CHROME_URL" -O /tmp/chrome.deb && \
    apt-get update && apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb; \
    \
    wget -q "$CHROMEDRIVER_URL" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/bin/ && \
    mv /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /usr/bin/chromedriver-linux64

# Copy and install Python dependencies first (cache optimization)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project files
COPY . .

# Expose port for Django
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]