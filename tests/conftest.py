import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data_loader import load_dataset  # noqa: E402


@pytest.fixture(scope="session")
def ds():
    d = load_dataset()
    assert d.valid, [c for c in d.checks if c.status == "fail"]
    return d
