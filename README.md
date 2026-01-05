# Mi primer repositorio

Este repositorio ha sido creado para fines de prueba e integración con ChatGPT y Codex.

## Estructura prevista

- `README.md`: Este archivo con la descripción general.
- `src/ine_news_scraper.py`: Scraper diario para la sección de comunicación social del INE.
- `requirements.txt`: Dependencias de Python.

## Uso rápido

1. Instala las dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecuta una sola vez:

```bash
python src/ine_news_scraper.py --once --max-items 5
```

3. Ejecuta todos los días (por defecto a las 08:00):

```bash
python src/ine_news_scraper.py --daily-at 08:00 --output noticias.json
```

## Objetivos

- Verificar la conexión entre GitHub y ChatGPT.
- Probar tareas automáticas con Codex.
- Explorar funcionalidades de análisis de código.

## Autor

Jorge Luis Benito Guerrero  
[guerrerojorge40](https://github.com/guerrerojorge40)
