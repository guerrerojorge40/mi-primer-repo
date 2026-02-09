# Mi primer repositorio

Este repositorio ha sido creado para fines de prueba e integración con ChatGPT y Codex.

## Generador de podcast de debate (es-MX)
1. Instala dependencias: `pip install edge-tts` y asegúrate de tener `ffmpeg` en PATH.
2. Ejecuta en modo archivo: `python podcast.py --input texto.txt --out salida.mp3 --min-minutes 20`.
3. O modo interactivo: `python podcast.py` y pega el texto; termina con EOF.

### Ejemplo de ejecución esperada
```bash
$ python podcast.py --input texto.txt --out salida.mp3 --min-minutes 20
Turnos generados: 42
Palabras aproximadas: 2950 (~20.3 min)
✅ Podcast generado: /workspace/mi-primer-repo/salida.mp3
```

## Autor
Jorge Luis Benito Guerrero  
[guerrerojorge40](https://github.com/guerrerojorge40)
