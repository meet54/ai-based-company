"""AI Company — run the CEO command center."""

import socket
import sys

import uvicorn

from src.config import settings


def _port_in_use(port: int, host: str) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True


if __name__ == "__main__":
    mode_labels = {
        "real": f"REAL AI — {settings.active_provider.upper()} ({settings.active_model})",
        "demo": "DEMO MODE (simulated responses)",
        "missing_key": f"API KEY MISSING for {settings.llm_provider.upper()}",
    }
    print(f"\n  AI Company: {settings.company_name}")
    print(f"  CEO: {settings.ceo_name}")
    print(f"  Mode: {mode_labels[settings.ai_mode]}")
    if settings.ai_mode == "missing_key":
        print("  >> Add OPENAI_API_KEY to .env and restart\n")
    else:
        print(f"  >> http://localhost:{settings.port}\n")

    if _port_in_use(settings.port, settings.host):
        print(f"  !! Port {settings.port} is already in use — another server is running.")
        print(f"  >> Open http://localhost:{settings.port} in your browser (no need to start again).")
        print("  >> To restart, stop the old process first:")
        print(f"       netstat -ano | findstr \":{settings.port}\"")
        print("       Stop-Process -Id <PID> -Force\n")
        sys.exit(1)

    uvicorn.run(
        "src.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
