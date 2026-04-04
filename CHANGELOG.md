# Changelog

## [Unreleased]

## [1.0.0] - 2026-04-04
### Added
- Initial public release
- AI quiz generation via local Ollama model (gemma3:4b recommended)
- Multiple Choice, True/False, and Fill in the Blanks question types
- Easy / Medium / Hard difficulty with tuned temperature profiles
- Interactive in-browser quiz mode with scoring
- PDF and TXT download
- Hosted mode with rate limiting (5 quizzes/hour, 15s cooldown)
- Prompt injection protection (20+ abuse patterns)
- Docker Compose setup with self-hosted and hosted profiles
- Cloudflare Tunnel deployment (no open ports)
- 32-test offline unit test suite

### Security
- Gitignored personal deployment configs — added `.example` templates
- Logs directory excluded from version control
