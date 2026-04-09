import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_PARENT = str(ROOT_DIR)

if SRC_PARENT not in sys.path:
    sys.path.insert(0, SRC_PARENT)
