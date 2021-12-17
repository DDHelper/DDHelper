from django.test import Client
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist, BadRequest

from account.models import Userinfo
from . import models


# Create your tests here.

class Login_Required_TestCase(TestCase):  # 检测Login_Required功能是否可以使用
    def test_login_required(self):
        c = Client()
        response = c.get('/subscribe/search', {'search_name': 'vac47'})
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
        response = c.get('/subscribe/search', {'search_name': ''})
        self.assertDictEqual(response.json(), {'code': 200,'data': []})        

        response = c.get('/subscribe/search', {'search_name': 'vac47'})
        self.assertEqual(response.json()["data"][0]["mid"], 3985768)        


class SubscribeTestCase(TestCase):  # 检测列表管理功能
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
        self.client.login(username='test_user', password='12345678')

    def test_subscribe(self):
        response = self.client.get("/subscribe/group_list")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()['data']), 0)
        self.assertEqual(response.json()['data'][0]['group_name'], models.DEFAULT_GROUP_NAME)
        self.assertEqual(response.json()['data'][0]['count'], 0)

        default_group = response.json()['data'][0]['gid']
        # 订阅不存在的Up主
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622555555555817,
                'gid': default_group
            })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['msg'], "添加的up主不存在或不符合要求")

        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': default_group
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/subscribe/group/members",
            {
                'gid': 0
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertGreater(len(json_body['data']['data']), 0)
        self.assertEqual(json_body['data']['group_name'], models.DEFAULT_GROUP_NAME)
        self.assertEqual(json_body['data']['data'][0]['mid'], 416622817)
        self.assertEqual(json_body['data']['data'][0]['name'], '步玎Pudding')

        # 更改默认分组名
        response = self.client.post(
            "/subscribe/group/update/",
            {
                'gid': default_group,
                'group_name': 'new_group2'
            })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['msg'], '默认分组无法改名')

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

        # 分组名重复
        response = self.client.post(
            "/subscribe/group/update/",
            {
                'gid': new_group,
                'group_name': 'new_group2'
            })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['msg'], '分组名重复')

        # 分组不存在
        response = self.client.post(
            "/subscribe/group/update/",
            {
                'gid': 16154849,
                'group_name': 'new_group2'
            })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['msg'], '分组不存在')

        response = self.client.delete(
            "/subscribe/group/delete/",
            f"gid={new_group}")
        self.assertEqual(response.status_code, 200)

        # 默认分组无法被删除
        response = self.client.delete(
            "/subscribe/group/delete/",
            f"gid={default_group}")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['msg'], '默认分组无法被删除')

        # 不存在分组无法被删除
        response = self.client.delete(
            "/subscribe/group/delete/",
            f"gid={6516546541651}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['msg'], '分组不存在')

        response = self.client.get(
            "/subscribe/group/members",
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
            "/subscribe/group/members",
            {
                'gid': new_group1
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertGreater(len(json_body['data']['data']), 0)

