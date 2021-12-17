from django.test import TestCase
from django.test import Client
from django.utils import timezone
import datetime

from account.models import Userinfo
from timeline.tasks import extract_from_text, classify_dynamic
from timeline.tasks import find_time_in_text, process_timeline
from dynamic.models import Dynamic
from dynamic.tasks import direct_sync_dynamic
from timeline.models import TimelineEntry, TimelineDynamicProcessInfo
from timeline import tasks
from DDHelper.settings import CST_TIME_ZONE
from subscribe.models import MemberGroup
# Create your tests here.


class TextFunctionTestcase(TestCase):  # 测试文本的提取、日期的提取和分类各个功能是否正确
    def test_TextExtract(self):  # 测试文本提取功能
        test_text = '''bilibili未来有你装扮详细内容奉上~\\n现已开启预约，明天晚7点正式开售！\\n海报不仅包括今年的主视觉图和Q版图，还有历年未来有你的主视觉
图！\\n\\n购买未来有你2021演唱会票更有超值回馈哦ヽ(o´∀`o)ﾉ\\n\\n#未来有你2021#'''
        extract_length = 30
        self.assertEqual(
            extract_from_text(test_text),
            test_text[0:extract_length])

        self.assertEqual(extract_from_text("我将在 12.3 发布一首新歌。"), "我将在 12.3 发布一首新歌。")

    def test_classify_dynamic(self):  # 测试文本分类功能
        test_text_list = [
            '''我将在 12.3 发布一首新歌。『藍才』- aisai配信：https://tf.lnk.to/aisai 这是我今年希望你听的最后一首歌''',
            '''博物编辑部专场直播来啦！张瑜老师，何长欢老师，林语尘老师，李聪颖老师，刘莹老师，齐聚一堂，给你讲讲今年采访中的秘闻趣事！比双十二更优惠的杂志订阅折扣，直播间专属礼物，等你来拿！
            12月17日中午12：30，预约起来吧！ ''',
            '''评论区中抽三个幸运观众送三份新周边，12月20日晚上开奖哦''',
            '''bilibili未来有你装扮详细内容奉上~现已开启预约，明天晚7点正式开售！海报不仅包括今年的主视觉图和Q版图，还有历年未来有你的主视觉图！'''
        ]
        test_ans_list = [
            'RE',
            'ST',
            'LO',
            'UN'
        ]
        for index, text in enumerate(test_text_list):
            self.assertEqual(classify_dynamic(text), test_ans_list[index])

    def test_day_of_month(self):
        self.assertEqual(tasks.day_of_month(2, 2001), 28)
        self.assertEqual(tasks.day_of_month(2, 2100), 28)
        self.assertEqual(tasks.day_of_month(2, 2004), 29)
        self.assertEqual(tasks.day_of_month(2, 2000), 29)

    def test_find_day_in_text(self):
        now = datetime.datetime(2021, 6, 7, tzinfo=CST_TIME_ZONE)
        self.assertIsNone(tasks.find_day_in_text("无聊", now=now))
        self.assertEqual(tasks.find_day_in_text("今天", now=now), 7)
        self.assertEqual(tasks.find_day_in_text("明天", now=now), 8)
        self.assertEqual(tasks.find_day_in_text("后天", now=now), 9)
        self.assertEqual(tasks.find_day_in_text("星期一", now=now), 7)
        self.assertEqual(tasks.find_day_in_text("星期二", now=now), 8)
        self.assertEqual(tasks.find_day_in_text("周三", now=now), 9)

        self.assertEqual(tasks.find_day_in_text("6号", now=now), 6)
        self.assertEqual(tasks.find_day_in_text("666号", now=now), None)
        self.assertEqual(tasks.find_day_in_text("十三日", now=now), 13)
        self.assertEqual(tasks.find_day_in_text("28日", now=now), 28)
        self.assertEqual(tasks.find_day_in_text("二十九号", now=now), 29)

    def test_find_hourandmin_in_text(self):
        self.assertEqual(tasks.find_hourandmin_in_text("哈哈哈"), None)
        self.assertEqual(tasks.find_hourandmin_in_text("12:12"), (12, 12))
        self.assertEqual(tasks.find_hourandmin_in_text("12点12"), (12, 12))
        self.assertEqual(tasks.find_hourandmin_in_text("12点12分"), (12, 12))
        self.assertEqual(tasks.find_hourandmin_in_text("12点半"), (12, 30))
        self.assertEqual(tasks.find_hourandmin_in_text("十二点半"), (12, 30))

    def test_find_time_in_appointment(self):
        now = datetime.datetime(2021, 6, 7, tzinfo=CST_TIME_ZONE)
        self.assertEqual(
            tasks.find_time_in_appointment("07-21 20:00", now=now),
            timezone.datetime(2021, 7, 21, 20, 00, tzinfo=CST_TIME_ZONE))

        now = datetime.datetime(2021, 12, 2, tzinfo=CST_TIME_ZONE)
        self.assertEqual(
            tasks.find_time_in_appointment("01-21 20:00", now=now),
            timezone.datetime(2022, 1, 21, 20, 00, tzinfo=CST_TIME_ZONE))

    def test_find_time_in_text(self):  # 测试文本时间提取功能
        now = datetime.datetime(2021, 12, 6, tzinfo=CST_TIME_ZONE)
        self.assertEqual(find_time_in_text("您好", now=now), None)

        test_text_list = [
            '''今天上午10点半直播''',
            '''周二直播''',
            '''12月20日20:00直播''',
        ]
        test_ans_list = [
            datetime.datetime(
                now.year,
                now.month,
                now.day,
                10, 30, tzinfo=CST_TIME_ZONE),
            datetime.datetime(
                now.year,
                now.month,
                now.day,
                tzinfo=CST_TIME_ZONE)
            + datetime.timedelta(
                days=((2 - now.weekday() - 1)%7)
            ),
            datetime.datetime(
                now.year,
                12, 20, 20, 0, tzinfo=CST_TIME_ZONE),
        ]
        for index, text in enumerate(test_text_list):
            self.assertEqual(find_time_in_text(text, now=now), test_ans_list[index], msg=text)

        now = datetime.datetime(2021, 11, 29, tzinfo=CST_TIME_ZONE)
        self.assertEqual(
            find_time_in_text("下个月2号13点半", now=now),
            datetime.datetime(now.year, 12, 2, 13, 30, tzinfo=CST_TIME_ZONE))

        now = datetime.datetime(2021, 12, 29, tzinfo=CST_TIME_ZONE)
        self.assertEqual(
            find_time_in_text("2号13点半", now=now),
            datetime.datetime(2022, 1, 2, 13, 30, tzinfo=CST_TIME_ZONE))


