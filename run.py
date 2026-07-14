"""
Single-script launcher for the Autonomous Research Agent.

Starts the FastAPI backend (port 8003), Streamlit UI (port 8501), and a static file server for the frontend (port 3000).
Press Ctrl+C to shut down.

Usage:
    uv run python run.py
"""

import argparse
import os
import signal
import subprocess
import sys
import time
import http.server
import socketserver
import threading

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
BACKEND_PORT = 8003
FRONTEND_PORT = 3000


def start_backend(host: str = "0.0.0.0", port: int = BACKEND_PORT):
    """Launch the FastAPI backend via uvicorn."""
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


def start_frontend(port: int = FRONTEND_PORT):
    """Serve the static HTML frontend."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=FRONTEND_DIR, **kwargs)
        def log_message(self, format, *args):
            pass # Suppress frontend logs for cleaner console

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print(f"Frontend server failed to start: {e}")


def start_streamlit():
    """Launch the Streamlit UI as a subprocess."""
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
         "--server.headless", "true"],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL, # Suppress streamlit logs for cleaner console
        stderr=subprocess.DEVNULL
    )


def main():
    print("=" * 60)
    print("  Autonomous Research Agent - Launcher")
    print("=" * 60)
    print(f"  Frontend UI        -> http://localhost:{FRONTEND_PORT}  <-- USE THIS FOR RESEARCH")
    print(f"  Streamlit UI       -> http://localhost:8501  <-- USE THIS FOR DEBUGGING")
    print(f"  Backend API        -> http://localhost:{BACKEND_PORT}")
    print(f"  API docs           -> http://localhost:{BACKEND_PORT}/docs\n")

    processes = []
    threads = []

    # Streamlit
    proc = start_streamlit()
    processes.append(proc)
    
    # Frontend
    t = threading.Thread(target=start_frontend, daemon=True)
    t.start()
    threads.append(t)
    
    time.sleep(0.3)

    def _shutdown(sig, frame):
        print("\n\n  Shutting down...")
        for p in processes:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        start_backend()
    except KeyboardInterrupt:
        _shutdown(None, None)

if __name__ == "__main__":
    main()
