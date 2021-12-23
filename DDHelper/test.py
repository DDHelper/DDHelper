import warnings
from json import JSONDecodeError

from django.test import TestCase
from django.core.exceptions import BadRequest
from DDHelper.util import load_params, mock, make_fake_response, FakeRequest, Fake


class TestException(Exception):
    pass


class load_params_Test(TestCase):
    def test_KeyError(self):
        with self.assertRaises(BadRequest):
            with load_params():
                raise KeyError

    def test_ValueError(self):
        with self.assertRaises(BadRequest):
            with load_params():
                raise ValueError('Testing ERROR')


class MockTest(TestCase):
    def test_mock(self):
        a = Fake(a=1)
        with mock(a, a=10):
            self.assertEqual(a.a, 10)
        self.assertEqual(a.a, 1)

    def test_make_response(self):
        rsp = make_fake_response(200, json={'a': 1})()
        self.assertEqual(rsp.status_code, 200)
        self.assertDictEqual(rsp.json(), {'a': 1})

        rsp = make_fake_response(200)()
        self.assertEqual(rsp.status_code, 200)
        with self.assertRaises(JSONDecodeError):
            rsp.json()

        rsp = make_fake_response(200, text="test")()
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.text, 'test')

        with self.assertRaises(TestException):
            make_fake_response(-1, exception=TestException)()

        def _raise():
            raise TestException()
        with self.assertRaises(TestException):
            make_fake_response(200, callback=_raise)()

        with self.assertRaises(TestException):
            make_fake_response(-1, callback=_raise)()

    def test_request_mock(self):
        requests = FakeRequest()

        rsp = requests.get("http://test.com")
        self.assertEqual(rsp.status_code, 404)

        requests.add_fake_request("http://test.com", 200, {'code': 200})

        requests.add_fake_request(".*", -1, exception=TestException)

        rsp = requests.get("http://test.com")
        self.assertEqual(rsp.status_code, 200)
        self.assertDictEqual(rsp.json(), {'code': 200})

        with self.assertRaises(TestException):
            requests.get("https://test.com/aabb")

    def test_warn(self):
        with self.assertWarns(Warning):
            warnings.warn("aaaa")
