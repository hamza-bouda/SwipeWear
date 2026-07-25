"""Guard against SQL that references columns the migrations never create.

Why this test exists: retrieval is unit-tested entirely against mocked
cursors and the golden scenario builds its products in memory, so neither
ever compares a query to the real schema. That gap let the vector retriever
ship with a SELECT over six non-existent columns, and reading `embedding`
from `products` when the vectors live in `product_embeddings` — the feed
returned nothing in production while every test stayed green.

The migrations are parsed rather than a live database queried so this runs
in CI with no Postgres.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations"

# Lines inside CREATE TABLE (...) that declare a constraint, not a column.
_NOT_A_COLUMN = re.compile(
    r"^(PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT|EXCLUDE)\b", re.IGNORECASE,
)
_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\n\);",
    re.IGNORECASE | re.DOTALL,
)
_ADD_COLUMN = re.compile(
    r"ALTER\s+TABLE\s+(\w+)(.*?);", re.IGNORECASE | re.DOTALL,
)
_ADD_COLUMN_NAME = re.compile(
    r"ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", re.IGNORECASE,
)


def _split_top_level(body: str) -> list[str]:
    """Split a CREATE TABLE body on commas outside parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def schema_from_migrations() -> dict[str, set[str]]:
    """Return {table: {column, …}} as the migrations would leave the database."""
    schema: dict[str, set[str]] = {}
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")

        for table, body in _CREATE_TABLE.findall(sql):
            columns = schema.setdefault(table.lower(), set())
            for part in _split_top_level(body):
                line = part.strip()
                if not line or line.startswith("--") or _NOT_A_COLUMN.match(line):
                    continue
                columns.add(line.split()[0].lower())

        for table, statement in _ADD_COLUMN.findall(sql):
            columns = schema.setdefault(table.lower(), set())
            for name in _ADD_COLUMN_NAME.findall(statement):
                columns.add(name.lower())

    return schema


@pytest.fixture(scope="module")
def schema() -> dict[str, set[str]]:
    return schema_from_migrations()


def test_migrations_are_parsable(schema):
    """Sanity check: the parser found the tables the pipeline depends on."""
    assert "products" in schema
    assert "product_embeddings" in schema
    assert "id" in schema["products"]
    assert "embedding" in schema["product_embeddings"]


def _iter_source_files() -> list[Path]:
    """Every backend source file, excluding tests and virtualenvs."""
    return [
        p for p in BACKEND_DIR.rglob("*.py")
        if "tests" not in p.parts
        and not any(part.startswith((".", "__pycache__")) for part in p.parts)
    ]


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(BACKEND_DIR).with_suffix("").parts)


def _discover_column_constants() -> list[tuple[str, str, tuple[str, ...]]]:
    """Find every module-level `*COLUMNS` list of string literals.

    Discovery rather than a hand-maintained list: the first version of this
    guard enumerated four modules by name and therefore sailed straight past
    retrieval/ladder.py, which carried the very same defect. A new module now
    has to opt out explicitly instead of being missed by default.

    Parsed statically so importing a module's dependencies is never required.
    """
    found: list[tuple[str, str, tuple[str, ...]]] = []
    for path in _iter_source_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - a broken file fails elsewhere
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if not target.id.upper().endswith("COLUMNS"):
                    continue
                if not isinstance(node.value, (ast.List, ast.Tuple)):
                    continue
                values = [
                    el.value for el in node.value.elts
                    if isinstance(el, ast.Constant) and isinstance(el.value, str)
                ]
                if len(values) == len(node.value.elts) and values:
                    found.append(
                        (_module_name(path), target.id, tuple(values))
                    )
    return found


# Column constants that deliberately describe a table other than products.
# Anything not listed here is checked against the products schema, so a new
# constant fails this test until it is either correct or classified.
_NOT_PRODUCTS_COLUMNS: frozenset[tuple[str, str]] = frozenset()

_DISCOVERED = _discover_column_constants()


def test_discovery_found_the_known_column_constants():
    """The AST walk must actually be finding constants — an empty sweep
    would make every assertion below vacuously pass."""
    names = {(mod, attr) for mod, attr, _ in _DISCOVERED}
    assert ("retrieval.retriever", "_PRODUCT_COLUMNS") in names
    assert ("retrieval.ladder", "_PRODUCT_COLUMNS") in names


@pytest.mark.parametrize(
    "module_path, attribute, columns",
    [pytest.param(m, a, c, id=f"{m}.{a}") for m, a, c in _DISCOVERED],
)
def test_selected_columns_exist_in_products(schema, module_path, attribute, columns):
    """Every column a query selects from products must exist in the schema."""
    if (module_path, attribute) in _NOT_PRODUCTS_COLUMNS:
        pytest.skip(f"{module_path}.{attribute} targets another table")

    missing = sorted({c.lower() for c in columns} - schema["products"])
    assert missing == [], (
        f"{module_path}.{attribute} selects column(s) absent from the products "
        f"table: {missing}. Add a migration, drop them from the query, or list "
        f"the constant in _NOT_PRODUCTS_COLUMNS if it describes another table."
    )


def test_cosine_queries_join_the_embeddings_table():
    """Any pgvector distance term must reach embeddings via product_embeddings.

    products has no embedding column; querying it produced an UndefinedColumn
    at runtime that only the fallback path masked. Checking every `<=>` literal
    in the backend catches the next module to make the same assumption.
    """
    offenders: list[str] = []
    for path in _iter_source_files():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            sql = node.value
            if "<=>" not in sql:
                continue
            if "product_embeddings" not in sql:
                offenders.append(f"{_module_name(path)}:{node.lineno}")
    assert offenders == [], (
        "cosine-distance SQL that never joins product_embeddings: "
        f"{offenders}. The vectors do not live in products."
    )
