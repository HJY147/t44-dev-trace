"""Strict SQLGlot-token CHECK prototype; no production import."""

import re

import sqlglot
from sqlglot import exp

from t44.persistence.schema import TABLES

_ALLOWED = {
    type(node)
    for table in TABLES.values()
    for check in table.constraints
    if type(check).__name__ == "CheckConstraint"
    for node in sqlglot.parse_one(str(check.sqltext), read="mysql").walk()
}
_LEXEME = re.compile(r"`[^`]+`|'(?:''|\\.|[^'])*'|[a-zA-Z_]\w*|\d+|<=|>=|<>|!=|[=<>+(),-]")


def check_signature(expression):
    source = str(expression).strip()
    try:
        tokens = sqlglot.tokenize(source, read="mysql")
        words = [source[token.start : token.end + 1] for token in tokens]
        if any(t.comments or not _LEXEME.fullmatch(w) for t, w in zip(tokens, words, strict=True)):
            return None
        if re.sub(r"\s", "", source) != re.sub(r"\s", "", "".join(words)):
            return None
        words = [w if w.startswith("'") else w.strip("`").lower() for w in words]
        if any(w == "not" and (i == 0 or words[i - 1] != "is") for i, w in enumerate(words)):
            return None
        if any(
            w in ("+", "-")
            and (
                i == 0
                or words[i - 1] in ("(", ",", "+", "-", "=", "<", ">", "<=", ">=", "<>", "!=")
            )
            for i, w in enumerate(words)
        ):
            return None
        trees = sqlglot.parse(source, read="mysql", error_level=sqlglot.ErrorLevel.RAISE)
        if len(trees) != 1 or trees[0] is None:
            return None

        def canonical(node):
            if isinstance(node, exp.Paren):
                return canonical(node.this)
            if isinstance(node, exp.Introducer):
                if (
                    node.this.lower() not in ("_ascii", "_utf8mb4")
                    or not isinstance(node.expression, exp.Literal)
                    or node.this.lower() == "_ascii"
                    and not node.expression.this.isascii()
                ):
                    raise ValueError("Unsupported literal introducer")
                return canonical(node.expression)
            if isinstance(node, exp.Identifier):
                return node.name.lower()
            if isinstance(node, exp.Expression):
                if type(node) not in _ALLOWED:
                    raise ValueError("Unsupported CHECK node")
                return type(node).__name__, tuple(
                    (key, canonical(value))
                    for key, value in sorted(node.args.items())
                    if value is not None
                )
            if isinstance(node, list):
                return tuple(canonical(value) for value in node)
            return node.lower() if isinstance(node, str) else node

        raw = tuple(
            w
            for i, w in enumerate(words)
            if w.startswith("'")
            or i + 1 < len(words)
            and words[i + 1] == "("
            and re.fullmatch(r"[a-zA-Z_]\w*", w)
            and w not in ("and", "or", "in")
        )
        return canonical(trees[0]), raw
    except (sqlglot.errors.SqlglotError, ValueError):
        return None
