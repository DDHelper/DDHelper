import datetime
import logging
import re
import json

from django.utils import timezone
from DDHelper.settings import CST_TIME_ZONE


from celery import shared_task
from celery.utils.log import get_task_logger

from dynamic.models import Dynamic
from timeline.models import TimelineEntry, TimelineDynamicProcessInfo

# 中文数字和阿拉伯数字的转换
chinese_number = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7,
                  '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12, '十三': 13,
                  '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18,
                  '十九': 19, '二十': 20, '二十一': 21, '二十二': 22, '二十三': 23,
                  '二十四': 24, '二十五': 25, '二十六': 26, '二十七': 27, '二十八': 28,
                  '二十九': 29, '三十': 30, '三十一': 31, '日': 7, '天': 7, '零': 0}

logger: logging.Logger = get_task_logger(__name__)


class TimelineException(Exception):
    # 捕捉Timeline所引起的异常
    def __init__(self, msg):
        super(TimelineException, self).__init__(msg)


def day_of_month(month, year):
    """
    返回某年某月的天数
    :param month: 要查询的月份
    :param year: 要查询的年份
    :return: integer 该年该月的天数
    """
    days_of_month = [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month != 2:
        return days_of_month[month - 1]
    elif year%4 == 0 and year%100 != 0:
        return 29
    elif year%100 == 0 and year%400 == 0:
        return 29
    else:
        return 28


def find_day_in_text(text, now):
    """
    在文本中提取日期
    :param text: 要提取日期的文本
    :param now: 进行提取时作为基准的现在的时间
    :return: integer 某个月的日期
    """
    now = now.astimezone(CST_TIME_ZONE)

    # 在一段文本中寻找日期
    specical_day_template = {'今天': 0, '明天': 1, '后天': 2}
    week_day_template = ['星期[一二三四五六七]', '周[一二三四五六七]']
    date_day_template = ['([0-9一二三四五六七八九十]){1,3}号', '([0-9一二三四五六七八九十]){1,3}日']
    # TODO: 此处应当在添加对于12.1,12.23这样日期的支持

    result_day = now.day
    for texts in enumerate(specical_day_template.keys()):  # 检测是否有特殊日期
        if re.search(texts[1], text) is not None:
            result_day = result_day + \
                         specical_day_template[re.search(texts[1], text)[0]]
            return result_day%day_of_month(
                now.month,
                now.year)
    for texts in week_day_template:  # 检测星期
        if re.search(texts, text) is not None:
            result_day = (result_day + (chinese_number[
                                            re.search(texts, text)[0][-1]] - 1 - now.weekday())%7)
            return result_day%day_of_month(
                now.month,
                now.year)
    for texts in date_day_template:  # 检测具体日期
        if re.search(texts, text) is not None:
            temp_day = re.search(texts, text)[0][:-1]
            try:
                result_day = int(temp_day)
            except ValueError:  # 抓取到的是中文，无法用int转换
                result_day = chinese_number[temp_day]
            finally:
                if result_day > 31 or result_day < 1:
                    break
                return result_day
    return None


def find_hourandmin_in_text(text):
    """
    在文本中提取小时和分钟
    :param text: 要提取小时和分钟的文本
    :return: (integer,integer) 提取的小时和分钟
    """
    # TODO: 此处应当再添加对于12点，1点的支持，还有对于上午下午晚上的识别
    hour_and_min_template = {0: '[0-9]{1,2}[点时:：][0-9]{2}[分]?',
                             1: '[0-9零一二三四五六七八九十]{1,3}点半'}
    for temp, (index, texts) in enumerate(hour_and_min_template.items()):
        if re.search(texts, text) is not None:
            temp_time = re.search(texts, text)
            if index == 1:  # 考虑第二种情况
                result_minute = 30
                try:
                    result_hour = int(temp_time[0][:-2])
                except ValueError:  # 抓取到的是中文，无法用int转换
                    result_hour = chinese_number[temp_time[0][:-2]]
            else:  # 考虑第一种情况
                result_hour = int(re.search(
                    '^[0-9]{1,2}', temp_time[0][0:2])[0])
                result_minute = int(re.search('[0-9]{2}', temp_time[0][2:])[0])
            return result_hour, result_minute
    return None


def find_time_in_appointment(appointment, now):
    """
    在文本中按照b站自带的预约功能提取文本中出现的时间
    :param appointment: b站自带的预约功能的文本
    :param now: 进行提取时作为基准的现在的时间
    :return: datetime 提取的时间对象
    """
    now = now.astimezone(CST_TIME_ZONE)

    result_year = now.year

    matched_time = re.search(
        r'[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]', appointment)
    if matched_time is None:
        raise TimelineException(f"在预约[{appointment}]中未找到对应的格式")
    result_month = int(matched_time[0][0:2])
    result_day = int(matched_time[0][3:5])
    result_hour = int(matched_time[0][6:8])
    result_minute = int(matched_time[0][9:11])
    result_time = timezone.datetime(result_year, result_month, result_day,
                                    result_hour, result_minute, tzinfo=CST_TIME_ZONE)
    # TODO: 使用timezone.timedelta实现
    if (result_time - now).days < -30:
        result_time = datetime.datetime(result_year + 1, result_month,
                                        result_day, result_hour,
                                        result_minute, tzinfo=CST_TIME_ZONE)
        # 处理年份缺省时实际上为下一年的情况，认为月份和日期比今天要早一个月以上，则判定为明年
    return result_time


def find_time_in_text(dynamic_text, now):
    """
    在动态文本中检测并提取文本中包含的时间
    :param dynamic_text: 需要提取时间的动态文本
    :param now: 进行提取时作为基准的现在的时间
    :return: datetime 提取的时间对象(提取失败返回None)
    """
    now = now.astimezone(CST_TIME_ZONE)

    result_year = now.year
    result_month = now.month
    result_day = now.day
    result_hour = now.hour
    result_minute = 0
    # 先尝试匹配日期
    result_day = find_day_in_text(dynamic_text, now=now)
    if result_day is not None:
        if result_day < now.day:  # 日期小于当前日期，应当为下一个月
            result_month = result_month + 1
            if result_month > 12:  # 考虑跨年情况
                result_month = 1
                result_year = result_year + 1
        if find_hourandmin_in_text(dynamic_text):
            result_hour, result_minute = find_hourandmin_in_text(dynamic_text)
            return datetime.datetime(
                result_year, result_month, result_day,
                result_hour, result_minute, tzinfo=CST_TIME_ZONE)
        else:
            return timezone.datetime(result_year, result_month, result_day, tzinfo=CST_TIME_ZONE)
    else:
        return None


def extract_from_text(text):
    """
    在文本中提取文本摘要
    :param text: 需要提取摘要的文本
    :return: string 提取的摘要信息
    """
    extract_length = 30  # 暂定提取前30个字作为摘要
    if len(text) >= extract_length:  # 处理动态文本少于30个字的情况
        return text[0:extract_length]
    else:
        return text


def classify_dynamic(dynamic_text):
    """
    对输入的动态文本进行分类
    :param dynamic_text: 需要分类的动态文本
    :return: string 文本分类的结果，具体分类类型见model定义处
    """
    stream_keywords = ['直播', '播']
    lottery_keywords = ['开奖', '抽奖', '抽']
    release_keywords = ['投稿', '新视频', '新歌', '新曲']
    for keyword in stream_keywords:
        if re.search(keyword, dynamic_text) is not None:
            return 'ST'
    for keyword in release_keywords:
        if re.search(keyword, dynamic_text) is not None:
            return 'RE'
    for keyword in lottery_keywords:
        if re.search(keyword, dynamic_text) is not None:
            return 'LO'
    return 'UN'


@shared_task
def process_timeline(dynamic_id):
    """
    对dynamic进行处理得到timeline对象
    :param dynamic_id: 需要处理的dynamic对象
    :return: None
    """
    logger.info(f"开始提取timeline：{dynamic_id}")
    info = TimelineDynamicProcessInfo.get(dynamic_id)
    if not info.should_update():
        logger.info(f"动态{dynamic_id}已处理，跳过")
        return
    try:
        do_process(dynamic_id)
    except ValueError as e:
        logger.warning(f"[{dynamic_id}] {e}")
    except TimelineException as e:
        logger.warning(f"[{dynamic_id}] {e}")
    info.apply_update()


def do_process(dynamic_id):
    """
    对dynamic执行文字、日期提取和分类并构建timeline对象
    :param dynamic_id: 需要处理的dynamic对象
    :return: None
    """
    origin_dynamic = Dynamic.objects.get(dynamic_id=dynamic_id)
    origin_dynamic.timestamp = origin_dynamic.timestamp.astimezone(CST_TIME_ZONE)
    dynamic_type = origin_dynamic.raw['desc']['type']
    card = json.loads(origin_dynamic.raw['card'])
    if dynamic_type == 1 or dynamic_type == 4:  # 转发或文字动态
        dynamic_text = card['item']['content']
    elif dynamic_type == 2:  # 图片动态
        dynamic_text = card['item']['description']
    elif dynamic_type == 8:  # 视频动态则直接判断为投稿新视频
        dynamic_text = card['title']
        TimelineEntry.objects.update_or_create(
            dynamic=origin_dynamic,
            defaults=dict(
                event_time=origin_dynamic.timestamp,
                type='RE',
                text={
                    'extract': f'投稿了{dynamic_text}'
                }
            )
        )
        return
    else:  # 其他类型的动态不太可能是时效性信息，直接舍弃
        return
    # 先提取时间信息判断是否为时效性动态
    dynamic_time = None
    try:  # 先检测是否使用了B站已有的直播预约功能,由预约信息中提取时间
        dynamic_time = find_time_in_appointment(
            origin_dynamic.raw['display']['add_on_card_info'][0]['reserve_attach_card']['desc_first']['text'],
            now=origin_dynamic.timestamp)
    except KeyError:
        dynamic_time = find_time_in_text(dynamic_text, now=origin_dynamic.timestamp)
    finally:
        if dynamic_time is not None:
            TimelineEntry.objects.update_or_create(dynamic=origin_dynamic,
                                                   defaults=dict(
                                                       event_time=dynamic_time,
                                                       type=classify_dynamic(
                                                           dynamic_text),
                                                       text={
                                                           'extract':
                                                               extract_from_text(
                                                                   dynamic_text)}))
