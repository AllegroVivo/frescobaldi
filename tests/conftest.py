import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _setup():
    """Mock the translation function to return the input string."""
    # Add translation function to builtins
    import builtins
    builtins._ = lambda x: x

    # Add the package path to sys.path so that imports work correctly
    from frescobaldi import __path__ as path
    sys.path[0:0] = map(os.path.abspath, path)
    del path[:]
    yield
