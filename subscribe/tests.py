from django.test import Client
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist, BadRequest
from django.http.response import JsonResponse
from django.db.models import Count
import subscribe.views
from account.models import Userinfo
from . import models
from biliapi.tasks import get_data_if_valid


# Create your tests here.

class Login_Required_TestCase(TestCase):  # 检测Login_Required功能是否可以使用
    def test_login_required(self):
        #未登录尝试搜索
        c = Client()
        response = c.get('/subscribe/search', {'search_name': 'vac47'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['msg'], "未登录")

        # covering models.MemberGroup.select_groups_by_account if not query.exists(): 
        # models.MemberGroup.select_groups_by_account(666)



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

        #covering /subscribe/search data is None
        old_value = get_data_if_valid
        def _get_data_if_valid(request):
            return None, None
        subscribe.views.get_data_if_valid = _get_data_if_valid
        response = c.get('/subscribe/search', {'search_name': 'vac47'})
        subscribe.views.get_data_if_valid = old_value    


class SubscribeTestCase(TestCase):  # 检测列表管理功能
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
        self.client.login(username='test_user', password='12345678')

        #backup user
        Userinfo.objects.create_user(
            username='test_user2',
            password='12345678',
            email='test2@test.test')
        self.client2 = Client()
        self.client2.login(username='test_user2', password='12345678')

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

        #重复添加
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': default_group
            })
        self.assertEqual(response.status_code, 200)

        #添加时无gid==删除
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 26139491,
                'gid': default_group
            })
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 26139491
            })

        response = self.client2.post(
            "/subscribe/group/add/",
            {
                'group_name': 'new_group_for_2'
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertEqual(json_body['success'], True)
        self.assertEqual(json_body['data']['group_name'], 'new_group_for_2')
        new_group_for_2 = json_body['data']['gid']
        #添加到非自己的group
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 26139491,
                'gid': new_group_for_2
            })
        #添加后搜索
        response = self.client.get('/subscribe/search', {'search_name': '步玎Pudding'})
        self.assertEqual(response.json()["data"][0]["mid"], 416622817)   

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


        #covering subscribe.views.add_new_member create is False
        subscribe.views.add_new_member(416622817)


        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': [new_group, default_group]
            })
        self.assertEqual(response.status_code, 200)

        #添加的up主不符合要求
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 484817723,
                'gid': [new_group, default_group]
            })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['msg'], '添加的up主不存在或不符合要求')

        #添加的up主不存在
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622854645617,
                'gid': [new_group, default_group]
            })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['msg'], '添加的up主不存在或不符合要求')


        response = self.client.post(
            "/subscribe/group/update/",
            {
                'gid': new_group,
                'group_name': 'new_group2'
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertEqual(json_body['data']['group_name'], 'new_group2')
        
        #移动成员
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 13946441,
                'gid': [new_group]
            })
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/subscribe/member/move/",
            {
                'old_group': new_group,
                'new_group': default_group,
                "mid_list" : [13946441],
                'remove_old': 1
            })
        self.assertEqual(response.status_code, 200)

        #移动成员分组不存在
        response = self.client.post(
            "/subscribe/member/move/",
            {
                'old_group': 16154849,
                'new_group': new_group,
                "mid_list" : [],
                'remove_old': 1
            })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['msg'], '分组不存在')

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

        #分组改名，给空字符串
        response = self.client.post(
            "/subscribe/group/update/",
            {
                'gid': new_group,
                'group_name': ''
            })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['msg'], '新分组名为空')


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
                'new_group': new_group2,
                'remove_old': 0
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/subscribe/group/members",
            {
                'gid': new_group2
            })
        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertGreater(len(json_body['data']['data']), 0)

