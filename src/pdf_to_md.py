#!/usr/bin/env python3
"""Convert PDF documents to a simple Markdown representation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber


def extract_text(pdf_path: Path) -> str:
    """Extract text from a PDF and format it as Markdown."""
    sections = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            cleaned = text.strip()
            sections.append(f"## Page {page_number}\n\n{cleaned}")
    return "\n\n".join(sections).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF file to Markdown by extracting its text."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the input PDF file.")
    parser.add_argument(
        "output_md",
        type=Path,
        help="Path where the Markdown output should be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = extract_text(args.input_pdf)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
