from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

try:
    import requests
except Exception:
    requests = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.brain_connector import BrainConnector


def http_ok(url: str, timeout: int = 3) -> tuple[bool, str]:
    try:
        if requests is not None:
            response = requests.get(url, timeout=timeout)
            return response.ok, f"HTTP {response.status_code}"
        request = Request(url, headers={"User-Agent": "ABRAHAM-BrainCheck/1.0"})
        with urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except Exception as exc:
        return False, str(exc)


def line(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "WARN"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")


def main() -> int:
    brain_root = Path(os.getenv("BRAIN_ROOT", r"C:\Users\herna\Documents\tutor_ia"))
    streamlit_url = os.getenv("STREAMLIT_URL", "http://127.0.0.1:8501")
    bridge_url = os.getenv("BRIDGE_API_URL", "http://127.0.0.1:8787")

    connector = BrainConnector(brain_root=brain_root, bridge_api_url=bridge_url)
    health = connector.health_check()

    line("Proyecto ABRAHAM", PROJECT_ROOT.exists(), str(PROJECT_ROOT))
    line("Cerebro local tutor_ia", brain_root.exists(), str(brain_root))
    line("Asistente web", (PROJECT_ROOT / "asistente-programacion.html").exists(), "asistente-programacion.html")

    streamlit_running, streamlit_detail = http_ok(streamlit_url)
    line("Streamlit responde", streamlit_running, streamlit_detail)

    bridge_ok = bool(health.get("bridge_api", {}).get("connected"))
    line("Bridge API", bridge_ok, bridge_url)

    anthropic_ok = bool(health.get("anthropic", {}).get("configured"))
    line("Anthropic", anthropic_ok, health.get("anthropic", {}).get("model", ""))

    probe = connector.answer(
        "Responde en una frase: estas conectado al asistente de programacion?",
        options={"fast_mode": True, "bridge_api": True, "anthropic": False},
    )
    line("BrainConnector responde", bool(probe.get("answer")), ", ".join(probe.get("sources_used", [])))

    fallback = connector.fallback_answer("Prueba de fallback")
    line("Fallback", bool(fallback), fallback[:90])

    return 0 if brain_root.exists() and (PROJECT_ROOT / "asistente-programacion.html").exists() and probe.get("answer") and fallback else 1


if __name__ == "__main__":
    raise SystemExit(main())
