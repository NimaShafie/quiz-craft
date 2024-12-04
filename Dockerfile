# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy all necessary files and folders into the container
COPY . /app

# Copy start_ollama.sh into the container (Ensure it's included)
COPY start_ollama.sh /app/start_ollama.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies for downloading and installing Ollama CLI
RUN apt-get update && apt-get install -y \
    curl \
    tar \
    libstdc++6 \
    procps \
    && apt-get clean

# Ensure required files are available in the correct paths
RUN test -f /app/response.json || echo "{}" > /app/response.json

# Expose the Streamlit default port
EXPOSE 8501

# Make the start_ollama.sh script executable
RUN chmod +x /app/start_ollama.sh

# Start Streamlit after Ollama is ready
CMD ["streamlit", "run", "src/QuizCraft.py"]
