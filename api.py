#!/usr/bin/env python3
"""API REST para generar podcasts de debate usando edge-tts."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_file, after_this_request

# Importar edge_tts para síntesis
try:
    import edge_tts
except ImportError as exc:
    raise SystemExit(
        "Falta la dependencia 'edge-tts'. Instálala con: pip install edge-tts"
    ) from exc

# Importar funciones del módulo podcast
from podcast import (
    build_debate_turns,
    ensure_ffmpeg,
    merge_and_normalize,
    SPEAKERS,
)

app = Flask(__name__)


@app.route("/")
def home():
    """Endpoint de bienvenida."""
    return jsonify({
        "message": "API de generación de podcasts de debate",
        "version": "1.0",
        "endpoints": {
            "/": "GET - Esta página de bienvenida",
            "/health": "GET - Estado de salud del servicio",
            "/generate": "POST - Genera un podcast a partir de texto"
        }
    })


@app.route("/health")
def health():
    """Endpoint de health check."""
    try:
        ensure_ffmpeg()
        return jsonify({
            "status": "healthy",
            "ffmpeg": "available"
        })
    except SystemExit:
        return jsonify({
            "status": "unhealthy",
            "ffmpeg": "missing"
        }), 500


@app.route("/generate", methods=["POST"])
def generate_podcast():
    """
    Genera un podcast de debate a partir de texto.
    
    Parámetros JSON esperados:
    - text: str (requerido) - Texto base para el debate
    - min_minutes: float (opcional, default=20) - Duración mínima en minutos
    - voice_f: str (opcional) - Voz femenina
    - voice_m: str (opcional) - Voz masculina
    
    Retorna: archivo MP3 del podcast generado
    """
    try:
        # Validar que se recibió JSON
        if not request.is_json:
            return jsonify({
                "error": "Se requiere Content-Type: application/json"
            }), 400
        
        data = request.get_json()
        
        # Validar parámetro requerido
        text = data.get("text", "").strip()
        if not text:
            return jsonify({
                "error": "El parámetro 'text' es requerido y no puede estar vacío"
            }), 400
        
        # Parámetros opcionales
        min_minutes = float(data.get("min_minutes", 20.0))
        voice_f = data.get("voice_f", SPEAKERS["HOST_F"])
        voice_m = data.get("voice_m", SPEAKERS["HOST_M"])
        
        # Crear copia local de SPEAKERS para evitar race conditions
        speakers_local = {
            "HOST_F": voice_f,
            "HOST_M": voice_m,
        }
        
        # Verificar ffmpeg
        ensure_ffmpeg()
        
        # Generar turnos del debate
        turns = build_debate_turns(text, min_minutes)
        total_words = sum(len(t[1].split()) for t in turns)
        est_minutes = total_words / 145
        
        # Crear directorio temporal que persista más allá de la función
        temp_dir = tempfile.mkdtemp(prefix="podcast_api_")
        output_file = Path(temp_dir) / "podcast.mp3"
        
        try:
            # Sintetizar y unir audio usando SPEAKERS locales
            parts = asyncio.run(synthesize_turns_with_voices(turns, Path(temp_dir), speakers_local))
            merge_and_normalize(parts, output_file, Path(temp_dir))
            
            # Registrar limpieza del directorio temporal después de enviar el archivo
            @after_this_request
            def cleanup(response):
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass
                return response
            
            # Retornar el archivo MP3
            return send_file(
                output_file,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="podcast.mp3"
            )
        except Exception as e:
            # Limpiar archivos temporales en caso de error
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    except ValueError as e:
        return jsonify({
            "error": f"Error en los parámetros: {str(e)}"
        }), 400
    except SystemExit as e:
        return jsonify({
            "error": f"Error del sistema: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Error inesperado: {str(e)}"
        }), 500


async def synthesize_turns_with_voices(turns, temp_dir, speakers):
    """Sintetizar turnos con voces específicas."""
    files = []
    for i, (speaker, text) in enumerate(turns, start=1):
        out = temp_dir / f"seg_{i:04d}.mp3"
        
        # Escapar texto para SSML
        esc = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        style = "friendly" if speaker == "HOST_F" else "chat"
        ssml = (
            "<speak version='1.0' xml:lang='es-MX'>"
            f"<voice name='{speakers[speaker]}'>"
            f"<mstts:express-as style='{style}' xmlns:mstts='https://www.w3.org/2001/mstts'>{esc}</mstts:express-as>"
            "<break time='700ms'/>"
            "</voice></speak>"
        )
        
        communicate = edge_tts.Communicate(ssml, voice=speakers[speaker])
        await communicate.save(str(out))
        files.append(out)
        print(f"[{i}/{len(turns)}] sintetizado {speaker}")
    return files


if __name__ == "__main__":
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
