"""Opt-in numeric request spans; measurement/export failures never change business results."""
from contextlib import contextmanager, suppress
from contextvars import ContextVar
from functools import wraps
from time import perf_counter_ns, thread_time_ns

_CURRENT = ContextVar('t44_numeric_request_trace', default=None)


def active():
    try:
        return _CURRENT.get() is not None
    except Exception:
        return False


def count(name, value=1):
    try:
        trace = _CURRENT.get()
        if (trace is not None and type(value) is int and isinstance(name, str)
                and len(name) <= 64 and name.isascii()
                and all(c.isalnum() or c in '._' for c in name)
                and (name in trace or len(trace) < 64)):
            trace[name] = min(2**63 - 1, trace.get(name, 0) + max(0, value))
    except Exception:
        pass


def _stamp():
    try:
        return perf_counter_ns(), thread_time_ns()
    except Exception:
        return None


@contextmanager
def span(name):
    start = _stamp() if active() else None
    try:
        yield
    finally:
        try:
            end = _stamp() if start is not None else None
            if end is not None:
                count(name + '.wall_ns', end[0] - start[0])
                count(name + '.cpu_ns', end[1] - start[1])
                count(name + '.calls')
        except Exception:
            pass


def measured(name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with span(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def _export(response, trace):
    original = response.headers['Server-Timing']
    value = original
    for name in sorted(trace):
        number = trace[name]
        if name.endswith('_ns'):
            metric = f"diag-{name[:-3].replace('.', '-')};dur={number / 1e6:.3f}"
        else:
            metric = f'diag-{name.replace(".", "-")};desc="{number:.0f}"'
        if len(value) + len(metric) + 2 > 2048:
            break
        value += ', ' + metric
    response.headers['Server-Timing'] = value


def diagnosed(enabled):
    """Runs in the sync thread. Readiness includes routing/thread dispatch, not Nginx ingress."""
    def decorate(function):
        @wraps(function)
        def wrapped(request):
            if not enabled:
                return function(request)
            try:
                prior = _CURRENT.get()
                trace = {}
                token = _CURRENT.set(trace)
            except Exception:
                return function(request)
            try:
                try:
                    ready = getattr(request.state, 'diagnostic_dispatch_ready_ns', None)
                    if ready is not None:
                        count('dispatch_wait.wall_ns', perf_counter_ns() - ready)
                except Exception:
                    pass
                with span('handle'):
                    response = function(request)
                with suppress(Exception):
                    _export(response, trace)
                return response
            finally:
                try:
                    _CURRENT.reset(token)
                except Exception:
                    with suppress(Exception):
                        _CURRENT.set(prior)
        return wrapped
    return decorate
