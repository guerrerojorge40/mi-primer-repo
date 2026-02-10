"""Omega Audit Generator v151.

Implementa:
- SmartIDResolver con resolución escalonada y validación cruzada.
- WebIntelAgent para rellenado automático de campos críticos faltantes.
- Ejecución robusta con retry, secciones safe-fail y manejo de pipes/encoding.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol


def configure_utf8_io() -> None:
    """Fuerza UTF-8 en stdout/stderr cuando sea posible."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def safe_print(*args: Any, **kwargs: Any) -> None:
    """Imprime manejando BrokenPipeError sin romper el proceso."""
    try:
        print(*args, **kwargs)
    except BrokenPipeError:
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(0)


def retry(max_attempts: int = 3, delay_s: float = 0.6, backoff: float = 2.0) -> Callable:
    """Decorador de reintentos para llamadas externas."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_exc: Optional[Exception] = None
            current_delay = delay_s
            while attempt < max_attempts:
                attempt += 1
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001 - queremos robustez global
                    last_exc = exc
                    if attempt >= max_attempts:
                        break
                    time.sleep(current_delay)
                    current_delay *= backoff
            raise RuntimeError(f"{fn.__name__} failed after {max_attempts} attempts") from last_exc

        return wrapper

    return decorator


class FootballApiClient(Protocol):
    """Interfaz mínima esperada del cliente API-Football."""

    def search_team_exact(self, team_name: str) -> List[Dict[str, Any]]: ...

    def search_team_fuzzy(self, team_name: str) -> List[Dict[str, Any]]: ...

    def list_teams_by_country(self, country: str) -> List[Dict[str, Any]]: ...

    def get_team_context(self, team_id: int) -> Dict[str, Any]: ...


class WebSearchClient(Protocol):
    """Interfaz mínima para búsquedas web."""

    def search_web(self, query: str) -> str: ...


@dataclass
class TeamResolution:
    team_id: int
    team_name: str
    country: Optional[str] = None
    league: Optional[str] = None
    source: str = "unknown"


class SmartIDResolver:
    def __init__(self, api_client: FootballApiClient, web_client: WebSearchClient):
        self.api = api_client
        self.web = web_client

    @retry(max_attempts=3)
    def _api_exact(self, team_name: str) -> List[Dict[str, Any]]:
        return self.api.search_team_exact(team_name)

    @retry(max_attempts=3)
    def _api_fuzzy(self, team_name: str) -> List[Dict[str, Any]]:
        return self.api.search_team_fuzzy(team_name)

    @retry(max_attempts=3)
    def _teams_by_country(self, country: str) -> List[Dict[str, Any]]:
        return self.api.list_teams_by_country(country)

    @retry(max_attempts=3)
    def _web_search(self, query: str) -> str:
        return self.web.search_web(query)

    def resolve(self, team_name: str, league: Optional[str] = None, country: Optional[str] = None) -> TeamResolution:
        """Resuelve IDs con estrategia escalonada + validación cruzada."""
        # 1) Exacta
        exact = self._api_exact(team_name)
        match = self._select_valid_match(exact, league=league, country=country)
        if match:
            return self._to_resolution(match, source="api_exact")

        # 2) Difusa
        fuzzy = self._api_fuzzy(team_name)
        match = self._select_valid_match(fuzzy, league=league, country=country)
        if match:
            return self._to_resolution(match, source="api_fuzzy")

        # 3) Por país
        if country:
            candidates = self._teams_by_country(country)
            local = self._local_name_filter(team_name, candidates)
            match = self._select_valid_match(local, league=league, country=country)
            if match:
                return self._to_resolution(match, source="api_country")

        # 4) Fallback web
        query = f"API Football team ID for {team_name} {league or ''}".strip()
        text = self._web_search(query)
        team_id = self._extract_team_id(text)
        if team_id is None:
            raise ValueError(f"No se pudo resolver el ID para {team_name}")

        # 5) Validación cruzada final
        context = self.api.get_team_context(team_id)
        if not self._matches_context(context, league=league, country=country):
            raise ValueError(
                f"ID {team_id} encontrado por web no coincide con liga/país esperados"
            )
        return TeamResolution(
            team_id=team_id,
            team_name=context.get("team_name", team_name),
            league=context.get("league"),
            country=context.get("country"),
            source="web_fallback",
        )

    def _matches_context(self, candidate: Dict[str, Any], league: Optional[str], country: Optional[str]) -> bool:
        c_league = (candidate.get("league") or "").lower()
        c_country = (candidate.get("country") or "").lower()
        if league and league.lower() not in c_league:
            return False
        if country and country.lower() not in c_country:
            return False
        return True

    def _select_valid_match(
        self,
        candidates: Iterable[Dict[str, Any]],
        league: Optional[str],
        country: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        for candidate in candidates:
            if self._matches_context(candidate, league=league, country=country):
                return candidate
        return None

    def _local_name_filter(self, team_name: str, candidates: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        needle = _normalize(team_name)
        results: List[Dict[str, Any]] = []
        for c in candidates:
            name = _normalize(c.get("team_name", ""))
            if needle in name or name in needle:
                results.append(c)
        return results

    def _extract_team_id(self, web_text: str) -> Optional[int]:
        """Extrae ID de texto libre buscando patrones frecuentes."""
        patterns = [
            r"\bteam\s*id\s*[:#]?\s*(\d{2,7})\b",
            r"\bapi[-\s]?football[^\d]{0,40}(\d{2,7})\b",
            r"\bID\s*(\d{2,7})\b",
        ]
        for pattern in patterns:
            m = re.search(pattern, web_text, flags=re.IGNORECASE)
            if m:
                return int(m.group(1))
        ids = re.findall(r"\b\d{2,7}\b", web_text)
        return int(ids[0]) if ids else None

    def _to_resolution(self, match: Dict[str, Any], source: str) -> TeamResolution:
        return TeamResolution(
            team_id=int(match["team_id"]),
            team_name=match.get("team_name", ""),
            league=match.get("league"),
            country=match.get("country"),
            source=source,
        )


class WebIntelAgent:
    """Completa campos críticos faltantes usando búsqueda web + extracción limpia."""

    CRITICAL_FIELDS = {
        "coach": lambda ctx: f"Current head coach of {ctx['team_name']} 2026",
        "injuries": lambda ctx: (
            f"Injuries and suspensions for {ctx['team_a']} vs {ctx['team_b']} match today"
        ),
        "weather": lambda ctx: (
            f"Weather forecast for {ctx['stadium']} {ctx['city']} match time today"
        ),
        "referee": lambda ctx: f"Referee for {ctx['team_a']} vs {ctx['team_b']} today",
    }

    def __init__(self, web_client: WebSearchClient):
        self.web = web_client

    @retry(max_attempts=3)
    def _web_search(self, query: str) -> str:
        return self.web.search_web(query)

    def detect_gaps(self, full_data: Dict[str, Any]) -> List[str]:
        missing = []
        for field in self.CRITICAL_FIELDS:
            value = full_data.get(field)
            if value is None or value == [] or value == "" or value == "?" or value == "{{WEB_REQUIRED}}":
                missing.append(field)
        return missing

    def enrich(self, full_data: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
        filled = dict(full_data)
        for field in self.detect_gaps(full_data):
            query_fn = self.CRITICAL_FIELDS[field]
            query = query_fn(context)
            raw = self._web_search(query)
            filled[field] = self._extract_clean_value(field, raw)
        return filled

    def _extract_clean_value(self, field: str, raw_text: str) -> str:
        """Extracción ligera; reemplazable por LLM si se integra luego."""
        compact = " ".join(raw_text.split())
        field_patterns = {
            "coach": r"(?:coach|manager)[:\-\s]+([A-Z][A-Za-zÀ-ÿ\-\s\.]{2,80})",
            "weather": r"(?:\d{1,2}°?C|rain|clear|cloudy|storm)[^\.]{0,120}",
            "referee": r"(?:referee|arbitro|árbitro)[:\-\s]+([A-Z][A-Za-zÀ-ÿ\-\s\.]{2,80})",
            "injuries": r"(?:injur(?:y|ies)|suspension)[^\.]{0,180}",
        }
        pattern = field_patterns.get(field)
        if pattern:
            m = re.search(pattern, compact, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip() if m.groups() else m.group(0).strip()
        return compact[:220]


def run_section(section_name: str, section_fn: Callable[[], str]) -> str:
    """Ejecuta una sección en modo safe-fail."""
    try:
        return section_fn()
    except Exception as exc:  # noqa: BLE001
        return f"## {section_name}\n⚠️ Error en sección: {exc}\n"


def build_markdown_report(sections: Dict[str, Callable[[], str]]) -> str:
    output = []
    for name, fn in sections.items():
        output.append(run_section(name, fn))
    return "\n".join(output)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main() -> int:
    configure_utf8_io()
    payload = os.environ.get("OMEGA_INPUT_JSON", "{}")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        safe_print("⚠️ OMEGA_INPUT_JSON inválido; usando objeto vacío")
        data = {}

    safe_print("Omega v151 listo. Módulos SmartIDResolver + WebIntelAgent habilitados.")
    safe_print(json.dumps({"received_keys": sorted(data.keys())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
