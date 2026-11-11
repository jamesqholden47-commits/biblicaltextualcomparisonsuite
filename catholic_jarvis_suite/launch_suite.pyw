"""
Launcher for CatholicJarvis Ultra Master Work Suite
Gracefully detects if server is running, falls back to open ports without killing alien processes,
and opens browser in dedicated native App Window mode.
"""

import os
import sys
import time
import socket
import json
import subprocess
import urllib.request
import webbrowser

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
PORT_FILE = os.path.join(DATA_DIR, "port.txt")

CANDIDATE_PORTS = [8080, 8081, 8082, 8083, 8084, 8085]

def is_our_server(port: int) -> bool:
    """Check if CatholicJarvis is already responding on the specified port."""
    try:
        url = f"http://127.0.0.1:{port}/api/health"
        req = urllib.request.Request(url, headers={"User-Agent": "CatholicJarvisLauncher"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("app") == "CatholicJarvis Master Work Suite"
    except Exception:
        pass
    return False

def is_port_available(port: int) -> bool:
    """Test if a local TCP port is free to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def select_port() -> int:
    # 1. First check if our server is already running on any candidate port
    for p in CANDIDATE_PORTS:
        if is_our_server(p):
            return p

    # 2. Check previously saved port if free
    if os.path.exists(PORT_FILE):
        try:
            with open(PORT_FILE, "r") as pf:
                saved_port = int(pf.read().strip())
                if is_port_available(saved_port):
                    return saved_port
        except Exception:
            pass

    # 3. Find the first available port
    for p in CANDIDATE_PORTS:
        if is_port_available(p):
            return p

    return 8080

def main():
    target_port = select_port()
    url = f"http://127.0.0.1:{target_port}"

    # Start server if not already running
    if not is_our_server(target_port):
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        cmd = [sys.executable, "app.py", "--port", str(target_port)]
        subprocess.Popen(cmd, cwd=APP_DIR, creationflags=creationflags)

        # Wait up to 10 seconds for server health check
        started = False
        for _ in range(20):
            time.sleep(0.5)
            if is_our_server(target_port):
                started = True
                break

    # Save active port
    try:
        with open(PORT_FILE, "w", encoding="utf-8") as pf:
            pf.write(str(target_port))
    except Exception:
        pass

    # Launch browser in standalone App Mode
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]

    launched = False
    for b_path in edge_paths:
        if os.path.exists(b_path):
            subprocess.Popen([b_path, f"--app={url}", "--window-size=1520,980"])
            launched = True
            break

    if not launched:
        webbrowser.open(url)

if __name__ == "__main__":
    main()
