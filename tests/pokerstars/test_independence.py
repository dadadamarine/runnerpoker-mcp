"""The pokerstars package must stay liftable into its own project."""

import ast
import sys
from pathlib import Path

import runnerpoker_mcp.pokerstars as package

PACKAGE_DIR = Path(package.__file__).parent


def imports_of(path: Path) -> list[tuple[int, str | None]]:
    """(relative level, module) for every import statement in a source file."""
    found: list[tuple[int, str | None]] = []
    for node in ast.walk(ast.parse(path.read_text("utf-8"))):
        if isinstance(node, ast.Import):
            found += [(0, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append((node.level, node.module))
    return found


def test_package_imports_only_the_standard_library_and_itself():
    for path in PACKAGE_DIR.glob("*.py"):
        for level, module in imports_of(path):
            if level == 1:
                continue
            assert level == 0, f"{path.name} imports from a parent package"
            assert module is not None
            assert module.split(".")[0] in sys.stdlib_module_names, f"{path.name} imports {module}"
