#!/usr/bin/env python3
"""Genera un podcast de debate (es-MX) entre dos voces neuronales usando TTS."""

from __future__ import annotations

import argparse
import asyncio
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Tuple

try:
    import edge_tts
except ImportError as exc:  # pragma: no cover - mensaje de error amigable
    raise SystemExit(
        "Falta la dependencia 'edge-tts'. Instálala con: pip install edge-tts"
    ) from exc

SPEAKERS = {
    "HOST_F": "es-MX-DaliaNeural",
    "HOST_M": "es-MX-JorgeNeural",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Genera un podcast de debate en español (México) entre una voz femenina y una masculina."
        )
    )
    parser.add_argument("--input", type=Path, help="Archivo de texto de entrada.")
    parser.add_argument("--out", type=Path, default=Path("salida.mp3"), help="MP3 final.")
    parser.add_argument(
        "--min-minutes",
        type=float,
        default=20.0,
        help="Duración mínima objetivo en minutos (por defecto: 20).",
    )
    parser.add_argument(
        "--voice-f",
        default=SPEAKERS["HOST_F"],
        help=f"Voz femenina (default: {SPEAKERS['HOST_F']}).",
    )
    parser.add_argument(
        "--voice-m",
        default=SPEAKERS["HOST_M"],
        help=f"Voz masculina (default: {SPEAKERS['HOST_M']}).",
    )
    return parser.parse_args()


def read_source_text(input_path: Path | None) -> str:
    if input_path:
        if not input_path.exists():
            raise SystemExit(f"No existe el archivo de entrada: {input_path}")
        return input_path.read_text(encoding="utf-8").strip()

    print("Pega tu texto. Finaliza con EOF (Ctrl+D en Linux/Mac, Ctrl+Z y Enter en Windows):")
    data = sys.stdin.read().strip()
    if not data:
        raise SystemExit("No se recibió texto de entrada.")
    return data


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    return [s.strip() for s in sentences if s.strip()]


def _clip_words(text: str, max_words: int = 20) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def build_debate_turns(text: str, min_minutes: float) -> List[Tuple[str, str]]:
    # Aprox. 145 palabras/min en locución conversacional en español.
    target_words = max(400, int(math.ceil(min_minutes * 145)))

    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    sentences = _split_sentences(text)
    if not sentences:
        raise SystemExit("El texto de entrada no contiene oraciones válidas.")

    key_points = paragraphs if paragraphs else sentences
    turns: List[Tuple[str, str]] = [
        (
            "HOST_F",
            "Bienvenidas y bienvenidos. Hoy abrimos un debate profundo basado exclusivamente en el texto que nos compartieron. "
            "No vamos a agregar datos externos: vamos a analizar ideas, relaciones, matices y posibles interpretaciones.",
        ),
        (
            "HOST_M",
            "Exacto. Yo propondré preguntas críticas y contraargumentos para tensionar cada punto, mientras mantenemos fidelidad total al contenido original. "
            "La meta es construir comprensión, no desviarnos del material base.",
        ),
    ]

    idx = 0
    while sum(len(t[1].split()) for t in turns) < target_words:
        a = _clip_words(key_points[idx % len(key_points)], 24)
        b = _clip_words(sentences[idx % len(sentences)], 22)
        c = _clip_words(sentences[(idx + 1) % len(sentences)], 22)
        d = _clip_words(key_points[(idx + 1) % len(key_points)], 24)

        turns.extend(
            [
                (
                    "HOST_F",
                    f"Arranquemos con esta idea del texto: «{a}». Mi lectura inicial es que aquí hay una tesis central que organiza el resto del discurso. "
                    "Si la entendemos como punto de partida, podemos comparar cómo dialoga con otras secciones y evaluar su consistencia interna.",
                ),
                (
                    "HOST_M",
                    f"Te compro la premisa, pero quiero poner presión. También aparece esta formulación: «{b}». "
                    "¿No crees que, leída con rigor, puede abrir una interpretación distinta o incluso generar tensión con la tesis principal? "
                    "Me interesa que expliquemos dónde hay complementariedad y dónde hay fricción.",
                ),
                (
                    "HOST_F",
                    f"Buena objeción. Para responderla, retomemos otra parte: «{c}». "
                    "Yo no lo veo como contradicción automática, sino como un cambio de enfoque dentro del mismo marco argumental. "
                    "Cuando conectamos estas líneas, emerge una progresión: planteamiento, matiz y reformulación.",
                ),
                (
                    "HOST_M",
                    f"Cierro este bloque con «{d}». En síntesis, tenemos una dialéctica útil: afirmación, duda, contraste y ajuste. "
                    "Para profundizar, conviene preguntar qué supuestos sostiene cada frase, cómo se justifican y qué implicaciones se desprenden si las llevamos al límite lógico.",
                ),
            ]
        )
        idx += 1

    turns.extend(
        [
            (
                "HOST_F",
                "Antes de cerrar, hagamos una recapitulación extensa. Partimos de las ideas troncales del texto, luego sometimos cada una a preguntas críticas, "
                "y finalmente observamos cómo los matices no necesariamente destruyen la tesis, sino que la vuelven más precisa.",
            ),
            (
                "HOST_M",
                "Totalmente. Nos quedamos con una lectura responsable: argumentar desde el propio contenido, explicitar supuestos, y reconocer ambigüedades sin inventar hechos externos. "
                "Gracias por acompañarnos en este ejercicio de debate razonado.",
            ),
        ]
    )

    return turns


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit(
            "No se encontró ffmpeg en el sistema. Instálalo para poder unir y normalizar el MP3 final."
        )


