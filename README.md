# Mi primer repositorio

Este repositorio ha sido creado para fines de prueba e integración con ChatGPT y Codex.

## Generador de podcast de debate (es-MX)

### Opción 1: API REST

1. Instala dependencias: `pip install -r requirements.txt` y asegúrate de tener `ffmpeg` en PATH.
2. Ejecuta el servidor: `python api.py`
3. La API estará disponible en `http://localhost:5000`

#### Endpoints disponibles

- **GET /** - Información de la API
- **GET /health** - Estado de salud del servicio
- **POST /generate** - Genera un podcast de debate

#### Ejemplo de uso del endpoint /generate

```bash
# Solicitud con curl
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "La inteligencia artificial está transformando el mundo. Sus aplicaciones son cada vez más amplias y sofisticadas.",
    "min_minutes": 5
  }' \
  --output podcast.mp3

# El archivo podcast.mp3 se descargará automáticamente
```

#### Parámetros JSON para /generate

- `text` (string, requerido): Texto base para generar el debate
- `min_minutes` (float, opcional, default=20): Duración mínima deseada en minutos
- `voice_f` (string, opcional): Voz femenina personalizada
- `voice_m` (string, opcional): Voz masculina personalizada

### Opción 2: Script de línea de comandos

1. Instala dependencias: `pip install edge-tts` y asegúrate de tener `ffmpeg` en PATH.
2. Ejecuta en modo archivo: `python podcast.py --input texto.txt --out salida.mp3 --min-minutes 20`.
3. O modo interactivo: `python podcast.py` y pega el texto; termina con EOF.

#### Ejemplo de ejecución esperada
```bash
$ python podcast.py --input texto.txt --out salida.mp3 --min-minutes 20
Turnos generados: 42
Palabras aproximadas: 2950 (~20.3 min)
✅ Podcast generado: /workspace/mi-primer-repo/salida.mp3
```

## Autor
Jorge Luis Benito Guerrero  
[guerrerojorge40](https://github.com/guerrerojorge40)
