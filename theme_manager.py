from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

THEME_FILE = Path("theme.json")

def default_theme() -> Dict:
    return {
        "ACCENT_BLUE": "#0858FF",
        "DARK_BG": "#000000",
        "PANEL_BG": "#070A0F",
        "CARD_BG": "#0E1420",
        "TEXT": "#FFFFFF",
        "MUTED": "#B9C2D0",
        "BORDER": "rgba(255,255,255,0.12)",
        "GRID_DAILY": "rgba(255,255,255,0.18)",
        "GRID_WEEKLY": "rgba(255,255,255,0.40)",
        "EMPTY_WEEKDAY": "#0B0F14",
        "EMPTY_WEEKEND": "#1A1F2A",
        "TABLE_BORDER": "rgba(255,255,255,0.20)",
        # Chart-specific overrides
        "CHART_BG": "#0A0F16",      # timeline pane background
        "TABLE_BG": "#101825",      # left grid background
        "HEADER_TEXT": "#FFFFFF",
        "AXIS_TEXT": "#B9C2D0",
        # NEW: pixel nudge to align table header with graph header
        "HEADER_ALIGN_YSHIFT": 30,
        "STATUS_COLORS": {
            "Completed": "#2ECC71",
            "In progress": "#0858FF",
            "Not started": "#6C7A89",
            "Overdue": "#FF4B4B",
            "Unknown": "#9B59B6",
        },
    }


def load_theme(path: str | None = None) -> Dict:
    file = Path(path) if path else THEME_FILE
    if file.exists():
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            t = default_theme()
            for k, v in data.items():
                if k == "STATUS_COLORS" and isinstance(v, dict):
                    t["STATUS_COLORS"].update(v)
                else:
                    t[k] = v
            return t
        except Exception:
            pass
    return default_theme()


def save_theme(theme: Dict, path: str | None = None) -> None:
    file = Path(path) if path else THEME_FILE
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(theme, f, indent=2)
    except Exception:
        pass
