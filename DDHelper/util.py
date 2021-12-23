from contextlib import contextmanager

from django.core.exceptions import BadRequest
from json import dumps, loads
import re

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


def none_call(*args, **kwargs):
    return None


class Fake:
    def __init__(self, **kwargs):
        for n in kwargs:
            setattr(self, n, kwargs[n])


def make_fake_response(status_code, json=None, exception=None, text=None, callback=None):
    if status_code == -1:
        def _exception():
            if callback is not None:
                callback()
            raise exception()
        return _exception

    def rsp():
        fake = Fake(
            status_code=status_code,
            json=lambda: loads(fake.text),
            text=text or (dumps(json, ensure_ascii=False) if json else ""))
        if callback is not None:
            callback()
        return fake
    return rsp


class FakeRequest:
    def __init__(self):
        self.urls = {}
        self.get_404 = make_fake_response(404, {})

    def add_fake_request(self, url, status_code, json=None, exception=None, **kwargs):
        self.urls[url] = make_fake_response(status_code, json=json, exception=exception, **kwargs)
        return self

    def get(self, url, *args, **kwargs):
        for _url in self.urls:
            if re.match(_url, url):
                return self.urls[_url]()
        return self.get_404()


def fake_request(url, status_code, json=None, exception=None, **kwargs):
    return FakeRequest().add_fake_request(url, status_code, json=json, exception=exception, **kwargs)
