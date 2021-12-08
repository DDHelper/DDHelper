from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import dynamic
from timeline.models import TimelineEntry
import json
import re
import datetime
from django.http.response import JsonResponse


# Create your views here.
def show_timeline(request):
    return JsonResponse()


def find_time_in_text(dynamic):
    # bilibili动态正文：document.getElementsByClassName("content-full")[0].innerText
    # 设置默认解析值
    # 此函数用于检测并提取动态中包含的时间
    result_year = datetime.datetime.now().year
    result_month = datetime.datetime.now().month
    result_day = datetime.datetime.now().day
    result_hour = datetime.datetime.now().hour
    result_minute = 0
    try:# 先检测是否使用了B站已有的直播预约功能
        time_in_rsp = dynamic['display']['add_on_card_info'][0]['reserve_attach_card']['desc_first']['text']
        matched_time = re.search(r'[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]', time_in_rsp)
        result_month = int(matched_time[0][0:2])
        result_day = int(matched_time[0][3:5])
        result_hour = int(matched_time[0][6:8])
        result_minute = int(matched_time[0][9:11])
        result_time = datetime.datetime(result_year, result_month, result_day, result_hour, result_minute)
        if (result_time - datetime.datetime.now()).days < -30:
        # 处理年份缺省时实际上为下一年的情况，认为月份和日期比今天要早一个月以上，则判定为明年
            result_time = datetime.datetime(result_year+1, result_month, result_day, result_hour, result_minute)
        return result_time
    except KeyError:
        # 如果该动态并没有使用b站预约功能，使用别的方法尝试获取时间信息
        # 先尝试匹配日期
        return None


def extract_from_text(text):
    # 从动态文本中提取摘要
    extract_length = 30  # 暂定提取前30个字作为摘要
    if len(text) >= extract_length: # 处理动态文本少于30个字的情况
        return text[0:extract_length]
    else:
        return text


def classify_dynamic(dynamic):
    # 输入b站动态，对动态进行分类，返回标签
    dyanamic_text = dynamic['data']['cards'][0]['card']
    stream_keywords = ['直播', '配信', '播']
    lottery_keywords = ['开奖', '抽奖', '抽']
    release_keywords = ['投稿', '新视频', '新歌', '新曲']
    for keyword in stream_keywords:
        if re.search(keyword, dyanamic_text)!=None:
            return 'ST'
    for keyword in release_keywords:
        if re.search(keyword, dyanamic_text)!=None:
            return 'RE'
    for keyword in lottery_keywords:
        if re.search(keyword, dyanamic_text)!=None:
            return 'LO'   
    return 'UN'


def create_TimelineEntry(origin_dynamic):

    TimelineEntry.objects.create(dynamic = origin_dynamic,
                                event_time = find_time_in_text(origin_dynamic.raw),
                                type = classify_dynamic(origin_dynamic.raw),
                                text = {
                                    'extract':extract_from_text(origin_dynamic.raw['data']['cards']['desc'])
                                }})