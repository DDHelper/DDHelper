from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from account.models import Userinfo
from django.urls import reverse

import random


# @csrf_exempt
# def login(request):
#     """
#     请求参数
#     Body:
#     参数名称	    参数类型	是否必须	    示例	    备注
#     username	T文本	是	    pawn
#     password	T文本	是	    123456

#     返回数据
#     名称	     类型	是否必须	默认值	备注	其他信息
#     code	number	必须
#     msg	    string	非必须
#     data	object	必须
#      - uid	string	必须

#     使用账号名和密码进行登录。
#     如果登录成功，返回用户信息，通过Set-Cookies返回认证信息
#     如果登录失败，code设置为403，不返回data
#     """
#     user = authenticate(username=request.POST.get('username'),
#                         password=request.POST.get('password'))

#     if user is not None:
#         response_ = JsonResponse({
#             'code': 200,
#             'data': {
#                 'uid': user.__str__()
#             }
#         })
#         response_.set_cookie('name',
#                              request.POST.get('username'),
#                              max_age=3600)
#     else:
#         response_ = JsonResponse({
#             'code': 403,
#             'msg': "user not existed or wrong password"
#         })
#         response_.status_code = 403
#     return response_


@csrf_exempt
def register(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    username	T文本	是	    user_abcd
    password	T文本	是	    123456abcd
    pin       T文本	是	    3242

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    msg	    string	非必须

    注册一个账号。
    如果填写成功，发送pin
    如果失败，code设置为403，msg为失败的原因
    """
    try:


        request.session['username'] = request.POST.get('username')
        request.session['password'] = request.POST.get('password')
        request.session['email'] = request.POST.get('email')
        request.session['uid'] = request.POST.get('uid')

        user = Userinfo.objects.create_user(
                username=request.session['username'],
                password=request.session['password'],
                email = request.session['email'],
                uid=request.session['uid']
                )
        user.save()
        
    except Exception as error:
        response_ = JsonResponse({
            'code': 403,
            'msg': error.__str__()
        })
        response_.status_code = 403
        return response_
    else:
        
        return JsonResponse({'code': 200})


@csrf_exempt
def send_pin(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    email       T文本	是	    123456abcd@xx.xxx

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    msg	    string	非必须

    注册一个账号。
    如果填写成功，发送pin
    如果失败，code设置为403，msg为失败的原因
    """
    try:

        request.session.set_expiry(0)
        pin = random.randint(999, 9999)
        request.session['pin'] = pin
        email = request.POST.get('email')
        # TODO:
        # send_pin(email, pin)
        
    except Exception as error:
        response_ = JsonResponse({
            'code': 403,
            'msg': error.__str__()
        })
        response_.status_code = 403
        return response_
    else:
        
        return JsonResponse({'code': 200})



@csrf_exempt
def verify_pin(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    pin	T文本	是	    1947
    

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    msg	    string	非必须

    验证一个账号的注册邮箱。
    如果验证成功，正常返回
    如果验证失败，code设置为403，msg为失败的原因
    """
    try:
        entered_pin = request.POST.get('pin')
        pin = request.session.get('pin', 'N/A')
        if pin == 'N/A':
            raise Exception('Verification PIN not found!')
        if entered_pin == pin: #if verification success
            return JsonResponse({'code': 200})
        else:
            raise Exception('Verification PIN not match!')
    except Exception as error:
        response_ = JsonResponse({
            'code': 403,
            'msg': error.__str__()
        })
        response_.status_code = 403
        return response_
    # else:
    #     return JsonResponse({'code': 200})   