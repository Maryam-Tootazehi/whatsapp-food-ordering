import restaurant_assistant


def test_package_imports_and_has_a_version() -> None:
    assert restaurant_assistant.__version__ == "0.1.0"
