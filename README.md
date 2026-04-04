# QuizCraft

> AI-powered quiz generator — self-hosted with Ollama, built with Streamlit.

**Author:** Nima Shafie  
**Live:** [quizcraft.shafie.org](https://quizcraft.shafie.org)  
**License:** [CC BY-NC-ND 4.0](LICENSE) — free for personal/academic use, not for commercial use

---

## What It Does

QuizCraft generates custom quizzes from any topic or uploaded text file using a locally-running LLM via [Ollama](https://ollama.com). No API keys. No cloud dependency. Your data stays on your machine.

- **Input:** type a topic, paste text, or upload a `.txt` / `.pdf` file
- **Quick topics:** 8 clickable topic suggestions
- **Configure:** question types (Multiple Choice, True/False, Fill in the Blanks), difficulty (Easy / Medium / Hard), question count
- **Output:** download as `.pdf` or `.txt`, or take the quiz interactively in-browser with scoring

---

## Architecture

A single `QuizCraft.py` file powers both deployment modes via an environment variable:

```
HOSTED_MODE=false  →  Port 8501  (self-hosted, no limits, 40 questions max)
HOSTED_MODE=true   →  Port 8502  (public, rate limited, 20 questions max)
```

Public deployment uses a Cloudflare Tunnel — no port forwarding required.

```
Internet → Cloudflare → cloudflared tunnel → nginx → Streamlit (port 8502)
```

---

## Recommended Model

**`gemma3:4b`** — Google Gemma 3, 4B parameters, Q4_K_M quantization. ~3.3GB RAM, solid JSON output quality.

```bash
ollama pull gemma3:4b
```

| Model | RAM | Notes |
|---|---|---|
| `gemma3:4b` | ~3.3GB | Recommended |
| `gemma3:12b` | ~8GB | Higher quality, needs more RAM |
| `llama3.2:3b` | ~2GB | Lighter, lower quality |

> **Note:** CPU-only inference takes 15–30 seconds per generation. This is expected for 4B parameter models without GPU acceleration.

---

## Setup — Self-Hosted (no Docker)

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.com)

```bash
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:4b
ollama serve &

streamlit run src/QuizCraft.py
```

Open **http://localhost:8501**

---

## Setup — Docker Compose

```bash
git clone https://github.com/NimaShafie/quiz-craft.git
cd quiz-craft

# Self-hosted only (port 8501)
docker compose up --build

# Both versions (8501 + 8502 with rate limiting)
docker compose --profile hosted up --build -d
```

---

## Configuration

### `config.ini`

```ini
[OLLAMA_DETAILS]
model_name  = gemma3:4b
ollama_host = http://localhost:11434
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `gemma3:4b` | Model name |
| `HOSTED_MODE` | `false` | Enable rate limiting + stricter caps |

---

## Project Structure

```
quiz-craft/
├── src/
│   ├── QuizCraft.py                  # Main app (single file, both modes)
│   ├── generate_quiz_from_prompt.py  # LLM quiz generation logic
│   ├── generate_quiz_on_file.py      # File-based generation (advanced)
│   └── config_reader.py              # Config + env var reader
├── deployment/
│   ├── nginx.conf                    # nginx reverse proxy config
│   └── cloudflared.conf              # Cloudflare tunnel config
├── images/logo/
│   └── quiz-craft-logo.png
├── tests/
│   └── test_quizcraft.py             # Offline unit tests (32 checks)
├── docs/                             # Project documentation
├── config.ini                        # Model + Ollama config
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

**"Cannot connect to Ollama"**
```bash
ollama list
ollama serve
```

**"Quiz generation timed out"**
Reduce question count. CPU inference takes 15–30 seconds for 3 questions.

**Docker: containers not starting**
```bash
docker compose ps
docker compose logs quizcraft_v1 --tail=30
```

---

## License

[CC BY-NC-ND 4.0](LICENSE) — free for personal and academic use.  
Commercial use is not permitted. Attribution required.