from django.core import mail
from django.test import TestCase

import account.views
from . import views
from . import models
from DDHelper import settings

# Create your tests here.


class RegisterTest(TestCase):
    def test_register(self):
        response = self.client.get(
            "/account/verify_pin/",
            {
                "email": "test@test.test",
                "pin": 0
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'code': 400, "msg": "未获取验证码"})

        # 不完整的参数会请求失败
        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456"
            })
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": 1234
            })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['msg'], "请先获取验证码")

        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)
        #连续send
        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['msg'], "重新发送验证码前请等待60秒")

        response = self.client.get(
            "/account/verify_pin/",
            {
                "email": "test@test.test",
                "pin": 0
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['match'], False)

        response = self.client.get(
            "/account/verify_pin/",
            {
                "email": "test@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['match'], True)

        response = self.client.get(
            "/account/verify_pin/",
            {
                "email": "test2@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['match'], False)

        #验证码错误
        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": 123
            })
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'code': 400, "msg": "验证码或邮箱不正确"})

        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            })
        self.assertEqual(response.status_code, 200)

        # 重复注册
        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            })
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'code': 400, "msg": "用户名或邮箱已被占用"})
    
    def test_register_brutal_guess(self):
        """
        暴力猜测验证码
        """
        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)
        
        for i in range(views.REGISTER_PIN_VERIFY_MAX_RETIES):
            response = self.client.post(
                "/account/register/",
                {
                    "username": "test_account",
                    "password": "123456",
                    "email": "test@test.test",
                    "pin": 123
                })
        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            })
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'code': 400, "msg": "验证码或邮箱不正确"})

    def test_pin_timeout(self):
        old_value = account.views.REGISTER_PIN_TIME_OUT
        account.views.REGISTER_PIN_TIME_OUT = 0

        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/account/verify_pin/",
            {
                "email": "test2@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            }
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)

        # 验证码超时，重新发送
        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)

        # 注册时验证码超时
        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": 123
            })
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'code': 400, "msg": "验证码已超时"})

        account.views.REGISTER_PIN_TIME_OUT = old_value


class LoginLogoutTest(TestCase):
    def setUp(self):
        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456",
                "email": "test@test.test",
                "pin": self.client.session[views.REGISTER_PIN]
            })
        self.assertEqual(response.status_code, 200)

    def test_login_logout(self):
        response = self.client.post(
            "/account/login/",
            {
                "username": "test_account",
                "password": "asda",
            })
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), {'code': 403, 'msg': "用户名或密码错误"})

        response = self.client.post(
            "/account/login/",
            {
                "username": "test_account",
                "password": "123456",
            })
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                'code': 200,
                'data': {
                    'username': 'test_account',
                    'uid': models.Userinfo.objects.get(username='test_account').uid
                }
            }
        )

        response = self.client.get("/account/user_info/")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                'code': 200,
                'data': {
                    'username': 'test_account',
                    'uid': models.Userinfo.objects.get(username='test_account').uid,
                    'email': 'test@test.test'
                }
            }
        )

        response = self.client.get("/account/logout/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/account/user_info/")
        self.assertEqual(response.status_code, 403)


class SendPinTest(TestCase):
    def test_pin_email_error(self):
        old_value = settings.EMAIL_FAIL_SILENTLY
        old_send_mail = mail.send_mail

        settings.EMAIL_FAIL_SILENTLY = False

        def _send_mail(*args, **kwargs):
            raise Exception()

        mail.send_mail = _send_mail

        response = self.client.post(
            "/account/send_pin/",
            {
                "email": "test@test.test",
            })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['msg'], '邮件发送失败，请重试')

        settings.EMAIL_FAIL_SILENTLY = old_value
        mail.send_mail = old_send_mail

