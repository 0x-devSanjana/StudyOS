import os
import sys
import subprocess
import webbrowser
from pathlib import Path

root = Path(__file__).resolve().parent
os.chdir(root)

requirements = root / "requirements.txt"
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

webbrowser.open("http://127.0.0.1:5000")
subprocess.call([sys.executable, "app.py"])
