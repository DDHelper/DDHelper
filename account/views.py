import random
import time
from contextlib import contextmanager

import django.contrib.auth as auth

from DDHelper.util import load_params
from .decorators import login_required
from django.core.exceptions import BadRequest
from django.core import mail
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from DDHelper import settings
from account.models import Userinfo

REGISTER_PIN = 'REGISTER_PIN'
REGISTER_EMAIL = 'REGISTER_EMAIL'
REGISTER_SEND_PIN_TIME = 'REGISTER_SEND_PIN_TIME'
REGISTER_PIN_VERIFY_RETIES = 'REGISTER_PIN_VERIFY_RETIES'
REGISTER_PIN_VERIFY_MAX_RETIES = 10
REGISTER_PIN_TIME_OUT = 60

OP_TYPE = {
    "register": "注册",
    "change_password": "修改密码",
}


@require_POST
@csrf_exempt
def login(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	    示例	    备注
    username	T文本	是	    pawn
    password	T文本	是	    123456

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	number	必须
    msg	    string	非必须
    data	object	必须
     - uid	string	必须

    使用账号名和密码进行登录。
    如果登录成功，返回用户信息，通过Set-Cookies返回认证信息
    如果登录失败，code设置为403，不返回data
    """
    with load_params():
        username = request.POST['username']
        password = request.POST['password']

    user = auth.authenticate(username=username,
                             password=password)
    if user is not None:
        auth.login(request, user)
        return JsonResponse({
            'code': 200,
            'data': {
                'username': user.username,
                'uid': user.uid
            }
        })
    else:
        return JsonResponse({
            'code': 403,
            'msg': "用户名或密码错误"
        }, status=403)


@login_required
@require_POST
@csrf_exempt
def logout(request):
    auth.logout(request)
    return JsonResponse({'code': 200})


@login_required
@require_POST
def change_password(request):
    with load_params():
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        email = request.user.email
        pin = int(request.POST['pin'])

    rsp = do_check_pin(request, email, pin)
    if rsp is not None:
        return rsp

    user = request.user
    if not user.check_password(old_password):
        return JsonResponse({
            'code': 400,
            'msg': '旧密码错误'
        }, status=400)

    user.set_password(new_password)
    user.save()

    auth.update_session_auth_hash(request, user)
    auth.logout(request)

    return JsonResponse({'code': 200, 'msg': ''})


@login_required
@require_GET
@csrf_exempt
def user_info(request):
    user = request.user
    return JsonResponse({
        "code": 200,
        "data": {
            "username": user.username,
            "uid": user.uid,
            "email": user.email
        }
    })


@require_POST
@csrf_exempt
def register(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    username	T文本	是	    user_abcd
    password	T文本	是	    123456abcd
    email       T文本    是      123546@sss.com
    pin         T文本	是	    3242

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    msg	    string	非必须

    注册一个账号。
    如果失败，code设置为403，msg为失败的原因
    """
    with load_params():
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        pin = int(request.POST['pin'])

    rsp = do_check_pin(request, email, pin)
    if rsp is not None:
        return rsp

    if Userinfo.objects.filter(Q(username=username) | Q(email=email)).exists():
        return JsonResponse({
            'code': 400,
            'msg': '用户名或邮箱已被占用'
        }, status=400)

    user = Userinfo.objects.create_user(
        username=username,
        password=password,
        email=email
    )
    user.save()

    return JsonResponse({'code': 200, 'msg': ''})


@require_POST
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
        if not check_pin_timeout(request):
            return JsonResponse({
                'code': 400,
                'msg': f'重新发送验证码前请等待{REGISTER_PIN_TIME_OUT}秒'
            }, status=400)
    except KeyError:
        pass

    with load_params():
        op_type = request.POST.get('type', "register")
        if op_type == "register":
            email = request.POST['email']
        else:
            if request.user.is_authenticated:
                email = request.user.email
            else:
                return JsonResponse({
                    'code': 403,
                    'msg': "未登录"
                }, status=403)

    pin = random.randint(100000, 999999)
    request.session[REGISTER_SEND_PIN_TIME] = time.time()
    request.session[REGISTER_EMAIL] = email
    request.session[REGISTER_PIN] = pin
    request.session[REGISTER_PIN_VERIFY_RETIES] = 0
    try:
        mail.send_mail(
            f'DDHelper验证码',
            f"您用于{OP_TYPE[op_type]}的验证码为：{pin}",
            settings.PIN_EMAIL,
            [email],
            fail_silently=settings.EMAIL_FAIL_SILENTLY,
        )
    except Exception as e:
        return JsonResponse({
            'code': 400,
            'msg': '邮件发送失败，请重试',
            'exception': str(e) if settings.DEBUG else ""
        }, status=400)
    return JsonResponse({'code': 200, 'msg': ''})


def do_check_pin(request, email, pin):
    """
    检查email和pin值，如果失败返回JsonResponse
    :param request:
    :param email:
    :param pin:
    :return:
    """
    try:
        if check_pin_timeout(request):
            return JsonResponse({
                'code': 400,
                'msg': '验证码已超时'
            }, status=400)
        if not check_pin(request, email=email, pin=pin):
            return JsonResponse({
                'code': 400,
                'msg': '验证码或邮箱不正确'
            }, status=400)
    except KeyError:
        return JsonResponse({
            'code': 400,
            'msg': '请先获取验证码'
        }, status=400)

    clear_pin_info(request)


def check_pin_timeout(request):
    """
    检查验证码是否超时，超时后删除验证码信息
    :param request:
    :return:
    """
    timeout = (time.time() - request.session[REGISTER_SEND_PIN_TIME]) > REGISTER_PIN_TIME_OUT
    if timeout:
        clear_pin_info(request)
    return timeout


def check_pin(request, email, pin):
    """
    检查一个请求的验证码状态，并增加一次尝试计数。
    超过最大尝试时返回False
    :param request:
    :param email:
    :param pin:
    :return:
    """
    request.session[REGISTER_PIN_VERIFY_RETIES] += 1
    if request.session[REGISTER_PIN_VERIFY_RETIES] >= REGISTER_PIN_VERIFY_MAX_RETIES:
        return False
    if email != request.session[REGISTER_EMAIL] or pin != request.session[REGISTER_PIN]:
        return False
    return True


def clear_pin_info(request):
    """
    清除注册用的验证码相关信息
    :param request:
    :return:
    """
    del request.session[REGISTER_PIN]
    del request.session[REGISTER_EMAIL]
    del request.session[REGISTER_SEND_PIN_TIME]
    del request.session[REGISTER_PIN_VERIFY_RETIES]


@require_GET
@csrf_exempt
def verify_pin(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    pin      	T文本	是	    1947
    email       T文本	是	    12354@aaa.com

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    match   bool    必须
    msg	    string	非必须

    验证一个账号的注册邮箱。
    如果验证成功，正常返回
    如果验证失败，code设置为403，msg为失败的原因
    """
    with load_params():
        email = request.GET['email']
        pin = int(request.GET['pin'])

    try:
        if check_pin_timeout(request):
            return JsonResponse({
                'code': 400,
                'msg': "验证码超时"
            }, status=400)
        return JsonResponse({
            'code': 200,
            'match': check_pin(request, email=email, pin=pin)
        })
    except KeyError:
        return JsonResponse({
            'code': 400,
            'msg': '未获取验证码'
        }, status=400)
