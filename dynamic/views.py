from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist, BadRequest

from subscribe.models import MemberGroup
from .models import Dynamic

# Create your views here.


@login_required
def list_dynamic(request):
    try:
        gid = int(request.GET.get('gid', 0))
        offset = int(request.GET.get('offset', 0))
        size = int(request.GET.get('size', 20))
    except KeyError or ValueError:  # 需要关注的对象还不在Member中，尝试加入
        raise BadRequest()

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        dynamics = Dynamic.select_dynamics_in_group(group, offset)
        dynamics = list(dynamics[:size + 1])
        has_more = len(dynamics) >= size + 1
        offset = dynamics[-1].dynamic_id if has_more else 0
        dynamics = dynamics[0:-2] if has_more else dynamics
        return JsonResponse({
            'code': 200,
            'data': {
                'has_more': has_more,
                'gid': group.gid,
                'group_name': group.group_name,
                'offset': offset,
                'data': [dynamic.as_dict() for dynamic in dynamics]
            }
        })
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)
