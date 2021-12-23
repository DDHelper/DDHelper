from contextlib import contextmanager

from django.core.exceptions import BadRequest


@contextmanager
def load_params():
    try:
        yield
    except (KeyError, ValueError):
        raise BadRequest()


@contextmanager
def mock(target, **kwargs):
    old_values = {}
    for n in kwargs:
        old_values[n] = getattr(target, n)
        setattr(target, n, kwargs[n])
    try:
        yield
    finally:
        for n in old_values:
            setattr(target, n, old_values[n])
