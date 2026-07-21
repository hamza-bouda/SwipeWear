#!/usr/bin/env python3
"""
Import boundary checker — enforces the anti-spaghetti rule from blueprint §11:
  A module may only import from another module's interfaces.py or from contracts/.
  Importing any other file of a sibling module is forbidden.

Usage: python backend/lint_imports.py
Returns exit code 1 if violations are found (used in CI).
"""
import ast
import sys
from pathlib import Path

BACKEND = Path(__file__).parent
MODULES = [
    "contracts", "ingestion", "vision", "embeddings", "preferences",
    "retrieval", "ranking", "policy", "explainability", "evaluation", "orchestration",
    "api",
]
MODULE_SET = set(MODULES)

violations: list[str] = []

for module in MODULES:
    module_dir = BACKEND / module
    for py_file in module_dir.rglob("*.py"):
        if "tests" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                if len(parts) < 2:
                    continue
                target_module = parts[0]
                target_subpath = parts[1] if len(parts) > 1 else ""
                if target_module not in MODULE_SET or target_module == module:
                    continue
                # allow imports from contracts (always ok)
                if target_module == "contracts":
                    continue
                # allow imports of interfaces only
                if target_subpath != "interfaces":
                    rel = py_file.relative_to(BACKEND)
                    violations.append(
                        f"{rel}:{node.lineno} — forbidden import of "
                        f"'{name}' (only '{target_module}.interfaces' is allowed)"
                    )

if violations:
    print("Import boundary violations found:")
    for v in violations:
        print(f"  ERROR: {v}")
    sys.exit(1)
else:
    print("Import boundary check passed.")
    sys.exit(0)
