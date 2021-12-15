from django.test import TestCase
from django.test import Client
import datetime
from timeline.tasks import extract_from_text, classify_dynamic
from timeline.tasks import find_time_in_text, process_timeline
from dynamic.models import Dynamic
# Create your tests here.


class TextFunctionTestcase(TestCase):  # 测试文本的提取、日期的提取和分类各个功能是否正确
    def test_TextExtract(self):  # 测试文本提取功能
        test_text = '''bilibili未来有你装扮详细内容奉上~\\n现已开启预约，明天晚7点正式开售！\\n海报不仅包括今年的主视觉图和Q版图，还有历年未来有你的主视觉
图！\\n\\n购买未来有你2021演唱会票更有超值回馈哦ヽ(o´∀`o)ﾉ\\n\\n#未来有你2021#'''
        extract_length = 30
        self.assertEqual(
            extract_from_text(test_text),
            test_text[0:extract_length])

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

    def test_find_time_in_text(self):  # 测试文本时间提取功能
        test_text_list = [
            '''今天上午10点半直播''',
            '''周二直播''',
            '''12月31日20:00直播'''
        ]
        test_ans_list = [
            datetime.datetime(
                datetime.datetime.now().year,
                datetime.datetime.now().month,
                datetime.datetime.now().day,
                10, 30),
            datetime.datetime(
                datetime.datetime.now().year,
                datetime.datetime.now().month,
                datetime.datetime.now().day,
            ) + datetime.timedelta(
                days=((2 - datetime.datetime.now().weekday() - 1) % 7)
            ),
            datetime.datetime(
                datetime.datetime.now().year,
                12, 31, 20, 0),
        ]
        for index, text in enumerate(test_text_list):
            self.assertEqual(find_time_in_text(text), test_ans_list[index])


# class TimelineTestCase(TestCase):
#     def setUp(self):
#         # TODO: 对测试所用的动态建立对应对象并process为timeline对象并进行测试

#         self.dynamic_id_list=[]
#         self.dynamic_time=[]
#         self.dynamic_type=[]
#         process_result = process_timeline(dynamic_id)
#         return self.dynamic_list

#     def test_TimelineView(self):

#     def test_DynamicProcess(self):
#         for index, dynamic_id in enumerate(self.dynamic_id_list):
            
#             self.assertEqual(process_result.event_time, self.dynamic_time[index])
#             self.assertEqual(process_result.type, self.dynamic_type[index])
