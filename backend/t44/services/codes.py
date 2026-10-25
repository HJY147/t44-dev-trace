"""Stable frozen transport/persistence codes, independent of display and Enum order."""

import hashlib

from t44.contracts import SPEC
from t44.domain import models as domain

# v1.2 ErrorCode order is identity-locked before assigning its already-frozen IDs.
# A future schema reorder must receive an explicit storage mapping migration.
_ERROR_NAMES = SPEC["components"]["schemas"]["ErrorCode"]["enum"]
_ERROR_ORDER_SHA256 = "b747164315e7e12197d71d2d76b74a035de43b1ae71a0b9b6baef1ac6977b611"
if hashlib.sha256("\n".join(_ERROR_NAMES).encode()).hexdigest() != _ERROR_ORDER_SHA256:
    raise RuntimeError("Frozen error-code storage order changed without a mapping migration")
ERROR_CODES = dict(enumerate(_ERROR_NAMES, 1))
ERROR_IDS = {value: key for key, value in ERROR_CODES.items()}


# Public compatibility classes expose actual ints, preserving their previous field types.
State = type("State", (), {member.name: member.code for member in domain.TaskState})
Action = type(
    "Action",
    (),
    {
        "APPROVE_REVIEW" if member is domain.Action.ACCEPT_REVIEW else member.name: member.code
        for member in domain.Action
    },
)
STATE_TO_DOMAIN = {member.code: member for member in domain.TaskState}
DOMAIN_TO_STATE = {member: member.code for member in domain.TaskState}
ROLE_TO_DOMAIN = {member.code: member for member in domain.ProjectRole}
STAGE_TO_DOMAIN = {member.code: member for member in domain.ResponsibilityStage}
DECISION_TYPE = {Action.DELIVER: 1, Action.ROLLBACK: 2, Action.REWORK: 3}
