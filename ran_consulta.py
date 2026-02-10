#!/usr/bin/env python3
"""Consulta el estatus de un trámite en el RAN (Registro Agrario Nacional) de México."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

try:
    import requests
except ImportError as exc:
    raise SystemExit(
        "Falta la dependencia 'requests'. Instálala con: pip install requests"
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consulta el estatus de un trámite en el RAN de México."
    )
    parser.add_argument(
        "--folio",
        type=str,
        required=True,
        help="Número de folio o solicitud del trámite.",
    )
    parser.add_argument(
        "--estado",
        type=str,
        help="Estado donde se realizó el trámite (opcional).",
    )
    parser.add_argument(
        "--municipio",
        type=str,
        help="Municipio donde se realizó el trámite (opcional).",
    )
    parser.add_argument(
        "--tipo",
        type=str,
        choices=["ejido", "comunidad", "colonia"],
        help="Tipo de trámite: ejido, comunidad o colonia (opcional).",
    )
    return parser.parse_args()


def consultar_tramite(
    folio: str,
    estado: Optional[str] = None,
    municipio: Optional[str] = None,
    tipo: Optional[str] = None,
) -> dict:
    """
    Consulta el estatus de un trámite en el RAN.
    
    Args:
        folio: Número de folio o solicitud del trámite
        estado: Estado donde se realizó el trámite
        municipio: Municipio donde se realizó el trámite
        tipo: Tipo de trámite (ejido, comunidad, colonia)
    
    Returns:
        Diccionario con la información del trámite
    """
    # Nota: El sitio del RAN puede usar HTTP o HTTPS dependiendo de su configuración
    # Intentamos con HTTPS primero por seguridad
    url_consulta = "https://consultasimcr.ran.gob.mx/consulta_tramite.aspx"
    
    # Preparar parámetros de búsqueda
    params = {"folio": folio}
    if estado:
        params["estado"] = estado
    if municipio:
        params["municipio"] = municipio
    if tipo:
        params["tipo"] = tipo
    
    try:
        # Configurar headers para simular un navegador
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9",
        }
        
        # Realizar la solicitud con los parámetros
        session = requests.Session()
        response = session.get(url_consulta, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        # TODO: Implementar parsing del HTML de respuesta para extraer
        # el estatus detallado del trámite. Por ahora retornamos información básica.
        return {
            "estatus": "consultado",
            "folio": folio,
            "url": url_consulta,
            "mensaje": "Para consultar el estatus completo, visita: https://consultasimcr.ran.gob.mx/consulta_tramite.aspx",
            "parametros": params,
        }
        
    except requests.exceptions.Timeout:
        return {
            "error": "Tiempo de espera agotado",
            "mensaje": "El servidor del RAN no respondió a tiempo. Intenta nuevamente más tarde.",
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": "Error de conexión",
            "mensaje": "No se pudo conectar al servidor del RAN. Verifica tu conexión a internet.",
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": "Error en la consulta",
            "mensaje": f"Ocurrió un error al consultar el RAN: {str(e)}",
        }


def mostrar_resultado(resultado: dict) -> None:
    """Muestra el resultado de la consulta de forma legible."""
    print("\n" + "=" * 60)
    print("CONSULTA DE TRÁMITE RAN - REGISTRO AGRARIO NACIONAL")
    print("=" * 60)
    
    if "error" in resultado:
        print(f"\n❌ ERROR: {resultado['error']}")
        print(f"   {resultado['mensaje']}")
    else:
        print(f"\n📋 Folio consultado: {resultado.get('folio', 'N/A')}")
        print(f"🌐 URL de consulta: {resultado.get('url', 'N/A')}")
        
        if "parametros" in resultado:
            print("\n📝 Parámetros de búsqueda:")
            for key, value in resultado["parametros"].items():
                print(f"   • {key.capitalize()}: {value}")
        
        print(f"\n💡 {resultado.get('mensaje', '')}")
        
        print("\n" + "-" * 60)
        print("INFORMACIÓN ADICIONAL:")
        print("-" * 60)
        print("• Para consultas telefónicas: 55 5062 1423 / 55 5062 1424")
        print("• Correo electrónico: reporte_rantel@ran.gob.mx")
        print("• Horario de atención: Lunes a viernes de 9:00 a 16:00 hrs")
        print("• Portal principal: https://www.gob.mx/ran/")
    
    print("=" * 60 + "\n")


def main() -> None:
    args = parse_args()
    
    print("🔍 Consultando trámite en el RAN...\n")
    
    resultado = consultar_tramite(
        folio=args.folio,
        estado=args.estado,
        municipio=args.municipio,
        tipo=args.tipo,
    )
    
    mostrar_resultado(resultado)


if __name__ == "__main__":
    main()
