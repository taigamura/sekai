from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from sekai.container import MissingCredentialsError, container
from sekai.curate import curate
from sekai.fetch import fetch_reddit
from sekai.render import render
from sekai.synthesize import SynthesizeError, synthesize

SUPPORTED_SOURCES = {"reddit"}
SUPPORTED_MODELS = {"haiku"}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sekai",
        description=(
            "Fetch EN-language online discourse about a topic and render a "
            "translated, culturally-framed Japanese Markdown report."
        ),
    )
    parser.add_argument("--topic", required=True, help="The subject to research.")
    parser.add_argument(
        "--sources", default="reddit", help="Comma-separated enabled sources."
    )
    parser.add_argument("--model", default="haiku", help="Synthesis LLM backend.")
    parser.add_argument(
        "--max-items", type=int, default=15, help="Items to keep after curation."
    )
    parser.add_argument("--out", default="report.md", help="Output file path.")
    return parser.parse_args(argv)


def _validate_sources(sources: str) -> list[str]:
    requested = [s.strip() for s in sources.split(",") if s.strip()]
    unsupported = [s for s in requested if s not in SUPPORTED_SOURCES]
    if unsupported:
        raise ValueError(
            f"Unsupported source(s): {', '.join(unsupported)}. "
            f"Currently supported: {', '.join(sorted(SUPPORTED_SOURCES))}."
        )
    return requested


def _validate_model(model: str) -> str:
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported model: {model}. "
            f"Currently supported: {', '.join(sorted(SUPPORTED_MODELS))}."
        )
    return model


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        _validate_sources(args.sources)
        _validate_model(args.model)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        reddit_client = container.reddit_client()
    except MissingCredentialsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    raw_items = fetch_reddit(args.topic, reddit_client)
    if not raw_items:
        print(
            f"Error: No Reddit discourse found for topic '{args.topic}' "
            "in the last 30 days.",
            file=sys.stderr,
        )
        return 1

    shortlist = curate(raw_items, max_items=args.max_items)

    try:
        llm_client = container.anthropic_client()
    except MissingCredentialsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        synthesis = synthesize(args.topic, shortlist, llm_client)
    except SynthesizeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report = render(synthesis)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written to {args.out}")
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
