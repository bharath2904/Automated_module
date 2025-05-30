FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy files into container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install --with-deps

# Expose the port
EXPOSE 5000

# Start the Flask app
CMD ["python", "main.py"]
