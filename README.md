# QuizCraft 🧠📚❓
> AI-powered quiz generator — powered by Ollama, built with Streamlit.

**Author:** Nima Shafie  
**License:** See [LICENSE](LICENSE)

---

## What It Does

QuizCraft generates custom quizzes from any topic or uploaded text file using a locally-running LLM via [Ollama](https://ollama.com). No API keys. No cloud. Your data stays on your machine.

- **Input:** type a topic, paste text, or upload a `.txt` / `.pdf` file
- **Configure:** question types (Multiple Choice, True/False, Fill in the Blanks), difficulty (Easy / Medium / Hard), and question count
- **Output:** download the quiz as `.pdf` or `.txt`

---

## Two Versions

| | Version 1 — Self-Hosted | Version 2 — Hosted |
|---|---|---|
| **Who** | You / your team | Anyone (public URL) |
| **Rate limit** | None | 5 quizzes/hour per IP |
| **Question cap** | 40 | 20 |
| **Security** | Basic input sanitization | Full abuse + injection protection |
| **Entry point** | `src/QuizCraft.py` | `src/QuizCraft_hosted.py` |
| **Port** | 8501 | 8502 |

---

## Recommended Model

**`gemma3:4b`** — Google Gemma 3, 4 billion parameter model. Fast, high quality, ~3GB RAM.

```bash
ollama pull gemma3:4b
```

Other good options from the Ollama library:

| Model | Size | Notes |
|---|---|---|
| `gemma3:4b` | ~3GB | ✅ Recommended — fast, accurate JSON output |
| `qwen3.5:4b` | ~3GB | Good multilingual support |
| `llama3.2:3b` | ~2GB | Lighter option for low-RAM machines |
| `gemma3:12b` | ~8GB | Higher quality, needs more VRAM |
| `qwen3.5:14b` | ~9GB | Best quality, needs 16GB+ RAM |

Change the model in `config.ini`:
```ini
[OLLAMA_DETAILS]
model_name = gemma3:4b
```

---

## Host OS Recommendation

**Recommended: Ubuntu 24.04 LTS**

Ubuntu 24.04 LTS is the ideal choice for hosting QuizCraft on a Linux VM because:
- Ollama's official install script targets Ubuntu/Debian first — best package compatibility
- Docker Engine and Docker Compose have first-class Ubuntu support
- `apt` ecosystem makes dependency management straightforward
- Long-term support through 2029 — no forced OS upgrades mid-deployment
- Largest community knowledge base for troubleshooting

> If your VM is already running **RHEL 8** (your airgap-cpp-devkit host), that works too — just use `dnf` instead of `apt` and note RHEL 8's GLIBC 2.28 may cause issues with some Ollama versions. RHEL 8 is fully supported for Docker-based deployment.

---

## Setup — Version 1 (Self-Hosted)

### Option A: Run Directly (no Docker)

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.com)

```bash
# 1. Clone the repo
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Install dependencies (~30MB — much lighter than the original)
pip install -r requirements.txt

# 4. Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &                  # Start in background (or run in a separate terminal)

# 5. Pull the model (one-time, ~3GB download)
ollama pull gemma3:4b

# 6. Run QuizCraft
streamlit run src/QuizCraft.py
```

Then open **http://localhost:8501** in your browser.

### Option B: Docker Compose

```bash
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

# Builds the app container, starts Ollama, and pulls gemma3:4b automatically
docker compose up --build
```

Open **http://localhost:8501**

---

## Setup — Version 2 (Hosted on Linux VM)

This runs both versions simultaneously. V2 adds rate limiting and stricter input validation.

### Step 1: Install Docker on Ubuntu 24.04

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group (no sudo needed going forward)
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone and Start

```bash
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

# Start BOTH versions (V1 on :8501, V2 on :8502)
docker compose --profile hosted up --build -d
```

### Step 3: nginx Reverse Proxy (recommended)

