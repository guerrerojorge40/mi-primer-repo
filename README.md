# Mi primer repositorio

Este repositorio ha sido creado para fines de prueba e integración con ChatGPT y Codex.

## Consulta de trámites RAN (Registro Agrario Nacional)
Herramienta para consultar el estatus de trámites en el RAN de México.

### Instalación de dependencias
```bash
pip install requests
```

### Uso
```bash
python ran_consulta.py --folio NUMERO_DE_FOLIO
```

### Opciones adicionales
```bash
python ran_consulta.py --folio NUMERO_DE_FOLIO --estado "Estado de México" --municipio "Toluca" --tipo ejido
```

### Ejemplo de ejecución
```bash
$ python ran_consulta.py --folio 12345
🔍 Consultando trámite en el RAN...

============================================================
CONSULTA DE TRÁMITE RAN - REGISTRO AGRARIO NACIONAL
============================================================

📋 Folio consultado: 12345
🌐 URL de consulta: http://consultasimcr.ran.gob.mx/consulta_tramite.aspx

📝 Parámetros de búsqueda:
   • Folio: 12345

💡 Para consultar el estatus completo, visita: http://consultasimcr.ran.gob.mx/consulta_tramite.aspx

------------------------------------------------------------
INFORMACIÓN ADICIONAL:
------------------------------------------------------------
• Para consultas telefónicas: 55 5062 1423 / 55 5062 1424
• Correo electrónico: reporte_rantel@ran.gob.mx
• Horario de atención: Lunes a viernes de 9:00 a 16:00 hrs
• Portal principal: https://www.gob.mx/ran/
============================================================
```

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
