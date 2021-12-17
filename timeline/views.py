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
    类似dynamic中的实现
    :param request:
    :return:
    """
    with load_params():
        gid = int(request.GET.get('gid', 0))
        offset = int(request.GET.get('offset', 0))
        size = int(request.GET.get('size', 20))
        if offset == 0:
            offset = None
        else:
            offset = datetime.datetime.fromtimestamp(offset).astimezone(CST_TIME_ZONE)

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
