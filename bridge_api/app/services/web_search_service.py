from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import requests

from app.config import settings
from app.models.schemas import Source


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebSearchResult:
    enabled: bool
    provider: str
    sources: list[Source] = field(default_factory=list)
    message: str = ""


class WebSearchService:
    provider_keys = {
        "tavily": "TAVILY_API_KEY",
        "serpapi": "SERPAPI_API_KEY",
        "brave": "BRAVE_API_KEY",
        "bing": "BING_SEARCH_API_KEY",
    }

    def configured_provider(self) -> tuple[str, str]:
        preferred = settings.web_search_provider.strip().lower() or "tavily"
        ordered = [preferred] + [provider for provider in self.provider_keys if provider != preferred]
        for provider in ordered:
            key = os.getenv(self.provider_keys[provider], "").strip()
            if key:
                return provider, key
        return preferred, ""

    def search(self, query: str, max_results: int | None = None) -> WebSearchResult:
        clean_query = str(query or "").strip()
        provider, api_key = self.configured_provider()
        if not clean_query:
            return WebSearchResult(False, provider, message="Consulta vacia para busqueda web.")
        if not api_key:
            return WebSearchResult(
                False,
                provider,
                message=(
                    "Busqueda inteligente activada, pero falta configurar una clave "
                    "TAVILY_API_KEY, SERPAPI_API_KEY, BRAVE_API_KEY o BING_SEARCH_API_KEY."
                ),
            )

        limit = max(1, min(max_results or settings.web_search_max_results, 10))
        try:
            if provider == "serpapi":
                raw_results = self._search_serpapi(clean_query, api_key, limit)
            elif provider == "brave":
                raw_results = self._search_brave(clean_query, api_key, limit)
            elif provider == "bing":
                raw_results = self._search_bing(clean_query, api_key, limit)
            else:
                raw_results = self._search_tavily(clean_query, api_key, limit)
        except Exception as exc:
            LOGGER.warning("Web search failed provider=%s query=%s: %s", provider, clean_query, exc)
            return WebSearchResult(False, provider, message=f"No se pudo completar la busqueda web con {provider}.")

        sources = self._to_sources(raw_results, provider, limit)
        return WebSearchResult(
            enabled=bool(sources),
            provider=provider,
            sources=sources,
            message="Busqueda web completada." if sources else "La busqueda web no devolvio resultados utiles.",
        )

    def _search_tavily(self, query: str, api_key: str, limit: int) -> list[dict[str, Any]]:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": limit,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=settings.web_search_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results") or []

    def _search_serpapi(self, query: str, api_key: str, limit: int) -> list[dict[str, Any]]:
        response = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google", "q": query, "api_key": api_key, "num": limit, "hl": "es"},
            timeout=settings.web_search_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("organic_results") or []

    def _search_brave(self, query: str, api_key: str, limit: int) -> list[dict[str, Any]]:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": query, "count": limit, "search_lang": "es"},
            timeout=settings.web_search_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        web = data.get("web") if isinstance(data.get("web"), dict) else {}
        return web.get("results") or []

    def _search_bing(self, query: str, api_key: str, limit: int) -> list[dict[str, Any]]:
        response = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers={"Ocp-Apim-Subscription-Key": api_key},
            params={"q": query, "count": limit, "mkt": "es-US"},
            timeout=settings.web_search_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        web_pages = data.get("webPages") if isinstance(data.get("webPages"), dict) else {}
        return web_pages.get("value") or []

    def _to_sources(self, results: list[dict[str, Any]], provider: str, limit: int) -> list[Source]:
        sources: list[Source] = []
        for index, item in enumerate(results, start=1):
            title = str(item.get("title") or item.get("name") or "").strip()
            url = str(item.get("url") or item.get("link") or "").strip()
            snippet = str(item.get("snippet") or item.get("description") or item.get("content") or "").strip()
            if not (title or url or snippet):
                continue
            sources.append(
                Source(
                    source=url or f"web:{provider}:{index}",
                    title=title or url or f"Resultado web {index}",
                    type="web",
                    url=url,
                    score=None,
                    text=snippet[:900],
                    metadata={"provider": provider, "rank": index},
                )
            )
            if len(sources) >= limit:
                break
        return sources


web_search_service = WebSearchService()
