import json
from timeline.models import TimelineEntry
from subscribe.models import MemberGroup
from account.decorators import login_required
import re
import datetime
from django.http.response import JsonResponse


chinese_number = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7,
                  '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12, '十三': 13,
                  '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18,
                  '十九': 19, '二十': 20, '二十一': 21, '二十二': 22, '二十三': 23,
                  '二十四': 24, '二十五': 25, '二十六': 26, '二十七': 27, '二十八': 28,
                  '二十九': 29, '三十': 30, '三十一': 31, '日': 7, '天': 7, '零': 0}


# Create your views here.
@login_required
def show_timeline(request):
    # 以post方式输入需要时效性的日期范围time_region，为两个元素的列表(必须返回)，
    # 每个元素有year,month,day,hour,minute,second6个属性
    # 还可以输入需要筛选的标签类型dynamic_type(含有'ST','RE','LO'三个元素中任意几个的列表)
    # 必须返回，不筛选则需要返回空列表
    # 还可以输入需要筛选的分组标签member_group(gid列表)
    # 必须返回，不筛选则需要返回空列表
    # 返回json，包含了搜索范围内的所有时效性动态对象及这些对象的全部信息
    time_region_list = request.POST.getlist('time_region')
    start_time = datetime.time(
        year=time_region_list[0].year,
        month=time_region_list[0].month,
        day=time_region_list[0].day,
        hour=time_region_list[0].hour,
        minute=time_region_list[0].minute,
        second=time_region_list[0].second
    )
    end_time = datetime.time(
        year=time_region_list[1].year,
        month=time_region_list[1].month,
        day=time_region_list[1].day,
        hour=time_region_list[1].hour,
        minute=time_region_list[1].minute,
        second=time_region_list[1].second
    )
    result_dynamic = TimelineEntry.objects.\
        filter(event_time__range=(start_time, end_time))
    dynamic_type = request.POST.getlist('dynamic_type')
    if dynamic_type != []:
        result_dynamic = result_dynamic.\
            filter(type__in=dynamic_type)
    selected_group = request.POST.getlist('member_group')
    if selected_group != []:
        selected_member = MemberGroup.objects.\
            filter(gid__in=selected_group).order_by('members').values_list(
                'members').distinct()
        result_dynamic = result_dynamic.\
            filter(dynamic__member__in=selected_member)
    dynamic_data = []
    for dynamic in result_dynamic:
        each_dynamic_data = {
            'event_time': dynamic.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            'text': json.dumps(dynamic.text),
            'type': dynamic.type,
            'member': {
                'mid': dynamic.dynamic.member.mid,
                'name': dynamic.dynamic.member.name,
                'face': dynamic.dynamic.member.face
            }}
        dynamic_data.append(each_dynamic_data)
    return JsonResponse(dynamic_data)


