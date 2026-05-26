# QuizCraft Dockerfile
# Author: Nima Shafie

FROM python:3.12-slim

WORKDIR /app

# System deps (curl needed for HEALTHCHECK)
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app

# Create non-root user and set up Streamlit config directory
RUN addgroup --system quizcraft && adduser --system --ingroup quizcraft quizcraft \
    && mkdir -p /home/quizcraft/.streamlit \
    && chown -R quizcraft:quizcraft /app /home/quizcraft

COPY streamlit_config/config.toml /home/quizcraft/.streamlit/config.toml

# Drop privileges
USER quizcraft

# Streamlit default port
EXPOSE 8501
EXPOSE 8502

# Health check via Streamlit's built-in health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default: Version 1 (override with docker compose command)
CMD ["streamlit", "run", "src/quiz_craft.py", "--server.port=8501", "--server.address=0.0.0.0"]
