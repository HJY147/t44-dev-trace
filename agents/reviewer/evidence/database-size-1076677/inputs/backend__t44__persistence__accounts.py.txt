"""Hash-only initialization boundary. Rejection auditing uses a fresh independent UoW."""

from uuid import uuid4

from argon2 import extract_parameters
from argon2.low_level import Type

from .codecs import utc_now
from .errors import CommitUncertain, PersistenceUnavailable


class PasswordHashRejected(ValueError):
    pass


class AuditUnavailable(PersistenceUnavailable):
    pass


def initialize_user(
    factory, *, username: str, display_name: str, password_hash: str, request_id: str | None = None
) -> int:
    request_id = request_id or uuid4().hex
    try:
        parameters = extract_parameters(password_hash)
        valid = (
            len(password_hash) <= 255
            and parameters.type is Type.ID
            and parameters.version == 19
            and parameters.salt_len >= 16
            and parameters.hash_len >= 32
            and parameters.memory_cost >= 19456
            and parameters.time_cost >= 2
            and parameters.parallelism >= 1
        )
    except (TypeError, ValueError):
        valid = False
    if not valid:
        try:
            with factory() as audit:
                audit.gateway.insert(
                    "audit_events",
                    dict(
                        actor_kind=3,
                        request_id=request_id,
                        operation_id="initializeUser",
                        outcome=2,
                        reason_code=11,
                        before_values=[],
                        after_values=[],
                        evidence=[],
                        created_at=utc_now(),
                    ),
                )
        except CommitUncertain:
            raise
        except Exception:
            raise AuditUnavailable("Password-hash rejection audit could not persist") from None
        raise PasswordHashRejected("Only a valid Argon2id password hash may be persisted")
    now = utc_now()
    with factory() as uow:
        return uow.gateway.insert(
            "users",
            dict(
                username=username,
                display_name=display_name,
                password_hash=password_hash,
                created_at=now,
                updated_at=now,
            ),
        )