def find_day_in_text(text):
    # 在一段文本中寻找日期
    specical_day_template = {'今天': 0, '明天': 1, '后天': 2, '大后天': 3}
    week_day_template = ['星期[一二三四五六七]', '周[一二三四五六七]']
    date_day_template = ['([0-9一二三四五六七八九十]){1,3}号', '([0-9一二三四五六七八九十]){1,3}日']
    result_day = datetime.datetime.now().day
    for texts in enumerate(specical_day_template.keys()):  # 检测是否有特殊日期
        if re.search(texts[1], text) is not None:
            result_day = result_day + \
                specical_day_template[re.search(texts[1], text)[0]]
            return result_day % datetime.datetime.now().month
    for texts in week_day_template:  # 检测星期
        if re.search(texts, text) is not None:
            result_day = (result_day + (chinese_number[
                re.search(texts, text)[0][-1]] - 1 - datetime.datetime.now
                ().weekday()) % 7)
            return result_day % datetime.datetime.now().month
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
    # 在一段文本中寻找具体时刻
    hour_and_min_template = {0: '[0-9]{1,2}[点时:][0-9]{2}[分]?',
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
            elif index == 0:  # 考虑第一种情况
                result_hour = int(re.search(
                    '^[0-9]{1,2}', temp_time[0][0:2])[0])
                result_minute = int(re.search('[0-9]{2}', temp_time[0][2:])[0])
            return result_hour, result_minute
    return None


def find_time_in_text(origin_dynamic):
    # 此函数用于检测并提取动态中包含的时间，成功检出时间返回检出的时间(datetime类型)，否则返回None
    # 设置默认解析值
    result_year = datetime.datetime.now().year
    result_month = datetime.datetime.now().month
    result_day = datetime.datetime.now().day
    result_hour = datetime.datetime.now().hour
    result_minute = 0
    try:  # 先检测是否使用了B站已有的直播预约功能
        time_in_rsp = origin_dynamic['display']['add_on_card_info'][0]
        ['reserve_attach_card']['desc_first']['text']
        matched_time = re.search(
            r'[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]', time_in_rsp)
        result_month = int(matched_time[0][0:2])
        result_day = int(matched_time[0][3:5])
        result_hour = int(matched_time[0][6:8])
        result_minute = int(matched_time[0][9:11])
        result_time = datetime.datetime(result_year, result_month, result_day,
                                        result_hour, result_minute)
        if (result_time - datetime.datetime.now()).days < -30:
            result_time = datetime.datetime(result_year + 1, result_month,
                                            result_day, result_hour,
                                            result_minute)
            # 处理年份缺省时实际上为下一年的情况，认为月份和日期比今天要早一个月以上，则判定为明年
        return result_time
    except KeyError:
        # 如果该动态并没有使用b站预约功能，使用别的方法尝试获取时间信息
        # 先尝试匹配日期
        if find_day_in_text(origin_dynamic['data']['cards']['desc']):
            result_day = find_day_in_text(origin_dynamic['data']['cards'][
                'desc'])
            if result_day < datetime.datetime.now().day:  # 日期小于当前日期，应当为下一个月
                result_month = result_month + 1
                if result_month > 12:  # 考虑跨年情况
                    result_month = 1
                    result_year = result_year + 1
            if find_hourandmin_in_text(origin_dynamic['data']['cards']['de\
            sc']):
                result_hour,
                result_minute = find_hourandmin_in_text(origin_dynamic['da\
                    ta']['cards']['desc'])
                return datetime.datetime(result_year, result_month, result_day,
                                         result_hour, result_minute)
            else:
                return datetime.datetime(result_year, result_month, result_day)
        else:
            return None


def extract_from_text(text):
    # 从动态文本中提取摘要
    extract_length = 30  # 暂定提取前30个字作为摘要
    if len(text) >= extract_length:  # 处理动态文本少于30个字的情况
        return text[0:extract_length]
    else:
        return text


def classify_dynamic(origin_dynamic):
    # 输入b站动态，对动态进行分类，返回标签
    dyanamic_text = origin_dynamic['data']['cards'][0]['card']
    stream_keywords = ['直播', '配信', '播']
    lottery_keywords = ['开奖', '抽奖', '抽']
    release_keywords = ['投稿', '新视频', '新歌', '新曲']
    for keyword in stream_keywords:
        if re.search(keyword, dyanamic_text) is not None:
            return 'ST'
    for keyword in release_keywords:
        if re.search(keyword, dyanamic_text) is not None:
            return 'RE'
    for keyword in lottery_keywords:
        if re.search(keyword, dyanamic_text) is not None:
            return 'LO'
    return 'UN'


def create_TimelineEntry(origin_dynamic):
    dynamic_time = find_time_in_text(origin_dynamic.raw)
    # 先提取时间信息判断是否为时效性动态
    if dynamic_time is not None:
        return TimelineEntry.objects.create(dynamic=origin_dynamic,
                                            event_time=dynamic_time,
                                            type=classify_dynamic(
                                                origin_dynamic.raw),
                                            text={'extract': extract_from_text(
                                                origin_dynamic.raw['data']['ca\
                                                    rds']['desc'])})
    else:
        return None
