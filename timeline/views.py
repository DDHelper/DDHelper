from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import re
import datetime
from django.http.response import JsonResponse


# Create your views here.
def show_timeline(request):
    return JsonResponse()


def find_time_in_text(text):
    # bilibili动态正文：document.getElementsByClassName("content-full")[0].innerText
    # 设置默认解析值
    # 此函数用于检测并提取动态中包含的时间
    result_year = datetime.datetime.now().year
    result_month = datetime.datetime.now().month
    result_day = datetime.datetime.now().day
    result_hour = datetime.datetime.now().hour
    result_minute = 0

    return datetime.datetime(result_year, result_month, result_day, result_hour, result_minute)


def extract_from_text(text):
    # 从动态文本中提取摘要
    extract_length = 30  # 暂定提取前30个字作为摘要
    if len(text) >= extract_length:
        return text[0:extract_length]
    else:
        return text


def classify_dynamic():
    # 输入b站动态，对动态进行分类，返回标签
    return
