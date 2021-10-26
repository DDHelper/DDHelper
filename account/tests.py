from django.test import TestCase

# Create your tests here.


class AccountTest(TestCase):
    def test_register(self):
        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456"
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456"
            })
        self.assertEqual(response.status_code, 403)

    def test_register_and_login(self):
        response = self.client.post(
            "/account/register/",
            {
                "username": "test_account",
                "password": "123456"
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/login/",
            {
                "username": "test_account",
                "password": "test"
            })
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            "/account/login/",
            {
                "username": "test_account",
                "password": "123456"
            })
        self.assertEqual(response.status_code, 200)
