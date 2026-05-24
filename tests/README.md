# QuizCraft Tests

## Running Tests

```bash
# Install test dependencies
pip install pytest

# From project root
python -m pytest tests/test_quiz_craft.py -v
```

Tests are offline — no Ollama connection required. They cover:

- `sanitize_prompt()` — injection stripping, length caps, control char removal
- `extract_quiz_json()` — clean JSON, markdown fences, preamble text, invalid inputs
- `normalize_question()` — all type aliases, bool/string answer normalization, edge cases
- `build_prompt()` — difficulty profiles, question count, topic injection, type instructions
- `DIFFICULTY_PROFILES` — temperature ordering, description presence
- `validate_and_sanitize_input()` — hosted version input validation

## Test Count

39 test cases across 6 test classes.

## Integration Testing

To test end-to-end with a live Ollama instance, confirm the server is reachable and the model is pulled first:

```bash
# Check what models are available on the Ollama server
ollama list

# Or if using a remote server
curl http://<server-ip>:11434/api/tags
```

Run a single quiz generation by piping the topic via stdin:

```bash
# Local Ollama (default)
echo "basic Python syntax" | python src/generate_quiz_from_prompt.py 5 Easy "Multiple Choice"

# Remote Ollama — set the host first
export OLLAMA_HOST=http://<server-ip>:11434
export OLLAMA_MODEL=qwen3:4b
echo "basic Python syntax" | python src/generate_quiz_from_prompt.py 5 Easy "Multiple Choice"
```

Should print valid JSON with 5 questions to stdout.

The prompt is read from stdin (not as a positional argument) to safely handle any text content without shell escaping issues.
