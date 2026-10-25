"""Stable frozen transport/persistence codes, independent of display and Enum order."""

import hashlib

from t44.contracts import FROZEN_ERROR_NAMES
from t44.domain import models as domain

# v1.2 ErrorCode order is identity-locked before assigning its already-frozen IDs.
# A future schema reorder must receive an explicit storage mapping migration.
_ERROR_NAMES = FROZEN_ERROR_NAMES
_ERROR_ORDER_SHA256 = "b747164315e7e12197d71d2d76b74a035de43b1ae71a0b9b6baef1ac6977b611"
if hashlib.sha256("\n".join(_ERROR_NAMES).encode()).hexdigest() != _ERROR_ORDER_SHA256:
    raise RuntimeError("Frozen error-code storage order changed without a mapping migration")
ERROR_CODES = dict(enumerate(_ERROR_NAMES, 1))
ERROR_IDS = {value: key for key, value in ERROR_CODES.items()}


State = domain.State
Action = domain.Action
