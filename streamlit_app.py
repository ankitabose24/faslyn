# ===========================================================================
# Faslyn — Production Root Entrypoint (streamlit_app.py)
# Seamlessly executes frontend/app.py across Streamlit Cloud, Docker & Local
# ===========================================================================
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

target_app = ROOT_DIR / "frontend" / "app.py"

import runpy
runpy.run_path(str(target_app), run_name="__main__")
