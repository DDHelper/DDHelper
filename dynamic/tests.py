import time
import datetime
import uuid

from django.test import TestCase
from django.utils import timezone
import pytz

from DDHelper.util import mock, fake_request
from account.models import Userinfo
from . import models
from . import dsync
from . import tasks
from .models import DynamicSyncInfo, Dynamic, SyncTask
from biliapi import tasks as biliapi

from subscribe.models import SubscribeMember, MemberGroup
from io import StringIO
from django.core.management import call_command
from DDHelper.settings import CST_TIME_ZONE


class SyncBeatTest(TestCase):
    def test_command_output(self):
        """
        测试sync_beat指令
        :return:
        """
        out = StringIO()
        call_command('sync_beat', stdout=out)
        self.assertIn('成功调用', out.getvalue())


class ModelTest(TestCase):
    def test_model_and_time(self):
        sm = SubscribeMember()
        sm.mid = 1
        sm.name = "t"
        sm.face = "http://aa.www/a.png"
        sm.last_profile_update = timezone.now()
        sm.save()

        m = models.DynamicMember()
        m.mid = sm
        m.last_dynamic_update = timezone.now()
        m.save()

        d = models.Dynamic()
        d.dynamic_id = 1
        d.member = sm
        d.dynamic_type = 233
        d.timestamp = timezone.datetime.fromtimestamp(1636009208, tz=CST_TIME_ZONE)
        d.raw = {"a": 1}
        d.save()

        self.assertEqual(str(d.timestamp), "2021-11-04 15:00:08+08:00")

        d = models.Dynamic.objects.get(dynamic_id=1)
        self.assertEqual(d.member.mid, 1)

        self.assertEqual(d.timestamp.timestamp(), 1636009208)
        self.assertEqual(str(d.timestamp), "2021-11-04 07:00:08+00:00")
        self.assertEqual(str(d.timestamp.astimezone(CST_TIME_ZONE)), "2021-11-04 15:00:08+08:00")

        models.Dynamic.objects.update_or_create(
            dynamic_id=2,
            defaults=dict(
                member=sm,
                dynamic_type=8,
                timestamp=d.timestamp.astimezone(CST_TIME_ZONE),
                raw={}
            ))

        d = models.Dynamic.objects.get(dynamic_id=2)
        self.assertEqual(d.timestamp.timestamp(), 1636009208)
        self.assertEqual(str(d.timestamp), "2021-11-04 07:00:08+00:00")
        self.assertEqual(str(d.timestamp.astimezone(CST_TIME_ZONE)), "2021-11-04 15:00:08+08:00")

    def test_sync_info_models(self):
        task_id = uuid.uuid4()
        sync_task = SyncTask(uuid=task_id)
        self.assertEqual(str(sync_task), str(task_id))
        sync_task.save()

        sync_info = DynamicSyncInfo(sid=1)
        sync_info.save()

        sync_info.total_tasks.add(sync_task)
        sync_info.success_tasks.add(sync_task)
        sync_info.failed_tasks.add(sync_task)
        with self.assertWarns(Warning):
            self.assertEqual(sync_info.pending_tasks, 0)
            time.sleep(0.1)
            sync_info = DynamicSyncInfo.objects.get(pk=1)
            self.assertNotEqual(sync_info.time_cost, 0)
            self.assertEqual(sync_info.as_dict()['sid'], 1)
            sync_info.__str__()


