"""INE Comunicación Social news scraper."""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

try:
    import requests
except ImportError:  # pragma: no cover - handled by runtime warning
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - handled by runtime warning
    BeautifulSoup = None

try:
    import schedule
except ImportError:  # pragma: no cover - handled by runtime warning
    schedule = None

DEFAULT_URL = "https://www.ine.mx/ine/comunicacion-social/"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class DependencyError(RuntimeError):
    """Raised when optional dependencies are missing."""


def ensure_dependencies() -> None:
    missing = []
    if requests is None:
        missing.append("requests")
    if BeautifulSoup is None:
        missing.append("beautifulsoup4")
    if missing:
        raise DependencyError(
            "Faltan dependencias: "
            + ", ".join(missing)
            + ". Instala con: pip install -r requirements.txt"
        )


def fetch_html(url: str) -> str:
    ensure_dependencies()
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def _text_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _extract_date(container) -> str | None:
    time_tag = container.find("time") if container else None
    if time_tag and (time_tag.get("datetime") or time_tag.text):
        return _text_or_none(time_tag.get("datetime") or time_tag.text)

    date_candidate = None
    if container:
        date_candidate = container.find(
            ["span", "p"],
            class_=lambda value: value and "date" in value.lower(),
        )
    if date_candidate:
        return _text_or_none(date_candidate.get_text())

    return None


def _iter_article_candidates(soup: "BeautifulSoup") -> Iterable:
    articles = soup.find_all("article")
    if articles:
        return articles
    main_section = soup.find("main") or soup
    return main_section.find_all(["div", "section"])


def parse_latest_news(html: str, base_url: str, max_items: int) -> list[dict[str, str | None]]:
    ensure_dependencies()
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, str | None]] = []
    seen_urls: set[str] = set()

    for candidate in _iter_article_candidates(soup):
        title_tag = candidate.find(["h1", "h2", "h3", "h4"])
        if not title_tag:
            continue
        link_tag = title_tag.find("a") or candidate.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
        url = urljoin(base_url, link_tag["href"])
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = _text_or_none(title_tag.get_text())
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": url,
                "date": _extract_date(candidate),
            }
        )
        if len(items) >= max_items:
            return items

    # Fallback: anchor scanning
    for link_tag in soup.find_all("a"):
        text = _text_or_none(link_tag.get_text())
        href = link_tag.get("href")
        if not text or not href:
            continue
        if len(text) < 10:
            continue
        url = urljoin(base_url, href)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        items.append({"title": text, "url": url, "date": None})
        if len(items) >= max_items:
            break

    return items


def fetch_latest_news(url: str, max_items: int) -> list[dict[str, str | None]]:
    html = fetch_html(url)
    return parse_latest_news(html, url, max_items)


def format_output(items: list[dict[str, str | None]]) -> str:
    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "items": items,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def run_once(url: str, max_items: int, output_path: str | None) -> None:
    items = fetch_latest_news(url, max_items)
    output = format_output(items)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(output)
        logging.info("Resultados guardados en %s", output_path)
    else:
        print(output)


def run_daily(url: str, max_items: int, output_path: str | None, daily_at: str) -> None:
    if schedule is None:
        raise DependencyError(
            "Falta la dependencia schedule. Instala con: pip install -r requirements.txt"
        )

    def job() -> None:
        logging.info("Ejecutando scraper diario...")
        run_once(url, max_items, output_path)

    schedule.every().day.at(daily_at).do(job)
    logging.info("Programado para ejecutarse diariamente a las %s", daily_at)

    while True:
        schedule.run_pending()
        time.sleep(1)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scraper diario para la sección de comunicación social del INE. "
            "Por defecto se ejecuta en modo diario."
        )
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="URL base del INE")
    parser.add_argument("--max-items", type=int, default=10, help="Número máximo de noticias")
    parser.add_argument("--output", help="Ruta para guardar el JSON")
    parser.add_argument(
        "--daily-at",
        default="08:00",
        help="Hora local para ejecución diaria (HH:MM)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecutar una sola vez y salir",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Nivel de logging (DEBUG, INFO, WARNING)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        if args.once:
            run_once(args.url, args.max_items, args.output)
        else:
            run_daily(args.url, args.max_items, args.output, args.daily_at)
    except DependencyError as exc:
        logging.error("%s", exc)
        return 1
    except Exception:
        logging.exception("Error ejecutando el scraper")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
