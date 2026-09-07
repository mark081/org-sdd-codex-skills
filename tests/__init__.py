"""Repository tests; import the installable organizational package explicitly."""
import sys
from pathlib import Path

ORG_SKILL = Path(__file__).resolve().parents[1] / "coordinate-org-sdd"
sys.path.insert(0, str(ORG_SKILL / "src"))
