"""Immutable task-operation prefix; original callbacks retain business decisions."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from t44.persistence.rows import RowsGateway

from .common import Call

type TaskCallback[Service] = Callable[[Service, RowsGateway, Call, dict], dict]
type TaskHandler[Service] = Callable[[Service, RowsGateway, Call], dict]


@dataclass(frozen=True)
class OperationPlan:
    authorize: Callable[[Call], None]

    def __call__[Service](self, callback: TaskCallback[Service]) -> TaskHandler[Service]:
        @wraps(callback)
        def execute(service: Service, gateway: RowsGateway, call: Call) -> dict:
            self.authorize(call)
            return callback(service, gateway, call, call.task(gateway))

        return execute
