from django.test import TestCase
from . import tasks
from DDHelper.util import mock, fake_request, none_call, FakeRequest


class TestException(Exception):
    pass

class ApiTest(TestCase):
    def test_api(self):
        user_profile = tasks.user_profile.delay(8401607).get()
        self.assertEqual(user_profile['code'], 0)
        self.assertEqual(user_profile['data']['mid'], 8401607)

        dynamic_history = tasks.space_history.delay(8401607, offset_dynamic_id=575349833245683072).get()
        self.assertEqual(dynamic_history['code'], 0)
        self.assertEqual(dynamic_history['data']['cards'][0]['desc']['uid'], 8401607)
        self.assertEqual(dynamic_history['data']['cards'][0]['desc']['dynamic_id'], 574365641487852129)

        search_result = tasks.search_user_name.delay('无米酱Official').get()
        self.assertEqual(search_result['code'], 0)
        self.assertEqual(search_result['data']['result'][0]['uname'], '无米酱Official')


class ProxyTest(TestCase):
    def test_client_info(self):
        with mock(tasks,
                  get_random_proxy=none_call,
                  requests=fake_request(".*", 400, {})):
            self.assertEqual(tasks.client_info(), None)
            self.assertEqual(tasks.client_info(proxies={}), None)

        with mock(tasks,
                  get_random_proxy=none_call,
                  requests=fake_request(".*", 200, {'code': 200})):
            self.assertDictEqual(tasks.client_info(), {'code': 200})

        with mock(tasks,
                  get_random_proxy=none_call,
                  requests=fake_request(".*", -1, exception=Exception)):
            self.assertEqual(tasks.client_info(), None)

    def test_get_random_proxy(self):
        with mock(tasks, GOOD_PROXY=1000, GOOD_PROXY_CALLS=0):
            self.assertEqual(tasks.get_random_proxy(), 1000)

        with mock(tasks, GOOD_PROXY=1000, GOOD_PROXY_CALLS=100):
            self.assertEqual(tasks.get_random_proxy(), None)

        self.assertEqual(tasks.get_random_proxy(retry=5), None)

        with mock(tasks.settings, PROXY_POOL="PROXY_POOL"):
            with mock(tasks,
                      GOOD_PROXY=None,
                      GOOD_PROXY_CALLS=0,
                      requests=FakeRequest().add_fake_request("PROXY_POOL", 200, text="localhost:2333")
                                            .add_fake_request('http://api.bilibili.com/client_info', 200, json={'code': 200})):
                self.assertDictEqual(
                    tasks.get_random_proxy(check_proxy=False),
                    {'http': 'http://localhost:2333'})

                self.assertDictEqual(
                    tasks.get_random_proxy(check_proxy=True),
                    {'http': 'http://localhost:2333'})

            with mock(tasks,
                      GOOD_PROXY=None,
                      GOOD_PROXY_CALLS=0,
                      requests=FakeRequest().add_fake_request("PROXY_POOL", 200, text="localhost:2333")
                                            .add_fake_request('http://api.bilibili.com/client_info', 400)):
                self.assertEqual(tasks.get_random_proxy(), None)

    def test_clear_proxy_info(self):
        @tasks.clear_proxy_info_on_error
        def _raise():
            raise TestException()

        with mock(tasks,
                  GOOD_PROXY={'http': 'http://localhost:2333'},
                  GOOD_PROXY_CALLS=0):
            with self.assertRaises(TestException):
                _raise()
            self.assertEqual(tasks.GOOD_PROXY, None)

    def test_default_wait_err(self):
        @tasks._default_wait()
        def _raise():
            raise TestException()

        with self.assertRaises(TestException):
            _raise()

    def test_api_retry(self):
        @tasks.api_retry
        def _none():
            return None

        @tasks.api_retry
        def _raise():
            raise TestException()

        self.assertEqual(_none(), None)

        with self.assertRaises(TestException):
            _raise()

    def test_blocked(self):
        @tasks.bili_api("http://test.test/")
        def _none():
            return None

        with mock(tasks,
                  GOOD_PROXY=None,
                  GOOD_PROXY_CALLS=0,
                  BLOCKED=False,
                  BLOCKED_START_TIME=None,
                  requests=fake_request(".*", 412)):
            self.assertEqual(_none(), None)
            self.assertEqual(tasks.BLOCKED, True)

        with mock(tasks,
                  GOOD_PROXY=None,
                  GOOD_PROXY_CALLS=0,
                  BLOCKED=False,
                  BLOCKED_START_TIME=None,
                  requests=fake_request(".*", 412, json={'code': 412})):
            self.assertEqual(_none(), None)
            self.assertEqual(tasks.BLOCKED, True)

    def test_get_date(self):
        self.assertTupleEqual(tasks.get_data_if_valid(None), (None, "unknown"))

        with mock(tasks,
                  requests=fake_request(".*", 200, json={'code': 0, 'message': '', 'data': 12345})):
            rsp = tasks.user_profile(1234)
            data, msg = tasks.get_data_if_valid(rsp)
            self.assertEqual(data, 12345)
            self.assertEqual(msg, None)

        with mock(tasks,
                  requests=fake_request(".*", 200, json={'code': -1, 'message': 'test', 'data': 12345})):
            rsp = tasks.user_profile(1234)
            data, msg = tasks.get_data_if_valid(rsp)
            self.assertEqual(data, None)
            self.assertEqual(msg, 'test')

        with mock(tasks,
                  requests=fake_request(".*", 200, json={'code': -1, 'msg': 'test', 'data': 12345})):
            rsp = tasks.user_profile(1234)
            data, msg = tasks.get_data_if_valid(rsp)
            self.assertEqual(data, None)
            self.assertEqual(msg, 'test')
