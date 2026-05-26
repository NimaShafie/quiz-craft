.PHONY: run run-hosted api mcp test lint typecheck security install install-dev clean help

help:
	@echo "QuizCraft — available make targets:"
	@echo "  run          Start the Streamlit UI (local mode)"
	@echo "  run-hosted   Start the Streamlit UI (hosted mode, rate limiting on)"
	@echo "  api          Start the FastAPI REST server on port 8000"
	@echo "  mcp          Start the MCP server"
	@echo "  test         Run all tests with coverage"
	@echo "  lint         Run ruff linter"
	@echo "  typecheck    Run mypy type checker"
	@echo "  security     Run bandit security scanner"
	@echo "  install      Install runtime dependencies"
	@echo "  install-dev  Install all dependencies including dev tools"
	@echo "  clean        Remove build artifacts and caches"

run:
	streamlit run src/quiz_craft.py

run-hosted:
	HOSTED_MODE=true streamlit run src/quiz_craft.py

api:
	uvicorn api:app --app-dir src --port 8000

mcp:
	python src/mcp_server.py

test:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/

typecheck:
	mypy src/ --ignore-missing-imports --no-strict-optional

security:
	bandit -r src/ -ll

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[all,dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info 2>/dev/null || true
