# QuizCraft Dockerfile
# Author: Nima Shafie

FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app

# Streamlit default port
EXPOSE 8501
EXPOSE 8502

# Default: Version 1 (override with docker compose command)
CMD ["streamlit", "run", "src/QuizCraft.py", "--server.port=8501", "--server.address=0.0.0.0"]
