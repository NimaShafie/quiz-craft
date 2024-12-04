#!/bin/sh
ollama serve &
sleep 5  # Give Ollama some time to start
ollama pull llama3
ollama run llama3:latest
