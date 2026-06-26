"""
QuizCraft CLI — generate quizzes from the terminal.

Usage:
    quizcraft --topic "World War II" --n-questions 5
    quizcraft --topic "Python basics" --difficulty Hard --types "Multiple Choice,True/False"
    quizcraft --topic "Cell biology" --output pdf --output-file quiz.pdf
    echo "Photosynthesis" | quizcraft --topic -   # read topic from stdin
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import typer
except ImportError:
    sys.exit(
        "Error: 'typer' is required for the CLI. Install it: pip install typer\n"
        "Or install all extras: pip install quiz-craft[cli]"
    )

from typing import Optional

from typing_extensions import Annotated

from generate_quiz_from_prompt import DIFFICULTY_PROFILES, generate_quiz

app = typer.Typer(
    name="quizcraft",
    help="Generate AI-powered quizzes from any topic or text.",
    add_completion=False,
)

_VALID_TYPES = ["Multiple Choice", "True/False", "Fill in the Blanks"]
_VALID_DIFFICULTIES = list(DIFFICULTY_PROFILES.keys())


def _parse_types(types_str: str) -> list[str]:
    result = [t.strip() for t in types_str.split(",") if t.strip()]
    for t in result:
        if t not in _VALID_TYPES:
            typer.echo(
                f"Error: unknown question type '{t}'. Valid types: {', '.join(_VALID_TYPES)}",
                err=True,
            )
            raise typer.Exit(1)
    return result or ["Multiple Choice"]


@app.command()
def main(
    topic: Annotated[
        str,
        typer.Option(
            "--topic", "-t",
            help="Topic or text to generate questions about. Use '-' to read from stdin.",
        ),
    ] = "",
    n_questions: Annotated[
        int,
        typer.Option("--n-questions", "-n", min=1, max=40, help="Number of questions."),
    ] = 5,
    difficulty: Annotated[
        str,
        typer.Option(
            "--difficulty", "-d",
            help=f"Difficulty: {', '.join(_VALID_DIFFICULTIES)}",
        ),
    ] = "Medium",
    types: Annotated[
        str,
        typer.Option("--types", help="Comma-separated question types."),
    ] = "Multiple Choice",
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format: json (default), txt, pdf"),
    ] = "json",
    output_file: Annotated[
        Optional[str],
        typer.Option("--output-file", "-f", help="Write output to file instead of stdout."),
    ] = None,
):
    """Generate a quiz from a topic or text passage."""
    # Validate difficulty
    if difficulty not in _VALID_DIFFICULTIES:
        typer.echo(
            f"Error: unknown difficulty '{difficulty}'. Valid: {', '.join(_VALID_DIFFICULTIES)}",
            err=True,
        )
        raise typer.Exit(1)

    # Resolve topic
    if topic == "-" or not topic:
        if sys.stdin.isatty() and not topic:
            typer.echo("Error: --topic is required (or use '-' to read from stdin).", err=True)
            raise typer.Exit(1)
        topic = sys.stdin.read().strip()
    if not topic:
        typer.echo("Error: topic cannot be empty.", err=True)
        raise typer.Exit(1)

    question_types = _parse_types(types)

    topic_preview = f"{topic[:60]}{'...' if len(topic) > 60 else ''}"
    typer.echo(
        f"Generating {n_questions} {difficulty} question(s) on '{topic_preview}' ...",
        err=True,
    )

    result = generate_quiz(
        number_of_questions=n_questions,
        difficulty=difficulty,
        user_prompt=topic,
        question_types=question_types,
    )

    if result.get("error"):
        typer.echo(f"Error: {result['error']}", err=True)
        raise typer.Exit(1)

    if not result.get("quiz"):
        typer.echo("Error: model returned an empty quiz. Try a different topic or model.", err=True)
        raise typer.Exit(1)

    output = output.lower()
    if output == "json":
        content = json.dumps(result, indent=2, ensure_ascii=False)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            typer.echo(f"Quiz saved to {output_file}", err=True)
        else:
            typer.echo(content)

    elif output == "txt":
        content = _format_as_text(result, topic)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            typer.echo(f"Quiz saved to {output_file}", err=True)
        else:
            typer.echo(content)

    elif output == "pdf":
        if not output_file:
            output_file = "quiz.pdf"
        _generate_pdf(result, topic, output_file)
        typer.echo(f"PDF saved to {output_file}", err=True)

    else:
        typer.echo(f"Error: unknown output format '{output}'. Use: json, txt, pdf", err=True)
        raise typer.Exit(1)


def _format_as_text(quiz_data: dict, topic: str) -> str:
    import datetime
    divider = "=" * 60
    thin = "-" * 60
    lines = [divider, "  QUIZCRAFT — AI-Generated Quiz"]
    if topic:
        lines.append(f"  Topic: {topic[:80]}")
    lines.append(f"  Generated: {datetime.datetime.now().strftime('%B %d, %Y')}")
    lines.append(divider)
    lines.append("")

    for i, q in enumerate(quiz_data.get("quiz", []), 1):
        qtype = q.get("type", "").strip().lower()
        lines.append(f"{i}.  {q['question']}")
        if qtype == "multiple choice":
            for idx, opt in enumerate(q.get("options", []), 1):
                lines.append(f"     {chr(96 + idx)})  {opt}")
        elif qtype == "true/false":
            lines.append("     a)  True")
            lines.append("     b)  False")
        elif qtype == "fill in the blanks":
            lines.append("     Answer: ___________________________")
        lines.append("")

    lines.extend([thin, "", "ANSWER KEY", thin])
    for i, q in enumerate(quiz_data.get("quiz", []), 1):
        lines.append(f"  {i}. {q['answer']}")
    lines.append("")
    return "\n".join(lines)


def _generate_pdf(quiz_data: dict, topic: str, output_file: str) -> None:
    try:
        from quiz_craft import generate_quiz_pdf
        pdf_bytes = generate_quiz_pdf(quiz_data, topic=topic)
        with open(output_file, "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        typer.echo(f"Error generating PDF: {e}", err=True)
        typer.echo("Falling back to text output.", err=True)
        txt_file = output_file.replace(".pdf", ".txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(_format_as_text(quiz_data, topic))
        typer.echo(f"Text quiz saved to {txt_file}", err=True)


if __name__ == "__main__":
    app()
