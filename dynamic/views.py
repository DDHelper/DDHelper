from django.shortcuts import render

from DDHelper.util import load_params
from account.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist, BadRequest
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, DetailView

from subscribe.models import MemberGroup
from .models import Dynamic, DynamicSyncInfo

# Create your views here.


class DynamicSyncInfoListView(ListView):
    paginate_by = 20
    queryset = DynamicSyncInfo.objects.order_by('-sid')
    context_object_name = 'dynamic_sync_info'


class DynamicSyncInfoDetailView(DetailView):
    queryset = DynamicSyncInfo.objects.all()
    context_object_name = 'dynamic_sync_info'


class DynamicSyncInfoLatestDetailView(DetailView):
    template_name = 'dynamic/dynamicsyncinfo_detail.html'

    def get_object(self, queryset=None):
        return DynamicSyncInfo.get_latest()


@require_GET
@login_required
def list_dynamic(request):
    with load_params():
        gid = int(request.GET.get('gid', 0))
        offset = int(request.GET.get('offset', 0))
        size = int(request.GET.get('size', 20))

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        dynamics = Dynamic.select_dynamics_in_group(group, offset)
        dynamics = list(dynamics[:size + 1])
        has_more = len(dynamics) >= size + 1
        offset = dynamics[-1].dynamic_id if has_more else 0
        dynamics = dynamics[0:-1] if has_more else dynamics
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