class DsyncTest(TestCase):
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
        self.client.login(username='test_user', password='12345678')

    def test_update_member_profile(self):
        member = SubscribeMember(mid=100)
        rsp = dsync.update_member_profile(
            member,
            data=dict(mid=100, name="test", face="http://test.test"),
            auto_save=False)

        self.assertEqual(rsp, None)
        self.assertEqual(member.name, 'test')
        self.assertEqual(member.face, "http://test.test")

        member = SubscribeMember(mid=100)
        rsp = dsync.update_member_profile(
            member,
            data=dict(mid=101, name="test", face="http://test.test"),
            auto_save=False)
        self.assertEqual(rsp, "mid mismatch")

        member = SubscribeMember(mid=100)
        with mock(biliapi,
                  requests=fake_request(".*", 200, {'code': -1, 'msg': 'test'})):
            self.assertEqual(
                dsync.update_member_profile(member, auto_save=False),
                'test'
            )

    def test_get_all_dynamic(self):
        with mock(biliapi,
                  requests=fake_request(".*", 200, {'code': -1, 'msg': 'test'})):
            member = SubscribeMember(mid=100)
            self.assertEqual(dsync.get_all_dynamic_since(member, 0)[1], 'test')

        with mock(biliapi,
                  requests=fake_request(".*", 200, {'code': 0, 'data': {'has_more': 0}})):
            member = SubscribeMember(mid=100)
            self.assertEqual(len(dsync.get_all_dynamic_since(member, 0)[0]), 0)

    def test_parse_dynamic_card(self):
        with self.assertWarns(Warning):
            self.assertIsNone(dsync.parse_dynamic_card(
                {
                    'desc': {
                        'dynamic_id': 100,
                        'dynamic_id_str': '100',
                        'type': 1,
                        'timestamp': 100000,
                        'uid': 100
                    }
                },
                SubscribeMember(mid=101)
            ))

        self.assertEqual(dsync.parse_dynamic_card(
            {
                'desc': {
                    'dynamic_id': 100,
                    'dynamic_id_str': '100',
                    'type': 1,
                    'timestamp': 100000,
                    'uid': 100
                }
            },
            SubscribeMember(mid=100)
        ).dynamic_id, 100)

        self.assertIsNone(dsync.parse_dynamic_card(
            {
                'desc': {
                    'dynamic_id': 100,
                    'dynamic_id_str': '100',
                    'type': 1,
                    'timestamp': 100000,
                    'uid': 100
                }
            }
        ).member_id)

    def test_dsync(self):
        member = SubscribeMember(mid=8401607)
        dsync.update_member_profile(member)

        member = dsync.get_subscribe_member(8401607)
        self.assertEqual(member.name, "无米酱Official")
        self.assertEqual(dsync.get_subscribe_member(1), None)

        self.assertEqual(dsync.get_saved_latest_dynamic(1), None)

    def test_raw(self):
        mid = 416622817
        member = SubscribeMember(mid=mid)
        dsync.update_member_profile(member)

        tasks.add_member.delay(mid)

        member = dsync.get_subscribe_member(mid)
        self.assertEqual(member.name, "步玎Pudding")
        self.assertNotEqual(dsync.get_saved_latest_dynamic(mid), None)
        self.assertGreater(models.Dynamic.objects.count(), 0)

    def test_task(self):
        response = self.client.get("/subscribe/group_list")
        default_group = response.json()['data'][0]['gid']
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': default_group
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/dynamic/list")
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json['data']['has_more'], True)
        self.assertEqual(len(json['data']['data']), 20)
        offset = json['data']['offset']

        response = self.client.get("/dynamic/list", {'offset': offset})
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json['data']['has_more'], True)
        self.assertEqual(json['data']['data'][0]['dynamic_id'], offset)

        tasks.call_full_sync(min_interval=3600)

        sync_info = DynamicSyncInfo.get_latest()
        self.assertNotEqual(sync_info, None)
        self.assertEqual(sync_info.finish(), True)
        self.assertEqual(sync_info.total_tasks.count(), 0)
        self.assertEqual(sync_info.success_tasks.count(), 0)

        time.sleep(1)
        tasks.call_full_sync(min_interval=0)

        sync_info = DynamicSyncInfo.get_latest()
        self.assertNotEqual(sync_info, None)
        self.assertEqual(sync_info.finish(), True)
        self.assertEqual(sync_info.total_tasks.count(), 1)
        self.assertEqual(sync_info.success_tasks.count(), 1)

    def test_direct_add(self):
        tasks.direct_sync_dynamic(604029782310941867)
        dy = Dynamic.objects.filter(pk=604029782310941867).first()
        self.assertNotEqual(dy, None)
        self.assertEqual(dy.raw['desc']['uid'], 1473830)

    def test_time_zone(self):
        tasks.direct_sync_dynamic(604776114479802924)
        dy = Dynamic.objects.filter(pk=604776114479802924).first()
        self.assertEqual(dy.timestamp.timestamp(), 1639648812)
        self.assertEqual(
            dy.timestamp.astimezone(CST_TIME_ZONE),
            datetime.datetime(2021, 12, 16, 18, 0, 12, tzinfo=CST_TIME_ZONE),
        )