Expose V2 to the public behind nginx with HTTPS. Install nginx:

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/quizcraft`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:8502;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;

        # Prevent timeout during LLM generation
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/quizcraft /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Add HTTPS with Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

### Step 4: Open Firewall Ports

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Persistent Service (auto-restart on reboot)

The Docker Compose `restart: unless-stopped` policy handles this. To verify:

```bash
docker compose ps
```

---

## Configuration

### `config.ini`

```ini
[OLLAMA_DETAILS]
model_name     = gemma3:4b
ollama_host    = http://localhost:11434   # or http://ollama:11434 in Docker
device         = cpu
data_directory = ./data
```

### Environment Variables (override config.ini)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `gemma3:4b` | Model name |

### Rate Limit Tuning (Hosted Version)

Edit `src/rate_limiter.py`:

```python
RATE_LIMIT_REQUESTS   = 5    # quizzes allowed per hour per IP
RATE_LIMIT_WINDOW_SEC = 3600 # rolling window in seconds
MAX_QUESTIONS_HOSTED  = 20   # max questions per quiz
COOLDOWN_SEC          = 15   # minimum seconds between requests
```

---

## Project Structure

```
quiz-craft/
├── src/
│   ├── QuizCraft.py               # Version 1: self-hosted UI
│   ├── QuizCraft_hosted.py        # Version 2: hosted UI with rate limiting
│   ├── generate_quiz_from_prompt.py  # Core LLM quiz generation (fixed)
│   ├── generate_quiz_on_file.py   # File-based quiz (legacy, advanced use)
│   ├── rate_limiter.py            # Rate limiting + abuse prevention (V2)
│   └── config_reader.py           # Config file + env var reader
├── images/logo/
│   └── quiz-craft-logo.png
├── data/                          # Drop PDF files here for file-mode
├── docs/                          # Project documentation
├── tests/                         # Test cases
├── config.ini                     # Model + Ollama configuration
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container build
├── docker-compose.yml             # Orchestration (V1 + V2)
└── README.md
```

---

## What Was Fixed

| Issue | Fix |
|---|---|
| **Difficulty did nothing** | Each difficulty now uses a distinct temperature + detailed prompt instructions describing how hard questions should be |
| **Same questions every time** | Removed hardcoded low temperature; added explicit "do not repeat" instruction |
| **Prompt injection risk** | `sanitize_prompt()` strips known injection phrases before sending to LLM |
| **Broken subprocess stdout** | Generation script now outputs ONLY JSON to stdout; all debug logging goes to stderr |
| **llama-index bloat (~4GB install)** | Replaced with direct Ollama HTTP API calls (`requests`) — `requirements.txt` is now ~30MB |
| **JSON parse failures** | Robust `extract_quiz_json()` with fallback regex, markdown fence stripping, and `json_mode=True` in API call |
| **Type normalization** | Answer types like `"mcq"`, `"true or false"`, `"fill-in-the-blank"` are all mapped to canonical values |
| **True/False answer bug** | Bool and string answer values both normalized correctly |
| **Fill in Blanks missing `___`** | Auto-appended if model forgets the blank marker |
| **No rate limiting (hosted)** | Per-IP rolling window with cooldown, quota display in UI |
| **No input validation (hosted)** | Abuse pattern detection, length caps, minimum word count |

---

## Security Notes (Hosted Deployment)

- **Rate limiting** is in-process (resets on server restart). For multi-process or multi-container deployments, swap `_ip_store` in `rate_limiter.py` for Redis.
- **Input sanitization** blocks common prompt injection phrases. It is not foolproof — treat the LLM as untrusted for output.
- **nginx** handles TLS termination and forwards `X-Forwarded-For` so the app can rate-limit by real client IP, not the proxy IP.
- The Ollama port (11434) is **not** exposed in the hosted docker-compose — it's internal to the Docker network only.
- For additional hardening, consider adding HTTP Basic Auth to the nginx config during a soft launch.

---

## Troubleshooting

**"Cannot connect to Ollama"**
```bash
# Check Ollama is running
ollama list
# If not, start it
ollama serve
```

**"Model not found"**
```bash
ollama pull gemma3:4b
```

**"Quiz generation timed out"**  
Try a smaller model (`llama3.2:3b`) or reduce the question count.

**Docker: Ollama container exits immediately**  
Run `docker compose logs ollama` — it may need the GPU runtime. For CPU-only, the default config works but is slower.

---

## License

See [LICENSE](LICENSE) for terms.
