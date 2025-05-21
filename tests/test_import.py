import importlib.metadata


def test_import() -> None:
    version = importlib.metadata.version("tornet-mp")
    assert isinstance(version, str) and len(version) > 0
