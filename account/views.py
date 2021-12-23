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
    用户登录，登录成功，返回用户信息，通过Set-Cookies返回认证信息，登录失败，code设置为403，不返回data
    :param request: POST型request
    请求参数
        username string 必要 登录用户名
        password string 必要 登陆密码
    :return: Response
    返回数据
        data object
        - uid num 登录的用户id
        - username 登录的用户名
        code num 状态码
        msg string 出错信息
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
    """
    用户登出
    :param request: POST型request
    :return: Response
    返回数据
        code num 状态码
    """
    auth.logout(request)
    return JsonResponse({'code': 200})


@login_required
@require_POST
def change_password(request):
    """
    用户更新密码
    :param request: POST型request
    请求参数
        old_password string 必要 旧密码
        new_password string 必要 新密码
        pin num 必要 验证码
    :return: Response
    返回数据
        code num 状态码
        msg string 出错信息
    """
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
    """
    获取用户信息
    :param request: GET型request
    :return: Response
    返回数据
        code num 状态码
        data object 用户信息
        - username string 用户名
        - uid num 用户id
        - email string 用户邮箱
    """
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
    用户注册
    :param request: POST型request
    请求参数
        username string 必要 登录用户名
        password string 必要 登陆密码
        email string 必要 注册邮箱
        pin num 必要 验证码
    :return: Response
    返回数据
        code num 状态码
        msg string 出错信息
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
    向给定邮箱发送验证码
    :param request: POST型request
    请求参数
        email string 非必要 未注册用户发送验证码的邮箱
    :return: Response
    返回数据
        code num 状态码
        msg string 出错信息
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
    检查email和pin值
    :param request:
    :param email: 待检查的邮箱
    :param pin: 待检查的验证码
    :return: Response
    返回数据
        code num 状态码
        msg string 出错信息
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
    :param request: request
    :return: Bool 超时则为真
    """
    timeout = (time.time() - request.session[REGISTER_SEND_PIN_TIME]) > REGISTER_PIN_TIME_OUT
    if timeout:
        clear_pin_info(request)
    return timeout


def check_pin(request, email, pin):
    """
    检查一个请求的验证码状态，并增加一次尝试计数。
    :param request:
    :param email: 待检查的邮箱
    :param pin: 待检查的验证码
    :return: Bool 超过最大尝试次数时返回False，否则返回True
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
    :return: None
    """
    del request.session[REGISTER_PIN]
    del request.session[REGISTER_EMAIL]
    del request.session[REGISTER_SEND_PIN_TIME]
    del request.session[REGISTER_PIN_VERIFY_RETIES]


@require_GET
@csrf_exempt
def verify_pin(request):
    """
    验证一个账号的注册邮箱
    :param request: GET型request
    请求参数
        email string 必要 待验证的邮箱
        pin string 必要 待验证的验证码
    :return: Response
    返回数据
        match bool 验证码是否验证正确，正确返回True，否则False
        code num 状态码
        msg string 出错信息
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
