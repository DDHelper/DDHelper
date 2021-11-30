from django.test import Client
from django.test import TestCase

from account.models import Userinfo
from subscribe.models import SubscribeMember, UserGroup, SubscribeList


# Create your tests here.


class SearchTestCase(TestCase):  # 检测搜索功能是否可以使用
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678')
        self.c = Client()
        self.c.login(username='test_user', password='12345678')

    def test_search_function_work(self):  # 检测是否能正确返回搜索结果
        response = self.c.get('/subscribe/search/', {'search_name': 'vac47'})
        self.assertEqual(response.json()["search_result"][0]["search_result_mid"], 3985768)


class ListManageTestCase(TestCase):  # 检测列表管理功能
    def setUp(self):
        self.user1 = Userinfo.objects.create_user(
            username='test_user',
            password='12345678')
        self.user2 = Userinfo.objects.create_user(
            username='test_user2',
            password='12345678')
        self.user3 = Userinfo.objects.create_user(
            username='test_user3',
            password='12345678')
        self.c = Client()
        self.c.login(username='test_user', password='12345678')
        self.mem1 = SubscribeMember.objects.create(
            mid=399918500,
            name='初音未来_Crypton',
            face='https://i2.hdslb.com/bfs/face/e6c83e92c8c2b5af89c64eea3acbc328c8e4eca1.jpg@256w_256h_1o.webp'
        )
        self.mem2 = SubscribeMember.objects.create(
            mid=3985768,
            name='vac47',
            face='https://i1.hdslb.com/bfs/face/53f80e75cb201ee89392d39ce509eb91a0daf87f.jpg@256w_256h_1o.webp'
        )
        self.mem3 = SubscribeMember.objects.create(
            mid=321598222,
            name='sasakure_uk',
            face='https://i1.hdslb.com/bfs/face/713015f7af1c553022d8f36aa28d7c363a53c682.jpg@256w_256h_1o.webp'
        )
        UserGroup.objects.create(user=self.user1, group_name='all')
        UserGroup.objects.create(user=self.user2, group_name='all')

    def test_mem_subscribe(self):
        UserGroup.objects.create(user=self.user1, group_name='my_fav')
        response = self.c.post('/subscribe/membersubscribe/', {'mid': 400183186,
                                                               'gid': (UserGroup.objects.get(group_name='my_fav').gid)})
        self.assertEqual(response.json()['result'], 'success')  # 测试关注新用户的功能
        self.assertEqual(SubscribeList.objects.get(group=UserGroup.objects.get(group_name='all', user=self.user1)).mem,
                         SubscribeMember.objects.get(mid=400183186))
        self.assertEqual(
            SubscribeList.objects.get(group=UserGroup.objects.get(group_name='my_fav', user=self.user1)).mem,
            SubscribeMember.objects.get(mid=400183186))
        response = self.c.post('/subscribe/membersubscribe/', {'mid': 627656088,
                                                               'gid': (UserGroup.objects.get(group_name='my_fav').gid)})
        self.assertEqual(response.json()['result'], 'fail')  # 测试禁止添加不符合要求的用户的功能

    def test_group_func(self):
        response = self.c.post('/subscribe/addgroup/', {'group_name': 'new_group'})
        self.assertEqual(response.json()['result'], 'success')  # 测试增加新分组的功能
        self.assertNotEquals(list(UserGroup.objects.filter(group_name='new_group', user=self.user1).values_list()),
                             [])  # 测试是否已经增加新分组
        response = self.c.post('/subscribe/updategroup/',
                               {'type': 'rename', 'gid': UserGroup.objects.get(group_name='new_group').gid,
                                'group_name': 'new_new_group'})
        self.assertEqual(response.json()['result'], 'success')  # 测试重命名分组的功能
        self.assertEquals(list(UserGroup.objects.filter(group_name='new_group', user=self.user1).values_list()),
                          [])  # 测试原名字分组是否还存在
        self.assertNotEquals(list(UserGroup.objects.filter(group_name='new_new_group', user=self.user1).values_list()),
                             [])  # 测试分组是否更新名字
        response = self.c.post('/subscribe/updategroup/',
                               {'type': 'rename', 'gid': UserGroup.objects.get(group_name='all', user=self.user2).gid,
                                'group_name': 'new_new_group'})
        self.assertEqual(response.json()['result'], 'fail')  # 测试不能修改其他人的分组
        response = self.c.post('/subscribe/updategroup/',
                               {'type': 'delete', 'gid': UserGroup.objects.get(group_name='new_new_group').gid})
        self.assertEquals(list(UserGroup.objects.filter(group_name='new_new_group', user=self.user1).values_list()),
                          [])  # 测试新分组是否已经被删除

    def test_mem_move(self):
        f1 = UserGroup.objects.create(user=self.user1, group_name='my_fav1')
        f2 = UserGroup.objects.create(user=self.user1, group_name='my_fav2')
        f = UserGroup.objects.create(user=self.user2, group_name='my_fav')
        response = self.c.post('/subscribe/membersubscribe/', {'mid': self.mem1.mid, 'gid': [f1.gid, f2.gid]})
        self.assertEqual(response.json()['result'],
                         'success')  # 测试关注是否成功
        self.assertEquals(
            list(SubscribeList.objects.filter(group=f1, mem=self.mem1).values_list('mem__mid', flat=True)),
            [self.mem1.mid])  # 测试是否关注成功
        self.assertEquals(
            list(SubscribeList.objects.filter(group=f2, mem=self.mem1).values_list('mem__mid', flat=True)),
            [self.mem1.mid])  # 测试是否关注成功
        SubscribeList.objects.create(group=f, mem=self.mem1)  # 手动创建未登录用户的关注
        response = self.c.post('/subscribe/membermove/', {'mid': self.mem1.mid, 'gid': [f1.gid]})
        self.assertEquals(
            list(SubscribeList.objects.filter(group=f1, mem=self.mem1).values_list('mem__mid', flat=True)),
            [self.mem1.mid])  # 测试是否移动分组成功
        self.assertEquals(list(SubscribeList.objects.filter(group=f2, mem=self.mem1).values_list()), [])  # 测试是否移动分组成功
        self.assertEquals(list(
            SubscribeList.objects.filter(group__user=self.user1, group__group_name='all', mem=self.mem1).values_list(
                'mem__mid', flat=True)), [self.mem1.mid])  # 测试是否移动分组成功
        response = self.c.post('/subscribe/membermove/', {'mid': self.mem1.mid, 'gid': []})
        self.assertEquals(list(SubscribeList.objects.filter(group=f, mem=self.mem1).values_list('mem__mid', flat=True)),
                          [self.mem1.mid])  # 测试不能修改其他人对用户的分组

    def test_show_list(self):
        f1 = UserGroup.objects.create(user=self.user1, group_name='my_fav1')
        f2 = UserGroup.objects.create(user=self.user1, group_name='my_fav2')
        SubscribeList.objects.create(mem=self.mem1, group=f1)
        SubscribeList.objects.create(mem=self.mem1, group=f2)
        SubscribeList.objects.create(mem=self.mem3, group=f1)
        SubscribeList.objects.create(mem=self.mem1, group=UserGroup.objects.get(user=self.user1, group_name='all'))
        SubscribeList.objects.create(mem=self.mem3,
                                     group=UserGroup.objects.get(user=self.user1, group_name='all'))  # 设置关注
        response = self.c.get('/subscribe/showlist/', {'gid': f1.gid})
        self.assertEquals(list(map(lambda d: d['mid'], response.json()['member_data'])),
                          [self.mem1.mid, self.mem3.mid])  # 测试访问分组f1分组成员正确
        self.assertEquals(list(map(lambda d: d['group_name'], response.json()['group_list'])),
                          ['all', 'my_fav1', 'my_fav2'])  # 测试访问分组f1分组列表正确
        response = self.c.get('/subscribe/showlist/', {'gid': f2.gid})
        self.assertEquals(response.json()['member_data'][0]['mid'], self.mem1.mid)  # 测试访问分组f2分组成员正确
        self.assertEquals(list(map(lambda d: d['group_name'], response.json()['group_list'])),
                          ['all', 'my_fav1', 'my_fav2'])  # 测试访问分组f2分组列表正确
        response = self.c.get('/subscribe/showlist/')
        self.assertEquals(list(map(lambda d: d['mid'], response.json()['member_data'])),
                          [self.mem1.mid, self.mem3.mid])  # 测试访问默认全体分组分组成员正确
        self.assertEquals(list(map(lambda d: d['group_name'], response.json()['group_list'])),
                          ['all', 'my_fav1', 'my_fav2'])  # 测试访问默认全体分组分组列表正确\

    def test_all_group(self):
        c_temp = Client()
        c_temp.login(username='test_user3', password='12345678')
        response = c_temp.get('/subscribe/showlist/')
        self.assertEquals(list(map(lambda d: d['group_name'], response.json()['group_list'])), ['all'])  # 测试能够自动创建all分组
