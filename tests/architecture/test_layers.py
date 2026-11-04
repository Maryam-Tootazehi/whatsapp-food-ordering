"""Guard the hexagonal structure: inner layers must not import outer layers or frameworks.

Reads every module's import statements with the ast module, so it needs no extra dependency
and fails with a message that names the file and the import.
"""

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).parents[2] / "src" / "restaurant_assistant"

FRAMEWORKS = {
    "fastapi", "starlette", "pydantic", "langgraph", "langchain", "langchain_core",
    "openai", "supabase", "postgrest", "psycopg", "sqlalchemy", "httpx", "requests",
}  # fmt: skip

# layer -> names it may never import
FORBIDDEN = {
    "domain": FRAMEWORKS
    | {
        "restaurant_assistant.application",
        "restaurant_assistant.storage",
        "restaurant_assistant.interfaces",
    },
    "application": FRAMEWORKS | {"restaurant_assistant.storage", "restaurant_assistant.interfaces"},
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def is_forbidden(module: str, forbidden: set[str]) -> bool:
    return any(module == f or module.startswith(f + ".") for f in forbidden)


@pytest.mark.parametrize("layer", sorted(FORBIDDEN))
def test_layer_does_not_import_outer_layers_or_frameworks(layer: str) -> None:
    violations = [
        f"{path.relative_to(PACKAGE)} imports {module}"
        for path in sorted((PACKAGE / layer).rglob("*.py"))
        for module in sorted(imported_modules(path))
        if is_forbidden(module, FORBIDDEN[layer])
    ]
    assert not violations, "Layer rule broken:\n" + "\n".join(violations)


def test_the_guard_itself_catches_a_violation(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("from fastapi import FastAPI\nimport restaurant_assistant.storage.x\n")
    found = {m for m in imported_modules(bad) if is_forbidden(m, FORBIDDEN["domain"])}
    assert found == {"fastapi", "restaurant_assistant.storage.x"}
