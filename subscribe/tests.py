from django.test import Client
from django.test import TestCase

from account.models import Userinfo
from . import models


# Create your tests here.

class Login_Required_TestCase(TestCase):  # 检测搜索功能是否可以使用
    def test_login_required(self):
        c = Client()
        response = c.get('/subscribe/search/', {'search_name': 'vac47'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['msg'], "未登录")

class SearchTestCase(TestCase):  # 检测搜索功能是否可以使用
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
    
    def test_search_function_work(self):  # 检测是否能正确返回搜索结果
        c = Client()
        c.login(username='test_user', password='12345678')
        response = c.get('/subscribe/search/', {'search_name': 'vac47'})
        self.assertEqual(response.json()["data"][0]["mid"], 3985768)        


class SubscribeTestCase(TestCase):  # 检测列表管理功能
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
        self.client.login(username='test_user', password='12345678')

    def test_subscribe(self):
        response = self.client.get("/subscribe/group_list/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()['data']), 0)
        self.assertEqual(response.json()['data'][0]['group_name'], models.DEFAULT_GROUP_NAME)
        self.assertEqual(response.json()['data'][0]['count'], 0)

        default_group = response.json()['data'][0]['gid']

        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': default_group
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/subscribe/group/members/",
            {
                'gid': 0
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertGreater(len(json_body['data']['data']), 0)
        self.assertEqual(json_body['data']['group_name'], models.DEFAULT_GROUP_NAME)
        self.assertEqual(json_body['data']['data'][0]['mid'], 416622817)
        self.assertEqual(json_body['data']['data'][0]['name'], '步玎Pudding')

        response = self.client.post(
            "/subscribe/group/add/",
            {
                'group_name': 'new_group'
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertEqual(json_body['success'], True)
        self.assertEqual(json_body['data']['group_name'], 'new_group')

        new_group = json_body['data']['gid']

        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': [new_group, default_group]
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/subscribe/group/update/",
            {
                'gid': new_group,
                'group_name': 'new_group2'
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertEqual(json_body['data']['group_name'], 'new_group2')

        response = self.client.delete(
            "/subscribe/group/delete/",
            f"gid={new_group}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/subscribe/group/members/",
            {
                'gid': new_group
            })
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            "/subscribe/group/add/",
            {
                'group_name': 'new_group1'
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertEqual(json_body['success'], True)
        self.assertEqual(json_body['data']['group_name'], 'new_group1')

        new_group1 = json_body['data']['gid']

        response = self.client.post(
            "/subscribe/group/add/",
            {
                'group_name': 'new_group2'
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertEqual(json_body['success'], True)
        self.assertEqual(json_body['data']['group_name'], 'new_group2')

        new_group2 = json_body['data']['gid']

        response = self.client.post(
            "/subscribe/member/move/",
            {
                'mid': [416622817],
                'old_group': default_group,
                'new_group': new_group1
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/subscribe/group/members/",
            {
                'gid': new_group1
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertGreater(len(json_body['data']['data']), 0)

