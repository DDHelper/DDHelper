from functools import wraps
from django.http import JsonResponse


def login_required(func):
    @wraps(func)
    def call_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return func(request, *args, **kwargs)
        else:
            return JsonResponse({
                'code': 403,
                'msg': "未登录"
            }, status=403)
    return call_func
