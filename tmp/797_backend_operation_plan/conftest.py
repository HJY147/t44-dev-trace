"""Reuse the exact existing synthetic SQLite application fixture."""

from importlib import import_module

application = import_module("tmp.backend.contracts.conftest").application
