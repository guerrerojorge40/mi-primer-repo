#!/usr/bin/env python3
"""Genera audios TTS en español (alta calidad) de al menos N minutos."""

from __future__ import annotations

import argparse
import asyncio
import math
import tempfile
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

SPANISH_VOICES = [
    "es-ES-ElviraNeural",
    "es-ES-AlvaroNeural",
    "es-MX-DaliaNeural",
    "es-MX-JorgeNeural",
    "es-AR-ElenaNeural",
    "es-CO-GonzaloNeural",
    "es-CO-SalomeNeural",
    "es-CL-CatalinaNeural",
    "es-PE-AlexNeural",
    "es-VE-SebastianNeural",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convierte texto a audio en español usando voces neuronales y garantiza "
            "una duración mínima (por defecto 30 minutos)."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Texto directo para sintetizar")
    source.add_argument("--text-file", type=Path, help="Ruta a archivo .txt")

    parser.add_argument(
        "--voice",
        default="es-ES-ElviraNeural",
        choices=SPANISH_VOICES,
        help="Voz neuronal en español",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("audio_30min.mp3"),
        help="Ruta del archivo de salida .mp3",
    )
    parser.add_argument(
        "--min-minutes",
        type=int,
        default=30,
        help="Duración mínima del audio en minutos (mínimo permitido: 30)",
    )
    parser.add_argument(
        "--rate",
        default="+0%",
        help='Velocidad de voz de Edge TTS (ej: "+0%%", "-10%%", "+15%%")',
    )
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.text:
        text = args.text.strip()
    else:
        text = args.text_file.read_text(encoding="utf-8").strip()

    if not text:
        raise ValueError("El texto no puede estar vacío.")
    return text


async def synthesize_segment(text: str, voice: str, rate: str, output: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(output))


def mp3_duration_seconds(mp3_path: Path) -> float:
    return float(MP3(mp3_path).info.length)


def repeat_mp3_bytes(segment: Path, output: Path, repeats: int) -> None:
    data = segment.read_bytes()
    with output.open("wb") as f:
        for _ in range(repeats):
            f.write(data)


def main() -> None:
    args = parse_args()
    if args.min_minutes < 30:
        raise SystemExit("Error: este programa requiere audios de al menos 30 minutos.")

    text = load_text(args)
    target_seconds = args.min_minutes * 60

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        segment = Path(tmpdir) / "segment.mp3"
        asyncio.run(synthesize_segment(text, args.voice, args.rate, segment))

        seg_seconds = mp3_duration_seconds(segment)
        if seg_seconds <= 0:
            raise RuntimeError("No se pudo medir la duración del segmento generado.")

        repeats = max(1, math.ceil(target_seconds / seg_seconds))
        repeat_mp3_bytes(segment, args.output, repeats)

        final_seconds = mp3_duration_seconds(args.output)
        if final_seconds < target_seconds:
            missing_repeats = math.ceil((target_seconds - final_seconds) / seg_seconds)
            segment_data = segment.read_bytes()
            with args.output.open("ab") as out_f:
                for _ in range(missing_repeats):
                    out_f.write(segment_data)
            final_seconds = mp3_duration_seconds(args.output)

    print(
        f"Audio generado: {args.output} | Voz: {args.voice} | "
        f"Duración: {final_seconds / 60:.2f} minutos"
    )


if __name__ == "__main__":
    main()
