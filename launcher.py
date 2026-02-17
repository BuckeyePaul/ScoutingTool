import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from waitress import serve

from app import app


def _set_working_directory():
    if getattr(sys, 'frozen', False):
        os.chdir(Path(sys.executable).parent)
    else:
        os.chdir(Path(__file__).parent)


def _open_browser_when_ready(url: str):
    time.sleep(1.2)
    webbrowser.open(url)


def main():
    _set_working_directory()
    local_url = 'http://127.0.0.1:5000'
    print('Starting NFL Draft Scout Assistant...')
    print(f'Opening {local_url}')

    threading.Thread(target=_open_browser_when_ready, args=(local_url,), daemon=True).start()
    serve(app, host='127.0.0.1', port=5000, threads=8)


if __name__ == '__main__':
    main()
