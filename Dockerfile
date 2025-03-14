# Use a lightweight Python image
FROM python:3.12-slim

# Set non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive




# Use a lightweight Python base image
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

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
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O /tmp/chrome.deb && \
    apt-get update && apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb

# Install ChromeDriver (explicit version to match Chrome)
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/bin/ && \
    mv /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /usr/bin/chromedriver-linux64


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip setuptools wheel


# Copy your project files
COPY . .



# Expose port for Django
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
