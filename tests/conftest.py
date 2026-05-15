import pytest


@pytest.fixture(scope="session", autouse=True)
def add_translator():
    """Mock the translation function to return the input string."""
    import builtins
    builtins._ = lambda x: x
    yield
