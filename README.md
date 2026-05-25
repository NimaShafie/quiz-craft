# QuizCraft

> AI-powered quiz generator — self-hosted with Ollama, built with Streamlit.

**Author:** Nima Shafie  
**Live:** [quizcraft.shafie.org](https://quizcraft.shafie.org)  
**License:** [CC BY-NC-ND 4.0](LICENSE)

---

## What It Does

QuizCraft generates custom quizzes from any topic or uploaded text file using a locally-running LLM via [Ollama](https://ollama.com). No API keys. No cloud dependency. Your data stays on your machine.

- **Input:** type a topic, paste text, or upload a `.txt` / `.pdf` file
- **Quick topics:** 8 clickable topic suggestions
- **Configure:** question types (Multiple Choice, True/False, Fill in the Blanks), difficulty (Easy / Medium / Hard), question count
- **Output:** download as `.pdf` or `.txt`, or take the quiz interactively in-browser with scoring

---

## Architecture

A single `quiz_craft.py` file powers both deployment modes via an environment variable:

```
HOSTED_MODE=false  →  Port 8501  (self-hosted, no limits, 40 questions max)
HOSTED_MODE=true   →  Port 8502  (public, rate limited, 20 questions max)
```

Public deployment uses a Cloudflare Tunnel — no port forwarding required.

```
Internet → Cloudflare → cloudflared tunnel → nginx → Streamlit (port 8502)
```

QuizCraft talks to Ollama over HTTP. By default Ollama runs on the same machine as the app, but it can also run on a separate server — see [Remote Ollama Setup](#setup--option-c-remote-ollama-server).

---

## Models

QuizCraft uses [Ollama](https://ollama.com) to run LLMs locally. You choose the model — Ollama downloads and manages it for you.

### Recommended: `qwen3:4b`

```bash
ollama pull qwen3:4b
```

### Model Comparison

| Model | RAM needed | Notes |
|---|---|---|
| `qwen3:4b` | ~3 GB | **Recommended** — fast, strong JSON output |
| `gemma3:4b` | ~3.3 GB | Good alternative, solid reasoning |
| `gemma3:12b` | ~8 GB | Higher quality, needs more RAM |
| `qwen2.5:7b` | ~5 GB | Strong instruction following |
| `llama3.1:8b` | ~6 GB | Well-rounded, reliable |
| `llama3.2:3b` | ~2 GB | Lightest option, lower quality |

> **CPU inference:** Expect 15–60 seconds per generation without a GPU. This is normal for 4B parameter models on CPU. Use a smaller model (`llama3.2:3b`) if speed is more important than quality.

> **GPU acceleration:** If you have an NVIDIA GPU, Ollama uses it automatically after installing the [CUDA toolkit](https://developer.nvidia.com/cuda-downloads). Generation drops to 3–8 seconds.

### Pulling a different model

Any model on [ollama.com/library](https://ollama.com/library) works. Pull it, then update `config.ini`:

```bash
ollama pull gemma3:12b
```

```ini
# config.ini
[OLLAMA_DETAILS]
model_name = gemma3:12b
```

---

## Setup — Option A: Same Machine (Recommended)

Run Ollama and QuizCraft on the same computer. This is the simplest setup.

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.com/download)

```bash
# 1. Clone the repo
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh
# Windows/macOS: download the installer from https://ollama.com/download

# 5. Pull a model
ollama pull qwen3:4b

# 6. Start the app
streamlit run src/quiz_craft.py
```

Open **http://localhost:8501**

The app auto-detects Ollama at `http://localhost:11434`. No configuration needed.

---

## Setup — Option B: Docker Compose

Runs Ollama and QuizCraft together in containers. No Python or Ollama install required on the host.

```bash
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

# Self-hosted (port 8501)
docker compose --profile dev up --build -d

# Both versions: self-hosted (8501) + public/rate-limited (8502)
docker compose --profile hosted up --build -d
```

The `ollama_pull` container automatically pulls `qwen3:4b` on first start. If you want a different model, edit `docker-compose.yml` before building:

```yaml
# docker-compose.yml — quizcraft_v1 and quizcraft_v2
environment:
  - OLLAMA_MODEL=gemma3:12b   # change to your preferred model
```

And update the pull step:

```yaml
# ollama_pull service
echo 'Pulling gemma3:12b ...';
curl -X POST http://ollama:11434/api/pull -d '{"name":"gemma3:12b"}';
```

---

## Setup — Option C: Remote Ollama Server

Run Ollama on a separate machine (e.g. a home server, NAS, or a VM with a GPU) and point QuizCraft at it over the network. The app machine only runs Streamlit.

### On the Ollama server

**1. Install Ollama and bind it to the network interface:**

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Bind to all interfaces so other machines can reach it
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

To make this permanent with systemd:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Then:

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

**2. Pull a model on the server:**

```bash
ollama pull qwen3:4b
```

**3. Verify it is reachable from the network:**

```bash
# Run this from another machine, replacing <server-ip> with your server's IP
curl http://<server-ip>:11434/api/tags
# Should return JSON listing available models
```

### On the QuizCraft machine

Edit `config.ini` to point at the remote server:

```ini
[OLLAMA_DETAILS]
ollama_host = http://<server-ip>:11434
model_name  = qwen3:4b
```

Or set environment variables instead (overrides config.ini):

```bash
export OLLAMA_HOST=http://<server-ip>:11434
export OLLAMA_MODEL=qwen3:4b
streamlit run src/quiz_craft.py
```

The QuizCraft machine does not need Ollama installed at all.

---

## Configuration

### `config.ini`

Fallback values used when environment variables are not set. Safe to edit for local/bare-metal installs.

```ini
[OLLAMA_DETAILS]
model_name  = qwen3:4b
ollama_host = http://localhost:11434
```

### Environment Variables

Environment variables take priority over `config.ini`. Use these for Docker or remote setups.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `qwen3:4b` | Model name (must be pulled on the Ollama server) |
| `HOSTED_MODE` | `false` | `true` enables rate limiting and stricter input caps |

---

## Project Structure

```
quiz-craft/
├── src/
│   ├── quiz_craft.py                 # Main Streamlit app (both modes)
│   └── generate_quiz_from_prompt.py  # LLM quiz generation logic
├── deployment/
│   ├── nginx.conf.example            # nginx reverse proxy config template
│   └── cloudflared.conf.example      # Cloudflare tunnel config template
├── images/logo/
│   └── quiz-craft-logo.png
├── tests/
│   └── test_quiz_craft.py            # Offline unit tests (39 checks)
├── docs/                             # Project documentation
├── config.ini                        # Model + host config (fallback values)
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Container build
└── docker-compose.yml                # Orchestration
```

---

## Security (Hosted Mode)

- **Rate limiting:** 5 quizzes/hour per IP, 15s cooldown between requests
- **Prompt injection protection:** 20+ abuse patterns stripped before LLM call
- **Input caps:** 2000 character prompt limit, minimum 2 words required
- **Ollama port** (11434) is internal to Docker network — not exposed publicly
- **Cloudflare Tunnel** — no open ports on the host machine

---

## Troubleshooting

**"Cannot reach Ollama at http://localhost:11434"**

Ollama is not running. Start it:
```bash
ollama serve
```
Then verify:
```bash
curl http://localhost:11434/api/tags
```

**"Model `qwen3:4b` not pulled"**

The model hasn't been downloaded yet:
```bash
ollama pull qwen3:4b
```
Check what is currently available:
```bash
ollama list
```

**"Ollama error: model 'X' not found"**

The model name in `config.ini` or `OLLAMA_MODEL` does not match what is pulled on the server. Run `ollama list` on the Ollama machine and update the name to match exactly.

**Remote server not reachable**

1. Confirm Ollama is bound to `0.0.0.0`, not `127.0.0.1` — see [Remote Ollama Setup](#setup--option-c-remote-ollama-server)
2. Check your firewall allows inbound TCP on port 11434
3. Test from the QuizCraft machine: `curl http://<server-ip>:11434/api/tags`

**"Quiz generation timed out"**

Generation took more than 180 seconds. Try:
- Reducing the question count
- Using a smaller model (`qwen3:4b` over `gemma3:12b`)
- Running Ollama on a machine with a GPU

**Docker: containers not starting**
```bash
docker compose ps
docker compose logs quizcraft_v1 --tail=50
docker compose logs ollama --tail=30
```

---

## License

[CC BY-NC-ND 4.0](LICENSE)
