#!/usr/bin/env python3
"""API REST para generar podcasts de debate usando edge-tts."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_file

# Importar funciones del módulo podcast
from podcast import (
    build_debate_turns,
    ensure_ffmpeg,
    merge_and_normalize,
    SPEAKERS,
    synthesize_turns,
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
        
        # Actualizar voces si fueron especificadas
        SPEAKERS["HOST_F"] = voice_f
        SPEAKERS["HOST_M"] = voice_m
        
        # Verificar ffmpeg
        ensure_ffmpeg()
        
        # Generar turnos del debate
        turns = build_debate_turns(text, min_minutes)
        total_words = sum(len(t[1].split()) for t in turns)
        est_minutes = total_words / 145
        
        # Crear archivo temporal para el resultado
        with tempfile.TemporaryDirectory(prefix="podcast_api_") as tmp:
            tmp_path = Path(tmp)
            output_file = tmp_path / "podcast.mp3"
            
            # Sintetizar y unir audio
            parts = asyncio.run(synthesize_turns(turns, tmp_path))
            merge_and_normalize(parts, output_file, tmp_path)
            
            # Retornar el archivo MP3
            return send_file(
                output_file,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="podcast.mp3"
            )
    
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
