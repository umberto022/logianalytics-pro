#!/usr/bin/env python3
"""
LogiAnalytics Pro — ejecuta la web (Streamlit) y la API (FastAPI) en paralelo.
"""

import os
import signal
import subprocess
import sys
import time
import webbrowser
from multiprocessing import Process

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.join(_BASE_DIR, "LogiAnalytics_Pro_Complete")
_STREAMLIT_APP = os.path.join(_PROJECT_DIR, "src", "app.py")
_STREAMLIT_CWD = os.path.join(_PROJECT_DIR, "src")
_API_DIR = os.path.join(_PROJECT_DIR, "src", "api")


def run_streamlit() -> None:
    print("Iniciando aplicacion web Streamlit...")
    if not os.path.isfile(_STREAMLIT_APP):
        print(f"ERROR: No existe {_STREAMLIT_APP}")
        sys.exit(1)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            _STREAMLIT_APP,
            "--server.port",
            "8501",
            "--server.address",
            "0.0.0.0",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=_STREAMLIT_CWD,
    )


def run_api() -> None:
    print("Iniciando API FastAPI...")
    main_py = os.path.join(_API_DIR, "main.py")
    if not os.path.isfile(main_py):
        print(f"ERROR: No existe {main_py}")
        sys.exit(1)
    subprocess.run([sys.executable, "main.py"], cwd=_API_DIR)


def signal_handler(sig, frame) -> None:
    print("\nDeteniendo servicios...")
    sys.exit(0)


def main() -> None:
    print(
        """
LogiAnalytics Pro
==================
Web:    http://localhost:8501
API:    http://localhost:8000
Docs:   http://localhost:8000/docs

Ctrl+C para detener.
"""
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    streamlit_process: Process | None = None
    api_process: Process | None = None

    try:
        streamlit_process = Process(target=run_streamlit)
        api_process = Process(target=run_api)

        streamlit_process.start()
        time.sleep(3)
        try:
            webbrowser.open("http://localhost:8501")
        except OSError:
            pass
        api_process.start()

        streamlit_process.join()
        api_process.join()

    except KeyboardInterrupt:
        print("\nDeteniendo servicios...")
        if streamlit_process is not None:
            streamlit_process.terminate()
            streamlit_process.join(timeout=5)
        if api_process is not None:
            api_process.terminate()
            api_process.join(timeout=5)
        print("Servicios detenidos.")


if __name__ == "__main__":
    main()
