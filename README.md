# Mi primer repositorio

Este repositorio ahora incluye un programa para convertir texto a audio con voces neuronales en español y generar audios de **al menos 30 minutos**.

## Requisitos

- Python 3.10+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso rápido

### 1) Desde texto directo

```bash
python tts_es_largo.py \
  --text "Hola, este es un ejemplo de narración en español." \
  --voice es-ES-ElviraNeural \
  --output salida_30min.mp3 \
  --min-minutes 30
```

### 2) Desde archivo de texto

```bash
python tts_es_largo.py \
  --text-file texto.txt \
  --voice es-MX-DaliaNeural \
  --output salida_45min.mp3 \
  --min-minutes 45
```

## Voces disponibles

- es-ES-ElviraNeural
- es-ES-AlvaroNeural
- es-MX-DaliaNeural
- es-MX-JorgeNeural
- es-AR-ElenaNeural
- es-CO-GonzaloNeural
- es-CO-SalomeNeural
- es-CL-CatalinaNeural
- es-PE-AlexNeural
- es-VE-SebastianNeural

## Notas

- El programa valida que la duración mínima solicitada sea de **30 minutos o más**.
- Genera un segmento base TTS y lo repite automáticamente hasta alcanzar la duración solicitada.
