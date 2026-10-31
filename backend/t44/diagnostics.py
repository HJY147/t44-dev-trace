"""Opt-in numeric request spans. No payloads, SQL, identifiers or credentials recorded."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter_ns, thread_time_ns

_CURRENT = ContextVar('t44_numeric_request_trace', default=None)


def active():
    return _CURRENT.get() is not None


def count(name, value=1):
    trace = _CURRENT.get()
    if trace is not None:
        trace[name] = trace.get(name, 0) + value


@contextmanager
def span(name):
    if not active():
        yield
        return
    wall, cpu = perf_counter_ns(), thread_time_ns()
    try:
        yield
    finally:
        count(name + '.wall_ns', perf_counter_ns() - wall)
        count(name + '.cpu_ns', thread_time_ns() - cpu)
        count(name + '.calls')


def measured(name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with span(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def diagnosed(enabled):
    """Runs in the sync endpoint thread. Middleware readiness is not ingress time."""
    def decorate(function):
        @wraps(function)
        def wrapped(request):
            if not enabled:
                return function(request)
            trace = {}
            token = _CURRENT.set(trace)
            trace['dispatch_wait.wall_ns'] = max(
                0, perf_counter_ns() - request.state.diagnostic_dispatch_ready_ns
            )
            try:
                with span('handle'):
                    response = function(request)
                # Header values are only constant names and numbers; no request data.
                names = sorted(trace)
                projected = []
                for name in names:
                    value = trace[name]
                    if name.endswith('_ns'):
                        projected.append(f"diag-{name[:-3].replace('.', '-')};dur={value / 1e6:.3f}")
                    else:
                        projected.append(f'diag-{name.replace(".", "-")};desc="{value:.0f}"')
                response.headers['Server-Timing'] += ', ' + ', '.join(projected)
                return response
            finally:
                _CURRENT.reset(token)
        return wrapped
    return decorate
