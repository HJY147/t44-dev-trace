"""Core metadata generated from the immutable, reviewed MySQL DDL, not a second field list."""

import hashlib
import re
from importlib.resources import files

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import mysql

SCHEMA_VERSION = 1
DDL_SHA256 = "c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4"


def ddl_text() -> str:
    content = files(__package__).joinpath("schema_v1.sql").read_text(encoding="utf-8")
    if hashlib.sha256(content.encode()).hexdigest() != DDL_SHA256:
        raise RuntimeError("Packaged migration checksum does not match frozen v1")
    return content


def _parts(body: str) -> list[str]:
    """Split hash-verified DDL at its four-space declaration boundaries."""
    return [part.strip() for part in re.split(r",\n    (?=\S)", body)]


def _type(spec: str):
    match = re.match(
        r"(INT|TINYINT|SMALLINT|MEDIUMINT|VARCHAR|CHAR|BINARY|DATETIME|JSON)(?:\((\d+)\))?", spec
    )
    if match is None:
        raise RuntimeError("Unsupported type in frozen DDL")
    name, size = match.groups()
    if name in ("INT", "TINYINT", "SMALLINT", "MEDIUMINT"):
        cls = mysql.INTEGER if name == "INT" else getattr(mysql, name)
        return cls(unsigned=True).with_variant(Integer(), "sqlite")
    if name in ("VARCHAR", "CHAR"):
        opts = {"charset": "ascii", "collation": "ascii_bin"} if "ascii_bin" in spec else {}
        return getattr(mysql, name)(int(size), **opts).with_variant(String(int(size)), "sqlite")
    if name == "BINARY":
        return mysql.BINARY(int(size)).with_variant(LargeBinary(int(size)), "sqlite")
    if name == "DATETIME":
        return mysql.DATETIME(fsp=int(size)).with_variant(DateTime(), "sqlite")
    return mysql.JSON(none_as_null=True).with_variant(JSON(none_as_null=True), "sqlite")


def _foreign_key(part: str) -> ForeignKeyConstraint:
    name, columns, parent, targets = re.fullmatch(
        r"CONSTRAINT (\w+) FOREIGN KEY \(([^)]+)\) REFERENCES (\w+)\(([^)]+)\)", part
    ).groups()
    return ForeignKeyConstraint(
        columns.split(","), [f"{parent}.{c}" for c in targets.split(",")], name=name
    )


def build_metadata() -> MetaData:
    metadata = MetaData()
    sql = ddl_text()
    for name, body in re.findall(r"CREATE TABLE (\w+) \(\n(.*?)\n\) ENGINE=", sql, re.S):
        declarations = []
        for part in _parts(body):
            if part.startswith("PRIMARY KEY"):
                continue
            if part.startswith("CONSTRAINT"):
                if " FOREIGN KEY " in part:
                    declarations.append(_foreign_key(part))
                else:
                    cname, expression = re.fullmatch(
                        r"CONSTRAINT (\w+) CHECK \((.*)\)", part, re.S
                    ).groups()
                    # MySQL checks remain intact; SQLite fixtures do not claim MySQL CHECK coverage.
                    declarations.append(
                        CheckConstraint(expression, name=cname).ddl_if(dialect="mysql")
                    )
            elif part.startswith(("UNIQUE KEY", "KEY")):
                kind, key, fields = re.fullmatch(
                    r"(UNIQUE KEY|KEY) (\w+) \(([^)]+)\)", part
                ).groups()
                args = fields.split(",")
                declarations.append(
                    UniqueConstraint(*args, name=key) if kind == "UNIQUE KEY" else Index(key, *args)
                )
            else:
                field, spec = part.split(" ", 1)
                default = re.search(r"\bDEFAULT (\d+)", spec)
                declarations.append(
                    Column(
                        field,
                        _type(spec),
                        primary_key=field == "id",
                        autoincrement="ignore_fk" if field == "id" else "auto",
                        nullable="NOT NULL" not in spec,
                        server_default=text(default[1]) if default else None,
                    )
                )
        Table(
            name,
            metadata,
            *declarations,
            mysql_engine="InnoDB",
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )
    for table, body in re.findall(r"ALTER TABLE (\w+)\s+(.*?);", sql, re.S):
        for part in _parts(body):
            metadata.tables[table].append_constraint(_foreign_key(part.removeprefix("ADD ")))
    return metadata


metadata = build_metadata()
TABLES = metadata.tables
