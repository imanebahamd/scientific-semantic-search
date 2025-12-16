"""
Package de données pour Scientific Semantic Search.
"""

from pathlib import Path

# Chemins des répertoires de données
DATA_DIR = Path(__file__).parent
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
SCRIPTS_DIR = DATA_DIR / "scripts"

__all__ = ['DATA_DIR', 'RAW_DIR', 'CLEANED_DIR', 'SCRIPTS_DIR']
