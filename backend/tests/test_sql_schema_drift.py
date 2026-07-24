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


@pytest.mark.parametrize(
    "module_path, attribute",
    [
        ("retrieval.retriever", "_PRODUCT_COLUMNS"),
        ("retrieval.fallback", "_DB_COLUMNS"),
        ("api.pipeline", "_SAMPLE_COLUMNS"),
        ("scripts.run_indexer", "_COLUMNS"),
    ],
)
def test_selected_columns_exist_in_products(schema, module_path, attribute):
    """Every column a query selects from products must exist in the schema."""
    import importlib

    module = importlib.import_module(module_path)
    selected = {c.lower() for c in getattr(module, attribute)}
    missing = sorted(selected - schema["products"])
    assert missing == [], (
        f"{module_path}.{attribute} selects column(s) absent from the products "
        f"table: {missing}. Add a migration or drop them from the query."
    )


def test_vector_search_reads_embedding_from_its_own_table():
    """The similarity term must come from product_embeddings, not products.

    products has no embedding column; querying it produced an UndefinedColumn
    at runtime that only the fallback path masked.
    """
    from retrieval.retriever import _QUERY_TEMPLATE

    assert "product_embeddings" in _QUERY_TEMPLATE
    assert "JOIN" in _QUERY_TEMPLATE.upper()
    assert "e.embedding" in _QUERY_TEMPLATE