class TimelineTestCase(TestCase):
    def assertTimelineProcess(self, dynamic_id, event_time=None, text=None, dynamic_type=None, is_none=False):
        # 同步动态
        direct_sync_dynamic(dynamic_id)
        # 处理动态
        process_timeline(dynamic_id)

        info = TimelineDynamicProcessInfo.get(dynamic_id)
        self.assertEqual(info.should_update(), False)
        result: TimelineEntry = TimelineEntry.objects.filter(dynamic_id=dynamic_id).first()
        # 判断结果
        if is_none:
            self.assertIsNone(result)
            return
        if event_time:
            self.assertEqual(result.event_time.astimezone(CST_TIME_ZONE), event_time)
        if text:
            self.assertDictEqual(result.text, text)
        if dynamic_type:
            self.assertEqual(result.type, dynamic_type)

    def test_dynamic_process(self):
        self.assertTimelineProcess(  # 测试视频动态
            604776114479802924,
            event_time=datetime.datetime(2021, 12, 16, 18, 0, 12, tzinfo=CST_TIME_ZONE),
            dynamic_type='RE',
            text={
                'extract': '投稿了DECO*27 - アニマル feat. 初音ミク'
            })

        process_timeline(604776114479802924)  # 覆盖Skip

        # 测试直播动态
        self.assertTimelineProcess(
            604788715913959797,
            event_time=datetime.datetime(2021, 12, 17, 12, 30, 0, tzinfo=CST_TIME_ZONE),
            dynamic_type='ST',
            text={
                'extract': '大象粪便里可以研究出什么？鸭子的不安是什么样的神态？普通人该'
            }
        )
        # 测试抽奖动态
        self.assertTimelineProcess(
            594350987608092128,
            event_time=datetime.datetime(2021, 11, 21, tzinfo=CST_TIME_ZONE),
            dynamic_type='LO',
            text={
                'extract': '【抽奖送书】#互动抽奖##新书推荐##转发关注评论抽奖##抽'
            }
        )

        # 测试非时效性动态
        self.assertTimelineProcess(
            89041896182999882,
            is_none=True
        )

        self.assertTimelineProcess(
            174001155365656648,
            is_none=True
        )

        self.assertTimelineProcess(
            599846007421184202,
            is_none=True
        )


class TimelineViewTestCase(TestCase):
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
        self.client.login(username='test_user', password='12345678')

        uid = self.client.get("/account/user_info").json()['data']['uid']

        for dynamic_id in [
            604788715913959797,
            604776114479802924,
        ]:
            direct_sync_dynamic(dynamic_id)
            process_timeline(dynamic_id)

        group = MemberGroup.get_group(uid, 0)
        group.members.add(2000819931, 177291194)

    def test_list_timeline(self):
        rsp = self.client.get("/timeline/list")
        self.assertEqual(rsp.status_code, 200)
        json = rsp.json()
        self.assertEqual(len(json['data']['data']), 2)

        rsp = self.client.get("/timeline/list", {'offset': 1639651746})
        self.assertEqual(rsp.status_code, 200)
        json = rsp.json()
        self.assertEqual(len(json['data']['data']), 1)

        rsp = self.client.get("/timeline/list", {'gid': 999})
        self.assertEqual(rsp.status_code, 404)