def run_cmd(cmd: Iterable[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"Error ejecutando comando:\n{' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )


def ssml_for_turn(speaker: str, text: str) -> str:
    esc = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    style = "friendly" if speaker == "HOST_F" else "chat"
    return (
        "<speak version='1.0' xml:lang='es-MX'>"
        f"<voice name='{SPEAKERS[speaker]}'>"
        f"<mstts:express-as style='{style}' xmlns:mstts='https://www.w3.org/2001/mstts'>{esc}</mstts:express-as>"
        "<break time='700ms'/>"
        "</voice></speak>"
    )


async def synthesize_turns(turns: List[Tuple[str, str]], temp_dir: Path) -> List[Path]:
    files: List[Path] = []
    for i, (speaker, text) in enumerate(turns, start=1):
        out = temp_dir / f"seg_{i:04d}.mp3"
        communicate = edge_tts.Communicate(ssml_for_turn(speaker, text), voice=SPEAKERS[speaker])
        await communicate.save(str(out))
        files.append(out)
        print(f"[{i}/{len(turns)}] sintetizado {speaker}")
    return files


def merge_and_normalize(parts: List[Path], out_file: Path, temp_dir: Path) -> None:
    concat_txt = temp_dir / "concat.txt"
    with concat_txt.open("w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.as_posix()}'\n")

    merged = temp_dir / "merged.mp3"
    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-c",
            "copy",
            str(merged),
        ]
    )

    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(merged),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar",
            "44100",
            "-b:a",
            "192k",
            str(out_file),
        ]
    )


def main() -> None:
    args = parse_args()
    ensure_ffmpeg()

    text = read_source_text(args.input)
    SPEAKERS["HOST_F"] = args.voice_f
    SPEAKERS["HOST_M"] = args.voice_m

    turns = build_debate_turns(text, args.min_minutes)
    total_words = sum(len(t[1].split()) for t in turns)
    est_minutes = total_words / 145

    print(f"Turnos generados: {len(turns)}")
    print(f"Palabras aproximadas: {total_words} (~{est_minutes:.1f} min)")

    out_file = args.out.expanduser().resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="podcast_tts_") as tmp:
        tmp_path = Path(tmp)
        try:
            parts = asyncio.run(synthesize_turns(turns, tmp_path))
        except Exception as exc:
            raise SystemExit(
                "No fue posible completar la síntesis TTS. Verifica tu conexión a internet y vuelve a intentar.\n"
                f"Detalle técnico: {exc}"
            ) from exc
        merge_and_normalize(parts, out_file, tmp_path)

    print(f"✅ Podcast generado: {out_file}")


if __name__ == "__main__":
    main()
