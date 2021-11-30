from django.test import TestCase
from . import views

# Create your tests here.


class RegisterTest(TestCase):
    def test_register(self):
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
        print(self.client.session[views.REGISTER_PIN])

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
