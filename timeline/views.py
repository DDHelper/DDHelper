import json
import datetime

from DDHelper.settings import CST_TIME_ZONE
from DDHelper.util import load_params
from timeline.models import TimelineEntry
from subscribe.models import MemberGroup
from account.decorators import login_required
from django.http.response import JsonResponse


# Create your views here.
@login_required
def show_timeline(request):
    """
    根据筛选条件展示符合要求的timeline
    :param request: GET型request
    请求参数
        gid	num 非必要 需要展示的timeline所在组id,不传入时显示当前用户默认分组
        offset num 非必要 timeline时间筛选的最新时间戳
        size num 非必要 请求的timeline数量，默认20条
    :return: Response
    返回数据
        data object
        - has_more bool 是否有符合条件但因为超出请求数量而为加载的timeline
        - gid num 所选取分组id
        - group_name string 所选取分组的名称
        - offset num 返回的timeline对象中最旧的时间戳
        - data object_array 各timeline的信息
        code integer 状态码
        msg string 出错信息
    """
    with load_params():
        gid = int(request.GET.get('gid', 0))
        offset = int(request.GET.get('offset', 0))
        size = int(request.GET.get('size', 20))
        if offset == 0:
            offset = None
        else:
            offset = datetime.datetime.fromtimestamp(offset, tz=CST_TIME_ZONE)

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        entry = TimelineEntry.select_entry_in_group(group, offset)
        entry = list(entry[:size + 1])
        has_more = len(entry) >= size + 1
        offset = entry[-1].event_time.timestamp() if has_more else 0
        entry = entry[0:-1] if has_more else entry
        return JsonResponse({
            'code': 200,
            'data': {
                'has_more': has_more,
                'gid': group.gid,
                'group_name': group.group_name,
                'offset': offset,
                'data': [e.as_dict() for e in entry]
            }
        })
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)
