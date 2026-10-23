"""Infrastructure exceptions: no SQL text, bound values, URLs or driver messages."""


class PersistenceError(RuntimeError):
    """An internal persistence failure; not an HTTP/business error code."""


class PersistenceUnavailable(PersistenceError):
    """The operation or cleanup could not complete."""


class PersistenceIntegrityError(PersistenceError):
    """A constraint rejected a statement; the whole UoW must roll back."""


class CommitUncertain(PersistenceError):
    """Commit acknowledgement failed; rollback cannot establish non-commit."""


class TransactionStateError(PersistenceError):
    """A closed, reused or rollback-only UoW cannot perform this operation."""


class StatementRejected(ValueError):
    """The internal allowlist rejected an identifier, expression or unsafe write."""
