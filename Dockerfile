# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies for downloading and installing Ollama CLI
RUN apt-get update && apt-get install -y \
    curl \
    tar \
    libstdc++6 \
    && apt-get clean

# Define Ollama CLI URL as an environment variable
ENV OLLAMA_CLI_URL=https://ollama.com/install.sh

# Install Ollama CLI with debugging output
RUN curl -sSfL $OLLAMA_CLI_URL -o /tmp/ollama_installer.sh && \
    chmod +x /tmp/ollama_installer.sh && \
    sh /tmp/ollama_installer.sh

# Verify Ollama CLI installation
RUN ollama serve & \
    sleep 5 && \
    ollama --version && \
    ollama stop

# Pre-download the Llama3 model
RUN ollama pull llama3

# Copy the application code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose application and Ollama ports
EXPOSE 80
EXPOSE 11434

# Define environment variable
ENV NAME=World

# Run app.py when the container launches
CMD ["python", "app.py"]
