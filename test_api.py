#!/usr/bin/env python3
"""Script de prueba para la API de podcasts."""

import requests
import json

# URL base de la API
BASE_URL = "http://localhost:5000"

def test_home():
    """Prueba el endpoint raíz."""
    print("=== Probando GET / ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()

def test_health():
    """Prueba el endpoint de salud."""
    print("=== Probando GET /health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()

def test_generate():
    """Prueba el endpoint de generación."""
    print("=== Probando POST /generate ===")
    payload = {
        "text": "La inteligencia artificial está transformando el mundo moderno. "
                "Sus aplicaciones van desde la medicina hasta la educación. "
                "Debemos considerar tanto sus beneficios como sus desafíos éticos.",
        "min_minutes": 2
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Guardar el archivo MP3
        with open("podcast_test.mp3", "wb") as f:
            f.write(response.content)
        print("✅ Podcast generado y guardado como 'podcast_test.mp3'")
    else:
        print(f"❌ Error: {response.json()}")
    print()

def test_error_handling():
    """Prueba el manejo de errores."""
    print("=== Probando manejo de errores ===")
    
    # Sin texto
    print("1. Solicitud sin parámetro 'text':")
    response = requests.post(
        f"{BASE_URL}/generate",
        json={},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()
    
    # Content-Type incorrecto
    print("2. Content-Type incorrecto:")
    response = requests.post(
        f"{BASE_URL}/generate",
        data="test"
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()

if __name__ == "__main__":
    try:
        test_home()
        test_health()
        test_error_handling()
        
        # Descomentar para probar generación real (requiere conexión a internet)
        # test_generate()
        
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar a la API. Asegúrate de que esté ejecutándose.")
    except Exception as e:
        print(f"❌ Error: {e}")
