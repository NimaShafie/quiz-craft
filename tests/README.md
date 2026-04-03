# QuizCraft Tests

## Running Tests

```bash
# Install test dependencies
pip install pytest

# From project root
python -m pytest tests/test_quizcraft.py -v
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

To test end-to-end with a live Ollama instance:

```bash
# Verify Ollama is running and model is pulled
ollama list

# Run a single quiz generation
python src/generate_quiz_from_prompt.py 5 Easy "basic Python syntax" "Multiple Choice"

# Should print valid JSON with 5 questions
```
