"""Vercel entrypoint for the Dash application."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src" / "dashboard"), str(ROOT / "src")]

from app import server as app
