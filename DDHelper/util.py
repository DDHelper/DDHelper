from contextlib import contextmanager

from django.core.exceptions import BadRequest


@contextmanager
def load_params():
    try:
        yield
    except KeyError or ValueError:
        raise BadRequest()
