from django.test import TestCase
from django.utils import timezone
import pytz
from . import models
from . import dsync
from . import tasks

CST_TIME_ZONE = pytz.timezone("Asia/Shanghai")


class ModelTest(TestCase):
    def test_model_and_time(self):
        m = models.Member()
        m.mid = 1
        m.name = "t"
        m.face = "http://aa.www/a.png"
        m.last_profile_update = timezone.now()
        m.last_dynamic_update = timezone.now()
        m.save()

        d = models.Dynamic()
        d.dynamic_id = 1
        d.member = m
        d.dynamic_type = 233
        d.timestamp = timezone.make_aware(timezone.datetime.fromtimestamp(1636009208), CST_TIME_ZONE)
        d.raw = {"a": 1}
        d.save()

        self.assertEqual(str(d.timestamp), "2021-11-04 15:00:08+08:00")

        d = models.Dynamic.objects.get(dynamic_id=1)
        self.assertEqual(d.member.mid, 1)

        self.assertEqual(d.timestamp.timestamp(), 1636009208)
        self.assertEqual(str(d.timestamp), "2021-11-04 07:00:08+00:00")
        self.assertEqual(str(d.timestamp.astimezone(CST_TIME_ZONE)), "2021-11-04 15:00:08+08:00")


class DsyncTest(TestCase):
    def test_dsync(self):
        member = models.Member(mid=8401607)
        dsync.update_member_profile(member)
        member.save()

        member = dsync.get_member(8401607)
        self.assertEqual(member.name, "无米酱Official")
        self.assertEqual(dsync.get_member(1), None)

        self.assertEqual(dsync.get_saved_latest_dynamic(1), None)

    def test_task(self):
        mid = 8401607
        tasks.add_member(mid, initial_sync=False)  # 直接调用celery task时与一般的函数调用行为相同

        member = dsync.get_member(mid)
        self.assertEqual(member.name, "无米酱Official")

        self.assertEqual(dsync.get_saved_latest_dynamic(mid), None)
        tasks.sync_member(member.mid)
        self.assertNotEqual(dsync.get_saved_latest_dynamic(mid), None)
        self.assertGreater(len(models.Dynamic.objects.all()), 0)


