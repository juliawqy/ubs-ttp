"""
Pytest configuration for recruitment service tests.
Adds services/ to sys.path so `from shared.x import y` resolves both
locally (pytest from repo root) and inside Docker (/app/shared).
"""
import sys
from pathlib import Path

services_dir = Path(__file__).resolve().parents[2]
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))
