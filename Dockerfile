# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy all necessary files and folders into the container
COPY . /app

# Install dependencies for downloading and installing Ollama CLI
RUN apt-get update && apt-get install -y \
    curl \
    tar \
    libstdc++6 \
    procps \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Streamlit and Ollama default ports
EXPOSE 8501

# Start Streamlit after Ollama is ready
CMD ["streamlit", "run", "src/QuizCraft.py"]
